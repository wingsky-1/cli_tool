"""模块管理器（门面模式）。"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from ptk_repl.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule
    from ptk_repl.core.completer import AutoCompleter
    from ptk_repl.core.interfaces import (
        IModuleDiscoverer,
        IModuleLoader,
        IModuleRegister,
    )


class ModuleManager:
    """模块管理器（门面模式）。

    组合 ModuleDiscoverer、ModuleLoader 和 ModuleRegister，
    提供统一的模块管理接口。

    Example:
        >>> manager = ModuleManager(...)
        >>> manager.discover_and_register_lazy()  # 发现并注册懒加载
        >>> manager.load_preloaded_modules()  # 加载预加载模块
        >>> module = manager.load_module("ssh")  # 按需加载
    """

    def __init__(
        self,
        discoverer: "IModuleDiscoverer",
        loader: "IModuleLoader",
        register: "IModuleRegister",
        config: ConfigManager,
        auto_completer: "AutoCompleter",
        register_commands_callback: Callable[["CommandModule"], None],
        error_callback: Callable[[str], None],
    ) -> None:
        """初始化模块管理器。

        Args:
            discoverer: 模块发现器
            loader: 模块加载器
            register: 模块注册器
            config: 配置管理器
            auto_completer: 自动补全器
            register_commands_callback: 注册命令的回调函数
            error_callback: 错误回调函数
        """
        self._discoverer = discoverer
        self._loader = loader
        self._register = register
        self._config = config
        self._auto_completer = auto_completer
        self._register_commands_callback = register_commands_callback
        self._error_callback = error_callback

    def load_module(self, module_name: str) -> "CommandModule | None":
        """加载并注册模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败则返回 None
        """
        # 1. 检查模块是否可用
        if not self._discoverer.is_available(module_name):
            self._error_callback(f"模块 '{module_name}' 不存在")
            return None

        # 2. 加载模块
        module = self._loader.load(module_name)
        if not module:
            self._error_callback(f"加载模块 '{module_name}' 失败")
            return None

        # 3. 注册模块（如果尚未注册）
        if not self._register.is_registered(module.name):
            try:
                self._register.register(module)
                # 4. 注册命令
                self._register_commands_callback(module)
                # 5. 通知补全器更新
                self._auto_completer._invalidate_cache()
            except Exception as e:
                self._error_callback(f"注册模块 '{module_name}' 失败: {e}")
                return None

        return module

    def load_modules(self) -> None:
        """加载所有预加载模块。"""
        # 1. Core 模块总是立即加载
        self.load_module("core")

        # 2. 从配置获取预加载模块列表
        preload_modules = self._config.get("core.preload_modules", [])

        # 3. 预加载配置中指定的模块
        for module_name in preload_modules:
            if module_name != "core":
                self.load_module(module_name)
