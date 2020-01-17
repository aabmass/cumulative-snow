from args import parse_args
import plot


def main() -> None:
    args = parse_args()
    plot.plot_cumulative_annual(args)


if __name__ == "__main__":
    main()
