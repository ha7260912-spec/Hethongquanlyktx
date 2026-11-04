from datetime import date, datetime


def month_start(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value).date()
    return date(value.year, value.month, 1)


def lock_students(cur, *student_ids):
    for student_id in sorted(set(student_ids)):
        cur.execute("SELECT MaSV FROM SinhVien WHERE MaSV=%s FOR UPDATE", (student_id,))
        if not cur.fetchone():
            raise ValueError("Sinh viên không tồn tại.")


def ensure_open(cur, student_id, value):
    cur.execute(
        "SELECT MaHD FROM HoaDon WHERE MaSV=%s AND KyThang=%s AND TrangThai='paid'",
        (student_id, month_start(value)),
    )
    if cur.fetchone():
        raise ValueError("Tháng này đã thanh toán. Không được thay đổi dữ liệu tính tiền.")


def error_message(exc):
    return getattr(exc, "msg", None) or str(exc)
