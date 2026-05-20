"""Print 5 randomly-sampled input_text values from the synthetic batch for review."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

random.seed(7)
path = Path(__file__).resolve().parents[1] / "data" / "synthetic_dense_v1_batch01.jsonl"
lines = path.read_text(encoding="utf-8").splitlines()
samples = random.sample(lines, 5)
for i, line in enumerate(samples, 1):
    obj = json.loads(line)
    slot = obj["metadata"]["slot"]
    persona = obj["metadata"]["persona"]
    print(f"--- Sample {i} (slot {slot} — {persona}) ---")
    print(obj["input_text"])
    print()
