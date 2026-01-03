"""类型安全命令装饰器。"""

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from ptk_repl.core.interfaces.cli_context import ICliContext


def _parse_args_to_dict(arg_str: str, model_cls: type[BaseModel]) -> dict[str, Any]:
    """解析参数字符串为字典。

    Args:
        arg_str: 参数字符串
        model_cls: Pydantic 模型类

    Returns:
        参数字典
    """
    import shlex

    try:
        tokens = shlex.split(arg_str)
    except ValueError:
        tokens = arg_str.split()

    kwargs: dict[str, Any] = {}
    i = 0
    fields = model_cls.model_fields

    while i < len(tokens):
        token = tokens[i]

        if token.startswith("--"):
            # 长选项
            key = token[2:].replace("-", "_")
            if key in fields:
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    kwargs[key] = tokens[i + 1]
                    i += 2
                else:
                    kwargs[key] = True
                    i += 1
        elif token.startswith("-") and len(token) == 2:
            # 短选项
            key = token[1]
            # 查找匹配的字段
            matching_fields = [f for f in fields if f.startswith(key)]
            if matching_fields:
                field_name = matching_fields[0]
                if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                    kwargs[field_name] = tokens[i + 1]
                    i += 2
                else:
                    kwargs[field_name] = True
                    i += 1
            else:
                i += 1
        else:
            # 位置参数
            positional = [f for f in fields if f not in kwargs]
            if positional:
                kwargs[positional[0]] = token
            i += 1

    return kwargs


def typed_command[T: BaseModel](
    model_cls: type[T],
) -> Callable[[Callable[..., Any]], Callable[["ICliContext", str], None]]:
    """类型安全命令装饰器。

    使用 Pydantic 模型进行参数验证。

    现在使用 ICliContext 接口，提供类型安全。

    Args:
        model_cls: Pydantic 模型类

    Returns:
        装饰器函数

    Example:
        ```python
        from pydantic import BaseModel, Field

        class ConnectArgs(BaseModel):
            host: str = Field(description="主机地址")
            port: int = Field(default=5432, description="端口号")

        @typed_command(ConnectArgs)
        def do_connect(self, args: ConnectArgs):
            print(f"连接到 {args.host}:{args.port}")
        ```
    """

    def decorator(func: Callable[..., Any]) -> Callable[["ICliContext", str], None]:
        @wraps(func)
        def wrapper(cli_context: "ICliContext", arg_str: str) -> None:
            try:
                kwargs = _parse_args_to_dict(arg_str, model_cls)
                args = model_cls(**kwargs)
                func(args)  # func 作为闭包，已经能访问外部的 self
            except ValidationError as e:
                cli_context.perror(f"参数验证错误:\n{e}")
            except ValueError as e:
                cli_context.perror(f"参数解析错误: {e}")
            except Exception as e:
                cli_context.perror(f"错误: {e}")

        wrapper._is_typed_wrapper = True  # type: ignore[attr-defined]
        wrapper._original_func = func  # type: ignore[attr-defined]
        wrapper._typed_model = model_cls  # type: ignore[attr-defined]
        return wrapper

    return decorator
