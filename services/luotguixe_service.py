from datetime import datetime, timedelta

from repositories import luotguixe_repo


DAILY_FEE = 3000


def _parse_datetime(value, required=False):
    if not value:
        if required:
            raise ValueError("Thời gian gửi xe không được để trống.")
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError):
        raise ValueError("Thời gian gửi xe không hợp lệ.")


def _covered_days(thoi_gian_gui, thoi_gian_lay):
    """Các ngày mà một lượt gửi xe chiếm chỗ, tính cả ngày vào và ngày ra."""
    ngay_cuoi = (thoi_gian_lay or thoi_gian_gui).date()
    ngay = thoi_gian_gui.date()
    days = set()
    while ngay <= ngay_cuoi:
        days.add(ngay)
        ngay += timedelta(days=1)
    return days


def _calculate_fee(bien_so, thoi_gian_gui, thoi_gian_lay, existing_rows, exclude_id=None):
    """Tính 3.000đ cho mỗi ngày mới của cùng một biển số.

    Nếu xe đã có lượt khác chiếm cùng ngày thì ngày đó không tính thêm,
    nên lượt thứ hai trong ngày sẽ miễn phí.
    """
    occupied_days = set()
    for row in existing_rows:
        if row.get("MaLuot") == exclude_id or row.get("BienSo") != bien_so:
            continue
        occupied_days.update(
            _covered_days(row["ThoiGianGui"], row.get("ThoiGianLay"))
        )

    new_days = _covered_days(thoi_gian_gui, thoi_gian_lay) - occupied_days
    return DAILY_FEE * len(new_days)


def _recalculate_rows(rows):
    """Hiển thị đúng quy tắc mới cả với dữ liệu cũ đang lưu trong bảng."""
    occupied_by_vehicle = {}
    ordered_rows = sorted(
        rows,
        key=lambda row: (
            row["BienSo"], row["ThoiGianGui"], row["MaLuot"]
        )
    )
    for row in ordered_rows:
        occupied_days = occupied_by_vehicle.setdefault(row["BienSo"], set())
        days = _covered_days(row["ThoiGianGui"], row.get("ThoiGianLay"))
        row["SoTien"] = DAILY_FEE * len(days - occupied_days)
        occupied_days.update(days)
    return rows


def _validate(bien_so, thoi_gian_lay, thoi_gian_gui):
    bien_so = (bien_so or "").strip()
    if not bien_so:
        raise ValueError("Vui lòng chọn biển số xe.")

    thoi_gian_lay = _parse_datetime(thoi_gian_lay)
    thoi_gian_gui = _parse_datetime(thoi_gian_gui, required=True)
    if thoi_gian_lay and thoi_gian_lay < thoi_gian_gui:
        raise ValueError("Giờ ra không được sớm hơn giờ vào.")

    return bien_so, thoi_gian_lay, thoi_gian_gui


def get_all():
    return _recalculate_rows(luotguixe_repo.get_all())


def get_one(ma_luot):
    row = luotguixe_repo.get_one(ma_luot)
    if not row:
        return None
    row["SoTien"] = _calculate_fee(
        row["BienSo"], row["ThoiGianGui"], row.get("ThoiGianLay"),
        luotguixe_repo.get_all(), exclude_id=ma_luot
    )
    return row


def get_xe():
    return luotguixe_repo.get_xe()


def create(bien_so, thoi_gian_lay, thoi_gian_gui):
    bien_so, thoi_gian_lay, thoi_gian_gui = _validate(
        bien_so, thoi_gian_lay, thoi_gian_gui
    )
    fee = _calculate_fee(
        bien_so, thoi_gian_gui, thoi_gian_lay,
        luotguixe_repo.get_all()
    )
    luotguixe_repo.create(bien_so, thoi_gian_lay, thoi_gian_gui, fee)
    return fee


def update(ma_luot, bien_so, thoi_gian_lay, thoi_gian_gui):
    if not luotguixe_repo.get_one(ma_luot):
        raise ValueError("Không tìm thấy lượt gửi xe cần sửa.")
    bien_so, thoi_gian_lay, thoi_gian_gui = _validate(
        bien_so, thoi_gian_lay, thoi_gian_gui
    )
    fee = _calculate_fee(
        bien_so, thoi_gian_gui, thoi_gian_lay,
        luotguixe_repo.get_all(), exclude_id=ma_luot
    )
    luotguixe_repo.update(
        ma_luot, bien_so, thoi_gian_lay, thoi_gian_gui, fee
    )
    return fee


def delete(ma_luot):
    if not luotguixe_repo.get_one(ma_luot):
        raise ValueError("Không tìm thấy lượt gửi xe cần xóa.")
    luotguixe_repo.delete(ma_luot)
