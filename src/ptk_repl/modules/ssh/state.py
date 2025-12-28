"""SSH 模块状态管理。"""

from typing import Any

from pydantic import BaseModel, Field, PrivateAttr

from ptk_repl.state.module_state import ModuleState


class SSHConnectionInfo(BaseModel):
    """SSH 连接信息。"""

    name: str
    host: str
    port: int
    username: str
    is_active: bool = True
    _client: Any = PrivateAttr(default=None)  # paramiko.SSHClient

    def get_client(self) -> Any:
        """获取 SSH 客户端。

        Returns:
            paramiko.SSHClient 实例，如果未设置则返回 None
        """
        return self._client

    def set_client(self, client: Any) -> None:
        """设置 SSH 客户端。

        Args:
            client: paramiko.SSHClient 实例
        """
        self._client = client

    def close(self) -> None:
        """关闭 SSH 连接。"""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass  # 忽略关闭时的错误
            self._client = None
        self.is_active = False


class SSHState(ModuleState):
    """SSH 模块状态。

    管理多个 SSH 连接的连接池。
    """

    # 连接池：环境名 -> 连接信息
    connections: dict[str, SSHConnectionInfo] = Field(default_factory=dict)

    # 已连接的环境名称集合
    active_environments: set[str] = Field(default_factory=set)

    # 连接历史
    connection_history: list[str] = Field(default_factory=list)

    def add_connection(self, conn_info: SSHConnectionInfo) -> None:
        """添加连接到连接池。

        Args:
            conn_info: 连接信息
        """
        self.connections[conn_info.name] = conn_info
        self.active_environments.add(conn_info.name)
        if conn_info.name not in self.connection_history:
            self.connection_history.append(conn_info.name)

    def remove_connection(self, env_name: str) -> None:
        """从连接池移除连接。

        Args:
            env_name: 环境名称
        """
        if env_name in self.connections:
            del self.connections[env_name]
        self.active_environments.discard(env_name)

    def get_connection(self, env_name: str) -> SSHConnectionInfo | None:
        """获取连接信息。

        Args:
            env_name: 环境名称

        Returns:
            连接信息，如���不存在则返回 None
        """
        return self.connections.get(env_name)

    def get_first_active_environment(self) -> str | None:
        """获取第一个活跃的环境名称。

        Returns:
            环境名称，如果没有活跃连接则返回 None
        """
        return next(iter(self.active_environments)) if self.active_environments else None

    def reset(self) -> None:
        """重置 SSH 状态。"""
        self.connections.clear()
        self.active_environments.clear()
        self.connection_history.clear()

    def close_all_connections(self) -> None:
        """关闭所有 SSH 连接。"""
        for conn_info in list(self.connections.values()):
            conn_info.close()
        self.connections.clear()
        self.active_environments.clear()
