from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Text


@dataclass
class Args:
    csv_path: str
    output_path: Optional[str]
    save_svgs: bool
    start_year: Optional[datetime]
    end_year: Optional[datetime]
    station: Optional[str]
    list_stations: bool


def _get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Graph NOAA/NCDC annual cumulative snowfall data and analyze"
    )
    parser.add_argument(
        "csv_path", help="Path to the CSV file containing daily snowfall recordings"
    )
    parser.add_argument("--output_path", help="Path to save the HTML file.")
    parser.add_argument(
        "--save_svgs",
        action="store_true",
        help="Also save each figure as an SVG. Used for embedding in the README.md",
    )
    parser.add_argument(
        "--start_year", type=_parse_year, help="Year to start analysis for"
    )
    parser.add_argument("--end_year", type=_parse_year, help="Year to end analysis for")
    parser.add_argument(
        "--station", help="Filter to only include this station if the csv has multiples"
    )
    parser.add_argument(
        "--list_stations",
        action="store_true",
        help="List stations and numbers of datapoints for each station in the csv "
        "file and exit",
    )
    return parser


def _parse_year(s: str) -> datetime:
    return datetime.strptime(s, "%Y")


def parse_args(argv: Optional[Sequence[Text]] = None) -> Args:
    parser = _get_parser()
    ns = parser.parse_args(argv)
    return Args(**vars(ns))
