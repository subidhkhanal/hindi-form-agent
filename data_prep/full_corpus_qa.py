"""Compute the full quality-gate metrics for the aggregated corpus."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "synthetic_dense_v1.jsonl"

SCHEMA_FIELDS = [
    "full_name", "age", "gender", "marital_status",
    "father_or_husband_name", "number_of_dependents",
    "village_or_town", "district", "state", "pincode",
    "occupation", "monthly_income_inr", "caste_category", "religion",
    "has_aadhaar", "has_pan", "has_voter_id", "has_ration_card",
    "has_bank_account", "bank_name",
]


def main() -> None:
    entries = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    n = len(entries)
    print(f"Total entries: {n}")

    # Density distribution
    densities = []
    for e in entries:
        filled = sum(1 for f in SCHEMA_FIELDS if e["output_json"].get(f) is not None)
        densities.append(filled)
    density_counter = Counter(densities)
    print("\nDensity distribution:")
    for d in sorted(density_counter):
        pct = 100 * density_counter[d] / n
        print(f"  {d} fields: {density_counter[d]} ({pct:.1f}%)")
    avg = sum(densities) / n
    print(f"  Avg: {avg:.2f}")

    # Religion
    print("\nReligion distribution:")
    religions = Counter(e["output_json"].get("religion") for e in entries)
    for r, c in religions.most_common():
        pct = 100 * c / n
        print(f"  {r}: {c} ({pct:.1f}%)")

    # Caste
    print("\nCaste distribution:")
    castes = Counter(e["output_json"].get("caste_category") for e in entries)
    for k, c in castes.most_common():
        pct = 100 * c / n
        print(f"  {k}: {c} ({pct:.1f}%)")

    # Gender
    print("\nGender split:")
    genders = Counter(e["output_json"].get("gender") for e in entries)
    for k, c in genders.most_common():
        pct = 100 * c / n
        print(f"  {k}: {c} ({pct:.1f}%)")

    # Region unique
    regions = set(e["output_json"].get("state") for e in entries if e["output_json"].get("state"))
    print(f"\nUnique states/regions: {len(regions)}")

    # Pincode
    pincode_count = sum(1 for e in entries if e["output_json"].get("pincode"))
    print(f"\nPincode coverage: {pincode_count}/{n} ({100*pincode_count/n:.1f}%)")

    # Location coverage: at least one of village_or_town or district
    loc_count = sum(1 for e in entries if e["output_json"].get("village_or_town") or e["output_json"].get("district"))
    print(f"Location (village or district): {loc_count}/{n} ({100*loc_count/n:.1f}%)")

    # Opener variety
    non_mera_naam = sum(1 for e in entries if not e["input_text"].startswith("मेरा नाम"))
    print(f"\nNon-'मेरा नाम' openers: {non_mera_naam}/{n} ({100*non_mera_naam/n:.1f}%)")

    # bank_name when has_bank_account=true
    has_acc = [e for e in entries if e["output_json"].get("has_bank_account") is True]
    has_name = [e for e in has_acc if e["output_json"].get("bank_name") is not None]
    if has_acc:
        pct = 100 * len(has_name) / len(has_acc)
        print(f"\nbank_name when has_bank_account=true: {len(has_name)}/{len(has_acc)} ({pct:.1f}%)")

    # ID explicitly false
    id_false_entries = sum(1 for e in entries if any(
        e["output_json"].get(f) is False
        for f in ["has_aadhaar", "has_pan", "has_voter_id", "has_ration_card", "has_bank_account"]
    ))
    print(f"\nEntries with at least one ID explicitly false: {id_false_entries}/{n} ({100*id_false_entries/n:.1f}%)")


if __name__ == "__main__":
    main()
