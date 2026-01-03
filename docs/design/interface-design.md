# Protocol 接口设计

本文档详细描述 PTK_REPL 的 Protocol 接口系统，包括设计理念、核心接口、使用示例和最佳实践。

## 🎯 设计概览

### 为什么使用 Protocol？

PTK_REPL 使用 **Protocol 接口**（而非 ABC）来支持鸭子类型和依赖注入。

**核心优势**：
- ✅ **鸭子类型**：无需显式继承，减少耦合
- ✅ **第三方友好**：第三方实现无需修改框架代码
- ✅ **依赖注入**：支持灵活的依赖注入
- ✅ **运行时检查**：`@runtime_checkable` 支持 `isinstance()` 检查
- ✅ **类型安全**：完整的静态类型检查支持

### Protocol vs ABC

| 特性 | Protocol（推荐） | ABC（不推荐） |
|------|-----------------|--------------|
| **鸭子类型** | ✅ 支持 | ❌ 需要显式继承 |
| **第三方扩展** | ✅ 无缝集成 | ❌ 必须继承 |
| **耦合度** | ✅ 低耦合 | ❌ 高耦合 |
| **类型检查** | ✅ 完整支持 | ✅ 完整支持 |
| **运行时检查** | ✅ `@runtime_checkable` | ✅ `isinstance()` |

**示例对比**：

```python
# ✅ Protocol（推荐）
from typing import Protocol

@runtime_checkable
class ICliContext(Protocol):
    def poutput(self, text: str) -> None: ...

# 任何符合接口的类都可以
class MyCLI:
    def poutput(self, text: str) -> None:
        print(text)

# 类型检查通过
cli: ICliContext = MyCLI()  # ✅

# ❌ ABC（不推荐）
from abc import ABC, abstractmethod

class ICliContext(ABC):
    @abstractmethod
    def poutput(self, text: str) -> None: ...

# 必须显式继承
class MyCLI(ICliContext):  # ⚠️ 强制继承
    def poutput(self, text: str) -> None:
        print(text)

# 第三方实现无法通过类型检查
class ThirdPartyCLI:  # ❌ 未继承，类型检查失败
    def poutput(self, text: str) -> None:
        print(text)
```

---

## 📦 7 个核心 Protocol 接口

PTK_REPL 定义了 7 个核心 Protocol 接口，覆盖 CLI、模块加载、命令执行等功能域。

### 接口层次结构

```
Protocol 接口系统
│
├─ CLI 上下文接口
│   └─ ICliContext - CLI 上下文（输出、状态）
│
├─ 模块加载接口
│   ├─ IModuleLoader - 模块加载器
│   ├─ IModuleRegister - 模块注册器
│   └─ IModuleDiscoverer - 模块发现器
│
├─ 命令相关接口
│   ├─ ICommandResolver - 命令名称解析器
│   ├─ IPromptProvider - 提示符提供者
│   └─ IRegistry - 命令注册表
```

---

## 🔌 接口详解

### 1. ICliContext - CLI 上下文接口

**文件**: [`src/ptk_repl/core/interfaces/cli_context.py`](../../src/ptk_repl/core/interfaces/cli_context.py)

**用途**: 统一的 CLI 上下文接口，提供输出和状态管理接口。

**接口定义**：
```python
from typing import Protocol

@runtime_checkable
class ICliContext(Protocol):
    """CLI 上下文接口。

    提供统一的输出和状态管理接口，支持鸭子类型。
    """

    def poutput(self, text: str) -> None:
        """输出普通消息。

        Args:
            text: 要输出的消息
        """
        ...

    def perror(self, text: str) -> None:
        """输出错误消息。

        Args:
            text: 错误消息
        """
        ...

    @property
    def state(self) -> StateManager:  # type: ignore[name-defined]
        """状态管理器。"""
        ...

    @property
    def registry(self) -> "IRegistry":  # type: ignore[name-defined]
        """命令注册表。"""
        ...
```

**实现类**：
- `PromptToolkitCLI`

**使用场景**：
- `typed_command` 装饰器中用于类型注解
- 依赖注入到需要 CLI 功能的组件

**使用示例**：
```python
from ptk_repl.core.interfaces import ICliContext

def process_command(cli: ICliContext, command: str) -> None:
    """处理命令（支持任何 ICliContext 实现）。"""
    cli.poutput(f"执行命令: {command}")

# 可以传入任何符合接口的对象
process_command(MyCLI(), "status")
process_command(ThirdPartyCLI(), "status")
```

---

### 2. IModuleLoader - 模块加载器接口

**文件**: [`src/ptk_repl/core/interfaces/module_loader.py`](../../src/ptk_repl/core/interfaces/module_loader.py)

**用途**: 统一的模块加载接口，支持懒加载和即时加载。

**接口定义**：
```python
@runtime_checkable
class IModuleLoader(Protocol):
    """模块加载器接口。

    支持懒加载和即时加载，使用鸭子类型。
    """

    def load(self, module_name: str) -> CommandModule | None:
        """加载模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果加载失败返回 None
        """
        ...

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载。

        Args:
            module_name: 模块名称

        Returns:
            是否已加载
        """
        ...

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载（懒加载）。

        Args:
            module_name: 模块名称
        """
        ...

    @property
    def loaded_modules(self) -> dict[str, CommandModule]:
        """已加载的模块字典。"""
        ...

    @property
    def lazy_modules(self) -> dict[str, type]:
        """懒加载模块字典。"""
        ...
```

**实现类**：
- `UnifiedModuleLoader`
- `ModuleLifecycleManager`（门面模式）

**设计模式**: 门面模式（ModuleLifecycleManager）

**使用示例**：
```python
from ptk_repl.core.interfaces import IModuleLoader

def load_all_modules(loader: IModuleLoader) -> None:
    """加载所有模块（支持任何 IModuleLoader 实现）。"""
    for module_name in ["ssh", "database", "redis"]:
        if not loader.is_loaded(module_name):
            loader.ensure_module_loaded(module_name)
```

---

### 3. IModuleRegister - 模块注册器接口

**文件**: [`src/ptk_repl/core/interfaces/module_register.py`](../../src/ptk_repl/core/interfaces/module_register.py)

**用途**: 统一的模块注册接口。

**接口定义**：
```python
@runtime_checkable
class IModuleRegister(Protocol):
    """模块注册器接口。"""

    def register(self, module: CommandModule) -> None:
        """注册模块。

        Args:
            module: 模块实例
        """
        ...

    def is_registered(self, module_name: str) -> bool:
        """检查模块是否已注册。

        Args:
            module_name: 模块名称

        Returns:
            是否已注册
        """
        ...

    def get_module(self, module_name: str) -> CommandModule | None:
        """获取已注册的模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果不存在返回 None
        """
        ...
```

**实现类**：
- `ModuleRegister`

---

### 4. IModuleDiscoverer - 模块发现器接口

**文件**: [`src/ptk_repl/core/interfaces/module_discoverer.py`](../../src/ptk_repl/core/interfaces/module_discoverer.py)

**用途**: 模块自动发现接口。

**接口定义**：
```python
@runtime_checkable
class IModuleDiscoverer(Protocol):
    """模块发现器接口。"""

    def discover_modules(self) -> list[str]:
        """发现所有可用模块。

        Returns:
            模块名称列表
        """
        ...

    def preload_all(
        self,
        tracker: "LazyModuleTracker",  # type: ignore[name-defined]
        resolver: "IModuleNameResolver",  # type: ignore[name-defined]
        exclude: list[str]
    ) -> None:
        """预加载所有模块到追踪器。

        Args:
            tracker: 懒加载追踪器
            resolver: 名称解析器
            exclude: 要排除的模块列表
        """
        ...
```

**实现类**：
- `ModuleDiscoveryService`

---

### 5. ICommandResolver - 命令解析器接口

**文件**: [`src/ptk_repl/core/interfaces/command_resolver.py`](../../src/ptk_repl/core/interfaces/command_resolver.py)

**用途**: 命令名称解析接口。

**接口定义**：
```python
@runtime_checkable
class ICommandResolver(Protocol):
    """命令名称解析器接口。"""

    def resolve(self, module_name: str) -> str:
        """解析模块名称为类名。

        Args:
            module_name: 模块名称

        Returns:
            类名
        """
        ...
```

**实现类**：
- `DefaultModuleNameResolver` - 默认解析策略
- `ConfigurableResolver` - 可配置解析策略

**设计模式**: 策略模式

**使用示例**：
```python
from ptk_repl.core.resolvers import DefaultModuleNameResolver, ConfigurableResolver

# 默认解析：ssh -> SSHModule
resolver = DefaultModuleNameResolver()
class_name = resolver.resolve("ssh")  # 返回: "SSHModule"

# 可配置解析：db -> DatabaseModule
resolver = ConfigurableResolver({
    "db": "DatabaseModule",
    "redis": "RedisModule"
})
class_name = resolver.resolve("db")  # 返回: "DatabaseModule"
```

---

### 6. IPromptProvider - 提示符提供者接口

**文件**: [`src/ptk_repl/core/interfaces/prompt_provider.py`](../../src/ptk_repl/core/interfaces/prompt_provider.py)

**用途**: 统一的提示符提供接口。

**接口定义**：
```python
@runtime_checkable
class IPromptProvider(Protocol):
    """提示符提供者接口。"""

    def get_prompt(self) -> str:
        """获取提示符字符串。

        Returns:
            提示符字符串
        """
        ...
```

**实现类**：
- `PromptProvider`

---

### 7. IRegistry - 命令注册表接口

**文件**: [`src/ptk_repl/core/interfaces/registry.py`](../../src/ptk_repl/core/interfaces/registry.py)

**用途**: 命令注册表接口。

**接口定义**：
```python
@runtime_checkable
class IRegistry(Protocol):
    """命令注册表接口。"""

    def register_command(
        self,
        module_name: str,
        command_name: str,
        handler: Callable,
        aliases: list[str] | None
    ) -> None:
        """注册命令。

        Args:
            module_name: 模块名称
            command_name: 命令名称
            handler: 命令处理函数
            aliases: 命令别名
        """
        ...

    def get_command_info(self, command_path: str) -> tuple | None:
        """获取命令信息。

        Args:
            command_path: 命令路径（如 "ssh connect"）

        Returns:
            (模块名, 命令名, 处理器) 元组，如果不存在返回 None
        """
        ...

    def get_module(self, module_name: str) -> CommandModule | None:
        """获取模块。

        Args:
            module_name: 模块名称

        Returns:
            模块实例，如果不存在返回 None
        """
        ...
```

**实现类**：
- `CommandRegistry`

---

## 💡 接口使用示例

### 在 typed_command 中使用 ICliContext

`typed_command` 装饰器使用 `ICliContext` 接口进行类型注解：

```python
from ptk_repl.core.interfaces import ICliContext
from ptk_repl.core.decoration.typed_command import typed_command

@typed_command(ConnectArgs)
def do_connect(self: Any, args: ConnectArgs) -> None:
    """连接到服务器。

    注意：这里的 self 不是 CommandModule，而是 cli 对象。
    """
    # 使用 Protocol 接口类型注解
    cli: ICliContext = self

    # 调用接口方法
    if args.port < 1 or args.port > 65535:
        cli.perror(f"端口号无效: {args.port}")
        return

    # 访问接口属性
    global_state = cli.state.global_state
    global_state.connected = True

    cli.poutput(f"已连接到 {args.host}:{args.port}")
```

**优势**：
- ✅ 支持任何 `ICliContext` 实现
- ✅ 类型安全（mypy 检查通过）
- ✅ 鸭子类型（无需显式继承）

### 在 CommandExecutor 中使用接口

`CommandExecutor` 使用多个 Protocol 接口：

```python
from ptk_repl.core.interfaces import (
    IModuleLoader,
    IRegistry,
    ICliContext
)

class CommandExecutor:
    """命令执行器。"""

    def __init__(
        self,
        module_loader: IModuleLoader,  # Protocol 接口
        registry: IRegistry,            # Protocol 接口
        cli: ICliContext                # Protocol 接口
    ) -> None:
        """初始化命令执行器。

        Args:
            module_loader: 模块加载器（任何 IModuleLoader 实现）
            registry: 命令注册表（任何 IRegistry 实现）
            cli: CLI 上下文（任何 ICliContext 实现）
        """
        self._module_loader = module_loader
        self._registry = registry
        self._cli = cli

    def execute(self, command_path: str, args: list[str]) -> None:
        """执行命令。"""
        # 使用接口方法
        command_info = self._registry.get_command_info(command_path)
        if not command_info:
            self._cli.perror(f"命令未找到: {command_path}")
            return

        module_name, command_name, handler = command_info

        # 确保模块已加载
        self._module_loader.ensure_module_loaded(module_name)

        # 执行命令
        handler(args)
```

**优势**：
- ✅ 依赖注入：可以注入任何实现
- ✅ 易于测试：可以注入 Mock 实现
- ✅ 低耦合：高层依赖接口而非具体实现

---

## 📐 接口设计原则

### 1. 接口隔离原则（ISP）

**规则**：每个接口只包含相关的方法，避免臃肿的"万能接口"。

**示例**：

```python
# ✅ 好的设计（接口隔离）
@runtime_checkable
class IModuleLoader(Protocol):
    def load(self, name: str) -> CommandModule | None: ...
    def is_loaded(self, name: str) -> bool: ...

@runtime_checkable
class IModuleRegister(Protocol):
    def register(self, module: CommandModule) -> None: ...
    def is_registered(self, name: str) -> bool: ...

# ❌ 不好的设计（臃肿的接口）
@runtime_checkable
class IModuleManager(Protocol):
    def load(self, name: str) -> CommandModule | None: ...
    def register(self, module: CommandModule) -> None: ...
    def discover(self) -> list[str]: ...
    def resolve(self, name: str) -> str: ...
```

### 2. 单一职责原则（SRP）

**规则**：每个接口只负责一个功能域。

**示例**：
- `ICliContext` - CLI 上下文（输出、状态）
- `IModuleLoader` - 模块加载
- `ICommandResolver` - 命令名称解析

### 3. 依赖倒置原则（DIP）

**规则**：高层依赖接口而非具体实现。

**示例**：
```python
# ✅ 好的设计（依赖接口）
class CommandExecutor:
    def __init__(self, loader: IModuleLoader) -> None:
        self._loader = loader  # 依赖接口

# ❌ 不好的设计（依赖具体实现）
class CommandExecutor:
    def __init__(self, loader: UnifiedModuleLoader) -> None:
        self._loader = loader  # 依赖具体类
```

---

## 🎯 何时定义新接口？

### 使用场景

**✅ 应该定义新接口**：
1. 有多个可能的实现类
2. 需要依赖注入
3. 第三方扩展
4. 需要运行时类型检查

**❌ 不应该定义新接口**：
1. 只有一个实现类
2. 不需要第三方扩展
3. 使用具体类更简单

### 决策流程

```
是否有多个实现类？
    │
    ├─ 是 → 定义 Protocol 接口 ✅
    │
    └─ 否 → 是否需要第三方扩展？
              │
              ├─ 是 → 定义 Protocol 接口 ✅
              │
              └─ 否 → 是否需要依赖注入？
                        │
                        ├─ 是 → 定义 Protocol 接口 ✅
                        │
                        └─ 否 → 使用具体类 ❌
```

**示例**：

```python
# ✅ 需要定义接口（多个实现）
@runtime_checkable
class IModuleNameResolver(Protocol):
    def resolve(self, name: str) -> str: ...

# 实现 1: 默认解析
class DefaultModuleNameResolver: ...

# 实现 2: 可配置解析
class ConfigurableResolver: ...

# 实现 3: 第三方自定义
class CustomResolver: ...

# ❌ 不需要定义接口（只有一个实现）
class ConnectionHelper:  # 直接使用具体类
    def connect(self, host: str, port: int) -> None: ...
```

---

## 🛠️ 接口演进路线图

### 当前版本（v0.2.0）

**已实现的接口**：
- ✅ 7 个核心 Protocol 接口
- ✅ 所有接口使用 `@runtime_checkable`
- ✅ 完整的类型注解

### 未来版本（v0.3.0+）

**计划添加的接口**：
- 🔜 `IConfigProvider` - 配置提供者接口
- 🔜 `IStateProvider` - 状态提供者接口
- 🔜 `ICompletionProvider` - 补全提供者接口
- 🔜 `IErrorHandler` - 错误处理接口

**演进方向**：
- 更多的功能域接口
- 更细粒度的接口拆分
- 更完善的类型注解

---

## 📚 相关文档

- [架构设计](architecture.md) - 系统架构和核心组件
- [API 参考](../implementation/api-reference.md) - 完整 API 文档
- [开发指南](../development/development.md) - Protocol 接口使用规范

---

**最后更新**: 2026-01-03
