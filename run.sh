#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p data out
python3 run.py
