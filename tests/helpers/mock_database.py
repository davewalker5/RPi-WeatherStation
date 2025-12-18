class MockDatabase:
    def create_database(self):
        pass

    def purge(self):
        pass

    def snapshot_sizes(self):
        pass

    def insert_bme_row(self, temperature, pressure, humidity):
        pass

    def insert_veml_row(self, als, white, lux, is_saturated):
        pass

    def insert_sgp_row(self, sraw, index, label, rating):
        pass
