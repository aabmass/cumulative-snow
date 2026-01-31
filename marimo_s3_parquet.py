import marimo

__generated_with = "0.19.7"
app = marimo.App(sql_output="native")


@app.cell
def _(mo):
    mo.md("""
    ### Select a station from the map or dropdown below
    """)
    return


@app.cell
def _(mo, pd, pl):
    @mo.persistent_cache
    def read_fwf_polars(url: str, **kwargs) -> pl.DataFrame:
        df = pd.read_fwf(url, header=0, **kwargs)
        return pl.from_pandas(df)


    _stations_df: pl.DataFrame = read_fwf_polars(
        "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt",
        colspecs=[
            (0, 11),  # ID
            (12, 20),  # LATITUDE
            (21, 30),  # LONGITUDE
            (31, 37),  # ELEVATION
            (38, 40),  # STATE
            (41, 71),  # NAME
            (72, 75),  # GSN FLAG
            (76, 79),  # HCN/CRN FLAG
            (80, 85),  # WMO ID
        ],
        names=[
            "ID",
            "LATITUDE",
            "LONGITUDE",
            "ELEVATION",
            "STATE",
            "NAME",
            "GSN_FLAG",
            "HCN_CRN_FLAG",
            "WMO_ID",
        ],
        usecols=["ID", "LATITUDE", "LONGITUDE", "ELEVATION", "STATE", "NAME"],
    )
    _inventory_df: pl.DataFrame = read_fwf_polars(
        "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt",
        colspecs=[
            (0, 11),  # ID
            (12, 20),  # LATITUDE
            (21, 30),  # LONGITUDE
            (31, 35),  # ELEMENT
            (36, 40),  # FIRSTYEAR
            (41, 45),  # LASTYEAR
        ],
        names=["ID", "LATITUDE", "LONGITUDE", "ELEMENT", "FIRSTYEAR", "LASTYEAR"],
        usecols=["ID", "ELEMENT", "FIRSTYEAR", "LASTYEAR"],
    )

    # Consider using lazy to optimize perf
    _stations_df = (
        _stations_df.join(
            _inventory_df.filter(pl.col("ELEMENT") == "SNOW").select(
                pl.col("ID"), pl.col("FIRSTYEAR"), pl.col("LASTYEAR")
            ),
            on=[pl.col("ID")],
        )
        .with_columns(NUM_YEARS=pl.col("LASTYEAR") - pl.col("FIRSTYEAR") + 1)
        # Reorder
        .select(
            "ID",
            "NAME",
            "STATE",
            "FIRSTYEAR",
            "LASTYEAR",
            "NUM_YEARS",
            "LATITUDE",
            "LONGITUDE",
            "ELEVATION",
        )
    )

    _initial_selection = (
        _stations_df.with_row_index().filter(pl.col("LASTYEAR") > 2015)["index"].to_list()
    )

    table = mo.ui.table(
        _stations_df,
        initial_selection=_initial_selection,
        format_mapping={"FIRSTYEAR": "{:d}", "LASTYEAR": "{:d}"},
    )
    mo.accordion({"Filter raw stations dataframe": table})
    return (table,)


@app.cell
def _(table):
    stations_df = table.value
    return (stations_df,)


@app.cell
def _(mo, px, stations_df):
    mo.stop(stations_df.is_empty())
    # Create the figure
    _fig = px.scatter_map(
        stations_df,
        lat="LATITUDE",
        lon="LONGITUDE",
        color="NUM_YEARS",
        size="NUM_YEARS",
        hover_name="NAME",
        hover_data={"NAME": True, "STATE": True, "ID": True, "NUM_YEARS": True},
        zoom=2,
        # height=800,
        # width=800,
    )
    _fig.update_traces(
        cluster=dict(
            enabled=True,
            maxzoom=5,  # Individual bubbles appear at zoom level 10+
            color="royalblue",
            # step=1,  # How many points trigger a cluster (1 is default)
        )
    )
    _fig.update_layout(clickmode="event+select", dragmode="pan")
    # del _fig

    # Wrap it in a marimo UI element
    map_selector = mo.ui.plotly(_fig, label="Choose a station by map (zoom and click)")

    # Display the map
    map_selector
    return (map_selector,)


@app.cell
def _(map_selector, mo, stations_df):
    def _key(name: str, state: str) -> str:
        return f"{state} - {name}"


    _values = {
        _key(name, state): id
        for name, state, id in zip(
            stations_df["NAME"], stations_df["STATE"], stations_df["ID"]
        )
    }

    # In case it was already selected in the map
    _value = None
    if map_selector.value:
        entry = map_selector.value[0]
        _value = _key(entry["NAME"], entry["STATE"])

    station_dropdown = mo.ui.dropdown(
        _values,
        label="Choose a station",
        value=_value,
    )
    station_dropdown
    return (station_dropdown,)


@app.cell
def _(station_dropdown):
    selected_station: str | None = station_dropdown.value
    return (selected_station,)


@app.cell
def _(data, mo, plot):
    _continous = mo.ui.plotly(plot.plot_continuous(data))
    _overlapping_all = (mo.ui.plotly(fig) for fig in plot.plot_overlapping(data))
    _monthly = mo.ui.plotly(plot.plot_monthly_averages(data))

    mo.vstack([_continous, *_overlapping_all, _monthly])
    return


@app.cell
def _(mo, paths):
    duckdb_df = mo.sql(
        f"""
        PIVOT (
            SELECT
                ID,
                strptime(DATE, '%Y%m%d')::DATE AS DATE,
                ELEMENT,
                CASE
                -- Temperature: Tenths of C to Fahrenheit
                    WHEN ELEMENT IN ('TMAX', 'TAVG', 'TMIN', 'TOBS') THEN ROUND((DATA_VALUE / 10.0) * 1.8 + 32, 2)
                    -- Precipitation: Tenths of mm to Inches
                    WHEN ELEMENT = 'PRCP' THEN ROUND(DATA_VALUE / 254.0, 2)
                    -- Snow: mm to Inches
                    WHEN ELEMENT IN ('SNOW', 'SNWD') THEN ROUND(DATA_VALUE / 25.4, 2)
                    ELSE DATA_VALUE
                END AS converted_value
            FROM
                read_parquet({paths}, hive_partitioning = true)
            WHERE
                ELEMENT IN ('TMAX', 'TAVG', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
                AND YEAR(strptime(DATE, '%Y%m%d')) > 1970
        ) ON ELEMENT IN ('TMAX', 'TAVG', 'TMIN', 'PRCP', 'SNOW', 'SNWD') USING FIRST(converted_value)
        GROUP BY
            ID,
            DATE
        ORDER BY
            ID,
            DATE
        """
    )
    return (duckdb_df,)


@app.cell
def _(duckdb_df, load_data):
    data = load_data.load_noaa_data(duckdb_df.df())
    return (data,)


@app.cell
async def _(mo):
    if is_wasm():
        import micropip

        await micropip.install(
            str(mo.notebook_location() / "public" / "cumulative_snow-0.1.0-py3-none-any.whl")
        )

    import plotly.express as px
    import plotly.io as pio

    import polars as pl
    import pandas as pd

    from cumulative_snow import load_data, plot
    from cumulative_snow.args import Args

    import os
    import urllib.request
    from urllib.parse import urlencode

    # Set plotly theme based on marimo theme
    pio.templates.default = "plotly_dark" if mo.app_meta().theme == "dark" else None
    return load_data, os, pd, pl, plot, px, urlencode, urllib


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.function
def is_wasm():
    import sys

    return "pyodide" in sys.modules


@app.cell
def hack_for_https_not_working(
    download_parquet,
    mo,
    selected_station: str | None,
    urlencode,
    urllib,
):
    # This whole cell is a hack to get around none of polars, pandas, duckdb's
    # https, fsspec, and botocore not working correctly in pyodide.
    #
    # TODO: link issues

    mo.stop(not selected_station)

    import xml.etree.ElementTree as ET
    import pyarrow.dataset as ds


    def list_public_objects_with_prefix(bucket_name, prefix, region="us-east-1"):
        # S3 API uses 'prefix' query parameter to filter results
        params = {"list-type": "2", "prefix": prefix}
        query_string = urlencode(params)
        url = f"https://{bucket_name}.s3.amazonaws.com/?{query_string}"

        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

        with urllib.request.urlopen(url) as response:
            r = response.read()
            root = ET.fromstring(r)

            # Extract keys from the XML response
            for content in root.findall("s3:Contents", ns):
                yield content.find("s3:Key", ns).text

            if not root.findall("s3:Contents", ns):
                raise RuntimeError(f"No objects found with prefix: {prefix}")


    paths = []
    for key in list_public_objects_with_prefix(
        "noaa-ghcn-pds",
        f"parquet/by_station/STATION={selected_station}",
    ):
        path = f"/tmp/{key}"
        url = f"https://noaa-ghcn-pds.s3.amazonaws.com/{key}"
        download_parquet(path, url)
        paths.append(path)
    return (paths,)


@app.cell
def _(mo, os, urllib):
    # This "caches" the computation really, the return value is not important
    @mo.persistent_cache
    def download_parquet(path: str, url: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        urllib.request.urlretrieve(url, path)
        return path
    return (download_parquet,)


if __name__ == "__main__":
    app.run()
