#!/usr/bin/env python

from cumulative_snow import load_data, plot
from cumulative_snow.args import parse_args


def main() -> None:
    args = parse_args()
    if args.list_stations:
        data = load_data.load_noaa_data(args)
        print(
            data[["STATION", "NAME", "SNOW"]]
            .groupby(["STATION", "NAME"])
            .count()
            .sort_values(by="SNOW", ascending=False)
            .rename({"SNOW": "Number of Datapoints"}, axis="columns")
        )
        return

    if not args.output_path:
        print("Use either --list_stations or set --output_path.")
        return

    plot.plot_cumulative_annual(args)
