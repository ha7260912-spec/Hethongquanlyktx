from repositories import dangkyphong_repo

def lay_danh_sach():
    return dangkyphong_repo.get_all()

def them_dang_ky(data):
    if not data.get("MaSV") or not data.get("SoPhong") or not data.get("NgayBatDau"):
        return False, "Vui lòng nhập đầy đủ Sinh viên, Phòng và Ngày bắt đầu!"
    
    # Gọi Repo (Lỗi Trigger phòng đầy sẽ được trả về từ đây)
    return dangkyphong_repo.create(data)