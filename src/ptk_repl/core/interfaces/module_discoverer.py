"""模块发现器接口。"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IModuleDiscoverer(Protocol):
    """模块发现器接口。

    负责发现和检查可用的模块。
    """

    def discover(self) -> list[str]:
        """发现所有可用模块。

        Returns:
            模块名称列表（按字母顺序排序）

        Examples:
            >>> discoverer.discover()
            ["core", "database", "ssh"]
        """
        ...

    def is_available(self, module_name: str) -> bool:
        """检查模块是否可用。

        Args:
            module_name: 模块名称

        Returns:
            是否可用

        Examples:
            >>> discoverer.is_available("ssh")
            True
            >>> discoverer.is_available("nonexistent")
            False
        """
        ...
