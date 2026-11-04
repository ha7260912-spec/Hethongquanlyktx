from database.connection import get_db
from repositories.rules import ensure_open, lock_students


def get_all():
    db = get_db()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT sd.MaSD, sd.MaSV, sv.HoTen,
               sd.MaDV, dv.TenDV,
               COALESCE(sd.DonGiaApDung, dv.DonGia) AS DonGia,
               sd.ThoiGianSuDung, sd.SoLuong,
               sd.SoLuong * COALESCE(sd.DonGiaApDung, dv.DonGia) AS ThanhTien
        FROM SuDungDichVu sd
        JOIN SinhVien sv ON sd.MaSV = sv.MaSV
        JOIN DichVu dv ON sd.MaDV = dv.MaDV
        ORDER BY sd.ThoiGianSuDung DESC, sd.MaSD DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows


def get_invoice(ma_sv, start=None, end=None):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        date_filter = ""
        params = [ma_sv]
        if start and end:
            date_filter = "AND sd.ThoiGianSuDung >= %s AND sd.ThoiGianSuDung < %s"
            params.extend([start, end])
        cur.execute("""
            SELECT sv.MaSV, sv.HoTen, sv.Lop, sv.SoCMT,
                   sd.MaSD, sd.ThoiGianSuDung, sd.SoLuong,
                   dv.MaDV, dv.TenDV,
                   COALESCE(sd.DonGiaApDung, dv.DonGia) AS DonGia,
                   sd.SoLuong * COALESCE(sd.DonGiaApDung, dv.DonGia) AS ThanhTien
            FROM SuDungDichVu sd
            JOIN SinhVien sv ON sv.MaSV = sd.MaSV
            JOIN DichVu dv ON dv.MaDV = sd.MaDV
            WHERE sd.MaSV = %s
            {date_filter}
            ORDER BY sd.ThoiGianSuDung ASC, sd.MaSD ASC
        """.format(date_filter=date_filter), params)
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
    cur.execute("SELECT MaDV, TenDV, DonGia FROM DichVu WHERE MaDV NOT IN ('XE_THANG','XE_PHAT') ORDER BY TenDV")
    rows = cur.fetchall()
    cur.close()
    return rows


def create(ma_sv, ma_dv, thoi_gian, so_luong):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        lock_students(cur, ma_sv)
        ensure_open(cur, ma_sv, thoi_gian)
        if ma_dv in ("XE_THANG", "XE_PHAT"):
            raise ValueError("Phí xe được ghi qua đăng ký vé/lượt xe.")
        cur.execute("SELECT DonGia FROM DichVu WHERE MaDV = %s", (ma_dv,))
        service = cur.fetchone()
        if not service:
            raise ValueError("Không tìm thấy dịch vụ.")
        cur.execute("""
            INSERT INTO SuDungDichVu
                (MaSV, MaDV, ThoiGianSuDung, SoLuong, DonGiaApDung)
            VALUES (%s, %s, %s, %s, %s)
        """, (ma_sv, ma_dv, thoi_gian, so_luong, service["DonGia"]))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_sd, ma_sv, ma_dv, thoi_gian, so_luong):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM SuDungDichVu WHERE MaSD=%s", (ma_sd,))
        old = cur.fetchone()
        if not old:
            raise ValueError("Không tìm thấy lượt sử dụng.")
        lock_students(cur, old["MaSV"], ma_sv)
        ensure_open(cur, old["MaSV"], old["ThoiGianSuDung"])
        ensure_open(cur, ma_sv, thoi_gian)
        if ma_dv in ("XE_THANG", "XE_PHAT"):
            raise ValueError("Phí xe được ghi qua đăng ký vé/lượt xe.")
        cur.execute("SELECT DonGia FROM DichVu WHERE MaDV = %s", (ma_dv,))
        service = cur.fetchone()
        if not service:
            raise ValueError("Không tìm thấy dịch vụ.")
        cur.execute("""
            UPDATE SuDungDichVu
            SET MaSV = %s, MaDV = %s,
                ThoiGianSuDung = %s, SoLuong = %s,
                DonGiaApDung = %s
            WHERE MaSD = %s
        """, (ma_sv, ma_dv, thoi_gian, so_luong,
              old["DonGiaApDung"] if old["MaDV"] == ma_dv else service["DonGia"], ma_sd))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_sd):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaSV,ThoiGianSuDung FROM SuDungDichVu WHERE MaSD=%s", (ma_sd,))
        old = cur.fetchone()
        if not old:
            raise ValueError("Không tìm thấy lượt sử dụng.")
        lock_students(cur, old["MaSV"])
        ensure_open(cur, old["MaSV"], old["ThoiGianSuDung"])
        cur.execute("DELETE FROM SuDungDichVu WHERE MaSD = %s", (ma_sd,))
        if cur.rowcount == 0:
            raise ValueError("Không tìm thấy bản ghi cần xóa.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
