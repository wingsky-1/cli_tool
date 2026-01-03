"""CLI 提示符管理器。"""

from ptk_repl.core.state.state_manager import StateManager


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
        gs = self.state_manager.global_state
        if gs.connected:
            ctx = gs.get_connection_context()
            if ctx and ctx.is_connected():
                # 使用多态方法，无需 isinstance 检查
                suffix = ctx.get_prompt_suffix()
                return f"(ptk:{suffix}) > "
            elif gs.current_host:
                # 兼容旧版本：显示主机和端口
                return f"(ptk:{gs.current_host}:{gs.current_port}) > "
        return "(ptk) > "
