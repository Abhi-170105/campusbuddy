"""
Step 2: turn text into vectors (lists of numbers) so similar meanings are close together.

Two backends:
  - sentence-transformers (all-MiniLM-L6-v2): understands meaning, e.g. "when do exams
    begin" matches "SEE start on 7 December". This is the real one, used on the laptop.
  - TF-IDF: matches shared words only. No download needed. Used as a fallback when
    sentence-transformers is not installed, and in unit tests so they run fast offline.

Both return unit-length vectors, so a dot product = cosine similarity (1 = same meaning).
"""
import pickle

import numpy as np

from . import config


class TfidfEmbedder:
    name = "tfidf"

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vec = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2),
                                   sublinear_tf=True, token_pattern=r"(?u)\b[\w.:%-]+\b")
        self.fitted = False

    def fit(self, texts):
        self.vec.fit(texts)
        self.fitted = True

    def encode(self, texts):
        m = self.vec.transform(texts).toarray().astype("float32")
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.where(norms == 0, 1, norms)

    def save(self, path):
        path.write_bytes(pickle.dumps(self.vec))

    def load(self, path):
        self.vec = pickle.loads(path.read_bytes())
        self.fitted = True


class SentenceTransformerEmbedder:
    name = "sentence-transformers"

    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.fitted = True

    def fit(self, texts):
        pass  # pre-trained, nothing to fit

    def encode(self, texts):
        return self.model.encode(list(texts), normalize_embeddings=True,
                                 convert_to_numpy=True).astype("float32")

    def save(self, path):
        pass

    def load(self, path):
        pass


def make_embedder(choice=None):
    choice = choice or config.EMBED
    if choice == "tfidf":
        return TfidfEmbedder()
    model = config.DEFAULT_EMBED_MODEL if choice == "auto" else choice
    try:
        return SentenceTransformerEmbedder(model)
    except Exception as err:                       # not installed, or no internet for the download
        if choice != "auto":
            raise
        print(f"[assistant] sentence-transformers unavailable ({type(err).__name__}); using TF-IDF.")
        return TfidfEmbedder()
