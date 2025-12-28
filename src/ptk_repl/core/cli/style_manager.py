"""CLI 样式管理器。"""

from prompt_toolkit.styles import Style


class StyleManager:
    """CLI 样式管理器。

    负责创建和管理 CLI 的视觉样式。
    """

    def create_style(self) -> Style:
        """创建 CLI 样式。

        Returns:
            Style 对象
        """
        return Style.from_dict(
            {
                "prompt": "ansigreen bold",
                # 补全菜单样式
                "completion-menu.completion": "bg:#008888 #ffffff",
                "completion-menu.completion.current": "bg:#00aaaa #000000",
                # 滚动条样式（增强视觉效果）
                "scrollbar.background": "bg:#88aaaa",
                "scrollbar.button": "bg:#222222",
                "scrollbar.arrow": "bg:#00aaaa #000000",
            }
        )
