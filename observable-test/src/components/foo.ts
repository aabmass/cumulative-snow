/**
 * TODO: sort out the mess with pyodide lock files
 */
// import * as lock from "./pyodide-lock.json";

// Need to pin to match lock file version from marimo 0.27.0
// @ts-ignore
import * as pyodideUntyped from "npm:pyodide@0.27.0";
const pyodide = pyodideUntyped as typeof import("pyodide");

// Can't use recommended npm:... imports because of https://github.com/plotly/plotly.js/issues/7322
// @ts-ignore
import "https://cdn.plot.ly/plotly-3.3.1.min.js";
declare const Plotly: typeof import("plotly.js");

// @ts-ignore
import { FileAttachment } from "observablehq:stdlib";

// Built from https://wasm.marimo.app/pyodide-lock.json
const lockFileURL = FileAttachment("./pyodide-lock.json").href;
console.log(lockFileURL);

const p = await pyodide.loadPyodide({
  lockFileURL,
  // https://pyodide.org/en/stable/usage/working-with-bundlers.html#using-pyodide-from-a-cdn
  indexURL: `https://cdn.jsdelivr.net/pyodide/v${pyodide.version}/full/`,
  packages: ["micropip", "plotly", "polars"],
});

export async function renderHtml(
  numPoints: number,
  element: HTMLElement | string,
) {
  const res = await p.runPythonAsync(
    `
import plotly.express as px
import polars as pl
import plotly.io as pio

pio.templates.default = "plotly_dark"

numPoints: int

print(f"Plotting {numPoints=}")
fig = px.scatter(pl.DataFrame({"a": [i for i in range(numPoints)], "b": [i * 2 for i in range(numPoints)]}), x="a", y="b")
fig.to_json()
`,
    {
      locals: p.toPy({ numPoints }),
    },
  );

  if (typeof res !== "string") {
    throw new Error(`Expected string result, got ${typeof res}`);
  }

  const json = JSON.parse(res);
  return await Plotly.newPlot(element, json);
}

/**
// export const stations = "hello";
export const stations = (
  await aq.loadCSV(
    "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.csv",
    {
      header: false,
      names: [
        "ID",
        "LATITUDE",
        "LONGITUDE",
        "ELEVATION",
        "STATE",
        "NAME",
        "GSN FLAG",
        "HCN_CRN_FLAG",
        "WMO_ID",
      ],
    },
  )
).filter((d) => aq.op.startswith(d.ID, "US"));

// Load from parquet https://noaa-ghcn-pds.s3.amazonaws.com/index.html#parquet/by_station/STATION=USW00014739/ELEMENT=SNOW/
const station = "USW00014739";
export const boston = await aq.loadArrow(
  `https://noaa-ghcn-pds.s3.amazonaws.com/parquet/by_station/STATION=${station}/ELEMENT=SNOW/c54109349b4d4f3eb2fbe6a2ba607a00_0.snappy.parquet`,
);
 */
