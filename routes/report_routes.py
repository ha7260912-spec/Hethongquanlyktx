import mysql.connector
from flask import Blueprint, current_app, flash, render_template, request

from repositories import report_repo
from routes.auth_routes import admin_required, login_required
from services import billing_service

bp = Blueprint("report", __name__, url_prefix="/bao-cao")


@bp.route("/")
@login_required
@admin_required
def index():
    try:
        report = billing_service.get_report(
            request.args.get("month"), request.args.get("year"),
            key=request.args.get("query", "Q01"), mode=request.args.get("mode", "month"),
            start=request.args.get("start"), end=request.args.get("end"),
            student_id=request.args.get("ma_sv", ""), anchor=request.args.get("anchor"),
        )
        return render_template("baocao/index.html", report=report)
    except ValueError as exc:
        flash(str(exc), "danger")
        status = 400
    except mysql.connector.Error:
        current_app.logger.exception("Không thể chạy truy vấn báo cáo")
        flash("Không thể truy vấn CSDL. Vui lòng kiểm tra kết nối và migration.", "danger")
        status = 503
    month, year = billing_service.current_period()
    return render_template("baocao/index.html", report={
        "catalog": report_repo.catalog(), "key": "Q01", "title": "Báo cáo",
        "scope": "month", "month": month, "year": year, "mode": "month",
        "start": None, "end": None, "anchor": "", "student_id": "",
        "rows": [], "columns": [], "sql": "",
    }), status
