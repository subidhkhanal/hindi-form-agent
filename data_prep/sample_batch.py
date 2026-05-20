"""Print N random input_text values from any batch file for spot-check."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    lines = args.file.read_text(encoding="utf-8").splitlines()
    samples = rng.sample(lines, min(args.n, len(lines)))
    for i, line in enumerate(samples, 1):
        obj = json.loads(line)
        slot = obj["metadata"]["slot"]
        persona = obj["metadata"]["persona"]
        fields_filled = sum(1 for v in obj["output_json"].values() if v is not None)
        print(f"--- Sample {i} (slot {slot}, {fields_filled} fields) — {persona} ---")
        print(obj["input_text"])
        print()


if __name__ == "__main__":
    main()
