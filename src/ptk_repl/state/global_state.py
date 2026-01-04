"""全局状态定义。"""

from typing import Any

from pydantic import BaseModel, Field

from ptk_repl.state.connection_context import ConnectionContext


class GlobalState(BaseModel):
    """全局应用状态。

    所有模块共享的全局状态。

    重构后移除了特定模块的字段，使用组合的连接上下文。
    """

    model_config = {"arbitrary_types_allowed": True}

    connected: bool = False
    current_host: str | None = None
    current_port: int | None = None
    auth_token: str | None = None
    active_module: str | None = None  # 当前激活的模块（用于命令省略）

    # 使用组合而非专用字段
    connection_context: ConnectionContext | None = Field(default=None, exclude=True)

    def set_connection_context(self, context: ConnectionContext) -> None:
        """设置连接上下文。

        Args:
            context: 连接上下文对象
        """
        self.connection_context = context
        self.connected = context.is_connected()

    def get_connection_context(self) -> ConnectionContext | None:
        """获取连接上下文。

        Returns:
            连接上下文对象，如果未设置则返回 None
        """
        return self.connection_context

    def clear_connection_context(self) -> None:
        """清除连接上下文。"""
        if self.connection_context:
            self.connection_context.disconnect()
        self.connection_context = None
        self.connected = False
        self.current_host = None
        self.current_port = None
        self.auth_token = None

    def set_active_module(self, module_name: str) -> None:
        """设置当前激活的模块。

        Args:
            module_name: 模块名称
        """
        self.active_module = module_name

    def get_active_module(self) -> str | None:
        """获取当前激活的模块。

        Returns:
            模块名称，如果未设置则返回 None
        """
        return self.active_module

    def get_connection_info(self) -> dict[str, Any]:
        """获取当前连接信息。"""
        if self.connection_context:
            info = self.connection_context.get_connection_info()
            info.update(
                {
                    "connected": self.connected,
                    "host": self.current_host,
                    "port": self.current_port,
                }
            )
            return info
        return {
            "connected": False,
            "type": None,
        }

    def reset(self) -> None:
        """重置全局状态。"""
        self.clear_connection_context()
        self.active_module = None
