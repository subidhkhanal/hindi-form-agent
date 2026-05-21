"""Smoke training: QLoRA fine-tune Sarvam-1 for ~100 steps on a Kaggle T4.

Validates the end-to-end training plumbing — 4-bit base load, LoRA attach,
prompt-only loss masking, save adapter, sample inference.
NOT a real training run. Too few steps, batch size 2.

Usage on Kaggle:
  python training/smoke_train.py --max-steps 100 --output-dir /kaggle/working/lora_smoke
  python training/smoke_train.py --inference-only --adapter /kaggle/working/lora_smoke
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Repo-root on sys.path so `from training.X` and `from schemas.X` both resolve
# when this file is invoked as a script (python training/smoke_train.py ...).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training.prompt_format import (  # noqa: E402
    OUTPUT_DELIMITER,
    format_for_inference,
    format_for_training,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-id", default="sarvamai/sarvam-1")
    p.add_argument("--train-jsonl", default="data/train_v1.jsonl")
    p.add_argument("--val-jsonl", default="data/val_v1.jsonl")
    p.add_argument("--output-dir", default="/kaggle/working/lora_smoke")
    p.add_argument("--max-steps", type=int, default=100)
    p.add_argument("--per-device-batch", type=int, default=2)
    p.add_argument("--grad-accum", type=int, default=4)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-seq-len", type=int, default=1024)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--inference-only", action="store_true")
    p.add_argument("--adapter", default=None,
                   help="Adapter path for --inference-only mode")
    p.add_argument("--n-inference-samples", type=int, default=3)
    p.add_argument("--max-new-tokens", type=int, default=512)
    return p.parse_args()


def load_jsonl(path: str) -> list[dict]:
    entries: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def run_inference(args: argparse.Namespace) -> None:
    """Load 4-bit base + adapter, generate N completions, validate JSON."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from schemas.citizen_profile import CitizenProfile

    if not args.adapter:
        sys.exit("ERROR: --inference-only requires --adapter <path>")

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        args.model_id, quantization_config=bnb, device_map={"": 0},
    )
    model = PeftModel.from_pretrained(base, args.adapter)
    model.eval()

    samples = load_jsonl(args.val_jsonl)[: args.n_inference_samples]

    parse_ok = 0
    validate_ok = 0
    for i, row in enumerate(samples, start=1):
        prompt = format_for_inference(row["input_text"])
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
            )
        gen_ids = out[0][inputs["input_ids"].shape[1]:]
        gen_text = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

        print(f"\n===== Sample {i} =====")
        print(f"--- input_text ---\n{row['input_text']}")
        print(f"\n--- predicted ---\n{gen_text}")
        print(f"\n--- gold ---\n{json.dumps(row['output_json'], ensure_ascii=False)}")

        # raw_decode returns the first valid JSON object and ignores trailing data,
        # so duplicate-JSON generations don't cause false "Extra data" failures.
        try:
            predicted_json, _ = json.JSONDecoder().raw_decode(gen_text)
            parse_ok += 1
            try:
                CitizenProfile.model_validate(predicted_json)
                validate_ok += 1
                print("[parse OK, schema OK]")
            except Exception as e:
                print(f"[parse OK, schema FAIL: {e}]")
        except json.JSONDecodeError as e:
            print(f"[parse FAIL: {e}]")

    n = len(samples)
    print(f"\nSummary: parse {parse_ok}/{n}, schema {validate_ok}/{n}")


def run_training(args: argparse.Namespace) -> None:
    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from trl import DataCollatorForCompletionOnlyLM, SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(args.model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"  # required for training (Llama default is "left")

    # T4 = Turing → fp16. bf16 would crash here.
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    # Pin to a single GPU — device_map="auto" shards across all visible GPUs on Kaggle
    # T4 x2, which breaks the loss reduction step (tensors on cuda:0 and cuda:1).
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id, quantization_config=bnb, device_map={"": 0},
    )
    model = prepare_model_for_kbit_training(model)

    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    # Read JSONL manually rather than via load_dataset("json", ...) — the latter uses
    # PyArrow which infers a single schema across all rows, and our train_v1.jsonl mixes
    # 4 sources whose metadata fields have inconsistent types (e.g. metadata.slot is int
    # in synthetic batches but str elsewhere). We only need `input_text` + `output_json`
    # for training, so drop everything else.
    def jsonl_to_text_dataset(path: str) -> Dataset:
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                # Append EOS so the model learns to stop at the end of the JSON.
                # Without this, generation keeps emitting more JSON objects until
                # max_new_tokens is reached, breaking json.loads with "Extra data".
                text = format_for_training(entry["input_text"], entry["output_json"])
                text += tokenizer.eos_token
                rows.append({"text": text})
        return Dataset.from_list(rows)

    train_ds = jsonl_to_text_dataset(args.train_jsonl)
    val_ds = jsonl_to_text_dataset(args.val_jsonl)

    # Mask the Hindi prompt — only the JSON contributes to loss.
    response_template = f"\n{OUTPUT_DELIMITER}\n"
    collator = DataCollatorForCompletionOnlyLM(response_template, tokenizer=tokenizer)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        max_steps=args.max_steps,
        per_device_train_batch_size=args.per_device_batch,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        logging_steps=10,
        save_steps=args.max_steps,
        eval_strategy="no",
        fp16=True,
        optim="paged_adamw_8bit",
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        dataset_text_field="text",
        max_seq_length=args.max_seq_len,
        data_collator=collator,
        tokenizer=tokenizer,
    )
    trainer.train()
    trainer.save_model(args.output_dir)
    print(f"Saved LoRA adapter to {args.output_dir}")


def main() -> None:
    args = parse_args()
    if args.inference_only:
        run_inference(args)
    else:
        run_training(args)


if __name__ == "__main__":
    main()
