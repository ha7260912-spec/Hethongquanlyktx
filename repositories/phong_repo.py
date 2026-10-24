from database.connection import get_db

def get_all():
    cur = get_db().cursor(dictionary=True)
    cur.execute("""
        SELECT p.*, (SELECT COUNT(*) FROM DangKyPhong d WHERE d.SoPhong=p.SoPhong AND d.NgayKetThuc IS NULL) AS DangO
        FROM Phong p ORDER BY SoPhong
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

def create(data):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Phong VALUES (%s, %s, %s, %s)", 
                    (data["SoPhong"], data["LoaiPhong"], data["DonGia"], data["SoNguoiToiDa"]))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, "Mã phòng đã tồn tại!"
    finally:
        cur.close()