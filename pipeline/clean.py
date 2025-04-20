#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json, re
from pathlib import Path

stopwords = set(
    Path("stopwords.txt").read_text(encoding="utf8").splitlines()
)

def filter_tokens(tokens: list[str]) -> list[str]:
    out = []
    for t in tokens:
            if t not in stopwords:
                out.append(t)
    return out

input_path  = Path("processed_posts_ckip.jsonl")
output_path = Path("processed_posts_filtered.jsonl")

with input_path.open(encoding="utf8") as fin, \
        output_path.open("w", encoding="utf8") as fout:
    for line in fin:
        rec = json.loads(line)
        seg_lists = rec.get("tokenized_segments", [])
        flat = seg_lists[0] if seg_lists else []
        rec["filtered_tokens"] = filter_tokens(flat)

        filtered_coms = {}
        for user, toks in rec.get("tokenized_comments", {}).items():
            filtered_coms[user] = filter_tokens(toks)
        rec["filtered_comments"] = filtered_coms

        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"filtered results：{output_path}")
