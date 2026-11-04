from datetime import datetime, time, timedelta

from database.connection import get_db
from repositories.rules import ensure_open, lock_students, month_start

SELECT_ROWS = """
    SELECT lg.MaLuot,lg.BienSo,d.MaSV,sv.HoTen,lg.MaDKXe,
           lg.ThoiGianLay,lg.ThoiGianGui,lg.SoTien
    FROM LuotGuiXe lg JOIN DangKyXeThang d ON d.MaDKXe=lg.MaDKXe
    JOIN SinhVien sv ON sv.MaSV=d.MaSV
"""


def get_all():
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(SELECT_ROWS + " ORDER BY lg.ThoiGianGui DESC,lg.MaLuot DESC")
        return cur.fetchall()
    finally:
        cur.close()


def get_one(ma_luot):
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute(SELECT_ROWS + " WHERE lg.MaLuot=%s", (ma_luot,))
        return cur.fetchone()
    finally:
        cur.close()


def get_xe():
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute("SELECT x.*,sv.HoTen FROM Xe x JOIN SinhVien sv ON sv.MaSV=x.MaSV ORDER BY x.BienSo")
        return cur.fetchall()
    finally:
        cur.close()


def _ticket(cur, bien_so, sent):
    cur.execute("SELECT MaSV FROM Xe WHERE BienSo=%s", (bien_so,))
    car = cur.fetchone()
    if not car:
        raise ValueError("Xe không tồn tại.")
    lock_students(cur, car["MaSV"])
    cur.execute("SELECT BienSo FROM Xe WHERE BienSo=%s FOR UPDATE", (bien_so,))
    cur.fetchone()
    cur.execute(
        "SELECT MaDKXe,MaSV FROM DangKyXeThang WHERE BienSo=%s AND KyThang=%s AND TrangThai='active'",
        (bien_so, month_start(sent)),
    )
    ticket = cur.fetchone()
    if not ticket:
        raise ValueError("Xe chưa có vé tháng tại ngày gửi. Hãy đăng ký vé tháng trước.")
    ensure_open(cur, ticket["MaSV"], sent)
    return ticket


def _no_overlap(cur, bien_so, sent, taken, exclude=0):
    cur.execute("""
        SELECT MaLuot FROM LuotGuiXe WHERE BienSo=%s AND MaLuot<>%s
        AND ThoiGianGui<%s AND (ThoiGianLay IS NULL OR ThoiGianLay>%s) LIMIT 1
    """, (bien_so, exclude, taken or datetime(9999, 12, 31, 23, 59, 59), sent))
    if cur.fetchone():
        raise ValueError("Lượt gửi bị trùng thời gian với lượt khác; hãy ghi giờ lấy xe của lượt đang mở.")


def _recalculate(cur, bien_so, day):
    start = datetime.combine(day, time.min)
    cur.execute("""
        SELECT MaLuot,SoTien FROM LuotGuiXe
        WHERE BienSo=%s AND ThoiGianGui>=%s AND ThoiGianGui<%s
        ORDER BY ThoiGianGui,MaLuot FOR UPDATE
    """, (bien_so, start, start + timedelta(days=1)))
    for index, row in enumerate(cur.fetchall()):
        fee = 0 if index < 2 else 3000
        if row["SoTien"] != fee:
            cur.execute("UPDATE LuotGuiXe SET SoTien=%s WHERE MaLuot=%s", (fee, row["MaLuot"]))


def create(bien_so, thoi_gian_lay, thoi_gian_gui):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        ticket = _ticket(cur, bien_so, thoi_gian_gui)
        _no_overlap(cur, bien_so, thoi_gian_gui, thoi_gian_lay)
        cur.execute("""
            INSERT INTO LuotGuiXe(BienSo,MaDKXe,ThoiGianLay,ThoiGianGui,SoTien)
            VALUES(%s,%s,%s,%s,0)
        """, (bien_so, ticket["MaDKXe"], thoi_gian_lay, thoi_gian_gui))
        inserted = cur.lastrowid
        _recalculate(cur, bien_so, thoi_gian_gui.date())
        cur.execute("SELECT SoTien FROM LuotGuiXe WHERE MaLuot=%s", (inserted,))
        fee = cur.fetchone()["SoTien"]
        db.commit()
        return fee
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def update(ma_luot, bien_so, thoi_gian_lay, thoi_gian_gui):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(SELECT_ROWS + " WHERE lg.MaLuot=%s", (ma_luot,))
        old = cur.fetchone()
        if not old:
            raise ValueError("Không tìm thấy lượt gửi xe.")
        cur.execute("SELECT MaSV FROM Xe WHERE BienSo=%s", (bien_so,))
        new_car = cur.fetchone()
        if not new_car:
            raise ValueError("Không tìm thấy xe.")
        lock_students(cur, old["MaSV"], new_car["MaSV"])
        ensure_open(cur, old["MaSV"], old["ThoiGianGui"])
        ticket = _ticket(cur, bien_so, thoi_gian_gui)
        _no_overlap(cur, bien_so, thoi_gian_gui, thoi_gian_lay, ma_luot)
        cur.execute("""
            UPDATE LuotGuiXe SET BienSo=%s,MaDKXe=%s,ThoiGianLay=%s,ThoiGianGui=%s WHERE MaLuot=%s
        """, (bien_so, ticket["MaDKXe"], thoi_gian_lay, thoi_gian_gui, ma_luot))
        for plate, day in sorted({(old["BienSo"],old["ThoiGianGui"].date()),(bien_so,thoi_gian_gui.date())}):
            _recalculate(cur, plate, day)
        cur.execute("SELECT SoTien FROM LuotGuiXe WHERE MaLuot=%s", (ma_luot,))
        fee = cur.fetchone()["SoTien"]
        db.commit()
        return fee
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()


def delete(ma_luot):
    db = get_db()
    cur = db.cursor(dictionary=True)
    try:
        cur.execute(SELECT_ROWS + " WHERE lg.MaLuot=%s", (ma_luot,))
        old = cur.fetchone()
        if not old:
            raise ValueError("Không tìm thấy lượt gửi xe.")
        lock_students(cur, old["MaSV"])
        ensure_open(cur, old["MaSV"], old["ThoiGianGui"])
        cur.execute("DELETE FROM LuotGuiXe WHERE MaLuot=%s", (ma_luot,))
        _recalculate(cur, old["BienSo"], old["ThoiGianGui"].date())
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        cur.close()
