import pytest
from registry import AppSettings, DeviceFactory, DeviceType
from service import BME280Sampler
from helpers import MockSMBus, BME280_TRIMMING_PARAMETERS, MockDatabase


def construct_sampler(data, enabled):
    settings = AppSettings(AppSettings.default_settings_file())
    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, data, None)
    factory = DeviceFactory(bus, None, None, settings)
    sensor = factory.create_device(DeviceType.BME280)
    return BME280Sampler(sensor, enabled, MockDatabase())

ROOM_STANDARD = {
    "block": [85, 28, 112, 125, 93, 240, 142, 35],
    "temperature": 21.0,
    "pressure": 1013.0027734375,
    "humidity": 49.998046875
}

@pytest.mark.parametrize("fixture", [
    ROOM_STANDARD
])
def test_bme280_sampler(fixture):
    sampler = construct_sampler(fixture["block"], True)
    sampler.sample_and_store()
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert True == sampler.is_available
    assert readings["temperature_c"] == pytest.approx(fixture["temperature"], abs=0.2)
    assert readings["pressure_hpa"] == pytest.approx(fixture["pressure"], abs=2.0)
    assert readings["humidity_pct"] == pytest.approx(fixture["humidity"], abs=3.0)


def test_bme280_sampler_disabled_on_start():
    sampler = construct_sampler(None, False)
    sampler.sample_and_store()
    readings = sampler.latest

    assert None == readings
    assert False == sampler.is_enabled
    assert True == sampler.is_available


@pytest.mark.parametrize("fixture", [
    ROOM_STANDARD
])
def test_bme280_sampler_enable_after_start(fixture):
    sampler = construct_sampler(fixture["block"], False)

    assert False == sampler.is_enabled

    sampler.sample_and_store()
    readings = sampler.latest
    assert None == readings

    sampler.enable()
    sampler.sample_and_store()
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert readings["temperature_c"] == pytest.approx(fixture["temperature"], abs=0.2)
    assert readings["pressure_hpa"] == pytest.approx(fixture["pressure"], abs=2.0)
    assert readings["humidity_pct"] == pytest.approx(fixture["humidity"], abs=3.0)


def test_bme280_sampler_with_no_sensor():
    sampler = BME280Sampler(None, True, MockDatabase())
    assert False == sampler.is_enabled
    assert False == sampler.is_available
