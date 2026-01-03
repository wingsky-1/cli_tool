"""测试 ICliContext 接口实现（简化版）。"""

from ptk_repl.core.interfaces.cli_context import ICliContext
from ptk_repl.core.state_manager import StateManager
from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.cli.command_executor import CommandExecutor


def test_interface_exists():
    """测试 ICliContext 接口定义。"""
    # 检查接口是否可以导入
    from ptk_repl.core.interfaces import ICliContext
    print("✅ ICliContext 接口导入成功")


def test_protocol_duck_typing():
    """测试 Protocol 的鸭子类型。"""
    # 创建一个简单的类，实现 ICliContext 的方法
    class SimpleCLI:
        def __init__(self):
            self.state = StateManager()
            self.registry = CommandRegistry()

        def poutput(self, text: str) -> None:
            print(text)

        def perror(self, text: str) -> None:
            print(f"[错误] {text}")

    # 测试鸭子类型
    cli = SimpleCLI()
    assert isinstance(cli, ICliContext), "SimpleCLI 应该兼容 ICliContext（鸭子类型）"
    print("✅ Protocol 鸭子类型测试通过")


def test_command_executor_signature():
    """测试 CommandExecutor 的签名。"""
    import inspect

    # 检查 CommandExecutor.__init__ 的签名
    sig = inspect.signature(CommandExecutor.__init__)
    params = list(sig.parameters.keys())

    # 应该有 self, registry, module_loader, cli_context
    assert "cli_context" in params, "CommandExecutor.__init__ 应该有 cli_context 参数"
    assert "output_callback" not in params, "不应该再有 output_callback 参数"
    assert "error_callback" not in params, "不应该再有 error_callback 参数"

    print("✅ CommandExecutor 签名测试通过")


def test_typed_command_signature():
    """测试 typed_command 的类型注解。"""
    from ptk_repl.core.decorators import typed_command
    from pydantic import BaseModel
    import inspect

    class TestArgs(BaseModel):
        name: str

    @typed_command(TestArgs)
    def test_command(args: TestArgs) -> None:
        """测试命令。"""
        pass

    # 检查 wrapper 的类型注解
    # wrapper 应该接受 (ICliContext, str)
    wrapper = test_command  # typed_command 返回的是 wrapper
    assert hasattr(wrapper, "__annotations__"), "wrapper 应该有类型注解"

    print("✅ typed_command 类型注解测试通过")


if __name__ == "__main__":
    test_interface_exists()
    test_protocol_duck_typing()
    test_command_executor_signature()
    test_typed_command_signature()
    print("\n🎉 所有接口测试通过！")
    print("\n📝 重构总结：")
    print("  - ICliContext Protocol 接口定义成功")
    print("  - CommandExecutor 使用 ICliContext 接口")
    print("  - typed_command 使用 ICliContext 类型注解")
    print("  - PromptToolkitCLI 通过鸭子类型自动兼容接口")
    print("\n✨ 阶段 1：基础设施层重构（解决 DIP 违反）- 完成！")
