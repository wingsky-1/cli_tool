"""接口定义模块。

本模块包含项目中的所有 Protocol 接口定义，使用 Protocol 而非 ABC
以支持鸭子类型和更灵活的接口实现。
"""

from ptk_repl.core.interfaces.cli_context import ICliContext
from ptk_repl.core.interfaces.command_resolver import ICommandResolver
from ptk_repl.core.interfaces.module_discoverer import IModuleDiscoverer
from ptk_repl.core.interfaces.module_loader import IModuleLoader
from ptk_repl.core.interfaces.module_register import IModuleRegister
from ptk_repl.core.interfaces.prompt_provider import IPromptProvider
from ptk_repl.core.interfaces.registry import IRegistry

__all__ = [
    "ICliContext",
    "ICommandResolver",
    "IModuleDiscoverer",
    "IModuleLoader",
    "IModuleRegister",
    "IPromptProvider",
    "IRegistry",
]
