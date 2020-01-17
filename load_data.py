import pandas as pd
from typing import Union


def load_noaa_data(file_path: str) -> pd.DataFrame:
    """Loads NOAA data from file path.

    Output dataframe has columns:
    - DATE = Date of measurement(index as well)
    - STATION = Station number?
    - NAME = Station name
    - SNOW = Snowfall (inches)
    - SNWD = Snow depth (inches)
    - WESD = Water equivalent of snow on the ground (inches)
    - WESF = Water equivalent of snowfall (inches)

    Additional dataset documentation: https://bit.ly/2Rs3Xyb
    """
    res = pd.read_csv(
        file_path,
        converters={
            "SNOW": _fill_zeroes,
            "SNWD": _fill_zeroes,
            "WESD": _fill_zeroes,
            "WESF": _fill_zeroes,
        },
    )
    res.set_index("DATE", inplace=True)
    return res


def _fill_zeroes(s: str) -> float:
    if s == "":
        return 0.0
    else:
        return float(s)
