"""SSH 连接管理器。"""

from typing import TYPE_CHECKING

from ptk_repl.modules.ssh.config import load_ssh_config
from ptk_repl.modules.ssh.ssh_client import SSHClientManager
from ptk_repl.modules.ssh.state import SSHConnectionInfo, SSHState
from ptk_repl.state.connection_context import SSHConnectionContext

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI


class SSHConnectionManager:
    """SSH 连接管理器。

    负责建立、管理和断开 SSH 连接。
    """

    def __init__(self, cli: "PromptToolkitCLI", ssh_state: SSHState) -> None:
        """初始化 SSH 连接管理器。

        Args:
            cli: PromptToolkitCLI 实例
            ssh_state: SSH 模块状态
        """
        self.cli = cli
        self.ssh_state = ssh_state

    def connect_to_environment(self, env_name: str) -> bool:
        """连接到指定的环境。

        Args:
            env_name: 环境名称

        Returns:
            连接是否成功
        """
        config = load_ssh_config(self.cli.config)

        # 查找环境配置
        env_config = None
        for env in config.environments:
            if env.name == env_name:
                env_config = env
                break

        if not env_config:
            available = [e.name for e in config.environments]
            self.cli.perror(f"环境 '{env_name}' 不存在。可用环境: {', '.join(available)}")
            return False

        # 检查是否已连接
        if env_config.name in self.ssh_state.active_environments:
            conn_info = self.ssh_state.get_connection(env_config.name)
            if conn_info and conn_info.is_active:
                # 已连接，直接设置为当前环境
                self._set_current_environment(env_config.name)
                self.cli.poutput(f"已切换到环境: {env_config.name}")
                return True

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
            self._set_current_environment(env_config.name)

            self.cli.poutput(f"已连接到环境: {env_config.name} ({env_config.description})")
            return True

        except Exception as e:
            self.cli.perror(f"连接失败: {e}")
            return False

    def disconnect_environment(self, env_name: str) -> bool:
        """断开指定环境的连接。

        Args:
            env_name: 环境名称

        Returns:
            断开是否成功
        """
        gs = self.cli.state.global_state

        # 检查环境是否在连接池中
        if env_name not in self.ssh_state.active_environments:
            self.cli.perror(f"环境 '{env_name}' 未连接")
            return False

        # 获取连接信息
        conn_info = self.ssh_state.get_connection(env_name)
        if not conn_info:
            self.cli.perror(f"环境 '{env_name}' 的连接信息不存在")
            return False

        # 关闭 SSH 连接
        try:
            client = conn_info.get_client()
            if client:
                client.close()
        except Exception as e:
            self.cli.poutput(f"关闭连接时出错: {e}")

        # 从连接池移除
        self.ssh_state.remove_connection(env_name)

        # 如果断开的是当前环境，需要切换
        ctx = gs.get_connection_context()
        was_current = isinstance(ctx, SSHConnectionContext) and ctx.current_env == env_name
        if was_current:
            next_env = self.ssh_state.get_first_active_environment()
            if next_env:
                new_ctx = SSHConnectionContext()
                new_ctx.set_env(next_env)
                gs.set_connection_context(new_ctx)
                self.cli.poutput(f"已断开 {env_name}，当前环境切换为: {next_env}")
            else:
                gs.clear_connection_context()
                self.cli.poutput(f"已断开 {env_name}，没有其他活跃连接")
        else:
            self.cli.poutput(f"已断开 {env_name}")

        return True

    def _set_current_environment(self, env_name: str) -> None:
        """设置当前环境。

        Args:
            env_name: 环境名称
        """
        gs = self.cli.state.global_state
        ssh_ctx = SSHConnectionContext()
        ssh_ctx.set_env(env_name)
        gs.set_connection_context(ssh_ctx)
