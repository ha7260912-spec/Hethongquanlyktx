"""Integration checks on an isolated sample DB, never on ql_ktx.

python tests/check_database.py --database ql_ktx_verify_20261027_a
Each test rolls back its writes, including repository calls to commit().
"""
import argparse
import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mysql.connector

from application import create_app
from config import Config
from database.connection import get_db
from repositories import billing_repo, report_repo, sudungdichvu_repo, ticket_repo, xe_repo
from services import billing_service, luotguixe_service


class DatabaseChecks(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.db = get_db()
        self.commits = patch.object(self.db, "commit", lambda: None)
        self.rollbacks = patch.object(self.db, "rollback", lambda: None)
        self.commits.start()
        self.rollbacks.start()

    def tearDown(self):
        self.commits.stop()
        self.rollbacks.stop()
        self.db.rollback()
        self.ctx.pop()

    def sql(self, sql, params=()):
        cur = self.db.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            return cur.fetchall() if cur.with_rows else cur.lastrowid
        finally:
            cur.close()

    def report(self, key, month=10):
        first, end = billing_repo.period(month, 2026)
        return report_repo.run(key, first, end, first, end)["rows"]

    def test_all_14_queries_and_expected_totals(self):
        self.assertEqual(len(report_repo.catalog()), 14)
        for key in report_repo.catalog():
            with self.subTest(query=key):
                self.report(key)
        totals = {r["MaSV"]: r["TongTien"] for r in self.report("Q01")}
        self.assertEqual(totals, {"SV01":808000,"SV02":670000,"SV03":600000,"SV04":400000})
        revenue = {r["MaDV"]:r["DoanhThu"] for r in self.report("Q04")}
        self.assertEqual(revenue["XE_THANG"], 300000)
        self.assertEqual(revenue["XE_PHAT"], 3000)
        self.assertEqual(revenue["DV04"], 0)
        self.assertEqual(sum(revenue.values()), 478000)
        self.assertEqual({r['MaDV'] for r in self.report('Q14')}, {'DV04'})
        self.assertEqual({r["MaSV"] for r in self.report("Q07")}, {"SV03","SV04"})

    def test_week_month_and_invalid_range(self):
        monthly = billing_service.get_report(10,2026,key="Q03")["rows"]
        weekly = billing_service.get_report(10,2026,key="Q03",mode="week",anchor="2026-10-27")["rows"]
        self.assertEqual(monthly[0]["SoLanDen"], 2)
        self.assertEqual(weekly[0]["SoLanDen"], 1)
        with self.assertRaises(ValueError):
            billing_service.get_report(10,2026,key="Q03",mode="range",start="2026-11-01",end="2026-10-01")

    def test_preview_does_not_create_tickets_or_charge_other_month(self):
        before = len(self.sql("SELECT * FROM DangKyXeThang"))
        self.assertEqual(billing_repo.get_student_invoice("SV01",9,2026)["total"], 0)
        self.assertEqual(billing_repo.get_student_invoice("SV01",11,2026)["total"], 500000)
        self.assertEqual(len(self.sql("SELECT * FROM DangKyXeThang")), before)

    def test_one_day_room_and_same_room_not_double_charged(self):
        self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung) VALUES('SV03','P102','2026-10-01','2026-10-01',600000)")
        invoice = billing_repo.get_student_invoice("SV03",10,2026)
        self.assertEqual(invoice["total"], 600000)
        self.assertEqual(len(invoice["details"]), 1)

    def test_parking_list_and_edit_use_same_stored_fee(self):
        rows = [r for r in luotguixe_service.get_all() if r["BienSo"] == "29A-001"]
        self.assertEqual([r["SoTien"] for r in sorted(rows,key=lambda r:r["MaLuot"])],[0,0,3000])
        for row in rows:
            self.assertEqual(luotguixe_service.get_one(row["MaLuot"])["SoTien"],row["SoTien"])
        fee = luotguixe_service.update(1,"29A-001","2026-10-27T09:00","2026-10-27T08:00")
        self.assertEqual(fee, 0)

    def test_backdated_insert_reorders_and_delete_recalculates(self):
        luotguixe_service.create("29A-001","2026-10-27T07:30","2026-10-27T07:00")
        rows = self.sql("SELECT SoTien FROM LuotGuiXe WHERE BienSo='29A-001' ORDER BY ThoiGianGui,MaLuot")
        self.assertEqual([r["SoTien"] for r in rows],[0,0,3000,3000])
        luotguixe_service.delete(1)
        rows = self.sql("SELECT SoTien FROM LuotGuiXe WHERE BienSo='29A-001' ORDER BY ThoiGianGui,MaLuot")
        self.assertEqual([r["SoTien"] for r in rows],[0,0,3000])

    def test_moving_parking_to_other_day_recalculates(self):
        self.assertEqual(luotguixe_service.update(3,"29A-001","2026-10-28T13:00","2026-10-28T12:00"),0)
        self.assertEqual(self.sql("SELECT SUM(SoTien) AS fee FROM LuotGuiXe")[0]["fee"],0)

    def test_invalid_parking_and_missing_monthly_ticket(self):
        with self.assertRaises(ValueError):
            luotguixe_service.create("29A-001","2026-10-27T08:45","2026-10-27T08:30")
        with self.assertRaises(ValueError):
            luotguixe_service.create("29A-001","2026-11-01T09:00","2026-11-01T08:00")
        with self.assertRaises(ValueError):
            luotguixe_service.create("29A-001","2026-10-27T07:00","2026-10-27T08:00")

    def test_two_ticket_limit_application_and_database(self):
        xe_repo.create("29A-003","SV01","Xe máy",date(2026,10,1))
        with self.assertRaises(ValueError):
            ticket_repo.register("29A-003",date(2026,10,1))
        with self.assertRaises(mysql.connector.Error):
            self.sql("INSERT INTO DangKyXeThang(MaSV,BienSo,KyThang,DonGia) VALUES('SV01','29A-003','2026-10-01',100000)")

    def test_ticket_cancel_renew_and_no_backdating(self):
        with self.assertRaises(ValueError):
            ticket_repo.cancel(1)
        ticket_repo.cancel(3)
        ticket_repo.register("29B-001",date(2026,10,1))
        self.assertEqual(len(ticket_repo.get_all(date(2026,10,1))),3)
        with self.assertRaises(ValueError):
            ticket_repo.register("29B-001",date(2026,9,1))

    def test_historical_price_is_kept_on_edit(self):
        self.sql("UPDATE DichVu SET DonGia=19000 WHERE MaDV='DV01'")
        sudungdichvu_repo.update(1,"SV01","DV01",datetime(2026,10,20,8),3)
        row = self.sql("SELECT DonGiaApDung,SoLuong FROM SuDungDichVu WHERE MaSD=1")[0]
        self.assertEqual(row["DonGiaApDung"],15000)
        self.assertEqual(row["SoLuong"],3)

    def test_invoice_snapshot_refresh_paid_lock_and_unique_period(self):
        saved = billing_repo.save_invoice("SV01",10,2026)
        self.assertEqual(saved["total"],808000)
        sudungdichvu_repo.update(1,"SV01","DV01",datetime(2026,10,20,8),3)
        self.assertEqual(billing_repo.get_student_invoice("SV01",10,2026)["total"],808000)
        refreshed = billing_repo.save_invoice("SV01",10,2026)
        self.assertEqual(refreshed["total"],823000)
        self.assertEqual(saved["ma_hd"],refreshed["ma_hd"])
        billing_repo.mark_paid(saved["ma_hd"])
        self.assertEqual(billing_repo.save_invoice("SV01",10,2026)["total"],823000)
        with self.assertRaises(ValueError):
            sudungdichvu_repo.delete(1)
        with self.assertRaises(mysql.connector.Error):
            self.sql("UPDATE HoaDon SET TongTien=1 WHERE MaHD=%s",(saved["ma_hd"],))
        with self.assertRaises(mysql.connector.Error):
            self.sql("DELETE FROM SuDungDichVu WHERE MaSD=1")
        with self.assertRaises(mysql.connector.Error):
            self.sql("UPDATE ChiTietHoaDon SET ThanhTien=0 WHERE MaHD=%s",(saved["ma_hd"],))
        with self.assertRaises(mysql.connector.Error):
            self.sql("INSERT INTO HoaDon(MaSV,KyThang,TongTien) VALUES('SV01','2026-10-01',1)")

    def test_room_full_and_student_overlap(self):
        with self.assertRaises(mysql.connector.Error):
            self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,DonGiaApDung) VALUES('SV05','P101','2026-10-01',500000)")
        with self.assertRaises(mysql.connector.Error):
            self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,DonGiaApDung) VALUES('SV01','P103','2026-10-01',400000)")

    def test_room_peak_occupancy_not_sum_of_disjoint_stays(self):
        self.sql("INSERT INTO Phong VALUES('PTEST','Kiểm thử',100000,2)")
        self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung) VALUES('SV01','PTEST','2026-01-01','2026-01-05',100000)")
        self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung) VALUES('SV02','PTEST','2026-01-06','2026-01-10',100000)")
        self.sql("INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung) VALUES('SV05','PTEST','2026-01-01','2026-01-10',100000)")

    def test_http_reports_tickets_invoices_and_access(self):
        client = self.app.test_client()
        self.assertEqual(client.get('/dich-vu/').status_code,302)
        self.assertEqual(client.post('/su-dung-dich-vu/them',data={}).status_code,302)
        with client.session_transaction() as session:
            session.update(user='admin',role='admin',hoten='Quản trị viên')
        for key in report_repo.catalog():
            with self.subTest(page=key):
                response = client.get('/bao-cao/',query_string={'query':key,'month':10,'year':2026})
                self.assertEqual(response.status_code,200)
        for url in ['/ve-xe/?month=10&year=2026','/hoa-don/?month=10&year=2026','/hoa-don/SV01?month=10&year=2026','/dich-vu/','/su-dung-dich-vu/']:
            with self.subTest(page=url):
                self.assertEqual(client.get(url).status_code,200)
        self.assertEqual(client.get('/bao-cao/?month=13&year=2026').status_code,400)

    def test_generate_all_ignores_students_without_costs(self):
        count,month,year = billing_service.generate_all(10,2026)
        self.assertEqual((count,month,year),(4,10,2026))
        self.assertEqual(len(billing_repo.get_invoices(10,2026)),4)
        self.assertEqual(self.sql("SELECT COUNT(*) AS c FROM HoaDon WHERE MaSV='SV05'")[0]['c'],0)

    def test_return_room_preserves_paid_months(self):
        from repositories import dangkyphong_repo
        saved = billing_repo.save_invoice('SV01',10,2026)
        billing_repo.mark_paid(saved['ma_hd'])
        dangkyphong_repo.end_registration(1,'2026-11-30')
        self.assertEqual(self.sql('SELECT NgayKetThuc FROM DangKyPhong WHERE MaDK=1')[0]['NgayKetThuc'],date(2026,11,30))
        with self.assertRaises(mysql.connector.Error):
            dangkyphong_repo.end_registration(1,'2026-10-15')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    args, remaining = parser.parse_known_args()
    if not args.database.startswith("ql_ktx_verify_"):
        parser.error("Only an isolated ql_ktx_verify_* sample database is allowed.")
    Config.MYSQL_DB = args.database
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
