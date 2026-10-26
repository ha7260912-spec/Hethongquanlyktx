
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


def create(ten_dv, don_gia):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # Khóa danh sách mã trong cùng transaction để tránh trùng mã khi
        # có hai thao tác thêm dịch vụ xảy ra gần như cùng lúc.
        cursor.execute("SELECT MaDV FROM DichVu FOR UPDATE")
        max_number = 0
        for row in cursor.fetchall():
            ma_dv = str(row["MaDV"] or "")
            if ma_dv.upper().startswith("DV") and ma_dv[2:].isdigit():
                max_number = max(max_number, int(ma_dv[2:]))

        ma_dv = f"DV{max_number + 1:02d}"
        cursor.execute("""
            INSERT INTO DichVu (MaDV, TenDV, DonGia)
            VALUES (%s, %s, %s)
        """, (ma_dv, ten_dv, don_gia))
        db.commit()
        return ma_dv
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
