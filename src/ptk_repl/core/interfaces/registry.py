"""注册表公共接口。"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IRegistry(Protocol):
    """注册表公共接口。

    提供对命令注册表的只读访问，避免直接访问私有成员。
    """

    def get_all_commands(self) -> dict[str, Any]:
        """获取所有命令的副本。

        Returns:
            命令字典的副本 {command_name: command_info}
            - command_name: 命令名称
            - command_info: 命令信息字典

        Note:
            返回的是副本，修改返回值不会影响原始注册表。

        Examples:
            >>> commands = registry.get_all_commands()
            >>> "help" in commands
            True
        """
        ...

    def get_all_aliases(self) -> dict[str, str]:
        """获取所有别名的副本。

        Returns:
            别名字典的副本 {alias: command_name}
            - alias: 别名
            - command_name: 对应的命令名称

        Note:
            返回的是副本，修改返回值不会影响原始注册表。

        Examples:
            >>> aliases = registry.get_all_aliases()
            >>> aliases["h"]
            "help"
        """
        ...
