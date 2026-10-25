from database.connection import get_db


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT x.BienSo, x.MaSV, sv.HoTen, x.LoaiXe
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
            "SELECT BienSo, MaSV, LoaiXe FROM Xe WHERE BienSo = %s",
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


def create(bien_so, ma_sv, loai_xe):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO Xe (BienSo, MaSV, LoaiXe)
            VALUES (%s, %s, %s)
        """, (bien_so, ma_sv, loai_xe))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(bien_so, ma_sv, loai_xe):
    db = get_db()
    cur = db.cursor()
    try:
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
