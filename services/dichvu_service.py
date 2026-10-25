
from repositories import dichvu_repo


def get_all():
    return dichvu_repo.get_all()


def create(ma_dv, ten_dv, don_gia):
    ma_dv = ma_dv.strip()
    ten_dv = ten_dv.strip()

    if not ma_dv or not ten_dv:
        raise ValueError("Mã và tên dịch vụ không được để trống.")

    try:
        don_gia = int(don_gia)
    except (ValueError, TypeError):
        raise ValueError("Đơn giá phải là số nguyên.")

    if don_gia < 0:
        raise ValueError("Đơn giá không được âm.")

    if dichvu_repo.get_by_id(ma_dv):
        raise ValueError("Mã dịch vụ đã tồn tại.")

    dichvu_repo.create(ma_dv, ten_dv, don_gia)


def update(ma_dv, ten_dv, don_gia):
    ma_dv = ma_dv.strip()
    ten_dv = ten_dv.strip()

    if not ten_dv:
        raise ValueError("Tên dịch vụ không được để trống.")

    try:
        don_gia = int(don_gia)
    except (ValueError, TypeError):
        raise ValueError("Đơn giá phải là số nguyên.")

    if don_gia < 0:
        raise ValueError("Đơn giá không được âm.")

    if not dichvu_repo.get_by_id(ma_dv):
        raise ValueError("Không tìm thấy dịch vụ.")

    dichvu_repo.update(ma_dv, ten_dv, don_gia)


def delete(ma_dv):
    if not dichvu_repo.get_by_id(ma_dv):
        raise ValueError("Không tìm thấy dịch vụ.")

    dichvu_repo.delete(ma_dv)
