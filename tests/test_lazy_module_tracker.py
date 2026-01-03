"""测试 LazyModuleTracker。"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

# 直接导入具体模块，避免触发 ptk_repl/__init__.py
from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli.cli import PromptToolkitCLI


class MockModule(CommandModule):
    """模拟模块。"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock module"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        pass


class MockModuleWithAliases(CommandModule):
    """带别名的模拟模块。"""

    @property
    def name(self) -> str:
        return "mock_alias"

    @property
    def description(self) -> str:
        return "Mock module with aliases"

    @property
    def aliases(self) -> list[str]:
        return ["ma", "mock_a"]

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        pass


class TestLazyModuleTracker:
    """LazyModuleTracker 测试。"""

    def test_init(self) -> None:
        """测试初始化。"""
        tracker = LazyModuleTracker()
        assert tracker.lazy_modules == {}
        assert tracker.loaded_modules == set()

    def test_add_lazy_module(self) -> None:
        """测试添加懒加载模块。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock", MockModule)

        # 检查模块已添加
        assert "mock" in tracker.lazy_modules
        assert tracker.lazy_modules["mock"] == MockModule

        # 检查模块未标记为已加载
        assert not tracker.is_loaded("mock")

    def test_add_lazy_module_with_aliases(self) -> None:
        """测试添加带别名的懒加载模块。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock_alias", MockModuleWithAliases)

        # 检查模块已添加
        assert "mock_alias" in tracker.lazy_modules

        # 检查别名解析（O(1)查找）
        assert tracker.find_by_alias("ma") == "mock_alias"
        assert tracker.find_by_alias("mock_a") == "mock_alias"

    def test_mark_as_loaded(self) -> None:
        """测试标记模块为已加载。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock", MockModule)

        # 标记为已加载
        tracker.mark_as_loaded("mock")

        # 检查状态
        assert tracker.is_loaded("mock")
        assert "mock" in tracker.loaded_modules

        # 检查已从懒加载列表中移除
        assert "mock" not in tracker.lazy_modules

    def test_is_loaded(self) -> None:
        """测试检查模块是否已加载。"""
        tracker = LazyModuleTracker()

        # 初始状态：未加载
        assert not tracker.is_loaded("mock")

        # 添加懒加载模块：仍未加载
        tracker.add_lazy_module("mock", MockModule)
        assert not tracker.is_loaded("mock")

        # 标记为已加载
        tracker.mark_as_loaded("mock")
        assert tracker.is_loaded("mock")

    def test_get_module_class(self) -> None:
        """测试获取模块类。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock", MockModule)

        # 获取存在的模块类
        assert tracker.get_module_class("mock") == MockModule

        # 获取不存在的模块类
        assert tracker.get_module_class("nonexistent") is None

        # 标记为已加载后无法获取（已从懒加载列表移除）
        tracker.mark_as_loaded("mock")
        assert tracker.get_module_class("mock") is None

    def test_resolve_alias(self) -> None:
        """测试别名解析（O(1)查找）。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock_alias", MockModuleWithAliases)

        # 解析别名
        assert tracker.find_by_alias("ma") == "mock_alias"
        assert tracker.find_by_alias("mock_a") == "mock_alias"

        # 不存在的别名
        assert tracker.find_by_alias("nonexistent") is None

    def test_duplicate_module_rejection(self) -> None:
        """测试重复添加模块（当前实现允许覆盖）。"""
        tracker = LazyModuleTracker()

        # 第一次添加
        tracker.add_lazy_module("mock", MockModule)
        assert tracker.lazy_modules["mock"] == MockModule

        # 第二次添加相同模块（会覆盖）
        tracker.add_lazy_module("mock", MockModuleWithAliases)
        assert tracker.lazy_modules["mock"] == MockModuleWithAliases

    def test_loaded_modules_property_immutability(self) -> None:
        """测试 loaded_modules 属性的不可变性。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock", MockModule)
        tracker.mark_as_loaded("mock")

        # 获取属性副本
        loaded = tracker.loaded_modules
        loaded.add("external_module")

        # 原始集合不受影响
        assert "external_module" not in tracker.loaded_modules
        assert tracker.loaded_modules == {"mock"}

    def test_lazy_modules_property_immutability(self) -> None:
        """测试 lazy_modules 属性的不可变性。"""
        tracker = LazyModuleTracker()
        tracker.add_lazy_module("mock", MockModule)

        # 获取属性副本
        lazy = tracker.lazy_modules
        lazy["external_module"] = MockModule

        # 原始字典不受影响
        assert "external_module" not in tracker.lazy_modules
        assert tracker.lazy_modules == {"mock": MockModule}
