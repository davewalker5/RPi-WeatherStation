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

    def find_adc_t_for_temperature(self, target):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_t):
            _, temp_c = self.compensate_temperature(adc_t)
            return temp_c

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.01)

    def find_adc_p_for_pressure(self, target, t_fine):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_p):
            pressure = self.compensate_pressure(t_fine, adc_p)
            return pressure

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.1)

    def find_adc_H_for_humidity(self, target, t_fine):
        adc_min = 0
        adc_max = (1 << 20) - 1

        def f(adc_h):
            H = self.compensate_humidity(t_fine, adc_h)
            return H

        return self._binary_search_adc(f, target, adc_min, adc_max, 40, 0.1)
