from repositories import xe_repo


def _validate(bien_so, ma_sv, loai_xe):
    bien_so = (bien_so or "").strip()
    ma_sv = (ma_sv or "").strip()
    loai_xe = (loai_xe or "").strip() or None
    if not bien_so or not ma_sv:
        raise ValueError("Biển số xe và sinh viên không được để trống.")
    if len(bien_so) > 15:
        raise ValueError("Biển số xe không được dài quá 15 ký tự.")
    if len(loai_xe or "") > 30:
        raise ValueError("Loại xe không được dài quá 30 ký tự.")
    return bien_so, ma_sv, loai_xe


def get_all():
    return xe_repo.get_all()


def get_one(bien_so):
    return xe_repo.get_one(bien_so)


def get_sinhvien():
    return xe_repo.get_sinhvien()


def create(bien_so, ma_sv, loai_xe):
    xe_repo.create(*_validate(bien_so, ma_sv, loai_xe))


def update(bien_so, ma_sv, loai_xe):
    if not xe_repo.get_one(bien_so):
        raise ValueError("Không tìm thấy xe cần sửa.")
    _, ma_sv, loai_xe = _validate(bien_so, ma_sv, loai_xe)
    xe_repo.update(bien_so, ma_sv, loai_xe)


def delete(bien_so):
    if not xe_repo.get_one(bien_so):
        raise ValueError("Không tìm thấy xe cần xóa.")
    xe_repo.delete(bien_so)
