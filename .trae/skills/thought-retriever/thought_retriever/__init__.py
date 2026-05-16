"""
Thought-Retriever 包初始化模块
基于论文 "Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts"
(UIUC/MIT/CMU, TMLR 2026) 实现的通用思想记忆系统

主要导出:
    - ThoughtMemory: 核心思想记忆管理类（推荐入口）
    - ThoughtConfig: 配置类
    - Thought: 思想数据类
"""

from .thought_memory import ThoughtMemory
from .config import ThoughtConfig
from .thought_store import Thought

__all__ = ["ThoughtMemory", "ThoughtConfig", "Thought"]
__version__ = "1.0.0"