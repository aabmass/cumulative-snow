import * as arrow from "apache-arrow";
import * as duckdb from "@duckdb/duckdb-wasm";

export type Stations = arrow.Table<{ id: arrow.Utf8; name: arrow.Utf8 }>;

export async function queryStationList(
  conn: duckdb.AsyncDuckDBConnection
): Promise<Stations> {
  return await conn.query<{ id: arrow.Utf8; name: arrow.Utf8 }>(
    `
    SELECT ID as id, NAME as name FROM read_csv(
      'https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.csv',
      header=False,
      columns={
        'ID': 'VARCHAR',
        'LATITUDE': 'FLOAT',
        'LONGITUDE': 'FLOAT',
        'ELEVATION': 'FLOAT',
        'STATE': 'VARCHAR',
        'NAME': 'VARCHAR',
        'GSN_FLAG': 'VARCHAR',
        'HCN_CRN_FLAG': 'VARCHAR',
        'WMO_ID': 'BIGINT'
      },
      quote='',
      ignore_errors=True
    )
    WHERE NAME like 'US%'
    -- LIMIT 1000;
    `
  );
}
