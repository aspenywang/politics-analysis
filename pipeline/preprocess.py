#!/usr/bin/env python3
# process_ptt.py ── segment content, combine comments by author, remove URLs, and tokenize

import argparse
import json
import re
from pathlib import Path

import jieba

URL_PATTERN = re.compile(r'https?://\S+')

def strip_urls(text: str) -> str:
    """Remove any http:// or https:// URLs from the text."""
    return URL_PATTERN.sub('', text)

def process_post(post):
    # 1. Segment content: strip whitespace, drop empty, and remove URLs
    raw_segments = post.get('content', []) or []
    segments = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg:
            continue
        seg = strip_urls(seg)
        if seg:
            segments.append(seg)

    # 2. Combine comments by same user, then strip URLs
    combined = {}
    for com in post.get('comments', []) or []:
        user = com.get('user') or com.get('author')
        text = com.get('content', '').strip()
        if not user or not text:
            continue
        # remove URLs here too
        text = strip_urls(text)
        if not text:
            continue
        combined.setdefault(user, []).append(text)

    combined_comments = {
        u: ' '.join(txts)
        for u, txts in combined.items()
    }

    # 3. Tokenize segments and comments
    tokenized_segments = [
        jieba.lcut(seg, cut_all=False)
        for seg in segments
    ]
    tokenized_comments = {
        u: jieba.lcut(text, cut_all=False)
        for u, text in combined_comments.items()
    }

    # build new record
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

def main():
    jieba.load_userdict('./tw_politic_dic.txt')

    parser = argparse.ArgumentParser(
        description="Segment content, combine comments, strip URLs, and tokenize with jieba."
    )
    parser.add_argument(
        '--input', '-i',
        default='../PostsCrawler/output/Gossiping.json',
        help="Input JSON file (array of posts)"
    )
    parser.add_argument(
        '--output', '-o',
        default='processed_posts.jsonl',
        help="Output JSONL file"
    )

    args = parser.parse_args()
    infile  = Path(args.input)
    outfile = Path(args.output)

    data = json.loads(infile.read_text(encoding='utf-8'))
    if not isinstance(data, list):
        parser.error("Input JSON must be an array of post objects")

    # Process each post and write as JSONL
    with outfile.open('w', encoding='utf-8') as fout:
        for post in data:
            processed = process_post(post)
            fout.write(json.dumps(processed, ensure_ascii=False) + '\n')

    print(f"Wrote {len(data)} posts to {outfile}")

if __name__ == '__main__':
    main()
