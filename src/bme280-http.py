#!/usr/bin/env python3
"""
HTTP JSON server for BME280 on Raspberry Pi

Endpoints:
  GET /api/now          -> read the sensor now; return JSON
  GET /api/last         -> read the most recent row from SQLite (optional --db)
  GET /healthz          -> {"status":"ok"}

Usage examples:
  python3 bme280_http.py --port 8080
  python3 bme280_http.py --addr 0x77 --bus 0 --port 8000
  python3 bme280_http.py --db bme280.db --port 8080
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse
import datetime as dt
import json
import signal
import sqlite3
import time
from smbus2 import SMBus

STOP = False

# --------------------- BME280 (same logic as logger) --------------------- #
class BME280:
    def __init__(self, bus=1, address=0x76):
        self.addr = address
        self.bus = SMBus(bus)

        self.dig_T1 = self._ru16(0x88)
        self.dig_T2 = self._rs16(0x8A)
        self.dig_T3 = self._rs16(0x8C)

        self.dig_P1 = self._ru16(0x8E)
        self.dig_P2 = self._rs16(0x90)
        self.dig_P3 = self._rs16(0x92)
        self.dig_P4 = self._rs16(0x94)
        self.dig_P5 = self._rs16(0x96)
        self.dig_P6 = self._rs16(0x98)
        self.dig_P7 = self._rs16(0x9A)
        self.dig_P8 = self._rs16(0x9C)
        self.dig_P9 = self._rs16(0x9E)

        self.dig_H1 = self._ru8(0xA1)
        self.dig_H2 = self._rs16(0xE1)
        self.dig_H3 = self._ru8(0xE3)
        e4 = self._rs8(0xE4); e5 = self._ru8(0xE5); e6 = self._rs8(0xE6)
        self.dig_H4 = (e4 << 4) | (e5 & 0x0F)
        self.dig_H5 = (e6 << 4) | (e5 >> 4)
        self.dig_H6 = self._rs8(0xE7)

        # humidity x1; temp/press x1; normal mode
        self._wu8(0xF2, 0x01)
        self._wu8(0xF4, 0x27)
        time.sleep(0.1)

    def _ru8(self, r):  return self.bus.read_byte_data(self.addr, r)
    def _rs8(self, r):
        v = self._ru8(r); return v - 256 if v > 127 else v
    def _ru16(self, r):
        lo = self._ru8(r); hi = self._ru8(r+1); return (hi << 8) | lo
    def _rs16(self, r):
        lo = self._ru8(r); hi = self._ru8(r+1); v = (hi << 8) | lo
        return v - 65536 if v > 32767 else v
    def _wu8(self, r, v): self.bus.write_byte_data(self.addr, r, v)

    def read(self):
        d = self.bus.read_i2c_block_data(self.addr, 0xF7, 8)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        adc_h = (d[6] << 8) | d[7]

        # temperature
        var1 = (((adc_t >> 3) - (self.dig_T1 << 1)) * self.dig_T2) >> 11
        var2 = (((((adc_t >> 4) - self.dig_T1) * ((adc_t >> 4) - self.dig_T1)) >> 12) * self.dig_T3) >> 14
        t_fine = var1 + var2
        t_c = ((t_fine * 5 + 128) >> 8) / 100.0

        # pressure
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1 * self.dig_P5) << 17) + (self.dig_P4 << 35)
        var1 = ((var1 * var1 * self.dig_P3) >> 8) + ((var1 * self.dig_P2) << 12)
        var1 = (((1 << 47) + var1) * self.dig_P1) >> 33
        if var1 == 0:
            p_hpa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.dig_P9 * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.dig_P8 * p) >> 19
            p = ((p + var1 + var2) >> 8) + (self.dig_P7 << 4)
            p_hpa = p / 25600.0

        # humidity
        h = t_fine - 76800
        h = (((((adc_h << 14) - (self.dig_H4 << 20) - (self.dig_H5 * h)) + 16384) >> 15)
             * (((((((h * self.dig_H6) >> 10) * (((h * self.dig_H3) >> 11) + 32768)) >> 10) + 2097152)
             * self.dig_H2 + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.dig_H1) >> 4)
        h = max(min(h, 419430400), 0)
        rh = (h >> 12) / 1024.0

        return t_c, p_hpa, rh

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

QUERY_LAST_SQL = """
SELECT ts_utc, temperature_c, pressure_hpa, humidity_pct
FROM readings ORDER BY id DESC LIMIT 1;
"""

def ensure_db(db_path):
    print(f"Ensuring database {db_path} exists")
    con = sqlite3.connect(db_path)
    con.executescript(CREATE_SQL)
    con.commit()
    con.close()

def insert_row(db_path, bus, addr, ts, t, p, h):
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(INSERT_SQL, (ts, t, p, h, bus, addr))
    con.commit()
    con.close()

def query_last_row(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    row = con.execute(QUERY_LAST_SQL).fetchone()
    con.close()
    return row

# ------------------------- HTTP handler ------------------------- #
class Handler(BaseHTTPRequestHandler):
    # Injected at server init:
    sensor: BME280 = None
    db_path: str | None = None
    bus: int | None = None
    addr: str | None = None

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # small CORS nicety for browser testing
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        now_iso = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        if self.path.startswith("/health"):
            return self._json(200, {"status": "ok", "time": now_iso})

        if self.path.startswith("/api/now"):
            try:
                t, p, h = self.sensor.read()
                insert_row(self.db_path, self.bus, self.addr, now_iso, t, p, h)
                return self._json(200, {
                    "time_utc": now_iso,
                    "temperature_c": round(t, 2),
                    "pressure_hpa": round(p, 2),
                    "humidity_pct": round(h, 2),
                })
            except Exception as ex:
                return self._json(503, {"error": str(ex)})

        if self.path.startswith("/api/last"):
            if not self.db_path:
                return self._json(400, {"error": "no --db specified on server"})
            try:
                row = query_last_row(self.db_path)
                if not row:
                    return self._json(404, {"error": "no rows"})
                return self._json(200, {
                    "time_utc": row["ts_utc"],
                    "temperature_c": round(row["temperature_c"], 2),
                    "pressure_hpa": round(row["pressure_hpa"], 2),
                    "humidity_pct": round(row["humidity_pct"], 2),
                })
            except Exception as ex:
                return self._json(500, {"error": str(ex)})

        # fallback 404
        return self._json(404, {"error": "not found"})

    # Quiet the default noisy log
    def log_message(self, *args):
        pass

# ------------------------- Main ------------------------- #
def main():
    global cur

    ap = argparse.ArgumentParser(description="BME280 JSON HTTP server")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (use 0.0.0.0 to expose on LAN)")
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--addr", default="0x76")
    ap.add_argument("--db", default=None, help="optional SQLite path to enable /api/last")
    args = ap.parse_args()

    addr_hex = int(args.addr, 16)
    sensor = BME280(bus=args.bus, address=addr_hex)

    ensure_db(args.db)

    def _stop(signum, frame):
        global STOP; STOP = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    Handler.sensor = sensor
    Handler.db_path = args.db
    Handler.bus = args.bus
    Handler.addr = args.addr

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Serving on http://{args.host}:{args.port}  (bus={args.bus} addr={hex(addr_hex)})")
    if args.db:
        print(f"/api/last reads from: {args.db}")
    try:
        while not STOP:
            server.handle_request()
    finally:
        try:
            sensor.bus.close()
        except Exception:
            pass
        print("Server stopped.")

if __name__ == "__main__":
    main()
