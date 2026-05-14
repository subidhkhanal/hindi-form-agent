"""Validate a JSONL file of (input_text, output_json) pairs against the schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from rich.table import Table

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.citizen_profile import CitizenProfile  # noqa: E402

console = Console()


def validate_file(path: Path) -> tuple[int, int, list[tuple[int, str]]]:
    """Returns (valid_count, total_count, errors)."""
    valid = 0
    total = 0
    errors: list[tuple[int, str]] = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                entry = json.loads(line)
                if "input_text" not in entry or "output_json" not in entry:
                    errors.append((line_no, "Missing 'input_text' or 'output_json' key"))
                    continue
                CitizenProfile(**entry["output_json"])
                valid += 1
            except json.JSONDecodeError as e:
                errors.append((line_no, f"Invalid JSON: {e}"))
            except ValidationError as e:
                errors.append((line_no, f"Schema violation: {e}"))
            except Exception as e:
                errors.append((line_no, f"Unexpected: {e}"))

    return valid, total, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate JSONL against CitizenProfile schema")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    if not args.path.exists():
        console.print(f"[red]File not found: {args.path}[/red]")
        return 1

    valid, total, errors = validate_file(args.path)

    console.print(f"\n[bold]Validation: {args.path}[/bold]")
    console.print(f"  [green]✓[/green] Valid: {valid}/{total}")
    console.print(f"  [red]✗[/red] Errors: {len(errors)}")

    if errors:
        table = Table(title="First 10 errors")
        table.add_column("Line", style="cyan")
        table.add_column("Error", style="red", overflow="fold")
        for line_no, err in errors[:10]:
            table.add_row(str(line_no), str(err)[:200])
        console.print(table)
        return 1

    console.print("[green]All entries valid.[/green]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
