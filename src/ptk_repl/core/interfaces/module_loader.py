"""模块加载器接口。"""

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


@runtime_checkable
class IModuleLoader(Protocol):
    """模块加载器接口。

    负责模块的加载、跟踪和懒加载管理。
    """

    def load(self, module_name: str) -> "CommandModule | None":
        """加载模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败则返回 None

        Examples:
            >>> loader = ModuleLoader(...)
            >>> module = loader.load("ssh")
            >>> assert module.name == "ssh"
        """
        ...

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载。

        Args:
            module_name: 模块名称

        Returns:
            是否已加载

        Examples:
            >>> loader.load("database")
            >>> loader.is_loaded("database")
            True
            >>> loader.is_loaded("ssh")
            False
        """
        ...

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载（懒加载）。

        如果模块尚未加载，则加载并注册它。

        Args:
            module_name: 模块名称
        """
        ...

    @property
    def loaded_modules(self) -> dict[str, "CommandModule"]:
        """已加载的模块字典。"""
        ...

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典（未加载的模块类）。"""
        ...
