#!/usr/bin/env bash
set -euo pipefail

PYBIN="${PYBIN:-python3}"
$PYBIN -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p assets/fonts assets logs .streamlit
cp -n .env.example .env 2>/dev/null || true

echo "Run:"
echo "source .venv/bin/activate && streamlit run app.py"
