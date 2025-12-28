# API 参考

PTK_REPL 核心 API 完整参考文档。

## 📦 目录

- [核心组件](#核心组件)
  - [PromptToolkitCLI](#prompttoolkitcli)
  - [CommandRegistry](#commandregistry)
  - [StateManager](#statemanager)
  - [ConfigManager](#configmanager)
  - [AutoCompleter](#autocompleter)
- [基类和接口](#基类和接口)
  - [CommandModule](#commandmodule)
  - [ModuleState](#modulestate)
- [装饰器](#装饰器)
  - [typed_command](#typed_command)
- [工具类](#工具类)
  - [HelpFormatter](#helpformatter)

## 核心组件

### PromptToolkitCLI

**文件**: [`src/ptk_repl/cli.py`](../src/ptk_repl/cli.py)

主控制器，管理所有核心组件和命令循环。

#### 初始化

```python
from ptk_repl.cli import PromptToolkitCLI
from pathlib import Path

cli = PromptToolkitCLI(
    config_path="ptk_repl_config.yaml",
    history_path=Path.home() / ".ptk_repl_history"
)
```

#### 主要方法

##### `cmdloop()`

启动命令循环。

```python
cli.cmdloop()
```

##### `register_command()`

注册命令到注册表。

```python
def handler(args: list[str]) -> None:
    print("执行命令")

cli.register_command(
    module_name="mymodule",
    command_name="mycommand",
    handler=handler,
    aliases=["mycmd", "mc"]
)
```

**参数**：
- `module_name` (str): 模块名称
- `command_name` (str): 命令名称
- `handler` (Callable): 命令处理函数
- `aliases` (list[str] | None): 命令别名列表

##### `register_module_commands()`

注册模块的所有命令。

```python
module = MyModule()
cli.register_module_commands(module)
```

##### `poutput()` / `perror()` / `pwarn()`

输出消息。

```python
cli.poutput("普通消息")
cli.perror("错误消息")
cli.pwarn("警告消息")
```

---

### CommandRegistry

**文件**: [`src/ptk_repl/core/registry.py`](../src/ptk_repl/core/registry.py)

命令注册表，管理所有模块和命令。

#### 主要方法

##### `register_command()`

```python
cli.registry.register_command(
    module_name="core",
    command_name="status",
    handler=do_status,
    aliases=["st"]
)
```

##### `get_command_info()`

获取命令信息。

```python
info = cli.registry.get_command_info("status")
# 返回: ("core", "status", do_status)
```

##### `get_module()`

获取模块实例。

```python
module = cli.registry.get_module("ssh")
# 返回: SSHModule 实例
```

##### `list_modules()`

列出所有模块。

```python
modules = cli.registry.list_modules()
# 返回: [CoreModule(), SSHModule(), DatabaseModule()]
```

##### `list_module_commands()`

列出模块的所有命令。

```python
commands = cli.registry.list_module_commands("ssh")
# 返回: ["connect", "disconnect", "log"]
```

---

### StateManager

**文件**: [`src/ptk_repl/core/state_manager.py`](../src/ptk_repl/core/state_manager.py)

状态管理器，管理全局状态和模块状态。

#### 属性

```python
cli.state.global_state  # GlobalState 实例
```

**GlobalState 字段**：
- `connected`: bool - 是否已连接
- `current_host`: str | None - 当前主机
- `current_port`: int | None - 当前端口
- `auth_token`: str | None - 认证令牌
- `connection_type`: str | None - 连接类型 ("ssh" | "database")
- `current_ssh_env`: str | None - 当前 SSH 环境名称

#### 主要方法

##### `get_module_state()`

获取模块状态。

```python
from ptk_repl.modules.ssh.state import SSHState

ssh_state = cli.state.get_module_state("ssh", SSHState)
# 如果状态不存在，创建新实例
# 如果状态已存在，返回现有实例
```

**参数**：
- `module_name` (str): 模块名称
- `state_cls` (type[ModuleState]): 状态类

**返回**: `state_cls` 实例

##### `reset_global_state()`

重置全局状态。

```python
cli.state.reset_global_state()
```

##### `reset_module_state()`

重置模块状态。

```python
cli.state.reset_module_state("ssh")
```

---

### ConfigManager

**文件**: [`src/ptk_repl/core/config_manager.py`](../src/ptk_repl/core/config_manager.py)

配置管理器，加载和管理 YAML 配置。

#### 主要方法

##### `get()`

获取配置值。

```python
# 获取顶层配置
preload_modules = cli.config.get("core.preload_modules", [])

# 获取嵌套配置
ssh_envs = cli.config.get("modules.ssh.environments", [])

# 获取整个配置字典
all_config = cli.config.get_all()
```

**参数**：
- `key` (str): 配置键，支持点号分隔的路径
- `default` (Any): 默认值

**返回**: 配置值

##### `reload()`

重新加载配置文件。

```python
cli.config.reload()
```

---

### AutoCompleter

**文件**: [`src/ptk_repl/core/completer.py`](../src/ptk_repl/core/completer.py)

自动补全器，从 CommandRegistry 自动发现命令。

#### 注册懒加载模块

```python
# 为尚未加载的模块预声明命令，用于补全
cli.registry.set_completer(cli.auto_completer)
cli.auto_completer.register_lazy_commands("redis", [
    "connect", "disconnect", "execute", "status"
])
```

#### 转换为 prompt_toolkit Completer

```python
from prompt_toolkit import PromptSession

session = PromptSession(
    completer=cli.auto_completer.to_prompt_toolkit_completer()
)
```

---

## 基类和接口

### CommandModule

**文件**: [`src/ptk_repl/core/base.py`](../src/ptk_repl/core/base.py)

所有模块必须继承的基类。

#### 抽象属性和方法

```python
from abc import abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager

class MyModule(CommandModule):
    @property
    @abstractmethod
    def name(self) -> str:
        """模块唯一标识符。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """模块描述。"""
        ...

    @abstractmethod
    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册模块命令。"""
        ...
```

#### 可选属性和方法

```python
class MyModule(CommandModule):
    @property
    def aliases(self) -> list[str]:
        """模块别名。"""
        return ["short_name"]

    @property
    def version(self) -> str:
        """模块版本。"""
        return "1.0.0"

    def initialize(self, state_manager: "StateManager") -> None:
        """模块初始化回调。"""
        self.state = state_manager.get_module_state(
            self.name, MyModuleState
        )

    def shutdown(self) -> None:
        """模块关闭回调。"""
        # 清理资源
        pass
```

---

### ModuleState

**文件**: [`src/ptk_repl/state/module_state.py`](../src/ptk_repl/state/module_state.py)

模块状态基类，所有模块状态必须继承。

#### 定义状态

```python
from pydantic import Field
from ptk_repl.state.module_state import ModuleState

class MyModuleState(ModuleState):
    """我的模块状态。"""

    counter: int = Field(default=0, description="计数器")
    last_action: str | None = Field(default=None, description="最后操作")

    def reset(self) -> None:
        """重置状态。"""
        self.counter = 0
        self.last_action = None
```

#### 使用状态

```python
def initialize(self, state_manager):
    # 获取状态
    self.state = state_manager.get_module_state(
        self.name, MyModuleState
    )

def do_increment(self, args):
    # 访问状态
    self.state.counter += 1
    self.state.last_action = "increment"

    print(f"计数: {self.state.counter}")
```

---

## 装饰器

### typed_command

**文件**: [`src/ptk_repl/core/decorators.py`](../src/ptk_repl/core/decorators.py)

基于 Pydantic v2 的类型安全命令装饰器。

#### 基本使用

```python
from pydantic import BaseModel, Field
from ptk_repl.core.decorators import typed_command

class ConnectArgs(BaseModel):
    """连接参数。"""

    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口")

@typed_command(ConnectArgs)
def do_connect(self, args: ConnectArgs) -> None:
    """连接到服务器。"""
    print(f"连接到 {args.host}:{args.port}")
```

#### 参数验证

typed_command 自动：
- 解析命令行参数
- 验证类型和范围
- 提供默认值
- 生成错误消息

**示例**：

```bash
# 用户输入
(ptk) mymodule connect localhost --port 7000

# 自动解析为
ConnectArgs(host="localhost", port=7000)

# 验证失败时
(ptk) mymodule connect localhost --port 99999
# 参数验证错误:
# port
#   Field error
#     Port must be less than or equal to 65535
#       Input type: integer
```

#### 支持的参数类型

```python
class ComplexArgs(BaseModel):
    # 必填参数
    name: str = Field(..., description="名称")

    # 可选参数（有默认值）
    count: int = Field(default=1, description="次数")

    # 类型验证
    age: int = Field(ge=0, le=150, description="年龄")

    # 枚举
    mode: str = Field(pattern="^(fast|slow)$", description="模式")

    # 联合类型
    value: str | None = Field(default=None)

    # 列表
    tags: list[str] = Field(default_factory=list)
```

#### 命令别名

```python
@cli.command(aliases=["conn", "c"])
@typed_command(ConnectArgs)
def do_connect(args: ConnectArgs) -> None:
    pass
```

---

## 工具类

### HelpFormatter

**文件**: [`src/ptk_repl/core/help_formatter.py`](../src/ptk_repl/core/help_formatter.py)

帮助信息格式化器。

#### 使用方式

```python
from ptk_repl.core.help_formatter import HelpFormatter

formatter = HelpFormatter(cli)

# 生成总览帮助
overview = formatter.format_overview_help()
print(overview)

# 生成命令详细帮助
cmd_help = formatter.format_command_help("ssh", "connect")
print(cmd_help)

# 生成模块帮助
module_help = formatter.format_module_help("ssh")
print(module_help)
```

---

## 完整示例

### 创建自定义模块

```python
"""文件管理模块。"""

from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field

from ptk_repl.core.base import CommandModule
from ptk_repl.core.decorators import typed_command

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager


class ListArgs(BaseModel):
    """列表参数。"""

    path: str = Field(default=".", description="目录路径")
    show_hidden: bool = Field(default=False, description="显示隐藏文件")


class FileModule(CommandModule):
    """文件管理模块。"""

    def __init__(self) -> None:
        super().__init__()
        self.cli: "PromptToolkitCLI | None" = None

    @property
    def name(self) -> str:
        return "file"

    @property
    def description(self) -> str:
        return "文件操作"

    @property
    def aliases(self) -> list[str]:
        return ["f"]

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        self.cli = cli

        @cli.command()
        @typed_command(ListArgs)
        def do_list(args: ListArgs) -> None:
            """列出文件。"""
            import os

            files = os.listdir(args.path)
            if not args.show_hidden:
                files = [f for f in files if not f.startswith(".")]

            cli.poutput(f"文件列表 ({args.path}):")
            for f in files:
                cli.poutput(f"  {f}")
```

### 注册命令的不同方式

```python
class MyModule(CommandModule):
    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        # 方式 1: 简单命令（无参数验证）
        @cli.command()
        def do_status(args: list[str]) -> None:
            cli.poutput("状态: OK")

        # 方式 2: 类型安全命令（参数验证）
        @cli.command(aliases=["st"])
        @typed_command(StatusArgs)
        def do_status_detailed(args: StatusArgs) -> None:
            cli.poutput(f"状态: {args.detail}")

        # 方式 3: 手动注册
        def do_custom(args: list[str]) -> None:
            pass

        cli.register_command(
            module_name="mymodule",
            command_name="custom",
            handler=do_custom,
            aliases=["cust"]
        )
```

---

## 类型注解参考

### 常用类型

```python
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager

# 函数类型注解
def register_commands(self, cli: "PromptToolkitCLI") -> None:
    pass

def initialize(self, state_manager: "StateManager") -> None:
    pass

# 可选参数
def connect(self, host: str, port: int = 22) -> None:
    pass

# 联合返回类型
def get_connection(self) -> SSHClient | None:
    pass

# 列表和字典
def list_files(self, path: str) -> list[str]:
    pass

def get_config(self) -> dict[str, Any]:
    pass
```

### 类型断言

```python
from typing import cast

# 断言为具体类型
module = cast(CommandModule, registry.get_module(name))

# 断言联合类型中的具体类型
host = cast(str, module.host)  # module.host 可能是 Any
```

---

## 相关文档

- [架构设计](../design/architecture.md)
- [模块开发教程](../guides/module-development.md)
- [开发指南](../development/development.md)

---

**最后更新**: 2025-12-28
