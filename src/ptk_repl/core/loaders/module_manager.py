"""模块管理器（门面模式）。"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from ptk_repl.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule
    from ptk_repl.core.completer import AutoCompleter


class ModuleManager:
    """模块管理器（门面模式 + 适配器模式）。

    组合 ModuleDiscoverer、ModuleLoader 和 ModuleRegister，
    提供统一的模块管理接口。

    同时实现 IModuleLoader 接口的所有方法，作为旧 ModuleLoader 的替代。
    """

    def __init__(
        self,
        discoverer: Any,  # IModuleDiscoverer
        loader: Any,  # IModuleLoader
        register: Any,  # IModuleRegister
        config: ConfigManager,
        auto_completer: "AutoCompleter",
        register_commands_callback: Callable[["CommandModule"], None],
        error_callback: Callable[[str], None],
        legacy_loader: Any,  # 旧的 ModuleLoader（提供 lazy_modules 等功能）
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
            legacy_loader: 旧的 ModuleLoader（提供兼容性功能）
        """
        self._discoverer = discoverer
        self._loader = loader
        self._register = register
        self._config = config
        self._auto_completer = auto_completer
        self._register_commands_callback = register_commands_callback
        self._error_callback = error_callback
        self._legacy_loader = legacy_loader

    def load_module(self, module_name: str) -> "CommandModule | None":
        """加载并注册模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败则返回 None
        """
        # 1. 检查模块是否可用
        if not cast(Any, self._discoverer).is_available(module_name):
            self._error_callback(f"模块 '{module_name}' 不存在")
            return None

        # 2. 加载模块
        module: CommandModule | None = cast(
            "CommandModule | None", cast(Any, self._loader).load(module_name)
        )
        if not module:
            self._error_callback(f"加载模块 '{module_name}' 失败")
            return None

        # 3. 注册模块（如果尚未注册）
        if not cast(Any, self._register).is_registered(module.name):
            try:
                cast(Any, self._register).register(module)
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
        # 委托给旧的 ModuleLoader（因为它有完整的懒加载支持）
        self._legacy_loader.load_modules()

    # ===== IModuleLoader 接口实现（委托给 legacy_loader） =====

    def load(self, module_name: str) -> "CommandModule | None":
        """加载模块（IModuleLoader 接口）。"""
        return cast("CommandModule | None", cast(Any, self._loader).load(module_name))

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载（IModuleLoader 接口）。"""
        return cast(bool, cast(Any, self._loader).is_loaded(module_name))

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载（IModuleLoader 接口，委托给 legacy_loader）。"""
        cast(Any, self._legacy_loader).ensure_module_loaded(module_name)

    @property
    def loaded_modules(self) -> dict[str, "CommandModule"]:
        """已加载的模块字典（IModuleLoader 接口，委托给 legacy_loader）。"""
        # legacy_loader 返回 set[str]，需要转换
        result: dict[str, CommandModule] = {}
        for name in cast(Any, self._legacy_loader).loaded_modules:
            module = cast("CommandModule | None", cast(Any, self._loader).load(name))
            if module:
                result[name] = module
        return result

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典（IModuleLoader 接口，委托给 legacy_loader）。"""
        return cast(dict[str, type], cast(Any, self._legacy_loader).lazy_modules)
