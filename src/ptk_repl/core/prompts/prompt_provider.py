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
        """动态生成提示符（包含活动模块信息）。

        Returns:
            提示符字符串
        """
        gs = self.state_manager.global_state

        # 获取活动模块
        active_module = gs.get_active_module()

        # 构建基础提示符
        if active_module:
            base = f"(ptk:{active_module}"
        else:
            base = "(ptk"

        # 添加连接上下文
        if gs.connected:
            ctx = gs.get_connection_context()
            if ctx and ctx.is_connected():
                suffix = ctx.get_prompt_suffix()
                if active_module:
                    # 显示: (ptk:ssh@prod) >
                    return f"{base}@{suffix}) > "
                else:
                    # 显示: (ptk:prod) >
                    return f"({base}:{suffix}) > "
            elif gs.current_host:
                if active_module:
                    return f"{base}@{gs.current_host}:{gs.current_port}) > "
                else:
                    return f"({base}:{gs.current_host}:{gs.current_port}) > "

        # 默认提示符
        if active_module:
            return f"{base}) > "
        return "(ptk) > "
