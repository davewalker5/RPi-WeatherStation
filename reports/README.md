# Weather Station Reporting

This folder contains Jupyter notebooks and supporting files for reporting on sensor readings stored in the Weather Station SQLite database. This provides more flexible reporting than the built-in reports in the application itself.

The following reports are currently available:

| Notebook                          | Report Type                                                                 |
| --------------------------------- | --------------------------------------------------------------------------- |
| bme280-health-missing-data.ipynb  | Missing value report for the BME280 sensors                                 |
| bme280-health-temperature.ipynb   | BME280 temperature sensor health                                            |
| bme280-health-pressure.ipynb      | BME280 pressure sensor health                                               |
| bme280-health-humidity.ipynb      | BME280 humidity sensor health                                               |
| daily-summary.ipynb               | Chart daily mean values for all applicable sensor readings                  |
| dew-point-comfort.ipynb           | Chart daily comfort score and diurnal dew point and comfort score variation |
| diurnal-heatmap.ipynb             | Chart diurnal heatmaps for all applicable sensor readings over time         |
| diurnal-pattern.ipynb             | Chart diurnal variation in all applicable sensor readings                   |
| pressure-event.ipynb              | Identify pressure events as a simple proxy for weather fronts               |
| sgp40-health-voc.ipynb            | SGP40 sensor health                                                         |
| veml7700-health-illuminance.ipynb | VEML7700 sensor health                                                      |
| voc-rating-distribution.ipynb     | Chart all-time VOC index distribution                                       |
| weekend-variation.ipynb           | Weekend vs weekday comparisons for all applicable sensor readings           |

## Setting Up the Reporting Environment

The reports have been written and tested using [Visual Studio Code](https://code.visualstudio.com/download) and the Jupyter extension from Microsoft using a Python virtual environment with the requirements listed in requirements.txt installed as the kernel for running the notebooks.

### Set Environment Variables

The following environment variable to be set *before* running code and opening the notebook:

``` bash
export WEATHER_DB=/path/to/weather.db
```

### Build the Virtual Environment

To build the virtual environment, run the following command:

```bash
./make_venv.sh
```

## Running a Report in Visual Studio Code

- Open the Jupyter notebook for the report of interest
- If using Visual Studio Code, select the Python virtual environment as the kernel for running the notebook
- Review the instructions at the top of the report and make any required changes to e.g. reporting parameters
- Click on "Run All" to run the report and export the results
- Exported results are written to a folder named "exported" within the reports folder
