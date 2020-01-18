from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Text


@dataclass
class Args:
    csv_path: str
    output_path: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]


def _get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Graph NOAA/NCDC annual cumulative snowfall data and analyze"
    )
    parser.add_argument(
        "csv_path", help="Path to the CSV file containing daily snowfall recordings"
    )
    parser.add_argument("--output_path", help="Path to save the figure to, pdf")
    parser.add_argument(
        "--start_year", type=_parse_year, help="Year to start analysis for"
    )
    parser.add_argument("--end_year", type=_parse_year, help="Year to end analysis for")
    return parser


def _parse_year(s: str) -> datetime:
    return datetime.strptime(s, "%Y")


def parse_args(argv: Optional[Sequence[Text]] = None) -> Args:
    parser = _get_parser()
    ns = parser.parse_args(argv)
    return Args(**vars(ns))
