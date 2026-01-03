"""测试连接上下文。"""

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
