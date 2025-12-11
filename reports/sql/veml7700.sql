SELECT      r.Timestamp, r.ALS, r.Illuminance, r.IsSaturated
FROM        VEML7700_READINGS r
ORDER BY    r.Timestamp ASC;
