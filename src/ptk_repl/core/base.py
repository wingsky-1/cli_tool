"""命令模块抽象基类。"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager


class CommandModule(ABC):
    """命令模块抽象基类。

    所有模块必须继承此类并实现所需的方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """模块名称（如 'database'）。"""
        pass

    @property
    def description(self) -> str:
        """模块描述。"""
        return ""

    @property
    def aliases(self) -> list[str]:
        """模块别名列表（如 ['db']）。"""
        return []

    @property
    def version(self) -> str:
        """模块版本。"""
        return "1.0.0"

    @abstractmethod
    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册模块的所有命令到 CLI。

        Args:
            cli: PromptToolkitCLI 实例
        """
        pass

    def initialize(self, state_manager: "StateManager") -> None:  # noqa: B027
        """模块初始化回调（可选）。

        在模块加载后调用，可用于初始化模块状态。

        Args:
            state_manager: 状态管理器实例
        """
        pass

    def shutdown(self) -> None:  # noqa: B027
        """模块关闭回调（可选）。

        在 CLI 退出前调用，可用于清理资源。
        """
        pass
