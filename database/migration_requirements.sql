-- Migration cho cac yeu cau bo sung cua he thong quan ly KTX.
-- Chay file nay sau khi da chay file tao CSDL goc va dang dung schema ql_ktx.
-- Chon dung schema truoc khi chay. Khong tu dong tao ve cho cac thang bat ky.

-- Luu don gia tai thoi diem phat sinh, tranh thay doi hoa don cu khi bang DichVu thay doi.
SET @add_service_price = (
    SELECT IF(COUNT(*) = 0,
        'ALTER TABLE SuDungDichVu ADD COLUMN DonGiaApDung DECIMAL(12,2) NULL AFTER SoLuong',
        'SELECT 1')
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND LOWER(TABLE_NAME) = 'sudungdichvu'
      AND COLUMN_NAME = 'DonGiaApDung'
);
PREPARE stmt_service_price FROM @add_service_price;
EXECUTE stmt_service_price;
DEALLOCATE PREPARE stmt_service_price;

UPDATE SuDungDichVu sd
JOIN DichVu dv ON dv.MaDV = sd.MaDV
SET sd.DonGiaApDung = dv.DonGia
WHERE sd.DonGiaApDung IS NULL;

ALTER TABLE SuDungDichVu
    MODIFY COLUMN DonGiaApDung DECIMAL(12,2) NOT NULL;

SET @add_room_price = (
    SELECT IF(COUNT(*) = 0,
        'ALTER TABLE DangKyPhong ADD COLUMN DonGiaApDung DECIMAL(12,2) NULL AFTER NgayKetThuc',
        'SELECT 1')
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND LOWER(TABLE_NAME) = 'dangkyphong'
      AND COLUMN_NAME = 'DonGiaApDung'
);
PREPARE stmt_room_price FROM @add_room_price;
EXECUTE stmt_room_price;
DEALLOCATE PREPARE stmt_room_price;

UPDATE DangKyPhong dk
JOIN Phong p ON p.SoPhong = dk.SoPhong
SET dk.DonGiaApDung = p.DonGia
WHERE dk.DonGiaApDung IS NULL;

ALTER TABLE DangKyPhong
    MODIFY COLUMN DonGiaApDung DECIMAL(12,2) NOT NULL;

-- Dang ky ve duoc tao ro rang theo thang, khong suy ra tu danh sach Xe.
CREATE TABLE IF NOT EXISTS DangKyXeThang (
    MaDKXe INT AUTO_INCREMENT PRIMARY KEY,
    MaSV VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    BienSo VARCHAR(15) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    KyThang DATE NOT NULL,
    DonGia DECIMAL(12,2) NOT NULL DEFAULT 100000,
    TrangThai ENUM('active', 'cancelled') NOT NULL DEFAULT 'active',
    NgayTao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_dk_xe_thang (MaSV, BienSo, KyThang),
    CONSTRAINT fk_dk_xe_sv FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV),
    CONSTRAINT fk_dk_xe_xe FOREIGN KEY (BienSo) REFERENCES Xe(BienSo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS HoaDon (
    MaHD INT AUTO_INCREMENT PRIMARY KEY,
    MaSV VARCHAR(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    KyThang DATE NOT NULL,
    TongTien DECIMAL(12,2) NOT NULL DEFAULT 0,
    TrangThai ENUM('unpaid', 'paid', 'overdue') NOT NULL DEFAULT 'unpaid',
    NgayLap DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    NgayThanhToan DATETIME NULL,
    GhiChu VARCHAR(255) NULL,
    UNIQUE KEY uq_hoa_don_thang (MaSV, KyThang),
    CONSTRAINT fk_hoa_don_sv FOREIGN KEY (MaSV) REFERENCES SinhVien(MaSV)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ChiTietHoaDon (
    MaCT INT AUTO_INCREMENT PRIMARY KEY,
    MaHD INT NOT NULL,
    LoaiKhoan VARCHAR(30) NOT NULL,
    MoTa VARCHAR(255) NOT NULL,
    SoLuong DECIMAL(12,2) NOT NULL DEFAULT 1,
    DonGia DECIMAL(12,2) NOT NULL DEFAULT 0,
    ThanhTien DECIMAL(12,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_cthd_hd FOREIGN KEY (MaHD) REFERENCES HoaDon(MaHD) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kiem tra nhanh sau migration.
SELECT TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME IN ('DangKyXeThang', 'HoaDon', 'ChiTietHoaDon');
