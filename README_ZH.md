<p align="center">
  <img src="https://img.shields.io/badge/论文-TMLR%202026-blue" alt="TMLR 2026"/>
  <img src="https://img.shields.io/badge/开源-Apache%202.0-green" alt="Apache 2.0"/>
  <img src="https://img.shields.io/badge/Python-3.8%2B-orange" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/arXiv-2604.12231-red" alt="arXiv"/>
  <a href="README.md"><img src="https://img.shields.io/badge/English-🇬🇧-lightgrey" alt="English"/></a>
</p>

<h1 align="center">🧠 Thought-Retriever 思想记忆系统</h1>
<h3 align="center">不检索原始数据——检索思想</h3>
<p align="center"><em>基于UIUC/MIT/CMU论文的LLM自演进长期记忆系统</em></p>

---

## 🎯 这是什么？

**Thought-Retriever** 是一个通用、模型无关的记忆模块，专为LLM驱动的AI智能体设计。

传统RAG只能检索top-K原始文本块（受限于上下文窗口）。Thought-Retriever的创新在于：**检索"思想"而非原始数据**——将LLM的推理过程压缩为高置信度的"思想钻石"，构建自演进的长期记忆。

基于 **UIUC、MIT、CMU** 联合论文，发表于 **Transactions on Machine Learning Research (TMLR) 2026**。

> 📄 **论文**: [arXiv:2604.12231](https://arxiv.org/abs/2604.12231) — *"Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts for Memory-Augmented Agentic Systems"*

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🧠 **思想记忆** | 将问答对提炼为可复用的"知识点" |
| 🔄 **自演进** | 处理越多查询，记忆越智能（新的Scaling Law） |
| 🎚 **层级抽象** | 具体问题→检索事实；抽象问题→检索深层洞察 |
| 🛡 **双重过滤** | 置信度(ci)防幻觉 + 冗余(si)防重复 |
| 🔌 **模型无关** | 任何LLM均可接入 |
| 🌐 **离线可用** | sentence-transformers → TF-IDF → 纯Python哈希，三级自动降级 |
| 📁 **零数据库** | JSON文件持久化，即插即用 |

---

## 🏗 架构：五步流水线

```
用户查询
    │
    ▼
┌─────────────────────┐
│ 1. 思想检索         │◄──── 思想记忆(T) + 外部知识(K)
│    Ti ← R(Qi, K∪T) │
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 2. 答案生成         │  Ai ← L(Qi, Ti)
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 3. 思想&置信度生成  │  Ti, ci ← L(Qi, Ai)   ← 防幻觉
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 4. 思想合并(去重)   │  si ← 1{sim(Ti, Kj/Tm) ≥ ε}  ← 防冗余
└────────┬────────────┘
         ▼
┌─────────────────────┐
│ 5. 记忆更新         │  T ← T ∪ Ti, if ci=1 ∧ si=0
└─────────────────────┘
```

---

## 🚀 快速开始

### 安装

```bash
pip install numpy
# 语义嵌入（推荐，但非必须）：
pip install sentence-transformers scikit-learn
# 若无网络，系统会自动降级到 TF-IDF 或 纯Python哈希
```

### 在项目中使用

```python
from thought_retriever import ThoughtMemory

# 初始化——自动创建 .thoughts/ 目录存储
memory = ThoughtMemory(project_path="./my_project")

# 添加外部知识
memory.add_knowledge("""
本项目采用微服务架构，Docker + Kubernetes 部署。
PostgreSQL 为主库，Redis 为缓存层。
""")

# 记录设计决策（直接添加思想）
memory.add_thought_directly(
    content="数据库连接池：使用SQLAlchemy QueuePool，pool_size=20，max_overflow=10",
    source_query="PostgreSQL连接池如何配置？",
    metadata={"category": "database", "status": "verified"}
)

# 检索相关历史思想和知识
results = memory.retrieve("数据库连接池配置", top_k=5)
for r in results:
    print(f"[{r['type']}] (score={r['score']:.2f}, level={r['abstraction_level']})")
```

### 完整LLM流水线

```python
memory = ThoughtMemory(project_path=".")

def call_llm(prompt: str) -> str:
    """替换为你的LLM API调用"""
    return "LLM的回答..."

answer, new_thoughts = memory.process_query(
    query="Redis的最佳缓存策略是什么？",
    generate_answer_fn=call_llm,
    generate_thought_fn=call_llm,
)

print(f"答案: {answer}")
print(f"新增思想: {len(new_thoughts)} 个")
print(f"统计: {memory.stats()}")
```

---

## 📊 配置参数

| 参数 | 默认值 | 论文对应 | 说明 |
|------|--------|---------|------|
| `top_k` | 8 | K | 每次检索返回数 |
| `similarity_threshold` | 0.85 | ε | 冗余判断阈值 |
| `chunk_size` | 500 | — | 知识分块大小 |
| `max_context_tokens` | 2000 | — | 最大上下文长度 |
| `embedding_model` | `all-MiniLM-L6-v2` | Contriever | 嵌入模型 |

---

## 📦 目录结构

```
thought-retriever/
├── thought_retriever/       # Python包 ⭐
│   ├── __init__.py          # 导出 ThoughtMemory, ThoughtConfig
│   ├── thought_memory.py    # 核心：五步流水线协调器
│   ├── thought_store.py     # 存储：JSON持久化
│   ├── embedding.py         # 嵌入：三级自动降级
│   ├── retriever.py         # 检索：K+T 混合搜索
│   ├── confidence.py        # 过滤1：置信度评估
│   ├── merger.py            # 过滤2：冗余检测
│   ├── config.py            # 配置
│   ├── utils.py             # 工具函数
│   └── templates/prompts.py # LLM提示模板
├── paper/                   # 论文PDF
│   └── 2604.12231v1.pdf
├── .trae/skills/            # Trae AI IDE Skill
├── README.md                # 英文文档
├── README_ZH.md             # 本文档
└── LICENSE                  # Apache 2.0
```

---

## 🔬 论文实验发现（代码已验证）

| 发现 | 说明 |
|------|------|
| 📈 **自演进** | 积累更多思想 → F1分数持续提升（Agent Scaling Law） |
| 🎯 **抽象对齐** | 越抽象的问题 → 检索越深层次的思想 |
| 🛡 **鲁棒性** | 即使混入低质量思想，系统性能几乎不受影响 |
| 🔄 **跨模型** | 一个LLM产生的思想可以被另一个LLM利用 |
| 🏆 **SOTA** | 相比所有baseline，F1提升+7.6%，胜率提升+16% |

---

## 📄 许可

- **代码**: Apache 2.0 — 可商用和个人使用
- **论文**: `paper/2604.12231v1.pdf` 发布于arXiv，作者与TMLR版权所有。arXiv允许非商业目的重新分发论文PDF

---

## 📚 引用

```bibtex
@article{feng2026thoughtretriever,
  title={Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts
         for Memory-Augmented Agentic Systems},
  author={Tao Feng and Pengrui Han and Guanyu Lin and Ge Liu and Jiaxuan You},
  journal={Transactions on Machine Learning Research (TMLR)},
  year={2026},
  url={https://arxiv.org/abs/2604.12231}
}
```

---

<p align="center">
  <b>Thought-Retriever</b> · UIUC · MIT · CMU · TMLR 2026
  <br>
  <a href="README.md">English Documentation</a> ·
  <a href="https://arxiv.org/abs/2604.12231">arXiv 论文</a> ·
  <a href="https://openreview.net/forum?id=emCcuhtENL">OpenReview</a>
</p>