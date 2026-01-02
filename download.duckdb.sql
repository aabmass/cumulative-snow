-- SAFETY SETTINGS
SET preserve_insertion_order = false;
SET memory_limit = '15GB'; 
SET partitioned_write_max_open_files = 1;

INSTALL cache_httpfs from community;
LOAD cache_httpfs;

CREATE OR REPLACE TEMP VIEW pivot_by_year AS (
    PIVOT (
        SELECT 
            ID, 
            strptime(DATE, '%Y%m%d')::DATE AS obs_date,
            YEAR,
            ELEMENT,
            CASE 
                -- Temperature: Tenths of C to Fahrenheit
                WHEN ELEMENT IN ('TMAX', 'TMIN', 'TOBS') 
                    THEN ROUND((DATA_VALUE / 10.0) * 1.8 + 32, 2)
                -- Precipitation: Tenths of mm to Inches
                WHEN ELEMENT = 'PRCP' 
                    THEN ROUND(DATA_VALUE / 254.0, 2)
                -- Snow: mm to Inches
                WHEN ELEMENT IN ('SNOW', 'SNWD') 
                    THEN ROUND(DATA_VALUE / 25.4, 2)
                ELSE DATA_VALUE 
            END AS converted_value
        FROM read_parquet(
            's3://noaa-ghcn-pds/parquet/by_year/YEAR=*/ELEMENT=*/*.parquet',
            hive_partitioning=true
        )
        WHERE
            ID LIKE 'US%' AND
            -- ID = 'USW00014739' AND
            ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
    )
    ON ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
    USING FIRST(converted_value)
    GROUP BY ID, obs_date, YEAR
);

COPY (
SELECT * FROM pivot_by_year WHERE YEAR = 2000 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2001 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2002 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2003 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2004 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2005 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2006 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2007 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2008 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2009 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2010 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2011 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2012 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2013 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2014 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2015 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2016 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2017 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2018 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2019 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2020 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2021 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2022 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2023 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2024 UNION ALL
SELECT * FROM pivot_by_year WHERE YEAR = 2025
)
TO 'daily-summaries-parquet' (FORMAT parquet, APPEND, PARTITION_BY (YEAR), COMPRESSION zstd);


EXPLAIN ANALYZE COPY (
    PIVOT (
        SELECT 
            ID, 
            strptime(DATE, '%Y%m%d')::DATE AS obs_date,
            ELEMENT,
            CASE 
                -- Temperature: Tenths of C to Fahrenheit
                WHEN ELEMENT IN ('TMAX', 'TMIN', 'TOBS') 
                    THEN ROUND((DATA_VALUE / 10.0) * 1.8 + 32, 2)
                -- Precipitation: Tenths of mm to Inches
                WHEN ELEMENT = 'PRCP' 
                    THEN ROUND(DATA_VALUE / 254.0, 2)
                -- Snow: mm to Inches
                WHEN ELEMENT IN ('SNOW', 'SNWD') 
                    THEN ROUND(DATA_VALUE / 25.4, 2)
                ELSE DATA_VALUE 
            END AS converted_value
        FROM read_parquet(
            's3://noaa-ghcn-pds/parquet/by_year/YEAR=*/ELEMENT=*/*.parquet',
            hive_partitioning=true
        )
        WHERE
            YEAR = 2020 AND
            ID LIKE 'US%' AND
            -- ID = 'USW00014739' AND
            ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
    )
    ON ELEMENT
    USING FIRST(converted_value)
    GROUP BY ID, obs_date
    ORDER BY ID, obs_date DESC
)
TO 'daily-summaries-pivot.zstd.parquet' (FORMAT parquet, COMPRESSION zstd);
