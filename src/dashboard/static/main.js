async function fetchCurrent() {
  const errorEl = document.getElementById("error");
  const updatedEl = document.getElementById("updated");

  errorEl.textContent = "";

  try {
    const res = await fetch("/api/current");
    const data = await res.json();

    if (data.error) {
      errorEl.textContent = data.error;
      return;
    }

    console.log(data);

    // Adjust these properties based on your actual JSON structure:
    document.getElementById("temperature").textContent = data.bme.temperature_c;
    document.getElementById("humidity").textContent = data.bme.humidity_pct;
    document.getElementById("pressure").textContent = data.bme.pressure_hpa;
    document.getElementById("lux").textContent = data.veml.illuminance_lux;
    document.getElementById("voc_label").textContent = data.sgp.voc_label;
    document.getElementById("voc_rating").textContent = data.sgp.voc_rating;

    const now = new Date();
    updatedEl.textContent = "Last updated: " + now.toLocaleTimeString();
  } catch (err) {
  }
}

// Fetch immediately on load
fetchCurrent();

// Then poll every 60 seconds
setInterval(fetchCurrent, 60000);
