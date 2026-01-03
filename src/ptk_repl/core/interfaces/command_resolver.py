"""命令解析器接口。"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ICommandResolver(Protocol):
    """命令解析器接口。

    负责将用户输入的命令字符串解析为模块名和命令名。
    """

    def resolve(self, command_str: str) -> tuple[str | None, str]:
        """解析命令字符串。

        Args:
            command_str: 命令字符串（如 "db connect"）

        Returns:
            (module_name, command_name) 元组
            - module_name: 模块名（如 "database"），如果是 core 模块则为 None
            - command_name: 命令名（如 "connect"）

        Examples:
            >>> resolver.resolve("db connect")
            ("database", "connect")
            >>> resolver.resolve("help")
            (None, "help")
        """
        ...
