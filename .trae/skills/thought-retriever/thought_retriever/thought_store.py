"""
思想存储层模块
负责思想的JSON文件持久化存储与读取

存储结构:
    {project_path}/.thoughts/
    ├── thoughts.json      # 思想数据（不含嵌入向量）
    ├── knowledge.json     # 外部知识数据
    ├── embeddings.npy     # 嵌入向量（numpy数组）
    └── config.json        # 配置快照

数据格式:
    Thought = {
        "id": "T_xxx",
        "content": "思想内容",
        "source_query": "原始查询",
        "source_answer": "原始回答",
        "abstraction_level": 2,
        "sources": ["K_xxx", "T_yyy"],
        "confidence": 1,
        "timestamp": "ISO时间戳",
        "metadata": {}
    }
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from .config import ThoughtConfig
from .utils import generate_id, timestamp_now


@dataclass
class KnowledgeChunk:
    """
    外部知识块数据结构

    Attributes:
        id: 知识块唯一标识 (K_ 前缀)
        content: 知识块文本内容
        timestamp: 创建时间戳
        metadata: 附加元数据
    """

    id: str
    content: str
    timestamp: str = field(default_factory=timestamp_now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Thought:
    """
    思想数据结构

    对应论文中的 Thought (Ti) 定义:
        - 查询条件化 (Query-Conditioned): 捕获查询与数据之间的逻辑联系
        - 抽象性 (Abstractive): 从原始对话中提炼连贯的知识点
        - 已验证 (Validated): 通过置信度检查(ci)和新颖性检查(si)

    Attributes:
        id: 思想唯一标识 (T_ 前缀)
        content: 思想内容（提炼后的知识点）
        source_query: 生成该思想的原始查询
        source_answer: 生成该思想的原始回答
        abstraction_level: 抽象层级（原始数据=1，一级思想=2，以此类推）
        sources: 来源ID列表（根溯源映射 Ô(T)）
        confidence: 置信度标记（1=有效, 0=无效）
        timestamp: 创建时间戳
        metadata: 附加元数据
    """

    id: str
    content: str
    source_query: str = ""
    source_answer: str = ""
    abstraction_level: int = 2
    sources: List[str] = field(default_factory=list)
    confidence: int = 1
    timestamp: str = field(default_factory=timestamp_now)
    metadata: Dict = field(default_factory=dict)


class ThoughtStore:
    """
    思想持久化存储管理器

    负责:
        - 思想的增删改查
        - 外部知识的管理
        - 嵌入向量的存储与加载
        - 数据文件的自动创建与维护
    """

    def __init__(self, config: ThoughtConfig):
        """
        初始化存储管理器

        Args:
            config: Thought-Retriever 配置对象
        """
        self.config = config
        self._thoughts: Dict[str, Thought] = {}
        self._knowledge: Dict[str, KnowledgeChunk] = {}
        self._embeddings: Optional[np.ndarray] = None
        self._id_to_index: Dict[str, int] = {}

        self._ensure_directory()
        self._load_all()

    def _ensure_directory(self) -> None:
        """确保存储目录存在，不存在则自动创建"""
        self.config.thoughts_dir.mkdir(parents=True, exist_ok=True)

    def _load_all(self) -> None:
        """从磁盘加载所有持久化数据"""
        self._load_thoughts()
        self._load_knowledge()
        self._load_embeddings()
        self._save_config()

    def _load_thoughts(self) -> None:
        """加载思想数据文件"""
        file_path = self.config.thoughts_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    thought = Thought(**item)
                    self._thoughts[thought.id] = thought
            except (json.JSONDecodeError, TypeError):
                self._thoughts = {}

    def _load_knowledge(self) -> None:
        """加载外部知识数据文件"""
        file_path = self.config.knowledge_file
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    chunk = KnowledgeChunk(**item)
                    self._knowledge[chunk.id] = chunk
            except (json.JSONDecodeError, TypeError):
                self._knowledge = {}

    def _load_embeddings(self) -> None:
        """加载嵌入向量缓存"""
        file_path = self.config.embeddings_file
        if file_path.exists():
            try:
                self._embeddings = np.load(file_path)
                # 重建ID到索引的映射
                self._rebuild_id_index()
            except (IOError, ValueError):
                self._embeddings = None
                self._id_to_index = {}

    def _rebuild_id_index(self) -> None:
        """基于所有条目重建ID到嵌入向量索引的映射"""
        self._id_to_index = {}
        idx = 0
        for kid in self._knowledge:
            self._id_to_index[kid] = idx
            idx += 1
        for tid in self._thoughts:
            self._id_to_index[tid] = idx
            idx += 1

    def _save_config(self) -> None:
        """保存配置快照到磁盘"""
        config_data = self.config.to_dict()
        with open(self.config.config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)

    def _save_thoughts(self) -> None:
        """将思想数据持久化到磁盘"""
        data = [asdict(t) for t in self._thoughts.values()]
        with open(self.config.thoughts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _save_knowledge(self) -> None:
        """将知识数据持久化到磁盘"""
        data = [asdict(k) for k in self._knowledge.values()]
        with open(self.config.knowledge_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_embeddings(self, embeddings: np.ndarray) -> None:
        """
        保存嵌入向量到磁盘

        Args:
            embeddings: 嵌入向量矩阵，每行对应一个条目
        """
        self._embeddings = embeddings
        np.save(str(self.config.embeddings_file), embeddings)

    def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> str:
        """
        添加外部知识块

        Args:
            content: 知识内容文本
            metadata: 附加元数据

        Returns:
            新知识块的ID
        """
        kid = generate_id(content, prefix="K")
        if kid in self._knowledge:
            return kid  # 已存在则跳过

        chunk = KnowledgeChunk(
            id=kid,
            content=content,
            metadata=metadata or {},
        )
        self._knowledge[kid] = chunk
        self._save_knowledge()
        return kid

    def add_thought(self, thought: Thought) -> str:
        """
        添加思想到存储

        Args:
            thought: Thought对象

        Returns:
            思想ID
        """
        if thought.id in self._thoughts:
            # 更新已有思想
            self._thoughts[thought.id] = thought
        else:
            self._thoughts[thought.id] = thought
        self._save_thoughts()
        return thought.id

    def get_all_items(self) -> List[Dict]:
        """
        获取所有可检索条目（知识块 + 思想）

        Returns:
            包含id、content、abstraction_level的字典列表
        """
        items = []
        for kid, chunk in self._knowledge.items():
            items.append({
                "id": kid,
                "content": chunk.content,
                "type": "knowledge",
                "abstraction_level": 1,  # 原始数据层级为1
            })
        for tid, thought in self._thoughts.items():
            if thought.confidence == 1:  # 仅包含有效思想
                items.append({
                    "id": tid,
                    "content": thought.content,
                    "type": "thought",
                    "abstraction_level": thought.abstraction_level,
                })
        return items

    def get_thought(self, thought_id: str) -> Optional[Thought]:
        """获取指定思想"""
        return self._thoughts.get(thought_id)

    def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeChunk]:
        """获取指定知识块"""
        return self._knowledge.get(knowledge_id)

    def remove_thought(self, thought_id: str) -> bool:
        """删除指定思想"""
        if thought_id in self._thoughts:
            del self._thoughts[thought_id]
            self._save_thoughts()
            return True
        return False

    def clear_thoughts(self) -> int:
        """清空所有思想，返回删除数量"""
        count = len(self._thoughts)
        self._thoughts.clear()
        self._save_thoughts()
        return count

    @property
    def thought_count(self) -> int:
        """有效思想数量"""
        return len(self._thoughts)

    @property
    def knowledge_count(self) -> int:
        """知识块数量"""
        return len(self._knowledge)

    @property
    def total_items(self) -> int:
        """总条目数"""
        return self.knowledge_count + self.thought_count