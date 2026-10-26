from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services import sinhvien_service
from routes.auth_routes import login_required, admin_required
from datetime import date

bp = Blueprint("sinhvien", __name__, url_prefix="/sinhvien")

# ==========================================
# PHẦN DÀNH CHO ADMIN
# ==========================================
@bp.route("/")
@login_required
@admin_required
def list_sv():
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    rows, total_pages, current_page = sinhvien_service.lay_danh_sach(search, page)
    return render_template("sinhvien/list.html", rows=rows, total_pages=total_pages, current_page=current_page, search=search)

@bp.route("/them", methods=["GET", "POST"])
@login_required
@admin_required
def them_sv():
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["MaSV", "SoCMT", "HoTen", "Lop", "QueQuan"]}
        data["NgaySinh"] = request.form.get("NgaySinh") or None
        ok, err = sinhvien_service.them_sinh_vien(data)
        if ok:
            flash("Thêm sinh viên thành công!", "success")
            return redirect(url_for("sinhvien.list_sv"))
        flash(f"Lỗi: {err}", "danger")
    return render_template("sinhvien/form.html", action="Thêm", sv=None)

@bp.route("/sua/<masv>", methods=["GET", "POST"])
@login_required
@admin_required
def sua_sv(masv):
    sv = sinhvien_service.lay_chi_tiet(masv)
    if not sv:
        flash("Không tìm thấy sinh viên!", "warning")
        return redirect(url_for("sinhvien.list_sv"))
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in ["SoCMT", "HoTen", "Lop", "QueQuan"]}
        data["NgaySinh"] = request.form.get("NgaySinh") or None
        ok, err = sinhvien_service.cap_nhat_sinh_vien(masv, data)
        if ok:
            flash("Cập nhật thành công!", "success")
            return redirect(url_for("sinhvien.list_sv"))
        flash(f"Lỗi: {err}", "danger")
    return render_template("sinhvien/form.html", action="Sửa", sv=sv)

@bp.route("/xoa/<masv>", methods=["POST"])
@login_required
@admin_required
def xoa_sv(masv):
    ok, err = sinhvien_service.xoa_sinh_vien(masv)
    if ok: flash("Đã xóa sinh viên!", "success")
    else: flash(err, "danger")
    return redirect(url_for("sinhvien.list_sv"))

@bp.route("/in-the/<masv>")
@login_required
@admin_required
def in_the(masv):
    sv = sinhvien_service.lay_chi_tiet(masv)
    if not sv:
        flash("Không tìm thấy sinh viên!", "danger")
        return redirect(url_for("sinhvien.list_sv"))
    return render_template("sinhvien/in_the.html", sv=sv)

# ==========================================
# PHẦN DÀNH CHO SINH VIÊN (PORTAL)
# ==========================================
@bp.route("/portal")
@login_required
def portal():
    if session.get("role") != "sinhvien":
        flash("Trang này chỉ dành cho sinh viên!", "danger")
        return redirect(url_for("main.index"))
        
    from database.connection import get_db
    db = get_db()
    cur = db.cursor(dictionary=True)
    
    # 1. Lấy thông tin sinh viên (để biết đang ở phòng nào)
    cur.execute("""
        SELECT sv.*, dk.SoPhong 
        FROM SinhVien sv
        LEFT JOIN DangKyPhong dk ON sv.MaSV = dk.MaSV AND dk.NgayKetThuc IS NULL AND dk.TrangThai = 'Đã duyệt'
        WHERE sv.MaSV = %s
    """, (session["user"],))
    sv = cur.fetchone()
    
    # 2. Lấy trạng thái đơn đăng ký gần nhất
    cur.execute("""
        SELECT TrangThai, SoPhong, NgayBatDau 
        FROM DangKyPhong 
        WHERE MaSV = %s 
        ORDER BY MaDK DESC LIMIT 1
    """, (session["user"],))
    don_dang_ky = cur.fetchone()
    
    cur.close()
    
    return render_template("sinhvien/portal_home.html", sv=sv, don_dang_ky=don_dang_ky)

@bp.route("/portal/info")
@login_required
def portal_info():
    if session.get("role") != "sinhvien":
        return redirect(url_for("main.index"))
    sv = sinhvien_service.lay_chi_tiet(session["user"])
    if not sv:
        sv = {"MaSV": session["user"], "HoTen": session["hoten"], "SoPhong": None, "NgaySinh": None, "Lop": None, "QueQuan": None, "SoCMT": None}
    return render_template("sinhvien/portal_info.html", sv=sv)

@bp.route("/portal/update_info", methods=["POST"])
@login_required
def portal_update_info():
    if session.get("role") != "sinhvien":
        return redirect(url_for("main.index"))
    masv = session["user"]
    data = {
        "SoCMT": request.form.get("SoCMT", "").strip(),
        "HoTen": request.form.get("HoTen", "").strip(),
        "NgaySinh": request.form.get("NgaySinh") or None,
        "Lop": request.form.get("Lop", "").strip(),
        "QueQuan": request.form.get("QueQuan", "").strip(),
    }
    ok, err = sinhvien_service.cap_nhat_sinh_vien(masv, data)
    if ok:
        flash("Cập nhật thông tin thành công!", "success")
    else:
        flash(f"Lỗi: {err}", "danger")
    return redirect(url_for("sinhvien.portal_info"))

@bp.route("/portal/rooms")
@login_required
def portal_rooms():
    if session.get("role") != "sinhvien":
        return redirect(url_for("main.index"))
    from repositories import phong_repo
    phongs = phong_repo.get_all()
    phong_trongs = [p for p in phongs if p['DangO'] < p['SoNguoiToiDa']]
    return render_template("sinhvien/portal_rooms.html", phongs=phong_trongs)

@bp.route("/dang-ky-phong/<so_phong>", methods=["POST"])
@login_required
def sv_dang_ky(so_phong):
    if session.get("role") != "sinhvien":
        return redirect(url_for("main.index"))
    from services import dangkyphong_service
    data = {
        "MaSV": session["user"],
        "SoPhong": so_phong,
        "NgayBatDau": date.today().isoformat(),
        "NgayKetThuc": None
    }
    ok, err = dangkyphong_service.them_dang_ky(data)
    if ok:
        flash(f"Đã gửi yêu cầu đăng ký phòng {so_phong}. Vui lòng chờ quản lý duyệt!", "info")
    else:
        flash(f"Lỗi: {err}", "danger")
    return redirect(url_for("sinhvien.portal_rooms"))