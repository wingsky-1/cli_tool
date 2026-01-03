"""测试 ModuleLifecycleManager。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

# 直接导入具体模块，避免触发 ptk_repl/__init__.py
from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.configuration.config_manager import ConfigManager
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from ptk_repl.core.loaders.module_lifecycle_manager import ModuleLifecycleManager
from ptk_repl.core.loaders.module_register import ModuleRegister
from ptk_repl.core.registry.command_registry import CommandRegistry
from ptk_repl.core.resolvers.module_name_resolver import DefaultModuleNameResolver
from ptk_repl.core.state.state_manager import StateManager
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


class TestModuleLifecycleManager:
    """ModuleLifecycleManager 测试。"""

    @pytest.fixture
    def modules_path(self, tmp_path: Path) -> Path:
        """模块路径 fixture。"""
        return tmp_path / "modules"

    @pytest.fixture
    def name_resolver(self) -> DefaultModuleNameResolver:
        """名称解析器 fixture。"""
        return DefaultModuleNameResolver()

    @pytest.fixture
    def registry(self) -> CommandRegistry:
        """命令注册表 fixture。"""
        return CommandRegistry()

    @pytest.fixture
    def state_manager(self) -> StateManager:
        """状态管理器 fixture。"""
        return StateManager()

    @pytest.fixture
    def module_register(
        self,
        registry: CommandRegistry,
        state_manager: StateManager,
    ) -> ModuleRegister:
        """模块注册器 fixture。"""
        return ModuleRegister(registry, state_manager)

    @pytest.fixture
    def config(self) -> ConfigManager:
        """配置管理器 fixture。"""
        return ConfigManager()

    @pytest.fixture
    def auto_completer(self) -> MagicMock:
        """自动补全器 fixture。"""
        return MagicMock()

    @pytest.fixture
    def error_callback(self) -> MagicMock:
        """错误回调 fixture。"""
        return MagicMock()

    @pytest.fixture
    def register_commands_callback(self) -> MagicMock:
        """命令注册回调 fixture。"""
        return MagicMock()

    @pytest.fixture
    def lifecycle_manager(
        self,
        modules_path: Path,
        name_resolver: DefaultModuleNameResolver,
        module_register: ModuleRegister,
        config: ConfigManager,
        auto_completer: MagicMock,
        register_commands_callback: MagicMock,
        error_callback: MagicMock,
    ) -> ModuleLifecycleManager:
        """生命周期管理器 fixture。"""
        modules_path.mkdir(parents=True, exist_ok=True)
        return ModuleLifecycleManager(
            modules_path=modules_path,
            name_resolver=name_resolver,
            module_register=module_register,
            config=config,
            auto_completer=auto_completer,
            register_commands_callback=register_commands_callback,
            error_callback=error_callback,
        )

    def test_facade_pattern_compatibility(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试门面模式兼容性。"""
        # 验证实现了 IModuleLoader 接口
        assert hasattr(lifecycle_manager, "load")
        assert hasattr(lifecycle_manager, "is_loaded")
        assert hasattr(lifecycle_manager, "ensure_module_loaded")
        assert hasattr(lifecycle_manager, "loaded_modules")
        assert hasattr(lifecycle_manager, "lazy_modules")

    def test_load_single_module(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试加载单个模块。"""
        # 手动添加到懒加载列表
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)

        # 加载模块
        module = lifecycle_manager.load("mock")

        # 验证加载成功
        assert module is not None
        assert isinstance(module, MockModule)
        assert lifecycle_manager.is_loaded("mock")

    def test_is_loaded(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试检查模块是否已加载。"""
        # 初始状态
        assert not lifecycle_manager.is_loaded("mock")

        # 添加并加载模块
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)
        lifecycle_manager.load("mock")

        # 加载后
        assert lifecycle_manager.is_loaded("mock")

    def test_ensure_module_loaded(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试确保模块已加载。"""
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)

        # 模块未加载
        assert not lifecycle_manager.is_loaded("mock")

        # 确保加载
        lifecycle_manager.ensure_module_loaded("mock")

        # 模块已加载
        assert lifecycle_manager.is_loaded("mock")

        # 再次调用（不应出错）
        lifecycle_manager.ensure_module_loaded("mock")

    def test_loaded_modules_property(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试 loaded_modules 属性。"""
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)
        lifecycle_manager.load("mock")

        # 检查属性
        loaded = lifecycle_manager.loaded_modules
        assert "mock" in loaded
        assert isinstance(loaded["mock"], MockModule)

    def test_lazy_modules_property(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试 lazy_modules 属性。"""
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)

        # 检查属性
        lazy = lifecycle_manager.lazy_modules
        assert "mock" in lazy
        assert lazy["mock"] == MockModule

    def test_callback_execution(
        self,
        lifecycle_manager: ModuleLifecycleManager,
        register_commands_callback: MagicMock,
        auto_completer: MagicMock,
    ) -> None:
        """测试回调执行。"""
        lifecycle_manager._tracker.add_lazy_module("mock", MockModule)

        # 加载模块
        lifecycle_manager.load("mock")

        # 验证回调被调用
        register_commands_callback.assert_called_once()
        auto_completer.refresh.assert_called_once()

    def test_load_core_immediately(
        self,
        lifecycle_manager: ModuleLifecycleManager,
        error_callback: MagicMock,
    ) -> None:
        """测试立即加载 core 模块。"""
        # 注意：这个测试依赖实际的 CoreModule
        # 如果 CoreModule 不存在或导入失败，会调用错误回调

        lifecycle_manager.load_module_immediately("core")

        # 如果加载成功，core 应该被标记为已加载
        # 如果加载失败，错误回调应该被调用
        if lifecycle_manager.is_loaded("core"):
            # 加载成功
            assert not error_callback.called
        else:
            # 加载失败
            assert error_callback.called

    def test_load_modules_workflow(
        self,
        lifecycle_manager: ModuleLifecycleManager,
    ) -> None:
        """测试加载所有模块的工作流。"""
        # 模拟配置
        lifecycle_manager._config._config = {"core": {"preload_modules": []}}

        # 模拟模块发现
        with patch("pkgutil.iter_modules") as mock_iter:
            mock_iter.return_value = []

            # 执行加载流程
            lifecycle_manager.load_modules()

            # Core 模块应该被加载（如果存在）
            # 其他模块根据配置加载
