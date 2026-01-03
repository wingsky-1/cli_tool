"""连接上下文抽象。

定义连接上下文的抽象基类和具体实现，使用组合替代继承。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class ConnectionType(str, Enum):
    """连接类型枚举。"""

    SSH = "ssh"
    DATABASE = "database"
    API = "api"
    CUSTOM = "custom"


class ConnectionContext(ABC):
    """连接上下文抽象基类。

    遵循开闭原则和里氏替换原则。
    """

    @property
    @abstractmethod
    def connection_type(self) -> ConnectionType:
        """获取连接类型。"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接。"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接。"""
        pass

    @abstractmethod
    def get_connection_info(self) -> dict[str, Any]:
        """获取连接信息。"""
        pass


class SSHConnectionContext(ConnectionContext):
    """SSH 连接上下文。"""

    def __init__(self) -> None:
        """初始化 SSH 连接上下文。"""
        self._current_env: str | None = None
        self._host: str | None = None
        self._port: int | None = None

    @property
    def connection_type(self) -> ConnectionType:
        """返回 SSH 连接类型。"""
        return ConnectionType.SSH

    @property
    def current_env(self) -> str | None:
        """获取当前 SSH 环境。"""
        return self._current_env

    def set_env(self, env: str, host: str | None = None, port: int | None = None) -> None:
        """设置当前 SSH 环境。"""
        self._current_env = env
        self._host = host
        self._port = port

    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self._current_env is not None

    def disconnect(self) -> None:
        """断开 SSH 连接。"""
        self._current_env = None
        self._host = None
        self._port = None

    def get_connection_info(self) -> dict[str, Any]:
        """获取连接信息。"""
        return {
            "type": "ssh",
            "env": self._current_env,
            "host": self._host,
            "port": self._port,
        }


class DatabaseConnectionContext(ConnectionContext):
    """数据库连接上下文。"""

    def __init__(self) -> None:
        """初始化数据库连接上下文。"""
        self._database: str | None = None
        self._host: str | None = None
        self._port: int | None = None

    @property
    def connection_type(self) -> ConnectionType:
        """返回数据库连接类型。"""
        return ConnectionType.DATABASE

    @property
    def active_database(self) -> str | None:
        """获取当前活动数据库。"""
        return self._database

    def set_database(self, database: str, host: str | None = None, port: int | None = None) -> None:
        """设置当前数据库。"""
        self._database = database
        self._host = host
        self._port = port

    def is_connected(self) -> bool:
        """检查是否已连接。"""
        return self._database is not None

    def disconnect(self) -> None:
        """断开数据库连接。"""
        self._database = None
        self._host = None
        self._port = None

    def get_connection_info(self) -> dict[str, Any]:
        """获取连接信息。"""
        return {
            "type": "database",
            "database": self._database,
            "host": self._host,
            "port": self._port,
        }
