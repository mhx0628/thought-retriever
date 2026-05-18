---
title: Thought-Retriever
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: static
pinned: true
license: apache-2.0
---

# 🧠 Thought-Retriever

**Don't Just Retrieve Raw Data — Retrieve Thoughts**

A self-evolving long-term memory system for LLM-based agents, based on the paper by **UIUC, MIT & CMU** (TMLR 2026).

## v2.0.0 — Chinese Optimization

- 🇨🇳 **Chinese Embedding Engine**: jieba tokenization + TF-IDF, 3-5x better for Chinese
- 🇨🇳 **Chinese Prompt Templates**: Auto language detection
- 🧹 **Smart Filtering**: Skip meaningless messages, clean LLM output labels
- 🛡 **Robust Parsing**: Support Chinese "是/否/有效/无效"

## Quick Install

```bash
pip install numpy jieba
git clone https://github.com/mhx0628/thought-retriever
```

## Quick Start

```python
from thought_retriever import ThoughtMemory, ThoughtConfig

config = ThoughtConfig(project_path=".", language="zh")
memory = ThoughtMemory(config=config)

memory.add_knowledge("小明今年10岁，喜欢画画和踢足球")
results = memory.retrieve("小明喜欢什么")
```

## Key Features

- 🧠 **Thought Memory**: Distills Q&A into reusable "knowledge diamonds"
- 🔄 **Self-Evolving**: The more queries you process, the smarter the memory gets
- 🎚 **Abstraction Hierarchy**: Shallow facts → deep insights
- 🛡 **Dual Filters**: Anti-hallucination + anti-redundancy
- 🔌 **Model-Agnostic**: Works with any LLM
- 🌐 **Offline-First**: 4-tier fallback embedding engine

## Links

- GitHub: https://github.com/mhx0628/thought-retriever
- Gitee: https://gitee.com/ma-hongxing-1/thought-retriever
- Paper: https://arxiv.org/abs/2604.12231
- CHANGELOG: https://github.com/mhx0628/thought-retriever/blob/main/CHANGELOG.md
