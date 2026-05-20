"""Generate diverse persona matrix for synthetic data generation.

Produces 800 persona slots. Slots 1-50 are read verbatim from the Day 3
calibration file (`personas_calibration.json`). Slots 51-800 are sampled
from weighted distributions roughly matching Indian demographics, filtered
through a realism check to reject implausible combinations.

Output: `data_prep/personas_full.json`.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


REGIONS_WEIGHTED = [
    ("Uttar Pradesh", 18), ("Maharashtra", 9), ("Bihar", 8),
    ("West Bengal", 7), ("Madhya Pradesh", 6), ("Tamil Nadu", 6),
    ("Rajasthan", 6), ("Karnataka", 5), ("Gujarat", 5),
    ("Andhra Pradesh", 4), ("Odisha", 3), ("Telangana", 3),
    ("Kerala", 3), ("Jharkhand", 3), ("Assam", 3),
    ("Punjab", 2), ("Chhattisgarh", 2), ("Haryana", 2),
    ("Delhi", 2), ("Uttarakhand", 1), ("Himachal Pradesh", 1),
    ("Tripura", 1), ("Meghalaya", 1), ("Manipur", 1),
    ("Goa", 1), ("Jammu and Kashmir", 1), ("Chandigarh", 1),
]

AGE_RANGES_WEIGHTED = [
    ("18-25", 15), ("25-35", 25), ("35-50", 30),
    ("50-65", 20), ("65-80", 10),
]

GENDERS_WEIGHTED = [("male", 48), ("female", 52)]

CASTES_WEIGHTED = [
    ("general", 30), ("obc", 40), ("sc", 15),
    ("st", 10), ("unspecified", 5),
]

RELIGIONS_WEIGHTED = [
    ("Hindu", 80), ("Muslim", 11), ("Christian", 4),
    ("Sikh", 3), ("Buddhist", 1), ("Jain", 1),
]

INCOME_LEVELS_WEIGHTED = [
    ("none", 15),
    ("low_5k_to_15k", 30),
    ("low_15k_to_30k", 25),
    ("middle_30k_to_60k", 20),
    ("high_60k_plus", 10),
]

OCCUPATIONS_WEIGHTED = [
    ("farmer", 12), ("MGNREGA_laborer", 4), ("agricultural_laborer", 6),
    ("dairy_farmer", 2), ("fisherman", 1), ("tea_garden_worker", 1),
    ("auto_driver", 3), ("delivery_executive", 2), ("street_vendor", 3),
    ("domestic_worker", 4), ("construction_laborer", 5),
    ("small_shopkeeper", 6), ("tailor", 3), ("small_business_owner", 3),
    ("milk_vendor", 1), ("salon_owner", 1),
    ("government_clerk", 3), ("school_teacher", 4), ("anganwadi_worker", 2),
    ("ASHA_worker", 2), ("ANM_health_worker", 1),
    ("private_sector_clerk", 4), ("factory_worker", 4),
    ("software_engineer", 2), ("private_sector_executive", 2),
    ("nurse", 2), ("bus_driver", 2), ("watchman", 2),
    ("homemaker", 8), ("student", 4),
    ("retired_government", 2), ("retired_private", 1),
    ("unemployed", 2), ("armed_forces_retired", 1),
]

MARITAL_WEIGHTED = [
    ("single", 20), ("married", 65),
    ("widowed", 12), ("divorced", 3),
]


def weighted_choice(rng: random.Random, options: list[tuple[str, int]]) -> str:
    items, weights = zip(*options)
    return rng.choices(items, weights=weights, k=1)[0]


def passes_realism_check(persona: dict) -> bool:
    age = persona["age_range"]
    occ = persona["occupation_type"]
    income = persona["income_level"]
    marital = persona["marital_status"]

    if age == "18-25" and occ in {"retired_government", "retired_private",
                                  "armed_forces_retired"}:
        return False
    if age == "65-80" and occ in {"software_engineer", "student",
                                  "delivery_executive"}:
        return False
    if occ == "student" and age not in {"18-25", "25-35"}:
        return False
    if occ in {"homemaker", "unemployed", "student"} and income == "high_60k_plus":
        return False
    if age == "18-25" and marital == "widowed":
        return False
    if occ in {"software_engineer", "private_sector_executive"} and income == "none":
        return False
    if occ in {"MGNREGA_laborer", "construction_laborer",
               "agricultural_laborer"} and income == "high_60k_plus":
        return False
    return True


def generate_persona(rng: random.Random, slot: int) -> dict:
    for _ in range(20):
        persona = {
            "slot": slot,
            "region": weighted_choice(rng, REGIONS_WEIGHTED),
            "age_range": weighted_choice(rng, AGE_RANGES_WEIGHTED),
            "gender": weighted_choice(rng, GENDERS_WEIGHTED),
            "occupation_type": weighted_choice(rng, OCCUPATIONS_WEIGHTED),
            "income_level": weighted_choice(rng, INCOME_LEVELS_WEIGHTED),
            "caste": weighted_choice(rng, CASTES_WEIGHTED),
            "religion": weighted_choice(rng, RELIGIONS_WEIGHTED),
            "marital_status": weighted_choice(rng, MARITAL_WEIGHTED),
        }
        if passes_realism_check(persona):
            return persona
    raise RuntimeError(f"Could not generate realistic persona for slot {slot}")


def main() -> None:
    rng = random.Random(42)

    project_root = Path(__file__).resolve().parents[1]

    day3_path = project_root / "data_prep" / "personas_calibration.json"
    with open(day3_path, "r", encoding="utf-8") as f:
        day3_personas = json.load(f)

    print(f"Loaded {len(day3_personas)} Day 3 personas (slots 1-50)")

    new_personas = [generate_persona(rng, slot) for slot in range(51, 801)]
    print(f"Generated {len(new_personas)} new personas (slots 51-800)")

    full = day3_personas + new_personas

    print("\nDistribution sanity check:")
    print(f"  Religions: {dict(Counter(p['religion'] for p in full))}")
    print(f"  Castes:    {dict(Counter(p['caste'] for p in full))}")
    print(f"  Genders:   {dict(Counter(p['gender'] for p in full))}")
    print(f"  Age:       {dict(Counter(p['age_range'] for p in full))}")
    print(f"  Marital:   {dict(Counter(p['marital_status'] for p in full))}")

    out_path = project_root / "data_prep" / "personas_full.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(full)} personas to {out_path}")


if __name__ == "__main__":
    main()
