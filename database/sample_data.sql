-- Chi chay tren database demo trong, khong nap vao du lieu dang su dung.
INSERT INTO Users(username,password,role,HoTen) VALUES
 ('admin',SHA2('admin123',256),'admin','Quản trị viên'),('letan',SHA2('user123',256),'user','Lễ tân');
INSERT INTO SinhVien(MaSV,SoCMT,HoTen,NgaySinh,Lop,QueQuan) VALUES
 ('SV01','000000000001','Nguyễn An','2006-01-01','D24CQCN01','Hà Nội'),
 ('SV02','000000000002','Trần Bình','2006-02-02','D24CQCN02','Hải Phòng'),
 ('SV03','000000000003','Lê Chi','2006-03-03','D24CQCN03','Nam Định'),
 ('SV04','000000000004','Phạm Dũng','2006-04-04','D24CQCN04','Hà Nam'),
 ('SV05','000000000005','Vũ Em','2006-05-05','D24CQCN05','Hà Nội');
INSERT INTO Phong VALUES('P101','Phòng 2 người',500000,2),('P102','Phòng 1 người',600000,1),('P103','Phòng 2 người',400000,2);
INSERT INTO DangKyPhong(MaSV,SoPhong,NgayBatDau,NgayKetThuc,DonGiaApDung) VALUES
 ('SV01','P101','2026-10-01',NULL,500000),('SV02','P101','2026-10-01',NULL,500000),
 ('SV03','P102','2026-10-31','2026-10-31',600000),('SV04','P103','2026-10-01',NULL,400000);
INSERT INTO DichVu VALUES('DV01','Giặt là',15000),('DV02','Ăn uống',20000),('DV03','Cho thuê xe',30000),('DV04','In ấn',1000);
INSERT INTO SuDungDichVu(MaSV,MaDV,ThoiGianSuDung,SoLuong,DonGiaApDung) VALUES
 ('SV01','DV01','2026-10-20 08:00:00',2,15000),('SV01','DV01','2026-10-27 08:00:00',1,15000),
 ('SV01','DV02','2026-10-27 12:00:00',3,20000),('SV02','DV02','2026-10-27 12:00:00',2,20000),
 ('SV02','DV03','2026-10-27 15:00:00',1,30000);
INSERT INTO Xe(BienSo,MaSV,LoaiXe,NgayDangKy) VALUES
 ('29A-001','SV01','Xe máy','2026-10-01'),('29A-002','SV01','Xe đạp','2026-10-01'),
 ('29B-001','SV02','Xe máy','2026-10-01'),('29C-001','SV03','Xe đạp','2026-10-01');
INSERT INTO DangKyXeThang(MaSV,BienSo,KyThang,DonGia) VALUES
 ('SV01','29A-001','2026-10-01',100000),('SV01','29A-002','2026-10-01',100000),('SV02','29B-001','2026-10-01',100000);
INSERT INTO LuotGuiXe(BienSo,MaDKXe,ThoiGianGui,ThoiGianLay) VALUES
 ('29A-001',1,'2026-10-27 08:00:00','2026-10-27 09:00:00'),
 ('29A-001',1,'2026-10-27 10:00:00','2026-10-27 11:00:00'),
 ('29A-001',1,'2026-10-27 12:00:00','2026-10-27 13:00:00'),
 ('29A-002',2,'2026-10-27 08:00:00','2026-10-27 09:00:00');
INSERT INTO Khach(SoCMT,Ten,NgaySinh) VALUES
 ('100000000001','Khách A','1980-01-01'),('100000000002','Khách B','1981-02-02'),('100000000003','Khách C','1982-03-03');
INSERT INTO Tham(MaKhach,MaSV,NgayDenChoi) VALUES(1,'SV01','2026-10-20'),(1,'SV01','2026-10-27'),(2,'SV02','2026-10-27');
