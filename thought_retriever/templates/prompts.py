"""
提示词模板模块
基于论文附录A.2中的提示词设计，适配通用开发场景

包含:
    - 思想与置信度生成提示 (对应论文Figure 3)
    - 答案生成提示
    - 查询改写提示
"""


def thought_confidence_prompt(query: str, answer: str) -> str:
    """
    思想与置信度生成提示模板

    对应论文 Figure 3 的提示设计:
        Step 1: 判断答案是否有效 (二值置信度)
        Step 2: 若有效，将问答对提炼为可复用的知识点

    Args:
        query: 用户查询
        answer: LLM生成的答案

    Returns:
        格式化的提示词字符串
    """
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


def answer_generation_prompt(query: str, context: str) -> str:
    """
    答案生成提示模板

    将检索到的上下文与用户查询组合，引导LLM生成答案

    Args:
        query: 用户查询
        context: 检索到的相关上下文（思想+知识块）

    Returns:
        格式化的提示词字符串
    """
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