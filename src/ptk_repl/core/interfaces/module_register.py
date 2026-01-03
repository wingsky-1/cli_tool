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
