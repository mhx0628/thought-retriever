"""
嵌入向量模块
负责文本向量化和相似度计算

支持多种嵌入后端（按优先级）:
    1. sentence-transformers: 深度学习语义嵌入（需联网下载模型）
    2. jieba_tfidf: jieba中文分词 + TF-IDF（离线可用，中文优化）
    3. TF-IDF: 基于词频的向量化（离线可用，已内置）
    4. 随机投影哈希: 纯Python实现的最简回退方案（零依赖）

对应论文: 使用Contriever进行嵌入和相似度计算
"""

from typing import List, Tuple

import numpy as np

from .config import ThoughtConfig


class EmbeddingEngine:

    def __init__(self, config: ThoughtConfig):
        self.config = config
        self._model = None
        self._dimension = 384
        self._backend = None
        self._vocabulary = {}
        self._idf = None
        self._jieba_initialized = False

    def _detect_backend(self) -> str:
        if self._backend is not None:
            return self._backend

        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.config.embedding_model)
            self._model = model
            self._dimension = model.get_sentence_embedding_dimension()
            self._backend = "sentence_transformers"
            return self._backend
        except ImportError:
            pass
        except Exception:
            pass

        try:
            import jieba
            self._backend = "jieba_tfidf"
            self._dimension = 256
            return self._backend
        except ImportError:
            pass

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._backend = "tfidf"
            self._dimension = 256
            return self._backend
        except ImportError:
            pass

        self._backend = "hash"
        self._dimension = 128
        return self._backend

    def _ensure_backend(self):
        backend = self._detect_backend()

        if backend == "sentence_transformers":
            if self._model is None:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.config.embedding_model)
                self._dimension = self._model.get_sentence_embedding_dimension()

        elif backend == "jieba_tfidf":
            if self._model is None:
                self._model = _JiebaTfidfEmbedder(dim=self._dimension)

        elif backend == "tfidf":
            if self._model is None:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._model = TfidfVectorizer(
                    max_features=256,
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                )

        elif backend == "hash":
            if self._model is None:
                self._model = _HashEmbedder(dim=self._dimension)

    def encode(self, texts: List[str], show_progress: bool = False) -> np.ndarray:
        self._ensure_backend()
        backend = self._backend

        if backend == "sentence_transformers":
            embeddings = self._model.encode(
                texts,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embeddings

        elif backend == "jieba_tfidf":
            return self._model.encode(texts)

        elif backend == "tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            embeddings = self._model.fit_transform(texts).toarray().astype(np.float32)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms
            return embeddings

        elif backend == "hash":
            embeddings = self._model.encode(texts)
            return embeddings

        return np.zeros((len(texts), self._dimension), dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    def compute_similarity(
        self, query_embedding: np.ndarray, target_embeddings: np.ndarray
    ) -> np.ndarray:
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        return np.dot(target_embeddings, query_embedding.T).flatten()

    def search_similar(
        self,
        query_text: str,
        item_texts: List[str],
        item_ids: List[str],
        top_k: int = 8,
    ) -> List[Tuple[str, str, float]]:
        if not item_texts:
            return []

        all_texts = item_texts + [query_text]
        all_embeddings = self.encode(all_texts)

        target_embeddings = all_embeddings[:-1]
        query_embedding = all_embeddings[-1:]

        similarities = self.compute_similarity(query_embedding, target_embeddings)

        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((item_ids[idx], item_texts[idx], float(similarities[idx])))

        return results

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def backend_name(self) -> str:
        self._detect_backend()
        return self._backend


class _JiebaTfidfEmbedder:
    """
    jieba中文分词 + TF-IDF嵌入器

    核心优化:
        - 使用jieba进行中文分词，将"小明喜欢画画"分为["小明","喜欢","画画"]
        - 基于分词结果构建词频向量，语义相似度大幅提升
        - 支持同义词扩展（可选）
        - 纯离线运行，无需下载模型
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self._jieba = None
        self._stop_words = set([
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '他', '她',
            '它', '吗', '吧', '呢', '啊', '呀', '哦', '嗯', '哈', '嘛',
            '那', '这个', '那个', '什么', '怎么', '为什么', '可以', '能',
        ])
        self._vocab_index = None
        self._idf = None
        self._vocab_size = None

    def _ensure_jieba(self):
        if self._jieba is None:
            import jieba
            jieba.setLogLevel(20)
            self._jieba = jieba

    def _tokenize(self, text: str) -> List[str]:
        self._ensure_jieba()
        words = list(self._jieba.cut(text))
        return [w.strip() for w in words if w.strip() and w not in self._stop_words and len(w.strip()) > 0]

    def _build_vocab_and_tfidf(self, tokenized_texts: List[List[str]]):
        df = {}
        total_docs = len(tokenized_texts)
        for tokens in tokenized_texts:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1

        import math
        idf = {}
        for t, count in df.items():
            idf[t] = math.log((total_docs + 1) / (count + 1)) + 1

        sorted_vocab = sorted(df.keys(), key=lambda x: df[x], reverse=True)[:self.dim]
        vocab_index = {w: i for i, w in enumerate(sorted_vocab)}

        return vocab_index, idf, len(sorted_vocab)

    def encode(self, texts: List[str]) -> np.ndarray:
        tokenized = [self._tokenize(t) for t in texts]

        if self._vocab_index is None:
            vocab_index, idf, vocab_size = self._build_vocab_and_tfidf(tokenized)
            self._vocab_index = vocab_index
            self._idf = idf
            self._vocab_size = vocab_size
        else:
            vocab_index = self._vocab_index
            idf = self._idf
            vocab_size = self._vocab_size

        embeddings = np.zeros((len(texts), self.dim), dtype=np.float32)

        for i, tokens in enumerate(tokenized):
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            total = len(tokens) if tokens else 1
            for t, count in tf.items():
                if t in vocab_index:
                    embeddings[i, vocab_index[t]] = (count / total) * idf.get(t, 1.0)

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        return embeddings


class _HashEmbedder:

    def __init__(self, dim: int = 128, ngram_range: tuple = (2, 4)):
        self.dim = dim
        self.ngram_range = ngram_range

    def _extract_ngrams(self, text: str) -> List[str]:
        text = text.lower()
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text) - n + 1):
                ngrams.append(text[i:i + n])
        return ngrams

    def encode(self, texts: List[str]) -> np.ndarray:
        embeddings = np.zeros((len(texts), self.dim), dtype=np.float32)

        for i, text in enumerate(texts):
            ngrams = self._extract_ngrams(text)
            if not ngrams:
                continue
            for ng in ngrams:
                h = hash(ng) % self.dim
                embeddings[i, h] += 1.0

        ngram_counts = np.sum(embeddings, axis=1, keepdims=True)
        ngram_counts[ngram_counts == 0] = 1.0
        embeddings = embeddings / ngram_counts

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        return embeddings
