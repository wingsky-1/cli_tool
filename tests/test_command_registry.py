"""测试 CommandRegistry 命令注册表。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.registry.command_registry import CommandRegistry
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.core.completion.auto_completer import AutoCompleter


# ===== Mock 模块 =====


class MockModule(CommandModule):
    """模拟模块。"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock module"

    @property
    def aliases(self) -> str:
        return "mk"

    def register_commands(self, cli) -> None:
        pass


class AnotherMockModule(CommandModule):
    """另一个模拟模块。"""

    @property
    def name(self) -> str:
        return "another"

    @property
    def description(self) -> str:
        return "Another module"

    def register_commands(self, cli) -> None:
        pass


# ===== 测试类 =====


class TestCommandRegistry:
    """CommandRegistry 测试。"""

    @pytest.fixture
    def registry(self) -> CommandRegistry:
        """命令注册表 fixture。"""
        return CommandRegistry()

    @pytest.fixture
    def mock_module(self) -> MockModule:
        """模拟模块 fixture。"""
        return MockModule()

    @pytest.fixture
    def mock_completer(self) -> MagicMock:
        """模拟补全器 fixture。"""
        completer = MagicMock()
        return completer

    def test_register_module(self, registry: CommandRegistry, mock_module: MockModule) -> None:
        """测试注册模块。"""
        # 注册模块
        registry.register_module(mock_module)

        # 验证模块已注册
        assert registry.get_module("mock") is mock_module
        assert registry.list_modules() == [mock_module]

    def test_register_duplicate_module(
        self, registry: CommandRegistry, mock_module: MockModule
    ) -> None:
        """测试重复注册模块。"""
        # 第一次注册
        registry.register_module(mock_module)
        assert registry.get_module("mock") is mock_module

        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="模块 'mock' 已存在"):
            registry.register_module(mock_module)

    def test_get_module(self, registry: CommandRegistry, mock_module: MockModule) -> None:
        """测试获取模块。"""
        # 未注册的模块
        assert registry.get_module("mock") is None

        # 注册后获取
        registry.register_module(mock_module)
        assert registry.get_module("mock") is mock_module

        # 不存在的模块
        assert registry.get_module("nonexistent") is None

    def test_list_modules(
        self, registry: CommandRegistry, mock_module: MockModule
    ) -> None:
        """测试列出所有模块。"""
        # 初始状态：空列表
        assert registry.list_modules() == []

        # 注册模块
        registry.register_module(mock_module)
        modules = registry.list_modules()
        assert len(modules) == 1
        assert modules[0] is mock_module

        # 注册另一个模块
        another = AnotherMockModule()
        registry.register_module(another)
        modules = registry.list_modules()
        assert len(modules) == 2
        assert mock_module in modules
        assert another in modules

    def test_register_command(self, registry: CommandRegistry) -> None:
        """测试注册命令。"""
        # 创建处理器
        def mock_handler():
            pass

        # 注册命令
        registry.register_command("mock", "test", mock_handler)

        # 验证命令已注册
        cmd_info = registry.get_command_info("mock test")
        assert cmd_info is not None
        assert cmd_info[0] == "mock"
        assert cmd_info[1] == "test"
        assert cmd_info[2] is mock_handler

    def test_register_core_command(self, registry: CommandRegistry) -> None:
        """测试注册核心命令（不带模块前缀）。"""
        def help_handler():
            pass

        # 注册核心命令
        registry.register_command("core", "help", help_handler)

        # 核心命令不带模块前缀
        cmd_info = registry.get_command_info("help")
        assert cmd_info is not None
        assert cmd_info[0] == "core"
        assert cmd_info[1] == "help"

    def test_register_duplicate_command(self, registry: CommandRegistry) -> None:
        """测试重复注册命令。"""
        def handler1():
            pass

        def handler2():
            pass

        # 第一次注册
        registry.register_command("mock", "test", handler1)

        # 第二次注册（应该抛出异常）
        with pytest.raises(ValueError, match="命令 'mock test' 已存在"):
            registry.register_command("mock", "test", handler2)

    def test_register_command_with_aliases(self, registry: CommandRegistry) -> None:
        """测试注册带别名的命令。"""
        def connect_handler():
            pass

        # 注册带别名的命令
        registry.register_command("database", "connect", connect_handler, aliases=["db conn", "dc"])

        # 验证别名映射
        aliases = registry.get_all_aliases()
        assert "db conn" in aliases
        assert aliases["db conn"] == "database connect"
        assert "dc" in aliases
        assert aliases["dc"] == "database connect"

        # 验证通过别名获取命令
        cmd_info = registry.get_command_info("db conn")
        assert cmd_info is not None
        assert cmd_info[2] is connect_handler

    def test_get_command_info(self, registry: CommandRegistry) -> None:
        """测试获取命令信息。"""
        def handler():
            pass

        # 注册命令
        registry.register_command("mock", "test", handler)

        # 获取命令信息
        cmd_info = registry.get_command_info("mock test")
        assert cmd_info == ("mock", "test", handler)

        # 不存在的命令
        cmd_info = registry.get_command_info("nonexistent")
        assert cmd_info is None

    def test_get_command_info_with_alias(self, registry: CommandRegistry) -> None:
        """测试通过别名获取命令信息。"""
        def handler():
            pass

        # 注册带别名的命令
        registry.register_command("database", "connect", handler, aliases=["db conn"])

        # 通过别名获取
        cmd_info = registry.get_command_info("db conn")
        assert cmd_info is not None
        assert cmd_info[0] == "database"
        assert cmd_info[2] is handler

    def test_list_module_commands(self, registry: CommandRegistry) -> None:
        """测试列出模块的所有命令。"""
        def handler1():
            pass

        def handler2():
            pass

        # 注册多个命令
        registry.register_command("mock", "test1", handler1)
        registry.register_command("mock", "test2", handler2)
        registry.register_command("another", "test3", handler1)

        # 列出 mock 模块的命令
        mock_commands = registry.list_module_commands("mock")
        assert "test1" in mock_commands
        assert "test2" in mock_commands
        assert len(mock_commands) == 2

        # 列出 another 模块的命令
        another_commands = registry.list_module_commands("another")
        assert "test3" in another_commands
        assert len(another_commands) == 1

    def test_set_completer(
        self, registry: CommandRegistry, mock_completer: MagicMock
    ) -> None:
        """测试设置补全器。"""
        # 设置补全器
        registry.set_completer(mock_completer)

        # 注册命令时应该触发补全器刷新
        def handler():
            pass

        registry.register_command("mock", "test", handler)

        # 验证补全器被刷新
        mock_completer.refresh.assert_called_once()

    def test_auto_refresh_on_register(
        self, registry: CommandRegistry, mock_completer: MagicMock
    ) -> None:
        """测试注册命令时自动刷新补全器。"""
        # 设置补全器
        registry.set_completer(mock_completer)

        # 注册命令
        def handler():
            pass

        registry.register_command("mock", "test", handler)

        # 验证补全器被刷新
        mock_completer.refresh.assert_called_once()

    def test_get_all_commands(self, registry: CommandRegistry) -> None:
        """测试获取所有命令。"""
        def handler():
            pass

        # 注册命令
        registry.register_command("mock", "test1", handler)
        registry.register_command("mock", "test2", handler)

        # 获取所有命令
        all_commands = registry.get_all_commands()
        assert "mock test1" in all_commands
        assert "mock test2" in all_commands

        # 验证返回的是副本（修改不影响原始）
        all_commands["new command"] = ("mock", "new", handler)
        assert registry.get_command_info("new command") is None

    def test_get_all_aliases(self, registry: CommandRegistry) -> None:
        """测试获取所有别名。"""
        def handler():
            pass

        # 注册带别名的命令
        registry.register_command("mock", "test", handler, aliases=["t", "mt"])

        # 获取所有别名
        all_aliases = registry.get_all_aliases()
        assert "t" in all_aliases
        assert "mt" in all_aliases
        assert all_aliases["t"] == "mock test"

        # 验证返回的是副本（修改不影响原始）
        all_aliases["new_alias"] = "mock test"
        assert "new_alias" not in registry.get_all_aliases()

    def test_resolve_module_name(
        self, registry: CommandRegistry, mock_module: MockModule
    ) -> None:
        """测试解析短模块名。"""
        # 注册模块
        registry.register_module(mock_module)

        # 精确匹配
        assert registry._resolve_module_name("mock") == "mock"

        # 短别名匹配
        assert registry._resolve_module_name("mk") == "mock"

        # 前缀匹配
        assert registry._resolve_module_name("mo") == "mock"

        # 不存在的模块
        assert registry._resolve_module_name("nonexistent") is None

    def test_get_command_info_with_short_module_name(
        self, registry: CommandRegistry, mock_module: MockModule
    ) -> None:
        """测试使用短模块名获取命令。"""
        def handler():
            pass

        # 注册模块和命令
        registry.register_module(mock_module)
        registry.register_command("mock", "test", handler)

        # 使用完整模块名
        cmd_info = registry.get_command_info("mock test")
        assert cmd_info is not None

        # 使用短别名
        cmd_info = registry.get_command_info("mk test")
        assert cmd_info is not None
        assert cmd_info[0] == "mock"

        # 使用前缀
        cmd_info = registry.get_command_info("mo test")
        assert cmd_info is not None
        assert cmd_info[0] == "mock"
