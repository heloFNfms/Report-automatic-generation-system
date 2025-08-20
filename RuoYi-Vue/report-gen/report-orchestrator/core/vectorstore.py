import os, json
from typing import List, Dict, Tuple, Any
import numpy as np
import hashlib
from datetime import datetime
import faiss

class Embedding:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
    
    def _ensure_model_loaded(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
    def encode(self, texts: List[str]) -> np.ndarray:
        self._ensure_model_loaded()
        return self.model.encode(texts, convert_to_numpy=True)

class FaissStore:
    def __init__(self, dim: int = 384, index_path: str = "faiss.index", meta_path: str = "faiss_meta.json"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        self.index = faiss.IndexFlatIP(dim)  # 内积相似度
        self.metadata: List[Dict[str, Any]] = []
        self.text_hashes: set = set()  # 用于去重
        self.version = 1
        self.load()

    def _get_text_hash(self, text: str) -> str:
        """计算文本哈希值用于去重"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def add(self, embs: np.ndarray, texts: List[str], metas: List[Dict[str, Any]]):
        """添加向量和元数据（带去重）"""
        if embs.shape[0] != len(texts) or len(texts) != len(metas):
            raise ValueError("embeddings, texts, metas length mismatch")
        
        # 过滤重复文本
        unique_embeddings = []
        unique_texts = []
        unique_metas = []
        
        for i, text in enumerate(texts):
            text_hash = self._get_text_hash(text)
            if text_hash not in self.text_hashes:
                self.text_hashes.add(text_hash)
                unique_embeddings.append(embs[i])
                unique_texts.append(text)
                unique_metas.append(metas[i])
        
        if not unique_embeddings:
            return  # 所有文本都重复
        
        unique_embeddings = np.array(unique_embeddings)
        
        # 归一化向量（用于余弦相似度）
        faiss.normalize_L2(unique_embeddings)
        self.index.add(unique_embeddings.astype("float32"))
        
        # 添加元数据
        for i, (text, meta) in enumerate(zip(unique_texts, unique_metas)):
            self.metadata.append({
                "text": text,
                "meta": meta,
                "id": len(self.metadata),
                "hash": self._get_text_hash(text),
                "added_at": datetime.now().isoformat(),
                "version": self.version
            })
        self.save()

    def search(self, query_emb: np.ndarray, top_k=5) -> List[Tuple[str, Dict]]:
        """搜索最相似的向量"""
        if self.index.ntotal == 0:
            return []
        
        if len(query_emb.shape) == 1:
            query_emb = query_emb.reshape(1, -1)
        
        # 归一化查询向量
        faiss.normalize_L2(query_emb)
        
        D, I = self.index.search(query_emb.astype("float32"), top_k)
        res = []
        for i in I[0]:
            if 0 <= i < len(self.metadata):
                meta = self.metadata[i]
                res.append((meta["text"], meta["meta"]))
        return res

    def save(self):
        """保存索引和元数据（版本化）"""
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        
        # 保存当前版本
        versioned_index_path = f"{self.index_path}.v{self.version}"
        versioned_meta_path = f"{self.meta_path}.v{self.version}"
        
        faiss.write_index(self.index, versioned_index_path)
        
        with open(versioned_meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": self.version,
                "created_at": datetime.now().isoformat(),
                "total_vectors": len(self.metadata),
                "metadata": self.metadata
            }, f, ensure_ascii=False, indent=2)
        
        # 同时保存为最新版本
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "version": self.version,
                "created_at": datetime.now().isoformat(),
                "total_vectors": len(self.metadata),
                "metadata": self.metadata
            }, f, ensure_ascii=False, indent=2)

    def load(self):
        """加载索引和元数据"""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        
        if os.path.exists(self.meta_path):
            with open(self.meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "metadata" in data:
                    # 新格式
                    self.metadata = data.get("metadata", [])
                    self.version = data.get("version", 1)
                else:
                    # 兼容旧格式
                    texts = data.get("texts", [])
                    metas = data.get("metas", [])
                    self.metadata = []
                    for i, (text, meta) in enumerate(zip(texts, metas)):
                        self.metadata.append({
                            "text": text,
                            "meta": meta,
                            "id": i,
                            "hash": self._get_text_hash(text),
                            "added_at": datetime.now().isoformat(),
                            "version": 1
                        })
                    self.version = 1
                
                # 重建哈希集合
                for meta in self.metadata:
                    if "hash" in meta:
                        self.text_hashes.add(meta["hash"])
                    else:
                        # 为旧数据生成哈希
                        text_hash = self._get_text_hash(meta["text"])
                        meta["hash"] = text_hash
                        self.text_hashes.add(text_hash)

    def cleanup_old_versions(self, keep_versions: int = 5):
        """清理旧版本文件"""
        import glob
        
        # 获取所有版本文件
        index_files = glob.glob(f"{self.index_path}.v*")
        meta_files = glob.glob(f"{self.meta_path}.v*")
        
        # 按版本号排序，保留最新的几个版本
        index_files.sort(key=lambda x: int(x.split('.v')[-1]), reverse=True)
        meta_files.sort(key=lambda x: int(x.split('.v')[-1]), reverse=True)
        
        # 删除多余的版本
        for file_path in index_files[keep_versions:]:
            try:
                os.remove(file_path)
            except OSError:
                pass
        
        for file_path in meta_files[keep_versions:]:
            try:
                os.remove(file_path)
            except OSError:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """获取向量库统计信息"""
        return {
            "version": self.version,
            "total_vectors": len(self.metadata),
            "unique_texts": len(self.text_hashes),
            "index_size": self.index.ntotal,
            "dimension": self.dim
        }

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
