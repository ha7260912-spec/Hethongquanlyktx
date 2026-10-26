from flask import Flask
from config import Config
from database import connection

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Khởi tạo kết nối Database
    connection.init_app(app)

    # Đăng ký tất cả các Routes (Blueprints) của Người A
    from routes.main_routes import bp as main_bp
    from routes.auth_routes import bp as auth_bp
    from routes.sinhvien_routes import bp as sv_bp
    from routes.phong_routes import bp as phong_bp
    from routes.dangkyphong_routes import bp as dk_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(sv_bp)
    app.register_blueprint(phong_bp)
    app.register_blueprint(dk_bp)

    # Người B sẽ đăng ký Blueprint của họ ở dưới này...
    from routes.dichvu_routes import dichvu_bp
    app.register_blueprint(dichvu_bp)
    from routes.sudungdichvu_routes import sudungdichvu_bp
    app.register_blueprint(sudungdichvu_bp)
    from routes.khach_routes import khach_bp
    app.register_blueprint(khach_bp)
    from routes.tham_routes import tham_bp
    app.register_blueprint(tham_bp)
    from routes.xe_routes import xe_bp
    app.register_blueprint(xe_bp)
    from routes.luotguixe_routes import luotguixe_bp
    app.register_blueprint(luotguixe_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)
