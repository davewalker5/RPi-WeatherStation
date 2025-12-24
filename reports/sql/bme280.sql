SELECT      r.Timestamp, r.Temperature, r.Pressure, r.Humidity
FROM        BME280_READINGS r
WHERE       ($DAYS IS NULL) OR ($DAYS IS NOT NULL AND r.Timestamp >= DATETIME('now', '-$DAYS days'))
ORDER BY    r.Timestamp ASC;
