"""日志查看逻辑。"""

import time
from typing import Any

import paramiko


def tail_log(client: paramiko.SSHClient, log_config: Any, mode: str) -> None:
    """查看日志（类似 tail -f）。

    Args:
        client: SSH 客户端
        log_config: 日志配置
        mode: 日志模式 (direct/k8s/docker)
    """
    if mode == "direct":
        _tail_direct_log(client, log_config)
    elif mode == "k8s":
        _tail_k8s_log(client, log_config)
    elif mode == "docker":
        _tail_docker_log(client, log_config)
    else:
        raise ValueError(f"不支持的日志模式: {mode}")


def _execute_command(client: paramiko.SSHClient, command: str) -> str:
    """执行 SSH 命令并返回输出。

    Args:
        client: SSH 客户端
        command: 要执行的命令

    Returns:
        命令输出（去除首尾空白）
    """
    _, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode("utf-8").strip()
    error = stderr.read().decode("utf-8").strip()
    if error:
        raise Exception(f"命令执行错误: {error}")
    return output


def _get_docker_containers(client: paramiko.SSHClient) -> list[str]:
    """获取所有 Docker 容器名称。

    Args:
        client: SSH 客户端

    Returns:
        容器名称列表
    """
    output = _execute_command(client, "docker ps --format '{{.Names}}'")
    return [line.strip() for line in output.split("\n") if line.strip()]


def _get_k8s_pods(client: paramiko.SSHClient, namespace: str | None = None) -> list[str]:
    """获取所有 K8s Pod 名称。

    Args:
        client: SSH 客户��
        namespace: 命名空间（可选）

    Returns:
        Pod 名称列表
    """
    if namespace:
        command = f"kubectl get pods -n {namespace} -o jsonpath='{{.items[*].metadata.name}}'"
    else:
        command = "kubectl get pods -o jsonpath='{.items[*].metadata.name}'"

    output = _execute_command(client, command)
    return [pod.strip() for pod in output.split() if pod.strip()]


def _execute_with_channel(client: paramiko.SSHClient, command: str) -> None:
    """通过 channel 执行命令并实时输出。

    Args:
        client: SSH 客户端
        command: 要执行的命令
    """
    channel = client.invoke_shell()
    channel.send((command + "\n").encode("utf-8"))

    try:
        while True:
            if channel.recv_ready():
                output = channel.recv(1024).decode("utf-8")
                print(output, end="", flush=True)
            time.sleep(0.1)
    except KeyboardInterrupt:
        channel.close()


def _tail_direct_log(client: paramiko.SSHClient, log_config: Any) -> None:
    """查看直接日志文件。

    Args:
        client: SSH 客户端
        log_config: 直接日志配置
    """
    command = f"tail -f {log_config.path}"
    _execute_with_channel(client, command)


def _tail_k8s_log(client: paramiko.SSHClient, log_config: Any) -> None:
    """查看 Kubernetes 日志（支持容器内文件）。

    Args:
        client: SSH 客户端
        log_config: Kubernetes 日志配置
    """
    from ptk_repl.modules.ssh.dialogs import match_containers, select_container_dialog

    # 获取所有 pod 并进行模糊匹配
    all_pods = _get_k8s_pods(client, log_config.namespace)
    matched_pods = match_containers(log_config.pod, all_pods)

    if not matched_pods:
        print(f"未找到匹配的 Pod: {log_config.pod}")
        return

    # 选择具体的 pod
    selected_pod = select_container_dialog(matched_pods, "Kubernetes Pod")
    if not selected_pod:
        return

    # 构建命令
    if log_config.path:
        # 查看容器内文件
        cmd_parts = ["kubectl", "exec"]

        if log_config.namespace:
            cmd_parts.extend(["-n", log_config.namespace])

        cmd_parts.extend([selected_pod, "--", "tail", "-f", log_config.path])
    else:
        # 查看容器默认日志
        cmd_parts = ["kubectl", "logs", "-f"]

        if log_config.namespace:
            cmd_parts.extend(["-n", log_config.namespace])

        cmd_parts.append(selected_pod)

        if log_config.container:
            cmd_parts.extend(["-c", log_config.container])

    command = " ".join(cmd_parts)
    _execute_with_channel(client, command)


def _tail_docker_log(client: paramiko.SSHClient, log_config: Any) -> None:
    """查看 Docker 容器日志（支持容器内文件）。

    Args:
        client: SSH 客户端
        log_config: Docker 日志配置
    """
    from ptk_repl.modules.ssh.dialogs import match_containers, select_container_dialog

    # 获取所有容器并进行模糊匹配
    all_containers = _get_docker_containers(client)
    matched_containers = match_containers(log_config.container_name, all_containers)

    if not matched_containers:
        print(f"未找到匹配的容器: {log_config.container_name}")
        return

    # 选择具体的容器
    selected_container = select_container_dialog(matched_containers, "Docker 容器")
    if not selected_container:
        return

    # 构建命令
    if log_config.path:
        # 查看容器内文件
        command = f"docker exec {selected_container} tail -f {log_config.path}"
    else:
        # 查看容器默认日志
        command = f"docker logs -f {selected_container}"

    _execute_with_channel(client, command)
