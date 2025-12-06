class MockVOCAlgorithm:
    def __init__(self, value):
        self.value = value
        self.last_sraw = None

    def process(self, sraw):
        self.last_sraw = sraw
        return self.value
