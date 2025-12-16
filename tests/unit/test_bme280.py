import pytest
from sensors import BME280
from helpers import MockSMBus, BME280_TRIMMING_PARAMETERS


ROOM_STANDARD = {
    "block": [85, 28, 112, 125, 93, 240, 142, 35],
    "temperature": 21.0,
    "pressure": 1013.0027734375,
    "humidity": 49.998046875
}

WARM_DRY = {
    "block": [87, 194, 112, 130, 201, 240, 126, 163],
    "temperature": 28.0,
    "pressure": 1005.0026953125,
    "humidity": 30.0087890625
}

WARM_HUMID = {
    "block": [88, 116, 240, 130, 201, 240, 169, 7],
    "temperature": 28.0,
    "pressure": 999.999375,
    "humidity": 85.0078125
}

COOL_DRY = {
    "block": [81, 163, 240, 116, 215, 240, 126, 123],
    "temperature": 10.01,
    "pressure": 1019.990390625,
    "humidity": 30.0009765625
}

COLD_NEAR_MIN = {
    "block": [69, 44, 240, 81, 243, 240, 135, 103],
    "temperature": -35.0,
    "pressure": 1030.0007421875,
    "humidity": 39.994140625
}

HOT_NEAR_MAX = {
    "block": [105, 66, 240, 171, 19, 240, 120, 151],
    "temperature": 80.0,
    "pressure": 950.0034765625,
    "humidity": 19.99609375
}

HIGH_ALTITUDE = {
    "block": [112, 96, 240, 112, 247, 240, 142, 159],
    "temperature": 5.01,
    "pressure": 800.000625,
    "humidity": 50.0068359375
}

LOW_PRESSURE_STORM = {
    "block": [88, 207, 240, 116, 215, 240, 174, 175],
    "temperature": 10.01,
    "pressure": 969.9954296875,
    "humidity": 89.99609375
}

HUMIDITY_CLIP_LOW = {
    "block": [85, 28, 112, 125, 93, 240, 0, 0],
    "temperature": 21.0,
    "pressure": 1013.0027734375,
    "humidity": 0.0
}

HUMIDITY_CLIP_HIGH = {
    "block": [85, 28, 112, 125, 93, 240, 191, 255],
    "temperature": 21.0,
    "pressure": 1013.0027734375,
    "humidity": 100.0
}


@pytest.mark.parametrize("fixture", [
    ROOM_STANDARD,
    WARM_DRY,
    WARM_HUMID,
    COOL_DRY,
    COLD_NEAR_MIN,
    HOT_NEAR_MAX,
    HIGH_ALTITUDE,
    LOW_PRESSURE_STORM,
    HUMIDITY_CLIP_LOW,
    HUMIDITY_CLIP_HIGH
])
def test_bme280_wrapper(fixture):
    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, fixture["block"], None)
    sensor = BME280(bus=bus, address=MockSMBus.BME280_ADDRESS, mux_address=None, channel=None)

    T, P, H = sensor.read()

    assert T == pytest.approx(fixture["temperature"], abs=0.2)
    assert P == pytest.approx(fixture["pressure"], abs=2.0)
    assert H == pytest.approx(fixture["humidity"], abs=3.0)
