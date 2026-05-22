# Results — `lora_v1` (Week 2 Day 3)

Held-out test-set evaluation of the first full QLoRA fine-tune of Sarvam-1 for
Hindi → CitizenProfile JSON extraction.

## Headline

| Metric | Value |
|---|---|
| Parse rate | **290 / 290 (100.0%)** |
| Schema validation rate | **290 / 290 (100.0%)** |
| Overall field accuracy (strict exact-match) | 5692 / 5800 (98.1%) |

Every prediction in the test set was valid JSON conforming to `CitizenProfile`.
Field-level errors come from open-text mismatches and inherited HiNER label
noise, not from broken structure.

## Model

- **Base**: [`sarvamai/sarvam-1`](https://huggingface.co/sarvamai/sarvam-1) (2.5 B params, public)
- **Adapter**: LoRA, saved as `lora_v1/` (~25 MB)
- **Trainable params**: 6,422,528 / 2,531,510,272 = **0.25%**
- **License**: Sarvam non-commercial (inherited from base)

## Training

| Knob | Value |
|---|---|
| Epochs | 3 |
| Steps (effective) | 849 |
| Per-device batch | 2 |
| Gradient accumulation | 4 → effective batch 8 |
| Learning rate | 2e-4, cosine schedule, 5% warmup |
| LoRA `r` / `α` | 16 / 32 |
| LoRA target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| LoRA dropout | 0.05 |
| Max sequence length | 1024 |
| Quantization | 4-bit NF4, double quant, fp16 compute |
| Optimizer | paged AdamW 8-bit |
| Mixed precision | fp16 (Kaggle T4, no bf16) |
| Loss masking | Completion-only via `DataCollatorForCompletionOnlyLM` |
| Eval cadence | every 100 steps; `load_best_model_at_end=True` |
| Train wall time | ~58 min on Kaggle T4 (single GPU) |

Train loss 1.37 → 0.011 over 849 steps. Eval loss 0.0325 (step 100) → 0.0115
(step 600) → continued falling through epoch 3. No overfitting observed; the
best checkpoint was loaded at end automatically.

## Data (Week 1 corpus)

| Source | Train | Val | Test | Notes |
|---|---|---|---|---|
| `handcrafted_seed` | 10 | 0 | 0 | Day 1 dense first-person anchors |
| `hiner` (subsampled) | 1,600 | 200 | 200 | Real-Hindi distributional signal, noisy |
| `synthetic_dense` | 640 | 80 | 80 | Day 3–4 first-person citizen profiles |
| `hardcases` | 20 | 10 | 10 | Day 5 stress-test categories |
| **Total** | **2,270** | **290** | **290** | |

Splits: `random.seed(42)`, deterministic. See [`data_prep/README.md`](../data_prep/README.md) for source-by-source methodology.

## Per-source results

| Source | n | Parse | Schema | Field acc | Gold-NN field acc |
|---|---:|---:|---:|---:|---:|
| `synthetic_dense` | 80 | 100.0% | 100.0% | 98.7% | **98.3%** |
| `hardcases` | 10 | 100.0% | 100.0% | 95.5% | 93.4% |
| `hiner` | 200 | 100.0% | 100.0% | 98.0% | 80.8% |

`synthetic_dense` is the actual target distribution (dense first-person citizen
profiles). 98.2% gold-NN field accuracy on this slice is the metric that matters
for the form-filling use case.

`hiner` gold-NN field accuracy is artificially low because gold labels are
themselves noisy (party names tagged as PER, multi-word locations truncated,
generic nouns mis-tagged). The model often produces a *more reasonable* answer
than the gold — exact-match counts these as wrong.

`hardcases` is the smallest slice (n=10); 1–2 stumbles drop the rate visibly,
but the categories are deliberately adversarial (disfluency, negation, mixed
scripts, implicit references).

## Per-field results

Sorted by gold-NN accuracy (descending):

| Field | Overall | Gold-NN | n (gold-NN) |
|---|---:|---:|---:|
| `marital_status` | 100.0% | **100.0%** | 80 |
| `father_or_husband_name` | 100.0% | **100.0%** | 59 |
| `number_of_dependents` | 99.3% | **100.0%** | 3 |
| `pincode` | 100.0% | **100.0%** | 10 |
| `caste_category` | 100.0% | **100.0%** | 78 |
| `religion` | 100.0% | **100.0%** | 80 |
| `has_aadhaar` | 100.0% | **100.0%** | 81 |
| `has_pan` | 100.0% | **100.0%** | 9 |
| `has_voter_id` | 100.0% | **100.0%** | 9 |
| `has_ration_card` | 100.0% | **100.0%** | 26 |
| `has_bank_account` | 100.0% | **100.0%** | 51 |
| `bank_name` | 100.0% | **100.0%** | 25 |
| `age` | 99.7% | 98.9% | 90 |
| `gender` | 99.7% | 98.9% | 90 |
| `state` | 99.0% | 97.8% | 90 |
| `village_or_town` | 99.0% | 95.1% | 41 |
| `monthly_income_inr` | 98.6% | 94.3% | 70 |
| `full_name` | 88.6% | 88.6% | 290 |
| `occupation` | 94.8% | 86.0% | 86 |
| `district` | 84.1% | 82.4% | 250 |

**Notable wins:**

- **All Literal-typed fields at 100% gold-NN**: the model perfectly canonicalizes
  free Hindi text to closed enum values (अनुसूचित जाति → `sc`, मुस्लिम → `इस्लाम`,
  विधवा → `widowed`, "रहती हूं" → `female`).
- **`bank_name` at 100% (25/25)**: the conditional-extraction rule worked
  perfectly. Model emits the bank name iff the speaker named it; emits `null`
  when only the existence of an account is mentioned. This is the field we
  worked hardest to calibrate during Week 1.
- **`father_or_husband_name` at 100% (59/59)**: the implicit-vs-explicit
  family-name distinction held up across the test set.
- **`age` at 98.9%**: Devanagari-text → integer conversion learned cleanly
  (चौवालीस → 44, इकहत्तर → 71, बावन → 52, etc.).

**Weak fields (and why):**

- **`district` 82.4%, `full_name` 88.6%**: these are the two fields HiNER labels.
  HiNER's annotation noise (party names mistagged as PER, multi-word locations
  truncated to fragments) propagates to model behavior on similar inputs. The
  stoplist-based filter caught the worst cases but residual noise remains.
- **`occupation` 86.0%**: open-text field with no canonical form. Predictions
  like "स्टेशनरी दुकानदार" vs gold "दुकानदार" — both correct, but strict
  exact-match marks the model wrong. Real semantic accuracy here is higher.

## Known limitations

1. **Strict exact-match underreports**. Predictions semantically equivalent to
   gold (canonical spelling variants like "तरणतारन" / "तरनतारन"; more-specific
   occupations) score as wrong. A normalized or semantic-similarity metric would
   raise the field accuracy number meaningfully without changing the underlying
   capability.
2. **HiNER noise ceiling**. Without cleaner labels for `full_name` and `district`,
   per-field accuracy on HiNER-source entries can't exceed the rate at which
   model and gold *agree* about what counts as a PER/LOC. Re-labeling HiNER
   manually is the only fix; deferred.
3. **Generation over-runs**. The model occasionally generates trailing JSON
   duplicates or Hindi narrative after the closing `}`. `JsonCompleteStop` in
   `evaluate.py` and `json.JSONDecoder().raw_decode()` in parsing both
   transparently handle this, but the model is "wasting" generation tokens. A
   stronger EOS signal during training would help.
4. **No deployment scaffolding yet**. The adapter exists; the inference
   service / API wrapper does not.

## Reproducing

```python
# Kaggle T4 x1 notebook (or T4 x2 with CUDA_VISIBLE_DEVICES=0)
!git clone --depth 1 https://github.com/subidhkhanal/hindi-form-agent.git /kaggle/working/repo
!pip install -q -r /kaggle/working/repo/training/requriment.txt

# Train (~60 min)
!cd /kaggle/working/repo && CUDA_VISIBLE_DEVICES=0 python training/smoke_train.py \
    --num-train-epochs 3 --eval-steps 100 --save-total-limit 2 \
    --output-dir /kaggle/working/lora_v1

# Evaluate (~10 min with JsonCompleteStop)
!cd /kaggle/working/repo && CUDA_VISIBLE_DEVICES=0 python training/evaluate.py \
    --adapter /kaggle/working/lora_v1 \
    --output-json /kaggle/working/eval_v1.json
```

Full raw report is at [`data/eval_v1.json`](../data/eval_v1.json).

## Follow-up ideas (not committed)

- Add a normalized field-comparison metric (whitespace-stripped, punctuation-stripped) and report both strict and normalized numbers.
- Iterate on `data_prep/ner_stoplist.py` to catch more HiNER mistags.
- Train a v2 with cleaner `full_name` filtering (e.g., require an honorific or first-person verb context).
- Build the app-side inference wrapper (Week 3).
- Push `lora_v1` to HuggingFace Hub under a fork for shareability.
