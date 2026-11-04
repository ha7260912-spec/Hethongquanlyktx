from datetime import datetime

from repositories import luotguixe_repo


def _parse_datetime(value, required=False):
    if not value and not required:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (ValueError, TypeError):
        raise ValueError("Thời gian gửi/lấy xe không hợp lệ.")


def _validate(bien_so, thoi_gian_lay, thoi_gian_gui):
    bien_so = (bien_so or "").strip().upper()
    if not bien_so:
        raise ValueError("Vui lòng chọn biển số xe.")
    sent = _parse_datetime(thoi_gian_gui, required=True)
    taken = _parse_datetime(thoi_gian_lay)
    if taken and taken < sent:
        raise ValueError("Giờ lấy xe không được sớm hơn giờ gửi.")
    return bien_so, taken, sent


def get_all():
    return luotguixe_repo.get_all()


def get_one(ma_luot):
    return luotguixe_repo.get_one(ma_luot)


def get_xe():
    return luotguixe_repo.get_xe()


def create(bien_so, thoi_gian_lay, thoi_gian_gui):
    return luotguixe_repo.create(*_validate(bien_so, thoi_gian_lay, thoi_gian_gui))


def update(ma_luot, bien_so, thoi_gian_lay, thoi_gian_gui):
    return luotguixe_repo.update(ma_luot, *_validate(bien_so, thoi_gian_lay, thoi_gian_gui))


def delete(ma_luot):
    luotguixe_repo.delete(ma_luot)
