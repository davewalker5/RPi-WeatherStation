SELECT      r.Timestamp, r.SRAW, r.VOCIndex, r.Label, r.Rating 
FROM        SGP40_READINGS r
ORDER BY    r.Timestamp ASC;
