from database.connection import get_db


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT t.MaTham, t.MaKhach, k.Ten AS TenKhach, k.SoCMT,
                   t.MaSV, sv.HoTen, t.NgayDenChoi
            FROM Tham t
            JOIN Khach k ON k.MaKhach = t.MaKhach
            JOIN SinhVien sv ON sv.MaSV = t.MaSV
            ORDER BY t.NgayDenChoi DESC, t.MaTham DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()


def get_one(ma_tham):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT MaTham, MaKhach, MaSV, NgayDenChoi FROM Tham WHERE MaTham = %s",
            (ma_tham,)
        )
        return cur.fetchone()
    finally:
        cur.close()


def get_khach():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaKhach, SoCMT, Ten FROM Khach ORDER BY Ten")
        return cur.fetchall()
    finally:
        cur.close()


def get_sinhvien():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaSV, HoTen FROM SinhVien ORDER BY HoTen")
        return cur.fetchall()
    finally:
        cur.close()


def create(ma_khach, ma_sv, ngay_den_choi):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO Tham (MaKhach, MaSV, NgayDenChoi)
            VALUES (%s, %s, %s)
        """, (ma_khach, ma_sv, ngay_den_choi))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_tham, ma_khach, ma_sv, ngay_den_choi):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE Tham
            SET MaKhach = %s, MaSV = %s, NgayDenChoi = %s
            WHERE MaTham = %s
        """, (ma_khach, ma_sv, ngay_den_choi, ma_tham))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_tham):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Tham WHERE MaTham = %s", (ma_tham,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy lượt thăm cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
