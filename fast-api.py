# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import BertForSequenceClassification, BertTokenizer
from snownlp import SnowNLP
import geoip2.database

app = FastAPI()

# ——加载模型/资源——
clf_tokenizer = BertTokenizer.from_pretrained("hfl/chinese-bert-wwm")
clf_model     = BertForSequenceClassification.from_pretrained("your-finetuned-model")
ip_reader     = geoip2.database.Reader("GeoLite2-Country.mmdb")

# ——数据模型——
class Post(BaseModel):
    post_id: str
    content: str

class Comments(BaseModel):
    post_id: str
    comments: list[str]

class IPData(BaseModel):
    ips: list[str]
    scores: list[int]

@app.post("/classify/")
def classify(post: Post):
    inputs = clf_tokenizer(post.content, return_tensors="pt", truncation=True)
    logits = clf_model(**inputs).logits
    label_id = int(logits.argmax())
    label_map = {0:"新闻",1:"政治文",2:"废文",3:"其他"}
    # 假设我们同时提取关键词（示例）
    keywords = [w for w in post.content.split() if len(w)>=2][:3]
    return {"post_id": post.post_id, "label": label_map[label_id], "keywords": keywords}

@app.post("/sentiment/")
def sentiment(data: Comments):
    scores = []
    for c in data.comments:
        txt = c.split(":",1)[1]
        s = SnowNLP(txt).sentiments  # [0,1]
        scores.append(+1 if s>0.6 else -1 if s<0.4 else 0)
    summary = {"positive":scores.count(1),"negative":scores.count(-1),"neutral":scores.count(0)}
    return {"post_id": data.post_id, "scores": scores, "summary": summary}

@app.post("/ip-analysis/")
def ip_analysis(data: IPData):
    by_country = {}
    for ip, sc in zip(data.ips, data.scores):
        rec = ip_reader.country(ip)
        cc = rec.country.iso_code or "UNK"
        if cc not in by_country:
            by_country[cc] = {"count":0,"pos":0,"neg":0,"neu":0}
        by_country[cc]["count"] += 1
        key = "pos" if sc>0 else "neg" if sc<0 else "neu"
        by_country[cc][key] += 1
    return {"by_country": by_country}

@app.post("/political-align/")
def political_align(post: Post):
    # 简单词典匹配示例
    green_terms = {"改革","劳工","平权"}
    blue_terms  = {"国防","经济自由","市场"}
    cnt_g = sum(post.content.count(t) for t in green_terms)
    cnt_b = sum(post.content.count(t) for t in blue_terms)
    if cnt_g>cnt_b: stance="偏绿"
    elif cnt_b>cnt_g: stance="偏蓝"
    else: stance="中立"
    evidence = [f"关键词：{t}" for t in (green_terms|blue_terms) if t in post.content]
    return {"post_id": post.post_id, "stance": stance, "evidence": evidence}
