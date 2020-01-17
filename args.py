from argparse import ArgumentParser
from dataclasses import dataclass
from typing import Optional, Sequence, Text


@dataclass
class Args:
    csv_path: str


def _get_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Graph NOAA/NCDC annual cumulative snowfall data and analyze"
    )
    parser.add_argument(
        "csv_path", help="Path to the CSV file containing daily snowfall recordings"
    )
    return parser


def parse_args(argv: Optional[Sequence[Text]] = None) -> Args:
    parser = _get_parser()
    ns = parser.parse_args(argv)
    return Args(**vars(ns))
