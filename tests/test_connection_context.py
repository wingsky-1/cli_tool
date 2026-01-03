"""测试连接上下文。"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.state.connection_context import (
    ConnectionContext,
    ConnectionType,
    DatabaseConnectionContext,
    SSHConnectionContext,
)
from ptk_repl.state.global_state import GlobalState


def test_ssh_connection_context():
    """测试 SSH 连接上下文。"""
    ctx = SSHConnectionContext()

    assert ctx.connection_type == ConnectionType.SSH
    assert not ctx.is_connected()

    ctx.set_env("production", "192.168.1.1", 22)
    assert ctx.is_connected()
    assert ctx.current_env == "production"

    ctx.disconnect()
    assert not ctx.is_connected()

    print("✅ SSHConnectionContext 测试通过")


def test_database_connection_context():
    """测试数据库连接上下文。"""
    ctx = DatabaseConnectionContext()

    assert ctx.connection_type == ConnectionType.DATABASE
    assert not ctx.is_connected()

    ctx.set_database("mydb", "localhost", 5432)
    assert ctx.is_connected()
    assert ctx.active_database == "mydb"

    ctx.disconnect()
    assert not ctx.is_connected()

    print("✅ DatabaseConnectionContext 测试通过")


def test_global_state_with_context():
    """测试 GlobalState 使用连接上下文。"""
    state = GlobalState()

    # 初始状态
    assert not state.connected
    assert state.get_connection_context() is None

    # 设置 SSH 上下文
    ssh_ctx = SSHConnectionContext()
    ssh_ctx.set_env("production", "192.168.1.1", 22)
    state.set_connection_context(ssh_ctx)

    assert state.connected
    assert state.get_connection_context() is ssh_ctx

    # 清除上下文
    state.clear_connection_context()
    assert not state.connected
    assert state.get_connection_context() is None

    print("✅ GlobalState 组合测试通过")


if __name__ == "__main__":
    test_ssh_connection_context()
    test_database_connection_context()
    test_global_state_with_context()
    print("\n🎉 所有连接上下文测试通过！")
    print("\n📝 阶段 3：状态管理重构（解决 LSP 违反）- 完成！")


# ===== 新增 pytest 风格测试类 =====


class TestConnectionContext:
    """连接上下文测试（pytest 风格）。"""

    def test_ssh_connection_context_lifecycle(self) -> None:
        """测试 SSH 连接上下文生命周期。"""
        ctx = SSHConnectionContext()

        # 初始状态
        assert ctx.connection_type == ConnectionType.SSH
        assert not ctx.is_connected()
        assert ctx.get_prompt_suffix() == "unknown"

        # 连接
        ctx.set_env("production", "192.168.1.1", 22)
        assert ctx.is_connected()
        assert ctx.current_env == "production"
        assert "production" in ctx.get_prompt_suffix()

        # 断开连接
        ctx.disconnect()
        assert not ctx.is_connected()
        assert ctx.get_prompt_suffix() == "unknown"

    def test_database_connection_context_lifecycle(self) -> None:
        """测试数据库连接上下文生命周期。"""
        ctx = DatabaseConnectionContext()

        # 初始状态
        assert ctx.connection_type == ConnectionType.DATABASE
        assert not ctx.is_connected()
        assert ctx.get_prompt_suffix() == "unknown"

        # 连接
        ctx.set_database("mydb", "localhost", 5432)
        assert ctx.is_connected()
        assert ctx.active_database == "mydb"
        assert "mydb" in ctx.get_prompt_suffix()

        # 断开连接
        ctx.disconnect()
        assert not ctx.is_connected()
        assert ctx.get_prompt_suffix() == "unknown"

    def test_global_state_composition(self) -> None:
        """测试 GlobalState 组合多个连接上下文。"""
        state = GlobalState()

        # 初始状态
        assert not state.connected
        assert state.get_connection_context() is None

        # 设置 SSH 上下文
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("production", "192.168.1.1", 22)
        state.set_connection_context(ssh_ctx)

        assert state.connected
        assert state.get_connection_context() is ssh_ctx
        assert isinstance(state.get_connection_context(), SSHConnectionContext)

        # 清除上下文
        state.clear_connection_context()
        assert not state.connected
        assert state.get_connection_context() is None

    def test_polymorphic_prompt_suffix(self) -> None:
        """测试多态提示符方法。"""
        # SSH 连接上下文
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("prod", "example.com", 22)
        ssh_suffix = ssh_ctx.get_prompt_suffix()
        assert "prod" in ssh_suffix

        # 数据库连接上下文
        db_ctx = DatabaseConnectionContext()
        db_ctx.set_database("testdb", "localhost", 5432)
        db_suffix = db_ctx.get_prompt_suffix()
        assert "testdb" in db_suffix

        # 验证多态：不同类型返回不同格式
        assert ssh_suffix != db_suffix

    def test_connection_type(self) -> None:
        """测试连接类型枚举。"""
        ssh_ctx = SSHConnectionContext()
        db_ctx = DatabaseConnectionContext()

        # SSH 类型
        assert ssh_ctx.connection_type == ConnectionType.SSH
        assert ssh_ctx.connection_type == "ssh"

        # 数据库类型
        assert db_ctx.connection_type == ConnectionType.DATABASE
        assert db_ctx.connection_type == "database"

        # 类型比较
        assert ssh_ctx.connection_type != db_ctx.connection_type

    def test_multiple_connections(self) -> None:
        """测试管理多个连接。"""
        # 创建多个连接上下文
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env("prod", "192.168.1.1", 22)

        db_ctx = DatabaseConnectionContext()
        db_ctx.set_database("mydb", "localhost", 5432)

        # 验证它们是独立的实例
        assert ssh_ctx is not db_ctx
        assert ssh_ctx.connection_type != db_ctx.connection_type
        assert ssh_ctx.is_connected()
        assert db_ctx.is_connected()

        # 验证各自的提示符
        ssh_suffix = ssh_ctx.get_prompt_suffix()
        db_suffix = db_ctx.get_prompt_suffix()
        assert ssh_suffix != db_suffix

        # 断开一个连接不影响另一个
        ssh_ctx.disconnect()
        assert not ssh_ctx.is_connected()
        assert db_ctx.is_connected()

