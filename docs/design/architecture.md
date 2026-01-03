# PTK_REPL 架构设计

本文档详细描述 PTK_REPL 的架构设计原则和核心组件。

## 📐 架构概览

PTK_REPL 采用**模块化**、**类型安全**和**配置驱动**的设计理念，核心目录按功能域分类（15个子包）。

### 核心设计原则

1. **模块化优先** - 所有功能以模块形式组织，模块间完全解耦
2. **类型安全** - 基于 Pydantic v2 的运行时类型验证
3. **懒加载** - 按需加载模块，最小化启动开销
4. **双层状态** - 全局状态 + 模块隔离状态
5. **自动发现** - 模块自动注册，零配置添加新功能
6. **接口隔离** - 7个Protocol接口支持鸭子类型和依赖注入
7. **单一职责** - 每个子包负责一个功能域

### 目录结构（2026-01-03 重构）

```
src/ptk_repl/
├── cli.py                          # CLI 入口
├── core/                           # 核心框架（按功能域分类）
│   ├── base/                       # 基类和抽象
│   │   ├── __init__.py
│   │   └── command_module.py       # CommandModule 基类
│   ├── cli/                        # CLI 相关组件
│   │   ├── __init__.py
│   │   ├── prompt_manager.py       # 提示符管理
│   │   └── style_manager.py        # 样式管理
│   ├── completion/                 # 自动补全
│   │   ├── __init__.py
│   │   └── auto_completer.py       # AutoCompleter
│   ├── configuration/              # 配置系统
│   │   ├── __init__.py
│   │   ├── config_manager.py       # ConfigManager
│   │   ├── providers/              # 配置提供者
│   │   └── themes/                 # 主题系统
│   ├── decoration/                 # 装饰���
│   │   ├── __init__.py
│   │   └── typed_command.py        # typed_command 装饰器
│   ├── error_handling/             # 错误处理系统（新增）
│   │   ├── __init__.py
│   │   ├── error_handlers.py       # ErrorHandlerChain
│   │   └── exceptions.py           # CLIException 层次结构
│   ├── exceptions/                 # 异常定义
│   │   ├── __init__.py
│   │   └── cli_exceptions.py       # CLIException
│   ├── execution/                  # 命令执行
│   │   ├── __init__.py
│   │   └── command_executor.py     # CommandExecutor
│   ├── formatting/                 # 格式化
│   │   ├── __init__.py
│   │   └── help_formatter.py       # HelpFormatter
│   ├── interfaces/                 # Protocol 接口（新增7个）
│   │   ├── __init__.py
│   │   ├── cli_context.py          # ICliContext
│   │   ├── module_loader.py        # IModuleLoader
│   │   ├── module_register.py      # IModuleRegister
│   │   └── ...
│   ├── loaders/                    # 模块加载系统（重构）
│   │   ├── __init__.py
│   │   ├── lazy_module_tracker.py  # LazyModuleTracker
│   │   ├── unified_module_loader.py # UnifiedModuleLoader
│   │   ├── module_discovery_service.py
│   │   ├── module_lifecycle_manager.py
│   │   └── module_register.py
│   ├── prompts/                    # 提示符管理（新增）
│   │   ├── __init__.py
│   │   └── prompt_provider.py      # IPromptProvider
│   ├── registry/                   # 命令注册表
│   │   ├── __init__.py
│   │   └── command_registry.py     # CommandRegistry
│   ├── resolvers/                  # 名称解析器（新增）
│   │   ├── __init__.py
│   │   └── module_name_resolver.py # IModuleNameResolver
│   └── state/                      # 状态管理
│       ├── __init__.py
│       └── state_manager.py        # StateManager
├── state/                          # 状态定义
│   ├── global_state.py             # GlobalState（使用连接上下文组合）
│   ├── connection_context.py       # ConnectionContext 抽象
│   └── module_state.py             # ModuleState 基类
└── modules/                        # 内置模块
    ├── core/                       # 核心命令
    ├── ssh/                        # SSH 模块
    └── database/                   # 数据库模块
```

### 设计模式应用

| 模式 | 应用场景 | 文件位置 |
|------|---------|---------|
| **门面模式** | ModuleLifecycleManager 统一模块加载 | core/loaders/module_lifecycle_manager.py |
| **策略模式** | 模块名称解析器 | core/resolvers/module_name_resolver.py |
| **责任链模式** | 错误处理 | core/error_handling/error_handlers.py |
| **组合优于继承** | 连接上下文 | state/connection_context.py |
| **鸭子类型** | Protocol 接口 | core/interfaces/ |

## 🔌 Protocol 接口系统（2026-01-03 新增）

### 为什么使用 Protocol？

PTK_REPL 使用 **Protocol 接口**（而非 ABC）来支持鸭子类型和依赖注入：

**鸭子类型优势**：
- ✅ 无需显式继承，减少耦合
- ✅ 支持第三方实现
- ✅ 依赖注入友好
- ✅ 运行时类型检查（`@runtime_checkable`）

**Protocol vs ABC**：
```python
# ❌ ABC（需要显式继承）
from abc import ABC, abstractmethod

class ICliContext(ABC):
    @abstractmethod
    def poutput(self, text: str) -> None: ...

class MyCLI(ICliContext):  # 必须显式继承
    pass

# ✅ Protocol（鸭子类型，推荐）
from typing import Protocol

@runtime_checkable
class ICliContext(Protocol):
    def poutput(self, text: str) -> None: ...

class MyCLI:  # 无需显式继承
    def poutput(self, text: str) -> None:
        print(text)
```

### 7个核心 Protocol 接口

#### 1. ICliContext - CLI 上下文接口

**文件**: `core/interfaces/cli_context.py`

**用途**: 统一的 CLI 上下文接口，支持输出和状态管理

**方法**:
- `poutput(text: str) -> None` - 输出普通消息
- `perror(text: str) -> None` - 输出错误消息

**属性**:
- `state: StateManager` - 状态管理器
- `registry: CommandRegistry` - 命令注册表

**实现**: `PromptToolkitCLI`

**使用场景**: `typed_command` 装饰器中使用

---

#### 2. IModuleLoader - 模块加载器接口

**文件**: `core/interfaces/module_loader.py`

**用途**: 统一的模块加载接口，支持懒加载和即时加载

**方法**:
- `load(module_name: str) -> CommandModule | None` - 加载模块
- `is_loaded(module_name: str) -> bool` - 检查是否已加载
- `ensure_module_loaded(module_name: str) -> None` - 确保模块已加载

**属性**:
- `loaded_modules: dict[str, CommandModule]` - 已加载的模块
- `lazy_modules: dict[str, type]` - 懒加载模块

**实现**: `UnifiedModuleLoader`, `ModuleLifecycleManager`

**设计模式**: 门面模式（ModuleLifecycleManager）

---

#### 3. IModuleRegister - 模块注册器接口

**文件**: `core/interfaces/module_register.py`

**用途**: 统一的模块注册接口

**方法**:
- `register(module: CommandModule) -> None` - 注册模块
- `is_registered(module_name: str) -> bool` - 检查是否已注册
- `get_module(module_name: str) -> CommandModule | None` - 获取模块

**实现**: `ModuleRegister`

---

#### 4. IModuleDiscoverer - 模块发现器接口

**文件**: `core/interfaces/module_discoverer.py`

**用途**: 模块自动发现接口

**方法**:
- `discover_modules() -> list[str]` - 发现所有模块
- `preload_all(tracker, resolver, exclude) -> None` - 预加载所有模块

**实现**: `ModuleDiscoveryService`

---

#### 5. ICommandResolver - 命令解析器接口

**文件**: `core/interfaces/command_resolver.py`

**用途**: 命令名称解析接口

**方法**:
- `resolve(module_name: str) -> str` - 解析模块类名

**实现**: `DefaultModuleNameResolver`, `ConfigurableResolver`

**设计模式**: 策略模式

---

#### 6. IPromptProvider - 提示符提供者接口

**文件**: `core/interfaces/prompt_provider.py`

**用途**: 统一的提示符提供接口

**方法**:
- `get_prompt() -> str` - 获取提示符

**实现**: `PromptProvider`

---

#### 7. IRegistry - 命令注册表接口

**文件**: `core/interfaces/registry.py`

**用途**: 命令注册表接口

**方法**:
- `register_command(...) -> None` - 注册命令
- `get_command_info(command_path: str) -> tuple | None` - 获取命令信息
- `get_module(module_name: str) -> CommandModule | None` - 获取模块

**实现**: `CommandRegistry`

---

## 🏗️ 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│              (PromptSession + prompt-toolkit)               │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   PromptToolkitCLI                          │
│  ┌───────────────┬─────────────────┬───────────────────┐  │
│  │ Command       │ StateManager    │ ConfigManager     │  │
│  │ Registry      │                 │                   │  │
│  └───────┬───────┴────────┬────────┴��──────────┬───────┘  │
└──────────┼────────────────┼──────────────────────┼─────────┘
           │                │                      │
    ┌──────▼────────┐  ┌───▼────────────┐   ┌─────▼───────┐
    │ AutoCompleter│  │GlobalState     │   │ YAML Config │
    └───────────────┘  └────────────────┘   └─────────────┘
                              │
                    ┌─────────┴──────────┐
                    │ ModuleState        │
                    │ (per module)       │
                    └────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       模块层                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────────────┐             │
│  │  Core   │  │  SSH    │  │   Database      │             │
│  │ Module  │  │ Module  │  │   Module        │             │
│  └─────────┘  └─────────┘  └─────────────────┘             │
│                                                               │
│  CommandModule (base class)                                  │
│  ├─ name: str                                                │
│  ├─ description: str                                         │
│  ├─ aliases: list[str]                                       │
│  ├─ version: str                                             │
│  ├─ register_commands(cli)                                  │
│  ├─ initialize(state_manager)                               │
│  └─ shutdown()                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📦 模块加载系统（2026-01-03 重构）

### 设计目标

将旧的 ModuleLoader（183行）拆分为 4 个职责单一的组件，符合**单一职责原则**。

### 四层架构

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
        └─��────────────────┼──────────────────┘
                           ↓
                  ┌───────────────┐
                  │    Tracker     │
                  │  (追踪状态)     │
                  └───────────────┘
```

### 四个核心组件

#### 1. LazyModuleTracker - 懒加载追踪器

**文件**: `core/loaders/lazy_module_tracker.py`

**职责**:
- 追踪哪些模块已加载、哪些模块待加载
- 追踪模块别名信息（O(1) 查找）

**数据结构**:
```python
_lazy_modules: dict[str, type]      # 模块名 -> 模块类
_loaded_modules: set[str]            # 已加载模块集合
_alias_to_module: dict[str, str]     # 别名 -> 模块名
```

**关键方法**:
- `add_lazy_module(name, cls)` - 添加懒加载模块
- `mark_as_loaded(name)` - 标记为已加载
- `is_loaded(name) -> bool` - 检查是否已加载
- `find_by_alias(alias) -> str | None` - 通过别名查找（O(1)）

---

#### 2. ModuleDiscoveryService - 自动发现服务

**文件**: `core/loaders/module_discovery_service.py`

**职责**:
- 自动扫描 `modules/` 目录
- 发现所有可用模块
- 预加载到懒加载追踪器

**关键方法**:
- `discover_modules() -> list[str]` - 发现所有模块
- `preload_all(tracker, resolver, exclude)` - 预加载所有模块

---

#### 3. UnifiedModuleLoader - 统一模块加载器

**文件**: `core/loaders/unified_module_loader.py`

**职责**:
- 加载模块实例
- 支持懒加载和即时加载
- 调用注册器和回调

**关键方法**:
- `load(module_name) -> CommandModule | None` - 加载模块
- `is_loaded(name) -> bool` - 检查是否已加载
- `ensure_module_loaded(name)` - 确保已加载

**工作流程**:
```
1. 检查是否已加载
2. 从懒加载列表获取模块类
3. 动态导入模块（如需要）
4. 创建模块实例
5. 注册到注册表
6. 标记为已加载
7. 执行加载后回调
```

---

#### 4. ModuleRegister - 模块注册器

**文件**: `core/loaders/module_register.py`

**职责**:
- 注册模块到注册表
- 调用模块初始化方法
- 错误清理

**关键方法**:
- `register(module)` - 注册模块
- `is_registered(name) -> bool` - 检查是否已注册
- `get_module(name) -> CommandModule | None` - 获取模块

---

### 5. ModuleLifecycleManager - 生命周期管理器（门面）

**文件**: `core/loaders/module_lifecycle_manager.py`

**职责**:
- 协调发现、加载、注册等组件
- 提供统一的模块管理接口
- 实现 IModuleLoader 接口

**关键方法**:
- `load_modules()` - 加载所有模块（主入口）
- `load_module_immediately(name)` - 立即加载模块

**设计模式**: **门面模式**（Facade Pattern）

---

### 性能优化

**别名查找优化**: O(n) → O(1)
```python
# 旧实现（O(n)）
for name, module in _lazy_modules.items():
    if name == alias or module.aliases == alias:
        return name

# 新实现（O(1)）
return self._alias_to_module.get(alias)
```

---

## ⚡ 错误处理系统（2026-01-03 新增）

### 设计目标

使用**责任链模式**处理异常，支持分层错误处理。

### 责任链架构

```
┌─────────────────────────────────────────────────────────────┐
│              ErrorHandlerChain (责任链)                      │
│                                                           │
│    ┌──────────────────────┐    ┌──────────────────────┐    │
│    │  CLIErrorHandler      │───→│  BaseErrorHandler     │    │
│    │  (处理 CLIException)  │    │  (兜底处理其他异常)    │    │
│    └──────────────────────┘    └──────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### CLIException 层次结构

```
CLIException (基类)
    ├─ CommandException
    │   ├─ CommandNotFoundError
    │   └─ InvalidArgumentError
    └─ ModuleException
        ├─ ModuleNotFoundError
        └─ ModuleLoadError
```

### 错误处理器

#### 1. CLIErrorHandler

**文件**: `core/error_handling/error_handlers.py`

**职责**: 处理所有 `CLIException` 异常

**处理流程**:
1. 检查异常类型
2. 提取错误详情
3. 格式化错误消息
4. 输出到 stderr

---

#### 2. BaseErrorHandler

**文件**: `core/error_handling/error_handlers.py`

**职责**: 兜底处理所有其他异常

**处理流程**:
1. 捕获非 CLIException 异常
2. 记录堆栈跟踪
3. 输出友好的错误消息

---

### 使用示例

```python
# 1. 定义模块专用异常
class SSHException(CLIException):
    """SSH 模块异常基类"""
    pass

class SSHConnectionError(SSHException):
    """SSH 连接错误"""
    pass

# 2. 在命令中抛出异常
def do_connect(self, args):
    if not self._connect():
        raise SSHConnectionError("无法连接到服务器")

# 3. 错误处理链自动处理
# ErrorHandlerChain 会捕获并显示友好的错误消息
```

---

## 🔐 连接上下文抽象（2026-01-03 新增）

### 设计目标

使用**组合替代继承**，通过多态方法替代 `isinstance` 检查，符合**开闭原则**。

### 问题：旧实现（违反 OCP）

```python
# ❌ 旧实现：使用 isinstance 检查
def get_prompt_suffix(self) -> str:
    gs = self.state.global_state

    if isinstance(gs.current_connection, SSHConnection):
        return f"@{gs.current_connection.host}"
    elif isinstance(gs.current_connection, DatabaseConnection):
        return f"[{gs.current_connection.database}]"
    else:
        return ""

# 问题：每次添加新连接类型都需要修改这里！
```

### 解决方案：新实现（符合 OCP）

```python
# ✅ 新实现：使用多态方法
class ConnectionContext(ABC):
    @abstractmethod
    def get_prompt_suffix(self) -> str:
        """返回提示符后缀（多态方法）"""
        pass

class SSHConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"@{self.host}"

class DatabaseConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"[{self.database}]"

# 在 GlobalState 中使用组合
class GlobalState(BaseModel):
    ssh_context: SSHConnectionContext | None = None
    db_context: DatabaseConnectionContext | None = None

    def get_active_context(self) -> ConnectionContext | None:
        # 返回当前活跃的连接上下文
        if self.ssh_context and self.ssh_context.is_connected:
            return self.ssh_context
        elif self.db_context and self.db_context.is_connected:
            return self.db_context
        return None

    def get_prompt_suffix(self) -> str:
        ctx = self.get_active_context()
        return ctx.get_prompt_suffix() if ctx else ""

# 优势：添加新连接类型无需修改 GlobalState！
```

### 设计模式：组合优于继承

**旧设计**（继承）:
```python
class GlobalState:
    current_connection: Connection  # 单一连接

# 问题：只能管理一个连接，切换连接会丢失状态
```

**新设计**（组合）:
```python
class GlobalState:
    ssh_context: SSHConnectionContext
    db_context: DatabaseConnectionContext
    # ... 可以添加更多连接上下文

# 优势：同时管理多个连接，状态独立
```

---

## 🧩 核心组件

### 1. PromptToolkitCLI (主控制器)

**文件**: [`src/ptk_repl/cli.py`](../src/ptk_repl/cli.py)

**职责**：
- 初始化和管理所有核心组件
- 处理用户输入和命令分发
- 管理模块生命周期（懒加载/卸载）
- 协调命令注册表和状态管理器

**关键方法**：
- `default_prompt()` - 动态生成提示符
- `_load_modules()` - 模块加载管理
- `register_command()` - 命令注册接口
- `cmdloop()` - 主命令循环

### 2. CommandRegistry (命令注册表)

**文件**: [`src/ptk_repl/core/registry.py`](../src/ptk_repl/core/registry.py)

**职责**：
- 管理所有模块和命令的注册
- 命令别名解析
- 模块发现和加载

**数据结构**：
```python
self._modules: dict[str, CommandModule]  # 模块名 -> 模块实例
self._command_map: dict[str, tuple]       # 命令 -> (模块, 命令, 处理器)
self._alias_map: dict[str, str]           # 别名 -> 完整命令
```

### 3. StateManager (状态管理器)

**文件**: [`src/ptk_repl/core/state_manager.py`](../src/ptk_repl/core/state_manager.py)

**职责**：
- 管理全局状态（跨模块共享）
- 管理模块状态（模块隔离）
- 状态持久化

**状态层次**：
```
StateManager
├── global_state: GlobalState        # 所有模块共享
│   ├── connected: bool
│   ├── current_host: str | None
│   ├── current_port: int | None
│   └── ...
└── module_states: dict[str, ModuleState]  # 每个模块独立
    ├── ssh: SSHState
    │   ├── connections: dict
    │   └── active_environments: list
    └── database: DatabaseState
        ├── active_database: str | None
        └── query_history: list
```

### 4. AutoCompleter (自动补全器)

**文件**: [`src/ptk_repl/core/completer.py`](../src/ptk_repl/core/completer.py)

**职责**：
- 从 CommandRegistry 自动发现命令
- 实时智能补全
- 参数补全（基于 Pydantic 模型）
- 懒加载模块的预声明补全

**补全层次**：
```
Top Level:          (空输入)
├── Core Commands:   status, modules, exit, help
├── Modules:         ssh, db, database
└── Aliases:         db (database 的短别名)

Module Level:        (ssh + 空格)
├── Sub Commands:    connect, log, disconnect
└── Parameters:      --host, --port, --lines
```

### 5. typed_command 装饰器

**文件**: [`src/ptk_repl/core/decorators.py`](../src/ptk_repl/core/decorators.py)

**职责**：
- 基于Pydantic v2的参数验证
- 参数解析（支持长短选项）
- 自动错误处理

**工作流程**：
```python
# 用户输入
database connect localhost --port 5432

# 解析为字典
{"host": "localhost", "port": 5432}

# Pydantic 验证
ConnectArgs(host="localhost", port=5432)

# 调用处理函数
do_connect(ConnectArgs(...))
```

## 🔄 命令执行流程

```
用户输入: "ssh connect 小米"
    │
    ├─→ PromptToolkitCLI.default()
    │
    ├─→ _parse_input()  # 分词
    │   ["ssh", "connect", "小米"]
    │
    ├─→ CommandRegistry.get_command_info()  # 查找命令
    │   │
    │   ├─ 检查: "ssh connect" 是否在 _command_map 中?
    │   ├─ 否 → 检查: "ssh" 是否是模块?
    │   └─ 是 → _ensure_module_loaded("ssh")  # 懒加载
    │
    ├─→ 找到命令处理器
    │   SSHModule.do_connect(args="小米")
    │
    ├─→ 参数验证 (如果使用 typed_command)
    │   解析参数 → Pydantic 验证 → 传递验证后的对象
    │
    └─→ 执行业务逻辑
        连接到 SSH 环境 "小米"
        更新 GlobalState (connected=True, host=...)
        更新 SSHState (connections["小米"] = ...)
```

## 🎯 模块接口

### CommandModule 基类

**文件**: [`src/ptk_repl/core/base.py`](../src/ptk_repl/core/base.py)

**必须实现**：
```python
@property
def name(self) -> str:
    """模块唯一标识符"""
    pass

@property
def description(self) -> str:
    """模块描述"""
    pass

def register_commands(self, cli: PromptToolkitCLI) -> None:
    """注册命令到 CLI"""
    pass
```

**可选实现**：
```python
@property
def aliases(self) -> list[str]:
    """模块别名列表"""
    return ["short_name"]

@property
def version(self) -> str:
    """模块版本"""
    return "1.0.0"

def initialize(self, state_manager: StateManager) -> None:
    """模块初始化回调"""
    # 获取模块状态
    self.state = state_manager.get_module_state(
        self.name, MyModuleState
    )

def shutdown(self) -> None:
    """模块关闭回调"""
    # 清理资源
    pass
```

## 📊 数据流

### 配置加载流程

```
ptk_repl_config.yaml
    │
    ├─→ ConfigManager.load()
    │   │
    │   ├─ 解析 YAML
    │   ├─ 验证配置
    │   └─ 存储到内部字典
    │
    ├─→ core.preload_modules
    │   ["ssh", "database"]
    │   │
    │   └─→ _load_module_immediately(module_name)
    │       ├─ 动态导入模块
    │       ├─ 创建模块实例
    │       ├─ module.register_commands(cli)
    │       └─ module.initialize(state_manager)
    │
    └─→ modules.*.environments
        SSH 环境配置
        │
        └─→ SSHModule 使用配置
            connect(环境名)
            查找环境 → 连接 SSH
```

### 状态管理流程

```
┌─ 全局状态 (跨模块)
│  GlobalState
│  ├─ connected: bool          # SSH/DB 是否连接
│  ├─ current_host: str        # 当前主机
│  └─ connection_type: str     # "ssh" | "database"
│
└─ 模块状态 (隔离)
   SSHState
   ├─ connections: dict       # SSH 连接池
   ├─ active_environments: list
   └─ connection_history: list

   DatabaseState
   ├─ active_database: str
   ├─ connection_pool_size: int
   └─ query_history: list
```

## 🔐 类型安全

### Pydantic v2 集成

**1. 参数模型定义**：
```python
from pydantic import BaseModel, Field

class ConnectArgs(BaseModel):
    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535)
    ssl: bool = Field(default=False)
```

**2. 装饰器使用**：
```python
@typed_command(ConnectArgs)
def do_connect(self, args: ConnectArgs) -> None:
    # args 已经是验证后的 ConnectArgs 对象
    print(f"连接到 {args.host}:{args.port}")
```

**3. 类型检查**：
- 运行时：Pydantic 自动验证和转换
- 静态时：mypy 类型检查通过 `TypedDict` 和类型注解

## 🚀 懒加载机制

### 工作原理

1. **模块发现** (`_discover_all_modules()`)：
   - 扫描 `ptk_repl/modules/` 目录
   - 注册所有模块类到 `_lazy_modules`

2. **按需加载** (`_ensure_module_loaded()`)：
   - 用户输入模块名时触发
   - 动态导入模块
   - 调用 `register_commands()` 注册命令

3. **预加载配置**：
   ```yaml
   core:
     preload_modules:
       - core          # 立即加载
       - ssh           # 启动时加载
       - database      # 启动时加载
   ```

### 性能优势

- **启动时间**：只加载 core 模块，启动快
- **内存占用**：未使用的模块不加载
- **灵活性**：可以添加无限多模块而不影响启动

## 📐 设计模式

### 1. 注册表模式 (Registry Pattern)

**实现**: [`CommandRegistry`](../src/ptk_repl/core/registry.py)

- 模块注册
- 命令注册
- 别名解析

### 2. 策略模式 (Strategy Pattern)

**实现**: [`CommandModule`](../src/ptk_repl/core/base.py)

- 每个模块实现相同的接口
- 不同的命令实现策略

### 3. 观察者模式 (Observer Pattern)

**实现**: [`StateManager`](../src/ptk_repl/core/state_manager.py)

- 全局状态变化通知所有模块
- 模块状态独立管理

### 4. 装饰器模式 (Decorator Pattern)

**实现**: [`typed_command`](../src/ptk_repl/core/decorators.py)

- 参数验证
- 错误处理
- 函数包装

## 🔌 扩展点

### 添加新模块

1. 继承 `CommandModule`
2. 实现 `register_commands()`
3. （可选）实现 `initialize()` 和 `shutdown()`
4. 无需修改框架代码

### 自定义补全

1. 实现 `AutoCompleter` 子类
2. 重写 `build_completion_dict()`
3. 使用 `cli.registry.set_completer()`

### 自定义状态

1. 继承 `ModuleState`
2. 使用 `Field()` 定义字段
3. 在 `initialize()` 中注册

## 📚 相关文档

- [模块开发教程](guides/module-development.md)
- [API 参考](implementation/api-reference.md)
- [配置指南](guides/configuration.md)

---

**最后更新**: 2025-12-28
