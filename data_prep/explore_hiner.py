"""One-time exploration script for HiNER. Run, read output, then move on."""

from collections import Counter
from datasets import load_dataset


def main() -> None:
    ds = load_dataset("cfilt/HiNER-collapsed", trust_remote_code=True)

    print("=" * 60)
    print("HiNER-collapsed structure")
    print("=" * 60)
    print(f"Splits available: {list(ds.keys())}")
    for split, data in ds.items():
        print(f"  {split}: {len(data)} examples")
    print()

    # Inspect first 3 examples to understand structure
    train = ds["train"]
    print("Column names:", train.column_names)
    print("Features:", train.features)
    print()

    # Get the label names
    if hasattr(train.features.get("ner_tags"), "feature"):
        label_names = train.features["ner_tags"].feature.names
        print(f"NER tag labels ({len(label_names)}):")
        for i, name in enumerate(label_names):
            print(f"  {i}: {name}")
    print()

    # Count tag distribution
    tag_counts: Counter = Counter()
    for ex in train:
        for tag_id in ex["ner_tags"]:
            tag_counts[label_names[tag_id]] += 1
    print("Tag distribution (top 15):")
    for tag, cnt in tag_counts.most_common(15):
        print(f"  {tag:20s}  {cnt:>8,}")
    print()

    # Show 3 example sentences with their entities
    print("=" * 60)
    print("Sample sentences with entity tagging")
    print("=" * 60)
    for i in range(3):
        ex = train[i]
        tokens = ex["tokens"]
        tags = [label_names[t] for t in ex["ner_tags"]]
        print(f"\nExample {i+1}:")
        print(f"  Sentence: {' '.join(tokens)}")
        print(f"  Tokens:   {tokens}")
        print(f"  Tags:     {tags}")


if __name__ == "__main__":
    main()
