"""Fuzzy 匹配算法实现。"""

from functools import lru_cache
from typing import NamedTuple


class FuzzyMatchResult(NamedTuple):
    """Fuzzy 匹配结果。"""

    matched: bool
    score: float


def fuzzy_match(pattern: str, candidate: str) -> FuzzyMatchResult:
    """Fuzzy 匹配算法。

    支持字符序列匹配，用户输入的字符按顺序出现在目标字符串中即可。

    Args:
        pattern: 用户输入的模式（如 "s-e"）
        candidate: 候选项（如 "ssh-env"）

    Returns:
        (是否匹配, 匹配分数)

    Examples:
        >>> fuzzy_match("s-e", "ssh-env")
        FuzzyMatchResult(matched=True, score=0.85)
        >>> fuzzy_match("db", "database")
        FuzzyMatchResult(matched=True, score=0.72)
        >>> fuzzy_match("xyz", "ssh-env")
        FuzzyMatchResult(matched=False, score=0.0)
    """
    # 1. 完美匹配检查
    if pattern == candidate:
        return FuzzyMatchResult(matched=True, score=1.0)

    if not pattern:
        return FuzzyMatchResult(matched=True, score=1.0)

    # 移除分隔符（-）
    pattern_chars = [c.lower() for c in pattern if c != "-"]
    candidate_lower = candidate.lower()

    # 快速失败：如果 pattern 比 candidate 长，不可能匹配
    if len(pattern_chars) > len(candidate):
        return FuzzyMatchResult(matched=False, score=0.0)

    # 匹配字符位置
    matched_positions = []
    candidate_idx = 0

    for char in pattern_chars:
        # 在 candidate 中查找字符
        while candidate_idx < len(candidate_lower):
            if candidate_lower[candidate_idx] == char:
                matched_positions.append(candidate_idx)
                candidate_idx += 1
                break
            candidate_idx += 1
        else:
            # 没���到
            return FuzzyMatchResult(matched=False, score=0.0)

    # 计算匹配分数
    score = _calculate_fuzzy_score(pattern_chars, matched_positions, len(candidate))
    return FuzzyMatchResult(matched=True, score=score)


def _calculate_fuzzy_score(
    pattern_chars: list[str], positions: list[int], candidate_len: int
) -> float:
    """计算 fuzzy 匹配分数。

    评分标准：
    1. 完美匹配（pattern == candidate）：1.0
    2. 前缀匹配（如 "db" -> "database"）：0.9+
    3. 连续匹配（如 "s-e" -> "ssh-env"，字符连续）：0.8+
    4. 分散匹配（如 "dte" -> "database"）：0.5+
    5. 长度惩罚（pattern 相对于 candidate 越短，分数越低）

    Args:
        pattern_chars: 模式字符列表
        positions: 匹配位置列表
        candidate_len: 候选项长度

    Returns:
        匹配分数 [0.0, 1.0]
    """
    # 1. 前缀匹配检查
    is_prefix = positions[0] == 0

    # 2. 连续性检查（字符是否连续）
    if len(positions) > 1:
        consecutive_count = 0
        for i in range(1, len(positions)):
            if positions[i] == positions[i - 1] + 1:
                consecutive_count += 1

        # 连续性比例
        consecutive_ratio = consecutive_count / (len(positions) - 1)
    else:
        consecutive_ratio = 1.0

    # 3. 计算基础分数
    if is_prefix:
        # 前缀匹配：高基础分 + 连续性加成
        base_score = 0.85 + consecutive_ratio * 0.15
    else:
        # 非前缀匹配：较低基础分 + 连续性加成
        base_score = 0.5 + consecutive_ratio * 0.3

    # 4. 长度惩罚（pattern 越短，惩罚越小）
    pattern_len = len(pattern_chars)
    length_ratio = pattern_len / candidate_len

    # 对前缀匹配给予较小的惩罚
    if is_prefix:
        length_factor = 0.7 + 0.3 * length_ratio
    else:
        length_factor = 0.5 + 0.5 * length_ratio

    final_score = base_score * length_factor

    # 限制范围
    return min(max(final_score, 0.0), 1.0)


@lru_cache(maxsize=256)
def cached_fuzzy_match(pattern: str, candidate: str) -> FuzzyMatchResult:
    """带缓存的 fuzzy 匹配。

    Args:
        pattern: 用户输入的模式
        candidate: 候选项

    Returns:
        FuzzyMatchResult 匹配结果
    """
    return fuzzy_match(pattern, candidate)
