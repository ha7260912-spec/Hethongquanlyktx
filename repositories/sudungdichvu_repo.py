from database.connection import get_db


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT sd.MaSD, sd.MaSV, sv.HoTen,
               sd.MaDV, dv.TenDV, dv.DonGia,
               sd.ThoiGianSuDung, sd.SoLuong,
               sd.SoLuong * dv.DonGia AS ThanhTien
        FROM SuDungDichVu sd
        JOIN SinhVien sv ON sd.MaSV = sv.MaSV
        JOIN DichVu dv ON sd.MaDV = dv.MaDV
        ORDER BY sd.ThoiGianSuDung DESC, sd.MaSD DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def get_invoice(ma_sv):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT sv.MaSV, sv.HoTen, sv.Lop, sv.SoCMT,
                   sd.MaSD, sd.ThoiGianSuDung, sd.SoLuong,
                   dv.MaDV, dv.TenDV, dv.DonGia,
                   sd.SoLuong * dv.DonGia AS ThanhTien
            FROM SuDungDichVu sd
            JOIN SinhVien sv ON sv.MaSV = sd.MaSV
            JOIN DichVu dv ON dv.MaDV = sd.MaDV
            WHERE sd.MaSV = %s
            ORDER BY sd.ThoiGianSuDung ASC, sd.MaSD ASC
        """, (ma_sv,))
        return cur.fetchall()
    finally:
        cur.close()


def get_sinhvien():
    cur = get_db().cursor(dictionary=True)
    cur.execute("SELECT MaSV, HoTen FROM SinhVien ORDER BY HoTen")
    rows = cur.fetchall()
    cur.close()
    return rows


def get_dichvu():
    cur = get_db().cursor(dictionary=True)
    cur.execute("SELECT MaDV, TenDV, DonGia FROM DichVu ORDER BY TenDV")
    rows = cur.fetchall()
    cur.close()
    return rows


def create(ma_sv, ma_dv, thoi_gian, so_luong):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            INSERT INTO SuDungDichVu
                (MaSV, MaDV, ThoiGianSuDung, SoLuong)
            VALUES (%s, %s, %s, %s)
        """, (ma_sv, ma_dv, thoi_gian, so_luong))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_sd, ma_sv, ma_dv, thoi_gian, so_luong):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("""
            UPDATE SuDungDichVu
            SET MaSV = %s, MaDV = %s,
                ThoiGianSuDung = %s, SoLuong = %s
            WHERE MaSD = %s
        """, (ma_sv, ma_dv, thoi_gian, so_luong, ma_sd))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy bản ghi cần sửa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_sd):
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM SuDungDichVu WHERE MaSD = %s", (ma_sd,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy bản ghi cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
