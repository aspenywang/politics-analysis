#!/usr/bin/env python3
# freq_analysis.py ── compute and print top-N frequent Chinese and non‑Chinese tokens

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Regex to detect any CJK Unified Ideograph (common Chinese range)
CHINESE_CHAR_RE = re.compile(r'[\u4e00-\u9fff]')

def is_chinese_token(tok: str) -> bool:
    return bool(CHINESE_CHAR_RE.search(tok))

def main():
    parser = argparse.ArgumentParser(
        description="Load processed posts JSONL and output top-N Chinese and non‑Chinese tokens."
    )
    parser.add_argument(
        '--input', '-i',
        default='processed_posts.jsonl',
        help="Input JSONL file (default: processed_posts.jsonl)"
    )
    parser.add_argument(
        '--top', '-t', type=int, default=1000,
        help="Number of top tokens to display in each list (default: 50)"
    )
    args = parser.parse_args()

    infile = Path(args.input)
    if not infile.exists():
        print(f"Error: file not found: {infile}", file=sys.stderr)
        sys.exit(1)

    chinese_counter = Counter()
    non_chinese_counter = Counter()

    # Read JSONL line by line
    with infile.open('r', encoding='utf-8') as fin:
        for lineno, raw in enumerate(fin, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Warning: skipping invalid JSON on line {lineno}: {e}", file=sys.stderr)
                continue

            # gather all tokens
            tokens = []
            for seg in post.get('tokenized_segments', []):
                tokens.extend(tok for tok in seg if tok.strip() and  len(tok) >=2)
            for com in post.get('tokenized_comments', {}).values():
                tokens.extend(tok for tok in com if tok.strip() and  len(tok) >=2)

            # split into Chinese vs non‑Chinese
            for tok in tokens:
                if is_chinese_token(tok):
                    chinese_counter[tok] += 1
                else:
                    non_chinese_counter[tok] += 1

    # Print top Chinese tokens
    print(f"\nTop {args.top} Chinese tokens:")
    print(f"{'Token':<10}Count")
    print(f"{'-'*10} {'-'*5}")
    for tok, cnt in chinese_counter.most_common(args.top):
        print(f"{tok:<10}{cnt}")

    # Print top non‑Chinese tokens
    print(f"\nTop {args.top} non‑Chinese tokens:")
    print(f"{'Token':<15}Count")
    print(f"{'-'*15} {'-'*5}")
    for tok, cnt in non_chinese_counter.most_common(args.top):
        print(f"{tok:<15}{cnt}")

if __name__ == '__main__':
    main()
