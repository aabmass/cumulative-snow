from args import parse_args
import plot
import load_data


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
    else:
        plot.plot_cumulative_annual(args)


if __name__ == "__main__":
    main()
