"""解析器模块。

本模块包含各种名称解析策略，使用 Protocol 支持鸭子类型。
"""

from ptk_repl.core.resolvers.module_name_resolver import (
    ConfigurableResolver,
    DefaultModuleNameResolver,
    IModuleNameResolver,
)

__all__ = [
    "IModuleNameResolver",
    "DefaultModuleNameResolver",
    "ConfigurableResolver",
]
