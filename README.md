# RPi-WeatherStation

[![GitHub issues](https://img.shields.io/github/issues/davewalker5/RPi-WeatherStation)](https://github.com/davewalker5/RPi-WeatherStation/issues)
[![Releases](https://img.shields.io/github/v/release/davewalker5/RPi-WeatherStation.svg?include_prereleases)](https://github.com/davewalker5/RPi-WeatherStation/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/davewalker5/RPi-WeatherStation/blob/master/LICENSE)
[![Language](https://img.shields.io/badge/language-python-blue.svg)](https://www.python.org)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/davewalker5/RPi-WeatherStation)](https://github.com/davewalker5/RPi-WeatherStation/)

## About

The RPi-WeatherStation is a simple home weather station based around a [Waveshare Raspberry Pi Zero WH](https://www.waveshare.com/wiki/Raspberry_Pi_Zero).

It provides command-line logging scripts for periodic capture of sensor readings and storage of those readings in a SQLite database.

It also implements a simple web service that can be run either as a command-lin script or installed as a systemd daemon. The web service periodically scans all the sensors, stores the data in a SQLite database and exposes endpoints to query the latest readings.

The following is a table of the current supported sensors:

| Measurement | Sensor | Reference |
| --- | --- | --- |
| Temperature | BME280 | [Bosch BME280 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf) |
| Pressure |  BME280 | [Bosch BME280 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf) |
| Humidity |  BME280 | [Bosch BME280 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf) |
| Illuminance | VEML7700 | [VEML7700 datasheet](https://www.vishay.com/docs/84286/veml7700.pdf) |
| Air Quality | SGP40 | [Sensiron SGP40 datasheet](https://sensirion.com/resource/datasheet/sgp40?utm_source=chatgpt.com) |

## Getting Started

Please see the [Wiki](https://github.com/davewalker5/RPi-WeatherStation/wiki) for configuration details and the user guide.

## Authors

- **Dave Walker** - _Initial work_

## Credits

- The BME280 integer compensation maths follows the [Bosch BME280 datasheet](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf) reference algorithm
- The implementation of the VEML7700 wrapper draws on the following references:
  - [Designing the VEML7700 Into an Application](https://www.vishay.com/docs/84323/designingveml7700.pdf)
  - [VEML7700 Data Sheet](https://www.vishay.com/docs/84286/veml7700.pdf)
  - [I2C Communication With The VEML7700 Light Sensor](https://forums.raspberrypi.com/viewtopic.php?t=198082)
- The implementation of the SGP40 wrapper draws on the following references:
  - [SGP40 Data Sheet](https://www.vishay.com/docs/84286/veml7700.pdf)
  - [SGP40 VOC Index](https://cdn.sparkfun.com/assets/e/9/3/f/e/GAS_AN_SGP40_VOC_Index_for_Experts_D1.pdf)

## Feedback

To file issues or suggestions, please use the [Issues](https://github.com/davewalker5/RPi-WeatherStation/issues) page for this project on GitHub.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
