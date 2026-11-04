from datetime import date

import mysql.connector
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from repositories import billing_repo, ticket_repo, xe_repo
from repositories.rules import error_message
from routes.auth_routes import login_required
from services.billing_service import parse_period

bp = Blueprint("ticket", __name__, url_prefix="/ve-xe")


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    source = request.form if request.method == "POST" else request.args
    try:
        month, year = parse_period(source.get("month"), source.get("year"))
        first, _ = billing_repo.period(month, year)
        if request.method == "POST":
            ticket_repo.register((source.get("BienSo") or "").strip(), first)
            flash("Đã đăng ký vé tháng, phí 100.000đ/xe.", "success")
            return redirect(url_for("ticket.index", month=month, year=year))
        return render_template("xe/tickets.html", tickets=ticket_repo.get_all(first), cars=xe_repo.get_all(), month=month, year=year)
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
        if request.method == "POST":
            return redirect(url_for("ticket.index"))
        return render_template("xe/tickets.html", tickets=[], cars=[], month=date.today().month, year=date.today().year), 400


@bp.route("/<int:ticket_id>/huy", methods=["POST"])
@login_required
def cancel(ticket_id):
    try:
        ticket_repo.cancel(ticket_id)
        flash("Đã hủy vé tháng chưa sử dụng.", "success")
    except (ValueError, mysql.connector.Error) as exc:
        flash(error_message(exc), "danger")
    return redirect(url_for("ticket.index", month=request.form.get("month"), year=request.form.get("year")))
