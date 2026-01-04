"""模糊匹配器 - 支持前缀匹配、子序列匹配和编辑距离。


结合三种匹配算法，提供智能补全建议：

1. **前缀匹配**（最严格）：'env' → 'env', 'environment'
2. **子序列匹配**（中等）：'se' → 'S**s**h **E**nv'
3. **Levenshtein 距离**（容错）：'envm' → 'env'（1次编辑）


评分策略：
    - 前缀匹配：100 分（完全匹配前缀）
    - 子序列匹配：50-90 分（根据连续性和位置）
    - 编辑距离：30-80 分（根据距离，最多容忍3次编辑）
    - 无匹配：0 分

优先级：前缀匹配 > 子序列匹配 > 编辑距离 > 无匹配

Example:
    >>> matcher = FuzzyMatcher()
    >>> results = matcher.match("env", ["ssh env", "environment", "env setup", "envelope"])
    >>> # 返回：[("env setup", 100), ("ssh env", 85), ("environment", 80), ("envelope", 60)]
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class MatchResult:
    """匹配结果。

    Attributes:
        candidate: 候选字符串
        score: 匹配分数（0-100）
        match_type: 匹配类型（'prefix', 'subsequence', 'levenshtein', 'none'）
    """

    candidate: str
    score: float
    match_type: str


class FuzzyMatcher:
    """模糊匹配器。

    结合前缀匹配、子序列匹配和 Levenshtein 距离三种算法，
    提供智能的模糊匹配能力。

    Attributes:
        enable_prefix: 是否启用前缀匹配（默认 True）
        enable_subsequence: 是否启用子序列匹配（默认 True）
        enable_levenshtein: 是否启用编辑距离（默认 True）
        max_levenshtein_distance: 最大编辑距离（��认 3）
    """

    def __init__(
        self,
        enable_prefix: bool = True,
        enable_subsequence: bool = True,
        enable_levenshtein: bool = True,
        max_levenshtein_distance: int = 3,
    ) -> None:
        """初始化模糊匹配器。

        Args:
            enable_prefix: 是否启用前缀匹配
            enable_subsequence: 是否启用子序列匹配
            enable_levenshtein: 是否启用编辑距离
            max_levenshtein_distance: 最大编辑距离（超过此距离视为不匹配）
        """
        self.enable_prefix = enable_prefix
        self.enable_subsequence = enable_subsequence
        self.enable_levenshtein = enable_levenshtein
        self.max_levenshtein_distance = max_levenshtein_distance

    def match(self, query: str, candidates: Sequence[str]) -> list[MatchResult]:
        """对候选列表进行模糊匹配，返回排序后的结果。

        Args:
            query: 查询字符串（用户输入）
            candidates: 候选字符串列表

        Returns:
            按分数降序排列的 MatchResult 列表

        Example:
            >>> matcher = FuzzyMatcher()
            >>> results = matcher.match("env", ["ssh env", "environment", "eval"])
            >>> [r.candidate for r in results]
            ['environment', 'ssh env', 'eval']
        """
        if not query:
            # 空查询：返回所有候选，分数为 0
            return [MatchResult(c, 0.0, "none") for c in candidates]

        results: list[MatchResult] = []

        for candidate in candidates:
            result = self._match_single(query, candidate)
            results.append(result)

        # 按分数降序排序
        results.sort(key=lambda r: r.score, reverse=True)

        # 过滤掉分数为 0 的结果
        return [r for r in results if r.score > 0]

    def _match_single(self, query: str, candidate: str) -> MatchResult:
        """对单个候选进行匹配。

        Args:
            query: 查询字符串
            candidate: 候选字符串

        Returns:
            MatchResult 对象
        """
        query_lower = query.lower()
        candidate_lower = candidate.lower()

        # 1. 前缀匹配（最高优先级）
        if self.enable_prefix and candidate_lower.startswith(query_lower):
            # 完全前缀：100 分
            # 部分前缀（不应发生，因为 startswith 是全有或全无）：0 分
            return MatchResult(candidate, 100.0, "prefix")

        # 2. 子序列匹配
        if self.enable_subsequence:
            subsequence_score = self._subsequence_match(query_lower, candidate_lower)
            if subsequence_score > 0:
                return MatchResult(candidate, subsequence_score, "subsequence")

        # 3. Levenshtein 距离匹配
        if self.enable_levenshtein:
            distance = self._levenshtein_distance(query_lower, candidate_lower)
            if distance <= self.max_levenshtein_distance:
                levenshtein_score = self._levenshtein_to_score(distance)
                return MatchResult(candidate, levenshtein_score, "levenshtein")

        # 4. 无匹配
        return MatchResult(candidate, 0.0, "none")

    def _subsequence_match(self, query: str, candidate: str) -> float:
        """子序列匹配评分。

        算法：
        1. 检查 query 是否是 candidate 的子序列
        2. 评分依据：
           - 基础分：50 分
           - 连续字符：+20 分
           - 首字符匹配：+10 分
           - 长度惩罚：(len(query) / len(candidate)) * 10

        Args:
            query: 查询字符串（小写）
            candidate: 候选字符串（小写）

        Returns:
            匹配分数（0-90），如果不是子序列则返回 0
        """
        # 检查是否是子序列
        if not self._is_subsequence(query, candidate):
            return 0.0

        # 基础分
        score = 50.0

        # 连续字符加分
        consecutive_count = self._count_consecutive_matches(query, candidate)
        score += min(consecutive_count * 10, 20)  # 最多 +20 分

        # 首字符匹配加分
        if candidate[0] == query[0]:
            score += 10.0

        # 长度惩罚（候选越长，分数越低）
        length_ratio = len(query) / len(candidate)
        score += length_ratio * 10

        return min(score, 90.0)  # 最高 90 分

    def _is_subsequence(self, query: str, candidate: str) -> bool:
        """检查 query 是否是 candidate 的子序列。

        Args:
            query: 查询字符串
            candidate: 候选字符串

        Returns:
            如果是子序列则返回 True

        Example:
            >>> _is_subsequence("se", "ssh env")
            True  # 's' 在位置 0, 'e' 在位置 4
        """
        it = iter(candidate)
        return all(char in it for char in query)

    def _count_consecutive_matches(self, query: str, candidate: str) -> int:
        """计算子序列匹配中的连续字符数。

        Args:
            query: 查询字符串
            candidate: 候选字符串

        Returns:
            连续字符数

        Example:
            >>> _count_consecutive_matches("env", "ssh env")
            3  # 'e', 'n', 'v' 连续出现在 "env" 中
        """
        count = 0
        max_count = 0

        it = iter(candidate)
        prev_pos = -1

        for char in query:
            # 查找字符在 candidate 中的位置
            for i, c in enumerate(it):
                if c == char:
                    if prev_pos == -1 or i == prev_pos + 1:
                        count += 1
                    else:
                        # 不连续，重置
                        count = 1
                    prev_pos = i
                    break

        max_count = max(max_count, count)
        return max_count

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """计算两个字符串的 Levenshtein 距离（编辑距离）。

        使用动态规划算法，时间复杂度 O(len(s1) * len(s2))。

        Args:
            s1: 第一个字符串
            s2: 第二个字符串

        Returns:
            编辑距离

        Example:
            >>> _levenshtein_distance("env", "envm")
            1  # 插入一个字符
            >>> _levenshtein_distance("env", "en")
            1  # 删除一个字符
            >>> _levenshtein_distance("env", "enb")
            1  # 替换一个字符
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        # s1 较长或相等
        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))

        for i, c1 in enumerate(s1):
            current_row = [i + 1]

            for j, c2 in enumerate(s2):
                # 计算插入、删除、替换的代价
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)

                current_row.append(min(insertions, deletions, substitutions))

            previous_row = current_row

        return previous_row[-1]

    def _levenshtein_to_score(self, distance: int) -> float:
        """将编辑距离转换为分数。

        评分策略：
        - 距离 0：不应调用此函数（应该是前缀匹配）
        - 距离 1：80 分
        - 距离 2：60 分
        - 距离 3：40 分
        - 距离 >3：线性衰减

        Args:
            distance: 编辑距离

        Returns:
            分数（0-80）
        """
        if distance == 0:
            return 100.0  # 理论上不应发生

        if distance == 1:
            return 80.0
        elif distance == 2:
            return 60.0
        elif distance == 3:
            return 40.0
        else:
            # 线性衰减，最低 0 分
            return max(0.0, 40.0 - (distance - 3) * 10)


# 便捷函数
def fuzzy_match(
    query: str,
    candidates: Sequence[str],
    enable_prefix: bool = True,
    enable_subsequence: bool = True,
    enable_levenshtein: bool = True,
    max_levenshtein_distance: int = 3,
) -> list[str]:
    """便捷的模糊匹配函数。

    Args:
        query: 查询字符串
        candidates: 候选字符串列表
        enable_prefix: 是否启用前缀匹配
        enable_subsequence: 是否启用子序列匹配
        enable_levenshtein: 是否启用编辑距离
        max_levenshtein_distance: 最大编辑距离

    Returns:
        按匹配度排序的候选字符串列表

    Example:
        >>> fuzzy_match("env", ["ssh env", "environment", "eval"])
        ['environment', 'ssh env', 'eval']
    """
    matcher = FuzzyMatcher(
        enable_prefix=enable_prefix,
        enable_subsequence=enable_subsequence,
        enable_levenshtein=enable_levenshtein,
        max_levenshtein_distance=max_levenshtein_distance,
    )

    results = matcher.match(query, candidates)
    return [r.candidate for r in results]
