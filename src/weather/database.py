import sqlite3
from datetime import datetime, timedelta, timezone

PURGE_INTERVAL_MINUTES = 60

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS BME280_READINGS (
    Id              INTEGER PRIMARY KEY AUTOINCREMENT,
    Timestamp       TEXT NOT NULL,
    Temperature     REAL NOT NULL,
    Pressure        REAL NOT NULL,
    Humidity        REAL NOT NULL,
    Bus             INTEGER NOT NULL,
    Address         TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS IX_BME280_READINGS_TS ON BME280_READINGS (Timestamp);
"""

PURGE_SQL = """
DELETE FROM BME280_READINGS WHERE Timestamp <= ?;
"""

INSERT_SQL = """
INSERT INTO BME280_READINGS (Timestamp, Temperature, Pressure, Humidity, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?);
"""

QUERY_LAST_SQL = """
SELECT Timestamp, Temperature, Pressure, Humidity
FROM BME280_READINGS ORDER BY Id DESC LIMIT 1;
"""

class Database:
    db_path: str | None = None
    retention: int | None = None
    bus: int | None = None
    addr: str | None = None

    def __init__(self, db_path, retention, bus, address):
        self.db_path = db_path
        self.retention = retention
        self.bus = bus
        self.address = address
        self.last_purged = None

    def create_database(self):
        con = sqlite3.connect(self.db_path)
        con.executescript(CREATE_SQL)
        con.commit()
        con.close()

    def purge(self):
        # Get the current timestamp and find out how long it is since old data was last purged. Only
        # purge old data periodically
        now = datetime.now(timezone.utc)
        if (self.last_purged is None) or (((now - self.last_purged).total_seconds() / 60.0) >= PURGE_INTERVAL_MINUTES):
            # Set the "last purged" timestamp
            self.last_purged = now

            # Connect to the database and purge old data
            timestamp = now - timedelta(days=self.retention)
            con = sqlite3.connect(self.db_path)
            cur = con.cursor()
            cur.execute(PURGE_SQL, (timestamp,))
            con.commit()
            con.close()

    def insert_row(self, timestamp, temperature, pressure, humidity):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(INSERT_SQL, (timestamp, temperature, pressure, humidity, self.bus, self.address))
        con.commit()
        con.close()

    def query_last_row(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        row = con.execute(QUERY_LAST_SQL).fetchone()
        con.close()
        return row
