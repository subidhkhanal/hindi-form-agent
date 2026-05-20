"""Print persona slots in a given range for batch generation reference."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="from_slot", type=int, required=True)
    parser.add_argument("--to", dest="to_slot", type=int, required=True)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    path = project_root / "data_prep" / "personas_full.json"
    with open(path, "r", encoding="utf-8") as f:
        personas = json.load(f)

    selected = [p for p in personas if args.from_slot <= p["slot"] <= args.to_slot]
    for p in selected:
        print(
            f"slot {p['slot']:>3} | {p['region']:<22} | "
            f"{p['age_range']:<6} | {p['gender']:<6} | "
            f"{p['occupation_type']:<26} | "
            f"income={p['income_level']:<18} | "
            f"caste={p['caste']:<11} | "
            f"religion={p['religion']:<10} | "
            f"marital={p['marital_status']}"
        )
    print(f"\nTotal: {len(selected)} personas in range [{args.from_slot}, {args.to_slot}]")


if __name__ == "__main__":
    main()
