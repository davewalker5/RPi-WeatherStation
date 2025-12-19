class MockSampler:
    def __init__(self, bme_values, veml_values, sgp_values):
        self.bme_values = bme_values
        self.bme_index = 0

        self.veml_values = veml_values
        self.veml_index = 0

        self.sgp_values = sgp_values
        self.sgp_index = 0

    def _get_next_value(self, values, index):
        if values:
            value = values[index]
            index = index + 1 if (index < len(values)) - 1 else 0
        else:
            value = None
            index = 0
        return value, index

    def get_latest_bme(self):
        value, self.bme_index = self._get_next_value(self.bme_values, self.bme_index)
        return value

    def get_latest_veml(self):
        value, self.veml_index = self._get_next_value(self.veml_values, self.veml_index)
        return value

    def get_latest_sgp(self):
        value, self.sgp_index = self._get_next_value(self.sgp_values, self.sgp_index)
        return value

    def get_device_status(self):
        return None

    def enable_device(self, _):
        pass

    def disable_device(self, _):
        pass

    def run(self):
        pass
