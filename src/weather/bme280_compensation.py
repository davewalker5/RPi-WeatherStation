from .bme280_calibration import BME280Calibration


class BME280Compensation(BME280Calibration):
    def __init__(self, sm_bus):
        super().__init__(sm_bus)

    # ---- External API
    def compensate_temperature(self, adc_t):
        var1 = (((adc_t >> 3) - (self.get_calibration_digit("T1") << 1)) * self.get_calibration_digit("T2")) >> 11
        var2 = (((((adc_t >> 4) - self.get_calibration_digit("T1")) * ((adc_t >> 4) - self.get_calibration_digit("T1"))) >> 12) * self.get_calibration_digit("T3")) >> 14
        t_fine = var1 + var2
        temp_c = ((t_fine * 5 + 128) >> 8) / 100.0
        return t_fine, temp_c

    def compensate_pressure(self, t_fine, adc_p):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.get_calibration_digit("P6")
        var2 = var2 + ((var1 * self.get_calibration_digit("P5")) << 17)
        var2 = var2 + (self.get_calibration_digit("P4") << 35)
        var1 = ((var1 * var1 * self.get_calibration_digit("P3")) >> 8) + ((var1 * self.get_calibration_digit("P2")) << 12)
        var1 = (((1 << 47) + var1) * self.get_calibration_digit("P1")) >> 33
        if var1 == 0:
            pressure_hpa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.get_calibration_digit("P9") * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.get_calibration_digit("P8") * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.get_calibration_digit("P7") << 4)
            pressure_hpa = pressure / 25600.0

        return pressure_hpa

    def compensate_humidity(self, t_fine, adc_h):
        h = t_fine - 76800
        h = (((((adc_h << 14) - (self.get_calibration_digit("H4") << 20) - (self.get_calibration_digit("H5") * h)) + 16384) >> 15)
             * (((((((h * self.get_calibration_digit("H6")) >> 10) * (((h * self.get_calibration_digit("H3")) >> 11) + 32768)) >> 10) + 2097152)
             * self.get_calibration_digit("H2") + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.get_calibration_digit("H1")) >> 4)
        h = max(min(h, 419430400), 0)
        humidity = (h >> 12) / 1024.0
        return humidity
