import pytest
from registry import AppSettings, DeviceFactory, DeviceType
from service import VEML7700Sampler
from helpers import MockSMBus, MockI2CMsg, MockDatabase

REG_ALS = 0x04
REG_WHITE = 0x05

def construct_sampler(als_data, white_data, enabled):
    settings = AppSettings(AppSettings.default_settings_file())
    bus = MockSMBus(None, { REG_ALS: als_data, REG_WHITE: white_data }, None)
    i2c_msg = MockI2CMsg()
    factory = DeviceFactory(bus, i2c_msg, None, settings)
    sensor = factory.create_device(DeviceType.VEML7700)
    return VEML7700Sampler(sensor, enabled, MockDatabase())


@pytest.mark.parametrize("fixture", [
    {"raw_als": 23592, "raw_white": 23592, "als_bytes": [40, 92], "white_bytes": [40, 92], "lux": 5435.5968}
])
def test_veml7700_wrapper_normal_range(fixture):
    sampler = construct_sampler(fixture["als_bytes"], fixture["white_bytes"], True)
    sampler.sample_and_store()
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert True == sampler.is_available
    assert readings["als"] == fixture["raw_als"]
    assert readings["white"] == fixture["raw_white"]
    assert readings["illuminance_lux"] == pytest.approx(fixture["lux"], abs=0.2)


def test_veml7700_sampler_disabled_on_start():
    sampler = construct_sampler(None, None, False)
    sampler.sample_and_store()
    readings = sampler.latest

    assert None == readings
    assert False == sampler.is_enabled
    assert True == sampler.is_available


@pytest.mark.parametrize("fixture", [
    {"raw_als": 23592, "raw_white": 23592, "als_bytes": [40, 92], "white_bytes": [40, 92], "lux": 5435.5968}
])
def test_veml7700_wrapper_normal_range(fixture):
    sampler = construct_sampler(fixture["als_bytes"], fixture["white_bytes"], False)
 
    assert False == sampler.is_enabled

    sampler.sample_and_store()
    readings = sampler.latest
    assert None == readings

    sampler.enable()
    sampler.sample_and_store()
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert readings["als"] == fixture["raw_als"]
    assert readings["white"] == fixture["raw_white"]
    assert readings["illuminance_lux"] == pytest.approx(fixture["lux"], abs=0.2)


def test_veml7700_sampler_with_no_sensor():
    sampler = VEML7700Sampler(None, True, MockDatabase())
    assert False == sampler.is_enabled
    assert False == sampler.is_available
