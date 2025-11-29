from .bme280_trimming_parameters import BME280TrimmingParameters
from .bme280_trimming_parameters import DIG_T1, DIG_T2, DIG_T3
from .bme280_trimming_parameters import DIG_P1, DIG_P2, DIG_P3, DIG_P4, DIG_P5, DIG_P6, DIG_P7, DIG_P8, DIG_P9
from .bme280_trimming_parameters import DIG_H1, DIG_H2, DIG_H3, DIG_H4, DIG_H5, DIG_H6


class BME280Compensation(BME280TrimmingParameters):
    def __init__(self, sm_bus, address):
        super().__init__(sm_bus, address)

    def compensate_temperature(self, adc_t):
        var1 = (((adc_t >> 3) - (self.get_trimming_parameter(DIG_T1) << 1)) * self.get_trimming_parameter(DIG_T2)) >> 11
        var2 = (((((adc_t >> 4) - self.get_trimming_parameter(DIG_T1)) * ((adc_t >> 4) - self.get_trimming_parameter(DIG_T1))) >> 12) * self.get_trimming_parameter(DIG_T3)) >> 14
        t_fine = var1 + var2
        temp_c = ((t_fine * 5 + 128) >> 8) / 100.0
        return t_fine, temp_c

    def compensate_pressure(self, t_fine, adc_p):
        var1 = t_fine - 128000
        var2 = var1 * var1 * self.get_trimming_parameter(DIG_P6)
        var2 = var2 + ((var1 * self.get_trimming_parameter(DIG_P5)) << 17)
        var2 = var2 + (self.get_trimming_parameter(DIG_P4) << 35)
        var1 = ((var1 * var1 * self.get_trimming_parameter(DIG_P3)) >> 8) + ((var1 * self.get_trimming_parameter(DIG_P2)) << 12)
        var1 = (((1 << 47) + var1) * self.get_trimming_parameter(DIG_P1)) >> 33
        if var1 == 0:
            pressure_hpa = 0.0
        else:
            p = 1048576 - adc_p
            p = (((p << 31) - var2) * 3125) // var1
            var1 = (self.get_trimming_parameter(DIG_P9) * (p >> 13) * (p >> 13)) >> 25
            var2 = (self.get_trimming_parameter(DIG_P8) * p) >> 19
            pressure = ((p + var1 + var2) >> 8) + (self.get_trimming_parameter(DIG_P7) << 4)
            pressure_hpa = pressure / 25600.0

        return pressure_hpa

    def compensate_humidity(self, t_fine, adc_h):
        h = t_fine - 76800
        h = (((((adc_h << 14) - (self.get_trimming_parameter(DIG_H4) << 20) - (self.get_trimming_parameter(DIG_H5) * h)) + 16384) >> 15)
             * (((((((h * self.get_trimming_parameter(DIG_H6)) >> 10) * (((h * self.get_trimming_parameter(DIG_H3)) >> 11) + 32768)) >> 10) + 2097152)
             * self.get_trimming_parameter(DIG_H2) + 8192) >> 14))
        h = h - (((((h >> 15) * (h >> 15)) >> 7) * self.get_trimming_parameter(DIG_H1)) >> 4)
        h = max(min(h, 419430400), 0)
        humidity = (h >> 12) / 1024.0
        return humidity
