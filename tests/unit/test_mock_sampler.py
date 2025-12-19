import pytest
from helpers import MockSampler

BME_READINGS = {
    "humidity_pct": 44.69,
    "pressure_hpa": 1008.93,
    "temperature_c": 18,
    "time_utc": "2025-12-19T09:28:19+00:00Z"
}

VEML_READINGS = {
    "als": 35434,
    "gain": 2,
    "illuminance_lux": 255.12,
    "integration_time_ms": 400,
    "saturated": False,
    "time_utc": "2025-12-19T09:50:07+00:00Z",
    "white": 65535
}

SGP_READINGS = {
    "humidity_pc": 42.63,
    "sraw": 31940,
    "temperature_c": 19.01,
    "time_utc": "2025-12-19T09:52:26+00:00Z",
    "voc_index": 33,
    "voc_label": "Excellent",
    "voc_rating": "*****"
}

@pytest.mark.parametrize("fixture", [
    BME_READINGS
])
def test_get_latest_bme(fixture):
    sampler = MockSampler([fixture], None, None)
    readings = sampler.get_latest_bme()

    for k, v in fixture.items():
        assert v == readings[k]


@pytest.mark.parametrize("fixture", [
    VEML_READINGS
])
def test_get_latest_veml(fixture):
    sampler = MockSampler(None, [fixture], None)
    readings = sampler.get_latest_veml()

    for k, v in fixture.items():
        assert v == readings[k]


@pytest.mark.parametrize("fixture", [
    SGP_READINGS
])
def test_get_latest_veml(fixture):
    sampler = MockSampler(None, None, [fixture])
    readings = sampler.get_latest_sgp()

    for k, v in fixture.items():
        assert v == readings[k]
