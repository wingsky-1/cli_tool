"""模块发现器。"""

from pathlib import Path


class ModuleDiscoverer:
    """模块发现器实现。

    负责从文件系统中发现可用的模块。

    Example:
        >>> discoverer = ModuleDiscoverer(Path("/path/to/modules"))
        >>> modules = discoverer.discover()
        >>> ["core", "database", "ssh"]
    """

    def __init__(self, modules_path: Path) -> None:
        """初始化模块发现器。

        Args:
            modules_path: 模块目录路径
        """
        self._modules_path = modules_path

    def discover(self) -> list[str]:
        """发现所有可用模块。

        Returns:
            模块名称列表（按字母顺序排序）

        Examples:
            >>> discoverer.discover()
            ["core", "database", "ssh"]
        """
        if not self._modules_path.exists():
            return []

        module_dirs = [
            d.name
            for d in self._modules_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        return sorted(module_dirs)

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
        module_path = self._modules_path / module_name
        return module_path.exists() and module_path.is_dir()
