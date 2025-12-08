import os
from flask import Flask, render_template, jsonify
import requests
from dotenv import load_dotenv

# Load .env into environment variables
load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/current")
def current_weather():
    WEATHER_SCHEME = os.getenv("WEATHER_SCHEME")
    WEATHER_HOST = os.getenv("WEATHER_HOST")
    WEATHER_PORT = os.getenv("WEATHER_PORT")
    WEATHER_API_BASE_URL = f"{WEATHER_SCHEME}://{WEATHER_HOST}:{WEATHER_PORT}/api"
    print(WEATHER_API_BASE_URL)

    try:
        # Get the latest BME280 readings
        resp = requests.get(f"{WEATHER_API_BASE_URL}/bme", timeout=3)
        resp.raise_for_status()
        bme_readings = resp.json()

        # Get the latest VEML7700 readings
        resp = requests.get(f"{WEATHER_API_BASE_URL}/veml", timeout=3)
        resp.raise_for_status()
        veml_readings = resp.json()

        # Get the latest SGP40 readings
        resp = requests.get(f"{WEATHER_API_BASE_URL}/sgp", timeout=3)
        resp.raise_for_status()
        sgp_readings = resp.json()

        # Build the response data
        data = {
            "bme": bme_readings,
            "veml": veml_readings,
            "sgp": sgp_readings
        }

    except Exception as e:
        return jsonify({"error": e}), 502

    return jsonify(data)

def main():
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    app.run(host="0.0.0.0", port=DASHBOARD_PORT, debug=True)


if __name__ == "__main__":
    main()
