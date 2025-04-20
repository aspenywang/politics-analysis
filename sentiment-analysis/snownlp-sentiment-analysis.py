import json

from snownlp import SnowNLP
import csv

from pipeline.preprocess import process_post

# Suppose you have a list of tokens (or short text snippets) in `tokens`
tokens = json.load(process_post())

# Compute sentiment score for each token/text
# SnowNLP.sentiments ∈ (0,1): closer to 1 ⇒ positive
lexicon = []
for tok in set(tokens):                  # remove duplicates
    s = SnowNLP(tok)
    score = s.sentiments
    # label thresholds: >0.6 positive, <0.4 negative, else neutral
    if score > 0.6:
        label = "positive"
    elif score < 0.4:
        label = "negative"
    else:
        label = "neutral"
    lexicon.append((tok, score, label))

# Write out CSV: token,score,label
with open("sentiment_lexicon.csv","w",encoding="utf-8",newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["token","score","label"])
    writer.writerows(lexicon)
