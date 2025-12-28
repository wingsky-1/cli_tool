"""模块加载器。"""

from collections.abc import Callable
from typing import TYPE_CHECKING

from ptk_repl.core.config_manager import ConfigManager
from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.state_manager import StateManager

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule
    from ptk_repl.core.completer import AutoCompleter


class ModuleLoader:
    """模块加载器。

    负责发现、预加载和懒加载模块。
    """

    def __init__(
        self,
        registry: CommandRegistry,
        state_manager: StateManager,
        config: ConfigManager,
        auto_completer: "AutoCompleter",
        register_commands_callback: Callable[["CommandModule"], None],
        error_callback: Callable[[str], None],
    ) -> None:
        """初始化模块加载器。

        Args:
            registry: 命令注册表
            state_manager: 状态管理器
            config: 配置管理器
            auto_completer: 自动补全器
            register_commands_callback: 注册命令的回调函数
            error_callback: 错误回调函数
        """
        self.registry = registry
        self.state_manager = state_manager
        self.config = config
        self.auto_completer = auto_completer
        self.register_commands_callback = register_commands_callback
        self.error_callback = error_callback

        # 懒加载支持
        self._lazy_modules: dict[str, type] = {}
        self._loaded_modules: set[str] = set()

    def discover_all_modules(self) -> None:
        """自动发现所有可用模块并注册到懒加载系统。"""
        import importlib
        import pkgutil

        try:
            # 导入 modules 包
            modules_package = importlib.import_module("ptk_repl.modules")

            # 遍历 modules 包中的所有模块
            for _, module_name, _ in pkgutil.iter_modules(modules_package.__path__):
                # 跳过 core 模块（它会被立即加载）
                if module_name == "core":
                    continue

                # 跳过已经在懒加载列表中的模块
                if module_name in self._lazy_modules:
                    continue

                # 预加载模块（添加到 _lazy_modules）
                self._preload_module(module_name)
        except Exception as e:
            self.error_callback(f"发现模块失败: {e}")

    def load_modules(self) -> None:
        """加载模块（core 立即加载，其他根据配置预加载或懒加载）。"""
        # 1. 自动发现所有可用模块并注册到懒加载系统
        self.discover_all_modules()

        # 2. Core 模块总是立即加载
        self.load_module_immediately("core")

        # 3. 从配置获取预加载模块列表
        preload_modules = self.config.get("core.preload_modules", [])

        # 4. 预加载配置中指定的模块
        for module_name in preload_modules:
            if module_name != "core" and module_name not in self._loaded_modules:
                self.load_module_immediately(module_name)

    def load_module_immediately(self, module_name: str) -> None:
        """立即加载模块。

        Args:
            module_name: 模块名称
        """
        if module_name == "core":
            from ptk_repl.modules.core.module import CoreModule

            module = CoreModule()
            self.registry.register_module(module)
            module.initialize(self.state_manager)
            self.register_commands_callback(module)
            self._loaded_modules.add(module_name)
        else:
            # 加载其他模块
            # 如果模块已经在 _lazy_modules 中，直接使用
            if module_name in self._lazy_modules:
                module_cls = self._lazy_modules[module_name]
                module = module_cls()
                self.registry.register_module(module)
                module.initialize(self.state_manager)
                self.register_commands_callback(module)
                self._loaded_modules.add(module_name)
                del self._lazy_modules[module_name]
            else:
                # 否则，先导入模块再加载
                import importlib

                try:
                    module_path = f"ptk_repl.modules.{module_name}"
                    mod = importlib.import_module(module_path)

                    # 特殊模块名称映射（处理缩写词）
                    special_casing = {"ssh": "SSH"}
                    class_name_prefix = special_casing.get(module_name, module_name.capitalize())
                    module_cls = getattr(mod, f"{class_name_prefix}Module")
                    module = module_cls()
                    self.registry.register_module(module)
                    module.initialize(self.state_manager)
                    self.register_commands_callback(module)
                    self._loaded_modules.add(module_name)
                except Exception as e:
                    self.error_callback(f"加载模块 '{module_name}' 失败: {e}")

    def _preload_module(self, module_name: str) -> None:
        """预加载模块（懒加载）。

        Args:
            module_name: 模块名称
        """
        import importlib

        try:
            module_path = f"ptk_repl.modules.{module_name}"
            mod = importlib.import_module(module_path)

            # 特殊模块名称映射（处理缩写词）
            special_casing = {"ssh": "SSH"}
            class_name_prefix = special_casing.get(module_name, module_name.capitalize())
            module_cls = getattr(mod, f"{class_name_prefix}Module")

            self._lazy_modules[module_name] = module_cls
        except Exception as e:
            self.error_callback(f"预加载模块 '{module_name}' 失败: {e}")

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载。

        Args:
            module_name: 模块名称
        """
        if module_name in self._loaded_modules:
            return

        if module_name in self._lazy_modules:
            module_cls = self._lazy_modules[module_name]
            module = module_cls()
            self.registry.register_module(module)
            module.initialize(self.state_manager)
            self.register_commands_callback(module)
            self._loaded_modules.add(module_name)
            del self._lazy_modules[module_name]
            self.auto_completer._invalidate_cache()

    @property
    def loaded_modules(self) -> set[str]:
        """已加载的模块集合。"""
        return self._loaded_modules

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典。"""
        return self._lazy_modules
