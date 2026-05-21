"""Evaluate a trained LoRA adapter on the held-out test set.

Computes:
- Parse rate (predicted JSON parses cleanly via raw_decode)
- Schema rate (parsed JSON validates against CitizenProfile)
- Field-level exact-match accuracy (20 fields × N entries)
- Per-source breakdown (handcrafted_seed / hiner / synthetic_dense / hardcases)
- Per-field accuracy, with separate stats for gold-non-null entries

Field comparison is STRICT exact match. The model can predict
"स्टेशनरी दुकानदार" when gold is "दुकानदार" — both reasonable, but
exact-match marks this wrong. So the field-accuracy number here is a
lower bound; semantic accuracy is higher.

Usage on Kaggle:
  python training/evaluate.py --adapter /kaggle/working/lora_v1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from training.prompt_format import format_for_inference  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--model-id", default="sarvamai/sarvam-1")
    p.add_argument("--adapter", required=True, help="Path to LoRA adapter directory")
    p.add_argument("--test-jsonl", default="data/test_v1.jsonl")
    p.add_argument("--output-json", default="/kaggle/working/eval_v1.json")
    p.add_argument("--max-new-tokens", type=int, default=512)
    p.add_argument("--limit", type=int, default=0,
                   help="If >0, evaluate only first N entries (sanity-check the eval).")
    p.add_argument("--print-every", type=int, default=10)
    return p.parse_args()


def load_jsonl(path: str) -> list[dict]:
    entries: list[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def main() -> None:
    args = parse_args()

    # Deferred heavy imports so --help is fast
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    from schemas.citizen_profile import CitizenProfile

    schema_fields = list(CitizenProfile.model_fields.keys())

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

    entries = load_jsonl(args.test_jsonl)
    if args.limit > 0:
        entries = entries[: args.limit]
    n = len(entries)
    print(f"Evaluating {n} entries from {args.test_jsonl}...")

    # Aggregators
    n_parse_ok = 0
    n_schema_ok = 0
    n_field_correct = 0
    n_field_total = 0

    by_source: dict[str, dict] = defaultdict(
        lambda: {"n": 0, "parse_ok": 0, "schema_ok": 0,
                 "field_correct": 0, "field_total": 0,
                 "gold_nn_correct": 0, "gold_nn_total": 0}
    )
    by_field: dict[str, dict] = defaultdict(
        lambda: {"correct": 0, "total": 0,
                 "gold_nn_correct": 0, "gold_nn_total": 0}
    )

    for i, entry in enumerate(entries):
        if i % args.print_every == 0:
            print(f"  [{i}/{n}]")

        source = entry.get("metadata", {}).get("source", "unknown")
        by_source[source]["n"] += 1

        prompt = format_for_inference(entry["input_text"])
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=args.max_new_tokens,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        gen_ids = out[0][inputs["input_ids"].shape[1]:]
        gen_text = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()

        # Parse
        predicted = None
        try:
            predicted, _ = json.JSONDecoder().raw_decode(gen_text)
            n_parse_ok += 1
            by_source[source]["parse_ok"] += 1
        except json.JSONDecodeError:
            pass

        # Schema validate
        if isinstance(predicted, dict):
            try:
                CitizenProfile.model_validate(predicted)
                n_schema_ok += 1
                by_source[source]["schema_ok"] += 1
            except Exception:
                pass

        # Field-level accuracy
        gold = entry["output_json"]
        pred_for_compare = predicted if isinstance(predicted, dict) else {}

        for field in schema_fields:
            gold_value = gold.get(field)
            pred_value = pred_for_compare.get(field)
            is_correct = gold_value == pred_value
            gold_nn = gold_value is not None

            n_field_total += 1
            by_source[source]["field_total"] += 1
            by_field[field]["total"] += 1
            if gold_nn:
                by_field[field]["gold_nn_total"] += 1
                by_source[source]["gold_nn_total"] += 1

            if is_correct:
                n_field_correct += 1
                by_source[source]["field_correct"] += 1
                by_field[field]["correct"] += 1
                if gold_nn:
                    by_field[field]["gold_nn_correct"] += 1
                    by_source[source]["gold_nn_correct"] += 1

    # Build report
    def safe_div(a: int, b: int) -> float:
        return a / b if b else 0.0

    report = {
        "n_entries": n,
        "adapter": args.adapter,
        "test_jsonl": args.test_jsonl,
        "overall": {
            "parse_ok": n_parse_ok,
            "parse_rate": safe_div(n_parse_ok, n),
            "schema_ok": n_schema_ok,
            "schema_rate": safe_div(n_schema_ok, n),
            "field_correct": n_field_correct,
            "field_total": n_field_total,
            "field_accuracy": safe_div(n_field_correct, n_field_total),
        },
        "by_source": {},
        "by_field": {},
    }
    for source, s in sorted(by_source.items()):
        report["by_source"][source] = {
            "n": s["n"],
            "parse_rate": safe_div(s["parse_ok"], s["n"]),
            "schema_rate": safe_div(s["schema_ok"], s["n"]),
            "field_accuracy": safe_div(s["field_correct"], s["field_total"]),
            "gold_nonnull_field_accuracy": (
                safe_div(s["gold_nn_correct"], s["gold_nn_total"])
                if s["gold_nn_total"] else None
            ),
            "n_gold_nonnull_fields": s["gold_nn_total"],
        }
    for field, s in by_field.items():
        report["by_field"][field] = {
            "accuracy": safe_div(s["correct"], s["total"]),
            "gold_nonnull_accuracy": (
                safe_div(s["gold_nn_correct"], s["gold_nn_total"])
                if s["gold_nn_total"] else None
            ),
            "n_gold_nonnull": s["gold_nn_total"],
        }

    # Write JSON report
    Path(args.output_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Pretty-print to stdout
    print()
    print("=" * 70)
    print(f"EVALUATION REPORT (n={n})")
    print("=" * 70)
    print()
    print("Overall:")
    print(f"  Parse rate:     {n_parse_ok:>3}/{n} ({100 * safe_div(n_parse_ok, n):.1f}%)")
    print(f"  Schema rate:    {n_schema_ok:>3}/{n} ({100 * safe_div(n_schema_ok, n):.1f}%)")
    print(f"  Field accuracy: {n_field_correct}/{n_field_total} "
          f"({100 * safe_div(n_field_correct, n_field_total):.1f}%)")
    print()
    print("By source (gold-NN = field accuracy on gold-non-null fields only):")
    print(f"  {'source':<20} {'n':>5} {'parse':>8} {'schema':>8} "
          f"{'field':>8} {'gold-NN':>8}")
    for source, s in report["by_source"].items():
        nn = s["gold_nonnull_field_accuracy"]
        nn_str = f"{100*nn:>7.1f}%" if nn is not None else "    n/a"
        print(f"  {source:<20} {s['n']:>5} "
              f"{100*s['parse_rate']:>7.1f}% "
              f"{100*s['schema_rate']:>7.1f}% "
              f"{100*s['field_accuracy']:>7.1f}% "
              f"{nn_str}")
    print()
    print("By field (sorted by gold-non-null accuracy, descending):")
    print(f"  {'field':<28} {'overall':>10} {'gold-NN':>10} {'n-gold-NN':>10}")
    sorted_fields = sorted(
        report["by_field"].items(),
        key=lambda kv: (kv[1]["gold_nonnull_accuracy"] is None,
                        -(kv[1]["gold_nonnull_accuracy"] or 0))
    )
    for field, s in sorted_fields:
        if s["gold_nonnull_accuracy"] is None:
            nn_str = "n/a"
        else:
            nn_str = f"{100 * s['gold_nonnull_accuracy']:.1f}%"
        print(f"  {field:<28} {100 * s['accuracy']:>9.1f}% "
              f"{nn_str:>10} {s['n_gold_nonnull']:>10}")
    print()
    print(f"Saved report to {args.output_json}")
    print()
    print("Note: field accuracy is STRICT exact-match. Predictions like")
    print("'स्टेशनरी दुकानदार' vs gold 'दुकानदार' count as wrong even though")
    print("both are reasonable. Real semantic accuracy is higher than the number.")


if __name__ == "__main__":
    main()
