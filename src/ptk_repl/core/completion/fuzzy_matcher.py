"""模糊匹配器 - 支持前缀、子序列和 Levenshtein 距离匹配。"""

import functools
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果。"""

    candidate: str
    score: int  # 0-100，越高越好

    def __lt__(self, other: "MatchResult") -> bool:
        """用于排序（分数高的在前）。"""
        return self.score > other.score


class FuzzyMatcher:
    """模糊匹配器。

    支持三层匹配算法：
    1. 前缀匹配（100 分，最快）
    2. 子序列匹配（50-90 分，中等）
    3. Levenshtein 距离（30-80 分，容错）
    """

    def __init__(self, cache_size: int = 128) -> None:
        """初始化模糊匹配器。

        Args:
            cache_size: LRU 缓存大小
        """
        self._cache: dict[tuple[str, tuple[str, ...]], list[MatchResult]] = {}
        self._cache_size = cache_size

    def match(self, query: str, candidates: list[str] | tuple[str, ...]) -> list[MatchResult]:
        """模糊匹配。

        Args:
            query: 查询字符串
            candidates: 候选列表

        Returns:
            匹配结果列表（按分数降序）
        """
        # 空查询返回所有候选
        if not query:
            return [MatchResult(c, 100) for c in candidates]

        # 检查缓存
        cache_key = (query, tuple(candidates))
        if cache_key in self._cache:
            return self._cache[cache_key]

        results: list[MatchResult] = []

        for candidate in candidates:
            # 第 1 层：前缀匹配（100 分）
            if candidate.startswith(query):
                results.append(MatchResult(candidate, 100))
                continue

            # 第 2 层：子序列匹配（50-90 分）
            subseq_score = self._subsequence_match(query, candidate)
            if subseq_score > 0:
                results.append(MatchResult(candidate, subseq_score))
                continue

            # 第 3 层：Levenshtein 距离（30-80 分）
            lev_score = self._levenshtein_match(query, candidate)
            if lev_score > 0:
                results.append(MatchResult(candidate, lev_score))

        # 排序：分数高的在前
        results.sort()

        # 更新缓存（LRU）
        if len(self._cache) >= self._cache_size:
            # 删除最早的缓存项
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[cache_key] = results

        return results

    def _subsequence_match(self, query: str, candidate: str) -> int:
        """子序列匹配。

        检查 query 是否是 candidate 的子序列（不连续）。

        Args:
            query: 查询字符串
            candidate: 候选字符串

        Returns:
            匹配分数（0 表示不匹配，50-90 表示匹配）
        """
        if not query or len(query) > len(candidate):
            return 0

        query_lower = query.lower()
        candidate_lower = candidate.lower()

        # 检查是否是子序列
        i = 0
        last_match_pos = -1
        consecutive_bonus = 0

        for char in candidate_lower:
            if i < len(query_lower) and char == query_lower[i]:
                # 检查是否连续匹配
                if last_match_pos >= 0 and i == last_match_pos + 1:
                    consecutive_bonus += 5
                last_match_pos = i
                i += 1

        if i != len(query_lower):
            return 0  # 不是子序列

        # 计算分数：基础 50 + 连续奖励 + 长度奖励
        base_score = 50
        length_bonus = min(20, len(query) * 2)
        return base_score + consecutive_bonus + length_bonus

    def _levenshtein_match(self, query: str, candidate: str) -> int:
        """Levenshtein 距离匹配。

        Args:
            query: 查询字符串
            candidate: 候选字符串

        Returns:
            匹配分数（0 表示距离太远，30-80 表示可接受）
        """
        if not query:
            return 0

        # 只在长度差异不超过 50% 时计算
        if abs(len(query) - len(candidate)) > max(len(query), len(candidate)) * 0.5:
            return 0

        distance = self._levenshtein_distance(query, candidate)

        # 距离阈值：最多允许 3 个错误，或长度的 30%
        max_distance = max(3, int(max(len(query), len(candidate)) * 0.3))

        if distance > max_distance:
            return 0

        # 计算分数：基础 80 - 距离惩罚
        base_score = 80
        penalty = distance * 10
        return max(30, base_score - penalty)

    @functools.lru_cache(maxsize=256)  # noqa: B019
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算 Levenshtein 距离（带缓存）。

        Args:
            s1: 字符串 1
            s2: 字符串 2

        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # 计算代价（不区分大小写）
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1.lower() != c2.lower())

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]


def fuzzy_match(
    query: str,
    candidates: list[str] | tuple[str, ...],
    threshold: int = 50,
) -> list[str]:
    """便捷函数：模糊匹配并返回候选列表。

    Args:
        query: 查询字符串
        candidates: 候选列表
        threshold: 分数阈值（低于此分数的不返回）

    Returns:
        匹配的候选列表（按分数降序）
    """
    matcher = FuzzyMatcher()
    results = matcher.match(query, candidates)
    return [r.candidate for r in results if r.score >= threshold]
