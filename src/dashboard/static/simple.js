function renderRating(rating, max = 5) {
  const full = "★".repeat(rating);
  const empty = "☆".repeat(max - rating);
  return full + empty;
}

async function fetchCurrent() {
  const errorEl = document.getElementById("error");
  const updatedEl = document.getElementById("updated");

  errorEl.textContent = "";

  try {
    // Get the latest sensor readings
    const res = await fetch("/api/current");
    const data = await res.json();

    // If there's an error, report it
    if (data.error) {
      errorEl.textContent = data.error;
      return;
    }

    // Update the readings
    if (data.bme != null) {
      document.getElementById("temperature").textContent = data.bme.temperature_c;
      document.getElementById("humidity").textContent = data.bme.humidity_pct;
      document.getElementById("pressure").textContent = data.bme.pressure_hpa;
    }

    if (data.veml != null) {
      document.getElementById("lux").textContent = data.veml.illuminance_lux;
    }

    if (data.sgp != null) {
      document.getElementById("voc_label").textContent = data.sgp.voc_label;
      document.getElementById("voc_rating").textContent = renderRating(data.sgp.voc_rating.length);
    } else {
      document.getElementById("voc_rating").textContent = renderRating(0);
    }

    // Update the last refresh date
    const now = new Date();
    updatedEl.textContent = "Last updated: " + now.toLocaleTimeString();
  } catch (err) {
    errorEl.textContent = err;
  }
}

// Fetch immediately on load
fetchCurrent();

// Then poll every 60 seconds
setInterval(fetchCurrent, 60000);
