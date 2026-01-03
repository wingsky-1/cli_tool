"""颜色主题系统。

提供可配置的颜色方案，遵循开闭原则（OCP）。
"""

from dataclasses import dataclass, field
from typing import Any

from colorama import Fore, Style


@dataclass
class ColorScheme:
    """颜色方案。

    定义帮助信息中各种文本元素的颜色。
    """

    # 标题颜色
    title: str = field(default_factory=lambda: Fore.LIGHTCYAN_EX + Style.BRIGHT)
    # 分隔线颜色
    separator: str = field(default_factory=lambda: Fore.LIGHTBLUE_EX)
    # 小节标题颜色
    section: str = field(default_factory=lambda: Fore.LIGHTMAGENTA_EX + Style.BRIGHT)
    # 模块名颜色
    module: str = field(default_factory=lambda: Fore.LIGHTGREEN_EX + Style.BRIGHT)
    # 命令名颜色
    command: str = field(default_factory=lambda: Fore.LIGHTWHITE_EX)
    # 别名颜色
    alias: str = field(default_factory=lambda: Fore.LIGHTYELLOW_EX)
    # 描述颜色
    description: str = field(default_factory=lambda: Fore.LIGHTWHITE_EX)
    # 参数颜色
    param: str = field(default_factory=lambda: Fore.LIGHTMAGENTA_EX)
    # 示例颜色
    example: str = field(default_factory=lambda: Fore.LIGHTBLUE_EX)
    # 标签颜色
    label: str = field(default_factory=lambda: Fore.LIGHTCYAN_EX + Style.BRIGHT)
    # 错误颜色
    error: str = field(default_factory=lambda: Fore.LIGHTRED_EX + Style.BRIGHT)

    def get_color(self, color_type: str) -> str:
        """获取指定类型的颜色。

        Args:
            color_type: 颜色类型（如 'title', 'command' 等）

        Returns:
            颜色字符串（ANSI 转义码）
        """
        return getattr(self, color_type, "")

    def color_text(self, text: str, color_type: str) -> str:
        """为文本添加颜色。

        Args:
            text: 要着色的文本
            color_type: 颜色类型

        Returns:
            着色后的文本（包含重置序列）
        """
        color = self.get_color(color_type)
        return f"{color}{text}{Style.RESET_ALL}"

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "ColorScheme":
        """从配置字典创建颜色方案。

        Args:
            config: 配置字典，键为颜色类型，值为 ANSI 颜色代码

        Returns:
            颜色方案实例
        """
        return cls(**{k: v for k, v in config.items() if k in cls.__dataclass_fields__})

    @classmethod
    def default(cls) -> "ColorScheme":
        """获取默认颜色方案。

        Returns:
            默认颜色方案实例
        """
        return cls()


@dataclass
class Theme:
    """主题配置。

    包含颜色方案和主题元数据。
    """

    name: str = "default"
    description: str = "默认主题"
    color_scheme: ColorScheme = field(default_factory=ColorScheme)

    @classmethod
    def default(cls) -> "Theme":
        """获取默认主题。

        Returns:
            默认主题实例
        """
        return cls()

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "Theme":
        """从配置字典创建主题。

        Args:
            config: 配置字典

        Returns:
            主题实例
        """
        name = config.get("name", "default")
        description = config.get("description", "")
        color_config = config.get("colors", {})
        color_scheme = ColorScheme.from_dict(color_config)

        return cls(name=name, description=description, color_scheme=color_scheme)


# 预定义主题
DARK_THEME = Theme(
    name="dark",
    description="深色主题（适合深色背景终端）",
    color_scheme=ColorScheme(
        title=Fore.LIGHTCYAN_EX + Style.BRIGHT,
        separator=Fore.LIGHTBLUE_EX,
        section=Fore.LIGHTMAGENTA_EX + Style.BRIGHT,
        module=Fore.LIGHTGREEN_EX + Style.BRIGHT,
        command=Fore.LIGHTWHITE_EX,
        alias=Fore.LIGHTYELLOW_EX,
        description=Fore.LIGHTWHITE_EX,
        param=Fore.LIGHTMAGENTA_EX,
        example=Fore.LIGHTBLUE_EX,
        label=Fore.LIGHTCYAN_EX + Style.BRIGHT,
        error=Fore.LIGHTRED_EX + Style.BRIGHT,
    ),
)

LIGHT_THEME = Theme(
    name="light",
    description="浅色主题（适合浅色背景终端）",
    color_scheme=ColorScheme(
        title=Fore.BLUE + Style.BRIGHT,
        separator=Fore.BLUE,
        section=Fore.MAGENTA + Style.BRIGHT,
        module=Fore.GREEN + Style.BRIGHT,
        command=Fore.BLACK,
        alias=Fore.YELLOW,
        description=Fore.BLACK,
        param=Fore.MAGENTA,
        example=Fore.BLUE,
        label=Fore.CYAN + Style.BRIGHT,
        error=Fore.RED + Style.BRIGHT,
    ),
)
