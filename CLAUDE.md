# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PTK_REPL 是一个基于 prompt-toolkit + Pydantic v2 构建的现代化模块化 CLI 框架。

**核心特性**：
- 🔌 **Protocol 接口** - 7个Protocol接口支持鸭子类型和依赖注入
- 🔐 **连接上下文抽象** - 多态方法替代 isinstance 检查
- ⚡ **错误处理系统** - 责任链模式处理异常
- 📦 **模块懒加载** - 按需加载，O(1) 别名查找
- 🎯 **类型安全** - Pydantic v2 运行时验证

## 常用命令

```bash
# 运行 REPL
uv run ptk_repl

# 运行测试
uv run pytest
uv run pytest --cov=ptk_repl

# 代码质量检查
uv run ruff check src/
uv run mypy src/
uv run lint  # 运行所有检查

# 构建
uv run python scripts/build_ptk_repl.py
```

## 核心架构

### 设计原则（SOLID）

1. **单一职责（SRP）** - 15个子包，每个一个功能域
2. **开闭原则（OCP）** - 多态方法替代 isinstance
3. **里氏替换（LSP）** - ConnectionContext 抽象
4. **接口隔离（ISP）** - 7个Protocol接口
5. **依赖倒置（DIP）** - 高层依赖接口

### 目录结构（15个子包）

```
src/ptk_repl/
├── cli.py                          # CLI 入口
├── core/                           # 核心框架（按功能域）
│   ├── interfaces/                 # 📌 Protocol 接口（7个）
│   ├── loaders/                    # 📦 模块加载系统（4组件）
│   ├── error_handling/             # ⚡ 错误处理链
│   ├── registry/                   # 命令注册表
│   ├── completion/                 # 自动补全
│   ├── configuration/              # 配置系统
│   ├── state/                      # 状态管理
│   └── [其他 8 个子包]            # base/cli/decoration/...
├── state/                          # 状态定义
│   ├── connection_context.py       # 📌 ConnectionContext 抽象
│   ├── global_state.py             # GlobalState
│   └── module_state.py             # ModuleState
└── modules/                        # 内置模块
    ├── core/
    ├── ssh/
    └── database/
```

完整目录结构见：[架构设计文档](docs/design/architecture.md)

### 命令执行流程

```
用户输入 → PromptToolkitCLI.default()
         → CommandRegistry 查找命令
         → 懒加载模块（UnifiedModuleLoader）
         → typed_command 参数验证（Pydantic v2）
         → 执行业务逻辑
         → ErrorHandlerChain 处理异常
         → 更新状态（GlobalState/ModuleState）
```

## 关键实现

### 1. Protocol 接口（鸭子类型）

**7个核心接口**：
- `ICliContext` - CLI 上下文（poutput/perror/state/registry）
- `IModuleLoader` - 模块加载器（load/is_loaded/ensure_module_loaded）
- `IModuleRegister` - 模块注册器（register/is_registered/get_module）
- `IModuleDiscoverer` - 模块发现器（discover_modules/preload_all）
- `ICommandResolver` - 命令名称解析器（resolve）
- `IPromptProvider` - 提示符提供者（get_prompt）
- `IRegistry` - 命令注册表（register_command/get_command_info/get_module）

**使用示例**：
```python
from ptk_repl.core.interfaces import IModuleLoader

def load_all(loader: IModuleLoader) -> None:
    # 支持任何 IModuleLoader 实现（鸭子类型）
    for name in ["ssh", "database"]:
        loader.ensure_module_loaded(name)
```

详见：[接口设计文档](docs/design/interface-design.md)

### 2. 模块加载系统（4组件架构）

```
ModuleLifecycleManager (门面)
    ↓
├── LazyModuleTracker       # 懒加载追踪（O(1)别名查找）
├── ModuleDiscoveryService  # 自动发现模块
├── UnifiedModuleLoader     # 统一加载逻辑
└── ModuleRegister          # 模块注册
```

详见：[API 参考 - 模块加载系统](docs/implementation/api-reference.md)

### 3. 连接上下文抽象（组合优于继承）

```python
class ConnectionContext(ABC):
    @abstractmethod
    def get_prompt_suffix(self) -> str:  # 多态方法
        pass

class SSHConnectionContext(ConnectionContext):
    def get_prompt_suffix(self) -> str:
        return f"@{self.host}"

# GlobalState 组合多个连接上下文
class GlobalState(BaseModel):
    ssh_context: SSHConnectionContext
    db_context: DatabaseConnectionContext
```

详见：[模块开发教程 - 连接上下文](docs/guides/module-development.md)

### 4. 错误处理系统（责任链）

```
ErrorHandlerChain
    ├─ CLIErrorHandler      # 处理 CLIException
    └─ BaseErrorHandler     # 兜底处理其他异常
```

**CLIException 层次结构**：
```
CLIException
    ├─ CommandException
    └─ ModuleException
```

## 新模块开发规范

### 快速步骤

1. **创建模块目录**：`src/ptk_repl/modules/mymodule/`
2. **定义模块类**（继承 `CommandModule`）：
   ```python
   class MyModule(CommandModule):
       @property
       def name(self) -> str:
           return "mymodule"

       def register_commands(self, cli: "PromptToolkitCLI") -> None:
           @cli.command()
           @typed_command(MyArgs)
           def do_mycommand(args: MyArgs) -> None:
               # 业务逻辑
               pass
   ```
3. **创建 `__init__.py`** 导出模块类
4. **在配置中启用模块**（编辑 `ptk_repl_config.yaml`）

### 核心规范

**必须实现**：
- `name` - 模块名称
- `description` - 模块描述
- `register_commands(cli)` - 注册命令

**可选实现**：
- `initialize(state_manager)` - 模块初始化（获取模块状态）
- `shutdown()` - 模块关闭（清理资源）
- `aliases` - 模块别名列表
- `version` - 模块版本

**类型注解**：
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI

def register_commands(self, cli: "PromptToolkitCLI") -> None:
    pass
```

**状态管理**：
```python
# 全局状态（跨模块共享）
global_state = cli.state.global_state
global_state.connected = True

# 模块状态（隔离）
self.state = state_manager.get_module_state("mymodule", MyModuleState)
self.state.counter += 1
```

完整开发教程：[模块开发教程](docs/guides/module-development.md)

## 相关文档

**设计文档**：
- [架构设计](docs/design/architecture.md) - 系统架构和核心组件
- [接口设计](docs/design/interface-design.md) - Protocol 接口详解
- [重构记录](docs/refactoring-guide.md) - 架构重构历史

**开发文档**：
- [开发指南](docs/development/development.md) - 开发环境搭建和代码规范
- [模块开发教程](docs/guides/module-development.md) - 如何创建自定义模块
- [API 参考](docs/implementation/api-reference.md) - 核心 API 完整参考

**配置和构建**：
- [配置文件说明](docs/ptk_repl-config.md) - ptk_repl 配置详解
- [PyInstaller 打包指南](docs/ptk_repl-pyinstaller.md) - 如何打包可执行文件

**测试文档**：
- [测试文档](tests/README.md) - 测试结构和规范

## Git 提交消息规范

- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建/工具链相关
