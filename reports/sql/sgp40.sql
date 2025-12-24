SELECT      r.Timestamp, r.SRAW, r.VOCIndex, r.Label, r.Rating 
FROM        SGP40_READINGS r
WHERE       ($DAYS IS NULL) OR ($DAYS IS NOT NULL AND r.Timestamp >= DATETIME('now', '-$DAYS days'))
ORDER BY    r.Timestamp ASC;
