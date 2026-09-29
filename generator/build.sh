#!/bin/bash
# 템플릿 다시 만들기: npm install && pip install lxml && ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p out
node build.js out
python3 postprocess.py out/stage1.pptx out/layout_spec.json ../ppt-template.pptx
