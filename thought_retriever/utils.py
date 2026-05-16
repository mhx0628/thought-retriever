"""
工具函数模块
提供分块、哈希、时间戳等通用工具函数
"""

import hashlib
from datetime import datetime, timezone
from typing import List


def generate_id(content: str, prefix: str = "T") -> str:
    """
    基于内容生成唯一ID

    使用SHA256哈希的前12位作为ID，保证相同内容生成相同ID（幂等性）

    Args:
        content: 用于生成ID的内容字符串
        prefix: ID前缀，'T'=Thought, 'K'=Knowledge

    Returns:
        格式为 {prefix}_{hash} 的唯一标识符
    """
    hash_hex = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{hash_hex}"


def timestamp_now() -> str:
    """
    获取当前UTC时间的ISO格式字符串

    Returns:
        ISO 8601格式的时间戳字符串
    """
    return datetime.now(timezone.utc).isoformat()


def chunk_text(text: str, chunk_size: int = 500) -> List[str]:
    """
    将长文本按chunk_size分割为数据块

    按段落边界优先分割，若段落过长则进一步按句子分割

    Args:
        text: 待分割的原始文本
        chunk_size: 每块的最大字符数（近似token数）

    Returns:
        分割后的文本块列表
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    paragraphs = text.split("\n")

    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 如果当前块加上新段落不超过chunk_size，则合并
        if len(current_chunk) + len(para) <= chunk_size:
            current_chunk = (current_chunk + "\n" + para).strip()
        else:
            # 保存当前块
            if current_chunk:
                chunks.append(current_chunk)

            # 如果单段超过chunk_size，按句子分割
            if len(para) > chunk_size:
                sentences = para.replace("。", "。\n").replace(". ", ".\n").split("\n")
                sub_chunk = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(sub_chunk) + len(sent) <= chunk_size:
                        sub_chunk = (sub_chunk + " " + sent).strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sent
                if sub_chunk:
                    current_chunk = sub_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def compute_abstraction_level(source_levels: List[int]) -> int:
    """
    递归计算思想的抽象层级

    对应论文公式: L(T) = 1 + (1/|R_T|) * Σ L(r), r ∈ R_T

    Args:
        source_levels: 来源条目的抽象层级列表

    Returns:
        计算后的抽象层级（整数）
    """
    if not source_levels:
        return 2  # 无来源时默认为一级思想
    avg = sum(source_levels) / len(source_levels)
    return int(avg) + 1


def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量

    使用简单的中英文混合估算: 英文约4字符/token, 中文约1.5字符/token

    Args:
        text: 待估算的文本

    Returns:
        估算的token数量
    """
    chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)