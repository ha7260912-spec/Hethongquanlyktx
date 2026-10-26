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

# Hàm trang trí: Bắt buộc quyền Admin (Chặn Sinh viên)
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Nếu không phải admin (ví dụ: sinh viên) thì đá về cổng sinh viên
        if session.get("role") != "admin":
            flash("Bạn không có quyền truy cập trang quản trị!", "danger")
            return redirect(url_for("sinhvien.portal"))
        return f(*args, **kwargs)
    return wrapper

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # ==========================================
        # 1. KIỂM TRA ADMIN (Bảng Users)
        # ==========================================
        cur.execute("SELECT * FROM Users WHERE username=%s AND password=%s", 
                    (username, hash_password(password)))
        user = cur.fetchone()
        
        if user:
            session["user"] = user["username"]
            session["role"] = user["role"] # Lúc này chỉ còn 'admin'
            session["hoten"] = user["HoTen"]
            flash(f"Xin chào Quản trị viên {user['HoTen']}!", "success")
            return redirect(url_for("main.index"))

        # ==========================================
        # 2. KIỂM TRA TÀI KHOẢN SINH VIÊN (Bảng SinhVien)
        # ==========================================
        cur.execute("SELECT * FROM SinhVien WHERE MaSV=%s AND Password=%s", 
                    (username, hash_password(password)))
        sv = cur.fetchone()
        
        if sv:
            session["user"] = sv["MaSV"]
            session["role"] = "sinhvien"
            session["hoten"] = sv["HoTen"]
            flash(f"Xin chào sinh viên {sv['HoTen']}!", "success")
            return redirect(url_for("sinhvien.portal"))
            
        # NẾU SAI TÀI KHOẢN
        cur.close()
        flash("Sai tài khoản hoặc mật khẩu!", "danger")
        
    return render_template("auth/login.html")

# ... (Giữ nguyên các hàm sinhvien_register, logout, change_password, forgot_password như cũ) ...
@bp.route("/sinhvien-register", methods=["GET", "POST"])
def sinhvien_register():
    if request.method == "POST":
        masv = request.form.get("masv", "").strip()
        socmt = request.form.get("socmt", "").strip()
        hoten = request.form.get("hoten", "").strip()
        ngaysinh = request.form.get("ngaysinh") or None
        lop = request.form.get("lop", "").strip()
        quequan = request.form.get("quequan", "").strip()
        password = request.form.get("password", "")

        if not masv or not socmt or not hoten or not password:
            flash("Vui lòng nhập đầy đủ các trường có dấu (*)!", "danger")
            return redirect(url_for("auth.sinhvien_register"))

        db = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM SinhVien WHERE MaSV=%s OR SoCMT=%s", (masv, socmt))
        if cur.fetchone():
            flash("Mã sinh viên hoặc Số CMT này đã được đăng ký!", "danger")
            cur.close()
            return redirect(url_for("auth.sinhvien_register"))

        try:
            cur.execute("""
                INSERT INTO SinhVien (MaSV, SoCMT, HoTen, NgaySinh, Lop, QueQuan, Password)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (masv, socmt, hoten, ngaysinh, lop, quequan, hash_password(password)))
            db.commit()
            flash("Đăng ký tài khoản thành công! Hãy đăng nhập.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.rollback()
            flash(f"Lỗi hệ thống: {str(e)}", "danger")
        finally:
            cur.close()

    return render_template("auth/sinhvien_register.html")

@bp.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for("auth.login"))

@bp.route("/doi-mat-khau", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_pass = request.form.get("old_password")
        new_pass = request.form.get("new_password")
        
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
            flash("Đổi mật khẩu thành công!", "success")
            return redirect(url_for("sinhvien.list_sv"))
        cur.close()
        
    return render_template("auth/change_password.html")

@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        cur.execute("SELECT * FROM Users WHERE username=%s", (username,))
        user = cur.fetchone()
        
        if user:
            new_pass = "123456"
            cur.execute("UPDATE Users SET password=%s WHERE username=%s", 
                        (hash_password(new_pass), username))
            db.commit()
            flash(f"Mật khẩu của bạn đã được đặt lại thành: {new_pass}.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Tên đăng nhập không tồn tại trong hệ thống!", "danger")
            
        cur.close()
        
    return render_template("auth/forgot_password.html")