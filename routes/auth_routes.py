import mysql.connector
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
        # .strip() giúp xóa dấu cách thừa nếu bạn gõ nhầm
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        cur = None
        try:
            cur = get_db().cursor(dictionary=True)
            cur.execute("SELECT * FROM Users WHERE username=%s AND password=%s",
                        (username, hash_password(password)))
            user = cur.fetchone()
        except mysql.connector.Error:
            flash("Chưa kết nối được cơ sở dữ liệu. Vui lòng cấu hình MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD và MYSQL_DB trên Render.", "danger")
            return render_template("auth/login.html")
        finally:
            if cur is not None:
                cur.close()
        
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"]
            session["hoten"] = user["HoTen"]
            flash(f"Xin chào {user['HoTen']}!", "success")
            return redirect(url_for("sinhvien.list_sv"))
            
        # Nếu sai, in thẳng ra màn hình web để dễ kiểm tra
        flash(f"Sai tài khoản! Bạn đã nhập: '{username}'", "danger")
        
    return render_template("auth/login.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for("auth.login"))

# Tính năng phụ: Đổi mật khẩu
@bp.route("/doi-mat-khau", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")

        cur = None
        try:
            db = get_db()
            cur = db.cursor(dictionary=True)

            cur.execute("SELECT * FROM Users WHERE username=%s AND password=%s",
                        (session["user"], hash_password(old_pass)))
            if not cur.fetchone():
                flash("Mật khẩu cũ không chính xác!", "danger")
            else:
                cur.execute("UPDATE Users SET password=%s WHERE username=%s",
                            (hash_password(new_pass), session["user"]))
                db.commit()
                flash("Đổi mật khẩu thành công! Hãy ghi nhớ mật khẩu mới.", "success")
                return redirect(url_for("sinhvien.list_sv"))
        except mysql.connector.Error:
            flash("Chưa kết nối được cơ sở dữ liệu. Vui lòng cấu hình các biến MYSQL_* trên Render.", "danger")
        finally:
            if cur is not None:
                cur.close()
        
    return render_template("auth/change_password.html")
# Tính năng phụ: Quên mật khẩu
@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()

        cur = None
        try:
            db = get_db()
            cur = db.cursor(dictionary=True)

            # Kiểm tra xem tài khoản có tồn tại không
            cur.execute("SELECT * FROM Users WHERE username=%s", (username,))
            user = cur.fetchone()

            if user:
                # Đặt lại mật khẩu mặc định là 123456
                new_pass = "123456"
                cur.execute("UPDATE Users SET password=%s WHERE username=%s",
                            (hash_password(new_pass), username))
                db.commit()
                flash(f"Mật khẩu của bạn đã được đặt lại thành: {new_pass}. Hãy đăng nhập lại!", "success")
                return redirect(url_for("auth.login"))
            else:
                flash("Tên đăng nhập không tồn tại trong hệ thống!", "danger")
        except mysql.connector.Error:
            flash("Chưa kết nối được cơ sở dữ liệu. Vui lòng cấu hình các biến MYSQL_* trên Render.", "danger")
        finally:
            if cur is not None:
                cur.close()
        
    return render_template("auth/forgot_password.html")
