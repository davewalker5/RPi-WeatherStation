import pytest
from sensors import VEML7700
from i2c import I2CDevice
from helpers import MockSMBus, MockI2CMsg

REG_ALS = 0x04
REG_WHITE = 0x05

@pytest.mark.parametrize("fixture", [
    {"raw_als": 0, "raw_white": 0, "als_bytes": [0, 0], "white_bytes": [0, 0], "lux": 0.0},
    {"raw_als": 5898, "raw_white": 5898, "als_bytes": [10, 23], "white_bytes": [10, 23], "lux": 1358.8992},
    {"raw_als": 11796, "raw_white": 11796, "als_bytes": [20, 46], "white_bytes": [20, 46], "lux": 2717.7984},
    {"raw_als": 17694, "raw_white": 17694, "als_bytes": [30, 69], "white_bytes": [30, 69], "lux": 4076.6976},
    {"raw_als": 23592, "raw_white": 23592, "als_bytes": [40, 92], "white_bytes": [40, 92], "lux": 5435.5968},
    {"raw_als": 29490, "raw_white": 29490, "als_bytes": [50, 115], "white_bytes": [50, 115], "lux": 6794.496},
    {"raw_als": 35388, "raw_white": 35388, "als_bytes": [60, 138], "white_bytes": [60, 138], "lux": 8153.3952},
    {"raw_als": 41286, "raw_white": 41286, "als_bytes": [70, 161], "white_bytes": [70, 161], "lux": 9512.294399999999},
    {"raw_als": 47184, "raw_white": 47184, "als_bytes": [80, 184], "white_bytes": [80, 184], "lux": 10871.1936},
    {"raw_als": 53082, "raw_white": 53082, "als_bytes": [90, 207], "white_bytes": [90, 207], "lux": 12230.0928},
    {"raw_als": 58980, "raw_white": 58980, "als_bytes": [100, 230], "white_bytes": [100, 230], "lux": 13588.992}
])
def test_veml7700_wrapper_normal_range(fixture):
    bus = MockSMBus(None, { REG_ALS: fixture["als_bytes"], REG_WHITE: fixture["white_bytes"]}, None)
    i2c_msg = MockI2CMsg()
    device = I2CDevice(bus, MockSMBus.VEML7700_ADDRESS, i2c_msg)
    sensor = VEML7700(i2c_device=device, gain=0.25, integration_time_ms=100)

    als, white, lux = sensor.read()

    assert als == fixture["raw_als"]
    assert white == fixture["raw_white"]
    assert lux == pytest.approx(fixture["lux"], abs=0.2)
