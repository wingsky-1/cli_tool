"""测试 PromptProvider 提示符提供者。"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.prompts.prompt_provider import PromptManager
from ptk_repl.core.interfaces.prompt_provider import IPromptProvider
from ptk_repl.core.state.state_manager import StateManager
from ptk_repl.state.global_state import GlobalState
from ptk_repl.state.connection_context import (
    ConnectionType,
    SSHConnectionContext,
    DatabaseConnectionContext,
)


# ===== 测试类 =====


class TestPromptManager:
    """PromptManager 测试。"""

    @pytest.fixture
    def state_manager(self) -> StateManager:
        """状态管理器 fixture。"""
        return StateManager()

    @pytest.fixture
    def prompt_manager(self, state_manager: StateManager) -> PromptManager:
        """PromptManager fixture。"""
        return PromptManager(state_manager)

    def test_default_prompt(self, prompt_manager: PromptManager) -> None:
        """测试默认提示符（未连接状态）。"""
        prompt = prompt_manager.get_prompt()
        assert prompt == "(ptk) > "

    def test_ssh_connection_prompt(self, prompt_manager: PromptManager) -> None:
        """测试 SSH 连接提示符（使用多态方法）。"""
        gs = prompt_manager.state_manager.global_state

        # 设置 SSH 连接上下文
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("prod", host="web-server-1")

        gs.set_connection_context(ssh_ctx)

        prompt = prompt_manager.get_prompt()

        # 应该使用 SSH 连接的多态方法
        assert "prod" in prompt
        assert "(ptk:" in prompt

    def test_database_connection_prompt(self, prompt_manager: PromptManager) -> None:
        """测试数据库连接提示符（使用多态方法）。"""
        gs = prompt_manager.state_manager.global_state

        # 设置数据库连接上下文
        db_ctx = DatabaseConnectionContext()
        db_ctx.set_database("mydb", host="localhost", port=5432)

        gs.set_connection_context(db_ctx)

        prompt = prompt_manager.get_prompt()

        # 应该使用数据库连接的多态方法
        assert "mydb" in prompt
        assert "(ptk:" in prompt

    def test_legacy_host_port_prompt(self, prompt_manager: PromptManager) -> None:
        """测试兼容旧版本的提示符（主机:端口格式）。"""
        gs = prompt_manager.state_manager.global_state

        # 设置 connected=True 但没有活跃的连接上下文
        gs.connected = True
        gs.current_host = "example.com"
        gs.current_port = 8080

        prompt = prompt_manager.get_prompt()

        # 应该显示主机和端口
        assert "example.com" in prompt
        assert "8080" in prompt
        assert "(ptk:" in prompt

    def test_no_active_connection_context(self, prompt_manager: PromptManager) -> None:
        """测试 connected=True 但没有活跃连接上下文的情况。"""
        gs = prompt_manager.state_manager.global_state

        # 设置 connected=True 但没有连接上下文
        gs.connected = True
        gs.current_host = None
        gs.current_port = None

        prompt = prompt_manager.get_prompt()

        # 应该回退到默认提示符
        assert prompt == "(ptk) > "

    def test_ssh_connection_disconnected_state(self, prompt_manager: PromptManager) -> None:
        """测试 SSH 连接上下文但 is_connected() 返回 False。"""
        gs = prompt_manager.state_manager.global_state

        # 设置 SSH 连接上下文但未连接
        ssh_ctx = SSHConnectionContext()
        # 保持 _is_connected=False，模拟未连接状态

        gs.set_connection_context(ssh_ctx)

        prompt = prompt_manager.get_prompt()

        # 应该回退到默认提示符
        assert prompt == "(ptk) > "

    def test_database_connection_disconnected_state(self, prompt_manager: PromptManager) -> None:
        """测试数据库连接上下文但 is_connected() 返回 False。"""
        gs = prompt_manager.state_manager.global_state

        # 设置数据库连接上下文但未连接
        db_ctx = DatabaseConnectionContext()
        # 保持 _is_connected=False，模拟未连接状态

        gs.set_connection_context(db_ctx)

        prompt = prompt_manager.get_prompt()

        # 应该回退到默认提示符
        assert prompt == "(ptk) > "


class TestIPromptProviderProtocol:
    """IPromptProvider Protocol 测试。"""

    def test_prompt_manager_implements_protocol(self) -> None:
        """测试 PromptManager 实现 IPromptProvider 接口。"""
        state_manager = StateManager()
        prompt_manager = PromptManager(state_manager)

        # 验证鸭子类型
        assert isinstance(prompt_manager, IPromptProvider)

    def test_custom_prompt_provider_duck_typing(self) -> None:
        """测试自定义提示符提供者的鸭子类型。"""

        class CustomPromptProvider:
            """自定义提示符提供者。"""

            def get_prompt(self) -> str:
                return "custom > "

        provider = CustomPromptProvider()

        # 验证鸭子类型
        assert isinstance(provider, IPromptProvider)
        assert provider.get_prompt() == "custom > "

    def test_incomplete_implementation_not_recognized(self) -> None:
        """测试不完整的实现不被识别为 IPromptProvider。"""

        class IncompleteProvider:
            """不完整的提供者（缺少 get_prompt 方法）。"""

            def some_other_method(self) -> str:
                return "incomplete"

        provider = IncompleteProvider()

        # 不应该被识别为 IPromptProvider
        assert not isinstance(provider, IPromptProvider)

    def test_protocol_duck_typing_with_runtime_checkable(self) -> None:
        """测试 @runtime_checkable 装饰器的功能。"""
        # IPromptProvider 使用了 @runtime_checkable
        # 因此 isinstance() 检查应该在运行时工作

        class ValidProvider:
            def get_prompt(self) -> str:
                return "valid"

        provider = ValidProvider()

        # isinstance() 应该返回 True
        assert isinstance(provider, IPromptProvider)

        # 验证可以调用方法
        assert hasattr(provider, "get_prompt")
        assert callable(provider.get_prompt)


class TestPromptManagerIntegration:
    """PromptManager 集成测试。"""

    def test_prompt_changes_with_connection_state(self) -> None:
        """测试提示符随连接状态变化。"""
        state_manager = StateManager()
        prompt_manager = PromptManager(state_manager)
        gs = state_manager.global_state

        # 初始状态
        assert prompt_manager.get_prompt() == "(ptk) > "

        # 连接到 SSH
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("prod", host="web-1")

        gs.set_connection_context(ssh_ctx)

        prompt_with_ssh = prompt_manager.get_prompt()
        assert "prod" in prompt_with_ssh

        # 断开连接
        gs.clear_connection_context()

        assert prompt_manager.get_prompt() == "(ptk) > "

    def test_multiple_connection_contexts_priority(self) -> None:
        """测试多个连接上下文的优先级。"""
        state_manager = StateManager()
        prompt_manager = PromptManager(state_manager)
        gs = state_manager.global_state

        # 设置 SSH 连接
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("prod", host="web-1")
        gs.set_connection_context(ssh_ctx)

        prompt = prompt_manager.get_prompt()

        # 应该使用 SSH 上下文（因为只有一个活跃连接）
        assert "prod" in prompt

    def test_prompt_format_consistency(self) -> None:
        """测试提示符格式一致性。"""
        state_manager = StateManager()
        prompt_manager = PromptManager(state_manager)

        # 默认提示符应该以 "> " 结尾
        assert prompt_manager.get_prompt().endswith("> ")

        # 所有提示符都应该包含 "(ptk:" 前缀（当 connected 时）
        gs = state_manager.global_state
        gs.connected = True
        gs.current_host = "localhost"
        gs.current_port = 8080

        prompt = prompt_manager.get_prompt()
        assert "(ptk:" in prompt
        assert prompt.endswith("> ")
