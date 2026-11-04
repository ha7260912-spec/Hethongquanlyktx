from database.connection import get_db
from repositories.rules import ensure_open, lock_students


def get_all(first):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute("""
            SELECT d.*,sv.HoTen FROM DangKyXeThang d
            JOIN SinhVien sv ON sv.MaSV=d.MaSV
            WHERE d.KyThang=%s ORDER BY sv.HoTen,d.BienSo
        """, (first,))
        return cur.fetchall()
    finally:
        cur.close()


def register(bien_so, first):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT MaSV,NgayDangKy FROM Xe WHERE BienSo=%s", (bien_so,))
        car = cur.fetchone()
        if not car:
            raise ValueError("Không tìm thấy xe.")
        lock_students(cur, car["MaSV"])
        ensure_open(cur, car["MaSV"], first)
        if first < car["NgayDangKy"].replace(day=1):
            raise ValueError("Không thể đăng ký vé trước tháng đăng ký xe.")
        cur.execute("SELECT MaDKXe,TrangThai FROM DangKyXeThang WHERE BienSo=%s AND KyThang=%s", (bien_so, first))
        existing = cur.fetchone()
        if existing and existing["TrangThai"] == "active":
            raise ValueError("Xe đã có vé tháng này.")
        cur.execute("""
            SELECT COUNT(*) AS c FROM DangKyXeThang
            WHERE MaSV=%s AND KyThang=%s AND TrangThai='active'
        """, (car["MaSV"], first))
        if cur.fetchone()["c"] >= 2:
            raise ValueError("Mỗi sinh viên tối đa 2 xe vé tháng trong một tháng.")
        if existing:
            cur.execute("UPDATE DangKyXeThang SET TrangThai='active' WHERE MaDKXe=%s", (existing["MaDKXe"],))
        else:
            cur.execute("""
                INSERT INTO DangKyXeThang(MaSV,BienSo,KyThang,DonGia)
                VALUES(%s,%s,%s,100000)
            """, (car["MaSV"], bien_so, first))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def cancel(ticket_id):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM DangKyXeThang WHERE MaDKXe=%s", (ticket_id,))
        ticket = cur.fetchone()
        if not ticket:
            raise ValueError("Không tìm thấy vé tháng.")
        lock_students(cur, ticket["MaSV"])
        ensure_open(cur, ticket["MaSV"], ticket["KyThang"])
        cur.execute("SELECT MaLuot FROM LuotGuiXe WHERE MaDKXe=%s LIMIT 1", (ticket_id,))
        if cur.fetchone():
            raise ValueError("Vé đã có lượt gửi xe, không được hủy.")
        cur.execute("UPDATE DangKyXeThang SET TrangThai='cancelled' WHERE MaDKXe=%s", (ticket_id,))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
