-- SAFETY SETTINGS
SET preserve_insertion_order = false;
SET memory_limit = '22GB'; 
PRAGMA enable_object_cache = true;
SET temp_directory = './duckdb_temp/';
INSTALL cache_httpfs from community;
-- Or upgrade to latest version with `FORCE INSTALL cache_httpfs from community;`
LOAD cache_httpfs;

COPY (
    SELECT 
        STATION, -- Hive partition key from the folder name
        DATE,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'TMAX') AS TMAX,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'TMIN') AS TMIN,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'PRCP') AS PRCP,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'SNOW') AS SNOW
    FROM read_parquet(
        's3://noaa-ghcn-pds/parquet/by_station/STATION=US*/*/*.parquet',
        hive_partitioning=true,
        hive_types={'STATION': VARCHAR, 'ELEMENT': VARCHAR}
    )
    -- We filter for US stations directly in the S3 glob above (STATION=US*)
    WHERE ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW')
    GROUP BY STATION, DATE
) TO 'us_wide_final.parquet' (FORMAT 'PARQUET', COMPRESSION 'ZSTD');


EXPLAIN ANALYZE SELECT 
        STATION, -- Hive partition key from the folder name
        DATE,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'TMAX') AS TMAX,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'TMIN') AS TMIN,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'PRCP') AS PRCP,
        MAX(DATA_VALUE) FILTER (WHERE ELEMENT = 'SNOW') AS SNOW
    FROM read_parquet(
        's3://noaa-ghcn-pds/parquet/by_station/STATION=US*/*/*.parquet',
        hive_partitioning=true,
        hive_types={'STATION': VARCHAR, 'ELEMENT': VARCHAR}
    )
    -- We filter for US stations directly in the S3 glob above (STATION=US*)
    WHERE ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW')
    GROUP BY STATION, DATE;
