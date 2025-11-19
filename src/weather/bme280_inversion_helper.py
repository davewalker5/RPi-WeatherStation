from .bme280_compensation import BME280Compensation


class BME280InversionHelper(BME280Compensation):
    def __init__(self, sm_bus):
        super().__init__(sm_bus)
        self.sm_bus = sm_bus

    def _binary_search_adc(self, f, target, lo, hi, maximum_iterations, tolerance):
        """
        Generic binary search over integer ADC range
        """
        best_adc = lo
        best_err = float("inf")

        while lo <= hi and maximum_iterations > 0:
            maximum_iterations -= 1
            mid = (lo + hi) // 2
            value = f(mid)
            err = value - target

            # Track the best value
            if abs(err) < best_err:
                best_err = abs(err)
                best_adc = mid

            if abs(err) <= tolerance:
                break

            if err < 0:
                # value < target - need larger ADC
                lo = mid + 1
            else:
                hi = mid - 1

        return best_adc


    def _adc20_to_bytes(self, adc):
        # Convert an ADC value to bytes as they appear in the BME280 registers
        # BME280 stores MSB, LSB, XLSB (XLSB uses top 4 bits)
        msb = (adc >> 12) & 0xFF
        lsb = (adc >> 4) & 0xFF
        xlsb = (adc & 0x0F) << 4
        return [msb, lsb, xlsb]

    def _adc16_to_bytes(self, adc):
        msb = (adc >> 8) & 0xFF
        lsb = adc & 0xFF
        return [msb, lsb]

    def _find_adc_t_for_temperature(self, target):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_t):
            _, temp_c = self.compensate_temperature(adc_t)
            return temp_c

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.01)

    def _find_adc_p_for_pressure(self, target, t_fine):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_p):
            pressure = self.compensate_pressure(t_fine, adc_p)
            return pressure

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.1)

    def _find_adc_h_for_humidity(self, target, t_fine):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_h):
            H = self.compensate_humidity(t_fine, adc_h)
            return H

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.1)

    def make_test_fixture(self, target_temperature, target_pressure, target_humidity):
        # Find adc_t
        adc_t = self._find_adc_t_for_temperature(target_temperature)
        t_fine, temperature = self.compensate_temperature(adc_t)

        # Find adc_p and adc_h for t_fine
        adc_p = self._find_adc_p_for_pressure(target_pressure, t_fine)
        adc_h = self._find_adc_h_for_humidity(target_humidity, t_fine)

        # Convert to bytes as they appear in the BME280 registers
        pressure_bytes = self._adc20_to_bytes(adc_p)
        temperature_bytes  = self._adc20_to_bytes(adc_t)
        humidity_bytes   = self._adc16_to_bytes(adc_h)

        # The measurement block 0xF7–0xFE is:
        # [
        #   pressure_msb,
        #   pressure_lsb,
        #   pressure_xlsb,
        #   temperature_msb,
        #   temperature_lsb,
        #   temperature_xlsb,
        #   humidity_msb,
        #   humidity_lsb
        # ]
        block = pressure_bytes + temperature_bytes + humidity_bytes

        return {
            "adc_T": adc_t,
            "adc_P": adc_p,
            "adc_H": adc_h,
            "block": block,
            "actual_temperature": temperature,
            "actual_pressure": self.compensate_pressure(adc_p, t_fine),
            "actual_humidity": self.compensate_humidity(adc_h, t_fine),
        }
