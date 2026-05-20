"""Convert HiNER (cfilt/HiNER-collapsed) into CitizenProfile JSONL entries.

Strategy
--------
For each HiNER sentence:
  1. Parse BIO-tagged tokens into entity spans.
  2. Keep sentences that have at least one PER (person) entity and
     pass length filters.
  3. Extract the first PER as full_name.
  4. For each LOC entity, classify as state / town / district
     via data_prep.indian_states.classify_location() and assign
     to the first unfilled corresponding field.
  5. Validate every output against CitizenProfile, drop failures.

Outputs sparse profiles (typically 1-4 fields filled). That's expected.
Synthetic generation in Days 3-7 will produce dense first-person profiles
to complement these.

HiNER-collapsed label scheme (verified via explore_hiner.py):
  O, B-PER, I-PER, B-LOC, I-LOC, B-ORG, I-ORG
ORG tags are ignored entirely — the dataset over-tags I-ORG on non-entity
tokens, but PER and LOC spans are reliable in spot-checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from datasets import load_dataset
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.citizen_profile import CitizenProfile  # noqa: E402
from data_prep.indian_states import classify_location  # noqa: E402
from data_prep.ner_stoplist import NER_NOISE_STOPLIST  # noqa: E402


MIN_TOKENS = 5
MAX_TOKENS = 50
TRAILING_PUNCT = ",।.;:!?\"'“”‘’()[]"
MIN_SINGLE_TOKEN_NAME_LEN = 4  # single-token names with <4 chars rejected as likely noise


def parse_bio_entities(tokens: list[str], tags: list[str]) -> list[tuple[str, str]]:
    """Convert BIO-tagged tokens into list of (entity_text, entity_type)."""
    entities: list[tuple[str, str]] = []
    current_tokens: list[str] = []
    current_type: str | None = None

    def flush() -> None:
        nonlocal current_tokens, current_type
        if current_tokens and current_type:
            text = " ".join(current_tokens).strip().strip(TRAILING_PUNCT).strip()
            if text:
                entities.append((text, current_type))
        current_tokens, current_type = [], None

    for tok, tag in zip(tokens, tags):
        if tag == "O" or tag is None:
            flush()
        elif tag.startswith("B-"):
            flush()
            current_tokens = [tok]
            current_type = tag[2:]
        elif tag.startswith("I-"):
            if current_type == tag[2:]:
                current_tokens.append(tok)
            else:
                flush()
                current_tokens = [tok]
                current_type = tag[2:]
        else:
            flush()

    flush()
    return entities


def is_noisy_name(name: str) -> bool:
    """Reject single-token names shorter than MIN_SINGLE_TOKEN_NAME_LEN.

    Multi-token names (2+ tokens) are always allowed regardless of length;
    Hindi single-character/two-character standalone names are overwhelmingly
    HiNER mistags of common particles.
    """
    if len(name.split()) == 1 and len(name) < MIN_SINGLE_TOKEN_NAME_LEN:
        return True
    return False


def hiner_to_profile(
    tokens: list[str], tags: list[str], counters: dict[str, int]
) -> dict | None:
    """Convert one HiNER example to a profile dict.

    Returns None if any filter rule rejects the entry. `counters` is mutated
    so the caller can report rejection breakdown.
    """
    if not (MIN_TOKENS <= len(tokens) <= MAX_TOKENS):
        counters["length"] += 1
        return None

    entities = parse_bio_entities(tokens, tags)
    persons = [e for (e, t) in entities if t == "PER"]
    locations = [e for (e, t) in entities if t == "LOC"]

    if not persons:
        counters["no_per"] += 1
        return None

    full_name = persons[0].strip()
    if not full_name:
        counters["empty_name"] += 1
        return None

    if is_noisy_name(full_name):
        counters["short_name"] += 1
        return None

    if full_name in NER_NOISE_STOPLIST:
        counters["stoplist_name"] += 1
        return None

    profile: dict = {"full_name": full_name}

    state_set = False
    town_set = False
    district_set = False
    bad_location = False

    for loc in locations:
        if loc in NER_NOISE_STOPLIST:
            bad_location = True
            break
        bucket = classify_location(loc)
        if bucket == "state" and not state_set:
            profile["state"] = loc
            state_set = True
        elif bucket == "town" and not town_set:
            profile["village_or_town"] = loc
            town_set = True
        elif bucket == "district" and not district_set:
            profile["district"] = loc
            district_set = True

    if bad_location:
        counters["stoplist_location"] += 1
        return None

    if sum(1 for v in profile.values() if v is not None) < 2:
        counters["too_sparse"] += 1
        return None

    return profile


def main() -> None:
    print("Loading HiNER-collapsed...")
    ds = load_dataset("cfilt/HiNER-collapsed", split="train", trust_remote_code=True)
    label_names = ds.features["ner_tags"].feature.names
    print(f"  Loaded {len(ds):,} train sentences.")
    print(f"  Label names: {label_names}")

    out_path = Path(__file__).resolve().parents[1] / "data" / "from_ner_v1.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    written = 0
    counters = {
        "length": 0,
        "no_per": 0,
        "empty_name": 0,
        "short_name": 0,
        "stoplist_name": 0,
        "stoplist_location": 0,
        "too_sparse": 0,
        "validation": 0,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in ds:
            tokens = ex["tokens"]
            tags = [label_names[t] for t in ex["ner_tags"]]

            profile_dict = hiner_to_profile(tokens, tags, counters)
            if profile_dict is None:
                continue

            try:
                CitizenProfile(**profile_dict)
            except ValidationError:
                counters["validation"] += 1
                continue

            entry = {
                "input_text": " ".join(tokens),
                "output_json": {
                    field: profile_dict.get(field)
                    for field in CitizenProfile.model_fields
                },
                "metadata": {
                    "source": "hiner",
                    "perspective": "third-person",
                    "fields_filled": sum(1 for v in profile_dict.values() if v is not None),
                },
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            written += 1

    print()
    print("Conversion complete.")
    print(f"  Written:                       {written:>6,}  -> {out_path}")
    print(f"  Rejected (length):             {counters['length']:>6,}")
    print(f"  Rejected (no PER):             {counters['no_per']:>6,}")
    print(f"  Rejected (empty name):         {counters['empty_name']:>6,}")
    print(f"  Rejected (short single-token): {counters['short_name']:>6,}")
    print(f"  Rejected (name in stoplist):   {counters['stoplist_name']:>6,}")
    print(f"  Rejected (loc in stoplist):    {counters['stoplist_location']:>6,}")
    print(f"  Rejected (fields_filled < 2):  {counters['too_sparse']:>6,}")
    print(f"  Rejected (schema validation):  {counters['validation']:>6,}")

    if written < 1000:
        print()
        print("WARNING: Fewer than 1,000 examples produced. Investigate the "
              "BIO parser and label-name handling.")


if __name__ == "__main__":
    main()
