import os
from datetime import datetime
import numpy as np
import pandas as pd
import torch
import open_clip
import faiss
from PIL import Image

# Locate CampusBuddy/ automatically regardless of current working directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS_CSV = os.path.join(BASE_DIR, "data", "items", "items.csv")
INDEX_FILE = os.path.join(BASE_DIR, "data", "items", "faiss.index")

NOTIFY_THRESHOLD = 0.30  # Configurable score threshold to notify owner

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_MODEL = None
_PREPROCESS = None
_TOKENIZER = None


def _load_clip():
    global _MODEL, _PREPROCESS, _TOKENIZER
    if _MODEL is None:
        _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        _MODEL = _MODEL.to(_DEVICE).eval()
        _TOKENIZER = open_clip.get_tokenizer("ViT-B-32")
    return _MODEL, _PREPROCESS, _TOKENIZER


def _resolve_path(path):
    if path is None:
        return None
    if os.path.exists(path):
        return path
    joined = os.path.join(BASE_DIR, path)
    if os.path.exists(joined):
        return joined
    raise FileNotFoundError(f"Image not found: {path}")


def _normalize(vec):
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec


def embed_image(image_path):
    model, preprocess, _ = _load_clip()
    img = Image.open(_resolve_path(image_path)).convert("RGB")
    tensor = preprocess(img).unsqueeze(0).to(_DEVICE)
    with torch.no_grad():
        feat = model.encode_image(tensor).cpu().numpy()[0].astype("float32")
    return _normalize(feat)


def embed_text(text):
    model, _, tokenizer = _load_clip()
    tokens = tokenizer([text]).to(_DEVICE)
    with torch.no_grad():
        feat = model.encode_text(tokens).cpu().numpy()[0].astype("float32")
    return _normalize(feat)


def embed_combined(description="", image_path=None):
    has_text = bool(description and description.strip())
    has_img = bool(image_path)
    if not has_text and not has_img:
        raise ValueError("Provide at least a description or an image_path.")

    vecs = []
    if has_img:
        vecs.append(embed_image(image_path))
    if has_text:
        vecs.append(embed_text(description.strip()))

    combined = np.mean(vecs, axis=0).astype("float32")
    return _normalize(combined)


def build_index():
    """Reads items.csv, embeds all items with CLIP, and builds a FAISS index."""
    df = pd.read_csv(ITEMS_CSV)
    vectors = []
    for _, row in df.iterrows():
        vec = embed_combined(str(row.get("description", "")), row.get("image_path"))
        vectors.append(vec)

    matrix = np.vstack(vectors).astype("float32")
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    faiss.write_index(index, INDEX_FILE)
    return index, df


def _load_index_and_df():
    df = pd.read_csv(ITEMS_CSV)
    if not os.path.exists(INDEX_FILE):
        return build_index()
    index = faiss.read_index(INDEX_FILE)
    if index.ntotal != len(df):
        return build_index()
    return index, df


def add_found_item(image_path, description, location, date, category="", color="", secret_detail=""):
    """Shared contract: adds a found item, updates items.csv + FAISS, and returns item_id."""
    df = pd.read_csv(ITEMS_CSV) if os.path.exists(ITEMS_CSV) else pd.DataFrame()
    next_num = len(df) + 1
    item_id = f"ITEM_{next_num:03d}"

    new_row = {
        "item_id": item_id,
        "image_path": image_path,
        "query_image_path": image_path,
        "description": description,
        "category": category,
        "color": color,
        "location": location,
        "date": date,
        "secret_detail": secret_detail,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(ITEMS_CSV, index=False)

    vec = embed_combined(description, image_path).reshape(1, -1)
    if os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        index.add(vec)
        faiss.write_index(index, INDEX_FILE)
    else:
        build_index()

    return item_id


def _date_close(d1, d2, max_days=3):
    try:
        dt1 = datetime.strptime(str(d1)[:10], "%Y-%m-%d")
        dt2 = datetime.strptime(str(d2)[:10], "%Y-%m-%d")
        return abs((dt1 - dt2).days) <= max_days
    except Exception:
        return False


def search_lost_item(description, image_path=None, k=5, category=None, location=None, date=None, threshold=NOTIFY_THRESHOLD):
    """Shared contract: searches by text, image, or both, with metadata re-ranking."""
    index, df = _load_index_and_df()
    query_vec = embed_combined(description, image_path).reshape(1, -1)

    fetch_k = min(len(df), max(k * 3, 10))
    scores, indices = index.search(query_vec, fetch_k)

    results = []
    for clip_score, idx in zip(scores[0], indices[0]):
        if idx < 0:
            continue
        row = df.iloc[idx]
        final_score = float(clip_score)

        # Metadata re-ranking boosts
        if location and str(row.get("location", "")).lower() == location.lower():
            final_score += 0.08
        if category and str(row.get("category", "")).lower() == category.lower():
            final_score += 0.08
        if date and _date_close(row.get("date", ""), date):
            final_score += 0.05

        results.append({
            "item_id": str(row["item_id"]),
            "score": round(final_score, 4),
            "location": str(row["location"]),
            "date": str(row["date"]),
            "notify": final_score >= threshold,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]
