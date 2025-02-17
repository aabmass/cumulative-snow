#!/bin/sh

uv run main.py datasets/boston_logan_snowfall.csv --start_year=2010 --output_path=boston_logan.svg
uv run main.py datasets/boston_logan_snowfall.csv --start_year=2010 --output_path=boston_logan.pdf
