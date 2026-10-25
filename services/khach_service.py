from datetime import datetime

from repositories import khach_repo


def _parse_date(value, required=False):
    if not value:
        if required:
            raise ValueError("Ngày đến không được để trống.")
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("Ngày sinh không hợp lệ.")


def _validate(so_cmt, ten, ngay_sinh):
    so_cmt = (so_cmt or "").strip()
    ten = (ten or "").strip()
    if not so_cmt or not ten:
        raise ValueError("Số CMT và tên khách không được để trống.")
    if len(so_cmt) > 15:
        raise ValueError("Số CMT không được dài quá 15 ký tự.")
    if len(ten) > 100:
        raise ValueError("Tên khách không được dài quá 100 ký tự.")
    return so_cmt, ten, _parse_date(ngay_sinh)


def get_all():
    return khach_repo.get_all()


def get_one(ma_khach):
    return khach_repo.get_one(ma_khach)


def create(so_cmt, ten, ngay_sinh):
    khach_repo.create(*_validate(so_cmt, ten, ngay_sinh))


def update(ma_khach, so_cmt, ten, ngay_sinh):
    if not khach_repo.get_one(ma_khach):
        raise ValueError("Không tìm thấy khách cần sửa.")
    khach_repo.update(ma_khach, *_validate(so_cmt, ten, ngay_sinh))


def delete(ma_khach):
    if not khach_repo.get_one(ma_khach):
        raise ValueError("Không tìm thấy khách cần xóa.")
    khach_repo.delete(ma_khach)
