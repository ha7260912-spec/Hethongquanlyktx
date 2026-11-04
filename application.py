import os
import mysql.connector
from flask import Flask
from config import Config
from database import connection

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if os.getenv("APP_ENV") == "production" and (
        not app.secret_key or app.secret_key == "dev" or len(app.secret_key) < 32
    ):
        raise RuntimeError("Production requires SECRET_KEY with at least 32 characters.")
    
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
    from routes.billing_routes import bp as billing_bp
    from routes.report_routes import bp as report_bp
    app.register_blueprint(billing_bp)
    app.register_blueprint(report_bp)
    from routes.ticket_routes import bp as ticket_bp
    app.register_blueprint(ticket_bp)

    @app.get("/healthz")
    def health():
        try:
            cursor = connection.get_db().cursor()
            try:
                cursor.execute("SELECT 1 FROM Users LIMIT 1")
                cursor.fetchall()
            finally:
                cursor.close()
        except mysql.connector.Error:
            return {"status": "unavailable"}, 503
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="127.0.0.1", port=5000)
