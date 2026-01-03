# 开发指南

本文档描述 PTK_REPL 项目的开发环境搭建、代码规范和开发流程。

## 🛠️ 开发环境

### 系统要求

- Python 3.12+
- uv (推荐) 或 pip
- Git
- Pre-commit hooks (可选但推荐)

### 环境搭建

```bash
# 1. 克隆仓库
git clone <repository-url>
cd cli_tool

# 2. 安装 uv (推荐)
pip install uv

# 3. 安装依赖
uv sync

# 4. 安装 pre-commit hooks (可选)
uv run pre-commit install
```

### 项目结构

**核心目录组织（2026-01-03 重构）**：

```
src/ptk_repl/
├── cli.py                          # CLI 入口
├── core/                           # 核心框架（按功能域分类，15个子包）
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
│   ├── decoration/                 # 装饰器
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
│   │   ├── module_discoverer.py    # IModuleDiscoverer
│   │   ├── command_resolver.py     # ICommandResolver
│   │   ├── prompt_provider.py      # IPromptProvider
│   │   └── registry.py             # IRegistry
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

**15个子包职责说明**：

| 子包 | 职责 | 关键组件 |
|------|------|----------|
| `base/` | 基类和抽象 | CommandModule |
| `cli/` | CLI 相关 | PromptManager, StyleManager |
| `completion/` | 自动补全 | AutoCompleter |
| `configuration/` | 配置系统 | ConfigManager, Providers, Themes |
| `decoration/` | 装饰器 | typed_command |
| `error_handling/` | 错误处理 | ErrorHandlerChain, CLIException |
| `exceptions/` | 异常定义 | CLIException |
| `execution/` | 命令执行 | CommandExecutor |
| `formatting/` | 格式化 | HelpFormatter |
| `interfaces/` | Protocol 接口 | 7个 Protocol 接口 |
| `loaders/` | 模块加载 | 4个加载组件 |
| `prompts/` | 提示符管理 | PromptProvider |
| `registry/` | 命令注册表 | CommandRegistry |
| `resolvers/` | 名称解析 | ModuleNameResolver |
| `state/` | 状态管理 | StateManager |

**设计原则**：
- ✅ **单一职责原则**：每个子包负责一个功能域
- ✅ **接口隔离原则**：7个 Protocol 接口支持鸭子类型
- ✅ **依赖倒置原则**：高层依赖接口而非具体实现

## 📋 代码规范

### Python 版本

- **目标版本**: Python 3.12+
- **类型检查**: mypy (严格模式)
- **代码风格**: ruff

### 类型注解规范

#### 1. 函数签名

**必须**添加类型注解：

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.core.cli import PromptToolkitCLI

def register_commands(self, cli: "PromptToolkitCLI") -> None:
    """注册模块命令。"""
    pass
```

**规则**：
- 使用 `TYPE_CHECKING` 处理前向引用
- 所有参数必须有类型注解
- 所有函数必须有返回类型注解

#### 2. 类型变量

使用 PEP 695 语法（Python 3.12+）：

```python
def typed_command[T: BaseModel](
    model_cls: type[T],
) -> Callable[[Callable[..., Any]], Callable[[Any, str], None]]:
    pass
```

#### 3. 联合类型

使用 `X | Y` 语法（Python 3.10+）：

```python
def get_module(self, name: str) -> CommandModule | None:
    pass
```

#### 4. 类型断言

使用 `typing.cast()` 而非 `type: ignore`：

```python
from typing import cast

# ✅ 正确
return cast(str, module.name)

# ❌ 错误
return module.name  # type: ignore[return-value]
```

### Pydantic 模型规范

#### 1. 使用 Tagged Union

对于多种类型的配置，使用 Pydantic v2 的 Tagged Union：

```python
from typing import Literal
from pydantic import BaseModel, Field

class LogConfig(BaseModel):
    """日志配置基类。"""
    log_type: Literal["direct", "k8s", "docker"]
    name: str

class DirectLogConfig(LogConfig):
    """直接日志配置。"""
    log_type: Literal["direct"] = Field(default="direct")
    path: str
```

#### 2. 字段描述

所有字段必须添加 `description`：

```python
class ConnectArgs(BaseModel):
    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口号")
```

### 导入规范

#### 1. 导入顺序

```python
# 1. 标准库
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

# 2. 第三方库
from pydantic import BaseModel, Field
from prompt_toolkit import PromptSession

# 3. 本地模块
from ptk_repl.core.base import CommandModule
from ptk_repl.core.decorators import typed_command
```

#### 2. TYPE_CHECKING 使用

仅在类型注解时导入，避免运行时循环依赖：

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI
    from ptk_repl.core.state_manager import StateManager

class MyModule(CommandModule):
    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        pass

    def initialize(self, state_manager: "StateManager") -> None:
        pass
```

---

### Protocol 接口使用规范（2026-01-03 新增）

#### 何时使用 Protocol？

PTK_REPL 使用 **Protocol 接口**（而非 ABC）来支持鸭子类型和依赖注入。

**使用场景**：
- ✅ 需要鸭子类型支持（无需显式继承）
- ✅ 有多个可能的实现类
- ✅ 依赖注入场景
- ✅ 第三方扩展

**不使用场景**：
- ❌ 只有一个实现类（使用具体类即可）
- ❌ 需要强制继承（使用 ABC）

#### Protocol vs ABC

**Protocol（推荐）**：
```python
from typing import Protocol

@runtime_checkable
class ICliContext(Protocol):
    """CLI 上下文接口（鸭子类型）。"""

    def poutput(self, text: str) -> None: ...

    def perror(self, text: str) -> None: ...

# 无需显式继承
class MyCLI:
    def poutput(self, text: str) -> None:
        print(text)

    def perror(self, text: str) -> None:
        print(f"Error: {text}", file=sys.stderr)

# 类型检查
cli: ICliContext = MyCLI()  # ✅ 通过（鸭子类型）
```

**ABC（不推荐）**：
```python
from abc import ABC, abstractmethod

class ICliContext(ABC):
    """CLI 上下文接口（必须显式继承）。"""

    @abstractmethod
    def poutput(self, text: str) -> None: ...

    @abstractmethod
    def perror(self, text: str) -> None: ...

# 必须显式继承
class MyCLI(ICliContext):  # ⚠️ 强制继承
    def poutput(self, text: str) -> None:
        print(text)

    def perror(self, text: str) -> None:
        print(f"Error: {text}", file=sys.stderr)

# 第三方实现无法通过类型检查
class ThirdPartyCLI:  # ❌ 未继承，类型检查失败
    def poutput(self, text: str) -> None:
        print(text)
```

#### 定义 Protocol 接口

**基本规范**：
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IMyInterface(Protocol):
    """接口简要描述（单行）。"""

    def method_name(self, param: str) -> None:
        """方法描述。

        Args:
            param: 参数描述
        """
        ...
```

**示例**：定义模块加载器接口
```python
@runtime_checkable
class IModuleLoader(Protocol):
    """模块加载器接口。

    支持懒加载和即时加载。
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
```

#### Protocol 接口最佳实践

1. **使用 `@runtime_checkable` 装饰器**
   - 支持运行时类型检查（`isinstance()`）
   - 在 typed_command 等需要运行时检查的场景中必需

2. **接口隔离原则**
   - 每个接口只包含相关的方法
   - 避免臃肿的"万能接口"

   **示例**：
   ```python
   # ✅ 好的设计（接口隔离）
   @runtime_checkable
   class IModuleLoader(Protocol):
       def load(self, name: str) -> CommandModule | None: ...

   @runtime_checkable
   class IModuleRegister(Protocol):
       def register(self, module: CommandModule) -> None: ...

   # ❌ 不好的设计（臃肿的接口）
   @runtime_checkable
   class IModuleManager(Protocol):
       def load(self, name: str) -> CommandModule | None: ...
       def register(self, module: CommandModule) -> None: ...
       def discover(self) -> list[str]: ...
       def resolve(self, name: str) -> str: ...
   ```

3. **在函数参数中使用 Protocol**
   - 支持多种实现
   - 依赖注入友好

   **示例**：
   ```python
   def process_command(
       cli: ICliContext,  # Protocol 接口
       command: str
   ) -> None:
       """处理命令（支持任何 ICliContext 实现）。"""
       cli.poutput(f"执行命令: {command}")

   # 可以传入任何符合接口的对象
   process_command(MyCLI(), "status")
   process_command(ThirdPartyCLI(), "status")
   ```

4. **Protocol 属性支持**
   - Protocol 可以定义属性
   - 实现类必须提供同名属性

   **示例**：
   ```python
   @runtime_checkable
   class ICliContext(Protocol):
       state: StateManager  # 属性
       registry: CommandRegistry  # 属性

       def poutput(self, text: str) -> None: ...

   class PromptToolkitCLI:
       state: StateManager
       registry: CommandRegistry

       def poutput(self, text: str) -> None:
           print(text)
   ```

#### 项目中的 7 个 Protocol 接口

PTK_REPL 定义了 7 个核心 Protocol 接口（位于 `src/ptk_repl/core/interfaces/`）：

| 接口 | 文件 | 用途 |
|------|------|------|
| `ICliContext` | `cli_context.py` | CLI 上下文（输出、状态） |
| `IModuleLoader` | `module_loader.py` | 模块加载器 |
| `IModuleRegister` | `module_register.py` | 模块注册器 |
| `IModuleDiscoverer` | `module_discoverer.py` | 模块发现器 |
| `ICommandResolver` | `command_resolver.py` | 命令名称解析器 |
| `IPromptProvider` | `prompt_provider.py` | 提示符提供者 |
| `IRegistry` | `registry.py` | 命令注册表 |

**详细文档**：[接口设计](../design/interface-design.md)

---

## 🔍 代码质量工具

### Pre-commit Hooks

项目使用 pre-commit 自动化代码质量检查：

```bash
# 安装 hooks
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files

# 跳过 hooks（不推荐）
git commit --no-verify -m "message"
```

### Ruff (Linter & Formatter)

**配置**: [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)

```bash
# 检查代码
uv run ruff check src/

# 自动修复
uv run ruff check --fix src/

# 格式化代码
uv run ruff format src/
```

### Mypy (Type Checker)

**配置**: [`pyproject.toml`](../pyproject.toml) (mypy section)

```bash
# 类型检查
uv run mypy src/

# 详细错误信息
uv run mypy src/ --show-error-codes
```

**类型检查配置**：
- `check_untyped_defs = true` - 检查未类型注解的函数
- `warn_redundant_casts = true` - 警告冗余的类型断言
- `warn_unused_ignores = true` - 警告未使用的 type: ignore
- `strict_equality = true` - 严格相等检查

## 🧪 测试规范

### 测试结构

```
tests/
├── test_ptk_repl_simple.py  # 简单集成测试
└── test_ptk_repl.py          # 详细单元测试
```

### 测试命令

```bash
# 运行所有测试
uv run pytest

# 运行特定测试文件
uv run pytest tests/test_ptk_repl_simple.py

# 显示详细输出
uv run pytest -v

# 显示覆盖率
uv run pytest --cov=ptk_repl
```

## 📝 文档规范

### Docstring 规范

使用 Google 风格的 docstring：

```python
def connect_ssh(host: str, port: int = 22) -> None:
    """连接到 SSH 服务器。

    Args:
        host: 主机地址
        port: SSH 端口，默认 22

    Raises:
        ConnectionError: 连接失败时抛出

    Examples:
        >>> connect_ssh("localhost", 22)
        已连接到 localhost:22
    """
    pass
```

### 类型提示的 Docstring

第一行应该是简洁的描述：

```python
class CommandRegistry:
    """命令注册表。

    管理所有模块和命令的注册。
    """
```

## 🔧 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

### 2. 开发和测试

```bash
# 修改代码
# ...

# 运行检查
uv run ruff check src/
uv run mypy src/
uv run pytest

# 运行 pre-commit
uv run pre-commit run --all-files
```

### 3. 提交更改

```bash
git add .
git commit -m "feat: add your feature description"
```

**提交消息规范**：
- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建/工具链相关

### 4. 推送和 PR

```bash
git push origin feature/your-feature-name
# 在 GitHub/GitLab 上创建 Pull Request
```

## 🎯 常见任务

### 添加新模块

详见 [模块开发教程](guides/module-development.md)

### 修改核心组件

1. 修改 `src/ptk_repl/core/` 下的文件
2. 更新相关文档
3. 运行 `uv run mypy src/` 确保类型检查通过
4. 运行 `uv run pytest` 确保测试通过
5. 更新 `docs/design/architecture.md`（如需要）

### 修复 Bug

1. 在 tests/ 中添加失败测试用例
2. 修复代码
3. 验证测试通过
4. 运行完整测试套件

### 性能优化

1. 使用 `uv run python -m cProfile` 分析性能
2. 识别瓶颈
3. 优化代码
4. 对比前后性能数据

## 🚦 常见问题

### 类型检查错误

**问题**: mypy 报告 "Returning Any from function"

**解决**: 使用 `typing.cast()` 进行类型断言

```python
from typing import cast

# ❌ 错误
return module.name

# ✅ 正确
return cast(str, module.name)
```

### 循环导入

**问题**: 两个模块互相导入导致错误

**解决**: 使用 `TYPE_CHECKING` 和字符串类型注解

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from other_module import OtherClass

def process(obj: "OtherClass") -> None:
    pass
```

### Pre-commit 失败

**问题**: pre-commit 检查失败

**解决**: 按错误类型处理

```bash
# ruff 错误
uv run ruff check --fix src/

# mypy 错误
uv run mypy src/
# 查看具体错误，修复类型注解

# 格式问题
uv run ruff format src/
```

## 📚 相关文档

- [架构设计](../design/architecture.md)
- [模块开发教程](guides/module-development.md)
- [API 参考](../implementation/api-reference.md)
- [配置指南](guides/configuration.md)

---

**最后更新**: 2026-01-03
