from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import sinhvien_service
from routes.auth_routes import login_required, admin_required

bp = Blueprint("sinhvien", __name__, url_prefix="/sinhvien")

@bp.route("/")
@login_required
def list_sv():
    # Lấy từ khóa tìm kiếm và số trang từ URL (mặc định trang 1)
    search = request.args.get("search", "")
    page = int(request.args.get("page", 1))
    
    # Gọi Service lấy dữ liệu
    rows, total_pages, current_page = sinhvien_service.lay_danh_sach(search, page)
    
    return render_template("sinhvien/list.html", 
                           rows=rows, 
                           total_pages=total_pages, 
                           current_page=current_page, 
                           search=search)

@bp.route("/them", methods=["GET", "POST"])
@login_required
def them_sv():
    if request.method == "POST":
        # Gom dữ liệu từ form
        data = {k: request.form.get(k, "").strip() for k in ["MaSV", "SoCMT", "HoTen", "Lop", "QueQuan"]}
        data["NgaySinh"] = request.form.get("NgaySinh") or None
        
        # Gọi Service xử lý
        ok, err = sinhvien_service.them_sinh_vien(data)
        
        if ok:
            flash("Thêm sinh viên thành công!", "success")
            return redirect(url_for("sinhvien.list_sv"))
        flash(f"Lỗi: {err}", "danger")
        
    return render_template("sinhvien/form.html", action="Thêm", sv=None)

@bp.route("/sua/<masv>", methods=["GET", "POST"])
@login_required
def sua_sv(masv):
    # Lấy thông tin sinh viên hiện tại
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
@admin_required  # <-- Chỉ tài khoản admin mới được phép gọi hàm này
def xoa_sv(masv):
    ok, err = sinhvien_service.xoa_sinh_vien(masv)
    if ok: 
        flash("Đã xóa sinh viên!", "success")
    else: 
        flash(err, "danger")
    return redirect(url_for("sinhvien.list_sv"))

# TÍNH NĂNG IN THẺ SINH VIÊN
@bp.route("/in-the/<masv>")
@login_required
def in_the(masv):
    # Lấy thông tin sinh viên
    sv = sinhvien_service.lay_chi_tiet(masv)
    if not sv:
        flash("Không tìm thấy sinh viên!", "danger")
        return redirect(url_for("sinhvien.list_sv"))
    
    # Trả về giao diện in thẻ
    return render_template("sinhvien/in_the.html", sv=sv)