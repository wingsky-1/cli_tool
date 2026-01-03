"""测试系统集成。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.completion.auto_completer import AutoCompleter
from ptk_repl.core.registry.command_registry import CommandRegistry
from ptk_repl.core.loaders.module_register import ModuleRegister
from ptk_repl.core.loaders.unified_module_loader import UnifiedModuleLoader
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from ptk_repl.core.resolvers.module_name_resolver import DefaultModuleNameResolver
from ptk_repl.core.state.state_manager import StateManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli.cli import PromptToolkitCLI


# ===== Mock 模块和组件 =====


class MockModule(CommandModule):
    """模拟模块。"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock module"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        # 简化：不注册任何命令
        pass


# ===== 集成测试 =====


class TestIntegration:
    """系统集成测试。"""

    @pytest.fixture
    def state_manager(self) -> StateManager:
        """状态管理器 fixture。"""
        return StateManager()

    @pytest.fixture
    def registry(self) -> CommandRegistry:
        """命令注册表 fixture。"""
        return CommandRegistry()

    @pytest.fixture
    def completer(self, registry: CommandRegistry) -> AutoCompleter:
        """自动补全器 fixture。"""
        return AutoCompleter(registry)

    @pytest.fixture
    def module_register(
        self, registry: CommandRegistry, state_manager: StateManager
    ) -> ModuleRegister:
        """模块注册器 fixture。"""
        return ModuleRegister(registry, state_manager)

    @pytest.fixture
    def lazy_tracker(self) -> LazyModuleTracker:
        """懒加载追踪器 fixture。"""
        return LazyModuleTracker()

    @pytest.fixture
    def name_resolver(self) -> DefaultModuleNameResolver:
        """名称解析器 fixture。"""
        return DefaultModuleNameResolver()

    @pytest.fixture
    def module_loader(
        self,
        name_resolver: DefaultModuleNameResolver,
        lazy_tracker: LazyModuleTracker,
        module_register: ModuleRegister,
    ) -> UnifiedModuleLoader:
        """模块加载器 fixture。"""
        # 不使用post_load_callbacks，简化测试
        return UnifiedModuleLoader(
            name_resolver=name_resolver,
            lazy_tracker=lazy_tracker,
            module_register=module_register,
            post_load_callbacks=None,  # 简化：不使用回调
        )

    def test_module_loading_pipeline(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        module_register: ModuleRegister,
        registry: CommandRegistry,
    ) -> None:
        """测试完整的模块加载流程。"""
        # 1. 声明懒加载模块
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 2. 验证模块尚未加载
        assert not module_loader.is_loaded("mock")
        assert registry.get_module("mock") is None

        # 3. 加载模块
        module = module_loader.load("mock")

        # 4. 验证模块已加载
        assert module is not None
        assert isinstance(module, MockModule)
        assert module_loader.is_loaded("mock")

        # 5. 验证模块已注册到注册表
        assert registry.get_module("mock") is module
        assert module_register.is_registered("mock")

    def test_command_registration_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        module_register: ModuleRegister,
    ) -> None:
        """测试模块注册工作流。"""
        # 1. 声明并加载模块
        lazy_tracker.add_lazy_module("mock", MockModule)
        module = module_loader.load("mock")

        # 2. 验证模块已注册
        assert module is not None
        assert module_register.is_registered("mock")

    def test_lazy_loading_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        registry: CommandRegistry,
    ) -> None:
        """测试懒加载工作流。"""
        # 1. 声明懒加载模块（但不加载）
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 2. 模块未加载
        assert not module_loader.is_loaded("mock")

        # 3. 检查懒加载列表
        lazy_modules = module_loader.lazy_modules
        assert "mock" in lazy_modules
        assert lazy_modules["mock"] == MockModule

        # 4. 按需加载
        module = module_loader.load("mock")
        assert module is not None

        # 5. 模块已加载
        loaded_modules = module_loader.loaded_modules
        assert "mock" in loaded_modules
        assert loaded_modules["mock"] is module

    def test_completer_integration_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        registry: CommandRegistry,
    ) -> None:
        """测试注册表集成工作流。"""
        # 1. 声明并加载模块
        lazy_tracker.add_lazy_module("mock", MockModule)
        module = module_loader.load("mock")

        # 2. 验证模块已注册到注册表
        assert module is not None
        assert registry.get_module("mock") is module

        # 3. 验证可以列出模块
        modules = registry.list_modules()
        assert module in modules

    def test_alias_resolution_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        registry: CommandRegistry,
    ) -> None:
        """测试模块别名解析工作流。"""
        # 1. 加载模块
        lazy_tracker.add_lazy_module("mock", MockModule)
        module = module_loader.load("mock")

        # 2. 验证模块已加载
        assert module is not None

        # 3. 验证可以通过模块名获取模块
        assert registry.get_module("mock") is module

        # 4. 验证可以通过短别名获取模块
        resolved = registry._resolve_module_name("mock")
        assert resolved == "mock"

    def test_module_state_isolation(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
        state_manager: StateManager,
    ) -> None:
        """测试模块状态隔离。"""
        # 1. 创建两个模块实例
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 2. 加载模块两次
        module1 = module_loader.load("mock")
        module2 = module_loader.load("mock")

        # 3. 验证返回同一个实例
        assert module1 is module2

    def test_error_handling_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
    ) -> None:
        """测试错误处理工作流。"""
        # 1. 尝试加载不存在的模块
        module = module_loader.load("nonexistent")

        # 2. 应该返回 None 而不是抛出异常
        assert module is None

        # 3. 验证不影响后续加载
        lazy_tracker.add_lazy_module("mock", MockModule)
        module = module_loader.load("mock")
        assert module is not None

    def test_lazy_module_declaration_workflow(
        self,
        lazy_tracker: LazyModuleTracker,
        module_loader: UnifiedModuleLoader,
    ) -> None:
        """测试懒加载模块声明工作流。"""
        # 1. 声明懒加载模块
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 2. 验证模块在懒加载列表中
        assert "mock" in module_loader.lazy_modules

        # 3. 加载模块
        module = module_loader.load("mock")

        # 4. 验证模块已加载
        assert module is not None
        assert module_loader.is_loaded("mock")
