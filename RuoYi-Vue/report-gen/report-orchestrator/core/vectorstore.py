import os, json
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

class Embedding:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)

class FaissStore:
    def __init__(self, dim=384, index_path=None, meta_path=None):
        import faiss
        self.faiss = faiss
        self.index = faiss.IndexFlatL2(dim)
        self.texts: List[str] = []
        self.metas: List[Dict] = []
        self.index_path = index_path or os.getenv("FAISS_INDEX_PATH", "./data/faiss.index")
        self.meta_path = meta_path or os.getenv("FAISS_META_PATH", "./data/faiss_meta.json")
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

    def add(self, embs: np.ndarray, texts: List[str], metas: List[Dict]):
        self.index.add(embs.astype("float32"))
        self.texts.extend(texts)
        self.metas.extend(metas)
        self.save()

    def search(self, query_emb: np.ndarray, top_k=5) -> List[Tuple[str, Dict]]:
        if self.index.ntotal == 0:
            return []
        D, I = self.index.search(query_emb.reshape(1, -1).astype("float32"), top_k)
        res = []
        for i in I[0]:
            if 0 <= i < len(self.texts):
                res.append((self.texts[i], self.metas[i]))
        return res

    def save(self):
        self.faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({"texts": self.texts, "metas": self.metas}, f, ensure_ascii=False)

    def load(self):
        if os.path.exists(self.index_path):
            self.index = self.faiss.read_index(self.index_path)
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.texts = data.get("texts", [])
                self.metas = data.get("metas", [])

class PGVectorStore:
    def __init__(self, dsn: str, dim=384):
        import psycopg
        self.pg = psycopg
        self.conn = psycopg.connect(dsn)
        self.dim = dim
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id BIGSERIAL PRIMARY KEY,
                    embedding vector({dim}),
                    text TEXT,
                    meta JSONB
                );
                """
            )
            self.conn.commit()

    def add(self, embs: np.ndarray, texts: List[str], metas: List[Dict]):
        with self.conn.cursor() as cur:
            for v, t, m in zip(embs.tolist(), texts, metas):
                cur.execute("INSERT INTO embeddings(embedding, text, meta) VALUES (%s, %s, %s)", (v, t, json.dumps(m)))
            self.conn.commit()

    def search(self, query_emb: np.ndarray, top_k=5):
        with self.conn.cursor() as cur:
            cur.execute("SELECT text, meta FROM embeddings ORDER BY embedding <-> %s LIMIT %s", (query_emb.tolist(), top_k))
            return cur.fetchall()
