from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import login_required
from services import sudungdichvu_service as service

sudungdichvu_bp = Blueprint(
    "sudungdichvu",
    __name__,
    url_prefix="/su-dung-dich-vu"
)


@sudungdichvu_bp.route("/")
def index():
    return render_template(
        "sudungdichvu/list.html",
        danh_sach=service.get_all(),
        sinh_vien=service.get_sinhvien(),
        dich_vu=service.get_dichvu()
    )


@sudungdichvu_bp.route("/hoa-don/<ma_sv>")
@login_required
def hoa_don(ma_sv):
    chi_tiet = service.get_invoice(ma_sv)
    if not chi_tiet:
        flash("Sinh viên này chưa có lượt sử dụng dịch vụ.", "warning")
        return redirect(url_for("sudungdichvu.index"))

    return render_template(
        "sudungdichvu/invoice.html",
        thong_tin=chi_tiet[0],
        chi_tiet=chi_tiet,
        tong_tien=sum((row["ThanhTien"] or 0) for row in chi_tiet),
        ngay_in=datetime.now(),
        ma_hoa_don=f"HD-{ma_sv}-{datetime.now():%Y%m%d%H%M}",
    )


@sudungdichvu_bp.route("/them", methods=["POST"])
def them():
    try:
        service.create(
            request.form.get("ma_sv"),
            request.form.get("ma_dv"),
            request.form.get("thoi_gian"),
            request.form.get("so_luong")
        )
        flash("Thêm lượt sử dụng dịch vụ thành công!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Không thể thêm lượt sử dụng dịch vụ.", "danger")

    return redirect(url_for("sudungdichvu.index"))


@sudungdichvu_bp.route("/sua/<int:ma_sd>", methods=["POST"])
def sua(ma_sd):
    try:
        service.update(
            ma_sd,
            request.form.get("ma_sv"),
            request.form.get("ma_dv"),
            request.form.get("thoi_gian"),
            request.form.get("so_luong")
        )
        flash("Cập nhật thành công!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Không thể cập nhật lượt sử dụng.", "danger")

    return redirect(url_for("sudungdichvu.index"))


@sudungdichvu_bp.route("/xoa/<int:ma_sd>", methods=["POST"])
def xoa(ma_sd):
    try:
        service.delete(ma_sd)
        flash("Xóa lượt sử dụng thành công!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Không thể xóa lượt sử dụng.", "danger")

    return redirect(url_for("sudungdichvu.index"))
