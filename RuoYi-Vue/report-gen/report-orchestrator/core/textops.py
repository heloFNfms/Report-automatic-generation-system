from typing import List

def flatten_snippets(items) -> List[str]:
    texts = []
    for it in items:
        t = it.get("summary") or it.get("snippet") or it.get("title")
        if t:
            texts.append(t)
    return texts

def chunk_texts(texts: List[str], max_len: int = 900) -> List[str]:
    chunks = []
    for t in texts:
        if not t:
            continue
        if len(t) <= max_len:
            chunks.append(t)
            continue
        parts = t.replace("\n", " ").split(". ")
        cur = ""
        for p in parts:
            if len(cur) + len(p) + 2 <= max_len:
                cur = (cur + ". " + p).strip(". ")
            else:
                if cur:
                    chunks.append(cur)
                cur = p
        if cur:
            chunks.append(cur)
    return chunks
