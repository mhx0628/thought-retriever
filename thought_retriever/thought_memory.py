"""
思想记忆管理核心模块
Thought-Retriever 框架的主入口，协调所有子模块完成五步流水线

基于论文 Algorithm 1 实现完整的推理算法:

    Input: 用户查询 Q, 外部知识 K, 思想记忆 T, 语言模型 L, 检索器 R, 相似度阈值 ε
    Output: 答案 A, 更新后的思想记忆 T

    1: A ← {}
    2: for Qi ∈ Q do
    3:     Ti ← R(Qi, K ∪ T)              # Thought retrieval
    4:     Ai ← L(Qi, Ti)                 # Answer generation
    5:     A ← A ∪ Ai
    6:     Ti, ci ← L(Qi, Ai)             # Thought and confidence generation
    7:     si ← 1{∃j,m; sim(Ti, Kj/Tm) ≥ ε}  # Thought merge
    8:     T ← T ∪ Ti, if ci = 1, si = 0  # Thought memory update
    9: end for
    10: return A, T
"""

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .config import ThoughtConfig
from .thought_store import ThoughtStore, Thought, KnowledgeChunk
from .embedding import EmbeddingEngine
from .retriever import ThoughtRetriever
from .confidence import ConfidenceFilter
from .merger import ThoughtMerger
from .utils import chunk_text, compute_abstraction_level, estimate_tokens, generate_id


class ThoughtMemory:
    """
    Thought-Retriever 思想记忆管理器（主入口类）

    提供完整的五步流水线:
        1. Thought Retrieval  - 检索相关思想和知识
        2. Answer Generation   - 基于检索结果生成答案
        3. Thought & Confidence Generation - 提炼思想并评估质量
        4. Thought Merge       - 检测冗余
        5. Thought Memory Update - 更新记忆库

    使用示例:
        >>> memory = ThoughtMemory(project_path=".")
        >>> memory.add_knowledge("项目使用微服务架构...")
        >>> answer, thoughts = memory.process_query(
        ...     query="如何设计API网关？",
        ...     generate_answer_fn=my_llm_function,
        ...     generate_thought_fn=my_llm_function
        ... )
        >>> results = memory.retrieve("API设计最佳实践")
        >>> print(memory.stats())
    """

    def __init__(
        self,
        project_path: str = ".",
        config: Optional[ThoughtConfig] = None,
        llm_fn: Optional[Callable[[str], str]] = None,
    ):
        """
        初始化思想记忆管理器

        Args:
            project_path: 项目根目录路径，思想数据存储于 {project_path}/.thoughts/
            config: 自定义配置（可选，默认使用论文参数）
            llm_fn: LLM调用函数（可选），签名为 fn(prompt: str) -> str
                    用于置信度评估的LLM模式
        """
        self.project_path = Path(project_path).resolve()
        self.config = config or ThoughtConfig(project_path=str(self.project_path))

        # 初始化各子模块
        self.store = ThoughtStore(self.config)
        self.embedding_engine = EmbeddingEngine(self.config)
        self.retriever = ThoughtRetriever(
            self.store, self.embedding_engine, self.config
        )
        self.confidence_filter = ConfidenceFilter(llm_fn=llm_fn)
        self.merger = ThoughtMerger(
            self.store, self.embedding_engine, self.config
        )

        # 嵌入向量缓存
        self._cached_embeddings = None
        self._id_to_index = {}

    def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> List[str]:
        """
        添加外部知识到知识库

        自动将长文本分块后逐块添加

        Args:
            content: 知识文本内容（会自动按chunk_size分块）
            metadata: 附加元数据

        Returns:
            添加的知识块ID列表
        """
        chunks = chunk_text(content, self.config.chunk_size)
        ids = []
        for chunk in chunks:
            kid = self.store.add_knowledge(chunk, metadata)
            ids.append(kid)
        # 知识变更后需要重建嵌入向量
        self._rebuild_embeddings()
        return ids

    def process_query(
        self,
        query: str,
        generate_answer_fn: Callable[[str, str], str],
        generate_thought_fn: Optional[Callable[[str], str]] = None,
        top_k: Optional[int] = None,
        metadata: Optional[Dict] = None,
    ) -> Tuple[str, List[Thought]]:
        """
        处理用户查询，执行完整的五步流水线

        对应论文 Algorithm 1 的完整流程

        Args:
            query: 用户查询文本
            generate_answer_fn: 答案生成函数
                签名: fn(query: str, context: str) -> str
            generate_thought_fn: 思想生成函数（可选，默认复用generate_answer_fn）
                签名: fn(prompt: str) -> str
                若不提供，则使用内置的从(Q,A)对提炼思想的方式
            top_k: 检索条数（默认使用配置值）
            metadata: 附加元数据（存入生成的思想中）

        Returns:
            (answer, new_thoughts):
                answer: 生成的答案文本
                new_thoughts: 本次新生成并成功存入记忆的思想列表
        """
        if generate_thought_fn is None:
            generate_thought_fn = generate_answer_fn

        # === Step 1: Thought Retrieval (思想检索) ===
        # 对应论文: Ti ← R(Qi, K ∪ T)
        retrieved_results, context = self.retriever.retrieve_with_context(query, top_k)

        # === Step 2: Answer Generation (答案生成) ===
        # 对应论文: Ai ← L(Qi, Ti)
        from .templates.prompts import answer_generation_prompt
        prompt = answer_generation_prompt(query, context)
        answer = generate_answer_fn(prompt)

        # === Step 3: Thought & Confidence Generation (思想与置信度生成) ===
        # 对应论文: Ti, ci ← L(Qi, Ai)
        from .templates.prompts import thought_confidence_prompt
        thought_prompt = thought_confidence_prompt(query, answer)
        thought_response = generate_thought_fn(thought_prompt).strip()

        # 解析LLM返回的思想和置信度
        thought_content, confidence = self._parse_thought_response(thought_response)

        new_thoughts = []

        if thought_content and confidence == 1:
            # === Step 4: Thought Merge (思想合并 - 冗余检测) ===
            # 对应论文: si ← 1{∃j,m; sim(Ti, Kj/Tm) ≥ ε}
            si, max_sim, closest_id = self.merger.check_redundancy(thought_content)

            # === Step 5: Thought Memory Update (思想记忆更新) ===
            # 对应论文: T ← T ∪ Ti, if ci = 1, si = 0
            if self.merger.should_add_thought(confidence, si):
                # 计算抽象层级
                source_ids = [r["id"] for r in retrieved_results]
                source_levels = []
                for r in retrieved_results:
                    source_levels.append(r.get("abstraction_level", 1))

                abstraction = compute_abstraction_level(source_levels)

                # 创建思想对象
                thought = Thought(
                    id=generate_id(thought_content, prefix="T"),
                    content=thought_content,
                    source_query=query,
                    source_answer=answer,
                    abstraction_level=abstraction,
                    sources=source_ids,
                    confidence=confidence,
                    metadata=metadata or {},
                )

                self.store.add_thought(thought)
                new_thoughts.append(thought)

                # 增量更新嵌入向量
                self._rebuild_embeddings()

        return answer, new_thoughts

    def add_thought_directly(
        self,
        content: str,
        source_query: str = "",
        source_answer: str = "",
        sources: Optional[List[str]] = None,
        abstraction_level: int = 2,
        confidence: int = 1,
        metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """
        直接添加思想（跳过LLM生成步骤）

        用于手动记录项目决策、设计思路等场景

        Args:
            content: 思想内容
            source_query: 来源查询
            source_answer: 来源回答
            sources: 来源ID列表
            abstraction_level: 抽象层级
            confidence: 置信度标记
            metadata: 附加元数据

        Returns:
            思想ID（若因冗余被拒绝则返回None）
        """
        # 冗余检查
        si, max_sim, closest_id = self.merger.check_redundancy(content)

        if not self.merger.should_add_thought(confidence, si):
            return None

        thought = Thought(
            id=generate_id(content, prefix="T"),
            content=content,
            source_query=source_query,
            source_answer=source_answer,
            abstraction_level=abstraction_level,
            sources=sources or [],
            confidence=confidence,
            metadata=metadata or {},
        )

        self.store.add_thought(thought)
        self._rebuild_embeddings()
        return thought.id

    def retrieve(
        self, query: str, top_k: int = None, include_metadata: bool = False
    ) -> List[dict]:
        """
        检索与查询相关的思想和知识

        Args:
            query: 查询文本
            top_k: 返回条数
            include_metadata: 是否包含完整元数据

        Returns:
            检索结果列表
        """
        return self.retriever.retrieve(query, top_k, include_metadata)

    def _parse_thought_response(self, response: str) -> Tuple[str, int]:
        """
        解析LLM返回的思想和置信度响应

        期望格式:
            1
            [思想内容]

        或:
            0

        Args:
            response: LLM原始响应文本

        Returns:
            (thought_content, confidence):
                thought_content: 思想内容（若ci=0则为空字符串）
                confidence: 置信度 (0或1)
        """
        response = response.strip()

        if not response:
            return "", 0

        # 尝试解析第一行为置信度
        lines = response.split("\n", 1)
        first_line = lines[0].strip()

        if first_line == "0":
            return "", 0
        elif first_line == "1":
            thought_content = lines[1].strip() if len(lines) > 1 else ""
            return thought_content, 1
        elif response.startswith("0"):
            return "", 0
        elif response.startswith("1"):
            # 处理 "1[内容]" 格式
            rest = response[1:].strip()
            return rest, 1

        # 无法解析时默认视为有效
        return response, 1

    def _rebuild_embeddings(self) -> None:
        """重建所有条目的嵌入向量缓存"""
        all_items = self.store.get_all_items()
        if not all_items:
            self._cached_embeddings = None
            self._id_to_index = {}
            return

        texts = [item["content"] for item in all_items]
        ids = [item["id"] for item in all_items]

        self._cached_embeddings = self.embedding_engine.encode(texts)
        self._id_to_index = {ids[i]: i for i in range(len(ids))}

        # 同时保存到磁盘
        self.store.save_embeddings(self._cached_embeddings)

    def stats(self) -> dict:
        """
        获取思想记忆的统计信息

        Returns:
            包含以下字段的字典:
                - total_thoughts: 思想总数
                - total_knowledge: 知识块总数
                - abstraction_distribution: 抽象层级分布
                - storage_path: 存储路径
        """
        # 计算抽象层级分布
        abstraction_dist = {}
        all_items = self.store.get_all_items()
        for item in all_items:
            level = item.get("abstraction_level", 1)
            abstraction_dist[level] = abstraction_dist.get(level, 0) + 1

        return {
            "total_thoughts": self.store.thought_count,
            "total_knowledge": self.store.knowledge_count,
            "total_items": self.store.total_items,
            "abstraction_distribution": abstraction_dist,
            "storage_path": str(self.config.thoughts_dir),
            "embedding_backend": self.embedding_engine.backend_name,
            "config": self.config.to_dict(),
        }

    def export_thoughts(self, file_path: Optional[str] = None) -> str:
        """
        导出所有思想为可读的Markdown格式

        Args:
            file_path: 导出文件路径（可选，默认在thoughts目录下）

        Returns:
            导出文件的绝对路径
        """
        if file_path is None:
            file_path = str(self.config.thoughts_dir / "thoughts_export.md")

        all_items = self.store.get_all_items()
        # 按类型和抽象层级排序
        thoughts = [i for i in all_items if i["type"] == "thought"]
        knowledge = [i for i in all_items if i["type"] == "knowledge"]

        lines = [
            "# Thought-Retriever 思想记忆导出",
            f"",
            f"## 统计",
            f"- 思想总数: {len(thoughts)}",
            f"- 知识块总数: {len(knowledge)}",
            f"- 总数: {len(all_items)}",
            f"",
            f"## 知识库 ({len(knowledge)} 条)",
            f"",
        ]

        for item in knowledge:
            lines.append(f"### {item['id']}")
            lines.append(f"")
            lines.append(item["content"])
            lines.append(f"")

        lines.append(f"## 思想库 ({len(thoughts)} 条)")
        lines.append(f"")

        # 按抽象层级分组
        by_level = {}
        for t in thoughts:
            level = t.get("abstraction_level", 1)
            by_level.setdefault(level, []).append(t)

        for level in sorted(by_level.keys()):
            lines.append(f"### 抽象层级 L={level} ({len(by_level[level])} 条)")
            lines.append(f"")
            for t in by_level[level]:
                thought_obj = self.store.get_thought(t["id"])
                lines.append(f"#### {t['id']}")
                lines.append(f"")
                lines.append(t["content"])
                if thought_obj and thought_obj.source_query:
                    lines.append(f"")
                    lines.append(f"> 来源查询: {thought_obj.source_query}")
                lines.append(f"")

        content = "\n".join(lines)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(Path(file_path).resolve())

    def clear(self) -> dict:
        """
        清空所有思想和知识数据

        Returns:
            清空前后的统计对比
        """
        before = self.stats()
        thought_count = self.store.clear_thoughts()
        # 清除知识块
        for kid in list(self.store._knowledge.keys()):
            del self.store._knowledge[kid]
        self.store._save_knowledge()
        self._cached_embeddings = None
        self._id_to_index = {}
        after = self.stats()
        return {"before": before, "after": after, "cleared_thoughts": thought_count}