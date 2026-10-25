
from flask import Blueprint, render_template, request, redirect, url_for, flash
from services import dichvu_service

dichvu_bp = Blueprint("dichvu", __name__, url_prefix="/dich-vu")


@dichvu_bp.route("/")
def index():
    danh_sach = dichvu_service.get_all()
    return render_template("dichvu/list.html", danh_sach=danh_sach)


@dichvu_bp.route("/them", methods=["POST"])
def them():
    try:
        dichvu_service.create(
            request.form.get("ma_dv", ""),
            request.form.get("ten_dv", ""),
            request.form.get("don_gia", "")
        )
        flash("Thêm dịch vụ thành công!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception:
        flash("Không thể thêm dịch vụ. Có thể mã dịch vụ đã tồn tại.", "error")

    return redirect(url_for("dichvu.index"))


@dichvu_bp.route("/sua/<ma_dv>", methods=["POST"])
def sua(ma_dv):
    try:
        dichvu_service.update(
            ma_dv,
            request.form.get("ten_dv", ""),
            request.form.get("don_gia", "")
        )
        flash("Cập nhật dịch vụ thành công!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception:
        flash("Không thể cập nhật dịch vụ.", "error")

    return redirect(url_for("dichvu.index"))


@dichvu_bp.route("/xoa/<ma_dv>", methods=["POST"])
def xoa(ma_dv):
    try:
        dichvu_service.delete(ma_dv)
        flash("Xóa dịch vụ thành công!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception:
        flash("Không thể xóa dịch vụ. Có thể dịch vụ đang được sử dụng.", "error")

    return redirect(url_for("dichvu.index"))
