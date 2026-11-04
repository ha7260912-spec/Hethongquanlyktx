"""Render the real templates with sample data, without a MySQL connection."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flask import render_template

from application import create_app


app = create_app()
student = {"MaSV": "SV01", "HoTen": "Sinh viên mẫu"}
service = {"MaDV": "DV01", "TenDV": "Giặt là", "DonGia": 15000}
usage = {
    **student,
    **service,
    "MaSD": 1,
    "ThoiGianSuDung": datetime(2026, 10, 27, 8),
    "SoLuong": 1,
    "ThanhTien": 15000,
}

with app.test_request_context("/"):
    from flask import session

    session.update(user="admin", role="admin", hoten="Quản trị viên")
    pages = {
        "usage": render_template(
            "sudungdichvu/list.html",
            danh_sach=[usage],
            sinh_vien=[student],
            dich_vu=[service],
        ),
        "services": render_template("dichvu/list.html", danh_sach=[service]),
        "student": render_template("sinhvien/form.html", action="Thêm", sv=None),
    }

sys.stdout.reconfigure(encoding="utf-8")
print(json.dumps(pages, ensure_ascii=False))
