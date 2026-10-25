from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from routes.auth_routes import login_required
from services import luotguixe_service


luotguixe_bp = Blueprint("luotguixe", __name__, url_prefix="/luot-gui-xe")


@luotguixe_bp.route("/")
@login_required
def index():
    return render_template(
        "luotguixe/list.html",
        danh_sach=luotguixe_service.get_all(),
    )


def _form_options():
    return {"xe_list": luotguixe_service.get_xe()}


@luotguixe_bp.route("/them", methods=["GET", "POST"])
@login_required
def them():
    data = {"BienSo": "", "ThoiGianLay": "", "ThoiGianGui": ""}
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            fee = luotguixe_service.create(
                data.get("BienSo"), data.get("ThoiGianLay"),
                data.get("ThoiGianGui")
            )
            flash(f"Thêm lượt gửi xe thành công! Phí: {fee:,.0f} đ.", "success")
            return redirect(url_for("luotguixe.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể thêm lượt gửi xe")
            flash("Không thể thêm lượt gửi xe.", "danger")
    return render_template(
        "luotguixe/form.html", action="Thêm", luot=data, **_form_options()
    )


@luotguixe_bp.route("/sua/<int:ma_luot>", methods=["GET", "POST"])
@login_required
def sua(ma_luot):
    luot = luotguixe_service.get_one(ma_luot)
    if not luot:
        flash("Không tìm thấy lượt gửi xe cần sửa.", "warning")
        return redirect(url_for("luotguixe.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        try:
            fee = luotguixe_service.update(
                ma_luot, data.get("BienSo"), data.get("ThoiGianLay"),
                data.get("ThoiGianGui")
            )
            flash(f"Cập nhật lượt gửi xe thành công! Phí: {fee:,.0f} đ.", "success")
            return redirect(url_for("luotguixe.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể cập nhật lượt gửi xe")
            flash("Không thể cập nhật lượt gửi xe.", "danger")
        luot = data

    return render_template(
        "luotguixe/form.html", action="Sửa", luot=luot, **_form_options()
    )


@luotguixe_bp.route("/xoa/<int:ma_luot>", methods=["POST"])
@login_required
def xoa(ma_luot):
    try:
        luotguixe_service.delete(ma_luot)
        flash("Xóa lượt gửi xe thành công!", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Không thể xóa lượt gửi xe")
        flash("Không thể xóa lượt gửi xe.", "danger")
    return redirect(url_for("luotguixe.index"))
