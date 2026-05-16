"""
嵌入向量模块
负责文本向量化和相似度计算

支持多种嵌入后端（按优先级）:
    1. sentence-transformers: 深度学习语义嵌入（需联网下载模型）
    2. TF-IDF: 基于词频的向量化（离线可用，已内置）
    3. 随机投影哈希: 纯Python实现的最简回退方案（零依赖）

对应论文: 使用Contriever进行嵌入和相似度计算
"""

from typing import List, Tuple

import numpy as np

from .config import ThoughtConfig


class EmbeddingEngine:
    """
    嵌入向量引擎

    支持多后端自动切换:
        - primary: sentence-transformers (Contriever风格深度嵌入)
        - fallback: TF-IDF (基于scikit-learn，离线可用)
        - emergency: HashEmbedding (纯Python，零依赖)

    自动检测可用后端，按优先级选择
    """

    def __init__(self, config: ThoughtConfig):
        """
        初始化嵌入引擎

        Args:
            config: Thought-Retriever 配置对象
        """
        self.config = config
        self._model = None
        self._dimension = 384
        self._backend = None  # 'sentence_transformers' | 'tfidf' | 'hash'
        self._vocabulary = {}
        self._idf = None

    def _detect_backend(self) -> str:
        """检测可用的嵌入后端"""
        if self._backend is not None:
            return self._backend

        # 优先尝试 sentence-transformers
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

        # 回退到 TF-IDF
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            # 不在这里初始化，而是延迟到首次encode时
            self._backend = "tfidf"
            self._dimension = 256  # TF-IDF默认维度（动态）
            return self._backend
        except ImportError:
            pass

        # 最终回退到纯Python哈希嵌入
        self._backend = "hash"
        self._dimension = 128
        return self._backend

    def _ensure_backend(self):
        """确保后端已就绪"""
        backend = self._detect_backend()

        if backend == "sentence_transformers":
            if self._model is None:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.config.embedding_model)
                self._dimension = self._model.get_sentence_embedding_dimension()

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
        """
        将文本列表编码为嵌入向量

        Args:
            texts: 待编码的文本列表
            show_progress: 是否显示进度条（仅sentence_transformers后端支持）

        Returns:
            shape=(len(texts), dimension) 的嵌入向量矩阵（L2归一化）
        """
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

        elif backend == "tfidf":
            # TF-IDF：先fit再transform，然后L2归一化
            from sklearn.feature_extraction.text import TfidfVectorizer
            embeddings = self._model.fit_transform(texts).toarray().astype(np.float32)
            # L2归一化
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            embeddings = embeddings / norms
            return embeddings

        elif backend == "hash":
            embeddings = self._model.encode(texts)
            return embeddings

        return np.zeros((len(texts), self._dimension), dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """
        将单个文本编码为嵌入向量

        Args:
            text: 待编码的文本

        Returns:
            shape=(dimension,) 的嵌入向量
        """
        return self.encode([text])[0]

    def compute_similarity(
        self, query_embedding: np.ndarray, target_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        计算查询向量与目标向量之间的余弦相似度

        由于向量已L2归一化，点积即为余弦相似度

        Args:
            query_embedding: shape=(dimension,) 或 (1, dimension)
            target_embeddings: shape=(N, dimension)

        Returns:
            shape=(N,) 的相似度数组
        """
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
        """
        搜索与查询文本最相似的条目

        将查询与候选文本一起编码，确保TF-IDF等后端维度一致

        Args:
            query_text: 查询文本
            item_texts: 候选条目文本列表
            item_ids: 候选条目ID列表
            top_k: 返回的最大条目数

        Returns:
            [(id, text, similarity_score), ...] 按相似度降序排列
        """
        if not item_texts:
            return []

        # 将查询与候选文本合并编码，保证维度一致
        all_texts = item_texts + [query_text]
        all_embeddings = self.encode(all_texts)

        target_embeddings = all_embeddings[:-1]  # 候选条目向量
        query_embedding = all_embeddings[-1:]    # 查询向量

        similarities = self.compute_similarity(query_embedding, target_embeddings)

        # 排序并取top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((item_ids[idx], item_texts[idx], float(similarities[idx])))

        return results

    @property
    def dimension(self) -> int:
        """嵌入向量维度"""
        return self._dimension

    @property
    def backend_name(self) -> str:
        """当前使用的嵌入后端名称"""
        self._detect_backend()
        return self._backend


class _HashEmbedder:
    """
    纯Python哈希嵌入器（零依赖回退方案）

    使用字符n-gram哈希生成稀疏嵌入向量
    不依赖任何外部库或模型下载
    """

    def __init__(self, dim: int = 128, ngram_range: tuple = (2, 4)):
        """
        初始化哈希嵌入器

        Args:
            dim: 嵌入向量维度
            ngram_range: n-gram范围 (min_n, max_n)
        """
        self.dim = dim
        self.ngram_range = ngram_range

    def _extract_ngrams(self, text: str) -> List[str]:
        """提取字符n-gram特征"""
        text = text.lower()
        ngrams = []
        for n in range(self.ngram_range[0], self.ngram_range[1] + 1):
            for i in range(len(text) - n + 1):
                ngrams.append(text[i:i + n])
        return ngrams

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        将文本编码为哈希嵌入向量

        Args:
            texts: 文本列表

        Returns:
            L2归一化的嵌入向量矩阵
        """
        embeddings = np.zeros((len(texts), self.dim), dtype=np.float32)

        for i, text in enumerate(texts):
            ngrams = self._extract_ngrams(text)
            if not ngrams:
                continue
            # 对每个n-gram进行哈希，累加到向量中
            for ng in ngrams:
                h = hash(ng) % self.dim
                embeddings[i, h] += 1.0

        # TF-IDF风格归一化：先除以总n-gram数，再L2归一化
        ngram_counts = np.sum(embeddings, axis=1, keepdims=True)
        ngram_counts[ngram_counts == 0] = 1.0
        embeddings = embeddings / ngram_counts

        # L2归一化
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embeddings = embeddings / norms

        return embeddings