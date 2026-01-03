"""测试错误处理系统。"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.error_handling.error_handlers import (
    BaseErrorHandler,
    CLIErrorHandler,
    ErrorHandlerChain,
    IErrorHandler,
    get_default_error_handler_chain,
)
from ptk_repl.core.exceptions.cli_exceptions import (
    CLIException,
    CommandException,
    ConfigurationException,
    ConnectionException,
    ModuleException,
    ValidationException,
)


def test_exception_hierarchy() -> None:
    """测试异常层次结构。"""
    # 基础异常
    exc = CLIException("基础错误", {"key": "value"})
    assert exc.message == "基础错误"
    assert exc.details == {"key": "value"}
    assert "基础错误" in str(exc)

    # 命令异常
    cmd_exc = CommandException("命令失败")
    assert isinstance(cmd_exc, CLIException)
    assert cmd_exc.message == "命令失败"

    # 模块异常
    mod_exc = ModuleException("模块加载失败")
    assert isinstance(mod_exc, CLIException)

    # 验证异常
    val_exc = ValidationException("参数无效")
    assert isinstance(val_exc, CLIException)

    # 连接异常
    conn_exc = ConnectionException("连接超时")
    assert isinstance(conn_exc, CLIException)

    # 配置异常
    config_exc = ConfigurationException("配置文件不存在")
    assert isinstance(config_exc, CLIException)

    print("✅ 异常层次结构测试通过")


def test_error_handlers() -> None:
    """测试错误处理器。"""
    # CLI 错误处理器
    cli_handler = CLIErrorHandler()
    assert cli_handler.can_handle(CLIException("测试"))
    assert not cli_handler.can_handle(ValueError("普通错误"))

    # 基础错误处理器
    base_handler = BaseErrorHandler()
    assert base_handler.can_handle(Exception("任何错误"))

    print("✅ 错误处理器测试通过")


def test_error_handler_chain() -> None:
    """测试错误处理链。"""
    # 创建处理链
    chain = ErrorHandlerChain([CLIErrorHandler(), BaseErrorHandler()])

    # 测试 CLI 异常
    cli_exc = CLIException("CLI 错误")
    assert chain.handle(cli_exc) is True  # CLIErrorHandler 处理

    # 测试普通异常
    normal_exc = ValueError("普通错误")
    assert chain.handle(normal_exc) is True  # BaseErrorHandler 处理

    print("✅ 错误处理链测试通过")


def test_protocol_duck_typing() -> None:
    """测试 Protocol 的鸭子类型。"""
    # 自定义错误处理器
    class CustomHandler:
        def can_handle(self, error: Exception) -> bool:
            return isinstance(error, ValueError)

        def handle(self, error: Exception) -> None:
            print(f"自定义处理: {error}")

    handler = CustomHandler()
    assert isinstance(handler, IErrorHandler), "应该兼容接口"
    assert handler.can_handle(ValueError("test"))
    assert not handler.can_handle(CLIException("test"))

    print("✅ Protocol 鸭子类型测试通过")


def test_default_error_handler_chain() -> None:
    """测试默认错误处理链。"""
    chain = get_default_error_handler_chain()
    assert isinstance(chain, ErrorHandlerChain)

    # 测试处理能力
    assert chain.handle(CLIException("测试")) is True
    assert chain.handle(ValueError("测试")) is True

    print("✅ 默认错误处理链测试通过")


if __name__ == "__main__":
    test_exception_hierarchy()
    test_error_handlers()
    test_error_handler_chain()
    test_protocol_duck_typing()
    test_default_error_handler_chain()
    print("\n🎉 所有错误处理测试通过！")
    print("\n📝 重构总结：")
    print("  - CLIException 异常层次结构定义成功")
    print("  - IErrorHandler Protocol 接口")
    print("  - CLIErrorHandler 和 BaseErrorHandler 实现")
    print("  - ErrorHandlerChain 责任链模式")
    print("  - 支持自定义错误处理器")
    print("\n✨ 阶段 7：错误处理统一（新增能力）- 完成！")
    print("\n🎊 所有 7 个重构阶段全部完成！")


# ===== 新增 pytest 风格测试类 =====


class TestErrorHandlerChain:
    """错误处理链测试（pytest 风格）。"""

    def test_cli_error_handler_with_details(self, capsys: pytest.CaptureFixture) -> None:
        """测试带详情的错误处理。"""
        cli_handler = CLIErrorHandler()

        # 创建带详情的异常
        exc = CLIException("命令执行失败", details={"host": "localhost", "port": 22})

        # 处理异常
        assert cli_handler.can_handle(exc)
        cli_handler.handle(exc)

        # 验证输出
        captured = capsys.readouterr()
        assert "命令执行失败" in captured.out
        assert "详情" in captured.out
        assert "localhost" in captured.out

    def test_error_handler_chain_priority(self, capsys: pytest.CaptureFixture) -> None:
        """测试处理链优先级。"""
        # 创建处理链（CLI -> Base）
        chain = ErrorHandlerChain([CLIErrorHandler(), BaseErrorHandler()])

        # 测试 CLI 异常（应该被 CLIErrorHandler 处理）
        cli_exc = CLIException("CLI 错误")
        chain.handle(cli_exc)

        captured = capsys.readouterr()
        # CLIErrorHandler 使用红色输出
        assert "CLI 错误" in captured.out

        # 测试普通异常（应该被 BaseErrorHandler 处理）
        normal_exc = ValueError("普通错误")
        chain.handle(normal_exc)

        captured = capsys.readouterr()
        # BaseErrorHandler 使用普通输出
        assert "错误: 普通错误" in captured.out

    def test_base_handler_fallback(self) -> None:
        """测试基础处理器兜底。"""
        # 只包含 BaseErrorHandler 的处理链
        chain = ErrorHandlerChain([BaseErrorHandler()])

        # 测试任何异常都应该被处理
        exc = ValueError("普通错误")
        chain.handle(exc)  # 不应该抛出异常

    def test_exception_hierarchy(self) -> None:
        """测试异常层次结构。"""
        # CLIException 是基类
        base_exc = CLIException("基础错误")
        assert isinstance(base_exc, CLIException)
        assert base_exc.message == "基础错误"

        # CommandException 继承自 CLIException
        cmd_exc = CommandException("命令失败")
        assert isinstance(cmd_exc, CLIException)
        assert isinstance(cmd_exc, CommandException)

        # ModuleException 继承自 CLIException
        mod_exc = ModuleException("模块加载失败")
        assert isinstance(mod_exc, CLIException)
        assert isinstance(mod_exc, ModuleException)

    def test_custom_exception(self) -> None:
        """测试自定义异常。"""
        # 定义自定义异常
        class SSHException(CLIException):
            """SSH 模块专用异常。"""
            pass

        # 创建异常实例
        ssh_exc = SSHException("SSH 连接失败", details={"host": "example.com", "port": 22})

        # 验证类型
        assert isinstance(ssh_exc, CLIException)
        assert isinstance(ssh_exc, SSHException)
        assert ssh_exc.message == "SSH 连接失败"
        assert ssh_exc.details == {"host": "example.com", "port": 22}

        # 验证可以被错误处理器处理
        cli_handler = CLIErrorHandler()
        assert cli_handler.can_handle(ssh_exc)

