
from database.connection import get_db


def get_all():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT MaDV, TenDV, DonGia
            FROM DichVu
            ORDER BY MaDV
        """)
        return cursor.fetchall()
    finally:
        cursor.close()


def get_by_id(ma_dv):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT MaDV, TenDV, DonGia FROM DichVu WHERE MaDV = %s",
            (ma_dv,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()


def create(ma_dv, ten_dv, don_gia):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO DichVu (MaDV, TenDV, DonGia)
            VALUES (%s, %s, %s)
        """, (ma_dv, ten_dv, don_gia))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def update(ma_dv, ten_dv, don_gia):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE DichVu
            SET TenDV = %s, DonGia = %s
            WHERE MaDV = %s
        """, (ten_dv, don_gia, ma_dv))
        db.commit()
        return cursor.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()


def delete(ma_dv):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM DichVu WHERE MaDV = %s",
            (ma_dv,)
        )
        db.commit()
        return cursor.rowcount
    except Exception:
        db.rollback()
        raise
    finally:
        cursor.close()
