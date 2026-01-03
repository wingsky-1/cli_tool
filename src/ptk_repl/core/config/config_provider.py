"""配置提供者接口和实现。

遵循单一职责原则（SRP）和依赖倒置原则（DIP）。
"""

import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from yaml import safe_load


@runtime_checkable
class IConfigProvider(Protocol):
    """配置提供者接口。

    使用 Protocol 支持鸭子类型。
    """

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        Args:
            key: 配置键（支持点号分隔的路径，如 'ssh.environments'）
            default: 默认值

        Returns:
            配置值，如果不存在则返回默认值
        """
        ...

    def has(self, key: str) -> bool:
        """检查配置键是否存在。

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        ...


class YamlConfigProvider:
    """YAML 配置文件提供者。

    职责：从 YAML 文件加载配置
    """

    def __init__(self, config_path: Path | str) -> None:
        """初始化 YAML 配置提供者。

        Args:
            config_path: YAML 配置文件路径
        """
        self._config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """加载 YAML 配置文件。"""
        if self._config_path.exists():
            with open(self._config_path, encoding="utf-8") as f:
                self._config = safe_load(f) or {}
        else:
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        Args:
            key: 配置键（支持点号分隔的路径）
            default: 默认值

        Returns:
            配置值，如果不存在则返回默认值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def has(self, key: str) -> bool:
        """检查配置键是否存在。

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        return self.get(key) is not None


class EnvConfigProvider:
    """环境变量配置提供者。

    职责：从环境变量读取配置
    """

    def __init__(self, prefix: str = "PTK_") -> None:
        """初始化环境变量配置提供者。

        Args:
            prefix: 环境变量前缀（如 'PTK_'）
        """
        self._prefix = prefix

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        Args:
            key: 配置键（会转换为大写并添加前缀）
            default: 默认值

        Returns:
            配置值，如果不存在则返回默认值
        """
        # 转换键名：ssh.environments -> PTK_SSH_ENVIRONMENTS
        env_key = self._prefix + key.upper().replace(".", "_")
        return os.getenv(env_key, default)

    def has(self, key: str) -> bool:
        """检查配置键是否存在。

        Args:
            key: 配置键

        Returns:
            是否存在
        """
        return self.get(key) is not None


class CompositeConfigProvider:
    """组合配置提供者。

    职责：合并多个配置提供者的结果（优先级：后面的覆盖前面的）
    """

    def __init__(self, providers: list[IConfigProvider]) -> None:
        """初始化组合配置提供者。

        Args:
            providers: 配置提供者列表（按优先级排序，后面的覆盖前面的）
        """
        self._providers = providers

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值，从第一个提供者获取，如果不存在则尝试下一个
        """
        # 反向遍历（优先级高的在后面）
        for provider in reversed(self._providers):
            if provider.has(key):
                return provider.get(key)

        return default

    def has(self, key: str) -> bool:
        """检查配置键是否存在。

        Args:
            key: 配置键

        Returns:
            任一提供者存在即返回 True
        """
        return any(provider.has(key) for provider in self._providers)
