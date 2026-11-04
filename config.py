import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "ql_ktx")
    MYSQL_SSL_CA = os.getenv("MYSQL_SSL_CA", "")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("APP_ENV") == "production"


def mysql_options(database=None):
    options = dict(
        host=Config.MYSQL_HOST, port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER, password=Config.MYSQL_PASSWORD,
        database=database, charset="utf8mb4",
        collation="utf8mb4_unicode_ci", connection_timeout=10,
    )
    if Config.MYSQL_SSL_CA:
        options.update(ssl_ca=Config.MYSQL_SSL_CA,
                       ssl_verify_cert=True, ssl_verify_identity=True)
    return options
