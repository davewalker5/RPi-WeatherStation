SELECT      Timestamp, Object_Type, Object_Name, Bytes
FROM        DB_SIZE_SNAPSHOTS
ORDER BY    Timestamp ASC, Object_Name ASC;
