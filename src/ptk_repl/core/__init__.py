"""核心组件。"""

# 状态管理
# 基础组件
from ptk_repl.core.base import CommandModule

# 自动补全
from ptk_repl.core.completion import AutoCompleter

# 配置管理
from ptk_repl.core.configuration.config_manager import ConfigManager

# 装饰器
from ptk_repl.core.decoration.typed_command import typed_command

# 命令执行
from ptk_repl.core.execution.command_executor import CommandExecutor

# 命令注册
from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.state import StateManager

__all__ = [
    "StateManager",
    "CommandRegistry",
    "AutoCompleter",
    "ConfigManager",
    "typed_command",
    "CommandModule",
    "CommandExecutor",
]
