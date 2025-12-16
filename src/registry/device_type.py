from enum import Enum

class DeviceType(str, Enum):
    MUX = "MUX"
    BME280 = "BME280"
    VEML7700 = "VEML7700"
    SGP40 = "SGP40"
    LCD = "LCD"
