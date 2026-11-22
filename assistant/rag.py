"""
The full RAG pipeline: Retrieval-Augmented Generation.

    question -> embed -> find top-k chunks (FAISS) -> confident enough?
                                                       no  -> "I don't know"
                                                       yes -> LLM writes the answer from those chunks
                                                              -> answer + sources

The index is built once and saved in assistant/index/. It is rebuilt
automatically when the documents or chunk settings change (we compare a
fingerprint), so adding a new document to data/docs/ just works.
"""
import hashlib
import json

import numpy as np

from . import config
from .documents import chunk_documents, load_documents, text_for_embedding
from .embedder import TfidfEmbedder, make_embedder
from .generator import make_generator
from .vector_store import VectorStore


def _fingerprint(docs, embedder_name, chunk_words, overlap):
    h = hashlib.sha256(f"{embedder_name}|{chunk_words}|{overlap}".encode())
    for d in docs:
        h.update(d["source"].encode())
        h.update(d["text"].encode("utf-8"))
    return h.hexdigest()[:16]


class Assistant:
    def __init__(self, docs_dir=None, index_dir=None, embed=None, llm=None,
                 top_k=None, threshold=None, chunk_words=None, overlap=None, save=True):
        self.docs_dir = docs_dir or config.DOCS_DIR
        self.index_dir = index_dir or config.INDEX_DIR
        self.top_k = top_k or config.TOP_K
        self.chunk_words = chunk_words or config.CHUNK_WORDS
        self.overlap = config.CHUNK_OVERLAP if overlap is None else overlap
        self.save = save
        self.embedder = make_embedder(embed)
        self.generator = make_generator(llm)
        self._build_or_load()
        self.threshold = self._pick_threshold(threshold)

    # ---------- index ----------
    def _build_or_load(self):
        docs = load_documents(self.docs_dir)
        if not docs:
            raise RuntimeError(f"No documents found in {self.docs_dir}")
        fp = _fingerprint(docs, self.embedder.name, self.chunk_words, self.overlap)
        meta_path = self.index_dir / "meta.json"
        if self.save and meta_path.exists() and json.loads(meta_path.read_text())["fingerprint"] == fp:
            self.chunks = json.loads((self.index_dir / "chunks.json").read_text(encoding="utf-8"))
            vectors = np.load(self.index_dir / "vectors.npy")
            if isinstance(self.embedder, TfidfEmbedder):
                self.embedder.load(self.index_dir / "tfidf.pkl")
            self.built = False
        else:
            self.chunks = chunk_documents(docs, self.chunk_words, self.overlap)
            texts = [text_for_embedding(c) for c in self.chunks]
            self.embedder.fit(texts)
            vectors = self.embedder.encode(texts)
            if self.save:
                self.index_dir.mkdir(parents=True, exist_ok=True)
                (self.index_dir / "chunks.json").write_text(json.dumps(self.chunks, indent=1), encoding="utf-8")
                np.save(self.index_dir / "vectors.npy", vectors)
                self.embedder.save(self.index_dir / "tfidf.pkl")
                meta = {"fingerprint": fp, "embedder": self.embedder.name, "chunks": len(self.chunks),
                        "documents": len(docs), "chunk_words": self.chunk_words, "overlap": self.overlap}
                meta_path.write_text(json.dumps(meta, indent=1))
            self.built = True
        self.store = VectorStore(vectors)
        self.n_docs = len(docs)

    def _pick_threshold(self, threshold):
        if threshold is not None:
            return float(threshold)
        if config.THRESHOLD_OVERRIDE:
            return float(config.THRESHOLD_OVERRIDE)
        tuned = self.index_dir / "tuned.json"
        if tuned.exists():
            saved = json.loads(tuned.read_text())
            if saved.get("embedder") == self.embedder.name:
                return float(saved["threshold"])
        return config.DEFAULT_THRESHOLDS[self.embedder.name]

    # ---------- question answering ----------
    def retrieve(self, question, k=None):
        q = self.embedder.encode([question])[0]
        return [dict(self.chunks[i], score=round(s, 4)) for i, s in self.store.search(q, k or self.top_k)]

    def ask(self, question):
        question = (question or "").strip()
        if not question:
            return {"answer": config.IDK, "sources": []}
        hits = self.retrieve(question)
        if not hits or hits[0]["score"] < self.threshold:
            return {"answer": config.IDK, "sources": []}          # safety net 1: weak retrieval
        passages = [h for h in hits if h["score"] >= self.threshold]
        answer, used = self.generator.answer(question, passages)
        if answer == config.IDK:
            return {"answer": config.IDK, "sources": []}          # safety net 2: model refused
        sources = [{"source": passages[i]["source"], "section": passages[i]["section"],
                    "score": passages[i]["score"], "snippet": passages[i]["text"][:200]}
                   for i in used]
        return {"answer": answer, "sources": sources}
