from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from routes.auth_routes import login_required
from services import xe_service


xe_bp = Blueprint("xe", __name__, url_prefix="/xe")


@xe_bp.route("/")
@login_required
def index():
    return render_template(
        "xe/list.html",
        danh_sach=xe_service.get_all(),
    )


def _form_options():
    return {"sinh_vien": xe_service.get_sinhvien()}


@xe_bp.route("/them", methods=["GET", "POST"])
@login_required
def them():
    data = {"BienSo": "", "MaSV": "", "LoaiXe": ""}
    if request.method == "POST":
        data = request.form.to_dict()
        try:
            xe_service.create(data.get("BienSo"), data.get("MaSV"), data.get("LoaiXe"))
            flash("Thêm xe thành công!", "success")
            return redirect(url_for("xe.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể thêm xe")
            flash("Không thể thêm xe. Có thể biển số đã tồn tại.", "danger")
    return render_template("xe/form.html", action="Thêm", xe=data, **_form_options())


@xe_bp.route("/sua/<path:bien_so>", methods=["GET", "POST"])
@login_required
def sua(bien_so):
    xe = xe_service.get_one(bien_so)
    if not xe:
        flash("Không tìm thấy xe cần sửa.", "warning")
        return redirect(url_for("xe.index"))

    if request.method == "POST":
        data = request.form.to_dict()
        try:
            xe_service.update(bien_so, data.get("MaSV"), data.get("LoaiXe"))
            flash("Cập nhật xe thành công!", "success")
            return redirect(url_for("xe.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            current_app.logger.exception("Không thể cập nhật xe")
            flash("Không thể cập nhật xe.", "danger")
        xe = {"BienSo": bien_so, **data}

    return render_template("xe/form.html", action="Sửa", xe=xe, **_form_options())


@xe_bp.route("/xoa/<path:bien_so>", methods=["POST"])
@login_required
def xoa(bien_so):
    try:
        xe_service.delete(bien_so)
        flash("Xóa xe thành công!", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception:
        current_app.logger.exception("Không thể xóa xe")
        flash("Không thể xóa xe. Có thể xe đã có lượt gửi.", "danger")
    return redirect(url_for("xe.index"))
