-- Output formatting
.headers on
.mode box
.nullvalue NULL

-- Run a query
SELECT *
FROM VEML7700_READINGS
ORDER BY id DESC
LIMIT 5;
