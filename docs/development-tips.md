# PTK_REPL 开发技巧

本文档提供 PTK_REPL 开发和使用中的实用技巧。

## 快速开始

### 安装和运行

```bash
# 安装依赖
uv sync

# 运行 REPL
uv run ptk_repl

# 或直接运行模块
uv run python -m ptk_repl.cli
```

### 基本使用

```bash
# 查看帮助
help

# 查看所有模块
modules

# 查看当前状态
status

# 退出
exit
```

---

## 开发技巧

### 1. 模块开发

#### 创建新模块

```python
# src/ptk_repl/modules/myfeature/module.py

from typing import TYPE_CHECKING
from ptk_repl.core.base import CommandModule

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI

class MyFeatureModule(CommandModule):
    @property
    def name(self) -> str:
        return "myfeature"

    @property
    def description(self) -> str:
        return "我的功能模块"

    def initialize(self, state_manager) -> None:
        """模块初始化"""
        from ptk_repl.state.module_state import ModuleState
        self.state = state_manager.get_module_state("myfeature", ModuleState)

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册命令"""
        @cli.command("hello")
        def hello(args: str) -> None:
            """打招呼命令"""
            cli.poutput("Hello from my feature!")
```

#### 使用 Pydantic 验证参数

```python
from pydantic import BaseModel, Field

class MyCommandArgs(BaseModel):
    name: str = Field(..., description="名称")
    count: int = Field(default=1, ge=1, le=100, description="次数")

@cli.command("doit")
@typed_command(MyCommandArgs)
def doit(args: MyCommandArgs) -> None:
    """执行命令"""
    for i in range(args.count):
        cli.poutput(f"{i+1}. {args.name}")
```

---

### 2. 状态管理

#### 全局状态

```python
# 访问全局状态
gs = cli.state.global_state

# 设置连接状态
gs.connected = True
gs.connection_type = "ssh"
gs.current_ssh_env = "production"
```

#### 模块状态

```python
# 定义模块状态
class MyModuleState(ModuleState):
    counter: int = 0
    items: list[str] = []

# 在模块中使用
self.state.counter += 1
self.state.items.append("item1")
```

---

### 3. 命令补全

#### 声明懒加载命令

```python
def register_commands(self, cli: "PromptToolkitCLI") -> None:
    # 先声明命令（用于补全）
    cli.auto_completer.register_lazy_commands("myfeature", [
        "command1",
        "command2",
        "command3"
    ])

    # 然后注册实际命令
    @cli.command("command1")
    def command1(args: str) -> None:
        ...
```

#### 参数补全（自动）

使用 `typed_command` 装饰器后，参数补全会自动生成：

```python
class ConnectArgs(BaseModel):
    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, description="端口号")

@cli.command("connect")
@typed_command(ConnectArgs)
def connect(args: ConnectArgs) -> None:
    ...
```

用户输入 `connect --` 后会自动提示：
- `--host` - 主机地址
- `--port` - 端口号

---

### 4. 配置管理

#### YAML 配置文件

```yaml
# ptk_repl_config.yaml

core:
  preload_modules:
    - core
    - ssh

ssh:
  environments:
    - name: production
      host: prod.example.com
      port: 22
      username: admin
      password: "${PROD_PASSWORD}"  # 支持环境变量
      log_type: k8s

log_paths:
  k8s:
    - name: 应用日志
      path: /var/log/app/app.log
    - name: 错误日志
      path: /var/log/app/error.log
```

#### 读取配置

```python
from ptk_repl.modules.ssh.config import load_ssh_config

config = load_ssh_config(cli.config)

# 访问环境配置
for env in config.environments:
    print(f"{env.name}: {env.host}")
```

---

## 调试技巧

### 1. 查看命令注册

```python
# 在 Python REPL 中
from ptk_repl.cli import PromptToolkitCLI

cli = PromptToolkitCLI()

# 查看所有模块
for module in cli.registry.list_modules():
    print(f"{module.name}: {module.description}")

# 查看模块命令
commands = cli.registry.list_module_commands("ssh")
print(f"SSH 命令: {commands}")
```

### 2. 测试命令解析

```python
# 测试命令解析
cmd_info = cli.registry.get_command_info("ssh env")
if cmd_info:
    module_name, command_name, handler = cmd_info
    print(f"模块: {module_name}, 命令: {command_name}")
```

### 3. 查看补全字典

```python
# 构建补全字典
completion_dict = cli.auto_completer.build_completion_dict()

# 查看顶层补全
print(completion_dict[""])

# 查看模块补全
print(completion_dict["ssh"])
```

---

## 性能优化建议

### 1. 模块预加载

如果某些模块需要快速启动，可以在配置中预加载：

```yaml
core:
  preload_modules:
    - core
    - ssh
    - database
```

### 2. 补全缓存

AutoCompleter 已内置缓存机制，无需手动优化。

### 3. 历史记录

默认历史记录文件：`~/.ptk_repl_history`

可以自定义：

```python
cli = PromptToolkitCLI(
    history_path="/custom/path/to/history"
)
```

---

## 常见问题

### Q: 如何添加新的核心命令？

A: 在 `src/ptk_repl/modules/core/module.py` 中添加：

```python
@cli.command("mycommand")
def mycommand(args: str) -> None:
    """我的新命令"""
    cli.poutput("执行新命令")
```

### Q: 如何修改提示符？

A: 编辑 `src/ptk_repl/core/prompts/prompt_provider.py`：

```python
def get_prompt(self) -> str:
    """动态生成提示符。"""
    gs = self.state_manager.global_state
    if gs.connected:
        ctx = gs.get_connection_context()
        if ctx and ctx.is_connected():
            # 使用多态方法，无需 isinstance 检查
            suffix = ctx.get_prompt_suffix()
            return f"(ptk:{suffix}) > "
        elif gs.current_host:
            # 兼容旧版本：显示主机和端口
            return f"(ptk:{gs.current_host}:{gs.current_port}) > "
    return "(ptk) > "
```

### Q: 如何禁用某个模块？

A: 在配置文件中不预加载即可，或者从 `src/ptk_repl/modules/` 中删除。

### Q: 如何调试模块加载问题？

A: 启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 最佳实践

### 1. 命令命名

- 使用简洁明了的动词（如 `connect`, `disconnect`, `query`）
- 避免与内置函数冲突（使用 `do_exit` 而非 `exit`）

### 2. 参数验证

- 始终使用 `typed_command` 进行参数验证
- 为所有参数添加 `description`
- 使用 `Field` 设置合理的默认值和约束

### 3. 错误处理

- 捕获特定异常，而非裸 `except:`
- 提供友好的错误信息
- 使用 `cli.perror()` 输出错误

### 4. 文档

- 为所有命令添加 docstring
- 第一行作为简短描述
- 使用 `用法：` 说明示例

```python
def command_example(args: str) -> None:
    """命令示例。

    用法：
        command_example arg1          # 基本用法
        command_example arg1 --opt    # 带选项

    示例：
        command_example test --count=5
    """
```

---

## 扩展阅读

- [架构设计](architecture.md)
- [模块开发教程](module-development.md)
- [API 参考](api-reference.md)

---

*最后更新：2025-12-28*
