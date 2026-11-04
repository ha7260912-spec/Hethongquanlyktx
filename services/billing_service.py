from datetime import date, datetime, timedelta

from repositories import billing_repo, report_repo


def current_period():
    today = date.today()
    return today.month, today.year


def parse_period(month, year):
    today = date.today()
    month = today.month if month in (None, "") else month
    year = today.year if year in (None, "") else year
    first, _ = billing_repo.period(month, year)
    return first.month, first.year


def get_invoice(ma_sv, month, year):
    month, year = parse_period(month, year)
    return billing_repo.get_student_invoice(ma_sv, month, year)


def save_invoice(ma_sv, month, year):
    month, year = parse_period(month, year)
    return billing_repo.save_invoice(ma_sv, month, year)


def get_invoices(month, year, status="", student_id=""):
    month, year = parse_period(month, year)
    return billing_repo.get_invoices(month, year, status, student_id), month, year


def generate_all(month, year):
    month, year = parse_period(month, year)
    first, next_day = billing_repo.period(month, year)
    candidates = report_repo.run("Q01", first, next_day, first, next_day)["rows"]
    for student in candidates:
        billing_repo.save_invoice(student["MaSV"], month, year)
    return len(candidates), month, year


def mark_paid(ma_hd):
    billing_repo.mark_paid(ma_hd)


def get_report(month, year, key="Q01", mode="month", start=None, end=None, student_id="", anchor=None):
    month, year = parse_period(month, year)
    first, next_day = billing_repo.period(month, year)
    if key not in report_repo.catalog():
        raise ValueError("Mã truy vấn không hợp lệ.")
    period_start, period_end = first, next_day
    if report_repo.catalog()[key]["scope"] == "range":
        try:
            if mode == "range":
                period_start = date.fromisoformat(start or "")
                period_end = date.fromisoformat(end or "") + timedelta(days=1)
            elif mode == "week":
                day = date.fromisoformat(anchor) if anchor else date.today()
                period_start = day - timedelta(days=day.weekday())
                period_end = period_start + timedelta(days=7)
            elif mode != "month":
                raise ValueError("Chế độ khoảng ngày không hợp lệ.")
        except (ValueError, OverflowError):
            raise ValueError("Hãy nhập đầy đủ khoảng ngày hợp lệ.")
        if period_start >= period_end:
            raise ValueError("Ngày bắt đầu phải không sau ngày kết thúc.")
    result = report_repo.run(key, first, next_day, period_start, period_end, (student_id or "").strip())
    return {
        **result, "month": month, "year": year, "start": period_start,
        "end": period_end - timedelta(days=1), "mode": mode, "student_id": student_id,
        "anchor": anchor or date.today().isoformat(), "catalog": report_repo.catalog(),
    }
