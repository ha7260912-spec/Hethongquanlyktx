from flask import Blueprint, redirect, url_for
from routes.auth_routes import login_required

bp = Blueprint("main", __name__)

@bp.route("/")
@login_required
def index():
    # Tạm thời chuyển hướng sang trang sinh viên
    return redirect(url_for("sinhvien.list_sv"))