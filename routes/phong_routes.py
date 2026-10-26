from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import phong_service
from routes.auth_routes import login_required, admin_required

bp = Blueprint("phong", __name__, url_prefix="/phong")

@bp.route("/")
@login_required
@admin_required
def list_p():
    rows = phong_service.lay_danh_sach()
    return render_template("phong/list.html", rows=rows)

@bp.route("/them", methods=["GET", "POST"])
@login_required
@admin_required
def them_p():
    if request.method == "POST":
        data = {
            "SoPhong": request.form.get("SoPhong", "").strip(),
            "LoaiPhong": request.form.get("LoaiPhong", "").strip(),
            "DonGia": float(request.form.get("DonGia", 0)),
            "SoNguoiToiDa": int(request.form.get("SoNguoiToiDa", 1))
        }
        ok, err = phong_service.them_phong(data)
        if ok:
            flash("Thêm phòng thành công!", "success")
            return redirect(url_for("phong.list_p"))
        flash(f"Lỗi: {err}", "danger")
        
    return render_template("phong/form.html", action="Thêm", p=None)

@bp.route("/sua/<so_phong>", methods=["GET", "POST"])
@login_required
@admin_required
def sua_p(so_phong):
    # Lấy thông tin phòng hiện tại
    phong = phong_service.lay_chi_tiet(so_phong)
    if not phong:
        flash("Không tìm thấy phòng!", "warning")
        return redirect(url_for("phong.list_p"))
        
    if request.method == "POST":
        data = {
            "LoaiPhong": request.form.get("LoaiPhong", "").strip(),
            "DonGia": float(request.form.get("DonGia", 0)),
            "SoNguoiToiDa": int(request.form.get("SoNguoiToiDa", 1))
        }
        ok, err = phong_service.cap_nhat_phong(so_phong, data)
        if ok:
            flash("Cập nhật phòng thành công!", "success")
            return redirect(url_for("phong.list_p"))
        flash(f"Lỗi: {err}", "danger")
        
    # Truyền action="Sửa" và biến p (chứa thông tin phòng) sang form
    return render_template("phong/form.html", action="Sửa", p=phong)

@bp.route("/xoa/<so_phong>", methods=["POST"])
@login_required
@admin_required
def xoa_p(so_phong):
    ok, err = phong_service.xoa_phong(so_phong)
    if ok:
        flash("Đã xóa phòng!", "success")
    else:
        flash(err, "danger")
    return redirect(url_for("phong.list_p"))