from repositories import phong_repo

def lay_danh_sach():
    return phong_repo.get_all()

def them_phong(data):
    # Validate dữ liệu cơ bản
    if not data.get("SoPhong"):
        return False, "Số phòng không được để trống!"
    if data.get("DonGia", 0) <= 0:
        return False, "Đơn giá phải lớn hơn 0!"
    if data.get("SoNguoiToiDa", 0) <= 0:
        return False, "Số người tối đa phải lớn hơn 0!"
    
    return phong_repo.create(data)