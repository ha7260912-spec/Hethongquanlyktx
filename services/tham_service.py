from datetime import datetime

from repositories import tham_repo


def _parse_date(value):
    try:
        return datetime.strptime(value or "", "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Ngày đến chơi không hợp lệ.")


def _validate(ma_khach, ma_sv, ngay_den_choi):
    if not ma_khach or not ma_sv:
        raise ValueError("Vui lòng chọn khách và sinh viên được thăm.")
    return int(ma_khach), ma_sv.strip(), _parse_date(ngay_den_choi)


def get_all():
    return tham_repo.get_all()


def get_one(ma_tham):
    return tham_repo.get_one(ma_tham)


def get_khach():
    return tham_repo.get_khach()


def get_sinhvien():
    return tham_repo.get_sinhvien()


def create(ma_khach, ma_sv, ngay_den_choi):
    tham_repo.create(*_validate(ma_khach, ma_sv, ngay_den_choi))


def update(ma_tham, ma_khach, ma_sv, ngay_den_choi):
    if not tham_repo.get_one(ma_tham):
        raise ValueError("Không tìm thấy lượt thăm cần sửa.")
    tham_repo.update(ma_tham, *_validate(ma_khach, ma_sv, ngay_den_choi))


def delete(ma_tham):
    if not tham_repo.get_one(ma_tham):
        raise ValueError("Không tìm thấy lượt thăm cần xóa.")
    tham_repo.delete(ma_tham)
