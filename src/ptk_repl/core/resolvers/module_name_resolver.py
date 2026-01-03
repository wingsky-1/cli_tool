"""模块名称解析器。

提供可扩展的模块名称到类名的解析策略，遵循开闭原则。
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IModuleNameResolver(Protocol):
    """模块名称解析器接口（Protocol - 鸭子类型）。

    负责将模块名(如 "ssh")解析为类名前缀(如 "SSH")。

    使用 Protocol 而非 ABC，支持鸭子类型：任何实现了解析方法的对象
    都自动兼容此接口，无需显式继承。

    Example:
        >>> class MyResolver:
        ...     def resolve_class_name(self, module_name: str) -> str:
        ...         return module_name.upper()
        ...
        >>> resolver = MyResolver()
        >>> resolver.resolve_class_name("ssh")
        'SSH'
        >>> isinstance(resolver, IModuleNameResolver)
        True
    """

    def resolve_class_name(self, module_name: str) -> str:
        """解析模块名为类名前缀。

        Args:
            module_name: 模块名称(如 "ssh", "database")

        Returns:
            类名前缀(如 "SSH", "Database")

        Example:
            >>> resolver.resolve_class_name("ssh")
            "SSH"
            >>> resolver.resolve_class_name("database")
            "Database"
        """
        ...


class DefaultModuleNameResolver:
    """默认模块名称解析器。

    使用首字母大写的规则。

    注意：无需显式继承 IModuleNameResolver，自动兼容
    """

    def resolve_class_name(self, module_name: str) -> str:
        """默认实现：首字母大写。

        Args:
            module_name: 模块名称

        Returns:
            首字母大写的类名前缀

        Example:
            >>> resolver = DefaultModuleNameResolver()
            >>> resolver.resolve_class_name("database")
            'Database'
            >>> resolver.resolve_class_name("ssh")
            'Ssh'
        """
        return module_name.capitalize()


class ConfigurableResolver:
    """可配置的模块名称解析器。

    从配置中读取特殊映射规则。

    Example:
        >>> resolver = ConfigurableResolver({"ssh": "SSH"})
        >>> resolver.resolve_class_name("ssh")
        'SSH'
        >>> resolver.resolve_class_name("database")
        'Database'  # 使用默认规则
    """

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        """初始化可配置解析器。

        Args:
            mapping: 模块名到类名前缀的映射字典
                    例如: {"ssh": "SSH", "api": "API"}
        """
        self._mapping = mapping or {"ssh": "SSH", "api": "API"}

    def resolve_class_name(self, module_name: str) -> str:
        """使用配置映射或默认规则。

        Args:
            module_name: 模块名称

        Returns:
            类名前缀（优先使用配置，否则使用默认规则）
        """
        return self._mapping.get(module_name, module_name.capitalize())
