import json
import re
from pathlib import Path

# 1. Load stopwords from file
stopwords = set(
    Path("../stopwords.txt").read_text(encoding="utf8").split()
)

# 2. Helper to strip URLs
def strip_urls(text: str) -> str:
    return re.sub(r"https?://\S+|www\.\S+", "", text)

# 3. Merge list of strings, remove signature lines & collapse whitespace
def merge_and_clean(contents: list[str]) -> str:
    text = "\n".join(contents)
    text = re.sub(r"(?im)^Sent\s+from.*$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# 4. Read raw posts JSON
data_path = Path("../../PostsCrawler/output/Gossiping.json")
raw_records = json.loads(data_path.read_text(encoding="utf8"))

# 5. Process each post: clean segments & combine comments
processed = []
sig_pattern = re.compile(r"(?im)^Sent\s+from.*$")
for post in raw_records:
    # Clean content segments
    raw_segments = post.get('content', []) or []
    segments = []
    for seg in raw_segments:
        seg = seg.strip()
        if not seg or sig_pattern.match(seg):
            continue
        seg = strip_urls(seg)
        # remove any signature remnants
        seg = sig_pattern.sub("", seg).strip()
        if seg:
            segments.append(seg)

    # Combine comments by user and clean
    combined = {}
    for com in post.get('comments', []) or []:
        user = com.get('user') or com.get('author')
        text = com.get('content', '').strip()
        if not user or not text or sig_pattern.match(text):
            continue
        text = strip_urls(text)
        text = sig_pattern.sub("", text).strip()
        if text:
            combined.setdefault(user, []).append(text)
    combined_comments = {u: merge_and_clean(txts) for u, txts in combined.items()}

    # Build output record
    processed.append({
        'board': post.get('board'),
        'title': post.get('title'),
        'author': post.get('author'),
        'date': post.get('date'),
        'url': post.get('url'),
        'segments': segments,
        'combined_comments': combined_comments,
        'score': post.get('score'),
        'ip': post.get('ip'),
        'tokenized_segments': [],    # placeholder
        'tokenized_comments': {}     # placeholder
    })

# 6. Write intermediate file before CKIP
processed_path = Path("ptt_processed.jsonl")
with processed_path.open("w", encoding="utf8") as fp:
    for rec in processed:
        fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(f"✅ Preprocessing complete. Output: {processed_path}")

