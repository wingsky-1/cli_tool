"""错误处理接口和实现。

使用责任链模式处理不同类型的错误。
"""

from typing import Protocol, runtime_checkable

from ptk_repl.core.exceptions import CLIException


@runtime_checkable
class IErrorHandler(Protocol):
    """错误处理器接口。

    使用 Protocol 支持鸭子类型。
    """

    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理此错误。

        Args:
            error: 异常对象

        Returns:
            是否可以处理
        """
        ...

    def handle(self, error: Exception) -> None:
        """处理错误。

        Args:
            error: 异常对象
        """
        ...


class BaseErrorHandler:
    """基础错误处理器。

    提供默认的错误处理行为。
    """

    def can_handle(self, error: Exception) -> bool:
        """默认处理所有错误。"""
        return True

    def handle(self, error: Exception) -> None:
        """默认处理：打印错误消息。"""
        print(f"错误: {error}")


class CLIErrorHandler:
    """CLI 错误处理器。

    专门处理 CLIException 及其子类。
    """

    def can_handle(self, error: Exception) -> bool:
        """检查是否为 CLI 异常。"""
        return isinstance(error, CLIException)

    def handle(self, error: Exception) -> None:
        """处理 CLI 异常。"""
        if isinstance(error, CLIException):
            # 使用红色文本显示错误
            from colorama import Fore, Style, init

            init(autoreset=True)
            print(f"{Fore.LIGHTRED_EX}{Style.BRIGHT}错误: {error}{Style.RESET_ALL}")
            if error.details:
                print(f"{Fore.LIGHTRED_EX}详情: {error.details}{Style.RESET_ALL}")


class ErrorHandlerChain:
    """错误处理链（责任链模式）。

    按顺序尝试每个处理器，直到有一个能够处理错误。
    """

    def __init__(self, handlers: list[IErrorHandler]) -> None:
        """初始化错误处理链。

        Args:
            handlers: 错误处理器列表（按优先级排序）
        """
        self._handlers = handlers

    def handle(self, error: Exception) -> bool:
        """处理错误。

        Args:
            error: 异常对象

        Returns:
            是否成功处理（如果有处理器能处理则返回 True）
        """
        for handler in self._handlers:
            if handler.can_handle(error):
                handler.handle(error)
                return True
        return False

    def add_handler(self, handler: IErrorHandler) -> None:
        """添加错误处理器。

        Args:
            handler: 错误处理器
        """
        self._handlers.append(handler)


def get_default_error_handler_chain() -> ErrorHandlerChain:
    """获取默认的错误处理链。

    Returns:
        配置好的错误处理链
    """
    return ErrorHandlerChain(
        [
            CLIErrorHandler(),  # 优先处理 CLI 异常
            BaseErrorHandler(),  # 处理其他所有异常
        ]
    )
