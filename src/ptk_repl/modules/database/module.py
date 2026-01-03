"""数据库命令模块。"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ptk_repl.core.base import CommandModule
from ptk_repl.core.decoration.typed_command import typed_command

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state.state_manager import StateManager


class ConnectArgs(BaseModel):
    """连接参数。"""

    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, description="端口号")
    ssl: bool = Field(default=False, description="是否使用 SSL")


class DatabaseModule(CommandModule):
    """数据库命令模块。"""

    def __init__(self) -> None:
        """初始化数据库模块。"""
        super().__init__()
        self.cli: PromptToolkitCLI | None = None

    @property
    def name(self) -> str:
        """模块名称。"""
        return "database"

    @property
    def description(self) -> str:
        """模块描述。"""
        return "数据库操作（连接、查询、断开）"

    @property
    def aliases(self) -> str | None:
        """模块短别名。"""
        return "db"

    def initialize(self, state_manager: "StateManager") -> None:
        """模块初始化。

        Args:
            state_manager: 状态管理器
        """
        from ptk_repl.modules.database.state import DatabaseState

        self.state = state_manager.get_module_state("database", DatabaseState)

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册数据库命令。

        Args:
            cli: PromptToolkitCLI 实例
        """
        self.cli = cli

        # 使用装饰器注册命令（更优雅的方式）
        @cli.command()
        @typed_command(ConnectArgs)
        def connect(args: ConnectArgs) -> None:
            """连接到数据库。"""
            from ptk_repl.state.connection_context import DatabaseConnectionContext

            gs = cli.state.global_state
            gs.connected = True
            gs.current_host = args.host
            gs.current_port = args.port

            # 设置数据库连接上下文
            db_ctx = DatabaseConnectionContext()
            db_ctx.set_database(f"db_{args.host}", args.host, args.port)
            gs.set_connection_context(db_ctx)

            if self.state:
                self.state.active_database = f"db_{args.host}"

            cli.poutput(f"已连接到 {args.host}:{args.port}")
            if args.ssl:
                cli.poutput("SSL 已启用")

        @cli.command()
        def disconnect(args: str) -> None:
            """断开连接。"""
            gs = cli.state.global_state
            gs.clear_connection_context()

            if self.state:
                self.state.reset()

            cli.poutput("已断开连接")

        @cli.command()
        def query(args: str) -> None:
            """执行查询。"""
            if not cli.state.global_state.connected:
                cli.perror("未连接到数据库")
                return

            if not args:
                cli.perror("请指定查询内容")
                return

            if self.state:
                self.state.query_history.append(args)

            cli.poutput(f"执行查询: {args}")
