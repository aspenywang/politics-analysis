import json
import random
import csv
from pathlib import Path

# Input JSONL (with your filtered_tokens field)
INPUT = Path("processed_posts_filtered.jsonl")
# Output CSV for manual labeling
ANNOTATION_CSV = Path("annotation_template.csv")
# Number of samples to pull for annotation
SAMPLE_SIZE = 300

# 1. Load all records
with INPUT.open(encoding="utf8") as f:
    records = [json.loads(line) for line in f]

# 2. Randomly sample N records
sampled = random.sample(records, k=min(SAMPLE_SIZE, len(records)))

# 3. Write out CSV with empty label column
with ANNOTATION_CSV.open("w", newline="", encoding="utf8") as f:
    writer = csv.writer(f)
    # Header: post_id, text, label
    writer.writerow(["post_id", "text", "label"])
    for rec in sampled:
        # Use your post identifier (e.g. URL tail or a dedicated post_id field)
        post_id = rec.get("url", "").split("/")[-1].replace(".html","")
        # Join cleaned tokens into a single string
        text = " ".join(rec.get("filtered_tokens", []))
        writer.writerow([post_id, text, ""])

print(f"✅ Annotation template generated: {ANNOTATION_CSV} ({len(sampled)} rows)")
