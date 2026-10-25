from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from routes.auth_routes import login_required
from services import tham_service


tham_bp = Blueprint("tham", __name__, url_prefix="/tham")


@tham_bp.route("/")
@login_required
def index():
    return render_template(
        "tham/list.html",
        danh_sach=tham_service.get_all(),
    )


def _form_options():
    return {
        "khach_list": tham_service.get_khach(),
        "sinh_vien": tham_service.get_sinhvien(),
    }


@tham_bp.route("/them", methods=["GET", "POST"])
@login_required
def them():
    data = {"MaKhach": "", "MaSV": "", "NgayDenChoi": ""}
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            tham_service.create(
                data.get("MaKhach"), data.get("MaSV"), data.get("NgayDenChoi")
            )
            flash("Thêm lượt thăm thành công!", "success")
            return redirect(url_for("tham.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể thêm lượt thăm")
            flash("Không thể thêm lượt thăm.", "danger")
    return render_template("tham/form.html", action="Thêm", tham=data, **_form_options())


@tham_bp.route("/sua/<int:ma_tham>", methods=["GET", "POST"])
@login_required
def sua(ma_tham):
    tham = tham_service.get_one(ma_tham)
    if not tham:
        flash("Không tìm thấy lượt thăm cần sửa.", "warning")
        return redirect(url_for("tham.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        try:
            tham_service.update(
                ma_tham, data.get("MaKhach"), data.get("MaSV"), data.get("NgayDenChoi")
            )
            flash("Cập nhật lượt thăm thành công!", "success")
            return redirect(url_for("tham.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể cập nhật lượt thăm")
            flash("Không thể cập nhật lượt thăm.", "danger")
        tham = data

    return render_template("tham/form.html", action="Sửa", tham=tham, **_form_options())


@tham_bp.route("/xoa/<int:ma_tham>", methods=["POST"])
@login_required
def xoa(ma_tham):
    try:
        tham_service.delete(ma_tham)
        flash("Xóa lượt thăm thành công!", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Không thể xóa lượt thăm")
        flash("Không thể xóa lượt thăm.", "danger")
    return redirect(url_for("tham.index"))
