from database.connection import get_db

def get_all():
    cur = get_db().cursor(dictionary=True)
    cur.execute("""
        SELECT dk.*, sv.HoTen, p.LoaiPhong FROM DangKyPhong dk 
        JOIN SinhVien sv ON dk.MaSV=sv.MaSV
        JOIN Phong p ON dk.SoPhong = p.SoPhong
        ORDER BY dk.MaDK DESC
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def create(data):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO DangKyPhong (MaSV, SoPhong, NgayBatDau, NgayKetThuc) VALUES (%s,%s,%s,%s)",
                    (data["MaSV"], data["SoPhong"], data["NgayBatDau"], data["NgayKetThuc"] or None))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        # ĐÂY LÀ NƠI BẮT LỖI TỪ TRIGGER "Phòng đã đầy"
        return False, str(e) 
    finally:
        cur.close()