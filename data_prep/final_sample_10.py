"""Deterministic 10-sample random selection from the aggregated corpus."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

random.seed(42)
path = Path(__file__).resolve().parents[1] / "data" / "synthetic_dense_v1.jsonl"
lines = path.read_text(encoding="utf-8").splitlines()
samples = random.sample(lines, 10)
for i, line in enumerate(samples, 1):
    obj = json.loads(line)
    slot = obj["metadata"]["slot"]
    persona = obj["metadata"]["persona"]
    fields = sum(1 for v in obj["output_json"].values() if v is not None)
    print(f"--- {i} (slot {slot}, {fields} fields) — {persona} ---")
    print(obj["input_text"])
    print()
