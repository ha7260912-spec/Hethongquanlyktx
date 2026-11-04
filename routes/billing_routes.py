import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from repositories.rules import error_message
from routes.auth_routes import admin_required, login_required
from services import billing_service

bp = Blueprint("billing", __name__, url_prefix="/hoa-don")


@bp.route("/")
@login_required
def index():
    status = request.args.get("status", "")
    student_id = request.args.get("ma_sv", "").strip()
    try:
        invoices, month, year = billing_service.get_invoices(
            request.args.get("month"), request.args.get("year"), status, student_id,
        )
        return render_template("hoadon/list.html", invoices=invoices,month=month,year=year,status=status,student_id=student_id)
    except ValueError as exc:
        flash(str(exc), "danger")
        code = 400
    except mysql.connector.Error:
        current_app.logger.exception("Không thể tải hóa đơn")
        flash("Không thể tải hóa đơn. Hãy kiểm tra kết nối CSDL.", "danger")
        code = 503
    month, year = billing_service.current_period()
    return render_template("hoadon/list.html",invoices=[],month=month,year=year,status="",student_id=""), code


@bp.route("/tao-tat-ca", methods=["POST"])
@login_required
@admin_required
def tao_tat_ca():
    try:
        count, month, year = billing_service.generate_all(request.form.get("month"),request.form.get("year"))
        flash(f"Đã xử lý {count} hóa đơn tháng {month:02d}/{year}; hóa đơn đã thanh toán được giữ nguyên.", "success")
        return redirect(url_for("billing.index",month=month,year=year))
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
        return redirect(url_for("billing.index"))


@bp.route("/<path:ma_sv>")
@login_required
def detail(ma_sv):
    try:
        invoice = billing_service.get_invoice(ma_sv,request.args.get("month"),request.args.get("year"))
        if not invoice:
            flash("Không tìm thấy sinh viên.", "warning")
            return redirect(url_for("billing.index"))
        return render_template("hoadon/detail.html",invoice=invoice)
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
        return redirect(url_for("billing.index"))


@bp.route("/<path:ma_sv>/tao", methods=["POST"])
@login_required
@admin_required
def save(ma_sv):
    try:
        invoice = billing_service.save_invoice(ma_sv,request.form.get("month"),request.form.get("year"))
        flash("Hóa đơn đã thanh toán được giữ nguyên." if invoice["trang_thai"] == "paid" else "Đã lưu chi tiết hóa đơn.", "success")
        return redirect(url_for("billing.detail",ma_sv=ma_sv,month=invoice["month"],year=invoice["year"]))
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
        return redirect(url_for("billing.index"))


@bp.route("/<int:ma_hd>/thanh-toan", methods=["POST"])
@login_required
@admin_required
def mark_paid(ma_hd):
    try:
        billing_service.mark_paid(ma_hd)
        flash("Đã thanh toán; hóa đơn và dữ liệu tính tiền của tháng được khóa.", "success")
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for("billing.index",month=request.form.get("month"),year=request.form.get("year")))
