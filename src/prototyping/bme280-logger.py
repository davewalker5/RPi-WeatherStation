#!/usr/bin/env python3
"""
BME280 → SQLite console logger for Raspberry Pi (Pi 1B friendly)

- Pure Python (uses smbus2 + sqlite3 from stdlib)
- Creates the SQLite DB/table automatically
- CLI options: interval, bus, address, db path, one-shot, table name
"""

import argparse
import datetime as dt
import sqlite3
import time
import signal
import sys

from smbus2 import SMBus

STOP = False

def _sig_handler(signum, frame):
    global STOP
    STOP = True

# --------------------- BME280 low-level (no external libs) ---------------------

class BME280:
    def __init__(self, bus=1, address=0x76):
        self.busnum = bus
        self.addr = address
        self.bus = SMBus(bus)

        # Read calibration data
        self.dig_T1 = self._read_u16(0x88)
        self.dig_T2 = self._read_s16(0x8A)
        self.dig_T3 = self._read_s16(0x8C)

        self.dig_P1 = self._read_u16(0x8E)
        self.dig_P2 = self._read_s16(0x90)
        self.dig_P3 = self._read_s16(0x92)
        self.dig_P4 = self._read_s16(0x94)
        self.dig_P5 = self._read_s16(0x96)
        self.dig_P6 = self._read_s16(0x98)
        self.dig_P7 = self._read_s16(0x9A)
        self.dig_P8 = self._read_s16(0x9C)
        self.dig_P9 = self._read_s16(0x9E)

        self.dig_H1 = self._read_u8(0xA1)
        self.dig_H2 = self._read_s16(0xE1)
        self.dig_H3 = self._read_u8(0xE3)
        e4 = self._read_s8(0xE4)
        e5 = self._read_u8(0xE5)
        e6 = self._read_s8(0xE6)
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = self._read_s8(0xE7)

        # Configure: humidity x1; temp/press x1; normal mode
        self._write_u8(0xF2, 0x01)
        self._write_u8(0xF4, 0x27)
        time.sleep(0.1)

    # ---- I2C helpers
    def _read_u8(self, reg):
        return self.bus.read_byte_data(self.addr, reg)

    def _read_s8(self, reg):
        v = self._read_u8(reg)
        return v - 256 if v > 127 else v

    def _read_u16(self, reg):
        lo = self._read_u8(reg)
        hi = self._read_u8(reg + 1)
        return (hi << 8) | lo

    def _read_s16(self, reg):
        lo = self._read_u8(reg)
        hi = self._read_u8(reg + 1)
        val = (hi << 8) | lo
        return val - 65536 if val > 32767 else val

    def _write_u8(self, reg, val):
        self.bus.write_byte_data(self.addr, reg, val)

    # ---- read one sample (returns temp °C, pressure hPa, humidity %)
    def read(self):
        data = self.bus.read_i2c_block_data(self.addr, 0xF7, 8)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]

        # Temperature
        var1 = (((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        temp_c = ((t_fine * 5 + 128) >> 8) / 100.0

        # Pressure
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17)
        var2 = var2 + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            pressure_hpa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
            pressure_hpa = pressure / 25600.0

        # Humidity
        h = t_fine - 76800
        h = (((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15)
             * (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152)
             * self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = max(min(h, 419430400), 0)
        humidity = (h >> 12) / 1024.0

        return temp_c, pressure_hpa, humidity

# ---------------------------- SQLite persistence -----------------------------

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

def ensure_db(path):
    con = sqlite3.connect(path)
    con.executescript(CREATE_SQL)
    con.commit()
    return con

# ---------------------------------- Main -------------------------------------

def main():
    ap = argparse.ArgumentParser(description="BME280 → SQLite logger")
    ap.add_argument("--db", default="bme280.db", help="SQLite database path")
    ap.add_argument("--interval", type=float, default=60.0, help="Sample interval seconds")
    ap.add_argument("--bus", type=int, default=0, help="I2C bus number (0 or 1 on Pi 1B)")
    ap.add_argument("--addr", default="0x76", help="I2C address (0x76 or 0x77)")
    ap.add_argument("--table", default="readings", help="Table name to insert into")
    ap.add_argument("--once", action="store_true", help="Take one reading and exit")
    args = ap.parse_args()

    # install signal handlers for graceful stop
    signal.signal(signal.SIGINT, _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    addr = int(args.addr, 16)

    con = ensure_db(args.db)
    cur = con.cursor()

    sensor = BME280(bus=args.bus, address=addr)

    def insert_row(ts, t, p, h):
        cur.execute(INSERT_SQL.replace("readings", args.table),
                    (ts, t, p, h, args.bus, hex(addr)))
        con.commit()

    def one_sample():
        t, p, h = sensor.read()
        ts = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        insert_row(ts, t, p, h)
        print(f"{ts}  T={t:.2f}°C  P={p:.2f} hPa  H={h:.2f}%")

    if args.once:
        one_sample()
        return

    print(f"Logging to {args.db} (table `{args.table}`) every {args.interval}s "
          f"on bus {args.bus} addr {hex(addr)}. Ctrl-C to stop.")
    next_t = time.monotonic()
    while not STOP:
        try:
            one_sample()
        except OSError as ex:
            # typical I2C hiccup (loose wire etc.)
            ts = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            print(f"{ts}  I2C error: {ex}; retrying in {args.interval}s", file=sys.stderr)
        next_t += args.interval
        sleep_for = max(0.0, next_t - time.monotonic())
        time.sleep(sleep_for)

    print("Stopping…")
    con.close()

if __name__ == "__main__":
    main()