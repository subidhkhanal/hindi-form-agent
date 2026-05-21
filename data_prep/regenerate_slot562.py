"""One-shot: replace slot 562 with a culturally-appropriate Buddhist persona.

Original: Saraswati Sharma + Buddhist + UP — Brahmin surname × Buddhist is
implausible per the updated domain reference. Replace with a Maharashtra
Ambedkarite-Buddhist persona (Kamble surname, SC caste, MH region).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "batches" / "synthetic_dense_v1_batch12.jsonl"


REPLACEMENT = {
    "input_text": "मेरा नाम सुनीता कांबले है। मेरी आयु अड़तालीस साल है। मेरे पति का नाम भीमराव कांबले है। हम महाराष्ट्र के नागपुर शहर में रहते हैं। पहले राज्य परिवहन की बस चलाती थी, अब वाहन खराब हो गया, फिलहाल कोई आय नहीं है। मैं अनुसूचित जाति की हूं और बौद्ध धर्म मानती हूं। आधार कार्ड और बैंक खाता है।",
    "output_json": {
        "full_name": "सुनीता कांबले",
        "age": 48,
        "gender": "female",
        "marital_status": "married",
        "father_or_husband_name": "भीमराव कांबले",
        "village_or_town": "नागपुर",
        "state": "महाराष्ट्र",
        "occupation": "बस चालक",
        "caste_category": "sc",
        "religion": "बौद्ध",
        "has_aadhaar": True,
        "has_bank_account": True,
    },
    "metadata": {
        "persona": "Maharashtra Ambedkarite bus driver no work married SC Buddhist female",
        "completeness": "dense",
        "formality": "formal",
        "region": "Maharashtra",
        "source": "synthetic-claude-day4",
        "slot": 562,
    },
}


def normalize_output(output: dict) -> dict:
    sys.path.insert(0, str(ROOT))
    from schemas.citizen_profile import CitizenProfile
    return {field: output.get(field) for field in CitizenProfile.model_fields}


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from schemas.citizen_profile import CitizenProfile

    lines = PATH.read_text(encoding="utf-8").splitlines()

    new_output = normalize_output(REPLACEMENT["output_json"])
    CitizenProfile(**new_output)
    new_entry = {
        "input_text": REPLACEMENT["input_text"],
        "output_json": new_output,
        "metadata": REPLACEMENT["metadata"],
    }
    new_line = json.dumps(new_entry, ensure_ascii=False)

    replaced = False
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("metadata", {}).get("slot") == 562:
            lines[i] = new_line
            fields_filled = sum(1 for v in new_output.values() if v is not None)
            print(f"  slot 562: replaced ({fields_filled} fields)")
            replaced = True
            break
    if not replaced:
        print("  WARN: slot 562 not found")

    PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {PATH}")


if __name__ == "__main__":
    main()
