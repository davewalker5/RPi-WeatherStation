from helpers import MockLCD, MockSampler
from service import LCDDisplay
from pprint import pprint as pp

DEGREE = chr(223)

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

def _confirm_valid_timestamp(timestamp):
    tokens = timestamp.split(":")
    assert len(tokens) == 3

    for i in range(3):
        try:
            value = int(tokens[0])
            upper = 23 if i == 0 else 59
            assert value >= 0
            assert value <= upper
        except ValueError:
            pass

def _confirm_displayed_output(lcd, values, member, label, units):
    line, text = lcd.output[0]
    assert 1 == line
    _confirm_valid_timestamp(text)

    line, text = lcd.output[1]
    assert 2 == line
    assert f"{label} = {values[member]}{units}" == text


def test_display_readings():
    sampler = MockSampler([BME_READINGS], [VEML_READINGS], [SGP_READINGS])
    lcd = MockLCD(None, None, None, None, None, None)
    display = LCDDisplay(lcd, True)

    # Temperature
    display.display_next(sampler)
    assert 1 == lcd.calls["clear"]
    assert 2 == lcd.calls["write"]
    _confirm_displayed_output(lcd, BME_READINGS, "temperature_c", "T", f"{DEGREE}C")

    # Pressure
    display.display_next(sampler)
    assert 2 == lcd.calls["clear"]
    assert 4 == lcd.calls["write"]
    _confirm_displayed_output(lcd, BME_READINGS, "pressure_hpa", "P", f" hPa")

    # Humidity
    display.display_next(sampler)
    assert 3 == lcd.calls["clear"]
    assert 6 == lcd.calls["write"]
    _confirm_displayed_output(lcd, BME_READINGS, "humidity_pct", "H", f"%")

    # Illuminance
    display.display_next(sampler)
    assert 4 == lcd.calls["clear"]
    assert 8 == lcd.calls["write"]
    _confirm_displayed_output(lcd, VEML_READINGS, "illuminance_lux", "I", f" lux")

    # Air quality rating
    display.display_next(sampler)
    assert 5 == lcd.calls["clear"]
    assert 10 == lcd.calls["write"]
    _confirm_displayed_output(lcd, SGP_READINGS, "voc_rating", "VOC", "")

def test_disable_enable():
    lcd = MockLCD(None, None, None, None, None, None)
    display = LCDDisplay(lcd, True)
    display.disable()

    assert not display.is_enabled
    assert display.is_available
    assert 1 == lcd.calls["clear"]
    assert 1 == lcd.calls["backlight_off"]

    display.enable()

    assert display.is_enabled
    assert display.is_available
    assert 2 == lcd.calls["clear"]
    assert 1 == lcd.calls["backlight_off"]
    assert 1 == lcd.calls["backlight_on"]

def test_create_disabled():
    lcd = MockLCD(None, None, None, None, None, None)
    _ = LCDDisplay(lcd, False)

    assert 1 == lcd.calls["clear"]
    assert 1 == lcd.calls["backlight_off"]

def test_create_with_no_lcd():
    display = LCDDisplay(None, True)

    assert not display.is_enabled
    assert not display.is_available

def test_write_when_disabled():
    sampler = MockSampler([BME_READINGS], [VEML_READINGS], [SGP_READINGS])
    lcd = MockLCD(None, None, None, None, None, None)
    display = LCDDisplay(lcd, False)
    display.display_next(sampler)

    assert 0 == lcd.calls["write"]
    assert 0 == len(lcd.output)
