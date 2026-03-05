from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import os, json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

@dataclass
class VectorStore:
    index_path: str
    meta_path: str
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    def __post_init__(self):
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.meta: List[Dict[str, Any]] = []

    def build(self, items: List[Dict[str, Any]]):
        texts = [it["text"] for it in items]
        if not texts:
            raise ValueError("No texts to index.")
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        emb = np.asarray(emb, dtype="float32")
        dim = emb.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(emb)
        self.index = index
        self.meta = items
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False)

    def load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

    def search(self, query: str, top_k: int = 6) -> List[Tuple[float, Dict[str, Any]]]:
        if self.index is None or not self.meta:
            raise RuntimeError("Vector index not loaded.")
        q = self.model.encode([query], normalize_embeddings=True)
        q = np.asarray(q, dtype="float32")
        scores, idxs = self.index.search(q, top_k)
        out = []
        for score, idx in zip(scores[0].tolist(), idxs[0].tolist()):
            if idx == -1:
                continue
            out.append((float(score), self.meta[idx]))
        return out
