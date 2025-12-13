import sqlite3
import datetime as dt

PURGE_INTERVAL_MINUTES = 60
SNAPSHOT_INTERVAL_MINUTES = 60

CREATE_SQL = [
"""
CREATE TABLE IF NOT EXISTS DB_SIZE_SNAPSHOTS (
    Timestamp           TEXT NOT NULL,
    Object_Type         TEXT NOT NULL,
    Object_Name         TEXT NOT NULL,
    Bytes               INTEGER NOT NULL,
    Method              TEXT
);
CREATE INDEX IF NOT EXISTS IX_DB_SIZE_SNAPSHOTS_TS ON DB_SIZE_SNAPSHOTS(Timestamp);
""",
"""
CREATE TABLE IF NOT EXISTS BME280_READINGS (
    Id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp           TEXT NOT NULL,
    Temperature         REAL NOT NULL,
    Pressure            REAL NOT NULL,
    Humidity            REAL NOT NULL,
    Bus                 INTEGER NOT NULL,
    Address             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS IX_BME280_READINGS_TS ON BME280_READINGS (Timestamp);
""",
"""
CREATE TABLE IF NOT EXISTS VEML7700_READINGS (
    Id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp           TEXT NOT NULL,
    ALS                 INTEGER NOT NULL,
    White               INTEGER NOT NULL,
    Illuminance         REAL NOT NULL,
    Gain                REAL NOT NULL,
    IntegrationTime     INTEGER NOT NULL,
    Bus                 INTEGER NOT NULL,
    Address             TEXT NOT NULL,
    IsSaturated         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS IX_VEML7700_READINGS_TS ON VEML7700_READINGS (Timestamp);
""",
"""
CREATE TABLE IF NOT EXISTS SGP40_READINGS (
    Id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp           TEXT NOT NULL,
    SRAW                INTEGER NOT NULL,
    VOCIndex            INTEGER NOT NULL,
    Label               TEXT NOT NULL,
    Rating              TEXT NOT NULL,
    Bus                 INTEGER NOT NULL,
    Address             TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS IX_SGP40_READINGS_TS ON SGP40_READINGS (Timestamp);
"""
]

PURGE_SQL = [
"""
DELETE FROM BME280_READINGS WHERE Timestamp <= ?;
""",
"""
DELETE FROM VEML7700_READINGS WHERE Timestamp <= ?;
""",
"""
DELETE FROM SGP40_READINGS WHERE Timestamp <= ?;
""",
"""
DELETE FROM DB_SIZE_SNAPSHOTS WHERE Timestamp <= ?;
"""
]

INSERT_SIZES_SQL = """
INSERT INTO DB_SIZE_SNAPSHOTS (Timestamp, Object_Type, Object_Name, Bytes, Method)
VALUES (?,?,?,?,?);
"""

INSERT_BME_SQL = """
INSERT INTO BME280_READINGS (Timestamp, Temperature, Pressure, Humidity, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?);
"""

INSERT_VEML_SQL = """
INSERT INTO VEML7700_READINGS (Timestamp, ALS, White, Illuminance, IsSaturated, Gain, IntegrationTime, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

INSERT_SGP_SQL = """
INSERT INTO SGP40_READINGS (Timestamp, SRAW, VOCIndex, Label, Rating, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?, ?);
"""

SELECT_TABLES_SQL = """
SELECT name FROM sqlite_master
WHERE type='table' AND name NOT LIKE 'sqlite_%'
ORDER BY name;
"""

SELECT_TABLE_SIZES_DBSTAT = """
WITH objs AS (
    SELECT ? AS name
    UNION ALL
    SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=?
)
SELECT COALESCE(SUM(d.pgsize),0)
FROM objs o
LEFT JOIN dbstat d ON d.name=o.name
WHERE d.schema='main';
"""

SELECT_SNAPSHOT_FOR_TODAY = """
SELECT 1
FROM DB_SIZE_SNAPSHOTS
WHERE Object_Type = 'db'
AND Object_Name = 'main'
AND Timestamp >= ?
AND Timestamp <  ?
LIMIT 1;
"""

class Database:
    db_path: str = None
    retention: int = None
    bus: int = None
    bme_addr: str = None
    veml_addr: str = None
    veml_gain: float = None
    veml_integration_time_ms: int = None
    sgp_addr: str = None

    def __init__(self, db_path, retention, bus, bme_address, veml_address, veml_gain, veml_integration_time_ms, sgp_address):
        self.db_path = db_path
        self.retention = retention
        self.bus = bus
        self.bme_address = bme_address
        self.veml_address = veml_address
        self.veml_gain = veml_gain
        self.veml_integration_time_ms = veml_integration_time_ms
        self.sgp_address = sgp_address
        self.last_purged = None
        self.last_snapshot_check = None

    def _has_dbstat(self, con):
        try:
            con.execute("SELECT 1 FROM dbstat LIMIT 1;").fetchone()
            return True
        except sqlite3.Error:
            return False

    def _table_columns(self, con, table):
        cols = con.execute(f"PRAGMA table_info({table});").fetchall()
        # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
        return [c[1] for c in cols]

    def _payload_expr_for_table(self, con, table):
        cols = self._table_columns(con, table)
        # LENGTH() works for TEXT/BLOB; for numeric it returns length of text representation if cast
        parts = [f"IFNULL(LENGTH(CAST({c} AS BLOB)),0)" for c in cols]
        return " + ".join(parts) if parts else "0"

    def _has_snapshot_for_today(self, con):
        # Get the date range
        start = dt.datetime.now(dt.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + dt.timedelta(days=1)

        try:
            # Look for at least one snapshot row in the specified date range
            row = con.execute(SELECT_SNAPSHOT_FOR_TODAY, (start.isoformat(), end.isoformat())).fetchone()
            return row is not None
        except:
            pass

    def _insert_reading(self, sql, params):
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.cursor()
            cur.execute(sql, params)
            con.commit()
        finally:
            con.close()

    def create_database(self):
        con = sqlite3.connect(self.db_path)
        for sql in CREATE_SQL:
            con.executescript(sql)
            con.commit()
        con.close()

    def purge(self):
        # Check there's a retention period applied
        if self.retention > 0:
            # Get the current timestamp and find out how long it is since old data was last purged. Only
            # purge old data periodically
            now = dt.datetime.now(dt.timezone.utc)
            elapsed = PURGE_INTERVAL_MINUTES if self.last_purged is None else (now - self.last_purged).total_seconds() / 60.0
            if elapsed >= PURGE_INTERVAL_MINUTES:
                # Set the "last purged" timestamp
                self.last_purged = now

                # Connect to the database and purge old data
                timestamp = now - dt.timedelta(minutes=self.retention)
                cutoff = timestamp.replace(microsecond=0).isoformat() + "Z"
                con = sqlite3.connect(self.db_path)
                cur = con.cursor()
                for sql in PURGE_SQL:
                    cur.execute(sql, (cutoff,))
                con.commit()
                con.close()

    def snapshot_sizes(self):
        # Get the current timestamp and find out how long it is since old data was last purged. Only
        # purge old data periodically
        now = dt.datetime.now(dt.timezone.utc)
        elapsed = SNAPSHOT_INTERVAL_MINUTES if self.last_snapshot_check is None else (now - self.last_snapshot_check).total_seconds() / 60.0
        if elapsed >= SNAPSHOT_INTERVAL_MINUTES:
            # Set the "last snapshot check" timestamp
            self.last_snapshot_check = now

            # See if we have a size snapshot for today. If not, create one
            con = sqlite3.connect(self.db_path)
            if not self._has_snapshot_for_today(con):
                # Capture the timestamp for "now" (UTC)
                ts = now.replace(microsecond=0).isoformat()

                # Database size
                con = sqlite3.connect(self.db_path)
                page_count = con.execute("PRAGMA page_count;").fetchone()[0]
                page_size  = con.execute("PRAGMA page_size;").fetchone()[0]
                con.execute(INSERT_SIZES_SQL, (ts, "db", "main", page_count * page_size, "pragma_pages"))

                # Get a list of tables
                tables = [r[0] for r in con.execute(SELECT_TABLES_SQL).fetchall()]

                if self._has_dbstat(con):
                    # Per-table bytes (table + indexes) using dbstat
                    for t in tables:
                        b = con.execute(SELECT_TABLE_SIZES_DBSTAT, (t, t)).fetchone()[0]
                        con.execute(INSERT_SIZES_SQL, (ts, "table", t, int(b), "dbstat"))
                else:
                    # Fallback: per-table “payload bytes” estimate (data only, not indexes)
                    for t in tables:
                        expr = self._payload_expr_for_table(con, t)
                        b = con.execute(f"SELECT COALESCE(SUM({expr}),0) FROM {t};").fetchone()[0]
                        con.execute(INSERT_SIZES_SQL, (ts, "table", t, int(b), "payload_estimate"))

                con.commit()
            con.close()

    def insert_bme_row(self, temperature, pressure, humidity):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        self._insert_reading(INSERT_BME_SQL, (timestamp, temperature, pressure, humidity, self.bus, self.bme_address))
        return timestamp

    def insert_veml_row(self, als, white, lux, is_saturated):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        self._insert_reading(INSERT_VEML_SQL, (timestamp, als, white, lux, is_saturated, self.veml_gain, self.veml_integration_time_ms, self.bus, self.veml_address))
        return timestamp

    def insert_sgp_row(self, sraw, index, label, rating):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        self._insert_reading(INSERT_SGP_SQL, (timestamp, sraw, index, label, rating, self.bus, self.sgp_address))
        return timestamp
