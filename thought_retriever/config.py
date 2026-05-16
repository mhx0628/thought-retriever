"""
配置管理模块
管理与论文一致的默认参数配置
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ThoughtConfig:
    """
    Thought-Retriever 配置类

    对应论文中的关键参数:
        - top_k (K): 检索返回条目数, 论文默认 K=8
        - similarity_threshold (ε): 思想冗余判断阈值, 论文默认 ε=0.85
        - chunk_size: 原始数据分块大小(token数), 论文默认 500
        - max_context_tokens: 最大上下文长度, 论文默认 2000

    Attributes:
        project_path: 项目根目录路径, 思想数据将存储在 {project_path}/.thoughts/
        top_k: 每次检索返回的条目数
        similarity_threshold: 余弦相似度判断冗余的阈值
        chunk_size: 知识分块大小(token数近似值)
        max_context_tokens: 最大上下文token数
        embedding_model: sentence-transformers 模型名称
        thoughts_dir_name: 思想存储目录名(相对于project_path)
    """

    project_path: str = "."
    top_k: int = 8
    similarity_threshold: float = 0.85
    chunk_size: int = 500
    max_context_tokens: int = 2000
    embedding_model: str = "all-MiniLM-L6-v2"
    thoughts_dir_name: str = ".thoughts"

    @property
    def thoughts_dir(self) -> Path:
        """获取思想存储目录的绝对路径"""
        return Path(self.project_path).resolve() / self.thoughts_dir_name

    @property
    def thoughts_file(self) -> Path:
        """获取思想数据JSON文件的路径"""
        return self.thoughts_dir / "thoughts.json"

    @property
    def knowledge_file(self) -> Path:
        """获取外部知识JSON文件的路径"""
        return self.thoughts_dir / "knowledge.json"

    @property
    def embeddings_file(self) -> Path:
        """获取嵌入向量缓存文件的路径"""
        return self.thoughts_dir / "embeddings.npy"

    @property
    def config_file(self) -> Path:
        """获取配置文件路径"""
        return self.thoughts_dir / "config.json"

    def to_dict(self) -> dict:
        """将配置序列化为字典"""
        return {
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "chunk_size": self.chunk_size,
            "max_context_tokens": self.max_context_tokens,
            "embedding_model": self.embedding_model,
        }

    @classmethod
    def from_dict(cls, data: dict, project_path: str = ".") -> "ThoughtConfig":
        """从字典创建配置对象"""
        return cls(
            project_path=project_path,
            top_k=data.get("top_k", 8),
            similarity_threshold=data.get("similarity_threshold", 0.85),
            chunk_size=data.get("chunk_size", 500),
            max_context_tokens=data.get("max_context_tokens", 2000),
            embedding_model=data.get("embedding_model", "all-MiniLM-L6-v2"),
        )