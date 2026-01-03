"""CLI 上下文接口。

定义 CLI 上下文的接口契约，使用 Protocol 支持鸭子类型。
任何实现了这些方法的对象都可以作为 CLI 上下文使用。
"""

from typing import Protocol, runtime_checkable

from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.state_manager import StateManager


@runtime_checkable
class ICliContext(Protocol):
    """CLI 上下文接口。

    提供命令执行所需的上下文能力，遵循依赖倒置原则。

    使用 Protocol 而非 ABC，支持鸭子类型：任何实现了这些方法的对象
    都自动兼容此接口，无需显式继承。

    Example:
        >>> class MyCLI:
        ...     def poutput(self, text: str) -> None:
        ...         print(text)
        ...
        ...     @property
        ...     def state(self) -> StateManager:
        ...         return self._state
        ...
        >>> cli = MyCLI()
        >>> isinstance(cli, ICliContext)  # 无需显式继承
        True
    """

    def poutput(self, text: str) -> None:
        """输出普通信息。

        Args:
            text: 输出文本
        """
        ...

    def perror(self, text: str) -> None:
        """输出错误信息。

        Args:
            text: 错误文本
        """
        ...

    @property
    def state(self) -> StateManager:
        """获取状态管理器。

        Returns:
            StateManager 实例
        """
        ...

    @property
    def registry(self) -> CommandRegistry:
        """获取命令注册表。

        Returns:
            CommandRegistry 实例
        """
        ...
