#!/bin/bash

uv build -o public/ --wheel
uv run marimo export html-wasm notebook.py -o build/ --mode run
