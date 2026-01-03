"""全局状态定义。"""

from typing import Any

from pydantic import BaseModel, Field

from ptk_repl.state.connection_context import ConnectionContext


class GlobalState(BaseModel):
    """全局应用状态。

    所有模块共享的全局状态。

    重构后移除了特定模块的字段，使用组合的连接上下文。
    """

    connected: bool = False
    current_host: str | None = None
    current_port: int | None = None
    auth_token: str | None = None

    # 使用组合而非专用字段
    _connection_context: ConnectionContext | None = Field(default=None, exclude=True)

    def set_connection_context(self, context: ConnectionContext) -> None:
        """设置连接上下文。

        Args:
            context: 连接上下文对象
        """
        self._connection_context = context
        self.connected = context.is_connected()

    def get_connection_context(self) -> ConnectionContext | None:
        """获取连接上下文。

        Returns:
            连接上下文对象，如果未设置则返回 None
        """
        return self._connection_context

    def clear_connection_context(self) -> None:
        """清除连接上下文。"""
        if self._connection_context:
            self._connection_context.disconnect()
        self._connection_context = None
        self.connected = False
        self.current_host = None
        self.current_port = None
        self.auth_token = None

    def get_connection_info(self) -> dict[str, Any]:
        """获取当前连接信息。"""
        if self._connection_context:
            info = self._connection_context.get_connection_info()
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
