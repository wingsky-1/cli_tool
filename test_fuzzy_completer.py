"""测试模糊匹配器和增强的 AutoCompleter。"""

import pytest

from ptk_repl.core.completion.fuzzy_matcher import (
    FuzzyMatcher,
    MatchResult,
    fuzzy_match,
)


class TestFuzzyMatcher:
    """模糊匹配器测试。"""

    @pytest.fixture
    def matcher(self) -> FuzzyMatcher:
        """模糊匹配器 fixture。"""
        return FuzzyMatcher()

    def test_prefix_match(self, matcher: FuzzyMatcher) -> None:
        """测试前缀匹配。"""
        results = matcher.match("env", ["environment", "env", "ssh env", "eval"])

        # environment 和 env 都是前缀匹配，分数 100
        assert len(results) >= 2
        assert any(r.candidate == "env" and r.score == 100.0 for r in results)
        assert any(r.candidate == "environment" and r.score == 100.0 for r in results)

    def test_subsequence_match(self, matcher: FuzzyMatcher) -> None:
        """测试子序列匹配。"""
        results = matcher.match("se", ["ssh env", "env setup", "select"])

        # ssh env: S**s**h **e**nv 是子序列
        assert any(r.candidate == "ssh env" and r.match_type == "subsequence" for r in results)

    def test_subsequence_consecutive(self, matcher: FuzzyMatcher) -> None:
        """测试连续子序列加分。"""
        results = matcher.match("env", ["ssh env", "environment"])

        ssh_env_score = next(r.score for r in results if r.candidate == "ssh env")
        env_score = next(r.score for r in results if r.candidate == "environment")

        # ssh env 中 "env" 连续出现，分数应该更高
        assert ssh_env_score > 70  # 50 + 20（连续） + 10（长度惩罚）

    def test_levenshtein_match(self, matcher: FuzzyMatcher) -> None:
        """测试编辑距离匹配。"""
        results = matcher.match("envm", ["env", "environment", "envelope"])

        # envm → env 是 1 次编辑（删除 m）
        assert any(r.candidate == "env" and r.match_type == "levenshtein" for r in results)

        # 分数应该是 80（距离 1）
        env_result = next(r for r in results if r.candidate == "env")
        assert env_result.score == 80.0

    def test_levenshtein_distance_calculation(self, matcher: FuzzyMatcher) -> None:
        """测试编辑距离计算。"""
        assert matcher._levenshtein_distance("env", "env") == 0
        assert matcher._levenshtein_distance("env", "envm") == 1  # 插入
        assert matcher._levenshtein_distance("env", "en") == 1  # 删除
        assert matcher._levenshtein_distance("env", "enb") == 1  # 替换
        assert matcher._levenshtein_distance("env", "enb") == 1

    def test_levenshtein_max_distance(self, matcher: FuzzyMatcher) -> None:
        """测试最大编辑距离限制。"""
        # 默认 max_distance=3
        results = matcher.match("abc", ["uvwxyz"])  # 距离 > 3

        # 不应该匹配
        assert len(results) == 0

    def test_no_match(self, matcher: FuzzyMatcher) -> None:
        """测试无匹配情况。"""
        results = matcher.match("xyz", ["env", "ssh", "database"])

        # 应该返回空列表
        assert len(results) == 0

    def test_empty_query(self, matcher: FuzzyMatcher) -> None:
        """测试空查询。"""
        results = matcher.match("", ["env", "ssh", "database"])

        # 空查询返回所有候选，分数为 0
        assert len(results) == 3
        assert all(r.score == 0.0 for r in results)

    def test_case_insensitive(self, matcher: FuzzyMatcher) -> None:
        """测试大小写不敏感。"""
        results = matcher.match("ENV", ["environment", "Env", "env"])

        # 应该匹配所有变体
        assert len(results) >= 3

    def test_scoring_priority(self, matcher: FuzzyMatcher) -> None:
        """测试评分优先级。"""
        results = matcher.match("env", ["env", "ssh env", "environment"])

        # 排序：前缀（100） > 子序列（<100） > 编辑距离（<90）
        scores = [r.score for r in results]
        assert scores[0] == 100.0  # env 或 environment（前缀）

    def test_convenience_function(self) -> None:
        """测试便捷函数。"""
        results = fuzzy_match("env", ["ssh env", "environment", "eval"])

        # 应该返回字符串列表
        assert isinstance(results, list)
        assert all(isinstance(r, str) for r in results)

    def test_disable_prefix_match(self) -> None:
        """测试禁用前缀匹配。"""
        matcher = FuzzyMatcher(enable_prefix=False)
        results = matcher.match("env", ["environment", "env"])

        # 不应该有前缀匹配结果
        assert not any(r.match_type == "prefix" for r in results)

    def test_disable_subsequence_match(self) -> None:
        """测试禁用子序列匹配。"""
        matcher = FuzzyMatcher(enable_subsequence=False)
        results = matcher.match("se", ["ssh env"])

        # 应该返回空或仅编辑距离结果
        assert len(results) == 0

    def test_disable_levenshtein_match(self) -> None:
        """测试禁用编辑距离匹配。"""
        matcher = FuzzyMatcher(enable_levenshtein=False)
        results = matcher.match("envm", ["env"])

        # 应该返回空（因为没有前缀或子序列匹配）
        assert len(results) == 0

    def test_custom_max_distance(self) -> None:
        """测试自定义最大编辑距离。"""
        matcher = FuzzyMatcher(max_levenshtein_distance=1)
        results = matcher.match("abc", ["abcd", "abcde"])

        # abcd 距离 1，应该匹配
        assert any(r.candidate == "abcd" for r in results)

        # abcde 距离 2，不应该匹配
        assert not any(r.candidate == "abcde" for r in results)


class TestEnhancedAutoCompleter:
    """增强的 AutoCompleter 测试。"""

    def test_parameter_completion_trigger(self, registry_mock) -> None:
        """测试参数补全触发。"""
        from ptk_repl.core.completion.auto_completer import AutoCompleter

        completer = AutoCompleter(registry_mock)

        # 模拟输入 "database connect --h"
        from unittest.mock import Mock

        doc = Mock()
        doc.text_before_cursor = "database connect --h"
        doc.text = "database connect --h"

        event = Mock()

        completions = list(completer.get_completions(doc, event))

        # 应该有 --host 参数补全
        assert any(c.text == "--host" for c in completions)

    def test_fuzzy_matching_integration(self, registry_mock) -> None:
        """测试模糊匹配集成。"""
        from ptk_repl.core.completion.auto_completer import AutoCompleter

        completer = AutoCompleter(registry_mock, enable_fuzzy=True)

        # 模拟输入 "ev"（应该匹配 "env"）
        from unittest.mock import Mock

        doc = Mock()
        doc.text_before_cursor = "ev"
        doc.text = "ev"

        event = Mock()

        completions = list(completer.get_completions(doc, event))

        # 应该有模糊匹配结果
        assert len(completions) > 0

    def test_lazy_module_completion(self, registry_mock) -> None:
        """测试懒加载模块补全。"""
        from ptk_repl.core.completion.auto_completer import AutoCompleter

        completer = AutoCompleter(registry_mock)

        # 注册懒加载模块
        completer.register_lazy_commands("database", ["connect", "query"])

        # 构建补全字典
        completion_dict = completer.build_completion_dict()

        # 应该包含懒加载模块
        assert "database" in completion_dict[""]
        assert "connect" in completion_dict["database"]

    def test_parameter_completion_meta(self, registry_mock) -> None:
        """测试参数补全元数据。"""
        from ptk_repl.core.completion.auto_completer import AutoCompleter

        completer = AutoCompleter(registry_mock)

        # 获取参数描述
        desc = completer._get_parameter_description("--host", "database connect")

        # 应该返回 "主机地址"
        assert desc == "主机地址"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
