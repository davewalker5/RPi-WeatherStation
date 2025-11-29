import pytest
from helpers import MockSMBus, BME280_TRIMMING_PARAMETERS

def test_read_trimming_parameters():
    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, None)
    for register, expected in BME280_TRIMMING_PARAMETERS.items():
        actual = bus.read_byte_data(None, register)
        assert actual == expected


@pytest.mark.parametrize("fixture", [
    [85, 28, 112, 125, 93, 240, 142, 35]
])
def test_read_i2c_block_data(fixture):
    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, fixture)
    actual = bus.read_i2c_block_data(MockSMBus.BME280_ADDRESS, None, len(fixture))
    assert actual == fixture
