#!/bin/bash
# 도면·STL·DXF 다시 만들기:  pip install -r requirements.txt && ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py
