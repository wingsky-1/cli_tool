"""注册表公共接口。"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


# 命令信息类型：(模块名, 命令名, 处理函数)
CommandInfo = tuple[str, str, Callable]


@runtime_checkable
class IRegistry(Protocol):
    """注册表公共接口。

    提供对命令注册表的完整访问接口。
    """

    def get_all_commands(self) -> dict[str, CommandInfo]:
        """获取所有命令的副本。

        Returns:
            命令字典的副本 {command_name: command_info}
        """
        ...

    def get_all_aliases(self) -> dict[str, str]:
        """获取所有别名的副本。

        Returns:
            别名字典的副本 {alias: command_name}
        """
        ...

    def get_command_info(self, command_str: str) -> CommandInfo | None:
        """获取命令信息。

        Args:
            command_str: 命令字符串

        Returns:
            (module_name, command_name, handler) 元组，如果命令不存在则返回 None
        """
        ...

    def get_module(self, module_name: str) -> "CommandModule | None":
        """获取模块实例。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果不存在则返回 None
        """
        ...

    def list_modules(self) -> list["CommandModule"]:
        """列出所有已注册的模块。

        Returns:
            模块对象列表
        """
        ...

    def list_module_commands(self, module_name: str) -> list[str]:
        """列出模块的所有命令。

        Args:
            module_name: 模块名称

        Returns:
            命令名称列表（不含模块前缀）
        """
        ...

    def set_completer(self, completer: object) -> None:
        """设置补全器。

        Args:
            completer: 补全器实例（AutoCompleter 或兼容对象）
        """
        ...
