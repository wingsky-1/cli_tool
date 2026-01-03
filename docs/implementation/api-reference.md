# API 参考

PTK_REPL 核心 API 完整参考文档。

## 📦 目录

- [Protocol 接口](#protocol-接口) (2026-01-03 新增)
  - [ICliContext](#iclicontext)
  - [IModuleLoader](#imoduleloader)
  - [IModuleRegister](#imoduleregister)
  - [IModuleDiscoverer](#imodulediscoverer)
  - [ICommandResolver](#icommandresolver)
  - [IPromptProvider](#ipromptprovider)
  - [IRegistry](#iregistry)
- [核心组件](#核心组件)
  - [PromptToolkitCLI](#prompttoolkitcli)
  - [CommandRegistry](#commandregistry)
  - [StateManager](#statemanager)
  - [ConfigManager](#configmanager)
  - [AutoCompleter](#autocompleter)
- [模块加载系统](#模块加载系统) (2026-01-03 重构)
  - [LazyModuleTracker](#lazymoduletracker)
  - [ModuleDiscoveryService](#modulediscoveryservice)
  - [UnifiedModuleLoader](#unifiedmoduleloader)
  - [ModuleRegister](#moduleregister)
  - [ModuleLifecycleManager](#modulelifecyclemanager)
- [基类和接口](#基类和接口)
  - [CommandModule](#commandmodule)
  - [ModuleState](#modulestate)
- [装饰器](#装饰器)
  - [typed_command](#typed_command)
- [工具类](#工具类)
  - [HelpFormatter](#helpformatter)

## Protocol 接口

PTK_REPL 使用 **Protocol 接口**支持鸭子类型和依赖注入。所有接口都使用 `@runtime_checkable` 装饰器，支持运行时类型检查。

### ICliContext

**文件**: [`src/ptk_repl/core/interfaces/cli_context.py`](../src/ptk_repl/core/interfaces/cli_context.py)

**用途**: CLI 上下文接口，提供统一的输出和状态管理接口。

#### 方法

##### `poutput(text: str) -> None`

输出普通消息。

**参数**:
- `text` (str): 要输出的消息

**示例**:
```python
@runtime_checkable
class ICliContext(Protocol):
    def poutput(self, text: str) -> None: ...

class MyCLI:
    def poutput(self, text: str) -> None:
        print(text)

# 类型检查
cli: ICliContext = MyCLI()
cli.poutput("Hello")
```

---

##### `perror(text: str) -> None`

输出错误消息。

**参数**:
- `text` (str): 错误消息

---

#### 属性

- `state: StateManager` - 状态管理器
- `registry: CommandRegistry` - 命令注册表

---

### IModuleLoader

**文件**: [`src/ptk_repl/core/interfaces/module_loader.py`](../src/ptk_repl/core/interfaces/module_loader.py)

**用途**: 模块加载器接口，支持懒加载和即时加载。

#### 方法

##### `load(module_name: str) -> CommandModule | None`

加载模块。

**参数**:
- `module_name` (str): 模块名称

**返回**: 模块实例，如果加载失败返回 None

---

##### `is_loaded(module_name: str) -> bool`

检查模块是否已加载。

**参数**:
- `module_name` (str): 模块名称

**返回**: 是否已加载

---

##### `ensure_module_loaded(module_name: str) -> None`

确保模块已加载（懒加载）。

**参数**:
- `module_name` (str): 模块名称

---

#### 属性

- `loaded_modules: dict[str, CommandModule]` - 已加载的模块字典
- `lazy_modules: dict[str, type]` - 懒加载模块字典

---

### IModuleRegister

**文件**: [`src/ptk_repl/core/interfaces/module_register.py`](../src/ptk_repl/core/interfaces/module_register.py)

**用途**: 模块注册器接口。

#### 方法

##### `register(module: CommandModule) -> None`

注册模块。

**参数**:
- `module` (CommandModule): 模块实例

---

##### `is_registered(module_name: str) -> bool`

检查模块是否已注册。

**参数**:
- `module_name` (str): 模块名称

**返回**: 是否已注册

---

##### `get_module(module_name: str) -> CommandModule | None`

获取已注册的模块。

**参数**:
- `module_name` (str): 模块名称

**返回**: 模块实例，如果不存在返回 None

---

### IModuleDiscoverer

**文件**: [`src/ptk_repl/core/interfaces/module_discoverer.py`](../src/ptk_repl/core/interfaces/module_discoverer.py)

**用途**: 模块发现器接口。

#### 方法

##### `discover_modules() -> list[str]`

发现所有可用模块。

**返回**: 模块名称列表

---

##### `preload_all(tracker, resolver, exclude) -> None`

预加载所有模块到追踪器。

**参数**:
- `tracker` (LazyModuleTracker): 懒加载追踪器
- `resolver` (IModuleNameResolver): 名称解析器
- `exclude` (list[str]): 要排除的模块列表

---

### ICommandResolver

**文件**: [`src/ptk_repl/core/interfaces/command_resolver.py`](../src/ptk_repl/core/interfaces/command_resolver.py)

**用途**: 命令名称解析器接口。

#### 方法

##### `resolve(module_name: str) -> str`

解析模块名称为类名。

**参数**:
- `module_name` (str): 模块名称

**返回**: 类名

---

### IPromptProvider

**文件**: [`src/ptk_repl/core/interfaces/prompt_provider.py`](../src/ptk_repl/core/interfaces/prompt_provider.py)

**用途**: 提示符提供者接口。

#### 方法

##### `get_prompt() -> str`

获取提示符字符串。

**返回**: 提示符字符串

---

### IRegistry

**文件**: [`src/ptk_repl/core/interfaces/registry.py`](../src/ptk_repl/core/interfaces/registry.py)

**用途**: 命令注册表接口。

#### 方法

##### `register_command(module_name, command_name, handler, aliases) -> None`

注册命令。

**参数**:
- `module_name` (str): 模块名称
- `command_name` (str): 命令名称
- `handler` (Callable): 命令处理函数
- `aliases` (list[str] | None): 命令别名

---

##### `get_command_info(command_path: str) -> tuple | None`

获取命令信息。

**参数**:
- `command_path` (str): 命令路径（如 "ssh connect"）

**返回**: (模块名, 命令名, 处理器) 元组，如果不存在返回 None

---

##### `get_module(module_name: str) -> CommandModule | None`

获取模块。

**参数**:
- `module_name` (str): 模块名称

**返回**: 模块实例，如果不存在返回 None

---

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

## 模块加载系统（2026-01-03 重构）

### 设计概述

模块加载系统已从旧的 ModuleLoader（183行）重构为4个职责单一的组件（454行），符合**单一职责原则**。

**架构图**：
```
┌─────────────────────────────────────────────────────────────┐
│           ModuleLifecycleManager (门面模式)                  │
│                  core/loaders/module_lifecycle_manager.py   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  Discovery    │  │    Loader     │  │   Register    │
│  Service      │  │               │  │               │
│ (发现模块)     │  │ (加载模块)     │  │ (注册模块)     │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ↓
                  ┌───────────────┐
                  │    Tracker     │
                  │  (追踪状态)     │
                  └───────────────┘
```

---

### LazyModuleTracker

**文件**: [`src/ptk_repl/core/loaders/lazy_module_tracker.py`](../src/ptk_repl/core/loaders/lazy_module_tracker.py)

**职责**: 追踪模块加载状态和别名映射（O(1) 查找）。

#### 初始化

```python
from ptk_repl.core.loaders.lazy_module_tracker import LazyModuleTracker

tracker = LazyModuleTracker()
```

#### 主要方法

##### `add_lazy_module(name: str, cls: type, aliases: list[str] | None = None) -> None`

添加懒加载模块。

**参数**:
- `name` (str): 模块名称
- `cls` (type): 模块类
- `aliases` (list[str] | None): 模块别名列表

---

##### `mark_as_loaded(name: str) -> None`

标记模块为已加载。

**参数**:
- `name` (str): 模块名称

---

##### `is_loaded(name: str) -> bool`

检查模块是否已加载。

**参数**:
- `name` (str): 模块名称

**返回**: 是否已加载

---

##### `find_by_alias(alias: str) -> str | None`

通过别名查找模块名（O(1) 复杂度）。

**参数**:
- `alias` (str): 别名

**返回**: 模块名，如果不存在返回 None

---

#### 属性

- `lazy_modules: dict[str, type]` - 懒加载模块字典（只读）
- `loaded_modules: set[str]` - 已加载模块集合（只读）

---

### ModuleDiscoveryService

**文件**: [`src/ptk_repl/core/loaders/module_discovery_service.py`](../src/ptk_repl/core/loaders/module_discovery_service.py)

**职责**: 自动扫描 `modules/` 目录，发现所有可用模块。

#### 初始化

```python
from pathlib import Path
from ptk_repl.core.loaders.module_discovery_service import ModuleDiscoveryService

discovery_service = ModuleDiscoveryService(
    modules_path=Path("src/ptk_repl/modules")
)
```

**参数**:
- `modules_path` (Path): 模块目录路径

#### 主要方法

##### `discover_modules() -> list[str]`

发现所有可用模块。

**返回**: 模块名称列表

**示例**:
```python
modules = discovery_service.discover_modules()
# 返回: ["core", "ssh", "database"]
```

---

##### `preload_all(tracker, resolver, exclude) -> None`

预加载所有模块到追踪器。

**参数**:
- `tracker` (LazyModuleTracker): 懒加载追踪器
- `resolver` (IModuleNameResolver): 名称解析器
- `exclude` (list[str]): 要排除的模块列表

**示例**:
```python
discovery_service.preload_all(
    tracker=tracker,
    resolver=name_resolver,
    exclude=["core"]
)
```

---

### UnifiedModuleLoader

**文件**: [`src/ptk_repl/core/loaders/unified_module_loader.py`](../src/ptk_repl/core/loaders/unified_module_loader.py)

**职责**: 统一的模块加载逻辑，支持懒加载和即时加载。

#### 初始化

```python
from ptk_repl.core.loaders.unified_module_loader import UnifiedModuleLoader

loader = UnifiedModuleLoader(
    name_resolver=name_resolver,
    lazy_tracker=tracker,
    module_register=module_register,
    post_load_callbacks=[callback1, callback2]
)
```

**参数**:
- `name_resolver` (IModuleNameResolver): 模块名称解析器
- `lazy_tracker` (LazyModuleTracker): 懒加载追踪器
- `module_register` (IModuleRegister): 模块注册器
- `post_load_callbacks` (list[Callable]): 加载后回调列表

#### 主要方法

##### `load(module_name: str) -> CommandModule | None`

加载模块。

**参数**:
- `module_name` (str): 模块名称

**返回**: 模块实例，如果加载失败返回 None

**工作流程**:
1. 检查是否已加载
2. 从懒加载列表获取模块类
3. 动态导入模块（如需要）
4. 创建模块实例
5. 注册到注册表
6. 标记为已加载
7. 执行加载后回调

**示例**:
```python
module = loader.load("ssh")
if module:
    print(f"成功加载 {module.name}")
```

---

##### `is_loaded(module_name: str) -> bool`

检查模块是否已加载。

**参数**:
- `module_name` (str): 模块名称

**返回**: 是否已加载

---

##### `ensure_module_loaded(module_name: str) -> None`

确保模块已加载（懒加载）。

**参数**:
- `module_name` (str): 模块名称

**示例**:
```python
# 确保模块已加载，如果未加载则自动加载
loader.ensure_module_loaded("ssh")
```

---

#### 属性

- `loaded_modules: dict[str, CommandModule]` - 已加载的模块字典
- `lazy_modules: dict[str, type]` - 懒加载模块字典

---

### ModuleRegister

**文件**: [`src/ptk_repl/core/loaders/module_register.py`](../src/ptk_repl/core/loaders/module_register.py)

**职责**: 注册模块到注册表，调用模块初始化方法，错误清理。

#### 初始化

```python
from ptk_repl.core.loaders.module_register import ModuleRegister

register = ModuleRegister(
    command_registry=registry,
    state_manager=state_manager
)
```

**参数**:
- `command_registry` (IRegistry): 命令注册表
- `state_manager` (StateManager): 状态管理器

#### 主要方法

##### `register(module: CommandModule) -> None`

注册模块。

**参数**:
- `module` (CommandModule): 模块实例

**工作流程**:
1. 调用 `module.register_commands(cli)` 注册命令
2. 调用 `module.initialize(state_manager)` 初始化模块
3. 如果失败，清理已注册的命令

**示例**:
```python
try:
    register.register(module)
    print(f"模块 {module.name} 注册成功")
except Exception as e:
    print(f"注册失败: {e}")
```

---

##### `is_registered(module_name: str) -> bool`

检查模块是否已注册。

**参数**:
- `module_name` (str): 模块名称

**返回**: 是否已注册

---

##### `get_module(module_name: str) -> CommandModule | None`

获取已注册的模块。

**参数**:
- `module_name` (str): 模块名称

**返回**: 模块实例，如果不存在返回 None

---

### ModuleLifecycleManager

**文件**: [`src/ptk_repl/core/loaders/module_lifecycle_manager.py`](../src/ptk_repl/core/loaders/module_lifecycle_manager.py)

**职责**: 协调发现、加载、注册等组件（门面模式），提供统一的模块管理接口。

#### 初始化

```python
from pathlib import Path
from ptk_repl.core.loaders.module_lifecycle_manager import ModuleLifecycleManager

lifecycle_manager = ModuleLifecycleManager(
    modules_path=Path("src/ptk_repl/modules"),
    name_resolver=name_resolver,
    module_register=module_register,
    config=config,
    auto_completer=auto_completer,
    register_commands_callback=lambda m: m.register_commands(cli),
    error_callback=lambda msg: cli.perror(msg)
)
```

**参数**:
- `modules_path` (Path): 模块目录路径
- `name_resolver` (IModuleNameResolver): 模块名称解析器
- `module_register` (IModuleRegister): 模块注册器
- `config` (ConfigManager): 配置管理器
- `auto_completer` (AutoCompleter): 自动补全器
- `register_commands_callback` (Callable): 命令注册回调
- `error_callback` (Callable): 错误回调

#### 主要方法

##### `load_modules() -> None`

加载所有模块（主入口）。

**执行流程**:
1. 自动发现所有模块
2. 预加载到懒加载追踪器
3. 立即加载 core 模块
4. 根据配置预加载其他模块

**示例**:
```python
# 在 CLI 启动时调用
lifecycle_manager.load_modules()
```

---

##### `load_module_immediately(module_name: str) -> None`

立即加载模块。

**参数**:
- `module_name` (str): 模块名称

**示例**:
```python
# 预加载配置中的模块
for module_name in config.get("core.preload_modules", []):
    lifecycle_manager.load_module_immediately(module_name)
```

---

#### IModuleLoader 接口实现

ModuleLifecycleManager 实现了 IModuleLoader 接口，所有方法委托给 UnifiedModuleLoader：

- `load(module_name) -> CommandModule | None`
- `is_loaded(module_name) -> bool`
- `ensure_module_loaded(module_name) -> None`
- `loaded_modules: dict[str, CommandModule]`
- `lazy_modules: dict[str, type]`

---

### 使用示例

#### 完整的模块加载流程

```python
from pathlib import Path
from ptk_repl.core.loaders.module_lifecycle_manager import ModuleLifecycleManager

# 1. 创建生命周期管理器
lifecycle_manager = ModuleLifecycleManager(
    modules_path=Path("src/ptk_repl/modules"),
    name_resolver=name_resolver,
    module_register=module_register,
    config=config,
    auto_completer=auto_completer,
    register_commands_callback=lambda m: m.register_commands(cli),
    error_callback=lambda msg: cli.perror(msg)
)

# 2. 加载所有模块
lifecycle_manager.load_modules()

# 3. 懒加载单个模块
lifecycle_manager.ensure_module_loaded("ssh")

# 4. 检查模块是否已加载
if lifecycle_manager.is_loaded("ssh"):
    print("SSH 模块已加载")
```

#### 直接使用 UnifiedModuleLoader

```python
from ptk_repl.core.loaders.unified_module_loader import UnifiedModuleLoader

loader = UnifiedModuleLoader(
    name_resolver=name_resolver,
    lazy_tracker=tracker,
    module_register=module_register,
    post_load_callbacks=[]
)

# 加载模块
module = loader.load("database")
if module:
    print(f"成功加载: {module.name}")
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

**最后更新**: 2026-01-03
