import pytest
from registry import AppSettings, DeviceFactory, DeviceType
from service import SGP40Sampler, BME280Sampler
from helpers import MockSMBus, MockI2CMsg, MockVOCAlgorithm, MockDatabase

def _crc8_sgp40(two_bytes: bytes) -> int:
    """
    CRC-8 for SGP40 (polynomial 0x31, init 0xFF).
    two_bytes must be length 2.
    """
    crc = 0xFF
    for b in two_bytes:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x31) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def construct_sampler(voc_algorithm, data, enabled):
    settings = AppSettings(AppSettings.default_settings_file())
    bus = MockSMBus(None, None, data)
    i2c_msg = MockI2CMsg()
    factory = DeviceFactory(bus, i2c_msg, voc_algorithm, settings)
    sensor = factory.create_device(DeviceType.SGP40)
    database = MockDatabase()
    bme_sampler = BME280Sampler(None, False, database)
    return SGP40Sampler(sensor, enabled, bme_sampler, database)


def test_sgp40_sampler_without_voc_algorithm():
    # No VOC algorithm -> VOC-related fields should be None
    sraw = 0x1000
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = _crc8_sgp40(bytes([msb, lsb]))
    sampler = construct_sampler(None, bytes([msb, lsb, crc]), True)
    sampler.sample_and_store(False)
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert True == sampler.is_available
    assert readings["sraw"] == sraw
    assert readings["voc_index"] is None
    assert readings["voc_label"] is None
    assert readings["voc_rating"] is None


@pytest.mark.parametrize(
    "voc_index, expected_label, expected_rating",
    [
        # Ranges/boundary values are taken from the sgp40 wrapper implementation
        (119,   "Good",          "****")
    ],
)
def test_sgp40_sampler_with_voc_algorithm(voc_index, expected_label, expected_rating):
    sraw = 0x2222
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = _crc8_sgp40(bytes([msb, lsb]))

    voc_algo = MockVOCAlgorithm(voc_index)
    sampler = construct_sampler(voc_algo, bytes([msb, lsb, crc]), True)
    sampler.sample_and_store(False)
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert True == sampler.is_available
    assert readings["sraw"] == sraw
    assert readings["voc_index"] == voc_index
    assert readings["voc_label"] == expected_label
    assert readings["voc_rating"] == expected_rating


def test_sgp40_sampler_enable_after_start():
    sraw = 0x1000
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = _crc8_sgp40(bytes([msb, lsb]))
    sampler = construct_sampler(None, bytes([msb, lsb, crc]), False)

    assert False == sampler.is_enabled

    sampler.sample_and_store(False)
    readings = sampler.latest
    assert None == readings

    sampler.enable()
    sampler.sample_and_store(False)
    readings = sampler.latest

    assert True == sampler.is_enabled
    assert readings["sraw"] == sraw
    assert readings["voc_index"] is None
    assert readings["voc_label"] is None
    assert readings["voc_rating"] is None


def test_sgp40_sampler_disabled_on_start():
    sampler = construct_sampler(None, None, False)
    sampler.sample_and_store(False)
    readings = sampler.latest

    assert None == readings
    assert False == sampler.is_enabled
    assert True == sampler.is_available


def test_sgp40_sampler_with_no_sensor():
    sampler = SGP40Sampler(None, True, None, MockDatabase())
    assert False == sampler.is_enabled
    assert False == sampler.is_available
