# Training — Week 2 Day 1 Smoke Run

## What this does

Validates the end-to-end QLoRA fine-tuning plumbing for Sarvam-1 on a Kaggle T4:
4-bit base load, LoRA adapter attach, prompt-only loss masking, save adapter,
sample inference. **Not a real training run** — too few steps (100), batch size 2.
Pass condition: loss goes down, adapter saves, inference produces parseable JSON.

The repo (https://github.com/subidhkhanal/hindi-form-agent) ships the training
data, prompt format, and the training script itself — so the Kaggle notebook is
just 4 cells that clone and run.

## Run on Kaggle (4 cells)

Notebook settings: **GPU T4 x1**, internet ON.

### Cell 1 — clone repo + install deps (~2-3 min)

```python
!git clone --depth 1 https://github.com/subidhkhanal/hindi-form-agent.git /kaggle/working/repo
!pip install -q -r /kaggle/working/repo/training/requriment.txt
```

### Cell 2 — HuggingFace login (only if Sarvam-1 is gated)

Add `HF_TOKEN` to Kaggle Secrets first (Add-ons → Secrets). If `sarvamai/sarvam-1`
loads without auth in Cell 3, skip this cell.

```python
from kaggle_secrets import UserSecretsClient
from huggingface_hub import login
login(token=UserSecretsClient().get_secret("HF_TOKEN"))
```

### Cell 3 — train (~15-25 min)

```python
!cd /kaggle/working/repo && python training/smoke_train.py \
    --max-steps 100 --output-dir /kaggle/working/lora_smoke
```

### Cell 4 — inference smoke (~1 min)

```python
!cd /kaggle/working/repo && python training/smoke_train.py \
    --inference-only --adapter /kaggle/working/lora_smoke --n-inference-samples 3
```

## What to check

- **Cell 3**: loss column logged every 10 steps with a *decreasing* trend
  (start ~3.x, end ~1.x is healthy; any monotonic decrease is enough for a
  smoke). Final line: `Saved LoRA adapter to /kaggle/working/lora_smoke`.
- **Cell 4**: prints 3 `input_text` / `predicted` / `gold` triples and a
  `Summary: parse N/3, schema N/3` line. ≥2/3 on both is the pass bar.
- **Adapter files**: `/kaggle/working/lora_smoke/adapter_config.json` and
  `adapter_model.safetensors` exist (downloadable from the Kaggle output panel).

## If something goes wrong

- **OOM on Cell 3** → lower `--per-device-batch` to 1 and raise `--grad-accum`
  to 8 (effective batch stays 8).
- **bf16 crash** → `smoke_train.py` already forces `fp16=True` for T4 (Turing,
  no bf16). If you somehow see a bf16 error, you're on an unexpected GPU.
- **Tokenizer mismatch / completion-only collator can't find the delimiter** →
  the response template must tokenize the same way standalone as inside a
  full example. Inspect the first batch's labels manually if loss starts at
  exactly `0.0` (means everything was masked) or doesn't decrease at all.
- **Sarvam-1 gated** → add `HF_TOKEN` to Kaggle Secrets and run Cell 2.

## Files

- `prompt_format.py` — `format_for_training`, `format_for_inference`,
  `OUTPUT_DELIMITER` (the Hindi `संरचित JSON:` marker)
- `smoke_train.py` — single CLI script, two modes (training, inference-only)
- `requriment.txt` — version-pinned deps installed by Cell 1
