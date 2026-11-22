"""
Step 3: store the chunk vectors and find the closest ones to a question.

FAISS (by Meta) does this fast even for millions of vectors. We use IndexFlatIP:
"flat" = compare against every vector (exact, fine for a few thousand chunks),
"IP" = inner product, which equals cosine similarity because vectors are unit length.
If FAISS cannot be installed, plain numpy gives the same results.
"""
import numpy as np

try:
    import faiss
except ImportError:                                 # numpy fallback, same results
    faiss = None


class VectorStore:
    def __init__(self, vectors):
        self.vectors = np.ascontiguousarray(vectors, dtype="float32")
        self.backend = "faiss" if faiss is not None else "numpy"
        if faiss is not None:
            self.index = faiss.IndexFlatIP(self.vectors.shape[1])
            self.index.add(self.vectors)

    def search(self, query_vec, k):
        """Return [(chunk_index, score)], best first."""
        q = np.ascontiguousarray(query_vec.reshape(1, -1), dtype="float32")
        k = min(k, len(self.vectors))
        if faiss is not None:
            scores, ids = self.index.search(q, k)
            return [(int(i), float(s)) for i, s in zip(ids[0], scores[0]) if i >= 0]
        scores = self.vectors @ q[0]
        top = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in top]
