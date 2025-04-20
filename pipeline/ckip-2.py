#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from ckip_transformers.nlp import CkipWordSegmenter

# 1. Load stopwords from file
stopwords = set(
    Path("stopwords.txt").read_text(encoding="utf8").split()
)

# 2. Define helper to strip URLs
def strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+|www\.\S+", "", text)

# 3. Define cleaning function: remove signature lines & collapse whitespace
def merge_and_clean(contents: list[str]) -> str:
    text = "\n".join(contents)
    # Remove lines containing "Sent from my" (case-insensitive)
    text = re.sub(r"(?im)^.*sent\s+from\s+my.*$", "", text)
    # Collapse multiple whitespace into a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# 4. Define token filter: keep tokens of ≥2 Chinese chars and not in stopwords
def filter_tokens(tokens: list[str]) -> list[str]:
    return [t for t in tokens if re.fullmatch(r"[\u4e00-\u9fff]{2,}", t) and t not in stopwords]

# 5. Read input JSON (a list of records)
data_path = Path("../PostsCrawler/output/Gossiping.json")
records = json.loads(data_path.read_text(encoding="utf8"))

# 6. Initialize CKIP segmenter
ws_driver = CkipWordSegmenter(model="bert-base", device=0)

# 7. Process a single post: clean segments, combine and clean comments, segment both
def process_post(post: dict) -> dict:
    # 7.1 Process content segments
    raw_segments = post.get('content', []) or []
    segments = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        seg = strip_urls(seg)
        if seg:
            segments.append(seg)

    # 7.2 Combine comments by same user and clean
    combined = {}
    for com in post.get('comments', []) or []:
        user = com.get('user') or com.get('author')
        text = com.get('content', '').strip()
        if not user or not text:
            continue
        text = strip_urls(text)
        if not text:
            continue
        combined.setdefault(user, []).append(text)
    combined_comments = {u: ' '.join(txts) for u, txts in combined.items()}

    # 7.3 Segment content and comments
    tokenized_segments = []
    if segments:
        tokenized_segments = ws_driver(segments)
        # filter each segment's tokens
        tokenized_segments = [filter_tokens(ts) for ts in tokenized_segments]

    tokenized_comments = {}
    if combined_comments:
        users = list(combined_comments.keys())
        texts = [combined_comments[u] for u in users]
        ws_results = ws_driver(texts)
        tokenized_comments = {u: filter_tokens(ts) for u, ts in zip(users, ws_results)}

    # 7.4 Build processed record
    return {
        'board': post.get('board'),
        'title': post.get('title'),
        'author': post.get('author'),
        'date': post.get('date'),
        'url': post.get('url'),
        'segments': segments,
        'tokenized_segments': tokenized_segments,
        'combined_comments': combined_comments,
        'tokenized_comments': tokenized_comments,
        'score': post.get('score'),
        'ip': post.get('ip'),
    }

# 8. Process all records
processed = [process_post(rec) for rec in records]

# 9. Write out to JSONL
out_path = Path("ptt_cleaned.jsonl")
with out_path.open("w", encoding="utf8") as fp:
    for rec in processed:
        fp.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Generated {len(processed)} processed records: {out_path}")
