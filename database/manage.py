"""Database setup/migration tools: python -m database.manage --help."""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import mysql.connector

from config import Config, mysql_options

ROOT = Path(__file__).resolve().parent


def connect(database=None):
    return mysql.connector.connect(**mysql_options(database))


def statements(source):
    delimiter = ";"
    pending = []
    for line in source.splitlines():
        if line.strip().upper().startswith("DELIMITER "):
            delimiter = line.strip().split()[1]
            continue
        if line.lstrip().startswith("--") or not line.strip():
            continue
        # SQL comments begin with -- followed by whitespace. Preserve quoted
        # strings while stripping trailing comments from old sample scripts.
        quote = None
        clean = []
        index = 0
        while index < len(line):
            char = line[index]
            if quote:
                clean.append(char)
                if char == "\\" and index + 1 < len(line):
                    index += 1
                    clean.append(line[index])
                elif char == quote:
                    if index + 1 < len(line) and line[index + 1] == quote:
                        index += 1
                        clean.append(line[index])
                    else:
                        quote = None
            elif char in "'\"`":
                quote = char
                clean.append(char)
            elif line[index:index+2] == "--" and (index+2 == len(line) or line[index+2].isspace()):
                break
            else:
                clean.append(char)
            index += 1
        line = "".join(clean).rstrip()
        if not line.strip():
            continue
        pending.append(line)
        if line.rstrip().endswith(delimiter):
            yield "\n".join(pending).rstrip()[:-len(delimiter)].strip()
            pending = []
    if pending:
        raise ValueError("SQL statement is missing its terminator.")


def run_sql(connection, filename):
    cur = connection.cursor()
    try:
        for statement in statements((ROOT / filename).read_text(encoding="utf-8-sig")):
            cur.execute(statement)
            if cur.with_rows:
                cur.fetchall()
            while cur.nextset():
                if cur.with_rows:
                    cur.fetchall()
        connection.commit()
    finally:
        cur.close()


def backup(connection):
    """Keep schema, triggers and data before changing the existing database."""
    cur = connection.cursor()
    cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
    names = [r[0] for r in cur.fetchall()]
    snapshot = {"database": connection.database, "tables": {}, "triggers": []}
    for name in names:
        safe = name.replace("`", "``")
        cur.execute(f"SHOW CREATE TABLE `{safe}`")
        ddl = cur.fetchone()[1]
        cur.execute(f"SELECT * FROM `{safe}`")
        columns = list(cur.column_names)
        snapshot["tables"][name] = {"ddl": ddl, "columns": columns, "rows": cur.fetchall()}
    cur.execute("SHOW TRIGGERS")
    for row in cur.fetchall():
        safe = row[0].replace("`", "``")
        cur.execute(f"SHOW CREATE TRIGGER `{safe}`")
        snapshot["triggers"].append(cur.fetchone()[2])
    cur.close()
    target = ROOT / "backups" / f"{connection.database}-{datetime.now():%Y%m%d-%H%M%S-%f}.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(snapshot, default=str, ensure_ascii=False), encoding="utf-8")
    return target


def add_column(cur, table, column, definition):
    cur.execute(
        "SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() "
        "AND LOWER(TABLE_NAME)=LOWER(%s) AND COLUMN_NAME=%s", (table, column),
    )
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")


def migrate(connection):
    saved = backup(connection)
    print(f"Backup: {saved}")
    run_sql(connection, "migration_requirements.sql")
    cur = connection.cursor()
    # Drop only the three obsolete business triggers; domain.sql recreates their
    # replacements. No tables or user records are dropped.
    for trigger in ("trg_tinh_tien_gui_xe", "trg_check_xe_limit", "trg_check_phong_full"):
        cur.execute(f"DROP TRIGGER IF EXISTS `{trigger}`")
    add_column(cur, "Xe", "NgayDangKy", "DATE NULL")
    add_column(cur, "LuotGuiXe", "MaDKXe", "INT NULL")
    add_column(cur, "ChiTietHoaDon", "ThoiGian", "DATETIME NULL")
    cur.execute("""
        INSERT IGNORE INTO DangKyXeThang (MaSV, BienSo, KyThang, DonGia)
        SELECT DISTINCT x.MaSV, x.BienSo, DATE_FORMAT(lg.ThoiGianGui, '%Y-%m-01'), 100000
        FROM LuotGuiXe lg JOIN Xe x ON x.BienSo=lg.BienSo
        WHERE NOT EXISTS(SELECT 1 FROM DangKyXeThang d WHERE d.BienSo=x.BienSo
          AND d.KyThang=DATE_FORMAT(lg.ThoiGianGui,'%Y-%m-01'))
    """)
    cur.execute("""
        UPDATE Xe x SET NgayDangKy = LEAST(
            COALESCE((SELECT MIN(DATE(lg.ThoiGianGui)) FROM LuotGuiXe lg WHERE lg.BienSo=x.BienSo), CURDATE()),
            COALESCE((SELECT MIN(d.KyThang) FROM DangKyXeThang d WHERE d.BienSo=x.BienSo), CURDATE())
        ) WHERE x.NgayDangKy IS NULL
    """)
    cur.execute("ALTER TABLE Xe MODIFY COLUMN NgayDangKy DATE NOT NULL")
    cur.execute("""
        UPDATE LuotGuiXe lg JOIN DangKyXeThang d
          ON d.BienSo=lg.BienSo AND d.KyThang=DATE_FORMAT(lg.ThoiGianGui, '%Y-%m-01')
        SET lg.MaDKXe=d.MaDKXe WHERE lg.MaDKXe IS NULL
    """)
    cur.execute("SELECT COUNT(*) FROM LuotGuiXe WHERE MaDKXe IS NULL")
    if cur.fetchone()[0]:
        raise ValueError("Có lượt xe chưa khớp với vé tháng. Hãy kiểm tra dữ liệu trước khi tiếp tục.")
    cur.execute("ALTER TABLE LuotGuiXe MODIFY COLUMN MaDKXe INT NOT NULL")
    cur.execute("SELECT 1 FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)='dangkyxethang' AND INDEX_NAME='uq_ve_bienso_thang' LIMIT 1")
    if not cur.fetchone():
        cur.execute("ALTER TABLE DangKyXeThang ADD UNIQUE KEY uq_ve_bienso_thang(BienSo,KyThang)")
    cur.execute("SELECT 1 FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=DATABASE() AND LOWER(TABLE_NAME)='luotguixe' AND COLUMN_NAME='MaDKXe' AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1")
    if not cur.fetchone():
        cur.execute("ALTER TABLE LuotGuiXe ADD CONSTRAINT fk_luot_ve FOREIGN KEY(MaDKXe) REFERENCES DangKyXeThang(MaDKXe)")
    cur.close()
    connection.commit()
    run_sql(connection, "domain.sql")
    cur = connection.cursor()
    # Preserve paid invoices and their source records; normalize unbilled rows.
    cur.execute("""
        UPDATE LuotGuiXe lg
        JOIN (SELECT MaLuot, IF(ROW_NUMBER() OVER (
              PARTITION BY BienSo, DATE(ThoiGianGui) ORDER BY ThoiGianGui, MaLuot
            ) <= 2, 0, 3000) AS Phi FROM LuotGuiXe) ranked ON ranked.MaLuot=lg.MaLuot
        JOIN DangKyXeThang d ON d.MaDKXe=lg.MaDKXe
        LEFT JOIN HoaDon hd ON hd.MaSV=d.MaSV AND hd.KyThang=d.KyThang AND hd.TrangThai='paid'
        SET lg.SoTien=ranked.Phi WHERE hd.MaHD IS NULL
    """)
    cur.close()
    connection.commit()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["inspect", "backup", "migrate", "init"])
    parser.add_argument("--database", default=Config.MYSQL_DB)
    parser.add_argument("--sample", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]{1,64}", args.database):
        parser.error("Database name must contain only letters, digits and underscores.")
    if args.action == "init":
        connection = connect()
        cur = connection.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{args.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.database = args.database
        cur.execute("SHOW TABLES")
        if cur.fetchall():
            raise ValueError("init chỉ chạy trên database trống. Dùng migrate cho dữ liệu hiện có.")
        cur.close()
        run_sql(connection, "schema.sql")
        run_sql(connection, "domain.sql")
        if args.sample:
            run_sql(connection, "sample_data.sql")
    else:
        connection = connect(args.database)
        if args.action == "backup":
            print(backup(connection))
        elif args.action == "migrate":
            migrate(connection)
        else:
            cur = connection.cursor()
            cur.execute("SHOW FULL TABLES")
            print(json.dumps(cur.fetchall()))
            cur.execute("SHOW TRIGGERS")
            print("Triggers:", [r[0] for r in cur.fetchall()])
            cur.execute("SELECT TrangThai, COUNT(*) FROM HoaDon GROUP BY TrangThai")
            print("Invoices:", cur.fetchall())
            cur.close()
    connection.close()
    print("OK")


if __name__ == "__main__":
    main()
