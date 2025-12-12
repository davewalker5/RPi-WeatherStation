const RANGES = {
    temperature: { min: -10, max: 40 },
    humidity: { min: 0, max: 100 },
    pressure: { min: 980, max: 1040 },
    illuminance: { min: 0, max: 10000 },
    voc: { min: 0, max: 500 }
};

function clamp(x, a, b) { return Math.min(b, Math.max(a, x)); }
function pct(x, min, max) { return (clamp(x, min, max) - min) / (max - min); }

function setGauge(svg, value, min, max, color) {
    const arc = svg.querySelector(".arc");
    const r = 46;
    const c = 2 * Math.PI * r;
    arc.style.strokeDasharray = `${c} ${c}`;
    const p = pct(value, min, max);
    arc.style.strokeDashoffset = `${c * (1 - p)}`;
    if (color) arc.style.stroke = color;
}

function setBar(el, value, min, max, color) {
    const p = pct(value, min, max);
    el.style.width = `${Math.round(p * 100)}%`;
    if (color) el.style.background = color;
}

function setStars(container, n) {
    container.innerHTML = "";
    const rating = clamp(Math.round(n), 1, 5);
    for (let i = 1; i <= 5; i++) {
        const s = document.createElement("span");
        s.className = "star" + (i <= rating ? " on" : "");
        s.textContent = "★";
        container.appendChild(s);
    }
}

function updateBME280(data) {
    if (data != null) {
        // Store the sensor values
        document.getElementById("temperature").textContent = data.temperature_c;
        document.getElementById("humidity").textContent = data.humidity_pct;
        document.getElementById("pressure").textContent = data.pressure_hpa;

        // Set the gauge colours and values
        const tempColor = (data.temperature_c >= 28) ? "var(--warn)" : (data.temperature_c <= 0) ? "var(--bad)" : "var(--accent)";
        setGauge(document.getElementById("temperatureGauge"), data.temperature_c, RANGES.temperature.min, RANGES.temperature.max, tempColor);
        setGauge(document.getElementById("humidityGauge"), data.humidity_pct, RANGES.humidity.min, RANGES.humidity.max, "var(--accent)");
        setGauge(document.getElementById("pressureGauge"), data.pressure_hpa, RANGES.pressure.min, RANGES.pressure.max, "var(--accent)");
    }
}

function  updateVEML7700(data) {
    if (data != null) {
        // Store the sensor values
        document.getElementById("illuminance").textContent = data.illuminance_lux;

        // Set the bar value
        setBar(document.getElementById("illuminanceBar"), data.illuminance_lux, RANGES.illuminance.min, RANGES.illuminance.max, "var(--accent)");

        // Set the illuminance level assessment
        const lux = data.illuminance_lux ?? 0;
        document.getElementById("illuminanceNotes").textContent =
            lux < 50 ? "Very dim" :
            lux < 300 ? "Indoor" :
            lux < 2000 ? "Bright indoor / shade" :
            lux < 10000 ? "Overcast daylight" : "Bright daylight";
    }
}

function updateSGP40(data) {
    if (data != null) {
        // Store the sensor values and label
        document.getElementById("vocIndex").textContent = data.voc_index;
        document.getElementById("vocLabel").textContent = data.voc_label;

        // Set the bar color and value
        const aqColor = (data.voc_rating <= 2) ? "var(--bad)" : (data.voc_rating >= 4) ? "var(--good)" : "var(--warn)";
        setBar(document.getElementById("vocBar"), data.voc_index, RANGES.voc.min, RANGES.voc.max, aqColor);

        // Set the star rating
        const rating = data.voc_rating ?? "";
        setStars(document.getElementById("vocRatingStars"), rating.length);
    }
}

async function refresh() {
    const res = await fetch("/api/current", { cache: "no-store" });
    const d = await res.json();

    // Write the response data to the raw data area
    document.getElementById("raw").textContent = JSON.stringify(d, null, 2);

    // Set the last updated text
    const dt = new Date();
    document.getElementById("updated").textContent = `Updated: ${dt.toLocaleString()}`;

    // Update the readings from each sensor
    updateBME280(d.bme);
    updateVEML7700(d.veml);
    updateSGP40(d.sgp);

}

refresh();
setInterval(refresh, 60000);