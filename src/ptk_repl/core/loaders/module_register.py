"""模块注册器。"""

from typing import TYPE_CHECKING

from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.state_manager import StateManager

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


class ModuleRegister:
    """模块注册器。

    负责将模块注册到 CLI 系统（初始化和命令注册）。

    Example:
        >>> register = ModuleRegister(registry, state_manager)
        >>> module = SSHModule()
        >>> register.register(module)
        # 模块现在已注册并可用
    """

    def __init__(self, registry: CommandRegistry, state_manager: StateManager) -> None:
        """初始化模块注册器。

        Args:
            registry: 命令注册表
            state_manager: 状态管理器
        """
        self._registry = registry
        self._state_manager = state_manager

    def is_registered(self, module_name: str) -> bool:
        """检查模块是否已注册。

        Args:
            module_name: 模块名称

        Returns:
            是否已注册
        """
        return module_name in self._registry._modules

    def register(self, module: "CommandModule") -> None:
        """注册模块到 CLI。

        Args:
            module: 模块实例

        Raises:
            Exception: 如果模块初始化失败
        """
        try:
            # 1. 注册模块到注册表
            self._registry.register_module(module)

            # 2. 调用模块的初始化方法
            module.initialize(self._state_manager)

        except Exception:
            # 清理：如果注册失败，从注册表中移除
            if module.name in self._registry._modules:
                del self._registry._modules[module.name]
            raise
