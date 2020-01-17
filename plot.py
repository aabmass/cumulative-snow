from args import Args
import load_data
import numpy as np
import matplotlib.pyplot as pl
import pandas as pd


def _init_matplotlib_config() -> None:
    small_size = 10
    bigger_size = 24
    pl.style.use("ggplot")
    pl.rc("font", size=small_size)
    pl.rc("axes", titlesize=small_size)
    pl.rc("axes", labelsize=bigger_size)
    pl.rc("xtick", labelsize=small_size)
    pl.rc("ytick", labelsize=small_size)
    pl.rc("legend", fontsize=small_size)
    pl.rc("figure", titlesize=bigger_size)


_init_matplotlib_config()


def plot_cumulative_annual(args: Args) -> None:
    data = load_data.load_noaa_data(args.csv_path)
    print(data)
    print(data.describe())

    # Add more subplots here
    fig, ax_top = pl.subplots(1, 1)

    # Groups by year anchored at the end of June, e.g. winter of 2010 is July
    # 2009 through June 2019
    grouper = pd.Grouper(freq="A-JUN", label="left")
    data_grouped_by_year = data.groupby(grouper)
    for year, data_per_year in data_grouped_by_year:
        data_per_year["SNOW"].cumsum().plot(ax=ax_top, label=year.year)

    ax_top.set_xlabel("Days")
    ax_top.set_ylabel("Snow (inches)")
    ax_top.legend()
    pl.show()
