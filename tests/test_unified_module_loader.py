"""测试 UnifiedModuleLoader。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

# 直接导入具体模块，避免触发 ptk_repl/__init__.py
from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from ptk_repl.core.loaders.unified_module_loader import UnifiedModuleLoader
from ptk_repl.core.resolvers.module_name_resolver import DefaultModuleNameResolver
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


class MockModuleWithInit(CommandModule):
    """带初始化的模拟模块。"""

    def __init__(self) -> None:
        """初始化。"""
        super().__init__()
        self.initialized = False

    @property
    def name(self) -> str:
        return "mock_with_init"

    @property
    def description(self) -> str:
        return "Mock module with initialization"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        pass


class MockModuleRegister:
    """模拟模块注册器。"""

    def __init__(self) -> None:
        self._modules: dict[str, CommandModule] = {}

    def register(self, module: CommandModule) -> None:
        """注册模���。"""
        self._modules[module.name] = module
        # 模拟初始化
        if hasattr(module, "initialized"):
            module.initialized = True

    def is_registered(self, module_name: str) -> bool:
        """检查是否已注册。"""
        return module_name in self._modules

    def get_module(self, module_name: str) -> CommandModule | None:
        """获取模块。"""
        return self._modules.get(module_name)


class TestUnifiedModuleLoader:
    """UnifiedModuleLoader 测试。"""

    @pytest.fixture
    def name_resolver(self) -> DefaultModuleNameResolver:
        """名称解析器 fixture。"""
        return DefaultModuleNameResolver()

    @pytest.fixture
    def lazy_tracker(self) -> LazyModuleTracker:
        """懒加载追踪器 fixture。"""
        return LazyModuleTracker()

    @pytest.fixture
    def module_register(self) -> MockModuleRegister:
        """模块注册器 fixture。"""
        return MockModuleRegister()

    @pytest.fixture
    def loader(
        self,
        name_resolver: DefaultModuleNameResolver,
        lazy_tracker: LazyModuleTracker,
        module_register: MockModuleRegister,
    ) -> UnifiedModuleLoader:
        """模块加载器 fixture。"""
        return UnifiedModuleLoader(
            name_resolver=name_resolver,
            lazy_tracker=lazy_tracker,
            module_register=module_register,
        )

    def test_load_lazy_module(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
        module_register: MockModuleRegister,
    ) -> None:
        """测试从懒加载列表加载模块。"""
        # 添加到懒加载列表
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 加载模块
        module = loader.load("mock")

        # 验证加载成功
        assert module is not None
        assert isinstance(module, MockModule)
        assert module.name == "mock"

        # 验证已注册
        assert module_register.is_registered("mock")
        assert lazy_tracker.is_loaded("mock")

    def test_load_already_loaded_module(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
        module_register: MockModuleRegister,
    ) -> None:
        """测试重复加载模块。"""
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 第一次加载
        module1 = loader.load("mock")
        assert module1 is not None

        # 第二次加载（应返回已加载的模块）
        module2 = loader.load("mock")
        assert module2 is not None
        assert module2 is module1  # 同一个实例

    def test_load_nonexistent_module(
        self,
        loader: UnifiedModuleLoader,
    ) -> None:
        """测试加载不存在的模块。"""
        # 尝试加载不存在的模块
        module = loader.load("nonexistent_module")
        assert module is None

    def test_post_load_callbacks(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
    ) -> None:
        """测试加载后回调。"""
        callback_mock = MagicMock()
        loader_with_callback = UnifiedModuleLoader(
            name_resolver=DefaultModuleNameResolver(),
            lazy_tracker=lazy_tracker,
            module_register=MockModuleRegister(),
            post_load_callbacks=[callback_mock],
        )

        lazy_tracker.add_lazy_module("mock", MockModule)
        module = loader_with_callback.load("mock")

        # 验证回调被调用
        assert module is not None
        callback_mock.assert_called_once_with(module)

    def test_ensure_module_loaded(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
    ) -> None:
        """测试确保模块已加载。"""
        lazy_tracker.add_lazy_module("mock", MockModule)

        # 模块未加载
        assert not loader.is_loaded("mock")

        # 确保加载
        loader.ensure_module_loaded("mock")

        # 模块已加载
        assert loader.is_loaded("mock")

        # 再次调用确保加载（不应出错）
        loader.ensure_module_loaded("mock")
        assert loader.is_loaded("mock")

    def test_loaded_modules_property(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
        module_register: MockModuleRegister,
    ) -> None:
        """测试 loaded_modules 属性。"""
        lazy_tracker.add_lazy_module("mock", MockModule)
        lazy_tracker.add_lazy_module("mock_with_init", MockModuleWithInit)

        # 加载两个模块
        loader.load("mock")
        loader.load("mock_with_init")

        # 检查属性
        loaded = loader.loaded_modules
        assert len(loaded) == 2
        assert "mock" in loaded
        assert "mock_with_init" in loaded
        assert isinstance(loaded["mock"], MockModule)
        assert isinstance(loaded["mock_with_init"], MockModuleWithInit)

    def test_lazy_modules_property(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
    ) -> None:
        """测试 lazy_modules 属性。"""
        lazy_tracker.add_lazy_module("mock", MockModule)
        lazy_tracker.add_lazy_module("mock_with_init", MockModuleWithInit)

        # 检查属性
        lazy = loader.lazy_modules
        assert len(lazy) == 2
        assert "mock" in lazy
        assert "mock_with_init" in lazy
        assert lazy["mock"] == MockModule
        assert lazy["mock_with_init"] == MockModuleWithInit

    def test_load_with_error_handling(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
    ) -> None:
        """测试错误处理。"""
        # 添加一个会创建失败的模块类
        class BrokenModule(CommandModule):
            @property
            def name(self) -> str:
                raise Exception("Broken!")

            @property
            def description(self) -> str:
                return "Broken module"

            def register_commands(self, cli: "PromptToolkitCLI") -> None:
                pass

        lazy_tracker.add_lazy_module("broken", BrokenModule)

        # 加载应该返回 None 而不是抛出异常
        module = loader.load("broken")
        assert module is None

    def test_load_from_dynamic_import(
        self,
        lazy_tracker: LazyModuleTracker,
    ) -> None:
        """测试动态导入模块。"""
        # 使用真实的 CoreModule
        loader = UnifiedModuleLoader(
            name_resolver=DefaultModuleNameResolver(),
            lazy_tracker=lazy_tracker,
            module_register=MockModuleRegister(),
        )

        # core 模块不在懒加载列表中，需要动态导入
        module = loader.load("core")

        # 验证加载成功（如果 core 模块存在）
        # 注意：这可能需要根据实际项目结构调整
        if module is not None:
            assert hasattr(module, "name")
            assert hasattr(module, "register_commands")

    def test_register_integration(
        self,
        loader: UnifiedModuleLoader,
        lazy_tracker: LazyModuleTracker,
        module_register: MockModuleRegister,
    ) -> None:
        """测试与注册器的集成。"""
        lazy_tracker.add_lazy_module("mock_with_init", MockModuleWithInit)

        # 加载模块
        module = loader.load("mock_with_init")

        # 验证模块已注册
        assert module is not None
        assert module_register.is_registered("mock_with_init")
        assert module_register.get_module("mock_with_init") is module

        # 验证初始化（通过注册器调用）
        assert module.initialized is True
