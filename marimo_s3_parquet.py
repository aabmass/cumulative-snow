import marimo

__generated_with = "0.19.6"
app = marimo.App()


@app.cell
def _(mo, pl):
    @mo.persistent_cache
    def load_stations():
        return (
            # scan_csv doesn't work with WASM for some reason https://github.com/pola-rs/polars/issues/20877
            pl.read_csv(
                "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.csv",
                has_header=False,
                truncate_ragged_lines=True,
                quote_char=None,
                # See https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt for details
                schema={
                    "ID": pl.String,
                    "LATITUDE": pl.Float32,
                    "LONGITUDE": pl.Float32,
                    "ELEVATION": pl.Float32,
                    "STATE": pl.String,
                    "NAME": pl.String,
                    "GSN_FLAG": pl.String,
                    "HCN_CRN_FLAG": pl.String,
                    "WMO_ID": pl.Int64,
                },
            ).filter(
                pl.col("ID").str.starts_with("US"),
            )
        )


    stations_df = load_stations()
    stations_df
    return (stations_df,)


@app.cell
def _(data, mo):
    _stations = (
        data.groupby(["ID"])
        .agg(SNOW=("SNOW", "count"), DATE_min=("DATE", "min"), DATE_max=("DATE", "max"))
        .sort_values(by="SNOW", ascending=False)
        .rename({"SNOW": "Number of Datapoints"}, axis="columns")
    )
    stations_table = mo.ui.table(_stations)
    stations_table
    return


@app.cell
def _(data, mo, plot):
    _continous = mo.ui.plotly(plot.plot_continuous(data))
    _overlapping_all = (mo.ui.plotly(fig) for fig in plot.plot_overlapping(data))
    _monthly = mo.ui.plotly(plot.plot_monthly_averages(data))

    mo.md(f"""
    Plot of foo

    {_continous}
    {mo.vstack(_overlapping_all)}
    {_monthly}

    """)
    return


@app.cell
def _(mo, stations_df):
    station_dropdown = mo.ui.dropdown(
        {
            f"{state} - {name}": id
            for name, state, id in zip(
                stations_df["NAME"], stations_df["STATE"], stations_df["ID"]
            )
        },
        label="Choose a station",
    )
    station_dropdown
    return (station_dropdown,)


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
                read_parquet(
                    {paths},
                    hive_partitioning = true
                )
            WHERE
                ELEMENT IN ('TMAX', 'TAVG', 'TMIN', 'PRCP', 'SNOW', 'SNWD')
                AND YEAR(strptime(DATE, '%Y%m%d')) > 1970
        ) ON ELEMENT IN ('TMAX', 'TAVG', 'TMIN', 'PRCP', 'SNOW', 'SNWD') USING FIRST(converted_value)
        GROUP BY
            ID,
            DATE
        ORDER BY ID, DATE
        """
    )
    return (duckdb_df,)


@app.cell
def _(duckdb_df, load_data):
    data = load_data.load_noaa_data(duckdb_df.to_pandas())
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

    from cumulative_snow import load_data, plot
    from cumulative_snow.args import Args

    import os
    import urllib.request
    from urllib.parse import urlencode

    # Set plotly theme based on marimo theme
    pio.templates.default = "plotly_dark" if mo.app_meta().theme == "dark" else None
    return load_data, os, pl, plot, urlencode, urllib


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.function
def is_wasm():
    import sys

    return "pyodide" in sys.modules


@app.cell
def _(Error, download_parquet, mo, station_dropdown, urlencode, urllib):
    mo.stop(
        not station_dropdown.value,
        mo.md("**You must select a station from Station Dropdown above**"),
    )

    import xml.etree.ElementTree as ET
    import pandas as pd
    import pyarrow.dataset as ds


    def list_public_objects_with_prefix(bucket_name, prefix, region="us-east-1"):
        # S3 API uses 'prefix' query parameter to filter results
        params = {"list-type": "2", "prefix": prefix}
        query_string = urlencode(params)
        url = f"https://{bucket_name}.s3.amazonaws.com/?{query_string}"

        ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

        try:
            with urllib.request.urlopen(url) as response:
                r = response.read()
                root = ET.fromstring(r)

                # Extract keys from the XML response
                for content in root.findall("s3:Contents", ns):
                    yield content.find("s3:Key", ns).text

                if not root.findall("s3:Contents", ns):
                    raise Error(f"No objects found with prefix: {prefix}")

        except Exception as e:
            print(f"Error: {e}")


    paths = []
    for key in list_public_objects_with_prefix(
        "noaa-ghcn-pds",
        f"parquet/by_station/STATION={station_dropdown.value}",
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
