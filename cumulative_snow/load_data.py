from typing import Union

import pandas as pd

from cumulative_snow.args import Args


def load_noaa_data(args: Args) -> pd.DataFrame:
    """Loads NOAA data from file path.

    Output dataframe has columns:
    - WINTER_YEAR = The year the winter started in
    - STATION = Station number?
    - NAME = Station name
    - SNOW = Snowfall (inches)
    - SNWD = Snow depth (inches)
    - WESD = Water equivalent of snow on the ground (inches)
    - WESF = Water equivalent of snowfall (inches)

    Additional dataset documentation: https://bit.ly/2Rs3Xyb
    """
    data = pd.read_csv(
        args.csv_path,
        converters={
            "SNOW": _fill_zeroes,
            "SNWD": _fill_zeroes,
            "WESD": _fill_zeroes,
            "WESF": _fill_zeroes,
        },
        parse_dates=["DATE"],
    )
    data.set_index("DATE", inplace=True)

    # Assigns year periods as being from July to the end of June e.g. winter of
    # 2010 is July 2009 through June 2019
    offset = pd.tseries.offsets.YearEnd(month=6)
    data["WINTER_YEAR"] = data.index - offset
    if args.station:
        data = data[data["STATION"] == args.station]

    return data


def _fill_zeroes(s: str) -> float:
    if s == "":
        return 0.0
    else:
        return float(s)
