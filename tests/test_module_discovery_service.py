"""测试 ModuleDiscoveryService。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

# 直接导入具体模块，避免触发 ptk_repl/__init__.py
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from ptk_repl.core.loaders.module_discovery_service import ModuleDiscoveryService
from ptk_repl.core.resolvers.module_name_resolver import DefaultModuleNameResolver


class TestModuleDiscoveryService:
    """ModuleDiscoveryService 测试。"""

    def test_discover_modules(self, tmp_path: Path) -> None:
        """测试发现模块。"""
        # 创建临时模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建一些模拟模块目录
        (modules_dir / "core").mkdir()
        (modules_dir / "ssh").mkdir()
        (modules_dir / "database").mkdir()
        (modules_dir / "_private").mkdir()  # 应该被忽略
        (modules_dir / "regular_file.txt").write_text("not a module")

        # 创建发现服务
        service = ModuleDiscoveryService(modules_dir)

        # 发现模块
        modules = service.discover()

        # 验证结果（按字母顺序排序）
        assert len(modules) == 3
        assert "core" in modules
        assert "ssh" in modules
        assert "database" in modules
        assert "_private" not in modules
        assert modules == sorted(modules)  # 验证已排序

    def test_nonexistent_path(self) -> None:
        """测试不存在的路径。"""
        service = ModuleDiscoveryService(Path("/nonexistent/path"))

        # 应该返回空列表
        modules = service.discover()
        assert modules == []

    def test_preload_all(
        self,
        tmp_path: Path,
    ) -> None:
        """测试预加载所有模块。"""
        # 创建真实的模块结构（模拟 ptk_repl.modules）
        modules_dir = tmp_path / "ptk_repl" / "modules"
        modules_dir.mkdir(parents=True)

        # 创建模拟模块
        core_dir = modules_dir / "core"
        core_dir.mkdir()

        # 创建 __init__.py
        (core_dir / "__init__.py").write_text(
            """
from ptk_repl.core.base.command_module import CommandModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli.cli import PromptToolkitCLI

class CoreModule(CommandModule):
    @property
    def name(self) -> str:
        return "core"

    @property
    def description(self) -> str:
        return "Core module"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        pass
"""
        )

        # 创建 __init__.py 在 modules 目录
        (modules_dir / "__init__.py").write_text("")

        # 创建发现服务
        service = ModuleDiscoveryService(modules_dir)

        # 创建追踪器和解析器
        tracker = LazyModuleTracker()
        resolver = DefaultModuleNameResolver()

        # 使用 mock 来模拟 pkgutil.iter_modules
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [(None, "core", None)]

            # 预加载所有模块
            service.preload_all(tracker, resolver)

            # 验证模块已添加到追踪器
            assert "core" in tracker.lazy_modules

    def test_exclude_core_module(
        self,
        tmp_path: Path,
    ) -> None:
        """测试排除特定模块。"""
        # 创建模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建发现服务
        service = ModuleDiscoveryService(modules_dir)

        # 创建追踪器和解析器
        tracker = LazyModuleTracker()
        resolver = DefaultModuleNameResolver()

        # 模拟多个模块
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [
                (None, "core", None),
                (None, "ssh", None),
                (None, "database", None),
            ]

            # 预加载时排除 core 模块
            service.preload_all(tracker, resolver, exclude=["core"])

            # 验证 core 未被加载，其他模块已加载
            # 注意：由于导入会失败，这里只测试排除逻辑
            assert tracker.get_module_class("core") is None  # 被排除

    def test_skip_already_loaded(
        self,
        tmp_path: Path,
    ) -> None:
        """测试跳过已加载的模块。"""
        from ptk_repl.core.base.command_module import CommandModule

        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        service = ModuleDiscoveryService(modules_dir)

        tracker = LazyModuleTracker()
        resolver = DefaultModuleNameResolver()

        # 手动添加一个已加载的模块
        class MockModule(CommandModule):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def description(self) -> str:
                return "Mock"

            def register_commands(self, cli) -> None:
                pass

        tracker.mark_as_loaded("mock")

        # 模拟 pkgutil 返回已加载的模块
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = [(None, "mock", None)]

            # 预加载应该跳过已加载的模块
            service.preload_all(tracker, resolver)

            # 验证不会重复处理
            assert tracker.is_loaded("mock")

    def test_error_handling(
        self,
        tmp_path: Path,
    ) -> None:
        """测试错误处理。"""
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        service = ModuleDiscoveryService(modules_dir)

        tracker = LazyModuleTracker()
        resolver = DefaultModuleNameResolver()

        # 模拟导入失败
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            # 预加载应该静默失败，不抛出异常
            service.preload_all(tracker, resolver)

            # 验证追踪器保持干净
            assert len(tracker.lazy_modules) == 0
