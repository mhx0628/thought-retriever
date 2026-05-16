"""
检索模块
实现论文中的 Thought Retrieval 步骤

从外部知识库 K 和思想记忆 T 的混合池中检索最相关的条目
检索方式: 基于嵌入向量的余弦相似度排序 (使用Contriever风格)
"""

from typing import List, Tuple

from .config import ThoughtConfig
from .embedding import EmbeddingEngine
from .thought_store import ThoughtStore


class ThoughtRetriever:
    """
    思想检索器

    对应论文 Algorithm 1 中的 Step 3: Ti ← R(Qi, K ∪ T)
    从外部知识 + 思想记忆的混合池中检索最相关的条目

    核心逻辑:
        1. 获取所有可检索条目（知识块 + 有效思想）
        2. 使用嵌入向量计算查询与所有条目的余弦相似度
        3. 返回 top_k 个最相关条目
    """

    def __init__(self, store: ThoughtStore, embedding_engine: EmbeddingEngine, config: ThoughtConfig):
        """
        初始化检索器

        Args:
            store: 思想存储管理器
            embedding_engine: 嵌入向量引擎
            config: 配置对象
        """
        self.store = store
        self.embedding = embedding_engine
        self.config = config

    def retrieve(
        self, query: str, top_k: int = None, include_metadata: bool = False
    ) -> List[dict]:
        """
        检索与查询最相关的条目

        对应论文公式: Ti ← R(Qi, K ∪ T)

        Args:
            query: 用户查询文本
            top_k: 检索返回条数（默认使用配置中的值）
            include_metadata: 是否包含完整元数据

        Returns:
            检索结果列表，每项包含 id, content, type, score, abstraction_level 等字段
        """
        if top_k is None:
            top_k = self.config.top_k

        # 获取所有可检索条目
        all_items = self.store.get_all_items()
        if not all_items:
            return []

        # 提取文本和ID
        item_texts = [item["content"] for item in all_items]
        item_ids = [item["id"] for item in all_items]

        # 执行相似度搜索
        search_results = self.embedding.search_similar(
            query_text=query,
            item_texts=item_texts,
            item_ids=item_ids,
            top_k=top_k,
        )

        # 组装结果
        id_to_item = {item["id"]: item for item in all_items}
        results = []
        for item_id, text, score in search_results:
            base = id_to_item.get(item_id, {})
            result = {
                "id": item_id,
                "content": text,
                "type": base.get("type", "unknown"),
                "score": score,
                "abstraction_level": base.get("abstraction_level", 1),
            }
            if include_metadata:
                if base.get("type") == "thought":
                    thought = self.store.get_thought(item_id)
                    if thought:
                        result["source_query"] = thought.source_query
                        result["sources"] = thought.sources
                        result["timestamp"] = thought.timestamp
                        result["metadata"] = thought.metadata
            results.append(result)

        return results

    def retrieve_with_context(
        self, query: str, top_k: int = None
    ) -> Tuple[List[dict], str]:
        """
        检索并构建上下文文本

        Args:
            query: 用户查询
            top_k: 检索条数

        Returns:
            (检索结果列表, 拼接后的上下文字符串)
        """
        results = self.retrieve(query, top_k)
        context_parts = []
        for r in results:
            context_parts.append(f"[{r['type']}] {r['content']}")
        context = "\n\n".join(context_parts)
        return results, context

    def get_abstraction_distribution(self, results: List[dict]) -> dict:
        """
        分析检索结果的抽象层级分布

        Args:
            results: 检索结果列表

        Returns:
            各抽象层级的条目计数
        """
        distribution = {}
        for r in results:
            level = r.get("abstraction_level", 1)
            distribution[level] = distribution.get(level, 0) + 1
        return distribution