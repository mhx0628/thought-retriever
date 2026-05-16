"""
置信度过滤模块
实现论文中的双重过滤机制之一: 置信度检查

对应论文 Algorithm 1 中的 Step 6: Ti, ci ← L(Qi, Ai)
输出二值置信度: ci=1 表示思想有效, ci=0 表示无效/幻觉
"""

from typing import Callable, Optional, Tuple


class ConfidenceFilter:
    """
    置信度过滤器

    负责判断生成的思想是否有效（非幻觉、有意义）

    论文中的设计:
        - ci 是离散二值: 1=有意义, 0=无意义或幻觉
        - 通过特殊提示词让LLM自我评估
        - 人类验证: 与人工判断一致率达96%（Abstract-single）和93%（Related-multi）

    支持两种模式:
        1. LLM评估模式: 使用LLM进行自我评估（推荐）
        2. 启发式模式: 基于规则的快速筛选（备用）
    """

    def __init__(self, llm_fn: Optional[Callable] = None):
        """
        初始化置信度过滤器

        Args:
            llm_fn: LLM调用函数，签名为 fn(prompt: str) -> str
                    若为None则使用启发式模式
        """
        self.llm_fn = llm_fn

    def evaluate(
        self, query: str, answer: str, thought_content: str
    ) -> Tuple[int, str]:
        """
        评估思想的质量和置信度

        对应论文 Figure 3 提示模板的完整流程

        Args:
            query: 用户查询
            answer: 生成的答案
            thought_content: 提炼的思想内容

        Returns:
            (confidence, reason):
                confidence: 1=有效, 0=无效
                reason: 判断依据
        """
        if self.llm_fn:
            return self._llm_evaluate(query, answer, thought_content)
        else:
            return self._heuristic_evaluate(query, answer, thought_content)

    def _llm_evaluate(
        self, query: str, answer: str, thought_content: str
    ) -> Tuple[int, str]:
        """
        使用LLM进行置信度评估

        发送专门设计的提示词让LLM判断答案是否有效且有意义

        Args:
            query: 用户查询
            answer: 生成的答案
            thought_content: 提炼的思想内容

        Returns:
            (confidence, reason)
        """
        from .templates.prompts import thought_confidence_prompt

        prompt = thought_confidence_prompt(query, answer)
        response = self.llm_fn(prompt).strip()

        # 解析LLM输出
        if response.startswith("0"):
            return 0, "LLM判定为无效答案或无意义内容"
        elif response.startswith("1"):
            return 1, "LLM判定为有效答案"
        else:
            # 无法解析时默认视为有效
            return 1, "LLM返回格式异常，默认视为有效"

    def _heuristic_evaluate(
        self, query: str, answer: str, thought_content: str
    ) -> Tuple[int, str]:
        """
        基于启发式规则的置信度评估

        备用方案，不依赖LLM API调用

        规则:
            - 答案过短 (<10字符) → 无效
            - 答案包含"无法回答"/"信息不足" → 无效
            - 思想内容为空 → 无效
            - 思想与查询完全不相关 → 无效

        Args:
            query: 用户查询
            answer: 生成的答案
            thought_content: 提炼的思想内容

        Returns:
            (confidence, reason)
        """
        # 规则1: 答案过短
        if len(answer.strip()) < 10:
            return 0, "答案过短（<10字符）"

        # 规则2: 答案包含无法回答的提示
        unable_keywords = ["无法回答", "信息不足", "insufficient information",
                          "cannot answer", "unable to", "not enough"]
        answer_lower = answer.lower()
        for kw in unable_keywords:
            if kw.lower() in answer_lower:
                return 0, f"答案包含否定关键词: {kw}"

        # 规则3: 思想内容不能为空
        if not thought_content or len(thought_content.strip()) < 10:
            return 0, "思想内容过短"

        # 规则4: 思想内容过长（可能包含冗余）
        if len(thought_content) > 5000:
            return 0, "思想内容过长（>5000字符），可能包含冗余"

        return 1, "启发式规则验证通过"

    def is_thought_valid(self, confidence: int) -> bool:
        """
        判断思想是否有效

        Args:
            confidence: 置信度值 (0或1)

        Returns:
            True表示思想有效，应保留
        """
        return confidence == 1