import os
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer

# FAISS 实现
class FaissStore:
    def __init__(self, dim=384):
        import faiss
        self.faiss = faiss
        self.index = faiss.IndexFlatL2(dim)
        self.texts: List[str] = []
        self.metas: List[Dict] = []

    def add(self, embs: np.ndarray, texts: List[str], metas: List[Dict]):
        self.index.add(embs.astype("float32"))
        self.texts.extend(texts)
        self.metas.extend(metas)

    def search(self, query_emb: np.ndarray, top_k=5):
        D, I = self.index.search(query_emb.reshape(1, -1).astype("float32"), top_k)
        return [(self.texts[i], self.metas[i]) for i in I[0]]

# PGVector（示例：仅接口，实际项目里创建表: id bigserial pk, embedding vector(384), text text, meta jsonb）
class PGVectorStore:
    def __init__(self, dsn: str, dim=384):
        import psycopg
        self.pg = psycopg
        self.conn = psycopg.connect(dsn)
        self.dim = dim
        with self.conn.cursor() as cur:
            cur.execute(
                """
                create table if not exists embeddings (
                  id bigserial primary key,
                  embedding vector(%s),
                  text text,
                  meta jsonb
                );
                """,
                (dim,)
            )
            self.conn.commit()

    def add(self, embs: np.ndarray, texts: List[str], metas: List[Dict]):
        with self.conn.cursor() as cur:
            for v, t, m in zip(embs.tolist(), texts, metas):
                cur.execute("insert into embeddings(embedding, text, meta) values (%s, %s, %s)", (v, t, m))
            self.conn.commit()

    def search(self, query_emb: np.ndarray, top_k=5):
        with self.conn.cursor() as cur:
            cur.execute(
                "select text, meta from embeddings order by embedding <-> %s limit %s",
                (query_emb.tolist(), top_k)
            )
            return cur.fetchall()

class Embedding:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)
