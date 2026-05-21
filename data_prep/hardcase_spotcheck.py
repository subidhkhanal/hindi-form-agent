"""Compact print of all 40 hard cases for human spot-check."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

path = Path(__file__).resolve().parents[1] / "data" / "hardcases_v1.jsonl"
entries = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

cat_counter: Counter[str] = Counter()
for e in entries:
    slot = e["metadata"]["slot"]
    cat = e["metadata"]["hard_case_category"]
    fields = sum(1 for v in e["output_json"].values() if v is not None)
    text = e["input_text"]
    text_short = text[:90] + ("..." if len(text) > 90 else "")
    cat_counter[cat] += 1
    print(f"{slot} [{cat:>24s}] {fields}f | {text_short}")

print()
print(f"Total: {len(entries)}")
print("Category counts:")
for cat, count in sorted(cat_counter.items()):
    print(f"  {cat:>24s}: {count}")
