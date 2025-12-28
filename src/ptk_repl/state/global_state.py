"""全局状态定义。"""

from pydantic import BaseModel


class GlobalState(BaseModel):
    """全局应用状态。

    所有模块共享的全局状态。
    """

    connected: bool = False
    current_host: str | None = None
    current_port: int | None = None
    auth_token: str | None = None

    # SSH 模块专用字段
    connection_type: str | None = None  # "ssh" | "database" | None
    current_ssh_env: str | None = None  # 当前 SSH 环境名称

    def reset(self) -> None:
        """重置全局状态。"""
        self.connected = False
        self.current_host = None
        self.current_port = None
        self.auth_token = None
        self.connection_type = None
        self.current_ssh_env = None
