"""测试 AutoCompleter 自动补全系统。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.completion.auto_completer import AutoCompleter
from ptk_repl.core.decoration.typed_command import typed_command
from pydantic import BaseModel, Field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prompt_toolkit.document import Document


# ===== Mock 和 Fixture =====


class MockCommandModule(CommandModule):
    """模拟命令模块。"""

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


class TestAutoCompleter:
    """AutoCompleter 测试。"""

    @pytest.fixture
    def registry(self) -> MagicMock:
        """命令注册表 fixture。"""
        reg = MagicMock()

        # 模拟核心命令
        reg.list_module_commands.return_value = ["status", "exit", "modules"]
        reg.list_modules.return_value = [MockCommandModule()]

        # 根据模块名返回不同结果
        def get_module_side_effect(name: str):
            if name == "mock":
                return MockCommandModule()
            return None

        reg.get_module.side_effect = get_module_side_effect

        reg.get_all_commands.return_value = {}
        reg.get_all_aliases.return_value = {}
        reg.get_command_info.return_value = None

        return reg

    @pytest.fixture
    def completer(self, registry: MagicMock) -> AutoCompleter:
        """自动补全器 fixture。"""
        return AutoCompleter(registry)

    def test_refresh_invalidates_cache(self, completer: AutoCompleter) -> None:
        """测试刷新使缓存失效。"""
        # 第一次构建
        dict1 = completer.build_completion_dict()
        assert completer._completion_dict is not None

        # 刷新
        completer.refresh()

        # 缓存应该被清除
        assert completer._completion_dict is None

        # 重新构建会生成新缓存
        dict2 = completer.build_completion_dict()
        assert completer._completion_dict is not None
        assert dict1 == dict2  # 内容相同，但缓存被重新生成

    def test_register_lazy_commands(self, completer: AutoCompleter) -> None:
        """测试注册懒加载命令。"""
        # 注册懒加载命令
        completer.register_lazy_commands("database", ["connect", "query", "disconnect"])

        # 验证命令已注册
        assert "database" in completer._lazy_module_commands
        assert completer._lazy_module_commands["database"] == ["connect", "disconnect", "query"]

        # 验证缓存被刷新
        assert completer._completion_dict is None

    def test_register_lazy_commands_merge(
        self, completer: AutoCompleter
    ) -> None:
        """测试懒加载命令合并。"""
        # 第一次注册
        completer.register_lazy_commands("database", ["connect", "query"])

        # 第二次注册（追加）
        completer.register_lazy_commands("database", ["disconnect", "backup"])

        # 验证合并（去重并排序）
        assert completer._lazy_module_commands["database"] == [
            "backup",
            "connect",
            "disconnect",
            "query",
        ]

    def test_build_completion_dict(self, completer: AutoCompleter) -> None:
        """测试构建补全字典。"""
        # 构建补全字典
        completion_dict = completer.build_completion_dict()

        # 验证基本结构
        assert "" in completion_dict  # 顶层补全
        assert "mock" in completion_dict  # 模块命令补全
        assert "mk" in completion_dict  # 短别名补全

        # 验证顶层包含核心命令和模块名
        top_level = completion_dict[""]
        assert "status" in top_level
        assert "exit" in top_level
        assert "mock" in top_level
        assert "mk" in top_level

    def test_build_completion_dict_with_lazy_commands(
        self, completer: AutoCompleter
    ) -> None:
        """测试构建包含懒加载命令的补全字典。"""
        # 注册懒加载命令
        completer.register_lazy_commands("database", ["connect", "query"])

        # 构建补全字典
        completion_dict = completer.build_completion_dict()

        # 验证懒加载模块在顶层
        assert "database" in completion_dict[""]

        # 验证懒加载模块的子命令
        assert "database" in completion_dict
        assert completion_dict["database"] == ["connect", "query"]

    def test_get_short_alias(self, completer: AutoCompleter) -> None:
        """测试获取短别名。"""
        # MockModule 有别名 "mk"
        short_alias = completer._get_short_alias("mock")
        assert short_alias == "mk"

        # 不存在的模块
        short_alias = completer._get_short_alias("nonexistent")
        assert short_alias is None

    def test_resolve_module_alias(self, completer: AutoCompleter) -> None:
        """测试解析模块短别名。"""
        # 解析短别名
        full_name = completer._resolve_module_alias("mk")
        assert full_name == "mock"

        # 不存在的别名
        full_name = completer._resolve_module_alias("unknown")
        assert full_name is None

    def test_resolve_alias(self, completer: AutoCompleter) -> None:
        """测试解析命令别名。"""
        # 设置别名映射
        completer._registry.get_all_aliases.return_value = {"db": "database", "db conn": "database connect"}

        # 解析简单别名
        resolved = completer._resolve_alias("db")
        assert resolved == "database"

        # 解析嵌套别名
        resolved = completer._resolve_alias("db conn")
        assert resolved == "database connect"

        # 非别名保持不变
        resolved = completer._resolve_alias("status")
        assert resolved == "status"

    def test_extract_command_description(self) -> None:
        """测试从命令处理函数提取描述。"""

        def mock_command():
            """这是命令的描述。

            更多细节...
            """
            pass

        # 提取描述
        desc = AutoCompleter(MagicMock())._extract_command_description(mock_command)
        assert desc == "这是命令的描述。"

    def test_build_parameter_completions(self, completer: AutoCompleter) -> None:
        """测试构建参数补全。"""

        # 创建 Pydantic 模型
        class ConnectArgs(BaseModel):
            """连接参数。"""

            host: str = Field(..., description="主机地址")
            port: int = Field(default=22, description="端口号")

        # 创建原始函数
        def mock_connect_original(self, args: ConnectArgs) -> None:
            """连接命令。"""
            pass

        # 创建 typed_command wrapper（手动模拟）
        def mock_connect_wrapper(cli_context, arg_str: str) -> None:
            pass

        # 设置typed_command属性（_typed_model在原始函数上）
        mock_connect_wrapper._original_func = mock_connect_original
        mock_connect_original._typed_model = ConnectArgs

        # 模拟注册表返回这个命令
        completer._registry.get_all_commands.return_value = {
            "database connect": ("database", "connect", mock_connect_wrapper)
        }

        # 构建参数补全
        param_dict = completer._build_parameter_completions()

        # 验证参数补全
        assert "database connect" in param_dict
        params = param_dict["database connect"]
        assert "--host" in params
        assert "-h" in params
        assert "--port" in params
        assert "-p" in params

    def test_get_parameter_description(self, completer: AutoCompleter) -> None:
        """测试从 Pydantic 模型提取参数描述。"""

        class ConnectArgs(BaseModel):
            """连接参数。"""

            host: str = Field(..., description="主机地址")
            port: int = Field(default=22, ge=1, le=65535, description="端口号")

        # 创建原始函数
        def mock_connect_original(self, args: ConnectArgs) -> None:
            """连接命令。"""
            pass

        # 创建 typed_command wrapper（手动模拟）
        def mock_connect_wrapper(cli_context, arg_str: str) -> None:
            pass

        # 设置typed_command属性（_typed_model在原始函数上）
        mock_connect_wrapper._original_func = mock_connect_original
        mock_connect_original._typed_model = ConnectArgs

        # 模拟命令信息
        completer._registry.get_command_info.return_value = ("database", "connect", mock_connect_wrapper)

        # 提取参数描述
        desc = completer._get_parameter_description("--host", "database connect")
        assert desc == "主机地址"

        desc = completer._get_parameter_description("--port", "database connect")
        assert desc == "端口号"

    def test_get_completion_meta_for_module(self, completer: AutoCompleter) -> None:
        """测试获取模块补全的元数据。"""
        # MockModule 的描述是 "Mock module"
        meta = completer._get_completion_meta("mock", "")
        assert meta == "Mock module"

        # 短别名也应该能解析
        meta = completer._get_completion_meta("mk", "")
        assert meta == "Mock module"

    def test_get_completion_meta_for_command(self, completer: AutoCompleter) -> None:
        """测试获取命令补全的元数据。"""

        def status_cmd():
            """显示系统状态。"""
            pass

        # 确保get_module对"status"返回None（不是模块）
        completer._registry.get_module.side_effect = lambda name: MockCommandModule() if name == "mock" else None

        # 模拟命令信息
        completer._registry.get_command_info.return_value = ("core", "status", status_cmd)

        # 提取命令描述
        meta = completer._get_completion_meta("status", "")
        assert meta == "显示系统状态。"

    def test_empty_completion(self, completer: AutoCompleter) -> None:
        """测试空补全场景。"""
        # 创建空的 Document
        from unittest.mock import Mock

        doc = Mock()
        doc.text_before_cursor = ""
        doc.text = ""

        # 创建 CompleteEvent
        event = Mock()

        # 获取补全（应该返回空列表）
        completions = list(completer.get_completions(doc, event))
        assert len(completions) == 0

    def test_context_aware_completion(self, completer: AutoCompleter) -> None:
        """测试上下文感知补全。"""
        from unittest.mock import Mock

        # 测试顶层补全（输入 "st"）
        doc = Mock()
        doc.text_before_cursor = "st"
        doc.text = "st"
        event = Mock()

        completions = list(completer.get_completions(doc, event))
        # 应该补全 "status"
        assert any(c.text == "status" for c in completions)

    def test_alias_completion_in_dict(self, completer: AutoCompleter) -> None:
        """测试别名补全在补全字典中。"""
        # 设置别名
        completer._registry.get_all_aliases.return_value = {
            "db": "database",
            "db conn": "database connect",
        }

        # 构建补全字典
        completion_dict = completer.build_completion_dict()

        # 验证别名模块存在
        assert "db" in completion_dict

        # 验证别名子命令存在
        assert "conn" in completion_dict["db"]

    def test_cache_performance(self, completer: AutoCompleter) -> None:
        """测试缓存性能优化。"""
        # 第一次构建（会生成缓存）
        dict1 = completer.build_completion_dict()
        assert completer._completion_dict is not None

        # 第二次构建（应该使用缓存）
        dict2 = completer.build_completion_dict()
        assert dict1 is dict2  # 同一个对象

        # 刷新后缓存失效
        completer.refresh()
        assert completer._completion_dict is None

        # 重新构建会生成新缓存
        dict3 = completer.build_completion_dict()
        assert completer._completion_dict is not None
        # 内容相同但对象可能不同（由于模块列表可能变化）
        assert dict3 == dict1 or dict3 is not dict1
