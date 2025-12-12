import pytest
from sensors import SGP40
from i2c import I2CDevice
from helpers import MockSMBus, MockI2CMsg, MockVOCAlgorithm


def construct_wrapper(voc_algorithm=None, read_bytes=None):
    """
    Helper that creates a new instance of the SGP40 wrapper using the mock SMBus

    If `read_bytes` is given, they are queued so that the first _measure_sraw()
    call will receive them as [MSB, LSB, CRC]
    """
    bus = MockSMBus(None, None, read_bytes)
    i2c_dev = I2CDevice(bus, MockSMBus.SGP40_ADDRESS, MockI2CMsg())
    wrapper = SGP40(i2c_dev, voc_algorithm=voc_algorithm, measurement_delay=0.0)
    return wrapper, bus


def test_crc8_sgp40_known_vector():
    wrapper, _ = construct_wrapper()
    # Lock in one arbitrary vector so future changes are caught
    crc = wrapper._crc8_sgp40(bytes([0xBE, 0xEF]))
    assert crc == 0x92  # 146 decimal


def test_humidity_to_ticks_clamps_and_scales():
    wrapper, _ = construct_wrapper()
    # Values from the scaling formula in the real implementation
    assert wrapper._humidity_to_ticks(-10.0) == 0
    assert wrapper._humidity_to_ticks(0.0) == 0
    assert wrapper._humidity_to_ticks(50.0) == 32768
    assert wrapper._humidity_to_ticks(100.0) == 65535
    assert wrapper._humidity_to_ticks(200.0) == 65535


def test_temperature_to_ticks_clamps_and_scales():
    wrapper, _ = construct_wrapper()
    assert wrapper._temperature_to_ticks(-100.0) == 0
    assert wrapper._temperature_to_ticks(-45.0) == 0
    assert wrapper._temperature_to_ticks(25.0) == 26214
    assert wrapper._temperature_to_ticks(130.0) == 65535
    assert wrapper._temperature_to_ticks(200.0) == 65535


def test_build_command_contents():
    wrapper, _ = construct_wrapper()
    cmd = wrapper._build_command(humidity=50.0, temperature=25.0)
    # From the implementation: [0x26, 0x0F, RH_MSB, RH_LSB, RH_CRC, T_MSB, T_LSB, T_CRC]
    assert cmd == bytes([0x26, 0x0F, 0x80, 0x00, 0xA2, 0x66, 0x66, 0x93])


def test_measure_sraw_happy_path_uses_i2c_and_returns_sraw():
    # Choose an arbitrary raw value and construct matching CRC
    dummy_wrapper, _ = construct_wrapper()
    sraw = 0x1234
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = dummy_wrapper._crc8_sgp40(bytes([msb, lsb]))

    wrapper, bus = construct_wrapper(read_bytes=bytes([msb, lsb, crc]))

    result = wrapper._measure_sraw(humidity=40.0, temperature=25.0)
    assert result == sraw

    # Expect two I2C transactions: one write (command) and one read (3 bytes)
    assert len(bus.i2c_messages) == 2

    write_msgs = bus.i2c_messages[0]
    assert len(write_msgs) == 1
    write_msg = write_msgs[0]
    assert write_msg["type"] == "write"
    assert write_msg["address"] == MockSMBus.SGP40_ADDRESS
    assert write_msg["buffer"] == wrapper._build_command(40.0, 25.0)

    read_msgs = bus.i2c_messages[1]
    assert len(read_msgs) == 1
    read_msg = read_msgs[0]
    assert read_msg["type"] == "read"
    assert read_msg["address"] == MockSMBus.SGP40_ADDRESS
    # bytes(msg) should yield exactly what we queued
    assert bytes(read_msg) == bytes([msb, lsb, crc])


def test_measure_sraw_bad_crc_raises_valueerror():
    dummy_wrapper, _ = construct_wrapper()
    sraw = 0x4321
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    good_crc = dummy_wrapper._crc8_sgp40(bytes([msb, lsb]))
    bad_crc = (good_crc + 1) & 0xFF

    wrapper, _ = construct_wrapper(read_bytes=bytes([msb, lsb, bad_crc]))

    with pytest.raises(ValueError, match="CRC"):
        wrapper._measure_sraw(humidity=50.0, temperature=20.0)


def test_measure_sraw_short_read_raises_ioerror(monkeypatch):
    wrapper, _ = construct_wrapper()

    # Skip the I2C plumbing here; just force the short read at the I2CDevice layer
    def fake_read_bytes_raw(length):
        return b"\x12\x34"  # only 2 bytes

    monkeypatch.setattr(wrapper.i2c_device, "read_bytes_raw", fake_read_bytes_raw)

    with pytest.raises(IOError):
        wrapper._measure_sraw(humidity=50.0, temperature=20.0)


def test_read_without_voc_algorithm():
    # No VOC algorithm -> VOC-related fields should be None
    dummy_wrapper, _ = construct_wrapper()
    sraw = 0x1000
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = dummy_wrapper._crc8_sgp40(bytes([msb, lsb]))

    wrapper, _ = construct_wrapper(voc_algorithm=None, read_bytes=bytes([msb, lsb, crc]))

    sraw_out, voc_index, voc_label, voc_rating = wrapper.read(humidity=45.0, temperature=23.0)
    assert sraw_out == sraw
    assert voc_index is None
    assert voc_label is None
    assert voc_rating is None

@pytest.mark.parametrize(
    "voc_index, expected_label, expected_rating",
    [
        # Ranges/boundary values are taken from the sgp40 wrapper implementation
        (0,    "Excellent",     "*****"),
        (79,   "Excellent",     "*****"),
        (80,   "Good",          "****"),
        (119,   "Good",          "****"),
        (120,   "Moderate",      "***"),
        (159,   "Moderate",      "***"),
        (160,  "Unhealthy",     "**"),
        (219,  "Unhealthy",     "**"),
        (220,  "Very Unhealthy","*"),
    ],
)
def test_read_with_voc_algorithm_and_classification(voc_index, expected_label, expected_rating):
    dummy_wrapper, _ = construct_wrapper()
    sraw = 0x2222
    msb = (sraw >> 8) & 0xFF
    lsb = sraw & 0xFF
    crc = dummy_wrapper._crc8_sgp40(bytes([msb, lsb]))

    voc_algo = MockVOCAlgorithm(voc_index)
    wrapper, bus = construct_wrapper(voc_algorithm=voc_algo, read_bytes=bytes([msb, lsb, crc]))

    sraw_out, voc_index, voc_label, voc_rating = wrapper.read(humidity=50.0, temperature=25.0)

    assert sraw_out == sraw
    assert voc_algo.last_sraw == sraw
    assert voc_index == voc_index
    assert voc_label == expected_label
    assert voc_rating == expected_rating


@pytest.mark.parametrize(
    "voc_index, expected_label, expected_rating",
    [
        # Ranges/boundary values are taken from the sgp40 wrapper implementation
        (0,    "Excellent",     "*****"),
        (79,   "Excellent",     "*****"),
        (80,   "Good",          "****"),
        (119,   "Good",          "****"),
        (120,   "Moderate",      "***"),
        (159,   "Moderate",      "***"),
        (160,  "Unhealthy",     "**"),
        (219,  "Unhealthy",     "**"),
        (220,  "Very Unhealthy","*"),
    ],
)
def test_classify_voc_index_ranges(voc_index, expected_label, expected_rating):
    wrapper, _ = construct_wrapper()
    label, rating = wrapper._classify_voc_index(voc_index)
    assert label == expected_label
    assert rating == expected_rating
