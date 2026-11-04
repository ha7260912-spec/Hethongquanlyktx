"""Initialize an empty, already-provisioned cloud database only."""
import os
from config import Config
from database.manage import connect, run_sql
from utils.security import hash_password

REQUIRED_TABLES = {
    "Users", "SinhVien", "Phong", "DangKyPhong", "DichVu", "SuDungDichVu",
    "Khach", "Tham", "Xe", "LuotGuiXe", "DangKyXeThang", "HoaDon", "ChiTietHoaDon",
}


def initialize():
    db = connect(Config.MYSQL_DB)
    cur = db.cursor()
    locked = False
    try:
        cur.execute("SELECT GET_LOCK('ktx_bootstrap', 60)")
        locked = cur.fetchone()[0] == 1
        if not locked:
            raise RuntimeError("Another deployment is initializing the database. Retry later.")
        cur.execute("SHOW FULL TABLES WHERE Table_type='BASE TABLE'")
        tables = {row[0].lower() for row in cur.fetchall()}
        if tables:
            if not {name.lower() for name in REQUIRED_TABLES}.issubset(tables):
                raise RuntimeError("Existing schema is incomplete; migrate it explicitly. No data was changed.")
            cur.execute("SELECT COUNT(*) FROM Users")
            if not cur.fetchone()[0]:
                raise RuntimeError("Schema exists without users. Create an administrator explicitly before deployment.")
            print("Existing database preserved; initialization skipped.")
            return
        username = os.getenv("ADMIN_USERNAME", "admin").strip()
        password = os.getenv("ADMIN_PASSWORD", "")
        if not username or len(username) > 50 or len(password) < 12:
            raise RuntimeError("Set ADMIN_USERNAME (1-50 chars) and ADMIN_PASSWORD (at least 12 chars).")
        run_sql(db, "schema.sql")
        run_sql(db, "domain.sql")
        cur.execute(
            "INSERT INTO Users (username,password,role,HoTen) VALUES (%s,%s,'admin',%s)",
            (username, hash_password(password), "Quản trị viên"),
        )
        db.commit()
        print("Cloud database initialized. No local or sample data was uploaded.")
    finally:
        if locked:
            cur.execute("SELECT RELEASE_LOCK('ktx_bootstrap')")
            cur.fetchone()
        cur.close()
        db.close()


if __name__ == "__main__":
    initialize()
