"""Subsample HiNER to ~2,000 entries stratified by fields_filled.

The Day-6 brief targeted strata 600/800/600 across fields_filled values 2/3/4.
The actual HiNER post-filter distribution is {2: 6398, 3: 24, 4: 0} — only two
strata exist in meaningful volume. We honour the brief's intent (~2,000 total
for distributional backbone) by:
  - taking ALL entries from non-dominant strata (3-field, 4-field)
  - topping up from the 2-field stratum to reach TARGET_TOTAL

Deterministic seed=42 for reproducibility.
Output: data/from_ner_v1_subsampled.jsonl (~2,000 entries).
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

TARGET_TOTAL = 2000


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    input_path = project_root / "data" / "from_ner_v1.jsonl"
    output_path = project_root / "data" / "from_ner_v1_subsampled.jsonl"

    by_fields_filled: dict[int, list[dict]] = defaultdict(list)

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            ff = entry.get("metadata", {}).get("fields_filled")
            if ff is None:
                output = entry.get("output_json", {})
                ff = sum(1 for v in output.values() if v is not None)
            by_fields_filled[ff].append(entry)

    print("Loaded HiNER strata:")
    for k, v in sorted(by_fields_filled.items()):
        print(f"  fields_filled={k}: {len(v)} entries")

    rng = random.Random(42)
    selected: list[dict] = []

    # Take ALL entries from non-dominant strata (3+, 4+) first.
    dominant_stratum = max(by_fields_filled, key=lambda k: len(by_fields_filled[k]))
    for ff in sorted(by_fields_filled):
        if ff == dominant_stratum:
            continue
        items = by_fields_filled[ff]
        selected.extend(items)
        print(f"  Selected all {len(items)} from stratum {ff} (preserving diversity)")

    # Top up from dominant stratum.
    remaining = TARGET_TOTAL - len(selected)
    dominant_pool = by_fields_filled[dominant_stratum]
    if remaining > 0:
        if remaining >= len(dominant_pool):
            picked = dominant_pool
        else:
            picked = rng.sample(dominant_pool, remaining)
        selected.extend(picked)
        print(f"  Selected {len(picked)} from stratum {dominant_stratum} "
              f"(top-up to reach {TARGET_TOTAL})")

    rng.shuffle(selected)

    with open(output_path, "w", encoding="utf-8") as f:
        for entry in selected:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(selected)} entries to {output_path}")


if __name__ == "__main__":
    main()
