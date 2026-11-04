# Triển khai website và MySQL trên cloud

Người truy cập chỉ cần trình duyệt và tài khoản website. MySQL chạy trên cloud, không phụ thuộc máy cá nhân của người truy cập hoặc máy lập trình viên.

## Railway: ứng dụng và MySQL cùng project

1. Tạo project, thêm dịch vụ MySQL **8.x** có volume lưu dữ liệu. Giữ dịch vụ MySQL trong mạng riêng của project.
2. Thêm ứng dụng từ repository GitHub của dự án. Railway dùng `Dockerfile` và `railway.json` trong thư mục gốc. Phải đẩy các thay đổi đã kiểm tra lên GitHub trước khi build.
3. Trong Variables của ứng dụng, đặt các biến bên dưới. Ví dụ service database tên `MySQL`; nếu tên khác, thay phần đó bằng tên thực tế. Chọn Reference Variable từ dashboard để lấy đúng biến.

```env
APP_ENV=production
SECRET_KEY=<chuoi-ngau-nhien-rieng-it-nhat-32-ky-tu>
MYSQL_HOST=${{MySQL.MYSQLHOST}}
MYSQL_PORT=${{MySQL.MYSQLPORT}}
MYSQL_USER=${{MySQL.MYSQLUSER}}
MYSQL_PASSWORD=${{MySQL.MYSQLPASSWORD}}
MYSQL_DB=${{MySQL.MYSQLDATABASE}}
DATABASE_BOOTSTRAP=1
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<mat-khau-rieng-it-nhat-12-ky-tu>
```

Có thể tạo SECRET_KEY trên máy bằng `python -c "import secrets; print(secrets.token_hex(32))"`, rồi nhập trực tiếp vào Variables. Không lưu bí mật vào Git.

4. Deploy ứng dụng. Lần đầu, chương trình tạo bảng, trigger, view, thủ tục và tài khoản admin trong **database trống đã được nhà cung cấp cấp sẵn**. Không cần quyền CREATE DATABASE. Không nạp dữ liệu mẫu và không tự tải dữ liệu cá nhân từ máy lên.
5. Khi service healthy, trong Settings → Networking tạo public domain HTTPS. Kiểm tra `/healthz` trả `{"status":"ok"}`, rồi đăng nhập bằng tài khoản admin vừa đặt.
6. Sau lần khởi tạo thành công, đặt `DATABASE_BOOTSTRAP=0`, xóa `ADMIN_PASSWORD` khỏi Variables và redeploy. Các lần deploy sau không thay cấu trúc hay ghi đè mật khẩu.

Nếu database không trống, chương trình kiểm tra các bảng cần thiết và tài khoản tồn tại rồi bỏ qua khởi tạo. Schema thiếu bảng sẽ dừng để tránh trộn với dữ liệu cũ. DDL MySQL không rollback toàn bộ được: nếu lần khởi tạo bị gián đoạn, phải kiểm tra và sửa schema trước khi thử lại.

## Render: Flask và MySQL bên ngoài

1. Tạo Web Service từ repository; dùng cấu hình `render.yaml`, hoặc đặt Build Command `pip install -r requirements.txt`, Start Command `python -m deployment.start`, Health Check Path `/healthz`.
2. Tạo MySQL 8.x trên nhà cung cấp hỗ trợ trigger, view, stored procedure và kết nối từ Render. Nếu dùng MySQL Railway với ứng dụng ở Render, lấy **host/port TCP Proxy bên ngoài**, không dùng host mạng riêng Railway.
3. Đặt `APP_ENV`, `SECRET_KEY`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB` bằng giá trị cloud thật. `localhost` trên Render là máy Render, không phải máy cá nhân.
4. Với database mới trống, đặt thêm `DATABASE_BOOTSTRAP=1`, `ADMIN_USERNAME`, `ADMIN_PASSWORD` như trên. Deploy, kiểm tra healthy và đăng nhập, rồi tắt bootstrap.
5. Nếu nhà cung cấp yêu cầu CA, gắn certificate dưới dạng secret file và đặt `MYSQL_SSL_CA` bằng đường dẫn file đó. Ứng dụng kiểm tra certificate và hostname khi biến này có giá trị. Dùng HTTPS khi truy cập vì cookie production được đánh dấu Secure.

## Giữ dữ liệu hiện tại

Bootstrap chỉ tạo cấu trúc trống và admin mới. Muốn giữ dữ liệu local, dùng Workbench Data Export xuất database `ql_ktx` gồm cấu trúc, dữ liệu, trigger, routines và views; nhập vào MySQL cloud trước khi cho website sử dụng. Không import các lệnh DROP/CREATE database gốc vào database tên khác của nhà cung cấp. File export có dữ liệu cá nhân và hash mật khẩu: không commit vào repository công khai.

Không chạy `sample_data.sql` trên database đang dùng. Database cũ chưa nâng cấp cần chạy `python -m database.manage migrate` với biến kết nối **trỏ đúng cloud** trong môi trường quản trị; lệnh có backup nhưng không tự chạy khi website khởi động.

## Kiểm tra sau deploy

- `/healthz` trả 200 khi đọc được bảng Users; trả 503 và không lộ thông tin kết nối nếu không đọc được.
- Đăng nhập, thêm dịch vụ thử trên website, kiểm tra trong MySQL cloud.
- Chạy một báo cáo và kiểm tra các thao tác giới hạn phòng/xe.
- Restart ứng dụng và xác nhận bản ghi vẫn còn trong database cloud.
- Mở link trên điện thoại dùng mạng di động để kiểm tra truy cập ngoài máy cá nhân.

Lựa chọn gói hosting/database và chi phí thực hiện trong tài khoản của chủ dự án. Các file cấu hình không tự tạo tài khoản hosting hoặc public URL.

Tài liệu nền tảng: https://docs.railway.com/databases/mysql · https://railway.com/guides/flask · https://render.com/docs/deploy-mysql
