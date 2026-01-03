"""模块发现服务。"""

import importlib
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
    from ptk_repl.core.resolvers import IModuleNameResolver


class ModuleDiscoveryService:
    """模块发现服务。

    负责从文件系统和 Python 包中发现可用模块。
    """

    def __init__(self, modules_path: Path) -> None:
        """初始化发现服务。

        Args:
            modules_path: 模块目录路径
        """
        self._modules_path = modules_path

    def discover(self) -> list[str]:
        """发现所有可用模块。

        Returns:
            模块名称列表（按字母顺序排序）
        """
        if not self._modules_path.exists():
            return []

        module_dirs = [
            d.name
            for d in self._modules_path.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        return sorted(module_dirs)

    def preload_all(
        self,
        tracker: "LazyModuleTracker",
        name_resolver: "IModuleNameResolver",
        exclude: list[str] | None = None,
    ) -> None:
        """预加载所有可用模块到追踪器。

        Args:
            tracker: 懒加载追踪器
            name_resolver: 名称解析器
            exclude: 要排除的模块列表（如 ["core"]）
        """
        exclude = exclude or []

        try:
            # 导入 modules 包
            modules_package = importlib.import_module("ptk_repl.modules")

            # 遍历所有模块
            for _, module_name, _ in pkgutil.iter_modules(modules_package.__path__):
                if module_name in exclude:
                    continue

                # 检查是否已经在追踪器中
                if tracker.is_loaded(module_name):
                    continue

                # 预加载模块类
                self._preload_module_class(module_name, tracker, name_resolver)

        except Exception:
            # 静默失败，模块加载时会再次尝试
            pass

    def _preload_module_class(
        self,
        module_name: str,
        tracker: "LazyModuleTracker",
        name_resolver: "IModuleNameResolver",
    ) -> None:
        """预加载模块类到追踪器。

        Args:
            module_name: 模块名称
            tracker: 懒加载追踪器
            name_resolver: 名称解析器
        """
        try:
            module_path = f"ptk_repl.modules.{module_name}"
            mod = importlib.import_module(module_path)

            class_name_prefix = name_resolver.resolve_class_name(module_name)
            module_cls = getattr(mod, f"{class_name_prefix}Module")

            tracker.add_lazy_module(module_name, module_cls)

        except Exception:
            # 静默失败，模块加载时会再次尝试
            pass
