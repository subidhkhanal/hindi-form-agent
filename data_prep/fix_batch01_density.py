"""One-shot fix script: trim over-dense entries in raw_batch01.json.

Reads the raw batch, applies surgical edits to entries that have >16 fields
filled by removing a chosen field from BOTH output_json AND the matching
substring from input_text. Writes the modified batch back.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH_FILE = ROOT / "data_prep" / "raw_batch01.json"


# (slot, field_to_drop, text_substring_to_remove_or_replace, replacement)
# Where replacement = "" means delete the substring outright.
FIXES = [
    # Slot 2: drop pincode AND has_ration_card (was at 18)
    (2, "pincode", ", पिनकोड 226010 है", ""),
    (2, "has_ration_card", ", मतदाता पहचान पत्र एवं राशन कार्ड", ", मतदाता पहचान पत्र"),

    # Slot 5: drop number_of_dependents
    (5, "number_of_dependents", " हमारी दो बेटियां हैं।", ""),

    # Slot 9: drop has_ration_card
    (9, "has_ration_card", " राशन कार्ड पर मेरा नाम पिताजी के साथ चढ़ा हुआ है।", ""),

    # Slot 12: drop number_of_dependents
    (12, "number_of_dependents", " हमारा एक बेटा है।", ""),

    # Slot 14: drop number_of_dependents
    (14, "number_of_dependents", " हमारी दो बेटियां हैं, बड़ी कॉलेज में पढ़ती है।", ""),

    # Slot 15: drop number_of_dependents
    (15, "number_of_dependents", " पत्नी और एक बेटा है।", ""),

    # Slot 19: drop has_voter_id (was: "मतदाता पहचान पत्र, राशन कार्ड सब है")
    (19, "has_voter_id", " पैन कार्ड, मतदाता पहचान पत्र, राशन कार्ड सब है।",
     " पैन कार्ड और राशन कार्ड दोनों हैं।"),

    # Slot 23: drop has_voter_id
    (23, "has_voter_id", "आधार कार्ड, मतदाता पहचान पत्र और राशन कार्ड है",
     "आधार कार्ड और राशन कार्ड है"),

    # Slot 26: drop number_of_dependents
    (26, "number_of_dependents", " दो बेटियां हैं, बड़ी की शादी हो गई है।", ""),

    # Slot 27: drop number_of_dependents
    (27, "number_of_dependents", " हमारे दो बच्चे हैं।", ""),

    # Slot 39: drop number_of_dependents
    (39, "number_of_dependents", ", पत्नी और दो बच्चे हैं", ""),

    # Slot 40: drop number_of_dependents
    (40, "number_of_dependents", " हमारे दो बेटे हैं।", ""),

    # Slot 41: drop number_of_dependents
    (41, "number_of_dependents", " पत्नी और तीन बच्चे हैं, सबसे बड़ा दसवीं में पढ़ता है।", ""),

    # Slot 50: drop number_of_dependents
    (50, "number_of_dependents", " हमारी एक बेटी है, जो कक्षा सात में पढ़ती है।", ""),
]


def main() -> None:
    with open(BATCH_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    by_slot = {e["metadata"]["slot"]: e for e in entries}

    applied: list[str] = []
    skipped: list[str] = []
    for slot, field, find, repl in FIXES:
        entry = by_slot.get(slot)
        if not entry:
            skipped.append(f"slot {slot}: not found")
            continue
        # Remove the JSON field if present
        if field in entry["output_json"]:
            del entry["output_json"][field]
            applied.append(f"slot {slot}: dropped JSON field '{field}'")
        else:
            skipped.append(f"slot {slot}: JSON field '{field}' not present")
        # Surgery on input_text
        text = entry["input_text"]
        if find in text:
            entry["input_text"] = text.replace(find, repl, 1)
            applied.append(f"slot {slot}: trimmed text segment for '{field}'")
        else:
            skipped.append(f"slot {slot}: text segment for '{field}' not matched")

    with open(BATCH_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    print("Applied:")
    for a in applied:
        print(f"  + {a}")
    if skipped:
        print("Skipped (review needed):")
        for s in skipped:
            print(f"  ! {s}")


if __name__ == "__main__":
    main()
