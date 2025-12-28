"""数据库模块状态。"""

from pydantic import Field

from ptk_repl.state.module_state import ModuleState


class DatabaseState(ModuleState):
    """数据库模块状态。"""

    active_database: str | None = None
    connection_pool_size: int = 10
    query_history: list[str] = Field(default_factory=list)

    def reset(self) -> None:
        """重置数据库状态。"""
        self.active_database = None
        self.connection_pool_size = 10
        self.query_history.clear()
