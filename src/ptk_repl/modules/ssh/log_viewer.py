"""SSH 日志查看器。"""

from typing import TYPE_CHECKING

from ptk_repl.modules.ssh.config import load_ssh_config
from ptk_repl.modules.ssh.dialogs import select_environment_dialog, select_log_dialog
from ptk_repl.modules.ssh.ssh_client import SSHClientManager
from ptk_repl.modules.ssh.state import SSHConnectionInfo, SSHState
from ptk_repl.modules.ssh.tail import tail_log

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI


class SSHLogViewer:
    """SSH 日志查看器。

    负责查看服务器日志。
    """

    def __init__(self, cli: "PromptToolkitCLI", ssh_state: SSHState) -> None:
        """初始化 SSH 日志查看器。

        Args:
            cli: PromptToolkitCLI 实例
            ssh_state: SSH 模块状态
        """
        self.cli = cli
        self.ssh_state = ssh_state

    def view_log(
        self, env: str | None = None, mode: str | None = None, file: str | None = None
    ) -> None:
        """查看服务器日志。

        Args:
            env: 环境名称（可选）
            mode: 日志模式（可选）
            file: 日志文件名称（可选）
        """
        gs = self.cli.state.global_state
        config = load_ssh_config(self.cli.config)

        # 1. 确定目标环境
        env_name = env
        if not env_name:
            env_name = gs.current_ssh_env

        if not env_name:
            # 没有当前环境，弹出选择对话框
            env_name = select_environment_dialog(config, self.ssh_state, gs)
            if not env_name:
                return

        # 2. 查找环境配置
        env_config = None
        for e in config.environments:
            if e.name == env_name:
                env_config = e
                break

        if not env_config:
            self.cli.perror(f"环境 '{env_name}' 不存在")
            return

        # 3. 确定日志模式（优先使用命令行参数，否则使用环境的 log_type）
        log_mode = mode or env_config.log_type

        # 4. 从全局配置获取该模式的日志路径
        log_configs = config.log_paths.get(log_mode, [])
        if not log_configs:
            self.cli.perror(f"模式 '{log_mode}' 没有配置日志路径")
            return

        # 5. 确定具体的日志文件
        if file:
            # 用户指定了文件
            log_config = next((lc for lc in log_configs if lc.name == file), None)
            if not log_config:
                available = [lc.name for lc in log_configs]
                self.cli.perror(f"日志 '{file}' 不存在。可用: {', '.join(available)}")
                return
        elif len(log_configs) == 1:
            log_config = log_configs[0]
        else:
            # 多个日志，弹出选择对话框
            log_config = select_log_dialog(log_configs, log_mode)
            if not log_config:
                return

        # 6. 获取或建立 SSH 连接
        conn_info = self.ssh_state.get_connection(env_name)
        if not conn_info or not conn_info.get_client():
            # 环境未连接，自动建立连接
            self.cli.poutput(f"正在连接到 {env_name}...")
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
                conn_info = SSHConnectionInfo(
                    name=env_config.name,
                    host=env_config.host,
                    port=env_config.port,
                    username=env_config.username,
                    is_active=True,
                )
                conn_info.set_client(client)

                # 添加到连接池
                self.ssh_state.add_connection(conn_info)

                # 设置为当前环境
                gs.connected = True
                gs.connection_type = "ssh"
                gs.current_ssh_env = env_config.name

                self.cli.poutput(f"已连接到 {env_name}")
            except Exception as e:
                self.cli.perror(f"连接失败: {e}")
                return

        # 7. 执行日志查看
        try:
            self.cli.poutput(f"正在查看 {env_name} 的 {log_config.name}... (Ctrl+C 退出)")
            tail_log(conn_info.get_client(), log_config, log_mode)
        except KeyboardInterrupt:
            self.cli.poutput("\n日志查看已终止")
        except Exception as e:
            self.cli.perror(f"查看日志失败: {e}")
