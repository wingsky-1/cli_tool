"""SSH 客户端封装。"""

import paramiko


class SSHClientManager:
    """SSH 客户端管理器。"""

    def connect(
        self,
        host: str,
        port: int,
        username: str,
        password: str | None = None,
        key_path: str | None = None,
        timeout: int = 10,
    ) -> paramiko.SSHClient:
        """建立 SSH 连接。

        Args:
            host: 主机地址
            port: SSH 端口
            username: 用户名
            password: 密码（可选）
            key_path: 私钥文件路径（可选）
            timeout: 连接超时时间（秒）

        Returns:
            已连接的 SSH 客户端

        Raises:
            Exception: 连接失败时抛出异常
        """
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if key_path:
                # 使用私钥连接
                key = paramiko.RSAKey.from_private_key_file(key_path)
                client.connect(
                    hostname=host, port=port, username=username, pkey=key, timeout=timeout
                )
            elif password:
                # 使用密码连接
                client.connect(
                    hostname=host, port=port, username=username, password=password, timeout=timeout
                )
            else:
                raise ValueError("必须提供 password 或 key_path")

            return client

        except Exception as e:
            client.close()
            raise Exception(f"SSH 连接失败 ({host}:{port}): {e}") from e

    def execute_command(self, client: paramiko.SSHClient, command: str) -> tuple[str, str, int]:
        """执行 SSH 命令。

        Args:
            client: SSH 客户端
            command: 要执行的命令

        Returns:
            (stdout, stderr, exit_code) 元组
        """
        stdin, stdout, stderr = client.exec_command(command)
        exit_code = stdout.channel.recv_exit_status()

        stdout_str = stdout.read().decode("utf-8")
        stderr_str = stderr.read().decode("utf-8")

        return stdout_str, stderr_str, exit_code
