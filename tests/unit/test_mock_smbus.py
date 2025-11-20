from helpers import MockSMBus, BME280_TRIMMING_PARAMETERS

def test_read_trimming_parameters():
    bus = MockSMBus(BME280_TRIMMING_PARAMETERS, None)
    for register, expected in BME280_TRIMMING_PARAMETERS.items():
        actual = bus.read_byte_data(None, register)
        assert actual == expected
