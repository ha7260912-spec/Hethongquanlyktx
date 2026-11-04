"""One-off local UI to transfer the configured database to an EMPTY cloud schema.

Run: python -m deployment.transfer
Credentials are submitted only to a loopback listener and never logged or saved.
"""
import secrets
import tempfile
from collections import Counter
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import mysql.connector
from config import Config, mysql_options
from database.manage import run_sql
from repositories.report_repo import catalog

TABLES = ("Users", "SinhVien", "Phong", "DichVu", "Khach", "Xe", "DangKyPhong",
          "SuDungDichVu", "Tham", "DangKyXeThang", "LuotGuiXe", "HoaDon", "ChiTietHoaDon")


def copy_data(target, verify_only=False):
    source = mysql.connector.connect(**mysql_options(Config.MYSQL_DB))
    cur = target.cursor()
    locked = False
    try:
        cur.execute("SELECT GET_LOCK('ktx_transfer',60)")
        locked = cur.fetchone()[0] == 1
        if not locked:
            raise ValueError("Another transfer is running.")
        cur.execute("SHOW FULL TABLES")
        existing = cur.fetchall()
        if existing and not verify_only:
            raise ValueError("Target is not empty. Transfer refused; no existing data was changed.")
        source.start_transaction(isolation_level="REPEATABLE READ", consistent_snapshot=True, readonly=True)
        reader = source.cursor()
        snapshots = {}
        try:
            for table in TABLES:
                reader.execute(f"SELECT * FROM `{table}`")
                snapshots[table] = (tuple(reader.column_names), reader.fetchall())
            if not verify_only:
                run_sql(target, "schema.sql")
            counts = {}
            for table, (columns, rows) in snapshots.items():
                column_sql = ",".join(f"`{name.replace('`','``')}`" for name in columns)
                placeholders = ",".join(["%s"] * len(columns))
                if rows and not verify_only:
                    cur.executemany(f"INSERT INTO `{table}` ({column_sql}) VALUES ({placeholders})", rows)
                cur.execute(f"SELECT COUNT(*) FROM `{table}`")
                counts[table] = cur.fetchone()[0]
                if counts[table] != len(rows):
                    raise ValueError(f"Row count mismatch for {table}.")
                if verify_only:
                    cur.execute(f"SELECT {column_sql} FROM `{table}`")
                    if Counter(cur.fetchall()) != Counter(rows):
                        raise ValueError(f"Table data mismatch for {table}.")
            if not verify_only:
                target.commit()
                run_sql(target, "domain.sql")
            for first, end in ((date(2024,10,1),date(2024,11,1)),
                               (date(2026,10,1),date(2026,11,1))):
                for query in catalog().values():
                    results = []
                    for connection in (source, target):
                        check = connection.cursor()
                        try:
                            check.execute("SET @ky_thang=%s,@thang_sau=%s,@tu_ngay=%s,@den_ngay=%s,@ma_sv=CONVERT('' USING utf8mb4) COLLATE utf8mb4_unicode_ci", (first,end,first,end))
                            check.execute(query["sql"])
                            results.append(Counter(check.fetchall()))
                        finally:
                            check.close()
                    if results[0] != results[1]:
                        raise ValueError(f"Report mismatch: {query['key']} for {first}.")
            return counts
        finally:
            reader.close()
    finally:
        source.rollback()
        source.close()
        if locked:
            cur.execute("SELECT RELEASE_LOCK('ktx_transfer')")
            cur.fetchone()
        cur.close()


def main():
    token = secrets.token_urlsafe(24)
    route = "/" + token
    state = {"done": False, "message": ""}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def respond(self, content, status=200):
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(("<!doctype html><meta charset=utf-8><title>KTX cloud transfer</title>"
                "<style>body{font:16px system-ui;max-width:720px;margin:40px auto}label{display:block;margin:12px 0}input,textarea{display:block;width:100%;padding:8px;box-sizing:border-box}button{padding:12px}</style>" + content).encode())

        def do_GET(self):
            if self.path != route:
                return self.respond("Not found",404)
            if state["done"]:
                return self.respond(state["message"])
            self.respond("<h1>Transfer ql_ktx to empty cloud database</h1><p>The local database is read-only. Existing target data is never overwritten.</p><form method=post>"
                "<label>Host<input name=host required></label><label>Port<input name=port type=number required></label>"
                "<label>Database<input name=database required></label><label>User<input name=user required></label>"
                "<label>Password<input name=password type=password required autocomplete=off></label>"
                "<label>CA certificate<textarea name=ca rows=8 required></textarea></label>"
                "<button name=action value=copy>Transfer and verify</button> "
                "<button name=action value=verify>Verify existing transfer</button></form>")

        def do_POST(self):
            if self.path != route or state["done"]:
                return self.respond("Not available",409)
            expected_origin = f"http://127.0.0.1:{self.server.server_port}"
            if self.headers.get("Origin") != expected_origin:
                return self.respond("Invalid origin",403)
            size = int(self.headers.get("Content-Length","0"))
            if not 0 < size < 32768:
                return self.respond("Invalid request size",400)
            fields = parse_qs(self.rfile.read(size).decode())
            target = None
            try:
                value = lambda key: fields[key][0]
                with tempfile.TemporaryDirectory(prefix="ktx-ca-") as directory:
                    ca = Path(directory)/"ca.pem"
                    ca.write_text(value("ca"),encoding="ascii")
                    target = mysql.connector.connect(host=value("host"),port=int(value("port")),
                        database=value("database"),user=value("user"),password=value("password"),
                        charset="utf8mb4",collation="utf8mb4_unicode_ci",connection_timeout=20,
                        ssl_ca=str(ca),ssl_verify_cert=True,ssl_verify_identity=True)
                    counts = copy_data(target, verify_only=value("action")=="verify")
                state["done"] = True
                state["message"] = "<h1>Transfer verified</h1><p>13 tables copied. All 14 reports match for October 2024 and October 2026.</p><ul>" + "".join(f"<li>{table}: {count}</li>" for table,count in counts.items()) + "</ul>"
                print("TRANSFER_VERIFIED: 13 tables; 28 report comparisons passed.",flush=True)
                self.respond(state["message"])
            except Exception as error:
                # Do not echo exception messages, which may contain connection information.
                code = getattr(error,"errno",None)
                print(f"TRANSFER_FAILED: {type(error).__name__}; code={code}",flush=True)
                if isinstance(error, ValueError) and str(error).startswith(("Target is not", "Row count mismatch", "Table data mismatch", "Report mismatch", "Another transfer")):
                    print(str(error),flush=True)
                self.respond("<h1>Transfer stopped</h1><p>Inspect the local console. No local data was changed. A partial cloud schema may need inspection before retrying.</p>",500)
            finally:
                if target:
                    target.close()

    server = HTTPServer(("127.0.0.1",0),Handler)
    print(f"TRANSFER_UI=http://127.0.0.1:{server.server_port}{route}",flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
