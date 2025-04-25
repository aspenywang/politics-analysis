
import json
from pathlib import Path
from ckip_transformers.nlp import CkipWordSegmenter
import re

# Load stopwords for filtering
stopwords = set(
    Path("../stopwords.txt").read_text(encoding="utf8").split()
)

def filter_tokens(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in stopwords]

# Read preprocessed JSONL
processed_path = Path("../preprocess/ptt_processed.jsonl")
processed = [json.loads(line) for line in processed_path.read_text(encoding="utf8").splitlines()]

# Initialize CKIP segmenter
ws_driver = CkipWordSegmenter(model="bert-base", device=0)

# Perform segmentation
for rec in processed:
    if rec['segments']:
        ws_out = ws_driver(rec['segments'])
        rec['tokenized_segments'] = [filter_tokens(ts) for ts in ws_out]
    if rec['combined_comments']:
        users = list(rec['combined_comments'].keys())
        texts = [rec['combined_comments'][u] for u in users]
        ws_out = ws_driver(texts)
        rec['tokenized_comments'] = {u: filter_tokens(ts) for u, ts in zip(users, ws_out)}

# Write final cleaned JSONL
tidy_path = Path("ptt_cleaned.jsonl")
with tidy_path.open("w", encoding="utf8") as fp:
    for rec in processed:
        fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"✅ CKIP segmentation complete. Output: {tidy_path}")
