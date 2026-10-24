from database.connection import get_db

def get_all(search="", page=1, per_page=10):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    offset = (page - 1) * per_page
    
    sql = "SELECT * FROM SinhVien WHERE MaSV LIKE %s OR HoTen LIKE %s ORDER BY MaSV LIMIT %s OFFSET %s"
    params = (f"%{search}%", f"%{search}%", per_page, offset)
    cur.execute(sql, params)
    rows = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) as total FROM SinhVien WHERE MaSV LIKE %s OR HoTen LIKE %s", (f"%{search}%", f"%{search}%"))
    total = cur.fetchone()['total']
    cur.close()
    return rows, total

def get_one(masv):
    cur = get_db().cursor(dictionary=True)
    cur.execute("SELECT * FROM SinhVien WHERE MaSV=%s", (masv,))
    row = cur.fetchone()
    cur.close()
    return row

def create(data):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO SinhVien (MaSV, SoCMT, HoTen, NgaySinh, Lop, QueQuan) VALUES (%s,%s,%s,%s,%s,%s)",
                    (data["MaSV"], data["SoCMT"], data["HoTen"], data["NgaySinh"], data["Lop"], data["QueQuan"]))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, "Mã SV hoặc CMT đã tồn tại!"
    finally:
        cur.close()

def update(masv, data):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("UPDATE SinhVien SET SoCMT=%s, HoTen=%s, NgaySinh=%s, Lop=%s, QueQuan=%s WHERE MaSV=%s",
                    (data["SoCMT"], data["HoTen"], data["NgaySinh"], data["Lop"], data["QueQuan"], masv))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()

def delete(masv):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM SinhVien WHERE MaSV=%s", (masv,))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, "Không thể xóa! Sinh viên này đang có dữ liệu ràng buộc."
    finally:
        cur.close()