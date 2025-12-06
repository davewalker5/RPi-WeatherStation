from .sampler import Sampler
from http.server import BaseHTTPRequestHandler
import json
import datetime as dt


class RequestHandler(BaseHTTPRequestHandler):
    sampler: Sampler = None

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _health(self):
        """
        Construct a health check response
        """
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        return self._json(200, {"status": "ok", "time": timestamp})

    def _latest_bme_readings(self):
        """
        Handle a request for the latest BME280 readings captured by the sampler
        """
        readings = self.sampler.get_latest_bme()
        return self._json(200, readings)

    def _latest_veml_readings(self):
        """
        Handle a request for the latest VEML7700 readings captured by the sampler
        """
        readings = self.sampler.get_latest_veml()
        return self._json(200, readings)

    def _latest_sgp_readings(self):
        """
        Handle a request for the latest SGP40 readings captured by the sampler
        """
        readings = self.sampler.sgp()
        return self._json(200, readings)

    def do_GET(self):
        """
        Handle a GET request
        """

        # Define handlers by routes
        routes = {
            "/api/health" : self._health,
            "/api/bme": self._latest_bme_readings,
            "/api/veml": self._latest_veml_readings,
            "/api/sgp": self._latest_sgp_readings,
        }

        # If the current route is in the dictionary, call the handler and return the
        # result
        route = self.path.casefold()
        if route in routes:
            return routes[route]()

        # Any other route generates a 404 error 
        return self._json(404, {"error": "not found"})
