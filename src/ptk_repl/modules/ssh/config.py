"""SSH 配置模型。"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class LogConfig(BaseModel):
    """日志配置基类（使用 Tagged Union）。"""

    log_type: Literal["direct", "k8s", "docker"] = Field(..., description="日志类型")
    name: str = Field(..., description="日志名称")


class DirectLogConfig(LogConfig):
    """直接日志配置。"""

    log_type: Literal["direct"] = Field(default="direct", description="日志类型")
    name: str = Field(..., description="日志名称")
    path: str = Field(..., description="日志文件路径")


class K8sLogConfig(LogConfig):
    """Kubernetes 日志配置。"""

    log_type: Literal["k8s"] = Field(default="k8s", description="日志类型")
    name: str = Field(..., description="日志名称")
    namespace: str | None = Field(default=None, description="命名空间")
    pod: str | None = Field(default=None, description="Pod 名称")
    container: str | None = Field(default=None, description="容器名称")
    path: str | None = Field(default=None, description="容器内日志文件路径（可选）")


class DockerLogConfig(LogConfig):
    """Docker 日志配置。"""

    log_type: Literal["docker"] = Field(default="docker", description="日志类型")
    name: str = Field(..., description="日志名称")
    container_name: str = Field(..., description="容器名称")
    path: str | None = Field(default=None, description="容器内日志文件路径（可选）")


class SSHEnvironment(BaseModel):
    """SSH 环境配置。"""

    name: str = Field(..., description="环境名称")
    description: str = Field(..., description="环境描述")
    host: str = Field(..., description="主机地址")
    port: int = Field(default=22, description="SSH 端口")
    username: str = Field(..., description="用户名")
    password: str | None = Field(default=None, description="密码")
    key_path: str | None = Field(default=None, description="私钥文件路径")
    log_type: str = Field(default="direct", description="日志模式类型: direct/k8s/docker")


class SSHModuleConfig(BaseModel):
    """SSH 模块配置。"""

    environments: list[SSHEnvironment] = Field(default_factory=list)
    log_paths: dict[str, list[LogConfig]] = Field(default_factory=dict)


def load_ssh_config(config_manager: Any) -> SSHModuleConfig:
    """从配置管理器加载 SSH 配置。

    Args:
        config_manager: 配置管理器实例

    Returns:
        SSH 模块配置
    """
    ssh_config_dict = config_manager.get("modules.ssh", {})

    if not ssh_config_dict:
        return SSHModuleConfig()

    # 解析环境列表
    environments = [SSHEnvironment(**env) for env in ssh_config_dict.get("environments", [])]

    # 解析全局日志配置
    log_paths: dict[str, list[LogConfig]] = {}
    raw_log_paths = ssh_config_dict.get("log_paths", {})

    for mode, configs in raw_log_paths.items():
        if mode == "direct":
            log_paths[mode] = [DirectLogConfig(**cfg) for cfg in configs]
        elif mode == "k8s":
            log_paths[mode] = [K8sLogConfig(**cfg) for cfg in configs]
        elif mode == "docker":
            log_paths[mode] = [DockerLogConfig(**cfg) for cfg in configs]

    return SSHModuleConfig(environments=environments, log_paths=log_paths)
