# CampusBuddy — AI Lost-and-Found Module (Member 2)

Multimodal Lost-and-Found search using **CLIP (`ViT-B-32`)** embeddings, **FAISS (`IndexFlatIP`)** vector search, metadata re-ranking, and ownership verification.

## Folder Structure
- `lostfound/__init__.py` — Core CLIP + FAISS pipeline and shared team functions
- `lostfound/extras.py` — Ownership verification, blurry-photo check, duplicate detection
- `lostfound/tests/test_lostfound.py` — Automated unit tests
- `data/items/items.csv` & `data/items/images/` — Item metadata and photos
- `eval/evaluate_lostfound.py` — Evaluation vs TF-IDF and ResNet50 baselines

## Shared Contract Functions (for Member 4 Backend)
- `lostfound.add_found_item(image_path, description, location, date) -> item_id`
- `lostfound.search_lost_item(description, image_path=None, k=5) -> [{"item_id", "score", "location", "date", "notify"}]`

## Running Tests & Evaluation
```bash
pytest CampusBuddy/lostfound/tests/
python CampusBuddy/eval/evaluate_lostfound.py
