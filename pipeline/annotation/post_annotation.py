#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import random
import csv
from pathlib import Path

# 來源 JSONL，裡面每一行都有 tokenized_segments: List[List[str]]
INPUT = Path("../ckip-segmentation/ptt_cleaned.jsonl")
# 標注模板輸出
ANNOTATION_CSV = Path("annotation_template.csv")
# 抽樣數量
SAMPLE_SIZE = 300

# 1. 讀入所有記錄
with INPUT.open(encoding="utf8") as f:
    records = [json.loads(line) for line in f]

# 2. 隨機抽樣，若記錄少於 SAMPLE_SIZE 則全取
sampled = random.sample(records, k=min(SAMPLE_SIZE, len(records)))

# 3. 寫出 CSV，留空 label 欄讓你手動標注
with ANNOTATION_CSV.open("w", newline="", encoding="utf8") as f:
    writer = csv.writer(f)
    # 欄位：post_id, board, title, text, label
    writer.writerow(["post_id", "board", "title", "text", "label"])
    for rec in sampled:
        # 取 post_id：用 URL 最後一段去掉 .html
        url = rec.get("url", "")
        post_id = url.split("/")[-1].replace(".html", "")

        # 原版資料有 board 與 title
        board = rec.get("board", "")
        title = rec.get("title", "")

        # tokenized_segments 是 List[List[str]]，通常只要第一段的 tokens
        segs = rec.get("tokenized_segments", [])
        tokens = segs[0] if segs and isinstance(segs[0], list) else []

        # 把 tokens 用空白串成一段文字
        text = " ".join(tokens)

        # 寫一行，label 欄空著
        writer.writerow([post_id, board, title, text, ""])

print(f"✅ Annotation template generated: {ANNOTATION_CSV} ({len(sampled)} rows)")
