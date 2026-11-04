import mysql.connector
from flask import g
from config import Config, mysql_options

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(**mysql_options(Config.MYSQL_DB))
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)
