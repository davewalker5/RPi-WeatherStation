SELECT      r.Timestamp, r.Humidity
FROM        BME280_READINGS r
ORDER BY    r.Timestamp ASC;
