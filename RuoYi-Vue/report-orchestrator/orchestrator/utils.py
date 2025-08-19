from typing import List
import math

def chunk_texts(texts: List[str], max_len: int = 800) -> List[str]:
    chunks = []
    for t in texts:
        if not t:
            continue
        if len(t) <= max_len:
            chunks.append(t)
            continue
        # naive split by sentence
        parts = t.split('. ')
        cur = ''
        for p in parts:
            if len(cur) + len(p) + 1 <= max_len:
                cur = (cur + '. ' + p).strip()
            else:
                if cur:
                    chunks.append(cur)
                cur = p
        if cur:
            chunks.append(cur)
    return chunks

    # compress chunks into a single prompt (naive concatenation + truncation)


def compress_chunks(chunks: List[str], max_tokens: int = 2000) -> str:
    joined = '\n\n'.join(chunks)
    if len(joined) <= 4000:
        return joined
    # truncate
    return joined[:4000]