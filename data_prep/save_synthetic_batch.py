"""Validate and persist a batch of synthetic citizen-profile entries.

Reads a list of candidate entries from a JSON array file, validates each
against CitizenProfile, and appends the valid ones to a target JSONL file.
Rejects entries that fail schema or fall outside the [min_fields, max_fields]
density window. Reports a summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.citizen_profile import CitizenProfile  # noqa: E402

console = Console()


SCHEMA_FIELDS = list(CitizenProfile.model_fields.keys())


def validate_and_count_fields(entry: dict) -> tuple[bool, int, str | None]:
    """Returns (is_valid, fields_filled_count, error_message_or_None)."""
    if "input_text" not in entry or "output_json" not in entry:
        return False, 0, "Missing input_text or output_json"

    output = entry["output_json"]
    try:
        CitizenProfile(**output)
    except ValidationError as e:
        return False, 0, f"Schema violation: {e}"

    filled = sum(1 for f in SCHEMA_FIELDS if output.get(f) is not None)
    return True, filled, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist synthetic batch")
    parser.add_argument("--input", type=Path, required=True,
                        help="JSON file containing an array of candidate entries")
    parser.add_argument("--output", type=Path, required=True,
                        help="Target JSONL file (will append)")
    parser.add_argument("--min-fields", type=int, default=11,
                        help="Reject entries with fewer than this many filled fields")
    parser.add_argument("--max-fields", type=int, default=16)
    args = parser.parse_args()

    if not args.input.exists():
        console.print(f"[red]Input file not found: {args.input}[/red]")
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        candidates = json.load(f)

    if not isinstance(candidates, list):
        console.print("[red]Input must be a JSON array.[/red]")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    rejected_schema = 0
    rejected_density = 0
    field_counts: list[int] = []

    with open(args.output, "a", encoding="utf-8") as f:
        for idx, entry in enumerate(candidates, 1):
            valid, filled, err = validate_and_count_fields(entry)
            if not valid:
                console.print(f"  [red]x[/red] Entry {idx}: {err}")
                rejected_schema += 1
                continue
            if not (args.min_fields <= filled <= args.max_fields):
                console.print(
                    f"  [yellow]![/yellow] Entry {idx}: {filled} fields "
                    f"(want {args.min_fields}-{args.max_fields})"
                )
                rejected_density += 1
                continue

            output_full = {
                field: entry["output_json"].get(field)
                for field in SCHEMA_FIELDS
            }
            normalized = {
                "input_text": entry["input_text"],
                "output_json": output_full,
                "metadata": entry.get("metadata", {}),
            }
            f.write(json.dumps(normalized, ensure_ascii=False) + "\n")
            written += 1
            field_counts.append(filled)

    console.print()
    console.print(f"[bold]Persistence summary[/bold]")
    console.print(f"  [green]ok[/green] Written:           {written}")
    console.print(f"  [red]x[/red] Rejected (schema):  {rejected_schema}")
    console.print(f"  [yellow]![/yellow] Rejected (density): {rejected_density}")
    if field_counts:
        console.print(f"  Avg fields filled:    {sum(field_counts)/len(field_counts):.1f}")
        console.print(f"  Min/Max:              {min(field_counts)} / {max(field_counts)}")

    return 0 if written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
