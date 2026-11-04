"""Verify the supplied original SQL on a new isolated database, skipping its reset commands."""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from application import create_app
from config import Config
from database.manage import connect, migrate, statements
from repositories import report_repo
from repositories.billing_repo import period


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'ql_ktx_verify_[A-Za-z0-9_]+', args.database):
        parser.error('Only isolated ql_ktx_verify_* databases are allowed.')
    db = connect()
    cur = db.cursor()
    cur.execute(f'CREATE DATABASE IF NOT EXISTS `{args.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    db.database = args.database
    cur.execute('SHOW TABLES')
    if cur.fetchall():
        raise ValueError('Verification target must be empty.')
    for sql in statements(Path(args.source).read_text(encoding='utf-8-sig')):
        if re.match(r'^(DROP\s+DATABASE|CREATE\s+DATABASE|USE\s|DESCRIBE\s)',sql,re.I):
            continue
        cur.execute(sql)
        if cur.with_rows:
            cur.fetchall()
    db.commit()
    cur.close()
    migrate(db)
    db.close()
    Config.MYSQL_DB = args.database
    app = create_app()
    with app.app_context():
        first, end = period(10,2024)
        for key in report_repo.catalog():
            report_repo.run(key,first,end,first,end)
        result = report_repo.run('Q01',first,end,first,end)['rows']
        actual = {r['MaSV']:r['TongTien'] for r in result}
        assert actual == {'SV01':783000,'SV02':615000,'SV03':890000}, actual
        assert sum(r['DoanhThu'] for r in report_repo.run('Q04',first,end,first,end)['rows']) == 488000
    print('PASS original SQL upgrade; all 14 queries; October 2024 expected totals.')


if __name__ == '__main__':
    main()
