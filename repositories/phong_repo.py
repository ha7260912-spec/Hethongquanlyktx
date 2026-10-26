from database.connection import get_db

def get_all():
    cur = get_db().cursor(dictionary=True)
    # Đã sửa: Chỉ đếm những sinh viên có trạng thái 'Đã duyệt'
    cur.execute("""
        SELECT p.*, 
        (SELECT COUNT(*) FROM DangKyPhong d 
         WHERE d.SoPhong = p.SoPhong 
           AND d.NgayKetThuc IS NULL 
           AND d.TrangThai = 'Đã duyệt') AS DangO
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

def update(so_phong, data):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE Phong 
            SET LoaiPhong=%s, DonGia=%s, SoNguoiToiDa=%s 
            WHERE SoPhong=%s
        """, (data["LoaiPhong"], data["DonGia"], data["SoNguoiToiDa"], so_phong))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        cur.close()

def delete(so_phong):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM Phong WHERE SoPhong=%s", (so_phong,))
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        # Lỗi này sẽ bắt được từ Khóa ngoại (Foreign Key) nếu phòng đang có sinh viên ở
        return False, "Không thể xóa! Phòng này đang có dữ liệu đăng ký của sinh viên."
    finally:
        cur.close()