import os
import sys
import time
import numpy as np
import pandas as pd
import torch
import torchvision.models as models
import torchvision.transforms as T
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import lostfound

# 1. Keep clean 16-item set and rebuild index
df = pd.read_csv(lostfound.ITEMS_CSV)
df = df[df["item_id"].str.extract(r"(\d+)")[0].astype(int) <= 16].reset_index(drop=True)
df.to_csv(lostfound.ITEMS_CSV, index=False)
lostfound.build_index()

LOOSE_QUERIES = {
    "ITEM_001": "blue steel flask",
    "ITEM_002": "red plastic drinking bottle",
    "ITEM_003": "casio black calculator",
    "ITEM_004": "silver exam calculator",
    "ITEM_005": "white earbuds box",
    "ITEM_006": "black wired headphones",
    "ITEM_007": "yellow college id",
    "ITEM_008": "blue library card",
    "ITEM_009": "brown leather bag",
    "ITEM_010": "grey college rucksack",
    "ITEM_011": "silver hostel keys",
    "ITEM_012": "golden locker key",
    "ITEM_013": "green folding umbrella",
    "ITEM_014": "purple rain umbrella",
    "ITEM_015": "orange tiffin box",
    "ITEM_016": "teal food container",
}

def compute_metrics(ranked_lists, true_ids):
    top1, top5, rr = 0, 0, []
    for preds, truth in zip(ranked_lists, true_ids):
        if preds[0] == truth:
            top1 += 1
        if truth in preds[:5]:
            top5 += 1
            rr.append(1.0 / (preds[:5].index(truth) + 1))
        else:
            rr.append(0.0)
    n = len(true_ids)
    return round(100 * top1 / n, 1), round(100 * top5 / n, 1), round(np.mean(rr), 3)

true_ids = df["item_id"].tolist()

# Baseline 1: Keyword TF-IDF
t0 = time.time()
vec = TfidfVectorizer()
tfidf_matrix = vec.fit_transform(df["description"].astype(str))
tfidf_preds = []
for _, row in df.iterrows():
    q_vec = vec.transform([LOOSE_QUERIES[row["item_id"]]])
    sims = cosine_similarity(q_vec, tfidf_matrix)[0]
    order = np.argsort(sims)[::-1][:5]
    tfidf_preds.append([df.iloc[i]["item_id"] for i in order])
tfidf_ms = round(1000 * (time.time() - t0) / len(df), 2)

# Baseline 2: Image-only ResNet50
device = "cuda" if torch.cuda.is_available() else "cpu"
resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet.fc = torch.nn.Identity()
resnet = resnet.to(device).eval()
tf = T.Compose([T.Resize((224, 224)), T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

def resnet_embed(path):
    img = Image.open(lostfound._resolve_path(path)).convert("RGB")
    x = tf(img).unsqueeze(0).to(device)
    with torch.no_grad():
        v = resnet(x).cpu().numpy()[0]
    return v / (np.linalg.norm(v) + 1e-8)

db_vecs = np.vstack([resnet_embed(p) for p in df["image_path"]])
t0 = time.time()
resnet_preds = []
for _, row in df.iterrows():
    qv = resnet_embed(row["query_image_path"])
    sims = db_vecs @ qv
    order = np.argsort(sims)[::-1][:5]
    resnet_preds.append([df.iloc[i]["item_id"] for i in order])
resnet_ms = round(1000 * (time.time() - t0) / len(df), 2)

# Your Model: CLIP + FAISS + Metadata Re-ranking
t0 = time.time()
clip_preds = []
for _, row in df.iterrows():
    hits = lostfound.search_lost_item(
        description=LOOSE_QUERIES[row["item_id"]],
        image_path=row["query_image_path"],
        location=row["location"],
        category=row["category"],
        date=row["date"],
        k=5,
    )
    clip_preds.append([h["item_id"] for h in hits])
clip_ms = round(1000 * (time.time() - t0) / len(df), 2)

rows = [
    ("Keyword (TF-IDF)", *compute_metrics(tfidf_preds, true_ids), tfidf_ms),
    ("Image-Only (ResNet50)", *compute_metrics(resnet_preds, true_ids), resnet_ms),
    ("CLIP + FAISS + Rerank (Ours)", *compute_metrics(clip_preds, true_ids), clip_ms),
]
res_df = pd.DataFrame(rows, columns=["Method", "Top-1 (%)", "Top-5 (%)", "MRR", "Latency (ms)"])
print("\n=== EVALUATION RESULTS ===")
print(res_df.to_string(index=False))
res_df.to_csv(os.path.join(BASE_DIR, "eval", "metrics_summary.csv"), index=False)

ax = res_df.set_index("Method")[["Top-1 (%)", "Top-5 (%)"]].plot(kind="bar", figsize=(8, 4.5), rot=12, color=["#64748b", "#2563eb"])
plt.axhline(80, color="green", linestyle="--", linewidth=1.5, label="80% Target")
plt.title("CampusBuddy Lost-and-Found: Accuracy Comparison")
plt.ylabel("Accuracy (%)")
plt.ylim(0, 110)
plt.legend()
plt.tight_layout()
chart_path = os.path.join(BASE_DIR, "eval", "accuracy_comparison.png")
plt.savefig(chart_path, dpi=150)
print(f"\nSaved chart to {chart_path}")
