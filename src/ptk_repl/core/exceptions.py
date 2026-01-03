"""CLI 异常层次结构。

提供统一的异常类型，便于错误处理和调试。
"""


class CLIException(Exception):
    """CLI 异常基类。

    所有 CLI 相关异常的基类。
    """

    def __init__(self, message: str, details: dict | None = None) -> None:
        """初始化 CLI 异常。

        Args:
            message: 错误消息
            details: 额外的错误详情（可选）
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """返回错误消息。"""
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


class CommandException(CLIException):
    """命令执行异常。

    命令执行过程中发生的错误。
    """

    pass


class ModuleException(CLIException):
    """模块异常。

    模块加载、初始化或执行过程中发生的错误。
    """

    pass


class ValidationException(CLIException):
    """参数验证异常。

    命令参数验证失败。
    """

    pass


class ConnectionException(CLIException):
    """连接异常。

    SSH、数据库等连接失败。
    """

    pass


class ConfigurationException(CLIException):
    """配置异常。

    配置加载、解析或验证失败。
    """

    pass
