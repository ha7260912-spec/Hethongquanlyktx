-- Viet lai cac doi tuong nghiep vu: co the chay lai, khong xoa bang hay du lieu.
INSERT IGNORE INTO DichVu(MaDV,TenDV,DonGia) VALUES
 ('XE_THANG','Vé gửi xe tháng',100000),('XE_PHAT','Gửi xe vượt lượt',3000);

DROP PROCEDURE IF EXISTS sp_kiem_tra_ky_mo;
DROP PROCEDURE IF EXISTS sp_kiem_tra_phong;
DROP PROCEDURE IF EXISTS sp_kiem_tra_ve_xe;
DELIMITER $$
CREATE PROCEDURE sp_kiem_tra_ky_mo(IN p_sv VARCHAR(10), IN p_ngay DATE)
BEGIN
 DECLARE v_sv VARCHAR(10);
 DECLARE v_count INT;
 SELECT MaSV INTO v_sv FROM SinhVien WHERE MaSV=p_sv FOR UPDATE;
 IF v_sv IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Sinh viên không tồn tại.'; END IF;
 SELECT COUNT(*) INTO v_count FROM HoaDon
 WHERE MaSV=p_sv AND KyThang=DATE_FORMAT(p_ngay,'%Y-%m-01') AND TrangThai='paid';
 IF v_count>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tháng này đã thanh toán, không được sửa dữ liệu tính tiền.'; END IF;
END$$
CREATE PROCEDURE sp_kiem_tra_phong(IN p_id INT, IN p_sv VARCHAR(10), IN p_phong VARCHAR(10), IN p_start DATE, IN p_end DATE)
BEGIN
 DECLARE v_max INT;
 DECLARE v_count INT;
 DECLARE v_peak INT;
 IF p_start IS NULL OR (p_end IS NOT NULL AND p_end<p_start) THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Khoảng ngày đăng ký phòng không hợp lệ.';
 END IF;
 SELECT SoNguoiToiDa INTO v_max FROM Phong WHERE SoPhong=p_phong FOR UPDATE;
 SELECT COUNT(*) INTO v_count FROM DangKyPhong
 WHERE MaSV=p_sv AND MaDK<>p_id AND NgayBatDau<=COALESCE(p_end,'9999-12-31')
 AND (NgayKetThuc IS NULL OR NgayKetThuc>=p_start);
 IF v_count>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Sinh viên đã có phòng trùng thời gian.'; END IF;
 SELECT COALESCE(MAX((SELECT COUNT(*) FROM DangKyPhong d
   WHERE d.SoPhong=p_phong AND d.MaDK<>p_id AND d.NgayBatDau<=anchors.ngay
   AND (d.NgayKetThuc IS NULL OR d.NgayKetThuc>=anchors.ngay))),0) INTO v_peak
 FROM (SELECT p_start AS ngay UNION SELECT NgayBatDau FROM DangKyPhong
   WHERE SoPhong=p_phong AND MaDK<>p_id AND NgayBatDau BETWEEN p_start AND COALESCE(p_end,'9999-12-31')) anchors;
 IF v_max IS NULL OR v_peak>=v_max THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Phòng đã đủ người trong khoảng đăng ký.'; END IF;
END$$
CREATE PROCEDURE sp_kiem_tra_ve_xe(IN p_id INT, IN p_sv VARCHAR(10), IN p_bien VARCHAR(15), IN p_thang DATE, IN p_state VARCHAR(15))
BEGIN
 DECLARE v_owner VARCHAR(10);
 DECLARE v_start DATE;
 DECLARE v_count INT;
 CALL sp_kiem_tra_ky_mo(p_sv,p_thang);
 SELECT MaSV,NgayDangKy INTO v_owner,v_start FROM Xe WHERE BienSo=p_bien FOR UPDATE;
 IF v_owner IS NULL OR v_owner<>p_sv OR DAY(p_thang)<>1 OR p_thang<DATE_FORMAT(v_start,'%Y-%m-01') THEN
   SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Vé tháng không khớp chủ xe hoặc ngày đăng ký xe.';
 END IF;
 IF p_state='active' THEN
   SELECT COUNT(*) INTO v_count FROM DangKyXeThang
   WHERE MaSV=p_sv AND KyThang=p_thang AND TrangThai='active' AND MaDKXe<>p_id;
   IF v_count>=2 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Mỗi sinh viên tối đa 2 xe vé tháng trong một tháng.'; END IF;
 END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS ktx_dkp_insert;
DROP TRIGGER IF EXISTS ktx_dkp_update;
DROP TRIGGER IF EXISTS ktx_dkp_delete;
DROP TRIGGER IF EXISTS ktx_usage_insert;
DROP TRIGGER IF EXISTS ktx_usage_update;
DROP TRIGGER IF EXISTS ktx_usage_delete;
DROP TRIGGER IF EXISTS ktx_ticket_insert;
DROP TRIGGER IF EXISTS ktx_ticket_update;
DROP TRIGGER IF EXISTS ktx_ticket_delete;
DROP TRIGGER IF EXISTS ktx_parking_insert;
DROP TRIGGER IF EXISTS ktx_parking_update;
DROP TRIGGER IF EXISTS ktx_parking_delete;
DROP TRIGGER IF EXISTS ktx_invoice_update;
DROP TRIGGER IF EXISTS ktx_invoice_delete;
DROP TRIGGER IF EXISTS ktx_detail_insert;
DROP TRIGGER IF EXISTS ktx_detail_update;
DROP TRIGGER IF EXISTS ktx_detail_delete;
DROP TRIGGER IF EXISTS ktx_car_update;
DELIMITER $$
CREATE TRIGGER ktx_dkp_insert BEFORE INSERT ON DangKyPhong FOR EACH ROW
BEGIN
 DECLARE v_paid INT;
 CALL sp_kiem_tra_ky_mo(NEW.MaSV,NEW.NgayBatDau);
 SELECT COUNT(*) INTO v_paid FROM HoaDon WHERE MaSV=NEW.MaSV AND TrangThai='paid'
 AND LAST_DAY(KyThang)>=NEW.NgayBatDau AND KyThang<=COALESCE(NEW.NgayKetThuc,'9999-12-31');
 IF v_paid>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Đăng ký này ảnh hưởng tháng đã thanh toán.'; END IF;
 CALL sp_kiem_tra_phong(0,NEW.MaSV,NEW.SoPhong,NEW.NgayBatDau,NEW.NgayKetThuc);
 IF NEW.DonGiaApDung IS NULL OR NEW.DonGiaApDung<=0 THEN
 SET NEW.DonGiaApDung=(SELECT DonGia FROM Phong WHERE SoPhong=NEW.SoPhong);
 END IF;
END$$
CREATE TRIGGER ktx_dkp_update BEFORE UPDATE ON DangKyPhong FOR EACH ROW
BEGIN
 DECLARE v_paid INT;
 DECLARE v_from DATE;
 DECLARE v_sv VARCHAR(10);
 SELECT MaSV INTO v_sv FROM SinhVien WHERE MaSV=NEW.MaSV FOR UPDATE;
 IF NEW.MaSV<>OLD.MaSV OR NEW.SoPhong<>OLD.SoPhong OR NEW.DonGiaApDung<>OLD.DonGiaApDung OR NEW.NgayBatDau<>OLD.NgayBatDau THEN
   SELECT COUNT(*) INTO v_paid FROM HoaDon WHERE MaSV IN(OLD.MaSV,NEW.MaSV) AND TrangThai='paid'
   AND LAST_DAY(KyThang)>=LEAST(NEW.NgayBatDau,OLD.NgayBatDau)
   AND KyThang<=GREATEST(COALESCE(NEW.NgayKetThuc,'9999-12-31'),COALESCE(OLD.NgayKetThuc,'9999-12-31'));
 ELSE
   SET v_from=LEAST(COALESCE(NEW.NgayKetThuc,'9999-12-31'),COALESCE(OLD.NgayKetThuc,'9999-12-31'));
   SELECT COUNT(*) INTO v_paid FROM HoaDon WHERE MaSV=OLD.MaSV AND TrangThai='paid'
   AND LAST_DAY(KyThang)>v_from AND KyThang<=GREATEST(COALESCE(NEW.NgayKetThuc,'9999-12-31'),COALESCE(OLD.NgayKetThuc,'9999-12-31'));
 END IF;
 IF v_paid>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không được thay đổi tiền phòng của tháng đã thanh toán.'; END IF;
 CALL sp_kiem_tra_phong(OLD.MaDK,NEW.MaSV,NEW.SoPhong,NEW.NgayBatDau,NEW.NgayKetThuc);
END$$
CREATE TRIGGER ktx_dkp_delete BEFORE DELETE ON DangKyPhong FOR EACH ROW
BEGIN
 DECLARE v_count INT;
 SELECT COUNT(*) INTO v_count FROM HoaDon WHERE MaSV=OLD.MaSV AND TrangThai='paid'
 AND LAST_DAY(KyThang)>=OLD.NgayBatDau AND KyThang<=COALESCE(OLD.NgayKetThuc,'9999-12-31');
 IF v_count>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Đăng ký phòng có hóa đơn đã thanh toán.'; END IF;
END$$
CREATE TRIGGER ktx_usage_insert BEFORE INSERT ON SuDungDichVu FOR EACH ROW
BEGIN
 CALL sp_kiem_tra_ky_mo(NEW.MaSV,DATE(NEW.ThoiGianSuDung));
 IF NEW.SoLuong<=0 OR NEW.DonGiaApDung<0 OR NEW.MaDV IN('XE_THANG','XE_PHAT') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Dịch vụ hoặc số lượng không hợp lệ. Phí xe ghi qua đăng ký/lượt xe.'; END IF;
END$$
CREATE TRIGGER ktx_usage_update BEFORE UPDATE ON SuDungDichVu FOR EACH ROW
BEGIN
 CALL sp_kiem_tra_ky_mo(OLD.MaSV,DATE(OLD.ThoiGianSuDung));
 CALL sp_kiem_tra_ky_mo(NEW.MaSV,DATE(NEW.ThoiGianSuDung));
 IF NEW.SoLuong<=0 OR NEW.DonGiaApDung<0 OR NEW.MaDV IN('XE_THANG','XE_PHAT') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Dịch vụ hoặc số lượng không hợp lệ.'; END IF;
END$$
CREATE TRIGGER ktx_usage_delete BEFORE DELETE ON SuDungDichVu FOR EACH ROW
BEGIN CALL sp_kiem_tra_ky_mo(OLD.MaSV,DATE(OLD.ThoiGianSuDung)); END$$
CREATE TRIGGER ktx_ticket_insert BEFORE INSERT ON DangKyXeThang FOR EACH ROW
BEGIN
 CALL sp_kiem_tra_ve_xe(0,NEW.MaSV,NEW.BienSo,NEW.KyThang,NEW.TrangThai);
 SET NEW.DonGia=100000;
END$$
CREATE TRIGGER ktx_ticket_update BEFORE UPDATE ON DangKyXeThang FOR EACH ROW
BEGIN
 DECLARE v_count INT;
 IF NEW.MaSV<>OLD.MaSV OR NEW.BienSo<>OLD.BienSo OR NEW.KyThang<>OLD.KyThang THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không đổi chủ xe/biển số/kỳ vé cũ. Hãy đăng ký vé mới.'; END IF;
 CALL sp_kiem_tra_ve_xe(OLD.MaDKXe,NEW.MaSV,NEW.BienSo,NEW.KyThang,NEW.TrangThai);
 SELECT COUNT(*) INTO v_count FROM LuotGuiXe WHERE MaDKXe=OLD.MaDKXe;
 IF NEW.TrangThai='cancelled' AND v_count>0 THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Vé đã có lượt gửi xe, không được hủy.'; END IF;
 SET NEW.DonGia=100000;
END$$
CREATE TRIGGER ktx_ticket_delete BEFORE DELETE ON DangKyXeThang FOR EACH ROW
BEGIN
 CALL sp_kiem_tra_ky_mo(OLD.MaSV,OLD.KyThang);
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hãy hủy vé thay vì xóa lịch sử đăng ký.';
END$$
CREATE TRIGGER ktx_parking_insert BEFORE INSERT ON LuotGuiXe FOR EACH ROW
BEGIN
 DECLARE v_sv VARCHAR(10);
 DECLARE v_count INT;
 SELECT MaSV INTO v_sv FROM DangKyXeThang WHERE MaDKXe=NEW.MaDKXe AND BienSo=NEW.BienSo
 AND KyThang=DATE_FORMAT(NEW.ThoiGianGui,'%Y-%m-01') AND TrangThai='active';
 IF v_sv IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Xe chưa có vé tháng hợp lệ tại ngày gửi.'; END IF;
 CALL sp_kiem_tra_ky_mo(v_sv,DATE(NEW.ThoiGianGui));
 IF NEW.ThoiGianLay IS NOT NULL AND NEW.ThoiGianLay<NEW.ThoiGianGui THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Giờ lấy xe phải từ giờ gửi trở đi.'; END IF;
 SELECT COUNT(*) INTO v_count FROM LuotGuiXe WHERE BienSo=NEW.BienSo
 AND DATE(ThoiGianGui)=DATE(NEW.ThoiGianGui) AND ThoiGianGui<=NEW.ThoiGianGui;
 SET NEW.SoTien=IF(v_count<2,0,3000);
END$$
CREATE TRIGGER ktx_parking_update BEFORE UPDATE ON LuotGuiXe FOR EACH ROW
BEGIN
 DECLARE v_sv VARCHAR(10);
 DECLARE v_count INT;
 SELECT MaSV INTO v_sv FROM DangKyXeThang WHERE MaDKXe=OLD.MaDKXe;
 CALL sp_kiem_tra_ky_mo(v_sv,DATE(OLD.ThoiGianGui));
 SET v_sv=NULL;
 SELECT MaSV INTO v_sv FROM DangKyXeThang WHERE MaDKXe=NEW.MaDKXe AND BienSo=NEW.BienSo
 AND KyThang=DATE_FORMAT(NEW.ThoiGianGui,'%Y-%m-01') AND TrangThai='active';
 IF v_sv IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Xe chưa có vé tháng hợp lệ.'; END IF;
 CALL sp_kiem_tra_ky_mo(v_sv,DATE(NEW.ThoiGianGui));
 IF NEW.ThoiGianLay IS NOT NULL AND NEW.ThoiGianLay<NEW.ThoiGianGui THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Giờ lấy xe phải từ giờ gửi trở đi.'; END IF;
 SELECT COUNT(*) INTO v_count FROM LuotGuiXe WHERE BienSo=NEW.BienSo
 AND DATE(ThoiGianGui)=DATE(NEW.ThoiGianGui) AND MaLuot<>OLD.MaLuot
 AND (ThoiGianGui<NEW.ThoiGianGui OR (ThoiGianGui=NEW.ThoiGianGui AND MaLuot<OLD.MaLuot));
 SET NEW.SoTien=IF(v_count<2,0,3000);
END$$
CREATE TRIGGER ktx_parking_delete BEFORE DELETE ON LuotGuiXe FOR EACH ROW
BEGIN
 DECLARE v_sv VARCHAR(10);
 SELECT MaSV INTO v_sv FROM DangKyXeThang WHERE MaDKXe=OLD.MaDKXe;
 CALL sp_kiem_tra_ky_mo(v_sv,DATE(OLD.ThoiGianGui));
END$$
CREATE TRIGGER ktx_invoice_update BEFORE UPDATE ON HoaDon FOR EACH ROW
BEGIN
 IF OLD.TrangThai='paid' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hóa đơn đã thanh toán không được sửa.'; END IF;
END$$
CREATE TRIGGER ktx_invoice_delete BEFORE DELETE ON HoaDon FOR EACH ROW
BEGIN
 IF OLD.TrangThai='paid' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hóa đơn đã thanh toán không được xóa.'; END IF;
END$$
CREATE TRIGGER ktx_detail_insert BEFORE INSERT ON ChiTietHoaDon FOR EACH ROW
BEGIN
 IF EXISTS(SELECT 1 FROM HoaDon WHERE MaHD=NEW.MaHD AND TrangThai='paid') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không thay đổi chi tiết hóa đơn đã thanh toán.'; END IF;
END$$
CREATE TRIGGER ktx_detail_update BEFORE UPDATE ON ChiTietHoaDon FOR EACH ROW
BEGIN
 IF EXISTS(SELECT 1 FROM HoaDon WHERE MaHD IN(OLD.MaHD,NEW.MaHD) AND TrangThai='paid') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không thay đổi chi tiết hóa đơn đã thanh toán.'; END IF;
END$$
CREATE TRIGGER ktx_detail_delete BEFORE DELETE ON ChiTietHoaDon FOR EACH ROW
BEGIN
 IF EXISTS(SELECT 1 FROM HoaDon WHERE MaHD=OLD.MaHD AND TrangThai='paid') THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Không thay đổi chi tiết hóa đơn đã thanh toán.'; END IF;
END$$
CREATE TRIGGER ktx_car_update BEFORE UPDATE ON Xe FOR EACH ROW
BEGIN
 IF (NEW.MaSV<>OLD.MaSV OR NEW.BienSo<>OLD.BienSo) AND
 EXISTS(SELECT 1 FROM DangKyXeThang WHERE BienSo=OLD.BienSo) THEN
 SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Xe có lịch sử vé tháng, không được đổi chủ/biển số.'; END IF;
END$$
DELIMITER ;

CREATE OR REPLACE VIEW v_phat_sinh_dich_vu AS
SELECT sd.MaSV, sd.MaDV, sd.ThoiGianSuDung AS ThoiGian, sd.SoLuong,
 sd.DonGiaApDung AS DonGia, sd.SoLuong*sd.DonGiaApDung AS ThanhTien,
 _utf8mb4'DICH_VU' COLLATE utf8mb4_unicode_ci AS LoaiKhoan, CAST(sd.MaSD AS CHAR(30) CHARACTER SET utf8mb4) COLLATE utf8mb4_unicode_ci AS ThamChieu
FROM SuDungDichVu sd
UNION ALL
SELECT d.MaSV,'XE_THANG',CAST(d.KyThang AS DATETIME),1,d.DonGia,d.DonGia,'VE_XE_THANG',d.BienSo
FROM DangKyXeThang d WHERE d.TrangThai='active'
UNION ALL
SELECT d.MaSV,'XE_PHAT',lg.ThoiGianGui,1,lg.SoTien,lg.SoTien,'PHI_GUI_XE',lg.BienSo
FROM LuotGuiXe lg JOIN DangKyXeThang d ON d.MaDKXe=lg.MaDKXe WHERE lg.SoTien>0;

CREATE OR REPLACE VIEW v_doanhthu_dichvu AS
SELECT MONTH(v.ThoiGian) AS Thang,YEAR(v.ThoiGian) AS Nam,d.MaDV,d.TenDV,SUM(v.ThanhTien) AS DoanhThu
FROM v_phat_sinh_dich_vu v JOIN DichVu d ON d.MaDV=v.MaDV
GROUP BY YEAR(v.ThoiGian),MONTH(v.ThoiGian),d.MaDV,d.TenDV;

CREATE OR REPLACE VIEW v_khach_tham AS
SELECT t.MaSV,sv.HoTen,k.Ten AS TenKhach,k.SoCMT,COUNT(*) AS SoLan,MAX(t.NgayDenChoi) AS LanCuoiCung
FROM Tham t JOIN Khach k ON k.MaKhach=t.MaKhach JOIN SinhVien sv ON sv.MaSV=t.MaSV
GROUP BY t.MaSV,sv.HoTen,k.MaKhach,k.Ten,k.SoCMT;
