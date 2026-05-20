"""Concatenate Day 3 batch01 + all Day 4 batches into the v1 synthetic file."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    batches_dir = data_dir / "batches"

    inputs: list[Path] = [data_dir / "synthetic_dense_v1_batch01.jsonl"]
    inputs += sorted(batches_dir.glob("synthetic_dense_v1_batch*.jsonl"))

    out_path = data_dir / "synthetic_dense_v1.jsonl"

    total = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for in_path in inputs:
            if not in_path.exists():
                print(f"WARNING: Missing batch file: {in_path}")
                continue
            with open(in_path, "r", encoding="utf-8") as f:
                count = 0
                for line in f:
                    line = line.strip()
                    if line:
                        out.write(line + "\n")
                        count += 1
                        total += 1
                print(f"  Added {count} from {in_path.name}")

    print(f"\nAggregated {total} entries to {out_path}")


if __name__ == "__main__":
    main()
