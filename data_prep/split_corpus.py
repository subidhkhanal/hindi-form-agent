"""Build train/val/test splits per the Day 6 design.

Splits:
- Hand-crafted seed: all 10 to train
- HiNER subsampled: 80/10/10
- Synthetic dense: 80/10/10
- Hard cases: 20/10/10 split, balanced across 10 categories (2/1/1 per cat)

Deterministic seed=42 for reproducibility.
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


def load_jsonl(path: Path) -> list[dict]:
    entries: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def write_jsonl(entries: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def split_standard(rng: random.Random, entries: list[dict], train_frac: float = 0.8,
                   val_frac: float = 0.1) -> tuple[list[dict], list[dict], list[dict]]:
    shuffled = entries.copy()
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_train = int(n * train_frac)
    n_val = int(n * val_frac)
    return (shuffled[:n_train],
            shuffled[n_train:n_train + n_val],
            shuffled[n_train + n_val:])


def split_hardcases(rng: random.Random, entries: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Balanced split: per-category 2/1/1 across train/val/test."""
    by_category: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        cat = e.get("metadata", {}).get("hard_case_category", "unknown")
        by_category[cat].append(e)

    train, val, test = [], [], []
    for cat, items in sorted(by_category.items()):
        if len(items) != 4:
            print(f"WARNING: category {cat} has {len(items)} entries, expected 4")
        shuffled = items.copy()
        rng.shuffle(shuffled)
        train.extend(shuffled[:2])
        val.extend(shuffled[2:3])
        test.extend(shuffled[3:4])

    return train, val, test


def tag_source(entries: list[dict], source: str) -> list[dict]:
    """Set canonical source bucket. Preserve any prior source as original_source."""
    for e in entries:
        meta = e.setdefault("metadata", {})
        prior = meta.get("source")
        if prior and prior != source:
            meta["original_source"] = prior
        meta["source"] = source
    return entries


def main() -> None:
    rng = random.Random(42)

    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    seed = load_jsonl(data_dir / "handcrafted_seed.jsonl")
    hiner = load_jsonl(data_dir / "from_ner_v1_subsampled.jsonl")
    synthetic = load_jsonl(data_dir / "synthetic_dense_v1.jsonl")
    hardcases = load_jsonl(data_dir / "hardcases_v1.jsonl")

    print(f"Loaded: seed={len(seed)}, hiner={len(hiner)}, "
          f"synthetic={len(synthetic)}, hardcases={len(hardcases)}")

    seed_train, seed_val, seed_test = seed, [], []
    hiner_train, hiner_val, hiner_test = split_standard(rng, hiner)
    synth_train, synth_val, synth_test = split_standard(rng, synthetic)
    hard_train, hard_val, hard_test = split_hardcases(rng, hardcases)

    seed_train = tag_source(seed_train, "handcrafted_seed")
    hiner_train = tag_source(hiner_train, "hiner")
    hiner_val = tag_source(hiner_val, "hiner")
    hiner_test = tag_source(hiner_test, "hiner")
    synth_train = tag_source(synth_train, "synthetic_dense")
    synth_val = tag_source(synth_val, "synthetic_dense")
    synth_test = tag_source(synth_test, "synthetic_dense")
    hard_train = tag_source(hard_train, "hardcases")
    hard_val = tag_source(hard_val, "hardcases")
    hard_test = tag_source(hard_test, "hardcases")

    train = seed_train + hiner_train + synth_train + hard_train
    val = seed_val + hiner_val + synth_val + hard_val
    test = seed_test + hiner_test + synth_test + hard_test

    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    write_jsonl(train, data_dir / "train_v1.jsonl")
    write_jsonl(val, data_dir / "val_v1.jsonl")
    write_jsonl(test, data_dir / "test_v1.jsonl")

    manifest = {
        "split_seed": 42,
        "splits": {
            "train": {
                "total": len(train),
                "handcrafted_seed": len(seed_train),
                "hiner": len(hiner_train),
                "synthetic_dense": len(synth_train),
                "hardcases": len(hard_train),
            },
            "val": {
                "total": len(val),
                "hiner": len(hiner_val),
                "synthetic_dense": len(synth_val),
                "hardcases": len(hard_val),
            },
            "test": {
                "total": len(test),
                "hiner": len(hiner_test),
                "synthetic_dense": len(synth_test),
                "hardcases": len(hard_test),
            },
        },
        "hardcase_per_category_split": "2 train / 1 val / 1 test (each of 10 categories)",
    }

    with open(data_dir / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("\n=== Split summary ===")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
