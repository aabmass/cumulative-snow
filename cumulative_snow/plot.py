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
    # _plot_overlapping(ax_middle, data)
    # _plot_monthly_averages(ax_bottom, data)

    # fig.suptitle(
    #     textwrap.fill(
    #         "Cumulative Snow per Winter Season at {} ({})".format(
    #             data["NAME"][0], data["STATION"][0]
    #         ),
    #         width=50,
    #     )
    # )
    if args.output_path:
        continuous_fig.write_html(args.output_path, include_plotlyjs="cdn")
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


def _plot_overlapping(ax: pl.Axes, data: pd.DataFrame) -> None:
    cumulative_data = data[["WINTER_YEAR", "SNOW"]].groupby(["WINTER_YEAR"]).cumsum()
    cumulative_data["WINTER_YEAR"] = data["WINTER_YEAR"]

    # Create a new index adjusted to be all in the same year (ignore the
    # specific year) by normalizing to timedelta since start of winter year
    # then adding it to an arbitrary year.
    deltas = cumulative_data.index - cumulative_data["WINTER_YEAR"]
    index_same_year = (
        pd.Timestamp(year=2000, day=1, month=7) + deltas - pd.Timedelta(days=1)
    )

    # Update winter year to be just the year int, for column labels after pivot
    data_overlapping = cumulative_data.assign(
        WINTER_YEAR=cumulative_data["WINTER_YEAR"].dt.year
    )
    data_overlapping.set_index(index_same_year, inplace=True)

    # Pivot WINTER_YEAR to be the new columns
    data_overlapping = data_overlapping.pivot(columns="WINTER_YEAR", values="SNOW")

    # Plot
    data_overlapping.plot(ax=ax, legend=False)

    label_lines.label_all(ax, xoffset=0.0, yoffset=-0.02, fontsize=6)
    ax.set_xlabel("Month")
    ax.set_ylabel("Snowfall (inches)")
    # Put a major tick per month
    locator = mdates.MonthLocator()
    fmt = mdates.DateFormatter("%b")
    ax.get_xaxis().set_major_locator(locator)
    ax.get_xaxis().set_major_formatter(fmt)
    ax.get_xaxis().set_visible(True)


def _plot_monthly_averages(ax: pl.Axes, data: pd.DataFrame) -> None:
    # Calculate cumulative snow totals per month in each year
    data["Cumulative Snow"] = (
        data["SNOW"].groupby([data.index.year, data.index.month]).cumsum()
    )

    # Average these things by month over all years
    avg_per_month = data.groupby([data.index.month]).mean(numeric_only=True)[
        ["Cumulative Snow", "TAVG", "TMAX", "TMIN"]
    ]

    # This is to cycle the whole DF so July is at the start
    dummy_sort_key = "dummy"
    avg_per_month[dummy_sort_key] = np.roll(avg_per_month.index, 6)
    avg_per_month.sort_values(dummy_sort_key, inplace=True)
    avg_per_month.drop(dummy_sort_key, axis=1, inplace=True)

    # Replace index month numbers with month names
    avg_per_month.set_index(
        pd.to_datetime(avg_per_month.index, format="%m").strftime("%b"),
        inplace=True,
    )

    # Plot
    avg_per_month.plot.bar(
        ax=ax,
        secondary_y=[col for col in avg_per_month.columns if col != "Cumulative Snow"],
    )

    ax.grid(True)
    ax.right_ax.grid(False)
    ax.set_xlabel("Month")
    ax.set_ylabel("Snowfall (Inches)")
    ax.right_ax.set_ylabel("Temperature (F)")
