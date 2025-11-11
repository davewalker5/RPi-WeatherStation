from .bme280 import BME280
from .database import insert_row, query_last_row
from http.server import BaseHTTPRequestHandler
import json
import datetime as dt


class RequestHandler(BaseHTTPRequestHandler):
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