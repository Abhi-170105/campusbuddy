import numpy as np
import pandas as pd
from PIL import Image, ImageFilter
import lostfound


def verify_ownership(item_id, claimer_answer, threshold=0.65):
    """Compares claimer's description against the finder's hidden secret_detail."""
    df = pd.read_csv(lostfound.ITEMS_CSV)
    match = df[df["item_id"] == item_id]
    if match.empty:
        return {"verified": False, "similarity": 0.0, "reason": "Item ID not found"}

    secret = str(match.iloc[0].get("secret_detail", "")).strip()
    if not secret or secret.lower() == "nan":
        return {"verified": True, "similarity": 1.0, "reason": "No secret detail set"}

    v1 = lostfound.embed_text(secret)
    v2 = lostfound.embed_text(claimer_answer)
    sim = float(np.dot(v1, v2))
    return {
        "verified": sim >= threshold,
        "similarity": round(sim, 4),
    }


def is_blurry(image_path, threshold=150.0):
    """Returns (True/False, sharpness_score). Low edge variance = blurry image."""
    img = Image.open(lostfound._resolve_path(image_path)).convert("L")
    edges = img.filter(ImageFilter.FIND_EDGES)
    sharpness = float(np.var(np.array(edges, dtype="float32")))
    return sharpness < threshold, round(sharpness, 2)


def check_duplicate(description, image_path=None, dup_threshold=0.92):
    """Checks if a nearly identical item already exists in the found database."""
    hits = lostfound.search_lost_item(description, image_path=image_path, k=1)
    if hits and hits[0]["score"] >= dup_threshold:
        return {"is_duplicate": True, "existing_item_id": hits[0]["item_id"], "score": hits[0]["score"]}
    return {"is_duplicate": False, "existing_item_id": None, "score": hits[0]["score"] if hits else 0.0}
