from database.connection import get_db


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT lg.MaLuot, lg.BienSo, x.MaSV, sv.HoTen,
                   lg.ThoiGianLay, lg.ThoiGianGui, lg.SoTien
            FROM LuotGuiXe lg
            JOIN Xe x ON x.BienSo = lg.BienSo
            JOIN SinhVien sv ON sv.MaSV = x.MaSV
            ORDER BY lg.ThoiGianGui DESC, lg.MaLuot DESC
        """)
        return cur.fetchall()
    finally:
        cur.close()


def get_one(ma_luot):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT MaLuot, BienSo, ThoiGianLay, ThoiGianGui, SoTien
            FROM LuotGuiXe
            WHERE MaLuot = %s
        """, (ma_luot,))
        return cur.fetchone()
    finally:
        cur.close()


def get_xe():
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


def create(bien_so, thoi_gian_lay, thoi_gian_gui, so_tien):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO LuotGuiXe
                (BienSo, ThoiGianLay, ThoiGianGui, SoTien)
            VALUES (%s, %s, %s, %s)
        """, (bien_so, thoi_gian_lay, thoi_gian_gui, so_tien))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_luot, bien_so, thoi_gian_lay, thoi_gian_gui, so_tien):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE LuotGuiXe
            SET BienSo = %s, ThoiGianLay = %s,
                ThoiGianGui = %s, SoTien = %s
            WHERE MaLuot = %s
        """, (bien_so, thoi_gian_lay, thoi_gian_gui, so_tien, ma_luot))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_luot):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM LuotGuiXe WHERE MaLuot = %s", (ma_luot,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy lượt gửi xe cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
