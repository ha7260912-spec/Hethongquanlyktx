import re
from pathlib import Path

from database.connection import get_db

SOURCE = Path(__file__).resolve().parents[1] / "database" / "queries.sql"
TITLES = [
    "Tổng chi phí từng sinh viên theo tháng", "Dịch vụ theo sinh viên và khoảng ngày",
    "Khách đến thăm và số lần theo sinh viên", "Doanh thu tất cả dịch vụ trong tháng",
    "Phòng còn chỗ", "Phòng đã đầy", "Sinh viên chưa sử dụng dịch vụ",
    "Sinh viên dùng ít nhất hai loại dịch vụ", "Top 10 sinh viên chi tiêu dịch vụ",
    "Dịch vụ doanh thu cao nhất", "Khách đến thăm nhiều nhất", "Xe vượt lượt miễn phí",
    "Công nợ sinh viên", "Dịch vụ chưa được sử dụng",
]


def catalog():
    source = SOURCE.read_text(encoding="utf-8")
    headers = list(re.finditer(r"^-- (Q\d{2}) \| ([^\n]+) \| (month|range)\s*$", source, re.M))
    result = {}
    for index, match in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(source)
        result[match[1]] = {
            "key": match[1], "title": TITLES[index], "scope": match[3],
            "sql": source[match.end():end].strip().rstrip(";"),
        }
    return result


def run(key, first, next_day, start, end, student_id=""):
    queries = catalog()
    if key not in queries:
        raise ValueError("Mã truy vấn không hợp lệ.")
    cur = get_db().cursor(dictionary=True)
    try:
        cur.execute("SET @ky_thang=%s,@thang_sau=%s,@tu_ngay=%s,@den_ngay=%s,@ma_sv=CONVERT(%s USING utf8mb4) COLLATE utf8mb4_unicode_ci,@nam=%s",
                    (first,next_day,start,end,student_id,first.year))
        cur.execute(queries[key]["sql"])
        rows = cur.fetchall()
        return {**queries[key], "rows": rows, "columns": list(cur.column_names)}
    finally:
        cur.close()
