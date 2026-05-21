"""Compare stats across train/val/test splits as a markdown report."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def load(path: Path) -> list[dict]:
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def stats(entries: list[dict]) -> dict:
    n = len(entries)
    if n == 0:
        return {}

    source_counts: Counter = Counter()
    fields_filled_dist: Counter = Counter()
    religion_counts: Counter = Counter()
    caste_counts: Counter = Counter()
    state_counts: Counter = Counter()
    hardcase_cats: Counter = Counter()

    for e in entries:
        meta = e.get("metadata", {})
        source_counts[meta.get("source", "unknown")] += 1

        output = e.get("output_json", {})
        ff = sum(1 for v in output.values() if v is not None)
        fields_filled_dist[ff] += 1

        if output.get("religion"):
            religion_counts[output["religion"]] += 1
        if output.get("caste_category"):
            caste_counts[output["caste_category"]] += 1
        if output.get("state"):
            state_counts[output["state"]] += 1
        if "hard_case_category" in meta:
            hardcase_cats[meta["hard_case_category"]] += 1

    avg_fields = sum(k * v for k, v in fields_filled_dist.items()) / n

    return {
        "n": n,
        "avg_fields_filled": avg_fields,
        "sources": dict(source_counts),
        "fields_filled_dist": dict(sorted(fields_filled_dist.items())),
        "religion_top5": dict(religion_counts.most_common(5)),
        "caste_dist": dict(caste_counts),
        "n_unique_states": len(state_counts),
        "hardcase_cats": dict(hardcase_cats),
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"

    train = load(data_dir / "train_v1.jsonl")
    val = load(data_dir / "val_v1.jsonl")
    test = load(data_dir / "test_v1.jsonl")

    tr, vl, ts = stats(train), stats(val), stats(test)

    print("# Train/Val/Test Distribution Comparison\n")
    print("## Top-level metrics\n")
    print("| Metric | Train | Val | Test |")
    print("|---|---|---|---|")
    print(f"| N | {len(train)} | {len(val)} | {len(test)} |")
    print(f"| Avg fields filled | {tr['avg_fields_filled']:.2f} | {vl['avg_fields_filled']:.2f} | {ts['avg_fields_filled']:.2f} |")
    print(f"| Unique states | {tr['n_unique_states']} | {vl['n_unique_states']} | {ts['n_unique_states']} |")

    print("\n## Source composition\n")
    print("| Source | Train | Val | Test |")
    print("|---|---|---|---|")
    for source in ["handcrafted_seed", "hiner", "synthetic_dense", "hardcases"]:
        tr_c = tr["sources"].get(source, 0)
        vl_c = vl["sources"].get(source, 0)
        ts_c = ts["sources"].get(source, 0)
        print(f"| {source} | {tr_c} | {vl_c} | {ts_c} |")

    print("\n## Fields-filled distribution\n")
    print("| Fields | Train | Val | Test |")
    print("|---|---|---|---|")
    all_ff = sorted(set(tr["fields_filled_dist"].keys())
                    | set(vl["fields_filled_dist"].keys())
                    | set(ts["fields_filled_dist"].keys()))
    for ff in all_ff:
        print(f"| {ff} | {tr['fields_filled_dist'].get(ff, 0)} | "
              f"{vl['fields_filled_dist'].get(ff, 0)} | "
              f"{ts['fields_filled_dist'].get(ff, 0)} |")

    print("\n## Caste distribution (where present)\n")
    print("| Caste | Train | Val | Test |")
    print("|---|---|---|---|")
    for cat in ["general", "obc", "sc", "st"]:
        print(f"| {cat} | {tr['caste_dist'].get(cat, 0)} | "
              f"{vl['caste_dist'].get(cat, 0)} | "
              f"{ts['caste_dist'].get(cat, 0)} |")

    print("\n## Religion (top 5 across splits)\n")
    print("| Religion | Train | Val | Test |")
    print("|---|---|---|---|")
    all_religions = sorted(set(tr["religion_top5"].keys())
                           | set(vl["religion_top5"].keys())
                           | set(ts["religion_top5"].keys()))
    for rel in all_religions:
        print(f"| {rel} | {tr['religion_top5'].get(rel, 0)} | "
              f"{vl['religion_top5'].get(rel, 0)} | "
              f"{ts['religion_top5'].get(rel, 0)} |")

    print("\n## Hard-case category coverage (must be 2/1/1 per category)\n")
    print("| Category | Train | Val | Test |")
    print("|---|---|---|---|")
    all_cats = sorted(set(tr["hardcase_cats"].keys())
                      | set(vl["hardcase_cats"].keys())
                      | set(ts["hardcase_cats"].keys()))
    for cat in all_cats:
        print(f"| {cat} | {tr['hardcase_cats'].get(cat, 0)} | "
              f"{vl['hardcase_cats'].get(cat, 0)} | "
              f"{ts['hardcase_cats'].get(cat, 0)} |")


if __name__ == "__main__":
    main()
