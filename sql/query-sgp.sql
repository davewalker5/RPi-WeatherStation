-- Output formatting
.headers on
.mode box
.nullvalue NULL

-- Run a query
SELECT *
FROM SGP40_READINGS
ORDER BY id DESC
LIMIT 5;
