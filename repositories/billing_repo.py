from datetime import date
from decimal import Decimal

from database.connection import get_db
from repositories.rules import lock_students


def period(month, year):
    try:
        month, year = int(month), int(year)
    except (TypeError, ValueError):
        raise ValueError("Tháng và năm phải là số.")
    if not 1 <= month <= 12 or not 2000 <= year <= 2100:
        raise ValueError("Tháng phải từ 1–12, năm từ 2000–2100.")
    return date(year, month, 1), date(year + (month == 12), 1 if month == 12 else month + 1, 1)


def _student(cur, ma_sv):
    cur.execute("SELECT MaSV,HoTen,Lop,SoCMT FROM SinhVien WHERE MaSV=%s", (ma_sv,))
    return cur.fetchone()


def _stored(cur, student, header):
    cur.execute("""
        SELECT LoaiKhoan,MoTa,ThoiGian,SoLuong,DonGia,ThanhTien
        FROM ChiTietHoaDon WHERE MaHD=%s ORDER BY MaCT
    """, (header["MaHD"],))
    return {
        "student": student, "month": header["KyThang"].month, "year": header["KyThang"].year,
        "first_day": header["KyThang"], "details": cur.fetchall(), "total": header["TongTien"],
        "ma_hd": header["MaHD"], "trang_thai": header["TrangThai"], "persisted": True,
        "ngay_lap": header["NgayLap"], "ngay_thanh_toan": header["NgayThanhToan"],
    }


def _preview(cur, student, first, next_day):
    # One full monthly charge per distinct room; returning to the same room
    # within a month is not charged twice. A transfer incurs each room's fee.
    cur.execute("""
        SELECT dk.SoPhong,MAX(dk.DonGiaApDung) AS DonGia
        FROM DangKyPhong dk
        WHERE dk.MaSV=%s AND dk.NgayBatDau<%s
          AND (dk.NgayKetThuc IS NULL OR dk.NgayKetThuc>=%s)
        GROUP BY dk.SoPhong ORDER BY dk.SoPhong
    """, (student["MaSV"], next_day, first))
    details = [{
        "LoaiKhoan": "PHONG", "MoTa": f"Tiền phòng {r['SoPhong']}",
        "ThoiGian": None, "SoLuong": 1, "DonGia": r["DonGia"], "ThanhTien": r["DonGia"],
    } for r in cur.fetchall()]
    cur.execute("""
        SELECT v.LoaiKhoan,d.TenDV,v.ThamChieu,v.ThoiGian,v.SoLuong,v.DonGia,v.ThanhTien
        FROM v_phat_sinh_dich_vu v JOIN DichVu d ON d.MaDV=v.MaDV
        WHERE v.MaSV=%s AND v.ThoiGian>=%s AND v.ThoiGian<%s
        ORDER BY v.ThoiGian,v.LoaiKhoan,v.ThamChieu
    """, (student["MaSV"], first, next_day))
    for row in cur.fetchall():
        row["MoTa"] = row["TenDV"] + (f" · {row['ThamChieu']}" if row["LoaiKhoan"] != "DICH_VU" else "")
        details.append(row)
    return {
        "student": student, "month": first.month, "year": first.year, "first_day": first,
        "details": details, "total": sum((r["ThanhTien"] for r in details), Decimal("0")),
        "ma_hd": None, "trang_thai": "draft", "persisted": False,
    }


def get_student_invoice(ma_sv, month, year):
    first, next_day = period(month, year)
    cur = get_db().cursor(dictionary=True)
    try:
        student = _student(cur, ma_sv)
        if not student:
            return None
        cur.execute("SELECT * FROM HoaDon WHERE MaSV=%s AND KyThang=%s", (ma_sv, first))
        header = cur.fetchone()
        return _stored(cur, student, header) if header else _preview(cur, student, first, next_day)
    finally:
        cur.close()


def save_invoice(ma_sv, month, year):
    first, next_day = period(month, year)
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        lock_students(cur, ma_sv)
        student = _student(cur, ma_sv)
        cur.execute("SELECT * FROM HoaDon WHERE MaSV=%s AND KyThang=%s FOR UPDATE", (ma_sv, first))
        header = cur.fetchone()
        if header and header["TrangThai"] == "paid":
            result = _stored(cur, student, header)
            db.commit()
            return result
        preview = _preview(cur, student, first, next_day)
        if header:
            invoice_id = header["MaHD"]
            cur.execute("UPDATE HoaDon SET TongTien=%s WHERE MaHD=%s", (preview["total"], invoice_id))
            cur.execute("DELETE FROM ChiTietHoaDon WHERE MaHD=%s", (invoice_id,))
        else:
            cur.execute("INSERT INTO HoaDon(MaSV,KyThang,TongTien) VALUES(%s,%s,%s)", (ma_sv,first,preview["total"]))
            invoice_id = cur.lastrowid
        for row in preview["details"]:
            cur.execute("""
                INSERT INTO ChiTietHoaDon(MaHD,LoaiKhoan,MoTa,ThoiGian,SoLuong,DonGia,ThanhTien)
                VALUES(%s,%s,%s,%s,%s,%s,%s)
            """, (invoice_id,row["LoaiKhoan"],row["MoTa"],row["ThoiGian"],row["SoLuong"],row["DonGia"],row["ThanhTien"]))
        cur.execute("SELECT * FROM HoaDon WHERE MaHD=%s", (invoice_id,))
        result = _stored(cur, student, cur.fetchone())
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def get_invoices(month, year, status="", student_id=""):
    first, _ = period(month, year)
    if status not in ("", "unpaid", "paid", "overdue"):
        raise ValueError("Trạng thái hóa đơn không hợp lệ.")
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT hd.*,sv.HoTen,sv.Lop FROM HoaDon hd
            JOIN SinhVien sv ON sv.MaSV=hd.MaSV
            WHERE hd.KyThang=%s AND (%s='' OR hd.TrangThai=%s)
              AND (%s='' OR hd.MaSV=%s)
            ORDER BY sv.HoTen,hd.MaHD
        """, (first,status,status,student_id,student_id))
        return cur.fetchall()
    finally:
        cur.close()


def mark_paid(ma_hd):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaSV FROM HoaDon WHERE MaHD=%s", (ma_hd,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Không tìm thấy hóa đơn.")
        lock_students(cur, row["MaSV"])
        cur.execute("UPDATE HoaDon SET TrangThai='paid',NgayThanhToan=NOW() WHERE MaHD=%s AND TrangThai<>'paid'", (ma_hd,))
        if not cur.rowcount:
            raise ValueError("Hóa đơn đã thanh toán.")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
