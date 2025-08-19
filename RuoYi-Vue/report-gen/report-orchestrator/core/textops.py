from typing import List, Tuple, Set
import re
import hashlib
try:
    import tiktoken
    from rank_bm25 import BM25Okapi
except ImportError:
    tiktoken = None
    BM25Okapi = None

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

def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """估算文本的 token 数量"""
    if tiktoken:
        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except:
            pass
    # 简单估算：中文按字符数，英文按单词数 * 1.3
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'\b\w+\b', text))
    return int(chinese_chars + english_words * 1.3)

def rerank_texts(query: str, texts: List[str], top_k: int = 6) -> List[Tuple[str, float]]:
    """使用 BM25 对文本进行重排序"""
    if not texts or not BM25Okapi:
        return [(t, 1.0) for t in texts[:top_k]]
    
    # 简单分词（支持中英文）
    def tokenize(text: str) -> List[str]:
        # 中文按字符分，英文按单词分
        chinese = re.findall(r'[\u4e00-\u9fff]', text)
        english = re.findall(r'\b\w+\b', text.lower())
        return chinese + english
    
    try:
        corpus_tokens = [tokenize(text) for text in texts]
        bm25 = BM25Okapi(corpus_tokens)
        query_tokens = tokenize(query)
        scores = bm25.get_scores(query_tokens)
        
        # 按分数排序
        ranked = sorted(zip(texts, scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
    except:
        # 如果 BM25 失败，返回原始顺序
        return [(t, 1.0) for t in texts[:top_k]]

def budget_context(texts: List[str], max_tokens: int = 1500, model: str = "gpt-3.5-turbo") -> List[str]:
    """根据 token 预算控制上下文长度"""
    result = []
    total_tokens = 0
    
    for text in texts:
        text_tokens = count_tokens(text, model)
        if total_tokens + text_tokens <= max_tokens:
            result.append(text)
            total_tokens += text_tokens
        else:
            # 如果单个文本就超过预算，截断它
            if not result and text_tokens > max_tokens:
                # 简单截断到预算内
                ratio = max_tokens / text_tokens
                truncated = text[:int(len(text) * ratio * 0.9)]  # 留点余量
                result.append(truncated)
            break
    
    return result

def smart_sentence_split(text: str) -> List[str]:
    """智能中英文混排分句"""
    if not text:
        return []
    
    # 预处理：保护特殊格式
    text = re.sub(r'(\d+\.\d+)', '<<NUM>>\\1<<NUM>>', text)  # 保护小数
    text = re.sub(r'([A-Z]\.)+', lambda m: m.group().replace('.', '<<DOT>>'), text)  # 保护缩写
    text = re.sub(r'(www\.|http[s]?://)', '<<URL>>\\1', text)  # 保护URL
    
    # 中英文混排分句规则
    patterns = [
        r'[。！？；]',  # 中文句号
        r'[.!?;](?=\s+[A-Z])',  # 英文句号后跟大写字母
        r'[.!?;](?=\s*$)',  # 句末标点
        r'\n+',  # 换行符
    ]
    
    sentences = [text]
    for pattern in patterns:
        new_sentences = []
        for sent in sentences:
            parts = re.split(f'({pattern})', sent)
            current = ''
            for i, part in enumerate(parts):
                if re.match(pattern, part):
                    current += part
                    new_sentences.append(current.strip())
                    current = ''
                else:
                    current += part
            if current.strip():
                new_sentences.append(current.strip())
        sentences = new_sentences
    
    # 恢复特殊格式
    result = []
    for sent in sentences:
        if not sent:
            continue
        sent = sent.replace('<<NUM>>', '').replace('<<DOT>>', '.').replace('<<URL>>', '')
        sent = sent.strip()
        if sent:
            result.append(sent)
    
    return result

def deduplicate_citations(texts: List[str], similarity_threshold: float = 0.8) -> List[str]:
    """引用去重"""
    if not texts:
        return []
    
    def text_hash(text: str) -> str:
        """计算文本哈希"""
        # 标准化文本：去除空白、标点，转小写
        normalized = re.sub(r'[\s\p{P}]+', '', text.lower())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def similarity(text1: str, text2: str) -> float:
        """计算文本相似度（简单版本）"""
        if not text1 or not text2:
            return 0.0
        
        # 转换为字符集合
        set1 = set(text1.lower())
        set2 = set(text2.lower())
        
        # Jaccard 相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    unique_texts = []
    seen_hashes: Set[str] = set()
    
    for text in texts:
        if not text.strip():
            continue
            
        # 完全重复检查
        text_hash_val = text_hash(text)
        if text_hash_val in seen_hashes:
            continue
        
        # 相似度检查
        is_similar = False
        for existing in unique_texts:
            if similarity(text, existing) >= similarity_threshold:
                is_similar = True
                break
        
        if not is_similar:
            unique_texts.append(text)
            seen_hashes.add(text_hash_val)
    
    return unique_texts

def smart_chunk_by_strategy(text: str, strategy: str = "sentence", max_tokens: int = 500, model: str = "gpt-3.5-turbo") -> List[str]:
    """智能分块策略"""
    if not text:
        return []
    
    if strategy == "sentence":
        return chunk_by_sentence(text, max_tokens, model)
    elif strategy == "paragraph":
        return chunk_by_paragraph(text, max_tokens, model)
    elif strategy == "token":
        return chunk_by_token(text, max_tokens, model)
    else:
        # 默认混合策略
        return chunk_by_mixed(text, max_tokens, model)

def chunk_by_sentence(text: str, max_tokens: int = 500, model: str = "gpt-3.5-turbo") -> List[str]:
    """按句子分块"""
    sentences = smart_sentence_split(text)
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence, model)
        
        if current_tokens + sentence_tokens <= max_tokens:
            current_chunk += (" " if current_chunk else "") + sentence
            current_tokens += sentence_tokens
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
            current_tokens = sentence_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def chunk_by_paragraph(text: str, max_tokens: int = 500, model: str = "gpt-3.5-turbo") -> List[str]:
    """按段落分块"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph, model)
        
        if current_tokens + paragraph_tokens <= max_tokens:
            current_chunk += ("\n\n" if current_chunk else "") + paragraph
            current_tokens += paragraph_tokens
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            # 如果单个段落超过限制，按句子分块
            if paragraph_tokens > max_tokens:
                chunks.extend(chunk_by_sentence(paragraph, max_tokens, model))
                current_chunk = ""
                current_tokens = 0
            else:
                current_chunk = paragraph
                current_tokens = paragraph_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def chunk_by_token(text: str, max_tokens: int = 500, model: str = "gpt-3.5-turbo") -> List[str]:
    """按 token 数量分块"""
    if count_tokens(text, model) <= max_tokens:
        return [text]
    
    # 简单按字符比例分块
    total_tokens = count_tokens(text, model)
    char_per_token = len(text) / total_tokens
    max_chars = int(max_tokens * char_per_token * 0.9)  # 留点余量
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + max_chars, len(text))
        
        # 尝试在句子边界分割
        if end < len(text):
            # 向前找句子结束符
            for i in range(end, max(start, end - 100), -1):
                if text[i] in '。！？.!?\n':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    
    return chunks

def chunk_by_mixed(text: str, max_tokens: int = 500, model: str = "gpt-3.5-turbo") -> List[str]:
    """混合分块策略：优先段落，其次句子，最后 token"""
    # 先尝试按段落分块
    paragraph_chunks = chunk_by_paragraph(text, max_tokens, model)
    
    # 检查是否有超长块需要进一步分割
    final_chunks = []
    for chunk in paragraph_chunks:
        if count_tokens(chunk, model) <= max_tokens:
            final_chunks.append(chunk)
        else:
            # 超长块按句子分割
            sentence_chunks = chunk_by_sentence(chunk, max_tokens, model)
            for sent_chunk in sentence_chunks:
                if count_tokens(sent_chunk, model) <= max_tokens:
                    final_chunks.append(sent_chunk)
                else:
                    # 还是超长就按 token 分割
                    final_chunks.extend(chunk_by_token(sent_chunk, max_tokens, model))
    
    return final_chunks
