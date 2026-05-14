# Hindi Form-Filling Agent

A QLoRA fine-tuning project that adapts **Sarvam-1** (2B-parameter Hindi/Indic base
model) to extract structured `CitizenProfile` JSON from free-form Hindi
self-descriptions — for use in government scheme registration, banking KYC,
insurance intake, and healthcare onboarding flows for Hindi-speaking users.

**Status: Day 1 ✅**

## Roadmap

- [ ] **Week 1 — Data foundation** (in progress)
  - [x] Day 1: Schema, seed examples, validation utilities
  - [ ] Day 2: HiNER → schema conversion (~1,500 examples)
  - [ ] Day 3–7: Synthetic generation, deduplication, train/val split
- [ ] **Week 2 — Data quality**: human review, hard-negative mining, schema-stress cases
- [ ] **Week 3 — Training infra**: QLoRA config for Sarvam-1, 4-bit quant, LoRA adapters
- [ ] **Week 4 — Training runs**: experiment grid, W&B tracking, checkpoint selection
- [ ] **Week 5 — Evaluation**: per-field F1, structural validity, hallucination rate, native-speaker review
- [ ] **Week 6 — Deployment**: FastAPI inference service, Hugging Face Spaces demo

## Stack

- **Base model**: [Sarvam-1](https://huggingface.co/sarvamai/sarvam-1) (2B params, Indic-tuned)
- **Fine-tuning**: QLoRA (4-bit NF4 quantization + LoRA adapters)
- **Schema/validation**: Pydantic v2
- **Serving**: FastAPI
- **Demo**: Hugging Face Spaces

## Repository layout

```
hindi-form-agent/
├── schemas/            # Pydantic target schemas (CitizenProfile)
├── data/               # JSONL training data + dataset documentation
├── data_prep/          # NER-to-schema converters, synthesizers (Week 1)
├── utils/              # Validation, statistics, dataset utilities
├── training/           # QLoRA training scripts (Weeks 3-4)
├── eval/               # Evaluation harness (Week 5)
└── app/                # FastAPI service (Week 6)
```

## Quick start

```bash
uv venv --python 3.10
uv pip install -e .

# Validate the seed dataset
python utils/validate_jsonl.py data/handcrafted_seed.jsonl

# View dataset statistics
python utils/dataset_stats.py data/handcrafted_seed.jsonl
```

On Windows shells, set `PYTHONIOENCODING=utf-8` so Devanagari characters render
correctly in stdout.

## License

MIT
