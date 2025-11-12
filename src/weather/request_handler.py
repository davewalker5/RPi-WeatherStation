from .bme280 import BME280
from .database import Database
from http.server import BaseHTTPRequestHandler
import json
import datetime as dt


class RequestHandler(BaseHTTPRequestHandler):
    sensor: BME280 = None
    database: Database = None

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _timestamp(self):
        """
        Return the current date and time as UTC
        """
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"

    def _health(self):
        """
        Construct a health check response
        """
        timestamp = self._timestamp()
        return self._json(200, {"status": "ok", "time": timestamp})

    def _reading_now(self):
        """
        Handle a request for the current readling
        """
        try:
            # Read the sensor and write the results to the database
            timestamp = self._timestamp()
            temperature, pressure, humnidity = self.sensor.read()
            self.database.insert_row(timestamp, temperature, pressure, humnidity)

            # Return the results as JSON
            return self._json(200, {
                "time_utc": timestamp,
                "temperature_c": round(temperature, 2),
                "pressure_hpa": round(pressure, 2),
                "humidity_pct": round(humnidity, 2),
            })
        except Exception as ex:
            return self._json(503, {"error": str(ex)})

    def _last_reading(self):
        """
        Handle a request for the last reading written to the database
        """
        try:
            # Retrieve the row and check it's valid - if not, return a not found error
            row = self.database.query_last_row()
            if not row:
                return self._json(404, {"error": "no rows"})

            # Return the row of data as JSON
            return self._json(200, {
                "time_utc": row["Timestamp"],
                "temperature_c": round(row["Temperature"], 2),
                "pressure_hpa": round(row["Pressure"], 2),
                "humidity_pct": round(row["Humidity"], 2),
            })
        except Exception as ex:
            return self._json(500, {"error": str(ex)})

    def do_GET(self):
        """
        Handle a GET request
        """
        if self.path.casefold() == "/health":
            return self._health()

        if self.path.casefold() == "/api/now":
            return self._reading_now()

        if self.path.startswith("/api/last"):
            return self._last_reading()

        # Any other route generates a 404 error 
        return self._json(404, {"error": "not found"})
