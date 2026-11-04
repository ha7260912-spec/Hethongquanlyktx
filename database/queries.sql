-- 14 truy van nghiep vu: 4 bat buoc + 10 bo sung de demo. Khoang ngay: [tu_ngay, den_ngay), den_ngay la ngay ke tiep.
SET @ky_thang='2026-10-01';
SET @thang_sau='2026-11-01';
SET @tu_ngay='2026-10-01';
SET @den_ngay='2026-11-01';
SET @ma_sv=CONVERT('' USING utf8mb4) COLLATE utf8mb4_unicode_ci;

-- Q01 | Tong chi phi tung sinh vien theo thang, gom tien phong | month
WITH room_parts AS (
 SELECT MaSV,SoPhong,MAX(DonGiaApDung) AS Phi FROM DangKyPhong
 WHERE NgayBatDau<@thang_sau AND (NgayKetThuc IS NULL OR NgayKetThuc>=@ky_thang)
 GROUP BY MaSV,SoPhong
), rooms AS (SELECT MaSV,SUM(Phi) AS TienPhong FROM room_parts GROUP BY MaSV),
fees AS (
 SELECT MaSV,SUM(IF(LoaiKhoan='DICH_VU',ThanhTien,0)) AS TienDichVu,
 SUM(IF(LoaiKhoan='VE_XE_THANG',ThanhTien,0)) AS TienVeXe,
 SUM(IF(LoaiKhoan='PHI_GUI_XE',ThanhTien,0)) AS PhiVuotLuot
 FROM v_phat_sinh_dich_vu WHERE ThoiGian>=@ky_thang AND ThoiGian<@thang_sau GROUP BY MaSV
)
SELECT sv.MaSV,sv.HoTen,sv.Lop,COALESCE(r.TienPhong,0) AS TienPhong,
 COALESCE(f.TienDichVu,0) AS TienDichVu,COALESCE(f.TienVeXe,0) AS TienVeXe,
 COALESCE(f.PhiVuotLuot,0) AS PhiVuotLuot,
 COALESCE(r.TienPhong,0)+COALESCE(f.TienDichVu,0)+COALESCE(f.TienVeXe,0)+COALESCE(f.PhiVuotLuot,0) AS TongTien
FROM SinhVien sv LEFT JOIN rooms r ON r.MaSV=sv.MaSV LEFT JOIN fees f ON f.MaSV=sv.MaSV
WHERE (r.MaSV IS NOT NULL OR f.MaSV IS NOT NULL) AND (@ma_sv='' OR sv.MaSV=@ma_sv)
ORDER BY sv.MaSV;

-- Q02 | Dich vu va tong tien theo sinh vien trong khoang ngay | range
SELECT sv.MaSV,sv.HoTen,d.MaDV,d.TenDV,SUM(v.SoLuong) AS TongSoLuong,SUM(v.ThanhTien) AS TongTien
FROM v_phat_sinh_dich_vu v JOIN SinhVien sv ON sv.MaSV=v.MaSV JOIN DichVu d ON d.MaDV=v.MaDV
WHERE v.ThoiGian>=@tu_ngay AND v.ThoiGian<@den_ngay AND (@ma_sv='' OR sv.MaSV=@ma_sv)
GROUP BY sv.MaSV,sv.HoTen,d.MaDV,d.TenDV ORDER BY sv.MaSV,d.MaDV;

-- Q03 | Khach tham tung sinh vien va so lan den trong tuan/thang | range
SELECT sv.MaSV,sv.HoTen,k.SoCMT,k.Ten,k.NgaySinh,COUNT(*) AS SoLanDen,MAX(t.NgayDenChoi) AS LanGanNhat
FROM Tham t JOIN SinhVien sv ON sv.MaSV=t.MaSV JOIN Khach k ON k.MaKhach=t.MaKhach
WHERE t.NgayDenChoi>=@tu_ngay AND t.NgayDenChoi<@den_ngay AND (@ma_sv='' OR sv.MaSV=@ma_sv)
GROUP BY sv.MaSV,sv.HoTen,k.MaKhach,k.SoCMT,k.Ten,k.NgaySinh ORDER BY sv.MaSV,SoLanDen DESC;

-- Q04 | Danh muc va doanh thu tat ca dich vu trong thang, ke ca 0 dong | month
SELECT d.MaDV,d.TenDV,COALESCE(SUM(v.SoLuong),0) AS TongSoLuong,COALESCE(SUM(v.ThanhTien),0) AS DoanhThu
FROM DichVu d LEFT JOIN v_phat_sinh_dich_vu v
 ON v.MaDV=d.MaDV AND v.ThoiGian>=@ky_thang AND v.ThoiGian<@thang_sau
GROUP BY d.MaDV,d.TenDV ORDER BY DoanhThu DESC,d.MaDV;

-- Q05 | Phong con cho tai ngay bat dau | range
SELECT p.SoPhong,p.LoaiPhong,p.SoNguoiToiDa,COUNT(d.MaDK) AS DangO,p.SoNguoiToiDa-COUNT(d.MaDK) AS ConTrong
FROM Phong p LEFT JOIN DangKyPhong d ON d.SoPhong=p.SoPhong AND d.NgayBatDau<=@tu_ngay
 AND (d.NgayKetThuc IS NULL OR d.NgayKetThuc>=@tu_ngay)
GROUP BY p.SoPhong,p.LoaiPhong,p.SoNguoiToiDa HAVING COUNT(d.MaDK)<p.SoNguoiToiDa ORDER BY p.SoPhong;

-- Q06 | Phong da day tai ngay bat dau | range
SELECT p.SoPhong,p.LoaiPhong,p.SoNguoiToiDa,COUNT(d.MaDK) AS DangO
FROM Phong p LEFT JOIN DangKyPhong d ON d.SoPhong=p.SoPhong AND d.NgayBatDau<=@tu_ngay
 AND (d.NgayKetThuc IS NULL OR d.NgayKetThuc>=@tu_ngay)
GROUP BY p.SoPhong,p.LoaiPhong,p.SoNguoiToiDa HAVING COUNT(d.MaDK)>=p.SoNguoiToiDa ORDER BY p.SoPhong;

-- Q07 | Sinh vien noi tru chua su dung dich vu nao | range
SELECT sv.MaSV,sv.HoTen,sv.Lop FROM SinhVien sv
WHERE EXISTS(SELECT 1 FROM DangKyPhong d WHERE d.MaSV=sv.MaSV AND d.NgayBatDau<@den_ngay
 AND (d.NgayKetThuc IS NULL OR d.NgayKetThuc>=@tu_ngay))
AND NOT EXISTS(SELECT 1 FROM v_phat_sinh_dich_vu v WHERE v.MaSV=sv.MaSV AND v.ThoiGian>=@tu_ngay AND v.ThoiGian<@den_ngay)
ORDER BY sv.MaSV;

-- Q08 | Sinh vien su dung it nhat hai loai dich vu | range
SELECT sv.MaSV,sv.HoTen,COUNT(DISTINCT v.MaDV) AS SoLoaiDichVu,SUM(v.ThanhTien) AS TongTien
FROM SinhVien sv JOIN v_phat_sinh_dich_vu v ON v.MaSV=sv.MaSV
WHERE v.ThoiGian>=@tu_ngay AND v.ThoiGian<@den_ngay
GROUP BY sv.MaSV,sv.HoTen HAVING COUNT(DISTINCT v.MaDV)>=2 ORDER BY SoLoaiDichVu DESC,sv.MaSV;

-- Q09 | Top 10 sinh vien chi tieu dich vu cao nhat | month
SELECT sv.MaSV,sv.HoTen,SUM(v.ThanhTien) AS TongTien
FROM SinhVien sv JOIN v_phat_sinh_dich_vu v ON v.MaSV=sv.MaSV
WHERE v.ThoiGian>=@ky_thang AND v.ThoiGian<@thang_sau
GROUP BY sv.MaSV,sv.HoTen ORDER BY TongTien DESC,sv.MaSV LIMIT 10;

-- Q10 | Dich vu co doanh thu cao nhat thang, bao gom dong hang | month
WITH revenue AS (
 SELECT d.MaDV,d.TenDV,SUM(v.ThanhTien) AS DoanhThu,
 DENSE_RANK() OVER(ORDER BY SUM(v.ThanhTien) DESC) AS Hang
 FROM DichVu d JOIN v_phat_sinh_dich_vu v ON v.MaDV=d.MaDV
 WHERE v.ThoiGian>=@ky_thang AND v.ThoiGian<@thang_sau
 GROUP BY d.MaDV,d.TenDV
)
SELECT MaDV,TenDV,DoanhThu FROM revenue WHERE Hang=1 ORDER BY MaDV;

-- Q11 | Khach den tham nhieu nhat, bao gom dong hang | range
WITH counts AS (
 SELECT k.MaKhach,k.SoCMT,k.Ten,COUNT(*) AS SoLanDen,DENSE_RANK() OVER(ORDER BY COUNT(*) DESC) AS Hang
 FROM Khach k JOIN Tham t ON t.MaKhach=k.MaKhach
 WHERE t.NgayDenChoi>=@tu_ngay AND t.NgayDenChoi<@den_ngay GROUP BY k.MaKhach,k.SoCMT,k.Ten
)
SELECT MaKhach,SoCMT,Ten,SoLanDen FROM counts WHERE Hang=1 ORDER BY MaKhach;

-- Q12 | Xe vuot hai luot mien phi trong ngay | range
SELECT d.MaSV,sv.HoTen,lg.BienSo,DATE(lg.ThoiGianGui) AS NgayGui,COUNT(*) AS SoLuot,
 COUNT(*)-2 AS LuotTinhPhi,SUM(lg.SoTien) AS TongPhi
FROM LuotGuiXe lg JOIN DangKyXeThang d ON d.MaDKXe=lg.MaDKXe JOIN SinhVien sv ON sv.MaSV=d.MaSV
WHERE lg.ThoiGianGui>=@tu_ngay AND lg.ThoiGianGui<@den_ngay
GROUP BY d.MaSV,sv.HoTen,lg.BienSo,DATE(lg.ThoiGianGui) HAVING COUNT(*)>2 ORDER BY NgayGui,lg.BienSo;

-- Q13 | Cong no sinh vien den het thang duoc chon | month
SELECT sv.MaSV,sv.HoTen,COUNT(*) AS SoHoaDonNo,SUM(hd.TongTien) AS TongNo,MIN(hd.KyThang) AS KyNoDau
FROM HoaDon hd JOIN SinhVien sv ON sv.MaSV=hd.MaSV
WHERE hd.TrangThai<>'paid' AND hd.KyThang<@thang_sau
GROUP BY sv.MaSV,sv.HoTen ORDER BY TongNo DESC,sv.MaSV;

-- Q14 | Dich vu khong co nguoi su dung | range
SELECT d.MaDV,d.TenDV,d.DonGia FROM DichVu d
WHERE NOT EXISTS(SELECT 1 FROM v_phat_sinh_dich_vu v WHERE v.MaDV=d.MaDV AND v.ThoiGian>=@tu_ngay AND v.ThoiGian<@den_ngay)
ORDER BY d.MaDV;
