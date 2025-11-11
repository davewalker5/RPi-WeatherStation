import sqlite3


CREATE_SQL = """
CREATE TABLE IF NOT EXISTS readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc        TEXT NOT NULL,               -- ISO8601 UTC
    temperature_c REAL NOT NULL,
    pressure_hpa  REAL NOT NULL,
    humidity_pct  REAL NOT NULL,
    bus           INTEGER NOT NULL,
    addr_hex      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_readings_ts ON readings(ts_utc);
"""

INSERT_SQL = """
INSERT INTO readings (ts_utc, temperature_c, pressure_hpa, humidity_pct, bus, addr_hex)
VALUES (?, ?, ?, ?, ?, ?);
"""

QUERY_LAST_SQL = """
SELECT ts_utc, temperature_c, pressure_hpa, humidity_pct
FROM readings ORDER BY id DESC LIMIT 1;
"""


def create_database(db_path):
    con = sqlite3.connect(db_path)
    con.executescript(CREATE_SQL)
    con.commit()
    return con

def insert_row(db_path, table_name, bus, addr, ts, t, p, h):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(INSERT_SQL.replace("readings", table_name), (ts, t, p, h, bus, addr))
    con.commit()
    con.close()

def query_last_row(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    row = con.execute(QUERY_LAST_SQL).fetchone()
    con.close()
    return row