import os
from flask import Flask, render_template, jsonify
import requests
from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()

app = Flask(__name__)

WEATHER_SCHEME = os.getenv("WEATHER_SCHEME", "http")
WEATHER_HOST = os.getenv("WEATHER_HOST", "localhost")
WEATHER_PORT = os.getenv("WEATHER_PORT", "80")
WEATHER_API_URL = f"{WEATHER_SCHEME}://{WEATHER_HOST}:{WEATHER_PORT}/api/current"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/current")
def current_weather():
    try:
        # Get the latest BME280 readings
        resp = requests.get("http://weatherpi.local/api/bme", timeout=3)
        resp.raise_for_status()
        bme_readings = resp.json()

        # Get the latest VEML7700 readings
        resp = requests.get("http://weatherpi.local/api/veml", timeout=3)
        resp.raise_for_status()
        veml_readings = resp.json()

        # Get the latest SGP40 readings
        resp = requests.get("http://weatherpi.local/api/sgp", timeout=3)
        resp.raise_for_status()
        sgp_readings = resp.json()

        # Build the response data
        data = {
            "bme": bme_readings,
            "veml": veml_readings,
            "sgp": sgp_readings
        }

    except Exception:
        return jsonify({"error": "Failed to contact weather station"}), 502

    return jsonify(data)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
