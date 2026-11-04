"""Deployment checks without cloud access or changes to the local database."""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from application import create_app
from config import Config, mysql_options
from deployment.bootstrap import REQUIRED_TABLES, initialize


class DeploymentTests(unittest.TestCase):
    def test_cloud_port_and_verified_tls(self):
        with patch.object(Config, "MYSQL_PORT", 12345), patch.object(Config, "MYSQL_SSL_CA", "/ca.pem"):
            opts = mysql_options("cloud")
        self.assertEqual(opts["port"], 12345)
        self.assertTrue(opts["ssl_verify_identity"])
        self.assertEqual(opts["database"], "cloud")

    def test_production_rejects_default_secret(self):
        with patch.dict(os.environ, APP_ENV="production"), patch.object(Config, "SECRET_KEY", "dev"):
            with self.assertRaises(RuntimeError):
                create_app()

    def test_health_detects_db_failure(self):
        import mysql.connector
        with patch.dict(os.environ, APP_ENV="development"):
            app = create_app()
        with patch("database.connection.get_db", side_effect=mysql.connector.Error("private details")):
            response = app.test_client().get("/healthz")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"private details", response.data)

    def test_password_reset_does_not_touch_database(self):
        with patch.dict(os.environ, APP_ENV="development"):
            app = create_app()
        with patch("routes.auth_routes.get_db") as get_db:
            response = app.test_client().post("/auth/forgot-password", data={"username": "admin"})
        self.assertEqual(response.status_code, 302)
        get_db.assert_not_called()

    def bootstrap_case(self, tables, password, count=1):
        db = MagicMock()
        cursor = db.cursor.return_value
        cursor.fetchone.side_effect = [(1,), (count,), (1,)] if tables else [(1,), (1,)]
        cursor.fetchall.return_value = [(name, "BASE TABLE") for name in tables]
        return db

    def test_existing_database_is_not_reinitialized(self):
        db = self.bootstrap_case(REQUIRED_TABLES, "")
        with patch("deployment.bootstrap.connect", return_value=db), patch("deployment.bootstrap.run_sql") as sql:
            initialize()
        sql.assert_not_called()
        db.commit.assert_not_called()
        db.close.assert_called_once()

    def test_partial_database_is_not_overwritten(self):
        db = self.bootstrap_case(["Users"], "")
        with patch("deployment.bootstrap.connect", return_value=db), patch("deployment.bootstrap.run_sql") as sql:
            with self.assertRaises(RuntimeError):
                initialize()
        sql.assert_not_called()

    def test_empty_database_requires_strong_admin_before_ddl(self):
        db = self.bootstrap_case([], "")
        with patch("deployment.bootstrap.connect", return_value=db), patch("deployment.bootstrap.run_sql") as sql, patch.dict(os.environ, ADMIN_PASSWORD=""):
            with self.assertRaises(RuntimeError):
                initialize()
        sql.assert_not_called()

    def test_initialization_seeds_no_default_accounts(self):
        db = self.bootstrap_case([], "")
        with patch("deployment.bootstrap.connect", return_value=db), patch("deployment.bootstrap.run_sql") as sql, patch.dict(os.environ, ADMIN_USERNAME="owner", ADMIN_PASSWORD="a-private-password-123"):
            initialize()
        self.assertEqual([call.args[1] for call in sql.call_args_list], ["schema.sql", "domain.sql"])
        insert = next(call for call in db.cursor.return_value.execute.call_args_list if "INSERT INTO Users" in call.args[0])
        self.assertEqual(insert.args[1][0], "owner")
        self.assertNotIn("a-private-password-123", insert.args[1])


if __name__ == "__main__":
    unittest.main()
