from sensors import BME280Compensation
import json


class BME280InversionHelper(BME280Compensation):
    def __init__(self, sm_bus, address):
        super().__init__(sm_bus, address)

    def _debug_pressure_range(self, t_fine):
        ADC_MIN = 0
        ADC_MAX = (1 << 20) - 1
        mid = (ADC_MIN + ADC_MAX) // 2

        print("P(ADC_MIN):", self.compensate_pressure(t_fine, ADC_MIN))
        print("P(mid):    ", self.compensate_pressure(t_fine, mid))
        print("P(ADC_MAX):", self.compensate_pressure(t_fine, ADC_MAX))

    def _debug_humidity_range(self, t_fine):
        ADC_MIN = 0
        ADC_MAX = (1 << 16) - 1
        mid = (ADC_MIN + ADC_MAX) // 2

        print("H(ADC_MIN):", self.compensate_humidity(t_fine, ADC_MIN))
        print("H(mid):    ", self.compensate_humidity(t_fine, mid))
        print("H(ADC_MAX):", self.compensate_humidity(t_fine, ADC_MAX))

    def _binary_search_adc(self, f, target, lo, hi, maximum_iterations, tolerance):
        """
        Generic binary search over integer ADC range.
        Works for both increasing and decreasing monotonic f.
        """
        # Evaluate endpoints once to detect direction
        f_lo = f(lo)
        f_hi = f(hi)
        increasing = f_hi > f_lo

        best_adc = lo
        best_err = abs(f_lo - target)

        while lo <= hi and maximum_iterations > 0:
            maximum_iterations -= 1
            mid = (lo + hi) // 2
            value = f(mid)
            err = value - target
            abs_err = abs(err)

            # Track the best value
            if abs_err < best_err:
                best_err = abs_err
                best_adc = mid

            if abs_err <= tolerance:
                break

            if increasing:
                # f increasing: move right if value < target
                if value < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            else:
                # f decreasing: move right if value > target
                if value > target:
                    lo = mid + 1
                else:
                    hi = mid - 1

        return best_adc

    def _adc20_to_bytes(self, adc):
        """
        Convert a 20-bit ADC value to bytes as they appear in the BME280 registers. The BME280
        stores MSB, LSB, XLSB with the latter using the top 4 bits
        """
        msb = (adc >> 12) & 0xFF
        lsb = (adc >> 4) & 0xFF
        xlsb = (adc & 0x0F) << 4
        return [msb, lsb, xlsb]

    def _adc16_to_bytes(self, adc):
        """
        Convert a 16-bit ADC value to bytes
        """
        msb = (adc >> 8) & 0xFF
        lsb = adc & 0xFF
        return [msb, lsb]

    def _find_adc_t_for_temperature(self, target, iterations, tolerance):
        """
        Given a target temperature, identify the corresponding ADC temperature value
         """
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_t):
            _, temp_c = self.compensate_temperature(adc_t)
            return temp_c

        return self._binary_search_adc(f, target, adc_min, adc_max, iterations, tolerance)

    def _find_adc_p_for_pressure(self, target, t_fine, iterations, tolerance):
        """
        Given a target pressure, identify the corresponding ADC pressure value
        """
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_p):
            return self.compensate_pressure(t_fine, adc_p)

        return self._binary_search_adc(f, target, adc_min, adc_max, iterations, tolerance)

    def _find_adc_h_for_humidity(self, target, t_fine, iterations, tolerance):
        """
        Given a target humidity, identify the corresponding ADC humidity value
        """
        adc_min = 0
        adc_max = (1 << 16) - 1  # 16-bit humidity ADC

        def f(adc_h):
            return self.compensate_humidity(t_fine, adc_h)

        return self._binary_search_adc(f, target, adc_min, adc_max, iterations, tolerance)

    def dump_bme280_trimming_parameters(self, address):
        """
        Dump the trimming parameters for a BME280
        """
        trimming_parameters = {}

        # Temperature and pressure registers 0x88–0xA1 (26 bytes)
        for reg in range(0x88, 0xA2):
            trimming_parameters[f"0x{reg:02X}"] = self.sm_bus.read_byte_data(address, reg)

        # Humidity registers 0xE1–0xE7 (7 bytes)
        for reg in range(0xE1, 0xE8):
            trimming_parameters[f"0x{reg:02X}"] = self.sm_bus.read_byte_data(address, reg)

        print(json.dumps(trimming_parameters, indent=2))

    def make_test_fixture(self, target_temperature, target_pressure, target_humidity, iterations, tolerance):
        """
        Given target values for temperature, pressure and humidity, calculate the relevant ADC
        values and measurement block
        """
        # Find adc_t
        adc_t = self._find_adc_t_for_temperature(target_temperature, iterations, tolerance)
        t_fine, temperature = self.compensate_temperature(adc_t)

        # Debugging
        # self._debug_pressure_range(t_fine)
        # self._debug_humidity_range(t_fine)

        # Find adc_p and adc_h for t_fine
        adc_p = self._find_adc_p_for_pressure(target_pressure, t_fine, iterations, tolerance)
        adc_h = self._find_adc_h_for_humidity(target_humidity, t_fine, iterations, tolerance)

        # Convert to bytes as they appear in the BME280 registers
        pressure_bytes = self._adc20_to_bytes(adc_p)
        temperature_bytes = self._adc20_to_bytes(adc_t)
        humidity_bytes = self._adc16_to_bytes(adc_h)

        # The measurement block is:
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
            "adc_t": adc_t,
            "adc_p": adc_p,
            "adc_h": adc_h,
            "block": block,
            "actual_temperature": temperature,
            "actual_pressure": self.compensate_pressure(t_fine, adc_p),
            "actual_humidity": self.compensate_humidity(t_fine, adc_h),
        }
