SELECT      r.Timestamp, r.Temperature, r.Pressure, r.Humidity
FROM        BME280_READINGS r
ORDER BY    r.Timestamp ASC;
