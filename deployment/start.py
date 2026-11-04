"""Production entry point for Render and Railway."""
import os


def main():
    os.environ.setdefault("APP_ENV", "production")
    # Validate configuration before any schema changes.
    from application import create_app
    create_app()
    if os.getenv("DATABASE_BOOTSTRAP") == "1":
        from deployment.bootstrap import initialize
        initialize()
    os.execvp("gunicorn", [
        "gunicorn", "--bind", f"0.0.0.0:{int(os.getenv('PORT', '8080'))}",
        "--workers", "2", "--threads", "4", "--timeout", "60",
        "--access-logfile", "-", "--error-logfile", "-", "run:app",
    ])


if __name__ == "__main__":
    main()
