#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import random
import csv
from pathlib import Path

INPUT = Path("../ckip-segmentation/ptt_cleaned.jsonl")
OUTPUT = Path("comments_annotation.csv")
SAMPLE_COMMENT_COUNT = 2000

records = [json.loads(line) for line in INPUT.read_text(encoding="utf8").splitlines()]

all_comments = []
for rec in records:
    post_id = rec.get("url","").split("/")[-1].replace(".html","")
    for user, text in rec.get("combined_comments", {}).items():
        all_comments.append((post_id, user, text))

sampled = random.sample(all_comments, k=min(SAMPLE_COMMENT_COUNT, len(all_comments)))

with OUTPUT.open("w", newline="", encoding="utf8") as f:
    writer = csv.writer(f)
    writer.writerow(["post_id","user","comment_text","label"])
    for post_id, user, text in sampled:
        writer.writerow([post_id, user, text, ""])

print(f"comments annotated: {OUTPUT} （ {len(sampled)} comments）")
