"""模块注册器接口。"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


@runtime_checkable
class IModuleRegister(Protocol):
    """模块注册器接口。

    负责将模块注册到 CLI 系统。
    """

    def register(self, module: "CommandModule") -> None:
        """注册模块到 CLI。

        Args:
            module: 模块实例

        Examples:
            >>> register = ModuleRegister(...)
            >>> module = SSHModule()
            >>> register.register(module)
            # 模块现在已注册并可用
        """
        ...

    def is_registered(self, module_name: str) -> bool:
        """检查模块是否已注册。

        Args:
            module_name: 模块名称

        Returns:
            是否已注册

        Examples:
            >>> register.is_registered("ssh")
            True
        """
        ...

    def get_module(self, module_name: str) -> "CommandModule | None":
        """获取已注册的模块实例。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果不存在则返回 None

        Examples:
            >>> module = register.get_module("ssh")
            >>> if module:
            ...     print(f"找到模块: {module.name}")
        """
        ...
