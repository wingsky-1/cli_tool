"""接口定义模块。

本模块包含项目中的所有 Protocol 接口定义，使用 Protocol 而非 ABC
以支持鸭子类型和更灵活的接口实现。
"""

from ptk_repl.core.interfaces.cli_context import ICliContext

__all__ = ["ICliContext"]
