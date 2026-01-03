"""CLI 提示符管理器。"""

from ptk_repl.core.state_manager import StateManager


class PromptManager:
    """CLI 提示符管理器。

    负责根据当前状态动态生成提示符。
    """

    def __init__(self, state_manager: StateManager) -> None:
        """初始化提示符管理器。

        Args:
            state_manager: 状态管理器
        """
        self.state_manager = state_manager

    def get_prompt(self) -> str:
        """动态生成提示符。

        Returns:
            提示符字符串
        """
        from ptk_repl.state.connection_context import (
            DatabaseConnectionContext,
            SSHConnectionContext,
        )

        gs = self.state_manager.global_state
        if gs.connected:
            ctx = gs.get_connection_context()
            if isinstance(ctx, SSHConnectionContext) and ctx.current_env:
                # SSH 连接：显示环境名称
                return f"(ptk:{ctx.current_env}) > "
            elif isinstance(ctx, DatabaseConnectionContext) and gs.current_host:
                # Database 连接：显示主机和端口
                return f"(ptk:{gs.current_host}:{gs.current_port}) > "
            elif gs.current_host:
                # 兼容旧版本：显示主机和端口
                return f"(ptk:{gs.current_host}:{gs.current_port}) > "
        return "(ptk) > "
