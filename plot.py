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
    fig, ax_top = pl.subplots(1, 1)

    for year, data_per_year in data.groupby("WINTER_YEAR"):
        data_per_year["SNOW"].cumsum().plot(ax=ax_top, label=year.year)

    fig.autofmt_xdate(rotation=70)
    ax_top.legend()
    ax_top.set_title("Cumulative Snow per Season (July-June)")
    ax_top.set_xlabel("Days")
    ax_top.set_ylabel("Snow (inches)")

    if args.output_path:
        fig.set_size_inches(11, 8.5)
        fig.savefig(args.output_path, format="pdf", bbox_inches="tight")
    else:
        pl.show()
