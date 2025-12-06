import sqlite3
import datetime as dt

PURGE_INTERVAL_MINUTES = 60

CREATE_SQL = [
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
"""
]

INSERT_BME_SQL = """
INSERT INTO BME280_READINGS (Timestamp, Temperature, Pressure, Humidity, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?);
"""

INSERT_VEML_SQL = """
INSERT INTO VEML7700_READINGS (Timestamp, ALS, White, Illuminance, IsSaturated, Gain, IntegrationTime, Bus, Address)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
"""

INSERT_SGP_SQL = """
INSERT INTO SGP40_READINGS (Timestamp, SRAW, Index, Label)
VALUES (?, ?, ?, ?);
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

    def __init__(self, db_path, retention, bus, bme_address, veml_address, veml_gain, veml_integration_time_ms, sgp_addr):
        self.db_path = db_path
        self.retention = retention
        self.bus = bus
        self.bme_address = bme_address
        self.veml_address = veml_address
        self.veml_gain = veml_gain
        self.veml_integration_time_ms = veml_integration_time_ms
        self.sgp_addr = sgp_addr
        self.last_purged = None

    def create_database(self):
        con = sqlite3.connect(self.db_path)
        for sql in CREATE_SQL:
            con.executescript(sql)
        con.commit()
        con.close()

    def purge(self):
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

    def insert_bme_row(self, temperature, pressure, humidity):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(INSERT_BME_SQL, (timestamp, temperature, pressure, humidity, self.bus, self.bme_address))
        con.commit()
        con.close()
        return timestamp

    def insert_veml_row(self, als, white, lux, is_saturated):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(INSERT_VEML_SQL, (timestamp, als, white, lux, is_saturated, self.veml_gain, self.veml_integration_time_ms, self.bus, self.veml_address))
        con.commit()
        con.close()
        return timestamp

    def insert_sgp_row(self, sraw, index, label):
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        cur.execute(INSERT_SGP_SQL, (timestamp, sraw, index, label, self.bus, self.sgp_address))
        con.commit()
        con.close()
        return timestamp
