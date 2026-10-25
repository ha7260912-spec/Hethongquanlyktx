from database.connection import get_db


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT MaKhach, SoCMT, Ten, NgaySinh
            FROM Khach
            ORDER BY MaKhach DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()


def get_one(ma_khach):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT MaKhach, SoCMT, Ten, NgaySinh FROM Khach WHERE MaKhach = %s",
            (ma_khach,)
        )
        return cur.fetchone()
    finally:
        cur.close()


def create(so_cmt, ten, ngay_sinh):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO Khach (SoCMT, Ten, NgaySinh)
            VALUES (%s, %s, %s)
        """, (so_cmt, ten, ngay_sinh))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_khach, so_cmt, ten, ngay_sinh):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE Khach
            SET SoCMT = %s, Ten = %s, NgaySinh = %s
            WHERE MaKhach = %s
        """, (so_cmt, ten, ngay_sinh, ma_khach))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_khach):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM Khach WHERE MaKhach = %s", (ma_khach,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy khách cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
