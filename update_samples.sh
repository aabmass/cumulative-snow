#!/bin/sh

uv run main.py datasets/boston_logan_snowfall.csv \
    --start_year=2005 \
    --save_svgs \
    --output_path=www/boston.html
