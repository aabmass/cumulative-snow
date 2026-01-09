import os
import duckdb
from concurrent.futures import ThreadPoolExecutor


# TUNING PARAMETERS
YEARS_TO_PROCESS = range(1850, 2026)
MAX_CONCURRENT_YEARS = 16  # Adjust this based on your RAM. Start low.


duckdb.execute(
    """
    SET preserve_insertion_order = false;
    SET memory_limit = '16GB'; 
    PRAGMA enable_object_cache = true;
    SET temp_directory = './duckdb_temp/';
    INSTALL cache_httpfs from community;
    -- Or upgrade to latest version with `FORCE INSTALL cache_httpfs from community;`
    LOAD cache_httpfs;
    """
)


def process_year(year):
    # Create a unique connection per thread to avoid locking
    conn = duckdb.connect()
    # Ensure S3 settings are inherited/set

    print(f"Starting Year: {year}")
    os.makedirs(f"us_wide_final/YEAR={year}", exist_ok=True)
    try:
        conn.execute(f"""
            COPY (
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

                FROM read_parquet('/mnt/windows/noaa_ghcn_local/YEAR={year}/ELEMENT=*/*.parquet', hive_partitioning=true)
                WHERE
                    ID LIKE 'US%' AND
                    -- ID = 'USW00014739' AND
                    ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
            )
            ON ELEMENT IN ('TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
            USING FIRST(converted_value)
            GROUP BY ID, obs_date, YEAR

                -- SELECT 
                --     {year} AS YEAR, ID, DATE,
                --     MAX(CASE WHEN ELEMENT = 'TMAX' THEN DATA_VALUE END) AS TMAX,
                --     MAX(CASE WHEN ELEMENT = 'SNOW' THEN DATA_VALUE END) AS SNOW
                -- -- FROM read_parquet('s3://noaa-ghcn-pds/parquet/by_year/YEAR={year}/ELEMENT=*/*.parquet')
                -- FROM read_parquet('/mnt/windows/noaa_ghcn_local/YEAR={year}/ELEMENT=*/*.parquet')
                -- WHERE ELEMENT IN ('TMAX', 'SNOW')
                -- GROUP BY ID, DATE
            ) TO 'us_wide_final/YEAR={year}/data.parquet' (FORMAT 'PARQUET');
        """)
        print(f"Finished Year: {year}")
    except Exception as e:
        print(f"Error in {year}: {e}")
    finally:
        conn.close()


# Execute with a controlled pool
with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_YEARS) as executor:
    executor.map(process_year, YEARS_TO_PROCESS)
