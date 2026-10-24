from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.connection import get_db
from utils.security import hash_password
from functools import wraps

bp = Blueprint("auth", __name__, url_prefix="/auth")

# Hàm trang trí: Bắt buộc đăng nhập
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("Vui lòng đăng nhập!", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapper

# Hàm trang trí: Bắt buộc quyền Admin
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Bạn không có quyền thực hiện hành động này!", "danger")
            return redirect(url_for("sinhvien.list_sv"))
        return f(*args, **kwargs)
    return wrapper

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        cur = get_db().cursor(dictionary=True)
        cur.execute("SELECT * FROM Users WHERE username=%s AND password=%s", 
                    (username, hash_password(password)))
        user = cur.fetchone()
        cur.close()
        
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            session["hoten"] = user["HoTen"]
            flash(f"Xin chào {user['HoTen']}!", "success")
            return redirect(url_for("sinhvien.list_sv"))
        flash("Sai tài khoản hoặc mật khẩu!", "danger")
    return render_template("auth/login.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for("auth.login"))