from flask import Blueprint, render_template, redirect, url_for, session
from routes.auth_routes import login_required  # Chỉ cần login_required, không dùng admin_required
from database.connection import get_db

bp = Blueprint("main", __name__)

@bp.route("/")
@login_required
def index():
    # Nếu là sinh viên thì đá về Cổng sinh viên, không cho vào Dashboard của Admin
    if session.get("role") == 'sinhvien':
        return redirect(url_for("sinhvien.portal"))

    try:
        db = get_db()
        cur = db.cursor(dictionary=True)
        
        # 1. Lấy các con số thống kê cơ bản
        cur.execute("SELECT COUNT(*) as c FROM SinhVien")
        sv = cur.fetchone()['c']
        
        cur.execute("SELECT COUNT(*) as c FROM Phong")
        phong = cur.fetchone()['c']
        
        cur.execute("SELECT COUNT(DISTINCT MaSV) as c FROM DangKyPhong WHERE NgayKetThuc IS NULL")
        dang_o = cur.fetchone()['c']
        
        # 2. Tính tổng sức chứa để vẽ biểu đồ tỷ lệ lấp đầy
        cur.execute("SELECT SUM(SoNguoiToiDa) as total_cap FROM Phong")
        total_cap = cur.fetchone()['total_cap'] or 1 # Tránh lỗi chia cho 0 nếu chưa có phòng
        occupancy_rate = round((dang_o / total_cap) * 100, 1)
        
        # 3. Lấy 5 hoạt động đăng ký phòng gần đây nhất
        cur.execute("""
            SELECT dk.MaSV, sv.HoTen, dk.SoPhong, dk.NgayBatDau 
            FROM DangKyPhong dk 
            JOIN SinhVien sv ON dk.MaSV = sv.MaSV 
            ORDER BY dk.MaDK DESC LIMIT 5
        """)
        recent_activities = cur.fetchall()
        
        cur.close()
        return render_template("index.html", 
                               stats={"sv": sv, "phong": phong, "dang_o": dang_o},
                               occupancy_rate=occupancy_rate,
                               total_cap=total_cap,
                               recent_activities=recent_activities)
    except Exception as e:
        return f"<h3>Có lỗi xảy ra khi tải Database: {e}</h3>"