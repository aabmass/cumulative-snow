from args import Args
import load_data
import numpy as np
import matplotlib.pyplot as pl
import pandas as pd


def _init_matplotlib_config() -> None:
    small_size = 10
    medium_size = 16
    bigger_size = 24
    pl.style.use("ggplot")
    pl.rc("font", size=small_size)
    pl.rc("axes", titlesize=small_size)
    pl.rc("axes", labelsize=bigger_size, titlesize=bigger_size)
    pl.rc("xtick", labelsize=small_size)
    pl.rc("ytick", labelsize=small_size)
    pl.rc("legend", fontsize=8)
    pl.rc("figure", titlesize=bigger_size)


_init_matplotlib_config()


def plot_cumulative_annual(args: Args) -> None:
    data = load_data.load_noaa_data(args.csv_path)

    bool_mask = pd.Series(True, data.index)
    if args.start_year:
        bool_mask &= data["WINTER_YEAR"] >= args.start_year
    if args.end_year:
        bool_mask &= data["WINTER_YEAR"] <= args.end_year
    data = data[bool_mask]

    print(data)
    print(data.describe())

    # Add more subplots here
    fig, (ax_top, ax_bottom) = pl.subplots(2, 1)

    cumulative_snow = data[["WINTER_YEAR", "SNOW"]].groupby(["WINTER_YEAR"]).cumsum()
    cumulative_snow["WINTER_YEAR"] = data["WINTER_YEAR"]
    cumulative_snow_per_year = cumulative_snow.groupby(data["WINTER_YEAR"].dt.year)[
        "SNOW"
    ]
    cumulative_snow_per_year.plot(ax=ax_top)
    _plot_overlapping(ax_bottom, cumulative_snow)

    fig.autofmt_xdate(rotation=70)
    ax_top.legend()
    ax_top.set_title("Cumulative Snow per Winter Season (July-June)")
    ax_top.set_xlabel("Days")
    ax_top.set_ylabel("Snow (inches)")

    if args.output_path:
        fig.set_size_inches(11, 8.5)
        fig.savefig(args.output_path, bbox_inches="tight")
    else:
        pl.show()


def _plot_overlapping(ax: pl.Axes, cumulative_data: pd.DataFrame) -> None:
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

    # Update index with formatted Mon-Day
    data_overlapping.set_index(data_overlapping.index.strftime("%b %-d"), inplace=True)
    data_overlapping.plot(ax=ax)

