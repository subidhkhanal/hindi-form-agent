"""One-shot: replace flagged entries in batch03 / batch04 JSONL files.

Slot 140 (batch03): MGNREGA wrongly placed in urban Chandigarh, income inflated.
  Fix: change occupation to small kirana shopkeeper, income ₹15,000.
Slot 174 (batch04): Hegde (Brahmin surname) wrongly paired with SC caste.
  Fix: change surname to Holaya (Karnataka SC-compatible).
Slot 180 (batch04): Anganwadi worker income ₹20K wildly above ₹4.5–10K reality.
  Fix: reduce income to ₹8,000 and adjust text accordingly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ROOT / "data" / "batches"


REPLACEMENTS = {
    140: {
        "input_text": "मेरा नाम राम लाल यादव है। मेरी आयु सड़सठ वर्ष है। मेरी पत्नी पार्वती देवी हैं। हम चंडीगढ़ के सेक्टर 50 में रहते हैं, पिनकोड 160047 है। मेरी एक छोटी किराना दुकान है, महीने में करीब अठारह हजार रुपये कमा लेता हूं। मैं पिछड़े वर्ग का हिंदू हूं। आधार कार्ड और बैंक खाता है।",
        "output_json": {"full_name": "राम लाल यादव", "age": 67, "gender": "male", "marital_status": "married", "father_or_husband_name": "पार्वती देवी", "village_or_town": "चंडीगढ़", "state": "चंडीगढ़", "pincode": "160047", "occupation": "किराना दुकानदार", "monthly_income_inr": 18000, "caste_category": "obc", "religion": "हिंदू", "has_aadhaar": True, "has_bank_account": True},
        "metadata": {"persona": "Chandigarh kirana shopkeeper elderly married OBC Hindu", "completeness": "dense", "formality": "formal", "region": "Chandigarh", "source": "synthetic-claude-day4", "slot": 140},
    },
    174: {
        "input_text": "मेरा नाम सुजाता होलया है। मेरी उम्र बाईस साल है। मेरे पति का नाम रवि होलया है। हम कर्नाटक के बेंगलुरु शहर के यलहंका इलाके में रहते हैं, पिनकोड 560064 है। मैं गृहिणी हूं, पति की आय से करीब बीस हजार रुपये मासिक का घर चलता है। मैं अनुसूचित जाति की हिंदू हूं। आधार कार्ड और बैंक खाता है।",
        "output_json": {"full_name": "सुजाता होलया", "age": 22, "gender": "female", "marital_status": "married", "father_or_husband_name": "रवि होलया", "village_or_town": "यलहंका", "state": "कर्नाटक", "pincode": "560064", "occupation": "गृहिणी", "monthly_income_inr": 20000, "caste_category": "sc", "religion": "हिंदू", "has_aadhaar": True, "has_bank_account": True},
        "metadata": {"persona": "Karnataka homemaker young married SC Hindu", "completeness": "dense", "formality": "formal", "region": "Karnataka", "source": "synthetic-claude-day4", "slot": 174},
    },
    180: {
        "input_text": "इस उम्र में भी आंगनवाड़ी में बच्चों की देखभाल का काम करती हूं। मेरा नाम मरीना डेका है, उम्र अड़सठ साल है। मेरे पति का नाम सेमुअल डेका है। हम असम के सोनितपुर जिले में रहते हैं। मानदेय करीब आठ हजार रुपये मासिक मिलते हैं। मैं सामान्य जाति की ईसाई हूं। आधार कार्ड, मतदाता पहचान पत्र और बैंक खाता है।",
        "output_json": {"full_name": "मरीना डेका", "age": 68, "gender": "female", "marital_status": "married", "father_or_husband_name": "सेमुअल डेका", "district": "सोनितपुर", "state": "असम", "occupation": "आंगनवाड़ी कार्यकर्ता", "monthly_income_inr": 8000, "caste_category": "general", "religion": "ईसाई", "has_aadhaar": True, "has_voter_id": True, "has_bank_account": True},
        "metadata": {"persona": "Assam elderly anganwadi married general Christian", "completeness": "dense", "formality": "formal", "region": "Assam", "source": "synthetic-claude-day4", "slot": 180},
    },
}

SLOT_TO_FILE = {
    140: BATCHES / "synthetic_dense_v1_batch03.jsonl",
    174: BATCHES / "synthetic_dense_v1_batch04.jsonl",
    180: BATCHES / "synthetic_dense_v1_batch04.jsonl",
}


def normalize_output(output: dict) -> dict:
    """Fill missing schema fields with None to match Day 3+ harness format."""
    from schemas.citizen_profile import CitizenProfile  # noqa: E402
    return {field: output.get(field) for field in CitizenProfile.model_fields}


def main() -> None:
    sys.path.insert(0, str(ROOT))
    from schemas.citizen_profile import CitizenProfile  # noqa: E402

    files_to_rewrite: dict[Path, list[str]] = {}

    for slot, replacement in REPLACEMENTS.items():
        path = SLOT_TO_FILE[slot]
        if path not in files_to_rewrite:
            files_to_rewrite[path] = path.read_text(encoding="utf-8").splitlines()

    for slot, replacement in REPLACEMENTS.items():
        path = SLOT_TO_FILE[slot]
        lines = files_to_rewrite[path]

        new_output = normalize_output(replacement["output_json"])
        # Validate before writing
        CitizenProfile(**new_output)
        new_entry = {
            "input_text": replacement["input_text"],
            "output_json": new_output,
            "metadata": replacement["metadata"],
        }
        new_line = json.dumps(new_entry, ensure_ascii=False)

        # Find the existing line by slot match
        replaced = False
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get("metadata", {}).get("slot") == slot:
                lines[i] = new_line
                replaced = True
                fields_filled = sum(1 for v in new_output.values() if v is not None)
                print(f"  slot {slot}: replaced in {path.name} (now {fields_filled} fields)")
                break
        if not replaced:
            print(f"  WARN: slot {slot} not found in {path.name}")

    for path, lines in files_to_rewrite.items():
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
