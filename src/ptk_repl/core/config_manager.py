"""配置管理器。"""

from pathlib import Path
from typing import Any

from ptk_repl.core.config import (
    CompositeConfigProvider,
    EnvConfigProvider,
    IConfigProvider,
    YamlConfigProvider,
)


class ConfigManager:
    """配置管理器。

    使用组合配置提供者加载配置，简化职责。
    """

    # 默认配置
    DEFAULT_CONFIG = {
        "core": {
            # core 模块总是立即加载
            # 其他模块默认懒加载，除非在 preload_modules 中指定
            "preload_modules": [],  # 预加载的模块列表（可选）
        },
        "completions": {
            "enabled": True,
            "show_descriptions": True,
            "cache": {"enabled": True},
        },
        # 内置的模块名称映射配置（不暴露给用户）
        "modules": {
            "name_mappings": {
                "ssh": "SSH",
                "api": "API",
            }
        },
    }

    def __init__(
        self, config_path: str | None = None, provider: IConfigProvider | None = None
    ) -> None:
        """初始化配置管理器。

        Args:
            config_path: 配置文件路径（可选）
            provider: 配置提供者（可选，默认使用 CompositeConfigProvider）
        """
        if provider:
            self._provider = provider
        else:
            # 构建默认的配置提供者链
            providers: list[IConfigProvider] = []
            config_file = config_path or self._find_config()
            if config_file:
                # YAML 配置提供者（优先级低于环境变量）
                providers.append(YamlConfigProvider(config_file))

            # 环境变量配置提供者（优先级最高）
            providers.append(EnvConfigProvider(prefix="PTK_"))

            # 组合提供者
            self._provider = CompositeConfigProvider(providers)

    @property
    def provider(self) -> IConfigProvider:
        """获取配置提供者。

        Returns:
            配置提供者实例
        """
        return self._provider

    def _find_config(self) -> str | None:
        """查找配置文件。

        Returns:
            配置文件路径，如果未找到则返回 None
        """
        paths = [
            Path.cwd() / "ptk_repl_config.yaml",
            Path.cwd() / "config" / "ptk_repl.yaml",
            Path.home() / ".ptk_repl" / "config.yaml",
        ]
        for path in paths:
            if path.exists():
                return str(path)
        return None

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        支持点号分隔的嵌套键，如 "core.enabled_modules"。

        Args:
            key: 配置键
            default: 默认值（从 DEFAULT_CONFIG 获取）

        Returns:
            配置值，如果未找到则返回默认值
        """
        # 先从提供者获取
        value = self._provider.get(key)

        # 如果提供者没有值，使用默认配置
        if value is None:
            keys = key.split(".")
            default_value: Any = self.DEFAULT_CONFIG
            for k in keys:
                if isinstance(default_value, dict) and k in default_value:
                    default_value = default_value[k]
                else:
                    return default
            return default_value if default_value is not None else default

        return value
