"""交互式对话框 - 使用 questionary 实现。"""

import re
from typing import TYPE_CHECKING, cast

import questionary
from questionary import Choice

if TYPE_CHECKING:
    from ptk_repl.modules.ssh.config import LogConfig, SSHModuleConfig
    from ptk_repl.modules.ssh.state import SSHState
    from ptk_repl.state.global_state import GlobalState


def select_environment_dialog(
    config: "SSHModuleConfig", state: "SSHState", global_state: "GlobalState"
) -> str | None:
    """选择 SSH 环境（带搜索功能）。

    Args:
        config: SSH 模块配置
        state: SSH 模块状态
        global_state: 全局状态

    Returns:
        选中的环境名称，取消则返回 None
    """
    if not config or not config.environments:
        return None

    # 获取当前环境
    from ptk_repl.state.connection_context import SSHConnectionContext

    ctx = global_state.get_connection_context()
    current_env = ctx.current_env if isinstance(ctx, SSHConnectionContext) else None

    # 构建选项列表（包含连接状态）
    choices = []
    for env in config.environments:
        is_connected = env.name in state.active_environments
        is_current = current_env == env.name

        # 状态图标
        if is_current:
            status = "🟢 [当前]"
        elif is_connected:
            status = "🔵 [已连接]"
        else:
            status = "⚪ [未连接]"

        display_text = f"{status} {env.name} - {env.description}"

        # 使用 Choice 对象，value 为环境名
        choices.append(
            Choice(
                title=display_text,
                value=env.name,
            )
        )

    # 使用 questionary.select，支持搜索
    result = questionary.select(
        message="请选择 SSH 环境:",
        choices=choices,
        qmark=">",  # 提示符
        pointer=">",  # 指针
        use_shortcuts=True,  # 启用快捷键
        use_indicator=False,  # 不显示指示器
    ).ask()

    return cast(str | None, result)


def select_log_dialog(log_configs: list["LogConfig"], mode: str) -> "LogConfig | None":
    """选择日志文件（带搜索功能）。

    Args:
        log_configs: 日志配置列表
        mode: 日志模式

    Returns:
        选中的日志配置，取消则返回 None
    """
    if not log_configs:
        return None

    mode_names = {
        "direct": "直接日志",
        "k8s": "Kubernetes 容器日志",
        "docker": "Docker 容器日志",
    }

    # 构建选项列表
    choices = []
    for cfg in log_configs:
        # 显示日志名称和描述
        display_text = cfg.name

        # 使用 getattr 安全访问可选属性
        if cfg.log_type == "direct":
            path = getattr(cfg, "path", None)
            if path:
                display_text += f" ({path})"
        elif cfg.log_type == "docker":
            container_name = getattr(cfg, "container_name", None)
            if container_name:
                display_text += f" (容器: {container_name})"
        elif cfg.log_type == "k8s":
            pod = getattr(cfg, "pod", None)
            if pod:
                display_text += f" (Pod: {pod})"

        choices.append(
            Choice(
                title=display_text,
                value=cfg,  # value 为配置对象本身
            )
        )

    result = questionary.select(
        message=f"选择 {mode_names.get(mode, mode)}:",
        choices=choices,
    ).ask()

    return cast("LogConfig | None", result)


def select_container_dialog(containers: list[str], container_type: str = "容器") -> str | None:
    """选择容器（带搜索功能）。

    Args:
        containers: 容器名称列表
        container_type: 容器类型描述（如 "Docker 容器"、"K8s Pod"）

    Returns:
        选中的容器名称，取消则返回 None
    """
    if not containers:
        return None

    # 单个容器直接返回
    if len(containers) == 1:
        return containers[0]

    # 构建选项列表
    choices = [Choice(title=c, value=c) for c in containers]

    result = questionary.select(
        message=f"选择 {container_type}:",
        choices=choices,
    ).ask()

    return cast(str | None, result)


def match_containers(pattern: str, containers: list[str]) -> list[str]:
    """模糊匹配容器名（保留此函数，用于 tail.py）。

    Args:
        pattern: 匹配模式（支持通配符 * 和正则表达式）
        containers: 容器名称列表

    Returns:
        匹配的容器名称列表
    """
    # 如果模式包含 *，转换为正则表达式
    if "*" in pattern:
        regex_pattern = pattern.replace("*", ".*")
        regex = re.compile(f"^{regex_pattern}$")
        return [c for c in containers if regex.match(c)]

    # 否则使用部分匹配
    pattern_lower = pattern.lower()
    return [c for c in containers if pattern_lower in c.lower()]
