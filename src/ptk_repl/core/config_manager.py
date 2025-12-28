"""配置管理器。"""

from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    """配置管理器。

    从 YAML 文件加载配置，如果没有配置文件则使用默认配置。
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
    }

    def __init__(self, config_path: str | None = None) -> None:
        """初始化配置管理器。

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path or self._find_config()
        self._config: dict[str, Any] = {}
        if self.config_path:
            self._load()
        else:
            # 使用默认配置
            self._config = self.DEFAULT_CONFIG.copy()

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

    def _load(self) -> None:
        """从文件加载配置。"""
        if not self.config_path:
            return

        try:
            with open(self.config_path, encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                loaded_config = loaded if isinstance(loaded, dict) else {}

                # 合并默认配置和用户配置
                self._config = self.DEFAULT_CONFIG.copy()
                self._merge_config(self._config, loaded_config)
        except Exception:
            # 加载失败时使用默认配置
            self._config = self.DEFAULT_CONFIG.copy()

    def _merge_config(self, base: dict, override: dict) -> None:
        """递归合并配置。

        Args:
            base: 基础配置（会被修改）
            override: 覆盖配置
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。

        支持点号分隔的嵌套键，如 "core.enabled_modules"。

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值，如果未找到则返回默认值
        """
        keys = key.split(".")
        value: Any = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default
