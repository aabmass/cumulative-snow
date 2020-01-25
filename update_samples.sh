#!/bin/sh

pipenv run python main.py datasets/boston_logan_snowfall.csv --start_year=2010 --output_path=boston_logan.svg
pipenv run python main.py datasets/boston_logan_snowfall.csv --start_year=2010 --output_path=boston_logan.pdf
