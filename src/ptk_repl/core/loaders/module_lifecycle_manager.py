"""模块生命周期管理器。"""

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from ptk_repl.core.base import CommandModule
from ptk_repl.core.configuration.config_manager import ConfigManager
from ptk_repl.core.interfaces import IModuleLoader
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker
from ptk_repl.core.loaders.module_discovery_service import ModuleDiscoveryService
from ptk_repl.core.loaders.unified_module_loader import UnifiedModuleLoader
from ptk_repl.core.resolvers import IModuleNameResolver

if TYPE_CHECKING:
    from ptk_repl.core.completion.auto_completer import AutoCompleter
    from ptk_repl.core.interfaces import IModuleRegister


class ModuleLifecycleManager(IModuleLoader):
    """模块生命周期管理器（门面模式）。

    协调发现、加载、注册等组件，提供统一的模块管理接口。
    这是旧 ModuleLoader 的直接替代品。
    """

    def __init__(
        self,
        modules_path: Path,
        name_resolver: "IModuleNameResolver",
        module_register: "IModuleRegister",
        config: ConfigManager,
        auto_completer: "AutoCompleter",
        register_commands_callback: Callable[[CommandModule], None],
        error_callback: Callable[[str], None],
    ) -> None:
        """初始化生命周期管理器。

        Args:
            modules_path: 模块目录路径
            name_resolver: 模块名称解析器
            module_register: 模块注册器
            config: 配置管理器
            auto_completer: 自动补全器
            register_commands_callback: 命令注册回调
            error_callback: 错误回调
        """
        # 1. 初始化组件
        self._tracker = LazyModuleTracker()
        self._discovery_service = ModuleDiscoveryService(modules_path)
        self._config = config
        self._auto_completer = auto_completer
        self._error_callback = error_callback
        self._name_resolver = name_resolver

        # 2. 创建加载器（注入回调）
        post_load_callbacks = [
            register_commands_callback,  # 注册命令
            lambda m: auto_completer.refresh(),  # 刷新补全
        ]

        self._loader = UnifiedModuleLoader(
            name_resolver=name_resolver,
            lazy_tracker=self._tracker,
            module_register=module_register,
            post_load_callbacks=post_load_callbacks,
        )

    def load_modules(self) -> None:
        """加载所有模块（主入口）。

        执行完整的加载流程：
        1. 自动发现所有模块
        2. 预加载到懒加载追踪器
        3. 立即加载 core 模块
        4. 根据配置预加载其他模块
        """
        # 1. 自动发现并预加载所有模块（排除 core）
        self._discovery_service.preload_all(
            self._tracker,
            self._name_resolver,
            exclude=["core"],
        )

        # 2. Core 模块总是立即加载
        self.load_module_immediately("core")

        # 3. 从配置获取预加载列表
        preload_modules = self._config.get("core.preload_modules", [])

        # 4. 预加载配置中的模块
        for module_name in preload_modules:
            if module_name != "core":
                self.load_module_immediately(module_name)

    def load_module_immediately(self, module_name: str) -> None:
        """立即加载模块。

        Args:
            module_name: 模块名称
        """
        if module_name == "core":
            from ptk_repl.modules.core.module import CoreModule

            try:
                module: CommandModule | None = CoreModule()
                if module:
                    self._loader._module_register.register(module)
                    self._tracker.mark_as_loaded(module_name)
                    # 触发回调
                    for callback in self._loader._post_load_callbacks:
                        callback(module)
            except Exception as e:
                self._error_callback(f"加载 core 模块失败: {e}")
        else:
            module = self._loader.load(module_name)
            if not module:
                self._error_callback(f"加载模块 '{module_name}' 失败")

    # ===== IModuleLoader 接口实现（委托给 UnifiedModuleLoader） =====

    def load(self, module_name: str) -> "CommandModule | None":
        """加载模块（IModuleLoader 接口）。"""
        return self._loader.load(module_name)

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载（IModuleLoader 接口）。"""
        return self._loader.is_loaded(module_name)

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载（IModuleLoader 接口）。"""
        self._loader.ensure_module_loaded(module_name)

    @property
    def loaded_modules(self) -> dict[str, "CommandModule"]:
        """已加载的模块字典（IModuleLoader 接口）。"""
        return self._loader.loaded_modules

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典（IModuleLoader 接口）。"""
        return self._loader.lazy_modules

    @property
    def lazy_tracker(self) -> LazyModuleTracker:
        """懒加载追踪器（用于模块名解析）。"""
        return self._tracker
