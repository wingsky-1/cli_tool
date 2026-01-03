"""提示符提供者接口。"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IPromptProvider(Protocol):
    """提示符提供者接口。

    负责根据当前状态生成 CLI 提示符。
    """

    def get_prompt(self) -> str:
        """获取当前提示符。

        Returns:
            提示符字符串

        Note:
            提示符会根据连接状态和类型动态变化。

        Examples:
            >>> provider.get_prompt()
            "> "
            >>> # 连接到 SSH 环境后
            >>> provider.get_prompt()
            "prod > "
        """
        ...
