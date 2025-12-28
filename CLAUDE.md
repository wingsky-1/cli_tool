# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

PTK_REPL 是一个基于 prompt-toolkit + Pydantic v2 构建的现代化模块化 CLI 框架。该项目采用懒加载机制、双层状态管理（全局状态 + 模块隔离状态）以及类型安全的命令参数验证。

## 常用命令

### 运行和测试
```bash
# 运行 REPL
uv run ptk_repl
# 或
uv run python -m ptk_repl.cli

# 运行测试
uv run pytest
uv run pytest tests/test_ptk_repl_simple.py  # 运行单个测试文件
uv run pytest -v                              # 详细输出
uv run pytest --cov=ptk_repl                  # 显示覆盖率
```

### 代码质量检查
```bash
# 代码检查
uv run ruff check src/
uv run ruff check --fix src/                  # 自动修复

# 类型检查
uv run mypy src/

# 代码格式化
uv run ruff format src/

# 运行所有检查
uv run lint
```

### Pre-commit Hooks
```bash
# 安装 hooks
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files

# 跳过 hooks（不推荐）
git commit --no-verify -m "message"
```

### 构建
```bash
# 使用项目构建脚本（推荐）
uv run python scripts/build_ptk_repl.py
```

该脚本会自动扫描 `src/ptk_repl/modules/` 目录下的所有模块，生成完整的 `hidden-import` 列表，并使用 PyInstaller 打包。

## 代码架构

### 核心设计原则
1. **模块化优先** - 所有功能以模块形式组织，模块间完全解耦
2. **类型安全** - 基于 Pydantic v2 的运行时类型验证
3. **懒加载** - 按需加载模块，最小化启动开销
4. **双层状态** - 全局状态（跨模块共享）+ 模块状态（隔离）
5. **自动发现** - 模块自动注册，零配置添加新功能

### 目录结构
```
src/ptk_repl/
├── cli.py                  # CLI 入口和主控制器 (PromptToolkitCLI)
├── core/                   # 核心框架
│   ├── base.py            # CommandModule 基类
│   ├── registry.py        # CommandRegistry - 命令注册表
│   ├── state_manager.py   # StateManager - 双层状态管理
│   ├── config_manager.py  # ConfigManager - YAML 配置管理
│   ├── decorators.py      # typed_command 装饰器（参数验证）
│   ├── completer.py       # AutoCompleter - 智能自动补全
│   └── help_formatter.py  # HelpFormatter - 帮助格式化
│
├── state/                  # 状态定义
│   ├── global_state.py    # GlobalState - 全局状态（跨模块共享）
│   └── module_state.py    # ModuleState 基类
│
└── modules/                # 内置模块
    ├── core/              # 核心命令（status, modules, exit）
    ├── database/          # 数据库模块示例
    └── ssh/               # SSH 模块（连接管理、日志查看）
```

### 命令执行流程
```
用户输入 → PromptToolkitCLI.default()
         → _parse_input() 分词
         → CommandRegistry.get_command_info() 查找命令
         → 懒加载模块（如需要）
         → typed_command 参数验证（Pydantic v2）
         → 执行业务逻辑
         → 更新状态（GlobalState/ModuleState）
```

## 开发规范

### Python 版本
- **目标版本**: Python 3.12+
- **类型检查**: mypy（严格模式）
- **代码风格**: ruff

### 类型注解规范

1. **使用 TYPE_CHECKING 处理前向引用**：
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI

def register_commands(self, cli: "PromptToolkitCLI") -> None:
    pass
```

2. **使用 PEP 695 语法（Python 3.12+ 类型变量）**：
```python
def typed_command[T: BaseModel](
    model_cls: type[T],
) -> Callable[[Callable[..., Any]], Callable[[Any, str], None]]:
    pass
```

3. **联合类型使用 `X | Y` 语法**：
```python
def get_module(self, name: str) -> CommandModule | None:
    pass
```

4. **使用 `typing.cast()` 而非 `type: ignore`**：
```python
from typing import cast

# ✅ 正确
return cast(str, module.name)

# ❌ 错误
return module.name  # type: ignore[return-value]
```

### Pydantic 模型规范

1. **使用 Tagged Union**（多种类型的配置）：
```python
from typing import Literal
from pydantic import BaseModel, Field

class LogConfig(BaseModel):
    log_type: Literal["direct", "k8s", "docker"]
    name: str

class DirectLogConfig(LogConfig):
    log_type: Literal["direct"] = Field(default="direct")
    path: str
```

2. **所有字段必须添加 `description`**：
```python
class ConnectArgs(BaseModel):
    host: str = Field(..., description="主机地址")
    port: int = Field(default=5432, ge=1, le=65535, description="端口号")
```

### 导入规范
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

### Docstring 规范

使用 Google 风格：
```python
def connect_ssh(host: str, port: int = 22) -> None:
    """连接到 SSH 服务器。

    Args:
        host: 主机地址
        port: SSH 端口，默认 22

    Raises:
        ConnectionError: 连接失败时抛出
    """
    pass
```

## 添加新模块

1. **创建模块目录**：`src/ptk_repl/modules/mymodule/`
2. **定义模块类**（继承 `CommandModule`）：
   - 必须实现：`name`, `description`, `register_commands()`
   - 可选实现：`aliases`, `version`, `initialize()`, `shutdown()`
3. **创建 `__init__.py`** 导出模块类
4. **在配置中启用模块**（编辑 `ptk_repl_config.yaml`）

详细步骤见 [docs/guides/module-development.md](docs/guides/module-development.md)

## 关键组件说明

### CommandModule 基类
所有模块必须继承此类。核心方法：
- `register_commands(cli)` - 注册命令到 CLI
- `initialize(state_manager)` - 模块初始化，获取模块状态
- `shutdown()` - 模块关闭，清理资源

### typed_command 装饰器
基于 Pydantic v2 的参数验证装饰器：
```python
@typed_command(CreateUserArgs)
def do_create(self, args: CreateUserArgs) -> None:
    # args 已经是验证后的 CreateUserArgs 对象
    print(f"创建用户: {args.username}")
```

### 双层状态管理
- **GlobalState**：跨模块共享（如：连接状态、当前主机）
- **ModuleState**：模块隔离（如：SSH 连接池、数据库查询历史）

访问方式：
```python
# 全局状态
global_state = cli.state.global_state
global_state.connected = True

# 模块状态
self.state = state_manager.get_module_state("mymodule", MyModuleState)
self.state.counter += 1
```

## 懒加载机制

模块按需加载，启动时只加载 `core` 模块。当用户输入模块名时，框架自动：
1. 动态导入模块
2. 调用 `module.register_commands(cli)`
3. 调用 `module.initialize(state_manager)`

配置预加载模块（启动时加载）：
```yaml
core:
  preload_modules:
    - core
    - ssh
    - database
```

## 相关文档

- [架构设计](docs/design/architecture.md) - 系统架构和核心组件设计
- [开发指南](docs/development/development.md) - 开发环境搭建和代码规范
- [模块开发教程](docs/guides/module-development.md) - 如何创建自定义模块
- [API 参考](docs/implementation/api-reference.md) - 核心 API 完整参考
- [配置文件说明](docs/ptk_repl-config.md) - ptk_repl 配置详解
- [PyInstaller 打包指南](docs/ptk_repl-pyinstaller.md) - 如何打包可执行文件

## Git 提交消息规范

- `feat:` - 新功能
- `fix:` - Bug 修复
- `docs:` - 文档更新
- `refactor:` - 代码重构
- `test:` - 测试相关
- `chore:` - 构建/工具链相关
