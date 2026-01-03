"""测试 HelpFormatter 帮助格式化器。"""

import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.formatting.help_formatter import HelpFormatter
from ptk_repl.core.registry.command_registry import CommandRegistry
from ptk_repl.core.state.state_manager import StateManager
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli.cli import PromptToolkitCLI


# ===== 辅助函数 =====


def strip_ansi_codes(text: str) -> str:
    """剥离 ANSI 颜色代码。

    Args:
        text: 包含 ANSI 颜色代码的文本

    Returns:
        剥离后的纯文本
    """
    # 匹配 ANSI 转义序列：ESC[ 参数 m
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


# ===== Mock 类 =====


class MockCLI:
    """模拟CLI类。"""

    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry
        self.state = StateManager()


class MockModule(CommandModule):
    """模拟模块。"""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock module for testing"

    @property
    def aliases(self) -> str:
        return "mk"

    @property
    def version(self) -> str:
        return "1.0.0"

    def register_commands(self, cli) -> None:
        """注册命令。"""
        pass


# ===== 测试类 =====


class TestHelpFormatter:
    """HelpFormatter 测试。"""

    @pytest.fixture
    def registry(self) -> CommandRegistry:
        """命令注册表 fixture。"""
        return CommandRegistry()

    @pytest.fixture
    def cli(self, registry: CommandRegistry) -> MockCLI:
        """CLI fixture。"""
        return MockCLI(registry)

    @pytest.fixture
    def formatter(self, cli: MockCLI) -> HelpFormatter:
        """HelpFormatter fixture。"""
        return HelpFormatter(cli)

    def test_extract_command_description_with_docstring(self, formatter: HelpFormatter) -> None:
        """测试提取带文档字符串的命令描述。"""

        def sample_command():
            """这是一个测试命令的描述。"""
            pass

        description = formatter.extract_command_description(sample_command)
        assert description == "这是一个测试命令的描述。"

    def test_extract_command_description_multiline_docstring(self, formatter: HelpFormatter) -> None:
        """测试提取多行文档字符串的命令描述（只取第一行）。"""

        def sample_command():
            """第一行描述。

            更多详细信息...
            """
            pass

        description = formatter.extract_command_description(sample_command)
        assert description == "第一行描述。"

    def test_extract_command_description_no_docstring(self, formatter: HelpFormatter) -> None:
        """测试提取无文档字符串的命令描述。"""

        def sample_command():
            pass

        description = formatter.extract_command_description(sample_command)
        assert description == "无描述"

    def test_extract_command_description_from_typed_command(self, formatter: HelpFormatter) -> None:
        """测试从typed_command包装器提取描述。"""

        class SampleArgs(BaseModel):
            """参数模型。"""
            name: str = Field(..., description="名称")

        def sample_command(args: SampleArgs) -> None:
            """这是原始命令。"""
            pass

        # 模拟typed_command包装器
        sample_command._original_func = sample_command.__wrapped__ = lambda x: None
        sample_command._original_func.__doc__ = "这是原始命令。"

        description = formatter.extract_command_description(sample_command)
        assert description == "这是原始命令。"

    def test_extract_parameter_info_with_typed_command(self, formatter: HelpFormatter) -> None:
        """测试提取typed_command的参数信息。"""

        class ConnectArgs(BaseModel):
            """连接参数。"""
            host: str = Field(..., description="主机地址")
            port: int = Field(default=5432, ge=1, le=65535, description="端口号")
            ssl: bool = Field(default=False, description="是否使用SSL")

        def connect_command(args: ConnectArgs) -> None:
            """连接命令。"""
            pass

        # 模拟typed_command包装器
        connect_command._original_func = lambda x: None
        connect_command._original_func._typed_model = ConnectArgs

        params = formatter.extract_parameter_info(connect_command)

        assert len(params) == 3

        # 验证host参数
        host_param = next(p for p in params if p["name"] == "host")
        assert host_param["description"] == "主机地址"
        assert host_param["required"] is True
        assert host_param["default"] is None

        # 验证port参数
        port_param = next(p for p in params if p["name"] == "port")
        assert port_param["description"] == "端口号"
        assert port_param["required"] is False
        assert port_param["default"] == 5432

        # 验证ssl参数
        ssl_param = next(p for p in params if p["name"] == "ssl")
        assert ssl_param["description"] == "是否使用SSL"
        assert ssl_param["required"] is False
        assert ssl_param["default"] is False

    def test_extract_parameter_info_no_parameters(self, formatter: HelpFormatter) -> None:
        """测试提取无参数的命令信息。"""

        def simple_command():
            """简单命令。"""
            pass

        params = formatter.extract_parameter_info(simple_command)
        assert len(params) == 0

    def test_get_command_aliases(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试获取命令别名。"""
        # 注册带别名的命令
        def handler():
            pass

        cli.registry.register_command("mock", "test", handler, aliases=["t", "mt"])

        # 获取别名
        aliases = formatter.get_command_aliases("mock", "test")
        assert "t" in aliases
        assert "mt" in aliases

    def test_get_command_aliases_no_aliases(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试获取无别名的命令别名。"""
        # 注册不带别名的命令
        def handler():
            pass

        cli.registry.register_command("mock", "test", handler)

        aliases = formatter.get_command_aliases("mock", "test")
        assert len(aliases) == 0

    def test_get_command_aliases_core_command(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试核心命令的别名。"""
        def handler():
            pass

        cli.registry.register_command("core", "help", handler, aliases=["h"])

        aliases = formatter.get_command_aliases("core", "help")
        assert "h" in aliases

    def test_format_command_item(self, formatter: HelpFormatter) -> None:
        """测试格式化命令项。"""

        # 基本格式
        item = formatter._format_command_item("test", "测试命令")
        clean_item = strip_ansi_codes(item)
        assert "test" in clean_item
        assert "测试命令" in clean_item

        # 带别名
        item_with_aliases = formatter._format_command_item("test", "测试命令", aliases=["t", "te"])
        clean_item_with_aliases = strip_ansi_codes(item_with_aliases)
        assert "test" in clean_item_with_aliases
        assert "(t, te)" in clean_item_with_aliases

        # 带缩进
        indented_item = formatter._format_command_item("test", "测试命令", indent=4)
        assert indented_item.startswith("    ")

    def test_separator(self, formatter: HelpFormatter) -> None:
        """测试生成分隔线。"""
        separator = formatter._separator()
        assert "━" * 65 in separator
        assert len(separator) >= 65

    def test_title(self, formatter: HelpFormatter) -> None:
        """测试生成标题。"""
        title = formatter._title("测试标题")
        assert "测试标题" in title
        assert len(title) >= 65  # 包含填充

    def test_section_header(self, formatter: HelpFormatter) -> None:
        """测试生成小节标题。"""
        header = formatter._section_header("核心命令")
        assert "核心命令" in header
        assert header.startswith("  ")

    def test_label(self, formatter: HelpFormatter) -> None:
        """测试生成标签。"""
        label = formatter._label("描述")
        assert "描述" in label
        assert label.startswith("  ")

    def test_error(self, formatter: HelpFormatter) -> None:
        """测试生成错误消息。"""
        error = formatter._error("测试错误")
        assert "[错误]" in error
        assert "测试错误" in error

    def test_color_text(self, formatter: HelpFormatter) -> None:
        """测试为文本添加颜色。"""
        # _color_text应该委托给color_scheme
        colored = formatter._color_text("测试", "command")
        assert "测试" in colored
        # 包含ANSI颜色码

    def test_get_short_module_alias(self, formatter: HelpFormatter) -> None:
        """测试获取模块短别名。"""
        # 已知的短别名
        assert formatter._get_short_module_alias("database") == "db"
        assert formatter._get_short_module_alias("file") == "fs"

        # 未知的模块
        assert formatter._get_short_module_alias("unknown") is None

    def test_format_command_help_nonexistent_command(self, formatter: HelpFormatter) -> None:
        """测试格式化不存在的命令帮助。"""
        help_text = formatter.format_command_help("mock", "nonexistent")
        assert "[错误]" in help_text
        assert "未找到命令" in help_text

    def test_format_module_help_nonexistent_module(self, formatter: HelpFormatter) -> None:
        """测试格式化不存在的模块帮助。"""
        help_text = formatter.format_module_help("nonexistent")
        assert "[错误]" in help_text
        assert "未找到模块" in help_text

    def test_format_module_help_module_with_no_commands(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试格式化没有命令的模块帮助。"""
        # 注册一个没有命令的模块
        module = MockModule()
        cli.registry.register_module(module)

        help_text = formatter.format_module_help("mock")
        assert "[错误]" in help_text
        assert "没有可用命令" in help_text

    def test_format_overview_help_empty_registry(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试格式化空注册表的总览帮助。"""
        overview = formatter.format_overview_help()
        assert "核心命令" in overview
        assert "提示:" in overview

    def test_format_overview_help_with_commands(self, cli: MockCLI, formatter: HelpFormatter) -> None:
        """测试格式化包含命令的总览帮助。"""
        # 注册核心命令
        def status_handler():
            """显示系统状态。"""
            pass

        cli.registry.register_command("core", "status", status_handler, aliases=["st"])

        # 注册模块
        module = MockModule()
        cli.registry.register_module(module)

        # 注册模块命令
        def test_handler():
            """测试命令。"""
            pass

        cli.registry.register_command("mock", "test", test_handler)

        overview = formatter.format_overview_help()

        # 验证包含核心命令
        assert "核心命令" in overview
        assert "status" in overview

        # 验证包含模块命令
        assert "模块命令" in overview
        assert "mock" in overview
        assert "test" in overview

        # 验证包含提示
        assert "提示:" in overview
        assert "help <command>" in overview
