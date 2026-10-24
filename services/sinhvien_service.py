from repositories import sinhvien_repo
import math

def lay_danh_sach(search, page):
    per_page = 10
    rows, total = sinhvien_repo.get_all(search, page, per_page)
    total_pages = math.ceil(total / per_page)
    return rows, total_pages, page

def them_sinh_vien(data):
    if not data.get("MaSV") or not data.get("HoTen"):
        return False, "Mã SV và Họ tên không được để trống!"
    return sinhvien_repo.create(data)

def lay_chi_tiet(masv):
    return sinhvien_repo.get_one(masv)

def cap_nhat_sinh_vien(masv, data):
    return sinhvien_repo.update(masv, data)

def xoa_sinh_vien(masv):
    return sinhvien_repo.delete(masv)