"""
提示词模板模块
基于论文附录A.2中的提示词设计，适配通用开发场景

包含:
    - 思想与置信度生成提示 (对应论文Figure 3)
    - 答案生成提示
    - 查询改写提示
"""

import re


def _detect_language(text: str) -> str:
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_chars = len(text.replace(' ', '').replace('\n', ''))
    if total_chars > 0 and zh_chars / total_chars > 0.15:
        return "zh"
    return "en"


def thought_confidence_prompt_zh(query: str, answer: str) -> str:
    return f"""给定问题：{query}
给定答案：{answer}

请根据提供的问题及其对应答案，执行以下步骤：

步骤1：判断答案是否为实际回答，还是仅表示因信息不足无法回答。如果是后者，只输出'0'，不加任何多余文字；否则输出'1'。

步骤2：如果是有效答案，请将问题和答案简洁地总结为一个连贯的知识点，形成一段流畅的文字。知识点应捕捉核心见解、推理逻辑或决策原则。

输出格式（如果有效）：
1
[你总结的知识点]

输出格式（如果无效）：
0"""


def answer_generation_prompt_zh(query: str, context: str) -> str:
    return f"""请根据以下检索到的上下文回答问题。

上下文：
{context}

问题：{query}

请仅根据上下文中的信息提供清晰、简洁的回答。如果上下文信息不足以回答问题，请明确说明。"""


def thought_confidence_prompt(query: str, answer: str, lang: str = "auto") -> str:
    if lang == "auto":
        lang = _detect_language(query + answer)
    if lang == "zh":
        return thought_confidence_prompt_zh(query, answer)
    return f"""Given question: {query}
Given answer: {answer}

Based on the provided question and its corresponding answer, perform the following steps:

Step 1: Determine if the answer is an actual answer or if it merely indicates that the question cannot be answered due to insufficient information. If the latter is true, just output '0' without any extra words, otherwise output '1'.

Step 2: If it is a valid answer, succinctly summarize both the question and answer into a coherent knowledge point, forming a fluent passage. The knowledge point should capture the core insight, reasoning logic, or decision principle.

Output format (if valid):
1
[Your summarized knowledge point here]

Output format (if invalid):
0"""


def answer_generation_prompt(query: str, context: str, lang: str = "auto") -> str:
    if lang == "auto":
        lang = _detect_language(query)
    if lang == "zh":
        return answer_generation_prompt_zh(query, context)
    return f"""Based on the following retrieved context, please answer the question.

Context:
{context}

Question: {query}

Please provide a clear, concise answer based solely on the information in the context. If the context does not contain sufficient information to answer the question, state that clearly."""


def query_rewrite_prompt(query: str) -> str:
    """
    查询改写提示模板

    将用户原始查询改写为更适合检索的格式

    Args:
        query: 原始用户查询

    Returns:
        格式化的提示词字符串
    """
    return f"""Rewrite the following query to be more suitable for semantic search retrieval.
Focus on extracting key concepts and technical terms.

Original query: {query}

Rewritten query:"""


def thought_merge_prompt(new_thought: str, existing_thought: str) -> str:
    """
    思想合并判断提示模板

    当新思想与已有思想高度相似时，判断是否可以合并

    Args:
        new_thought: 新生成的思想
        existing_thought: 已存在的相似思想

    Returns:
        格式化的提示词字符串
    """
    return f"""Compare the following two knowledge points and determine if they convey the same core information.

Knowledge Point 1: {new_thought}

Knowledge Point 2: {existing_thought}

Are these two knowledge points semantically equivalent or highly overlapping? Answer only 'yes' or 'no'."""