import numpy as np
from typing import List, Any

try:
    import faiss
except Exception:
    faiss = None

from ..matching.embedding import get_embedding


class SemanticIndex:
    """A lightweight semantic index with optional faiss support.

    Methods:
    - add(id, text, embedding=None)
    - search(query_text, top_k=5) -> list of (id, score)
    """

    def __init__(self):
        self.ids: List[Any] = []
        self.embs = None
        self._use_faiss = faiss is not None
        self._faiss_index = None
        self._id_map = {}

    def add(self, id_, text: str, embedding=None):
        if embedding is None:
            embedding = get_embedding(text)
        vec = np.array(embedding, dtype=np.float32)
        if self._use_faiss:
            if self._faiss_index is None:
                dim = vec.shape[0]
                index = faiss.IndexFlatIP(dim)
                self._faiss_index = faiss.IndexIDMap(index)
            # normalize for inner product similarity
            faiss.normalize_L2(vec.reshape(1, -1))
            try:
                stored_id = int(id_)
            except Exception:
                stored_id = abs(hash(id_)) % (2 ** 63)
            self._id_map[int(stored_id)] = id_
            self._faiss_index.add_with_ids(vec.reshape(1, -1), np.array([int(stored_id)], dtype=np.int64))
        else:
            if self.embs is None:
                self.embs = vec.reshape(1, -1)
            else:
                self.embs = np.vstack([self.embs, vec.reshape(1, -1)])
            self.ids.append(id_)

    def search(self, query_text: str, top_k: int = 5):
        q = get_embedding(query_text)
        qv = np.array(q, dtype=np.float32)
        results = []
        if self._use_faiss and self._faiss_index is not None:
            faiss.normalize_L2(qv.reshape(1, -1))
            D, I = self._faiss_index.search(qv.reshape(1, -1), top_k)
            for score, idx in zip(D[0], I[0]):
                if idx == -1:
                    continue
                orig = self._id_map.get(int(idx), int(idx))
                results.append((orig, float(score)))
        else:
            if self.embs is None:
                return []
            # compute cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity

            sims = cosine_similarity([qv], self.embs)[0]
            top_idx = np.argsort(sims)[::-1][:top_k]
            for i in top_idx:
                results.append((self.ids[i], float(sims[i])))
        return results


_GLOBAL_INDEX = None


def get_global_index() -> SemanticIndex:
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is None:
        _GLOBAL_INDEX = SemanticIndex()
    return _GLOBAL_INDEX
