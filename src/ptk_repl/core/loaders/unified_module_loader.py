"""统一模块加载器。"""

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING

from ptk_repl.core.interfaces import IModuleLoader, IModuleRegister
from ptk_repl.core.resolvers import IModuleNameResolver

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule
    from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker


class UnifiedModuleLoader(IModuleLoader):
    """统一模块加载器。

    负责加载模块实例，支持懒加载和即时加载。
    实现 IModuleLoader 接口，确保可替换性。
    """

    def __init__(
        self,
        name_resolver: IModuleNameResolver,
        lazy_tracker: "LazyModuleTracker",
        module_register: IModuleRegister,
        post_load_callbacks: list[Callable[[CommandModule], None]] | None = None,
    ) -> None:
        """初始化模块加载器。

        Args:
            name_resolver: 模块名称解析器
            lazy_tracker: 懒加载追踪器
            module_register: 模块注册器
            post_load_callbacks: 加载后回调列表（如补全刷新、命令注册）
        """
        self._name_resolver = name_resolver
        self._lazy_tracker = lazy_tracker
        self._module_register = module_register
        self._post_load_callbacks = post_load_callbacks or []

    def load(self, module_name: str) -> "CommandModule | None":
        """加载模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败则返回 None
        """
        # 1. 检查是否已加载
        if self._lazy_tracker.is_loaded(module_name):
            # 从注册表获取已加载的模块
            return self._module_register.get_module(module_name)

        try:
            # 2. 从懒加载列表获取模块类
            module_cls = self._lazy_tracker.get_module_class(module_name)

            if not module_cls:
                # 3. 动态导入模块
                module_path = f"ptk_repl.modules.{module_name}"
                mod = importlib.import_module(module_path)

                class_name_prefix = self._name_resolver.resolve_class_name(module_name)
                module_cls = getattr(mod, f"{class_name_prefix}Module")

            # 4. 创建模块实例
            module: CommandModule = module_cls()

            # 5. 注册模块（包括初始化）
            self._module_register.register(module)

            # 6. 标记为已加载
            self._lazy_tracker.mark_as_loaded(module_name)

            # 7. 执行加载后回调
            for callback in self._post_load_callbacks:
                callback(module)

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
        return self._lazy_tracker.is_loaded(module_name)

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载（懒加载）。

        Args:
            module_name: 模块名称
        """
        if not self.is_loaded(module_name):
            self.load(module_name)

    @property
    def loaded_modules(self) -> dict[str, "CommandModule"]:
        """已加载的模块字典（只读）。"""
        result: dict[str, CommandModule] = {}
        for name in self._lazy_tracker.loaded_modules:
            module = self._module_register.get_module(name)
            if module:
                result[name] = module
        return result

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典（只读）。"""
        return self._lazy_tracker.lazy_modules
