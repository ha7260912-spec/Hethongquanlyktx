from datetime import datetime
from repositories import sudungdichvu_repo as repo


def get_all():
    return repo.get_all()


def get_invoice(ma_sv):
    return repo.get_invoice((ma_sv or "").strip())


def get_sinhvien():
    return repo.get_sinhvien()


def get_dichvu():
    return repo.get_dichvu()


def validate(ma_sv, ma_dv, thoi_gian, so_luong):
    ma_sv = str(ma_sv).strip()
    ma_dv = str(ma_dv).strip()

    if not ma_sv or not ma_dv:
        raise ValueError("Vui lòng chọn sinh viên và dịch vụ.")

    try:
        so_luong = int(so_luong)
    except (ValueError, TypeError):
        raise ValueError("Số lượng phải là số nguyên.")

    if so_luong <= 0:
        raise ValueError("Số lượng phải lớn hơn 0.")

    try:
        thoi_gian = datetime.strptime(
            thoi_gian, "%Y-%m-%dT%H:%M"
        )
    except (ValueError, TypeError):
        raise ValueError("Thời gian sử dụng không hợp lệ.")

    return ma_sv, ma_dv, thoi_gian, so_luong


def create(ma_sv, ma_dv, thoi_gian, so_luong):
    data = validate(ma_sv, ma_dv, thoi_gian, so_luong)
    repo.create(*data)


def update(ma_sd, ma_sv, ma_dv, thoi_gian, so_luong):
    data = validate(ma_sv, ma_dv, thoi_gian, so_luong)
    repo.update(ma_sd, *data)


def delete(ma_sd):
    repo.delete(ma_sd)
