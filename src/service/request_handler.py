from .sampler import Sampler
from .http_method import HttpMethod
from registry import DeviceType
from http.server import BaseHTTPRequestHandler
import json
import datetime as dt


class RequestHandler(BaseHTTPRequestHandler):
    sampler: Sampler = None

    ROUTES = {
        HttpMethod.GET: {
            "/api/health": "_health",
            "/api/status": "_status",
            "/api/bme/latest": "_latest_bme_readings",
            "/api/veml/latest": "_latest_veml_readings",
            "/api/sgp/latest": "_latest_sgp_readings",
        },
        HttpMethod.PUT: {
            "/api/bme/on": "_bme_on",
            "/api/bme/off": "_bme_off",
            "/api/veml/on": "_veml_on",
            "/api/veml/off": "_veml_off",
            "/api/sgp/on": "_sgp_on",
            "/api/sgp/off": "_sgp_off",
            "/api/lcd/on": "_lcd_on",
            "/api/lcd/off": "_lcd_off"
        }
    }

    def _get_handler(self, verb: HttpMethod, route):
        """
        Get the handler for a given verb and route
        """
        # If the verb is in the ROUTES dictionary and the route is in the dictionary for that
        # verb, return the handler
        if verb.value in self.ROUTES and route in self.ROUTES[verb]:
            return getattr(self, self.ROUTES[verb][route])

        # Fall through to "no handler"
        return None

    def _json(self, status: int, payload: dict):
        """
        Convert the payload to JSON and send it as the response
        """
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

    def _status(self):
        """
        Handle a request for the status of all the devices
        """
        timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat() + "Z"
        return self._json(200, {"status": "ok", "time": timestamp})

    def _latest_bme_readings(self):
        """
        Handle a request for the latest BME280 readings captured by the sampler
        """
        readings = self.sampler.get_latest_bme()
        return self._json(200, readings)

    def _bme_on(self):
        """
        Enable the BME280
        """
        self.sampler.enable_device(DeviceType.BME280)
        return self._health()

    def _bme_off(self):
        """
        Disable the BME280
        """
        self.sampler.disable_device(DeviceType.BME280)
        return self._health()

    def _latest_veml_readings(self):
        """
        Handle a request for the latest VEML7700 readings captured by the sampler
        """
        readings = self.sampler.get_latest_veml()
        return self._json(200, readings)

    def _veml_on(self):
        """
        Enable the VEML7700
        """
        self.sampler.enable_device(DeviceType.VEML7700)
        return self._health()

    def _veml_off(self):
        """
        Disable the VEML7700
        """
        self.sampler.disable_device(DeviceType.VEML7700)
        return self._health()

    def _latest_sgp_readings(self):
        """
        Handle a request for the latest SGP40 readings captured by the sampler
        """
        readings = self.sampler.get_latest_sgp()
        return self._json(200, readings)

    def _sgp_on(self):
        """
        Enable the SGP40
        """
        self.sampler.enable_device(DeviceType.SGP40)
        return self._health()

    def _sgp_off(self):
        """
        Disable the SGP40
        """
        self.sampler.disable_device(DeviceType.SGP40)
        return self._health()

    def _lcd_on(self):
        """
        Enable the LCD
        """
        self.sampler.enable_device(DeviceType.LCD)
        return self._health()

    def _lcd_off(self):
        """
        Disable the LCD
        """
        self.sampler.disable_device(DeviceType.LCD)
        return self._health()

    def do_GET(self):
        """
        Handle a GET request
        """
        # Get the handler
        route = self.path.casefold()
        handler = self._get_handler(HttpMethod.GET, route)

        # If there's a handler defined, call it and return the value it returns
        if handler:
            return handler()

        # Any other route generates a 404 error 
        return self._json(404, {"error": f"GET {route} not found"})

    def do_PUT(self):
        """
        Handle a PUT request
        """
        # Get the handler
        route = self.path.casefold()
        handler = self._get_handler(HttpMethod.PUT, route)

        # If there's a handler defined, call it and return the value it returns
        if handler:
            return handler()

        # Any other route generates a 404 error 
        return self._json(404, {"error": f"PUT {route} not found"})
