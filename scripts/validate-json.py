#!/usr/bin/env python3
"""Validate all JSON files in the repo."""

import json
import sys
from pathlib import Path

FILES = [
    Path("hacs.json"),
    Path(".prettierrc.json"),
    *sorted(Path("custom_components").rglob("*.json")),
]
errors = 0

for json_file in FILES:
    content = json_file.read_text(encoding="utf-8")
    try:
        json.loads(content)
        print(f"OK  {json_file}")
    except json.JSONDecodeError as e:
        print(f"ERR {json_file}: {e}")
        errors += 1

sys.exit(errors)
