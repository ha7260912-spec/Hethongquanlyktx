from database.connection import get_db
from datetime import date
from repositories.rules import lock_students


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT x.BienSo, x.MaSV, sv.HoTen, x.LoaiXe, x.NgayDangKy
            FROM Xe x
            JOIN SinhVien sv ON sv.MaSV = x.MaSV
            ORDER BY x.BienSo
        """)
        return cur.fetchall()
    finally:
        cur.close()


def get_one(bien_so):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT BienSo, MaSV, LoaiXe, NgayDangKy FROM Xe WHERE BienSo = %s",
            (bien_so,)
        )
        return cur.fetchone()
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


def create(bien_so, ma_sv, loai_xe, ngay_dang_ky=None):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        lock_students(cur, ma_sv)
        cur.execute("""
            INSERT INTO Xe (BienSo, MaSV, LoaiXe, NgayDangKy)
            VALUES (%s, %s, %s, %s)
        """, (bien_so, ma_sv, loai_xe, ngay_dang_ky or date.today()))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(bien_so, ma_sv, loai_xe):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaSV FROM Xe WHERE BienSo=%s", (bien_so,))
        old = cur.fetchone()
        if not old:
            raise ValueError("Không tìm thấy xe.")
        lock_students(cur, old["MaSV"], ma_sv)
        if old["MaSV"] != ma_sv:
            cur.execute("SELECT MaDKXe FROM DangKyXeThang WHERE BienSo=%s LIMIT 1", (bien_so,))
            if cur.fetchone():
                raise ValueError("Xe có lịch sử vé tháng, không được đổi chủ xe.")
        cur.execute("""
            UPDATE Xe
            SET MaSV = %s, LoaiXe = %s
            WHERE BienSo = %s
        """, (ma_sv, loai_xe, bien_so))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(bien_so):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Xe WHERE BienSo = %s", (bien_so,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy xe cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
