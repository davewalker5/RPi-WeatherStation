SELECT      r.Timestamp, r.ALS, r.Illuminance, r.IsSaturated
FROM        VEML7700_READINGS r
WHERE       ($DAYS IS NULL) OR ($DAYS IS NOT NULL AND r.Timestamp >= DATETIME('now', '-$DAYS days'))
ORDER BY    r.Timestamp ASC;
