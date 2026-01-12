import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import type { AsyncDuckDB, AsyncDuckDBConnection } from "@duckdb/duckdb-wasm";
import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { createDb } from "./duckdb";
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
      <Combobox items={dbState.stations.getChild("id")?.toJSON()}>
        <ComboboxInput
          id="small-form-framework"
          placeholder="Select a framework"
          required
        />
        <ComboboxContent>
          <ComboboxEmpty>No frameworks found.</ComboboxEmpty>
          <ComboboxList>
            {(item, idx) => {
              const { id, name } = dbState.stations.get(idx) ?? {};
              const value = `${name} (${id})`;
              return (
                <ComboboxItem key={item} value={item}>
                  {value}
                </ComboboxItem>
              );
            }}
          </ComboboxList>
        </ComboboxContent>
      </Combobox>
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
