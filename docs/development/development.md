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

```
cli_tool/
├── src/ptk_repl/          # 源代码
│   ├── core/              # 核心框架
│   ├── state/             # 状态定义
│   ├── modules/           # 内置模块
│   └── cli.py             # CLI 入口
├── tests/                 # 测试代码
├── docs/                  # 文档
├── scripts/               # 构建脚本
├── pyproject.toml         # 项目配置
├── .pre-commit-config.yaml  # Pre-commit 配置
└── ptk_repl_config.yaml.example  # 配置示例
```

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

**最后更新**: 2025-12-28
