from typing import List, Dict

def simple_rerank(results: List[Dict], query: str, topk: int = 8) -> List[Dict]:
    # 超简版打分：标题/摘要里包含词数
    scores = []
    for it in results:
        text = (it.get("title","") + " " + it.get("snippet","")).lower()
        score = sum(text.count(w.lower()) for w in query.split())
        scores.append((score, it))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scores[:topk]]

def compress(results: List[Dict], max_items: int = 6) -> List[Dict]:
    return results[:max_items]

def to_bullets(results: List[Dict]) -> str:
    return "\n".join([f"- {it.get('title','(no title)')}: {it.get('snippet','')[:200]}" for it in results])
