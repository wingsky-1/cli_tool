# 后续工作清单

## 📊 当前状态

**已完成**：
- ✅ 核心框架（CommandModule, CommandRegistry, StateManager, ConfigManager, PromptToolkitCLI）
- ✅ 状态系统（Pydantic v2）
- ✅ 功能模块（core, database, ssh）
- ✅ 代码质量检查通过（ruff, mypy）
- ✅ PyInstaller 打包指南
- ✅ 配置驱动的模块加载
- ✅ 智能自动补全系统
- ✅ 懒加载机制

**代码质量**：
- ✅ ruff: All checks passed!
- ✅ mypy: Success, no issues found

---

## 🎯 后续工作（按优先级排序）

### 优先级 1：代码清理和测试（推荐）

#### 1. 编写单元测试 🧪
**状态**: 待完成
**工作量**: 2-3小时

**测试覆盖**：
```python
# tests/test_core/
├── test_registry.py          # CommandRegistry 测试
├── test_state_manager.py     # StateManager 测试
├── test_config_manager.py    # ConfigManager 测试
└── test_base.py              # CommandModule 测试

# tests/test_modules/
├── test_core_module.py       # Core 模块测试
├── test_database_module.py   # Database 模块测试
└── test_ssh_module.py        # SSH 模块测试
```

**示例测试**：
```python
# tests/test_core/test_state_manager.py
import pytest
from ptk_repl.core.state_manager import StateManager
from ptk_repl.state.global_state import GlobalState
from ptk_repl.state.module_state import ModuleState

def test_global_state_initialization():
    manager = StateManager()
    state = manager.global_state

    assert isinstance(state, GlobalState)
    assert state.connected is False
    assert state.current_host is None

def test_module_state_isolation():
    manager = StateManager()

    # 获取两个模块的状态
    state1 = manager.get_module_state("module1", ModuleState)
    state2 = manager.get_module_state("module2", ModuleState)

    # 确保是不同的实例
    assert state1 is not state2
```

**收益**：
- 保证代码质量
- 防止回归
- 文档化预期行为

#### 2. 编写集成测试 🧪
**状态**: 待完成
**工作量**: 1-2小时

```python
# tests/test_integration/test_cli_workflow.py
def test_ssh_workflow():
    """测试完整的 SSH 工作流"""
    cli = PromptToolkitCLI()

    # 模拟命令执行
    cli.onecmd(["ssh", "connect", "小米"])
    assert cli.state.global_state.connected is True

    cli.onecmd(["ssh", "log", "应用日志", "--lines", "10"])
    # 验证状态更新

    cli.onecmd(["ssh", "disconnect"])
    assert cli.state.global_state.connected is False
```

---

### 优先级 2：文档和用户体验

#### 3. 创建模块开发指南 📚
**状态**: 待完成
**工作量**: 1-2小时

**内容**：
```markdown
# 模块开发指南

## 快速开始

### 1. 创建新模块

```bash
mkdir -p src/ptk_repl/modules/mymodule
```

### 2. 定义模块类

```python
from ptk_repl.core.base import CommandModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.core.cli import PromptToolkitCLI

class MyModule(CommandModule):
    @property
    def name(self) -> str:
        return "mymodule"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        # 注册命令
        pass
```

### 3. 启用模块

编辑 `ptk_repl_config.yaml`：
```yaml
core:
  preload_modules:
    - mymodule
```

## 高级主题

### 状态管理
### 命令别名
### 错误处理
### 配置访问
```

---

### 优先级 3：功能增强

#### 4. 添加更多日志模式支持 ⚡
**状态**: 待完成
**工作量**: 2-3小时

**新增日志模式**：
- Systemd Journal 日志模式
- ELK Stack 日志查询
- 云服务日志（AWS CloudWatch, Azure Log Analytics）

**收益**：
- 支持更多场景
- 更强大的日志管理能力

#### 5. 实现命令历史增强 ⚡
**状态**: 待完成
**工作量**: 1-2小时

**功能**：
- 历史命令搜索（Ctrl+R）
- 历史命令持久化
- 历史命令去重

---

### 优先级 4：高级特性（可选）

#### 6. 实现插件系统 🔌
**状态**: 可选
**工作量**: 3-4小时

**功能**：
- entry points 发现
- 第三方插件支持
- 插件管理命令

**决策点**：
- ❌ 如果是内部工具 → 不需要
- ✅ 如果是开源项目 → 强烈推荐

#### 7. 实现命令管道 🔧
**状态**: 可选
**工作量**: 4-5小时

**功能**：
```bash
# 支持命令管道
db query users | ssh upload 小米:/tmp/data.json
```

#### 8. 实现脚本模式 📜
**状态**: 可选
**工作量**: 2-3小时

**功能**：
```bash
# 从脚本文件执行命令
ptk_repl --script commands.txt
```

---

### 优先级 5：发布准备

#### 9. PyPI 发布准备 🚀
**状态**: 待完成
**工作量**: 1小时

**清单**：
- [ ] 完善 `pyproject.toml` 元数据
- [ ] 编写 `README.md`（PyPI 会显示）
- [ ] 添加 `LICENSE` 文件
- [ ] 版本号规范
- [ ] CHANGELOG.md
- [ ] 测试打包：`uv build`
- [ ] 本地安装测试：`uv pip install dist/*.whl`

#### 10. CI/CD 配置 🔄
**状态**: 可选
**工作量**: 1-2小时

**内容**：
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Run tests
        run: |
          uv sync
          uv run pytest
      - name: Lint
        run: |
          uv run ruff check
          uv run mypy
```

---

## 🎯 推荐实施路线

### 路线 A：最小可用（MVP）⚡
**时间**: 1-2小时
**目标**: 快速清理和使用

1. ✅ 基本功能测试（手动测试）（30分钟）
2. ✅ 更新文档（30分钟）

**适合**: 个人工具、内部使用

---

### 路线 B：生产就绪 🏢
**时间**: 1天
**目标**: 可以分享给团队使用

1. ✅ 路线 A 的所有内容
2. ✅ 编写单元测试（2-3小时）
3. ✅ 编写集成测试（1-2小时）
4. ✅ 创建开发指南（1-2小时）

**适合**: 团队工具、公司内部使用

---

### 路线 C：开源项目 🌟
**时间**: 2-3天
**目标**: 发布到 GitHub 和 PyPI

1. ✅ 路线 B 的所有内容
2. ✅ 添加更多日志模式支持（2-3小时）
3. ✅ 实现命令历史增强（1-2小时）
4. ✅ 实现插件系统（3-4小时，可选）
5. ✅ PyPI 发布（1小时）
6. ✅ CI/CD 配置（1-2小时）

**适合**: 开源项目、公共工具

---

## 💡 我的建议

根据您的情况，我建议：

**立即执行**（今天）：
1. 手动测试所有功能（30分钟）
2. 更新文档（30分钟）

**本周完成**：
3. 编写单元测试（2-3小时）
4. 创建开发指南（1-2小时）

**可选**（如果需要）：
5. 添加更多日志模式支持
6. 实现命令历史增强
7. 准备 PyPI 发布

---

## ❓ 需要帮助吗

告诉我您想要：
- **路线 A** - 我帮您快速测试和更新文档
- **路线 B** - 我帮您编写测试
- **路线 C** - 我帮您实现完整功能
- **其他** - 您有其他想法或需求