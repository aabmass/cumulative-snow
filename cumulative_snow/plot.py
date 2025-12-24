import textwrap

import matplotlib.dates as mdates
import matplotlib.pyplot as pl

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from cumulative_snow import label_lines, load_data
from cumulative_snow.args import Args

pd.options.plotting.backend = "plotly"


def _init_matplotlib_config() -> None:
    small_size = 10
    medium_size = 14
    bigger_size = 18
    pl.style.use("ggplot")
    pl.rc("font", size=small_size)
    pl.rc("axes", titlesize=small_size)
    pl.rc("axes", labelsize=small_size, titlesize=medium_size)
    pl.rc("xtick", labelsize=small_size)
    pl.rc("ytick", labelsize=small_size)
    pl.rc("legend", fontsize=8)
    pl.rc("figure", titlesize=bigger_size)


_init_matplotlib_config()


def plot_cumulative_annual(args: Args) -> None:
    data = load_data.load_noaa_data(args)

    bool_mask = pd.Series(True, data.index)
    if args.start_year:
        bool_mask &= data["WINTER_YEAR"] >= args.start_year.year
    if args.end_year:
        bool_mask &= data["WINTER_YEAR"] <= args.end_year.year
    data = data[bool_mask]

    # fig, (ax_top, ax_middle, ax_bottom) = pl.subplots(3, 1)
    # fig = make_subplots(rows=3, cols=1)

    continuous_fig = _plot_continuous(data)
    overlapping_fig = _plot_overlapping(data)
    monthly_averages_fig = _plot_monthly_averages(data)

    # fig.suptitle(
    #     textwrap.fill(
    #         "Cumulative Snow per Winter Season at {} ({})".format(
    #             data["NAME"][0], data["STATION"][0]
    #         ),
    #         width=50,
    #     )
    # )
    if args.output_path:
        with open(args.output_path, "w") as f:
            f.write("<html><head></head><body>")
            for i, fig in enumerate(
                [continuous_fig, overlapping_fig, monthly_averages_fig]
            ):
                # Include the JS engine only once to keep the file small
                include_js = "cdn" if i == 0 else False
                fig.write_html(
                    f,
                    default_height=600,
                    full_html=False,
                    include_plotlyjs=include_js,
                )

            f.write("</body></html>")

        # fig.savefig(args.output_path, bbox_inches="tight")
    else:
        pl.show()


def _plot_continuous(data: pd.DataFrame) -> go.Figure:
    # data = data.copy()
    # data["CUMULATIVE_SNOW"] = data.groupby("WINTER_YEAR")["SNOW"].cumsum()

    return px.line(
        data,
        x="DATE",
        y="CUMULATIVE_SNOW",
        color="WINTER_YEAR",
        title="Cumulative Snow per Winter Season",
        labels={"CUMULATIVE_SNOW": "Snowfall (inches)", "DATE": "Date"},
    )


def _plot_overlapping(data: pd.DataFrame) -> go.Figure:
    data = data.copy()

    # Normalize to the 1999-2000 winter year. Note 2000 includes the leap day.
    data["NORMALIZED_WINTER_DATE"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": (
                    data["DATE"].dt.year - data["WINTER_SEASON_START"].dt.year + 1999
                ),
                "month": data["DATE"].dt.month,
                "day": data["DATE"].dt.day,
            }
        )
    )

    return px.line(
        data,
        x="NORMALIZED_WINTER_DATE",
        y="CUMULATIVE_SNOW",
        color="WINTER_YEAR",
        title="Cumulative Snow per Winter Season (Overlapping Years)",
        labels={
            "CUMULATIVE_SNOW": "Snowfall (inches)",
            "NORMALIZED_WINTER_DATE": "Date in Winter Season",
        },
    ).update_xaxes(tickformat="%b %d")


def _plot_monthly_averages(data: pd.DataFrame) -> go.Figure:
    month_order = [
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
    ]

    # 1. Sum daily data into specific month-year buckets
    # (e.g., Total snow in Jan 2020, Total snow in Jan 2021...)
    monthly_summaries = (
        data.groupby(
            [
                data["DATE"].dt.year.rename("YEAR"),
                data["DATE"].dt.strftime("%b").rename("MONTH"),
            ]
        )
        .agg({"TAVG": "mean", "TMAX": "mean", "TMIN": "mean", "SNOW": "sum"})
        # move grouped index into regular columns
        .reset_index()
    )

    final_data = monthly_summaries.groupby("MONTH").mean(numeric_only=True)
    final_data = final_data.reindex(month_order)

    fig = px.bar(
        final_data,
        x=final_data.index,
        y=["SNOW", "TMAX", "TAVG", "TMIN"],
        title="Monthly Averages",
        barmode="group",
        template="ggplot2",
        labels={
            "SNOW": "Snowfall (inches)",
            "TAVG": "Avg Temp",
            "TMAX": "Max Temp",
            "TMIN": "Min Temp",
        },
    )

    # Hacks to get dual axis with separate units
    fig.update_layout(
        yaxis2=dict(title="Degrees (°F)", side="right", overlaying="y", showgrid=False),
        yaxis_title="Snowfall (Inches)",
    )
    fig.update_traces(yaxis="y2", selector=lambda t: t.name in ["TAVG", "TMAX", "TMIN"])
    fig.update_traces(yaxis="y1", selector=lambda t: t.name == "SNOW")

    return fig
