import marimo

__generated_with = "0.19.5"
app = marimo.App(width="medium")


@app.cell
def _(data, mo):
    _stations = (
        data.groupby(["STATION", "NAME"])
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
def _(Args, mo):
    args = Args(csv_path=mo.notebook_dir() / "datasets" / "boston_logan_snowfall.csv")
    return (args,)


@app.cell
def _(args, load_data):
    data = load_data.load_noaa_data(args)
    return (data,)


@app.cell
async def _(is_wasm, mo):
    if is_wasm():
        import micropip

        await micropip.install(
            str(mo.notebook_location() / "public" / "cumulative_snow-0.1.0-py3-none-any.whl")
        )

    import plotly.express as px
    import plotly.io as pio

    from cumulative_snow import load_data, plot
    from cumulative_snow.args import Args

    # Set plotly theme based on marimo theme
    pio.templates.default = "plotly_dark" if mo.app_meta().theme == "dark" else None
    return Args, load_data, plot


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _():
    def is_wasm():
        import sys

        return "pyodide" in sys.modules


    is_wasm()
    return (is_wasm,)


if __name__ == "__main__":
    app.run()
