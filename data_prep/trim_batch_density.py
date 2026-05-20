"""Trim over-dense entries in a batch JSON file.

For each entry with >max_fields filled, drops fields in priority order and
attempts to remove the matching text segment from input_text. Writes the
modified batch back in place.

Usage: python data_prep/trim_batch_density.py <batch_json_path> [max_fields]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

DROP_PRIORITY = [
    "number_of_dependents",
    "has_voter_id",
    "has_ration_card",
    "has_pan",
    "pincode",
    "bank_name",
    "village_or_town",
    "father_or_husband_name",
    "monthly_income_inr",
]

TEXT_PRUNERS: dict[str, list[tuple[str, str]]] = {
    "number_of_dependents": [
        (r", पत्नी और [ऀ-ॿ]+ बच्चे हैं", ""),
        (r" पत्नी और [ऀ-ॿ]+ बच्चे हैं।", ""),
        (r" हमारे [ऀ-ॿ]+ बच्चे हैं।", ""),
        (r" हमारी [ऀ-ॿ]+ बेटियां हैं।", ""),
        (r" हमारी [ऀ-ॿ]+ बेटियां हैं[^।]*।", ""),
        (r" हमारा [ऀ-ॿ]+ बेटा है।", ""),
        (r" हमारा एक बेटा है।", ""),
        (r" हमारी एक बेटी है।", ""),
        (r" हमारी एक बेटी है[^।]*।", ""),
    ],
    "has_voter_id": [
        (r", मतदाता पहचान पत्र", ""),
        (r"मतदाता पहचान पत्र, ", ""),
        (r" और मतदाता पहचान पत्र", ""),
        (r" एवं मतदाता पहचान पत्र", ""),
    ],
    "has_pan": [
        (r", पैन कार्ड", ""),
        (r"पैन कार्ड, ", ""),
        (r" और पैन कार्ड", ""),
        (r" एवं पैन कार्ड", ""),
    ],
    "has_ration_card": [
        (r", राशन कार्ड", ""),
        (r"राशन कार्ड, ", ""),
        (r" और राशन कार्ड", ""),
        (r" एवं राशन कार्ड", ""),
        (r" राशन कार्ड भी बना हुआ है।", ""),
        (r" राशन कार्ड भी बनवाया है।", ""),
    ],
    "pincode": [
        (r", पिनकोड \d{6} है", ""),
        (r" पिनकोड \d{6} है।", "।"),
    ],
    "bank_name": [],
    "village_or_town": [],
    "father_or_husband_name": [],
    "monthly_income_inr": [],
}


def count_filled(output: dict) -> int:
    return sum(1 for v in output.values() if v is not None)


def trim_entry(entry: dict, max_fields: int) -> tuple[bool, list[str]]:
    output = entry["output_json"]
    text = entry["input_text"]
    notes: list[str] = []
    while count_filled(output) > max_fields:
        dropped = False
        for field in DROP_PRIORITY:
            if field in output and output[field] is not None:
                pruners = TEXT_PRUNERS.get(field, [])
                text_changed = False
                for pattern, replacement in pruners:
                    new_text = re.sub(pattern, replacement, text, count=1)
                    if new_text != text:
                        text = new_text
                        text_changed = True
                        break
                del output[field]
                notes.append(f"dropped {field}" + (" (+text)" if text_changed else " (json only)"))
                dropped = True
                break
        if not dropped:
            notes.append(f"could not drop further; still at {count_filled(output)} fields")
            return False, notes

    entry["input_text"] = text
    entry["output_json"] = output
    return True, notes


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: trim_batch_density.py <batch_json> [max_fields=14]")
        sys.exit(2)

    path = Path(sys.argv[1])
    max_fields = int(sys.argv[2]) if len(sys.argv) > 2 else 14

    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    trimmed = 0
    failed = 0
    for entry in entries:
        original = count_filled(entry["output_json"])
        if original > max_fields:
            ok, notes = trim_entry(entry, max_fields)
            new = count_filled(entry["output_json"])
            slot = entry.get("metadata", {}).get("slot", "?")
            status = "OK" if ok else "PARTIAL"
            print(f"  [{status}] slot {slot}: {original} -> {new}  ({'; '.join(notes)})")
            if ok:
                trimmed += 1
            else:
                failed += 1

    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print(f"\nTrimmed {trimmed} entries; {failed} could not fully meet target.")


if __name__ == "__main__":
    main()
