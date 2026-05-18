<p align="center">
  <img src="https://img.shields.io/badge/Paper-TMLR%202026-blue" alt="TMLR 2026"/>
  <img src="https://img.shields.io/badge/License-Apache%202.0-green" alt="Apache 2.0"/>
  <img src="https://img.shields.io/badge/Python-3.8%2B-orange" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/arXiv-2604.12231-red" alt="arXiv"/>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文文档-🇨🇳-lightgrey" alt="中文"/></a>
</p>

<h1 align="center">🧠 Thought-Retriever</h1>
<h3 align="center">Don't Just Retrieve Raw Data — Retrieve Thoughts</h3>
<p align="center"><em>A self-evolving long-term memory system for LLM-based agents</em></p>

---

## 🎯 What is Thought-Retriever?

**Thought-Retriever** is a universal, model-agnostic memory module for LLM-based agents. Instead of simply retrieving raw text chunks like traditional RAG, it **retrieves "thoughts"** — distilled, validated reasoning abstractions extracted from past LLM interactions.

This approach enables AI agents to:

- **Escape the context window prison** — no longer limited by token budgets
- **Self-evolve** — the more queries you process, the smarter the memory gets
- **Think in hierarchies** — shallow facts for concrete questions, deep insights for abstract ones
- **Filter out noise** — dual filters for confidence (anti-hallucination) and redundancy (anti-duplication)

Built on the paper by **UIUC, MIT & CMU**, published in **Transactions on Machine Learning Research (TMLR) 2026**.

> 📄 **Paper**: [arXiv:2604.12231](https://arxiv.org/abs/2604.12231) — *"Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts for Memory-Augmented Agentic Systems"*

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🧠 **Thought Memory** | Distills Q&A into reusable "knowledge diamonds" |
| 🔄 **Self-Evolving** | Performance scales with the number of accumulated thoughts |
| 🎚 **Abstraction Hierarchy** | Shallow thoughts for facts, deep thoughts for abstract reasoning |
| 🛡 **Dual Filters** | Confidence (ci) + Redundancy (si) = clean, reliable memory |
| 🔌 **Model-Agnostic** | Works with any LLM API or local model |
| 🌐 **Offline-First** | Falls back from sentence-transformers → TF-IDF → pure-Python hash embeddings |
| 📁 **Zero Database** | Pure JSON persistence — no DBMS required |
| 📦 **pip Installable** | Import as a Python package in any project |
| 🇨🇳 **Chinese Optimized** | jieba tokenization + Chinese prompt templates, 3-5x better for Chinese |
| 🧹 **Smart Filtering** | Auto-skip meaningless messages, clean LLM output labels |

---

## 🏗 Architecture

```
User Query
    │
    ▼
┌─────────────────┐
│ 1. Thought      │◄──── Thought Memory (T) + External Knowledge (K)
│    Retrieval    │       Ti ← R(Qi, K ∪ T)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Answer       │       Ai ← L(Qi, Ti)
│    Generation   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Thought &    │       Ti, ci ← L(Qi, Ai)
│    Confidence   │       (anti-hallucination filter)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Thought      │       si ← 1{sim(Ti, Kj/Tm) ≥ ε}
│    Merge        │       (anti-redundancy filter)
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Memory       │       T ← T ∪ Ti, if ci=1 ∧ si=0
│    Update       │
└─────────────────┘
```

---

## 🚀 Quick Start

### Installation

```bash
pip install thought-retriever
# Or install dependencies manually:
pip install numpy jieba
# For semantic embeddings (recommended):
pip install sentence-transformers scikit-learn
# The system auto-falls back to TF-IDF or pure-Python hashing
```

### Basic Usage

```python
from thought_retriever import ThoughtMemory

# Initialize with project-aware storage (creates .thoughts/)
memory = ThoughtMemory(project_path="./my_project")

# Add external knowledge
memory.add_knowledge("""
The project uses microservices architecture deployed with Docker + Kubernetes.
PostgreSQL is the primary database, Redis handles caching.
""")

# Directly log a design decision as a thought
memory.add_thought_directly(
    content="Database connection pooling: use SQLAlchemy QueuePool with "
            "pool_size=20, max_overflow=10, fronted by pgbouncer",
    source_query="How to configure PostgreSQL connection pooling?",
    metadata={"category": "database", "status": "verified"}
)

# Retrieve relevant thoughts for a new query
results = memory.retrieve("database connection pooling", top_k=5)
for r in results:
    print(f"[{r['type']}] (score={r['score']:.2f}, level={r['abstraction_level']})")
    print(f"  {r['content'][:80]}...")
```

### Chinese Usage

```python
from thought_retriever import ThoughtConfig, ThoughtMemory

# Recommended config for Chinese
config = ThoughtConfig(
    project_path="./my_project",
    language="zh",  # Use Chinese prompt templates
)
memory = ThoughtMemory(config=config)

# Add Chinese knowledge
memory.add_knowledge("小明今年10岁，喜欢画画和踢足球")

# Retrieve Chinese memories
results = memory.retrieve("小明喜欢什么")
```

### Full Pipeline with an LLM

```python
from thought_retriever import ThoughtMemory

memory = ThoughtMemory(project_path=".")

def my_llm(prompt: str) -> str:
    """Replace this with your LLM API call."""
    return "Your LLM answer here..."

answer, new_thoughts = memory.process_query(
    query="What's the best caching strategy for Redis?",
    generate_answer_fn=my_llm,
    generate_thought_fn=my_llm,
)

print(f"Answer: {answer}")
print(f"New thoughts stored: {len(new_thoughts)}")

# Check stats
print(memory.stats())
```

---

## 📊 Config Reference

| Parameter | Default | Paper Equivalent | Description |
|-----------|---------|-----------------|-------------|
| `top_k` | 8 | K | Number of items retrieved per query |
| `similarity_threshold` | 0.85 | ε | Cosine similarity threshold for redundancy detection |
| `chunk_size` | 500 | — | Token budget for text chunking |
| `max_context_tokens` | 2000 | — | LLM context window limit |
| `embedding_model` | `all-MiniLM-L6-v2` | Contriever | Sentence transformer model name |
| `language` | `auto` | — | Language setting (auto/zh/en), affects prompt template selection |
| `thought_prompt_lang` | `auto` | — | Thought generation prompt language |

```python
from thought_retriever import ThoughtConfig, ThoughtMemory

config = ThoughtConfig(
    project_path=".",
    top_k=10,
    similarity_threshold=0.90,
)
memory = ThoughtMemory(config=config)
```

---

## 📦 Project Structure

```
thought-retriever/
├── thought_retriever/          # Python package
│   ├── __init__.py             # Public API exports
│   ├── thought_memory.py       # Core: 5-step pipeline orchestrator
│   ├── thought_store.py        # Persistence: JSON-backed storage
│   ├── embedding.py            # Embedding: 3-tier fallback engine
│   ├── retriever.py            # Retrieval: K ∪ T search
│   ├── confidence.py           # Filter 1: Confidence evaluation
│   ├── merger.py               # Filter 2: Redundancy detection
│   ├── config.py               # Configuration dataclass
│   ├── utils.py                # Utilities (chunking, IDs, abstraction)
│   └── templates/
│       └── prompts.py          # LLM prompt templates
├── paper/                      # Original paper (arXiv:2604.12231)
│   └── 2604.12231v1.pdf
├── .trae/skills/thought-retriever/  # Trae AI IDE skill
│   └── SKILL.md
├── README.md                   # This file
├── README_ZH.md                # 中文文档
├── CHANGELOG.md                # Version changelog
├── LICENSE                     # Apache 2.0
└── setup.py                    # pip install support
```

---

## 🔬 Paper Findings Validated in Code

| Finding | Details |
|---------|---------|
| 📈 **Self-Evolution** | F1 score increases with the number of accumulated thoughts (a new scaling law for agents) |
| 🎯 **Abstraction Alignment** | Abstract queries retrieve deeper thoughts (higher L value) |
| 🛡 **Filter Robustness** | Even with low-quality thoughts injected, system performance remains stable |
| 🔄 **Cross-Model Transfer** | Thoughts generated by one LLM can be leveraged by another |
| 🏆 **SOTA Performance** | +7.6% F1 / +16% Win Rate over baselines on AcademicEval |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📄 License

- **Code**: Apache 2.0 — free for commercial and personal use
- **Paper**: The original PDF (`paper/2604.12231v1.pdf`) is hosted on arXiv under standard arXiv distribution terms. arXiv allows redistribution of the PDF for non-commercial purposes with proper attribution. The paper is copyright by its authors and TMLR.

---

## 📚 Citation

```bibtex
@article{feng2026thoughtretriever,
  title={Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts for Memory-Augmented Agentic Systems},
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
  <a href="https://github.com/ulab-uiuc/Thought-Retriever">GitHub</a> ·
  <a href="https://arxiv.org/abs/2604.12231">arXiv</a> ·
  <a href="https://openreview.net/forum?id=emCcuhtENL">OpenReview</a>
</p>