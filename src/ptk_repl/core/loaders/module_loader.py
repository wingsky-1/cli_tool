"""模块加载器（简化版）。"""

import importlib
from typing import TYPE_CHECKING

from ptk_repl.core.resolvers import IModuleNameResolver

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


class ModuleLoader:
    """模块加载器（简化版）。

    仅负责加载模块，不负责发现和注册。

    Example:
        >>> loader = ModuleLoader(name_resolver)
        >>> module = loader.load("ssh")
        >>> loader.is_loaded("ssh")
        True
    """

    def __init__(self, name_resolver: IModuleNameResolver) -> None:
        """初始化模块加载器。

        Args:
            name_resolver: 模块名称解析器
        """
        self._name_resolver = name_resolver
        self._loaded_modules: dict[str, CommandModule] = {}

    def load(self, module_name: str) -> "CommandModule | None":
        """加载模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败则返回 None
        """
        # 如果已经加载，直接返回
        if module_name in self._loaded_modules:
            return self._loaded_modules[module_name]

        try:
            # 动态导入模块
            module_path = f"ptk_repl.modules.{module_name}"
            mod = importlib.import_module(module_path)

            # 使用解析器获取类名前缀
            class_name_prefix = self._name_resolver.resolve_class_name(module_name)
            module_cls = getattr(mod, f"{class_name_prefix}Module")

            # 创建模块实例
            module: CommandModule = module_cls()
            self._loaded_modules[module_name] = module
            return module

        except Exception:
            return None

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载。

        Args:
            module_name: 模块名称

        Returns:
            是否已加载
        """
        return module_name in self._loaded_modules

    @property
    def loaded_modules(self) -> dict[str, "CommandModule"]:
        """已加载的模块字典（只读）。"""
        return self._loaded_modules.copy()

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载。

        Args:
            module_name: 模块名称
        """
        if not self.is_loaded(module_name):
            self.load(module_name)

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典。

        注意：新的 ModuleLoader 不支持懒加载，返回空字典。
        懒加载功能由 legacy_loader 提供。
        """
        return {}
