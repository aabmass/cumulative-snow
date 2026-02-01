#!/bin/bash

uv build -o public/ --wheel
uv run marimo export html-wasm marimo_s3_parquet.py -o build/ --mode run --force
