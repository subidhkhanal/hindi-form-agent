# Data

## Files

### `handcrafted_seed.jsonl`

Ten hand-crafted (input_text, output_json, metadata) triples used as a quality
anchor for the fine-tuning dataset. Each Hindi self-description was written to
sound like a real speaker — varying register (casual/formal/Hinglish), region
(Bihar, UP, MP, Delhi, Mumbai, Rajasthan), and completeness (sparse / moderate
/ dense).

**Dataset language scope:** Standard Modern Hindi (Devanagari) and Roman-script
Hinglish only. Regional dialects (Bhojpuri, Awadhi, Maithili, Magahi) are out
of scope for v1 — they require dedicated dialect-aware annotation that's
planned for a future iteration.

The set deliberately includes:

- Code-mixed Hinglish (examples #4, #5, #9)
- Self-corrected / conflicting age (examples #5, #10)
- All four caste categories (general, OBC, SC, ST)
- All four government ID booleans (`has_aadhaar`, `has_pan`, `has_voter_id`, `has_ration_card`)

## Format

One JSON object per line:

```json
{
  "input_text": "<natural Hindi text>",
  "output_json": { /* CitizenProfile fields */ },
  "metadata": {
    "persona": "<short description>",
    "completeness": "sparse" | "moderate" | "dense",
    "formality": "casual" | "formal" | "hinglish",
    "region": "<state or region>"
  }
}
```

## Schema

`output_json` must validate against [`schemas.citizen_profile.CitizenProfile`](../schemas/citizen_profile.py).
Run `python utils/validate_jsonl.py data/handcrafted_seed.jsonl` to verify.

## Privacy

**No real personal data.** All names, ages, locations, incomes, and IDs in
this directory are synthetic. Government ID fields are stored as booleans
only — never as actual ID numbers — by design of the schema.
