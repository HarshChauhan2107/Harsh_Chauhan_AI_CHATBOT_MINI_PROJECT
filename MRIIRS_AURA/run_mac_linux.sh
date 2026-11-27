#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PYTHON_BIN="$(command -v python3 || command -v python)"
if [ ! -x ".venv/bin/python" ]; then "$PYTHON_BIN" -m venv .venv; fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo "Open http://127.0.0.1:5000 in your browser"
.venv/bin/python app.py
