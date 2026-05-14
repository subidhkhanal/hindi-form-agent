"""Compute statistics over a JSONL dataset to monitor diversity and coverage."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

SCHEMA_FIELDS = [
    "full_name", "age", "gender", "marital_status",
    "father_or_husband_name", "number_of_dependents",
    "village_or_town", "district", "state", "pincode",
    "occupation", "monthly_income_inr", "caste_category", "religion",
    "has_aadhaar", "has_pan", "has_voter_id", "has_ration_card",
    "has_bank_account", "bank_name",
]


def compute_stats(path: Path) -> None:
    field_coverage: Counter[str] = Counter()
    input_lengths: list[int] = []
    completeness_dist: Counter[str] = Counter()
    formality_dist: Counter[str] = Counter()
    region_dist: Counter[str] = Counter()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)

            text = entry.get("input_text", "")
            input_lengths.append(len(text))

            output = entry.get("output_json", {})
            filled = sum(1 for fld in SCHEMA_FIELDS if output.get(fld) is not None)

            for fld in SCHEMA_FIELDS:
                if output.get(fld) is not None:
                    field_coverage[fld] += 1

            if filled <= 6:
                completeness_dist["sparse (≤6)"] += 1
            elif filled <= 10:
                completeness_dist["moderate (7-10)"] += 1
            else:
                completeness_dist["dense (11+)"] += 1

            meta = entry.get("metadata", {})
            formality_dist[meta.get("formality", "unknown")] += 1
            region_dist[meta.get("region", "unknown")] += 1

    total = sum(completeness_dist.values())

    console.print(f"\n[bold]Dataset stats: {path}[/bold]")
    console.print(f"  Total examples: {total}")
    if input_lengths:
        avg = sum(input_lengths) / len(input_lengths)
        console.print(f"  Avg input length: {avg:.0f} chars")
        console.print(f"  Min/Max length: {min(input_lengths)} / {max(input_lengths)}")

    console.print("\n[bold]Completeness distribution:[/bold]")
    for k, v in completeness_dist.items():
        pct = 100 * v / total if total else 0
        console.print(f"  {k}: {v} ({pct:.1f}%)")

    console.print("\n[bold]Formality distribution:[/bold]")
    for k, v in formality_dist.items():
        pct = 100 * v / total if total else 0
        console.print(f"  {k}: {v} ({pct:.1f}%)")

    console.print("\n[bold]Region distribution:[/bold]")
    for k, v in region_dist.items():
        pct = 100 * v / total if total else 0
        console.print(f"  {k}: {v} ({pct:.1f}%)")

    table = Table(title="\nField coverage")
    table.add_column("Field", style="cyan")
    table.add_column("Count", style="green")
    table.add_column("%", style="yellow")
    for field in SCHEMA_FIELDS:
        count = field_coverage[field]
        pct = 100 * count / total if total else 0
        table.add_row(field, str(count), f"{pct:.1f}%")
    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stats for a JSONL dataset")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if not args.path.exists():
        console.print(f"[red]File not found: {args.path}[/red]")
        return
    compute_stats(args.path)


if __name__ == "__main__":
    main()
