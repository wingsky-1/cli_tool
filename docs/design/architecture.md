# PTK_REPL 架构设计

本文档详细描述 PTK_REPL 的架构设计原则和核心组件。

## 📐 架构概览

PTK_REPL 采用**模块化**、**类型安全**和**配置驱动**的设计理念。

### 核心设计原则

1. **模块化优先** - 所有功能以模块形式组织，模块间完全解耦
2. **类型安全** - 基于 Pydantic v2 的运行时类型验证
3. **懒加载** - 按需加载模块，最小化启动开销
4. **双层状态** - 全局状态 + 模块隔离状态
5. **自动发现** - 模块自动注册，零配置添加新功能

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
