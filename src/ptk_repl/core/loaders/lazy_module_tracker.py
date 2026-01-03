"""懒加载模块追踪器。"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


class LazyModuleTracker:
    """懒加载模块追踪器。

    负责追踪哪些模块已加载、哪些模块待加载（懒加载），
    以及模块的别名信息。
    """

    def __init__(self) -> None:
        """初始化追踪器。"""
        self._lazy_modules: dict[str, type[CommandModule]] = {}
        self._loaded_modules: set[str] = set()
        self._alias_to_module: dict[str, str] = {}

    def add_lazy_module(self, module_name: str, module_cls: type[CommandModule]) -> None:
        """添加懒加载模块。

        Args:
            module_name: 模块名称
            module_cls: 模块类
        """
        self._lazy_modules[module_name] = module_cls

        # 缓存别名信息（创建临时实例检查）
        try:
            temp_instance = module_cls()
            if hasattr(temp_instance, "aliases") and temp_instance.aliases:
                self._alias_to_module[temp_instance.aliases] = module_name
        except Exception:
            # 如果创建实例失败，跳过别名缓存
            pass

    def mark_as_loaded(self, module_name: str) -> None:
        """标记模块为已加载。

        Args:
            module_name: 模块名称
        """
        self._loaded_modules.add(module_name)
        if module_name in self._lazy_modules:
            del self._lazy_modules[module_name]

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载。

        Args:
            module_name: 模块名称

        Returns:
            是否已加载
        """
        return module_name in self._loaded_modules

    def find_by_alias(self, alias: str) -> str | None:
        """通过别名查找模块名。

        Args:
            alias: 模块别名

        Returns:
            模块名称，如果未找到则返回 None
        """
        return self._alias_to_module.get(alias)

    def get_module_class(self, module_name: str) -> type[CommandModule] | None:
        """获取模块类（从懒加载列表）。

        Args:
            module_name: 模块名称

        Returns:
            模块类，如果不存在则返回 None
        """
        return self._lazy_modules.get(module_name)

    @property
    def lazy_modules(self) -> dict[str, type[CommandModule]]:
        """懒加载模块字典（只读）。"""
        return self._lazy_modules.copy()

    @property
    def loaded_modules(self) -> set[str]:
        """已加载模块集合（只读）。"""
        return self._loaded_modules.copy()
