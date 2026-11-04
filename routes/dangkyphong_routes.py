from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import dangkyphong_service
from repositories import sinhvien_repo, phong_repo
from repositories import dangkyphong_repo
from repositories.rules import error_message
import mysql.connector
from routes.auth_routes import login_required

bp = Blueprint("dangkyphong", __name__, url_prefix="/dangkyphong")

@bp.route("/")
@login_required
def list_dk():
    rows = dangkyphong_service.lay_danh_sach()
    return render_template("dangkyphong/list.html", rows=rows)

@bp.route("/them", methods=["GET", "POST"])
@login_required
def them_dk():
    if request.method == "POST":
        data = {
            "MaSV": request.form.get("MaSV"),
            "SoPhong": request.form.get("SoPhong"),
            "NgayBatDau": request.form.get("NgayBatDau"),
            "NgayKetThuc": request.form.get("NgayKetThuc") or None
        }
        ok, err = dangkyphong_service.them_dang_ky(data)
        if ok:
            flash("Đăng ký phòng thành công!", "success")
            return redirect(url_for("dangkyphong.list_dk"))
        
        # NẾU PHÒNG ĐẦY, TRIGGER SẼ BẮN LỖI VÀO BIẾN err
        flash(f"Lỗi từ CSDL: {err}", "danger")
        
    # Lấy danh sách để hiển thị lên Dropdown (Select box)
    sinhviens, _ = sinhvien_repo.get_all(per_page=100000)
    phongs = phong_repo.get_all()
    
    return render_template("dangkyphong/form.html", sinhviens=sinhviens, phongs=phongs)


@bp.route('/<int:registration_id>/tra-phong', methods=['POST'])
@login_required
def tra_phong(registration_id):
    try:
        dangkyphong_repo.end_registration(registration_id, request.form.get('NgayKetThuc'))
        flash('Đã ghi nhận ngày trả phòng và giữ lịch sử đăng ký.', 'success')
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), 'danger')
    return redirect(url_for('dangkyphong.list_dk'))
