from typing import Any, Callable

import matplotlib.pyplot as pl
import numpy as np
import pandas as pd


def label_all(
    ax: pl.Axes,
    fontsize: int = None,
    xoffset: float = -0.01,
    yoffset: float = 0.03,
    x_to_float: Callable[[Any], float] = None,
    **kwargs: Any,
) -> None:
    """Label all lines in the axes

    - xoffset and yoffset are fractional (axes coordinate) offset to apply to
      the text added.
    """

    data_to_axes = ax.transData + ax.transAxes.inverted()
    x_to_float = x_to_float or _x_to_float

    for line in ax.get_lines():
        xdata, ydata = line.get_data(orig=True)

        # x, y in data coordinates
        nonnan_mask = ~np.isnan(ydata)
        x = x_to_float(xdata[nonnan_mask][-1])
        y = ydata[nonnan_mask][-1]

        # x, y in axes coordinates
        x, y = data_to_axes.transform((x_to_float(x), y))
        ax.text(
            x + xoffset,
            y + yoffset,
            line.get_label(),
            transform=ax.transAxes,
            fontsize=fontsize,
            **kwargs,
        )


def _x_to_float(x: Any) -> float:
    if hasattr(x, "__float__"):
        return float(x)
    elif isinstance(x, pd.Period):
        return x.ordinal
    raise Exception(f"Can't convert {type(x)} to float")
