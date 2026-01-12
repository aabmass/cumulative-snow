import type { AsyncDuckDB, AsyncDuckDBConnection } from "@duckdb/duckdb-wasm";
import Plot from "react-plotly.js";
import { createDb } from "./duckdb";
import { useEffect, useState } from "react";
import { queryStationList, type Stations } from "./queries";

interface DbState {
  conn: AsyncDuckDBConnection;
  x: number[];
  y: number[];
  stations: Stations;
}

export default function Plots(): React.ReactNode {
  const [dbState, setDbState] = useState<DbState | null>(null);
  useEffect(() => {
    let db: AsyncDuckDB | undefined;
    let conn: AsyncDuckDBConnection | undefined;
    async function setup() {
      db = await createDb();
      conn = await db.connect();

      const stations = await queryStationList(conn);

      setDbState({
        conn: conn,
        x: [],
        y: [],
        stations,
      });
    }
    setup().catch(console.error);

    return () => {
      conn?.close().finally(db?.terminate);
    };
  }, []);

  return dbState ? (
    <div>
      <ul>
        {dbState.stations.map((station) => (
          <li key={station.id}>{station.name}</li>
        ))}
      </ul>
      <Plot
        data={[
          {
            x: dbState?.x,
            y: dbState?.y,
            type: "scatter",
            mode: "lines+markers",
            marker: { color: "red" },
          },
          { type: "bar", x: [1, 2, 3], y: [2, 5, 3] },
        ]}
        layout={{}}
      />
    </div>
  ) : (
    <p>Loading...</p>
  );
}
