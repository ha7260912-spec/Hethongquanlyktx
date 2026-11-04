from datetime import date

from database.connection import get_db
from repositories.rules import error_message, lock_students


def get_all():
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT dk.*,sv.HoTen,p.LoaiPhong FROM DangKyPhong dk
            JOIN SinhVien sv ON dk.MaSV=sv.MaSV JOIN Phong p ON dk.SoPhong=p.SoPhong
            ORDER BY dk.MaDK DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()


def create(data):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        start = date.fromisoformat(str(data.get("NgayBatDau") or ""))
        end = date.fromisoformat(str(data["NgayKetThuc"])) if data.get("NgayKetThuc") else None
        if end and end < start:
            raise ValueError("Ngày kết thúc không được trước ngày bắt đầu.")
        lock_students(cur, data["MaSV"])
        cur.execute("SELECT DonGia FROM Phong WHERE SoPhong=%s FOR UPDATE", (data["SoPhong"],))
        room = cur.fetchone()
        if not room:
            raise ValueError("Không tìm thấy phòng.")
        # The database trigger checks peak concurrent occupancy and overlapping
        # student registrations while this transaction holds the room lock.
        cur.execute("""
            INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung)
            VALUES(%s,%s,%s,%s,%s)
        """, (data["MaSV"],data["SoPhong"],start,end,room["DonGia"]))
        db.commit()
        return True, None
    except Exception as exc:
        db.rollback()
        return False, error_message(exc)
    finally:
        cur.close()


def end_registration(registration_id, end):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        end = date.fromisoformat(end or "")
        cur.execute("SELECT * FROM DangKyPhong WHERE MaDK=%s", (registration_id,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Không tìm thấy đăng ký phòng.")
        if end < row["NgayBatDau"]:
            raise ValueError("Ngày trả phòng không được trước ngày bắt đầu.")
        lock_students(cur, row["MaSV"])
        cur.execute("UPDATE DangKyPhong SET NgayKetThuc=%s WHERE MaDK=%s", (end,registration_id))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
