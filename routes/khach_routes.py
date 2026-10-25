from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from routes.auth_routes import login_required
from services import khach_service


khach_bp = Blueprint("khach", __name__, url_prefix="/khach")


@khach_bp.route("/")
@login_required
def index():
    return render_template("khach/list.html", danh_sach=khach_service.get_all())


@khach_bp.route("/them", methods=["GET", "POST"])
@login_required
def them():
    data = {"SoCMT": "", "Ten": "", "NgaySinh": ""}
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            khach_service.create(
                data.get("SoCMT"), data.get("Ten"), data.get("NgaySinh")
            )
            flash("Thêm khách thành công!", "success")
            return redirect(url_for("khach.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể thêm khách")
            flash("Không thể thêm khách. Có thể số CMT đã tồn tại.", "danger")
    return render_template("khach/form.html", action="Thêm", khach=data)


@khach_bp.route("/sua/<int:ma_khach>", methods=["GET", "POST"])
@login_required
def sua(ma_khach):
    khach = khach_service.get_one(ma_khach)
    if not khach:
        flash("Không tìm thấy khách cần sửa.", "warning")
        return redirect(url_for("khach.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        try:
            khach_service.update(
                ma_khach, data.get("SoCMT"), data.get("Ten"), data.get("NgaySinh")
            )
            flash("Cập nhật khách thành công!", "success")
            return redirect(url_for("khach.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể cập nhật khách")
            flash("Không thể cập nhật khách. Có thể số CMT đã tồn tại.", "danger")
        khach = data

    return render_template("khach/form.html", action="Sửa", khach=khach)


@khach_bp.route("/xoa/<int:ma_khach>", methods=["POST"])
@login_required
def xoa(ma_khach):
    try:
        khach_service.delete(ma_khach)
        flash("Xóa khách thành công!", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Không thể xóa khách")
        flash("Không thể xóa khách. Có thể khách đã có lượt thăm.", "danger")
    return redirect(url_for("khach.index"))
