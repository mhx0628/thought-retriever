---
name: "thought-retriever"
description: "基于UIUC/MIT/CMU Thought-Retriever论文的思想记忆系统。将LLM推理过程压缩为'思想钻石'，构建自演进长短期记忆。在项目开发中持续积累和检索高维逻辑思想，避免AI金鱼记忆问题。当需要记录项目决策、积累领域知识、检索历史推理时使用。"
---

# Thought-Retriever - 通用思想记忆系统

基于论文 *"Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts for Memory-Augmented Agentic Systems"* (UIUC/MIT/CMU, TMLR 2026) 实现的通用思想记录与检索框架。

## 核心理念

传统RAG（检索增强生成）受限于上下文窗口物理长度，只能检索top-K原始数据块。Thought-Retriever创新性地提出：**检索"思想"而非原始数据**。

通过将模型历史推理过程压缩为高置信度的"思想钻石"，系统构建起一套自演进的动态长短期记忆机制，并内置双重过滤网以剔除冗余并对抗幻觉。

## 五步流水线

```
用户查询 → [1.思想检索] → [2.答案生成] → [3.思想&置信度生成] → [4.思想合并(去重)] → [5.思想记忆更新]
              ↑                                                                    |
              └────────────────── 思想记忆库 (持久化) ←────────────────────────────┘
```

### 1. Thought Retrieval (思想检索)
从外部知识库 + 思想记忆中检索最相关的top-K条目（基于嵌入向量余弦相似度）

### 2. Answer Generation (答案生成)
LLM基于检索到的信息生成答案

### 3. Thought & Confidence Generation (思想与置信度生成)
LLM从(Q, A)对中提炼可复用的"知识点"，同时输出二值置信度(0/1)判断思想是否有效

### 4. Thought Merge (思想合并)
计算新思想与已有思想的余弦相似度，若超过阈值(默认0.85)则标记为冗余

### 5. Thought Memory Update (思想记忆更新)
仅保留 ci=1（有效）且 si=0（非冗余）的思想，存入记忆库

## 抽象层级计算

- 原始数据块：L(K) = 1
- 从原始数据派生的思想：L(T) = 2
- 从多级思想派生的思想：L(T) = 1 + avg(source_levels)
- 更抽象的问题倾向于检索更高抽象层级的思想

## 安装使用

```bash
# 安装依赖
pip install sentence-transformers numpy

# 在任何Python项目中使用
from thought_retriever import ThoughtMemory

# 初始化思想记忆
memory = ThoughtMemory(project_path=".")

# 添加外部知识（项目文档、代码规范等）
memory.add_knowledge("项目的核心架构采用微服务设计...")

# 处理查询，自动生成并存储思想
answer, new_thoughts = memory.process_query(
    query="如何设计数据库连接池？",
    generate_answer_fn=your_llm_function
)

# 检索相关思想
thoughts = memory.retrieve("数据库性能优化", top_k=5)

# 查看统计
print(memory.stats())
```

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | 8 | 每次检索返回的条目数 |
| `similarity_threshold` | 0.85 | 思想冗余判断阈值 |
| `chunk_size` | 500 | 知识分块大小(tokens) |
| `max_context_tokens` | 2000 | 最大上下文长度 |

## 使用场景

1. **项目开发**：记录架构决策、设计模式选择、Bug修复思路
2. **代码审查**：积累审查经验，自动检索相关历史Review意见
3. **文档编写**：从历史讨论中提取最佳实践
4. **知识管理**：将会议讨论、技术分享转化为结构化思想
5. **AI辅助编程**：为AI Agent提供项目专属的长期记忆

## 目录结构

```
.trae/skills/thought-retriever/
├── SKILL.md                        # 本文件
└── thought_retriever/
    ├── __init__.py                 # 包入口，导出主要API
    ├── thought_memory.py           # 核心：思想记忆管理主类
    ├── thought_store.py            # 存储层：JSON文件持久化
    ├── embedding.py                # 嵌入层：向量化与相似度搜索
    ├── retriever.py                # 检索层：多源检索
    ├── confidence.py               # 置信度过滤与质量评估
    ├── merger.py                   # 冗余检测与合并模块
    ├── config.py                   # 配置管理
    ├── utils.py                    # 工具函数
    └── templates/
        └── prompts.py              # 提示词模板
```