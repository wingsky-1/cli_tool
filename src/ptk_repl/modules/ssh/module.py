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
        """模块关闭时的清理工作。"""
        # 关闭所有SSH连接
        self.state.close_all_connections()

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册模块的所有命令。

        Args:
            cli: PromptToolkitCLI 实例
        """
        from ptk_repl.modules.ssh.config import load_ssh_config
        from ptk_repl.modules.ssh.dialogs import select_environment_dialog
        from ptk_repl.modules.ssh.ssh_client import SSHClientManager
        from ptk_repl.modules.ssh.tail import tail_log

        # env 命令
        @cli.command("env")
        def env(args: str) -> None:
            """连接或切换 SSH 环境。

            用法：
                ssh env           # 交互式选择环境
                ssh env prod     # 直接连接到 prod 环境
            """
            config = load_ssh_config(cli.config)

            # 解析参数
            env_name = args.strip() if args.strip() else None

            if not env_name:
                # 无参数：弹出交互式对话框
                env_name = select_environment_dialog(config, self.state, cli.state.global_state)
                if not env_name:
                    return  # 用户取消

            # 查找环境配置
            env_config = None
            for env in config.environments:
                if env.name == env_name:
                    env_config = env
                    break

            if not env_config:
                available = [e.name for e in config.environments]
                cli.perror(f"环境 '{env_name}' 不存在。可用环境: {', '.join(available)}")
                return

            # 检查是否已连接
            if env_config.name in self.state.active_environments:
                conn_info = self.state.get_connection(env_config.name)
                if conn_info and conn_info.is_active:
                    # 已连接，直接设置为当前环境
                    _set_current_environment(cli, env_config.name)
                    cli.poutput(f"已切换到环境: {env_config.name}")
                    return

            # 建立新连接
            try:
                ssh_mgr = SSHClientManager()
                client = ssh_mgr.connect(
                    host=env_config.host,
                    port=env_config.port,
                    username=env_config.username,
                    password=env_config.password,
                    key_path=env_config.key_path,
                )

                # 创建连接信息
                from ptk_repl.modules.ssh.state import SSHConnectionInfo

                conn_info = SSHConnectionInfo(
                    name=env_config.name,
                    host=env_config.host,
                    port=env_config.port,
                    username=env_config.username,
                    is_active=True,
                )
                conn_info.set_client(client)

                # 添加到连接池
                self.state.add_connection(conn_info)

                # 设置为当前环境
                _set_current_environment(cli, env_config.name)

                cli.poutput(f"已连接到环境: {env_config.name} ({env_config.description})")

            except Exception as e:
                cli.perror(f"连接失败: {e}")

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

            # 检查环境是否在连接池中
            if env_name not in self.state.active_environments:
                cli.perror(f"环境 '{env_name}' 未连接")
                return

            # 获取连接信息
            conn_info = self.state.get_connection(env_name)
            if not conn_info:
                cli.perror(f"环境 '{env_name}' 的连接信息不存在")
                return

            # 关闭 SSH 连接
            try:
                client = conn_info.get_client()
                if client:
                    client.close()
            except Exception as e:
                cli.poutput(f"关闭连接时出错: {e}")

            # 从连接池移除
            self.state.remove_connection(env_name)

            # 如果断开的是当前环境，需要切换
            was_current = gs.current_ssh_env == env_name
            if was_current:
                next_env = self.state.get_first_active_environment()
                if next_env:
                    gs.current_ssh_env = next_env
                    cli.poutput(f"已断开 {env_name}，当前环境切换为: {next_env}")
                else:
                    gs.connected = False
                    gs.connection_type = None
                    gs.current_ssh_env = None
                    cli.poutput(f"已断开 {env_name}，没有其他活跃连接")
            else:
                cli.poutput(f"已断开 {env_name}")

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
            from ptk_repl.modules.ssh.dialogs import select_log_dialog

            gs = cli.state.global_state
            config = load_ssh_config(cli.config)

            # 1. 确定目标环境
            env_name = args.env
            if not env_name:
                env_name = gs.current_ssh_env

            if not env_name:
                # 没有当前环境，弹出选择对话框
                env_name = select_environment_dialog(config, self.state, gs)
                if not env_name:
                    return

            # 2. 查找环境配置
            env_config = None
            for env in config.environments:
                if env.name == env_name:
                    env_config = env
                    break

            if not env_config:
                cli.perror(f"环境 '{env_name}' 不存在")
                return

            # 3. 确定日志模式（优先使用命令行参数，否则使用环境的 log_type）
            mode = args.mode or env_config.log_type

            # 4. 从全局配置获取该模式的日志路径
            log_configs = config.log_paths.get(mode, [])
            if not log_configs:
                cli.perror(f"模式 '{mode}' 没有配置日志路径")
                return

            # 5. 确定具体的日志文件
            if args.file:
                # 用户指定了文件
                log_config = next((lc for lc in log_configs if lc.name == args.file), None)
                if not log_config:
                    available = [lc.name for lc in log_configs]
                    cli.perror(f"日志 '{args.file}' 不存在。可用: {', '.join(available)}")
                    return
            elif len(log_configs) == 1:
                log_config = log_configs[0]
            else:
                # 多个日志，弹出选择对话框
                log_config = select_log_dialog(log_configs, mode)
                if not log_config:
                    return

            # 6. 获取或建立 SSH 连接
            conn_info = self.state.get_connection(env_name)
            if not conn_info or not conn_info.get_client():
                # 环境未连接，自动建立连接
                cli.poutput(f"正在连接到 {env_name}...")
                try:
                    ssh_mgr = SSHClientManager()
                    client = ssh_mgr.connect(
                        host=env_config.host,
                        port=env_config.port,
                        username=env_config.username,
                        password=env_config.password,
                        key_path=env_config.key_path,
                    )

                    # 创建连接信息
                    from ptk_repl.modules.ssh.state import SSHConnectionInfo

                    conn_info = SSHConnectionInfo(
                        name=env_config.name,
                        host=env_config.host,
                        port=env_config.port,
                        username=env_config.username,
                        is_active=True,
                    )
                    conn_info.set_client(client)

                    # 添加到连接池
                    self.state.add_connection(conn_info)

                    # 设置为当前环境
                    _set_current_environment(cli, env_config.name)

                    cli.poutput(f"已连接到 {env_name}")
                except Exception as e:
                    cli.perror(f"连接失败: {e}")
                    return

            # 7. 执行日志查看
            try:
                cli.poutput(f"正在查看 {env_name} 的 {log_config.name}... (Ctrl+C 退出)")
                tail_log(conn_info.get_client(), log_config, mode)
            except KeyboardInterrupt:
                cli.poutput("\n日志查看已终止")
            except Exception as e:
                cli.perror(f"查看日志失败: {e}")


def _set_current_environment(cli: "PromptToolkitCLI", env_name: str) -> None:
    """设置当前环境。

    Args:
        cli: PromptToolkitCLI 实例
        env_name: 环境名称
    """
    gs = cli.state.global_state
    gs.connected = True
    gs.connection_type = "ssh"
    gs.current_ssh_env = env_name
