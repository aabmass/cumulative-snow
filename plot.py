from args import Args
import load_data
import numpy as np
import matplotlib.pyplot as pl


def plot_cumulative_annual(args: Args) -> None:
    data = load_data.load_noaa_data(args.csv_path)
    data.plot()
    pl.show()
