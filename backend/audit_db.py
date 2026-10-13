import sqlite3, json
conn = sqlite3.connect('bharatscheme.db')
cur = conn.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])
for t in tables:
    count = cur.execute(f'SELECT COUNT(*) FROM {t[0]}').fetchone()[0]
    print(f'  {t[0]}: {count} rows')
for t in tables:
    schema = cur.execute(f'PRAGMA table_info({t[0]})').fetchall()
    print(f'  {t[0]} cols:', [col[1] for col in schema])
# Check a sample scheme
sample = cur.execute("SELECT id, slug, title_en, official_portal_url FROM schemes LIMIT 3").fetchall()
for row in sample:
    print('SCHEME:', row[0], '|', row[2][:40], '|', row[3])
# Check for NULL urls
null_urls = cur.execute("SELECT COUNT(*) FROM schemes WHERE official_portal_url IS NULL OR official_portal_url = ''").fetchone()[0]
print('Schemes with NULL/empty portal URLs:', null_urls)
conn.close()
print('DB AUDIT COMPLETE')
