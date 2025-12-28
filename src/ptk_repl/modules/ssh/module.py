"""SSH 模块主类。"""

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from ptk_repl.core.base import CommandModule
from ptk_repl.core.decorators import typed_command

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager


class DisconnectArgs(BaseModel):
    """disconnect 命令参数。"""

    env_name: str | None = Field(default=None, description="环境名称（可选）")


class TailArgs(BaseModel):
    """tail 命令参数。"""

    env: str | None = Field(default=None, description="环境名称（可选）")
    mode: str | None = Field(default=None, description="日志模式 (direct/k8s/docker)")
    file: str | None = Field(default=None, description="日志文件名称")


class SSHModule(CommandModule):
    """SSH 模块。

    提供 SSH 连接管理和日志查看功能。
    """

    @property
    def name(self) -> str:
        """模块名称。"""
        return "ssh"

    @property
    def description(self) -> str:
        """模块描述。"""
        return "SSH 连接管理和日志查看"

    @property
    def aliases(self) -> list[str]:
        """模块别名列表。"""
        return []

    def initialize(self, state_manager: "StateManager") -> None:
        """模块初始化。

        Args:
            state_manager: 状态管理器实例
        """
        from ptk_repl.modules.ssh.state import SSHState

        self.state = state_manager.get_module_state("ssh", SSHState)

    def shutdown(self) -> None:
        """模块���闭时的清理工作。"""
        # 关闭所有SSH连接
        self.state.close_all_connections()

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册模块的所有命令。

        Args:
            cli: PromptToolkitCLI 实例
        """
        from ptk_repl.modules.ssh.connection import SSHConnectionManager
        from ptk_repl.modules.ssh.dialogs import select_environment_dialog
        from ptk_repl.modules.ssh.log_viewer import SSHLogViewer

        # 初始化管理器
        conn_manager = SSHConnectionManager(cli, self.state)
        log_viewer = SSHLogViewer(cli, self.state)

        # env 命令
        @cli.command("env")
        def env(args: str) -> None:
            """连接或切换 SSH 环境。

            用法：
                ssh env           # 交互式选择环境
                ssh env prod     # 直接连接到 prod 环境
            """
            from ptk_repl.modules.ssh.config import load_ssh_config

            config = load_ssh_config(cli.config)

            # 解析参数
            env_name = args.strip() if args.strip() else None

            if not env_name:
                # 无参数：弹出交互式对话框
                env_name = select_environment_dialog(config, self.state, cli.state.global_state)
                if not env_name:
                    return  # 用户取消

            # 使用连接管理器连接
            conn_manager.connect_to_environment(env_name)

        # disconnect 命令
        @cli.command("disconnect")
        @typed_command(DisconnectArgs)
        def disconnect(args: DisconnectArgs) -> None:
            """断开 SSH 连接。"""
            gs = cli.state.global_state

            # 确定要断开的环境
            env_name = args.env_name
            if not env_name:
                env_name = gs.current_ssh_env

            if not env_name:
                cli.perror("没有指定环境，也没有当前连接")
                return

            # 使用连接管理器断开
            conn_manager.disconnect_environment(env_name)

        # tail 命令
        @cli.command("tail")
        @typed_command(TailArgs)
        def tail(args: TailArgs) -> None:
            """查看服务器日志。

            用法：
                ssh tail                    # 使用当前环境的 log_type
                ssh tail prod              # 指定环境
                ssh tail --mode k8s        # 指定模式（覆盖环境的 log_type）
                ssh tail prod --file 应用日志  # 指定日志文件
            """
            # 使用日志查看器查看日志
            log_viewer.view_log(env=args.env, mode=args.mode, file=args.file)
