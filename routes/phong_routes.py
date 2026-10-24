from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import phong_service
from routes.auth_routes import login_required

bp = Blueprint("phong", __name__, url_prefix="/phong")

@bp.route("/")
@login_required
def list_p():
    rows = phong_service.lay_danh_sach()
    return render_template("phong/list.html", rows=rows)

@bp.route("/them", methods=["GET", "POST"])
@login_required
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
        
    return render_template("phong/form.html")