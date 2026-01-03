# 模块开发教程

本教程将指导你如何为 PTK_REPL 创建自定义模块。

## 🎯 教程概述

我们将创建一个 **Redis 管理模块**，支持：
- 连接到 Redis 服务器
- 执行 Redis 命令
- 管理多个 Redis 连接

## 📦 第一步：创建模块目录

```bash
mkdir -p src/ptk_repl/modules/redis
touch src/ptk_repl/modules/redis/__init__.py
touch src/ptk_repl/modules/redis/module.py
touch src/ptk_repl/modules/redis/state.py
```

## 📝 第二步：定义模块状态

创建 `state.py`，定义模块的状态模型：

```python
"""Redis 模块状态。"""

from pydantic import Field
from ptk_repl.state.module_state import ModuleState


class RedisState(ModuleState):
    """Redis 模块状态。"""

    active_connection: str | None = Field(default=None, description="当前活跃连接名称")
    connections: dict[str, dict[str, str | int]] = Field(
        default_factory=dict,
        description="Redis 连接池"
    )

    def reset(self) -> None:
        """重置 Redis 状态。"""
        self.active_connection = None
        self.connections.clear()
```

**状态字段说明**：
- `active_connection`: 当前使用的连接名称
- `connections`: 所有连接的配置（host, port, db 等）

## 🏗️ 第三步：实现模块类

创建 `module.py`，实现 Redis 模块：

```python
"""Redis 管理模块。"""

from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field

from ptk_repl.core.base import CommandModule
from ptk_repl.core.decorators import typed_command

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager


class ConnectArgs(BaseModel):
    """连接参数。"""

    host: str = Field(..., description="Redis 主机地址")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis 端口")
    db: int = Field(default=0, ge=0, le=15, description="数据库编号")
    password: str | None = Field(default=None, description="密码")


class ExecuteArgs(BaseModel):
    """执行命令参数。"""

    command: str = Field(..., description="Redis 命令（如 GET, SET）")
    args: list[str] = Field(default_factory=list, description="命令参数")


class RedisModule(CommandModule):
    """Redis 管理模块。"""

    def __init__(self) -> None:
        """初始化 Redis 模块。"""
        super().__init__()
        self.cli: "PromptToolkitCLI | None" = None
        self.state: RedisState | None = None

    @property
    def name(self) -> str:
        """模块名称。"""
        return "redis"

    @property
    def description(self) -> str:
        """模块描述。"""
        return "Redis 连接和命令管理"

    @property
    def aliases(self) -> list[str]:
        """模块别名。"""
        return ["r"]

    @property
    def version(self) -> str:
        """模块版本。"""
        return "1.0.0"

    def initialize(self, state_manager: "StateManager") -> None:
        """模块初始化。"""
        from ptk_repl.modules.redis.state import RedisState

        self.state = state_manager.get_module_state("redis", RedisState)

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册 Redis 命令。"""
        self.cli = cli

        @cli.command()
        @typed_command(ConnectArgs)
        def do_connect(args: ConnectArgs) -> None:
            """连接到 Redis 服务器。"""
            if not self.state:
                return

            conn_name = f"{args.host}:{args.port}"
            self.state.connections[conn_name] = {
                "host": args.host,
                "port": args.port,
                "db": args.db,
            }
            self.state.active_connection = conn_name

            cli.poutput(f"✓ 已连接到 Redis: {args.host}:{args.port} [DB {args.db}]")

        @cli.command()
        @typed_command(ExecuteArgs)
        def do_execute(args: ExecuteArgs) -> None:
            """执行 Redis 命令。"""
            if not self.state or not self.state.active_connection:
                cli.perror("未连接到 Redis")
                return

            conn = self.state.connections[self.state.active_connection]
            cli.poutput(f"执行: {args.command} {' '.join(args.args)}")
            cli.poutput(f"(连接: {self.state.active_connection})")

            # TODO: 实际执行 Redis 命令
            # import redis
            # r = redis.Redis(host=conn['host'], port=conn['port'], db=conn['db'])
            # result = r.execute_command(args.command, *args.args)
            # cli.poutput(f"结果: {result}")

        @cli.command()
        def do_status() -> None:
            """显示 Redis 连接状态。"""
            if not self.state:
                return

            if self.state.active_connection:
                conn = self.state.connections.get(self.state.active_connection)
                cli.poutput(f"当前连接: {self.state.active_connection}")
                if conn:
                    cli.poutput(f"  主机: {conn['host']}")
                    cli.poutput(f"  端口: {conn['port']}")
                    cli.poutput(f"  数据库: {conn['db']}")
            else:
                cli.poutput("未连接")

            if self.state.connections:
                cli.poutput(f"\n所有连接: {', '.join(self.state.connections.keys())}")

        @cli.command()
        def do_disconnect() -> None:
            """断开 Redis 连接。"""
            if not self.state:
                return

            if self.state.active_connection:
                cli.poutput(f"已断开: {self.state.active_connection}")
                self.state.active_connection = None
```

**关键点说明**：

1. **类型注解**：
   - 使用 `TYPE_CHECKING` 避免循环导入
   - 所有函数都有完整的类型注解

2. **状态管理**：
   - 在 `initialize()` 中获取模块状态
   - 使用状态存储连接信息

3. **命令注册**：
   - 使用 `@cli.command()` 装饰器注册命令
   - 使用 `@typed_command()` 进行参数验证

4. **别名支持**：
   - `aliases` 属性定义模块别名
   - 用户可以使用 `r` 或 `redis` 访问模块

## 📦 第四步：创建包初始化文件

创建 `__init__.py`，导出模块类：

```python
"""Redis 管理模块。"""

from ptk_repl.modules.redis.module import RedisModule

__all__ = ["RedisModule"]
```

## 🧪 第五步：测试模块

### 1. 运行 REPL

```bash
uv run ptk_repl
```

### 2. 测试基本功能

```bash
# 查看模块列表
(ptk) modules

# 连接到 Redis
(ptk) redis connect localhost --port 6379 --db 0

# 查看状态
(ptk) redis status

# 执行命令
(ptk) redis execute GET --args mykey

# 断开连接
(ptk) redis disconnect

# 使用别名
(ptk) r connect localhost
```

## 🎨 第六步：添加配置支持（可选）

### 更新配置文件

编辑 `ptk_repl_config.yaml`：

```yaml
core:
  preload_modules:
    - core
    - redis    # 添加 Redis 模块

modules:
  redis:
    # 预定义连接
    connections:
      - name: "本地开发"
        host: "localhost"
        port: 6379
        db: 0

      - name: "生产环境"
        host: "redis.example.com"
        port: 6379
        db: 0
        password: "your_password"
```

### 修改模块以支持配置

```python
def initialize(self, state_manager: "StateManager") -> None:
    """模块初始化。"""
    from ptk_repl.modules.redis.state import RedisState

    self.state = state_manager.get_module_state("redis", RedisState)

    # 从配置加载预定义连接
    config = self.cli.config.get("modules.redis", {})
    for conn_config in config.get("connections", []):
        self.state.connections[conn_config["name"]] = conn_config
```

## 🚀 高级功能

### 1. 添加命令别名

```python
def register_commands(self, cli: "PromptToolkitCLI") -> None:
    """注册 Redis 命令。"""

    @cli.command(aliases=["conn", "c"])
    @typed_command(ConnectArgs)
    def do_connect(args: ConnectArgs) -> None:
        """连接到 Redis 服务器。"""
        pass
```

现在用户可以使用：
- `redis connect`
- `redis conn`
- `redis c`

### 2. 添加补全支持

模块自动支持自动补全，无需额外配置。用户输入时会看到：

```
(ptk) redis conn<TAB>
connect    status    execute   disconnect

(ptk) redis connect --<TAB>
--host     --port     --db       --password
```

### 3. 添加帮助文档

```python
def do_connect(args: ConnectArgs) -> None:
    """连接到 Redis 服务器。

    Examples:
        redis connect localhost
        redis connect localhost --port 6380 --db 1
    """
    pass
```

用户可以查看帮助：

```
(ptk) help redis connect
```

## 📊 完整示例

### 基础模块（无状态）

```python
"""简单问候模块。"""

from typing import TYPE_CHECKING

from ptk_repl.core.base import CommandModule

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI


class GreetingModule(CommandModule):
    """问候模块。"""

    @property
    def name(self) -> str:
        return "greeting"

    @property
    def description(self) -> str:
        return "简单的问候功能"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        @cli.command()
        def do_hello(args: list[str]) -> None:
            """打招呼。"""
            name = " ".join(args) if args else "世界"
            cli.poutput(f"你好, {name}!")
```

### 高级模块（带状态和类型验证）

```python
"""计算器模块。"""

from typing import TYPE_CHECKING, cast

from pydantic import BaseModel, Field

from ptk_repl.core.base import CommandModule
from ptk_repl.core.decorators import typed_command
from ptk_repl.state.module_state import ModuleState

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager


class CalculatorState(ModuleState):
    """计算器状态。"""

    history: list[str] = Field(default_factory=list, description="计算历史")
    last_result: float | None = Field(default=None, description="上次计算结果")


class AddArgs(BaseModel):
    """加法参数。"""

    a: float = Field(..., description="第一个数")
    b: float = Field(..., description="第二个数")


class CalculatorModule(CommandModule):
    """计算器模块。"""

    def __init__(self) -> None:
        super().__init__()
        self.cli: "PromptToolkitCLI | None" = None
        self.state: CalculatorState | None = None

    @property
    def name(self) -> str:
        return "calc"

    @property
    def description(self) -> str:
        return "简单计算器"

    def initialize(self, state_manager: "StateManager") -> None:
        self.state = state_manager.get_module_state("calc", CalculatorState)

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        self.cli = cli

        @cli.command(aliases=["add", "sum"])
        @typed_command(AddArgs)
        def do_add(args: AddArgs) -> None:
            """加法运算。"""
            result = args.a + args.b
            cli.poutput(f"{args.a} + {args.b} = {result}")

            if self.state:
                self.state.last_result = result
                self.state.history.append(f"{args.a} + {args.b} = {result}")

        @cli.command()
        def do_history() -> None:
            """显示计算历史。"""
            if self.state and self.state.history:
                for i, entry in enumerate(self.state.history, 1):
                    cli.poutput(f"{i}. {entry}")
```

## 🔧 调试技巧

### 1. 使用日志

```python
import logging

logger = logging.getLogger(__name__)

def do_connect(args: ConnectArgs) -> None:
    logger.info(f"连接到 Redis: {args.host}:{args.port}")
    # ...
```

### 2. 使用 pdb

```python
def do_connect(args: ConnectArgs) -> None:
    import pdb; pdb.set_trace()  # 设置断点
    # ...
```

### 3. 查看状态

```python
@cli.command()
def do_debug() -> None:
    """显示调试信息。"""
    if self.state:
        self.cli.poutput(f"状态: {self.state.model_dump_json(indent=2)}")
```

## 📚 最佳实践

### 1. 命令命名

- 使用动词：`connect`, `disconnect`, `execute`
- 避免缩写：使用 `disconnect` 而非 `disc`
- 保持一致：相似功能使用相同前缀

### 2. 错误处理

```python
def do_connect(args: ConnectArgs) -> None:
    try:
        # 连接逻辑
        pass
    except ConnectionRefusedError:
        self.cli.perror(f"无法连接到 {args.host}:{args.port}")
    except Exception as e:
        self.cli.perror(f"错误: {e}")
```

### 3. 状态验证

```python
def do_execute(args: ExecuteArgs) -> None:
    if not self.state:
        self.cli.perror("模块未初始化")
        return

    if not self.state.active_connection:
        self.cli.perror("未连接到 Redis")
        return

    # 执行逻辑
```

### 4. 类型安全

始终使用 `typed_command` 和 Pydantic 模型：

```python
# ✅ 推荐
@typed_command(ConnectArgs)
def do_connect(args: ConnectArgs) -> None:
    pass

# ❌ 不推荐
def do_connect(args: list[str]) -> None:
    host = args[0]
    port = int(args[1]) if len(args) > 1 else 6379
```

---

## 🔐 使用连接上下文（ConnectionContext）（2026-01-03 新增）

### 什么是连接上下文？

连接上下文（ConnectionContext）是一种**抽象基类**，使用**多态方法**替代 `isinstance` 检查，符合**开闭原则（OCP）**。

### 为什么使用连接上下文？

**问题：旧实现（违反 OCP）**
```python
# ❌ 旧实现：使用 isinstance 检查
def get_prompt_suffix(self) -> str:
    gs = self.state.global_state

    if isinstance(gs.current_connection, SSHConnection):
        return f"@{gs.current_connection.host}"
    elif isinstance(gs.current_connection, DatabaseConnection):
        return f"[{gs.current_connection.database}]"
    # 每次添加新连接类型都需要修改这里！
```

**解决方案：新实现（符合 OCP）**
```python
# ✅ 新实现：使用多态方法
class ConnectionContext(ABC):
    @abstractmethod
    def get_prompt_suffix(self) -> str:
        """返回提示符后缀（多态方法）。"""
        pass

class SSHConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"@{self.host}"

class DatabaseConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"[{self.database}]"

# 添加新连接类型无需修改现有代码！
class RedisConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"redis:{self.host}"
```

### 如何定义连接上下文

**步骤 1**：定义连接上下文类

```python
"""Redis 连接上下文。"""

from ptk_repl.state.connection_context import ConnectionContext, ConnectionType

class RedisConnectionContext(ConnectionContext):
    """Redis 连接上下文。"""

    def __init__(
        self,
        host: str,
        port: int = 6379,
        db: int = 0
    ) -> None:
        """初始化 Redis 连接上下文。

        Args:
            host: Redis 主机地址
            port: Redis 端口
            db: 数据库编号
        """
        self.host = host
        self.port = port
        self.db = db
        self._is_connected = False

    @property
    def connection_type(self) -> ConnectionType:
        """连接类型。"""
        return ConnectionType.REDIS

    @property
    def is_connected(self) -> bool:
        """是否已连接。"""
        return self._is_connected

    def connect(self) -> None:
        """连接到 Redis。"""
        # 实际连接逻辑
        self._is_connected = True

    def disconnect(self) -> None:
        """断开连接。"""
        self._is_connected = False

    def get_prompt_suffix(self) -> str:
        """返回提示符后缀（多态方法）。"""
        return f"redis:{self.host}:{self.port}[{self.db}]"
```

**步骤 2**：在 GlobalState 中组合连接上下文

```python
"""扩展 GlobalState 以支持 Redis 连接上下文。"""

from typing import Literal
from pydantic import Field
from ptk_repl.state.global_state import GlobalState as BaseGlobalState
from ptk_repl.modules.redis.connection_context import RedisConnectionContext

class GlobalState(BaseGlobalState):
    """扩展的全局状态。"""

    redis_context: RedisConnectionContext | None = Field(
        default=None,
        description="Redis 连接上下文"
    )

    def get_active_context(self) -> ConnectionContext | None:
        """获取当前活跃的连接上下文。"""
        # 按优先级返回活跃的连接上下文
        if self.ssh_context and self.ssh_context.is_connected:
            return self.ssh_context
        elif self.db_context and self.db_context.is_connected:
            return self.db_context
        elif self.redis_context and self.redis_context.is_connected:
            return self.redis_context
        return None
```

**步骤 3**：在模块中使用连接上下文

```python
class RedisModule(CommandModule):
    """Redis 管理模块。"""

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册 Redis 命令。"""
        self.cli = cli

        @cli.command()
        @typed_command(ConnectArgs)
        def do_connect(args: ConnectArgs) -> None:
            """连接到 Redis 服务器。"""
            # 创建连接上下文
            context = RedisConnectionContext(
                host=args.host,
                port=args.port,
                db=args.db
            )

            # 连接
            context.connect()

            # 更新 GlobalState
            cli.state.global_state.redis_context = context
            cli.poutput(f"✓ 已连接到 Redis: {args.host}:{args.port}")
```

### 完整示例：Redis 模块使用连接上下文

```python
"""Redis 连接上下文。"""

from enum import Enum
from ptk_repl.state.connection_context import ConnectionContext, ConnectionType

# 扩展 ConnectionType 枚举
class ConnectionType(str, Enum):
    """连接类型枚举。"""
    SSH = "ssh"
    DATABASE = "database"
    REDIS = "redis"  # 新增

class RedisConnectionContext(ConnectionContext):
    """Redis 连接上下文。"""

    def __init__(self, host: str, port: int = 6379, db: int = 0) -> None:
        self.host = host
        self.port = port
        self.db = db
        self._client = None

    @property
    def connection_type(self) -> ConnectionType:
        return ConnectionType.REDIS

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def connect(self) -> None:
        """连接到 Redis。"""
        # import redis
        # self._client = redis.Redis(host=self.host, port=self.port, db=self.db)
        self._client = "mock_client"  # 模拟
        print(f"已连接到 {self.host}:{self.port}")

    def disconnect(self) -> None:
        """断开连接。"""
        if self._client:
            # self._client.close()
            self._client = None

    def get_prompt_suffix(self) -> str:
        """返回提示符后缀。"""
        return f"redis:{self.host}[{self.db}]"

    def execute_command(self, command: str, *args) -> Any:
        """执行 Redis 命令。"""
        if not self.is_connected:
            raise Exception("未连接到 Redis")
        # return self._client.execute_command(command, *args)
        return f"执行: {command} {' '.join(args)}"
```

### 优势总结

- ✅ **开闭原则**：添加新连接类型无需修改现有代码
- ✅ **多态方法**：使用多态替代 `isinstance` 检查
- ✅ **组合优于继承**：GlobalState 组合多个连接上下文
- ✅ **易于扩展**：第三方可以自定义连接上下文

---

## ⚡ 使用错误处理系统（2026-01-03 新增）

### 什么是错误处理系统？

PTK_REPL 使用**责任链模式**处理异常，支持分层错误处理。

### 错误处理链架构

```
ErrorHandlerChain（责任链）
    │
    ├─→ CLIErrorHandler      # 处理 CLIException
    │   ├─ CommandException
    │   └─ ModuleException
    │
    └─→ BaseErrorHandler     # 兜底处理其他异常
```

### 如何定义模块专用异常

**步骤 1**：定义模块异常层次

```python
"""Redis 模块异常。"""

from ptk_repl.core.exceptions.cli_exceptions import CLIException

class RedisException(CLIException):
    """Redis 模块异常基类。"""
    pass

class RedisConnectionError(RedisException):
    """Redis 连接错误。"""

    def __init__(self, message: str, host: str, port: int) -> None:
        """初始化连接错误。

        Args:
            message: 错误消息
            host: 主机地址
            port: 端口号
        """
        super().__init__(message)
        self.host = host
        self.port = port

class RedisCommandError(RedisException):
    """Redis 命令执行错误。"""

    def __init__(self, message: str, command: str) -> None:
        """初始化命令错误。

        Args:
            message: 错误消息
            command: Redis 命令
        """
        super().__init__(message)
        self.command = command

class RedisAuthError(RedisException):
    """Redis 认证错误。"""
    pass
```

**步骤 2**：在命令中抛出异常

```python
class RedisModule(CommandModule):
    """Redis 管理模块。"""

    @cli.command()
    @typed_command(ConnectArgs)
    def do_connect(args: ConnectArgs) -> None:
        """连接到 Redis 服务器。"""
        try:
            # 尝试连接
            client = redis.Redis(host=args.host, port=args.port, db=args.db)
            client.ping()

            # 保存连接
            self.state.active_connection = f"{args.host}:{args.port}"
            self.state.connections[self.state.active_connection] = client

            cli.poutput(f"✓ 已连接到 Redis: {args.host}:{args.port}")

        except redis.AuthenticationError:
            # 认证失败
            raise RedisAuthError(f"Redis 认证失败: {args.host}:{args.port}")

        except redis.ConnectionError as e:
            # 连接失败
            raise RedisConnectionError(
                f"无法连接到 Redis: {str(e)}",
                host=args.host,
                port=args.port
            )

        except Exception as e:
            # 其他错误
            raise RedisException(f"Redis 连接错误: {str(e)}")

    @cli.command()
    @typed_command(ExecuteArgs)
    def do_execute(args: ExecuteArgs) -> None:
        """执行 Redis 命令。"""
        if not self.state or not self.state.active_connection:
            raise RedisCommandError("未连接到 Redis", args.command)

        try:
            client = self.state.connections[self.state.active_connection]
            result = client.execute_command(args.command, *args.args)
            cli.poutput(f"结果: {result}")

        except redis.ResponseError as e:
            raise RedisCommandError(f"命令执行失败: {str(e)}", args.command)
```

**步骤 3**：错误处理链自动处理

错误处理链会自动捕获并显示友好的错误消息：

```python
# 用户执行命令
(ptk) redis connect invalid-host --port 9999

# 错误处理链自动输出
❌ RedisConnectionError: 无法连接到 Redis: Connection refused
  主机: invalid-host
  端口: 9999
```

### CLIException 层次结构

```
CLIException (基类)
    ├─ CommandException
    │   ├─ CommandNotFoundError
    │   └─ InvalidArgumentError
    ├─ ModuleException
    │   ├─ ModuleNotFoundError
    │   └─ ModuleLoadError
    └─ [你的模块专用异常]
        ├─ RedisException
        │   ├─ RedisConnectionError
        │   ├─ RedisCommandError
        │   └─ RedisAuthError
        └─ ...
```

### 错误处理最佳实践

1. **使用专用异常类型**
   ```python
   # ✅ 推荐：使用专用异常
   raise RedisConnectionError("连接失败", host="localhost", port=6379)

   # ❌ 不推荐：使用通用异常
   raise Exception("连接失败")
   ```

2. **提供详细的错误信息**
   ```python
   # ✅ 推荐：包含上下文信息
   raise RedisCommandError(
       f"命令执行失败: {str(e)}",
       command=args.command
   )

   # ❌ 不推荐：信息不足
   raise RedisCommandError("失败", args.command)
   ```

3. **异常层次清晰**
   ```python
   # ✅ 推荐：合理的异常层次
   RedisException (基类)
   ├─ RedisConnectionError (连接相关)
   ├─ RedisCommandError (命令相关)
   └─ RedisAuthError (认证相关)

   # ❌ 不推荐：扁平的异常结构
   RedisError (所有错误)
   ```

### 自定义错误处理器（高级）

如果需要自定义错误处理逻辑，可以扩展错误处理链：

```python
from ptk_repl.core.error_handling.error_handlers import ErrorHandler

class RedisErrorHandler(ErrorHandler):
    """Redis 错误处理器。"""

    def can_handle(self, error: Exception) -> bool:
        """检查是否可以处理此错误。"""
        return isinstance(error, RedisException)

    def handle(self, error: Exception, cli) -> None:
        """处理 Redis 异常。"""
        if isinstance(error, RedisConnectionError):
            cli.perror(f"连接错误: {error.message}")
            cli.perror(f"  主机: {error.host}")
            cli.perror(f"  端口: {error.port}")
        elif isinstance(error, RedisCommandError):
            cli.perror(f"命令错误: {error.message}")
            cli.perror(f"  命令: {error.command}")
        else:
            cli.perror(f"Redis 错误: {error.message}")

# 注册自定义处理器
# cli.error_handler_chain.add_handler(RedisErrorHandler())
```

### 完整示例：带错误处理的 Redis 模块

```python
"""Redis 管理模块（带完整错误处理）。"""

class RedisModule(CommandModule):
    """Redis 管理模块。"""

    @cli.command()
    @typed_command(ConnectArgs)
    def do_connect(args: ConnectArgs) -> None:
        """连接到 Redis 服务器。"""
        try:
            # 连接逻辑
            client = redis.Redis(
                host=args.host,
                port=args.port,
                db=args.db,
                password=args.password,
                socket_connect_timeout=5
            )

            # 测试连接
            client.ping()

            # 保存连接
            conn_name = f"{args.host}:{args.port}"
            self.state.connections[conn_name] = {
                "client": client,
                "host": args.host,
                "port": args.port,
                "db": args.db
            }
            self.state.active_connection = conn_name

            cli.poutput(f"✓ 已连接到 Redis: {args.host}:{args.port} [DB {args.db}]")

        except redis.AuthenticationError:
            raise RedisAuthError(
                f"Redis 认证失败: {args.host}:{args.port}"
            )

        except redis.ConnectionError as e:
            raise RedisConnectionError(
                f"无法连接到 Redis 服务器: {str(e)}",
                host=args.host,
                port=args.port
            )

        except redis.TimeoutError:
            raise RedisConnectionError(
                f"连接超时: {args.host}:{args.port}",
                host=args.host,
                port=args.port
            )

        except Exception as e:
            raise RedisException(f"未知错误: {str(e)}")

    @cli.command()
    def do_disconnect() -> None:
        """断开 Redis 连接。"""
        if not self.state or not self.state.active_connection:
            raise RedisCommandError("未连接到 Redis", "disconnect")

        try:
            conn_name = self.state.active_connection
            client = self.state.connections[conn_name]["client"]
            client.close()

            del self.state.connections[conn_name]
            self.state.active_connection = None

            cli.poutput(f"✓ 已断开连接: {conn_name}")

        except Exception as e:
            raise RedisException(f"断开连接失败: {str(e)}")
```

---

## 🎓 进阶主题

详见：
- [架构设计](../design/architecture.md) - 深入理解框架设计
- [API 参考](../implementation/api-reference.md) - 完整 API 文档
- [开发指南](../development/development.md) - 代码规范和工具

---

**最后更新**: 2026-01-03
