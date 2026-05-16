"""
思想合并（冗余检测）模块
实现论文中的双重过滤机制之二: 冗余检查

对应论文 Algorithm 1 中的 Step 7: si ← 1{∃j,m; sim(Ti, Kj/Tm) ≥ ε}
通过余弦相似度判断新思想是否与已有条目冗余

核心参数 ε (similarity_threshold): 默认 0.85
    - sim < ε: 新思想是新颖的 (si=0), 可加入记忆
    - sim ≥ ε: 新思想是冗余的 (si=1), 应丢弃
"""

from typing import List, Tuple

import numpy as np

from .config import ThoughtConfig
from .embedding import EmbeddingEngine
from .thought_store import ThoughtStore


class ThoughtMerger:
    """
    思想合并器

    负责检测新生成思想与已有思想/知识的冗余度

    论文中:
        - 计算Ti与所有已有条目(Tm, Kj)的最大嵌入相似度
        - si = 1 表示冗余（相似度≥ε），不应加入记忆
        - si = 0 表示新颖（相似度<ε），可以加入记忆
        - 论文验证: 即使注入低质量/不相关思想，系统性能几乎不受影响
    """

    def __init__(self, store: ThoughtStore, embedding_engine: EmbeddingEngine, config: ThoughtConfig):
        """
        初始化合并器

        Args:
            store: 思想存储管理器
            embedding_engine: 嵌入向量引擎
            config: 配置对象
        """
        self.store = store
        self.embedding = embedding_engine
        self.config = config

    def check_redundancy(self, thought_content: str) -> Tuple[int, float, str]:
        """
        检查思想是否与已存在条目冗余

        计算新思想与所有已有条目的最大余弦相似度
        若超过阈值ε，则标记为冗余

        Args:
            thought_content: 新思想的内容文本

        Returns:
            (si, max_similarity, closest_id):
                si: 0=新颖可加入, 1=冗余应丢弃
                max_similarity: 与最相似条目的相似度
                closest_id: 最相似条目的ID
        """
        all_items = self.store.get_all_items()
        if not all_items:
            return 0, 0.0, ""

        # 编码所有已有条目文本 + 新思想文本
        item_texts = [item["content"] for item in all_items]
        item_ids = [item["id"] for item in all_items]

        # 编码并计算相似度
        all_texts = item_texts + [thought_content]
        embeddings = self.embedding.encode(all_texts)

        target_embeddings = embeddings[:-1]  # 已有条目向量
        new_embedding = embeddings[-1:]      # 新思想向量

        similarities = self.embedding.compute_similarity(
            new_embedding, target_embeddings
        )

        max_idx = int(np.argmax(similarities))
        max_sim = float(similarities[max_idx])
        closest_id = item_ids[max_idx]

        # 判断是否冗余
        if max_sim >= self.config.similarity_threshold:
            return 1, max_sim, closest_id
        else:
            return 0, max_sim, closest_id

    def find_similar_thoughts(
        self, thought_content: str, min_similarity: float = 0.5
    ) -> List[Tuple[str, str, float]]:
        """
        查找与新思想相似的所有已有思想

        Args:
            thought_content: 新思想内容
            min_similarity: 最低相似度阈值

        Returns:
            [(id, content, similarity), ...] 相似度降序排列
        """
        all_items = self.store.get_all_items()
        if not all_items:
            return []

        item_texts = [item["content"] for item in all_items]
        item_ids = [item["id"] for item in all_items]

        all_texts = item_texts + [thought_content]
        embeddings = self.embedding.encode(all_texts)

        target_embeddings = embeddings[:-1]
        new_embedding = embeddings[-1:]

        similarities = self.embedding.compute_similarity(
            new_embedding, target_embeddings
        )

        results = []
        for i, sim in enumerate(similarities):
            if sim >= min_similarity:
                results.append((item_ids[i], item_texts[i], float(sim)))

        results.sort(key=lambda x: x[2], reverse=True)
        return results

    def should_add_thought(self, confidence: int, redundancy_flag: int) -> bool:
        """
        综合判断是否应将思想加入记忆

        对应论文更新条件: ci = 1 AND si = 0

        Args:
            confidence: 置信度 (1=有效, 0=无效)
            redundancy_flag: 冗余标记 (0=新颖, 1=冗余)

        Returns:
            True表示应加入记忆
        """
        return confidence == 1 and redundancy_flag == 0