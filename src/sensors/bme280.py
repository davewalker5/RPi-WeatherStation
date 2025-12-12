import time
from .bme280_compensation import BME280Compensation


class BME280(BME280Compensation):
    def __init__(self, bus, address):
        super().__init__(bus, address)

        # Configure: humidity x1; temp/press x1; normal mode
        self._write_u8(0xF2, 0x01)
        self._write_u8(0xF4, 0x27)
        time.sleep(0.1)

    def read(self):
        data = self.sm_bus.read_i2c_block_data(self.address, 0xF7, 8)
        adc_p = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_t = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_h = (data[6] << 8) | data[7]

        # Calibrate the readings
        t_fine, temp_c = self.compensate_temperature(adc_t)
        pressure_hpa = self.compensate_pressure(t_fine, adc_p)
        humidity = self.compensate_humidity(t_fine, adc_h)

        return temp_c, pressure_hpa, humidity
