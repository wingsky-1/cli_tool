# PTK_REPL 测试文档

本文档描述 PTK_REPL 的测试结构和测试规范。

## 测试结构

```
tests/
├── test_connection_context.py    # 连接上下文测试
├── test_config_provider.py        # 配置提供者测试
├── test_color_theme.py            # 颜色主题测试
├── test_error_handling.py          # 错误处理测试
├── test_iclicontext.py             # ICliContext 接口测试
├── test_module_name_resolver.py    # 模块名称解析器测试
└── test_ptk_repl.py                # 核心功能集成测试
```

## 运行测试

### 运行所有测试

```bash
uv run pytest
```

### 运行特定测试文件

```bash
uv run pytest tests/test_ptk_repl.py
uv run pytest tests/test_connection_context.py
```

### 显示详细输出

```bash
uv run pytest -v
```

### 显示覆盖率报告

```bash
uv run pytest --cov=ptk_repl
uv run pytest --cov=ptk_repl --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试覆盖率目标

- **目标覆盖率**: ≥ 90%
- **当前覆盖率**: 待统计

## 测试规范

### 1. 测试文件命名

- 测试文件名以 `test_` 开头
- 测试类名以 `Test` 开头
- 测试方法名以 `test_` 开头

### 2. 使用 pytest

PTK_REPL 使用 pytest 作为测试框架。

**示例**：
```python
"""测试连接上下文。"""

from ptk_repl.state.connection_context import SSHConnectionContext

class TestSSHConnectionContext:
    """SSH 连接上下文测试。"""

    def test_init(self):
        """测试初始化。"""
        ctx = SSHConnectionContext("localhost", 22, "user")
        assert ctx.host == "localhost"
        assert ctx.port == 22

    def test_get_prompt_suffix(self):
        """测试获取提示符后缀。"""
        ctx = SSHConnectionContext("example.com", 22, "user")
        suffix = ctx.get_prompt_suffix()
        assert suffix == "@example.com"
```

### 3. 使用 Fixture

```python
import pytest
from ptk_repl.core.state_manager import StateManager
from ptk_repl.state.global_state import GlobalState

@pytest.fixture
def state_manager():
    """状态管理器 fixture。"""
    return StateManager()

@pytest.fixture
def global_state():
    """全局状态 fixture。"""
    return GlobalState()
```

### 4. 测试 Protocol 接口

```python
"""测试 ICliContext 接口。"""

from typing import cast
from ptk_repl.core.interfaces import ICliContext
from ptk_repl.cli import PromptToolkitCLI

class TestICliContext:
    """ICliContext 接口测试。"""

    def test_duck_typing(self):
        """测试鸭子类型。"""
        class MyCLI:
            def poutput(self, text: str) -> None:
                print(text)

            def perror(self, text: str) -> None:
                print(f"Error: {text}", file=sys.stderr)

        # 类型检查
        cli: ICliContext = MyCLI()  # ✅ 应该通过类型检查

        # 运行时检查
        assert isinstance(cli, ICliContext)  # ✅ 应该返回 True
```

### 5. 测试异常

```python
"""测试错误处理。"""

import pytest
from ptk_repl.core.exceptions.cli_exceptions import CommandException

class TestCommandException:
    """CommandException 测试。"""

    def test_command_exception(self):
        """测试命令异常。"""
        with pytest.raises(CommandException) as exc_info:
            raise CommandException("命令执行失败")

        assert str(exc_info.value) == "命令执行失败"
```

## 代码质量检查

### Ruff（Linter & Formatter）

```bash
# 检查测试代码
uv run ruff check tests/

# 自动修复
uv run ruff check --fix tests/

# 格式化测试代码
uv run ruff format tests/
```

### Mypy（Type Checker）

```bash
# 类型检查测试代码
uv run mypy tests/
```

## Pre-commit Hooks

项目使用 pre-commit 自动化代码质量检查：

```bash
# 安装 hooks
uv run pre-commit install

# 手动运行所有检查
uv run pre-commit run --all-files
```

## 测试开发工作流

### 1. 创建测试文件

```bash
touch tests/test_my_feature.py
```

### 2. 编写测试

```python
"""测试新功能。"""

import pytest
from ptk_repl.core.base import CommandModule

class TestMyFeature:
    """新功能测试。"""

    def test_basic_usage(self):
        """测试基本用法。"""
        # 测试代码
        assert True
```

### 3. 运行测试

```bash
uv run pytest tests/test_my_feature.py -v
```

### 4. 检查覆盖率

```bash
uv run pytest tests/test_my_feature.py --cov=ptk_repl
```

### 5. 提交代码

```bash
git add tests/test_my_feature.py
git commit -m "test: 添加新功能测试"
```

## 相关文档

- [开发指南](../docs/development/development.md) - 开发环境搭建和代码规范
- [架构设计](../docs/design/architecture.md) - 系统架构和核心组件
- [API 参考](../docs/implementation/api-reference.md) - 核心 API 文档

---

**最后更新**: 2026-01-03
**测试状态**: ✅ 持续改进中
