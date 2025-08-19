from rank_bm25 import BM25Okapi
from typing import List
from nltk.tokenize import word_tokenize

def rerank_bm25(queries: List[str], texts: List[str]) -> List[int]:
    tokenized = [word_tokenize(t.lower()) for t in texts]
    bm25 = BM25Okapi(tokenized)
    # combine queries
    q = ' '.join(queries).lower()
    qtok = word_tokenize(q)
    scores = bm25.get_scores(qtok)
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return ranked