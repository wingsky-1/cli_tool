# PTK_REPL - 现代化模块化 CLI 框架

> 基于 prompt-toolkit + Pydantic 构建的可扩展命令行界面框架

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Types: mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy-lang.org/)

## ✨ 特性

- 🎨 **现代化界面** - 基于 prompt-toolkit 的优美交互体验
- 🧩 **模块化架构** - 清晰的模块接口，易于扩展
- 🎯 **类型安全** - 基于 Pydantic v2 的参数验证
- 🔧 **配置驱动** - YAML 配置文件管理
- 🚀 **零心智负担** - 新增模块只需修改配置
- 📦 **PyInstaller 友好** - 自动打包所有模块
- 🔄 **懒加载机制** - 按需加载模块，提升启动速度
- 💾 **双层状态管理** - 全局状态 + 模块隔离状态
- ⚡ **智能自动补全** - 实时命令补全和描述提示

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ptk_repl.git
cd ptk_repl

# 使用 uv 安装（推荐）
pip install uv
uv sync

# 或使用 pip
pip install -e .
```

### 运行

```bash
uv run ptk_repl
```

或者：

```bash
uv run python -m ptk_repl.cli
```

### 基本使用

```bash
# 查看状态
(ptk) status

# SSH 连接管理
(ptk) ssh connect 小米
(ptk) ssh log 应用日志 --lines 100
(ptk) ssh disconnect

# 数据库操作
(ptk) database connect localhost --port 5432
(ptk) db query users --limit 50
(ptk) db disconnect

# 查看所有模块
(ptk) modules

# 退出
(ptk) exit
```

## 📦 内置模块

### Core 模块
核心命令，提供基础功能：
- `status` - 显示当��状态
- `modules` - 列出所有模块
- `exit` / `quit` - 退出 REPL

### SSH 模块
SSH 连接和日志管理：
- `ssh connect <环境>` - 连接到预定义的 SSH 环境
- `ssh log <日志名称> [--lines LINES]` - 查看日志
- `ssh disconnect` - 断开 SSH 连接

**支持的日志模式**：
- **直接日志模式** - 读取服务器上的日志文件
- **Docker 日志模式** - 查看 Docker 容器日志
- **Kubernetes 日志模式** - 查看 K8s Pod 日志

### Database 模块
数据库操作示例：
- `database connect <host> [--port PORT]` - 连接数据库
- `database query <table> [--limit LIMIT]` - 查询表
- `database disconnect` - 断开连接

**命令别名**：
- `db connect`, `db conn`
- `db query`, `db q`
- `db disconnect`, `db disc`

## 🔧 配置

编辑 `ptk_repl_config.yaml`：

```yaml
core:
  # 预加载的模块（可选）
  preload_modules:
    - database
    - ssh

# 补全配置
completions:
  enabled: true
  show_descriptions: true
  cache:
    enabled: true

modules:
  ssh:
    # SSH 环境定义
    environments:
      - name: 小米
        description: "生产环境服务器"
        host: "192.168.31.115"
        port: 22
        username: "tangyi"
        password: "your_password"
        log_type: "direct"  # direct/docker/k8s

    # 日志路径配置
    log_paths:
      direct:
        - name: "应用日志"
          path: "/var/log/app/application.log"

      docker:
        - name: "Redis 容器日志"
          container_name: "redis"

      k8s:
        - name: "前端服务日志"
          namespace: "frontend"
          pod: "frontend-nginx-*"
          container: "nginx"
```

## 📚 开发指南

### 创建新模块

1. **创建模块目录**

```bash
mkdir -p src/ptk_repl/modules/mymodule
```

2. **定义模块类**

```python
# src/ptk_repl/modules/mymodule/module.py
from ptk_repl.core.base import CommandModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI

class MyModule(CommandModule):
    def __init__(self) -> None:
        super().__init__()
        self.cli: "PromptToolkitCLI | None" = None

    @property
    def name(self) -> str:
        return "mymodule"

    @property
    def description(self) -> str:
        return "我的自定义模块"

    @property
    def version(self) -> str:
        return "1.0.0"

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册模块命令"""
        self.cli = cli

        @cli.command()
        def do_hello(args: list[str]) -> None:
            """打招呼命令"""
            cli.poutput("Hello from mymodule!")
```

3. **创建 `__init__.py`**

```python
# src/ptk_repl/modules/mymodule/__init__.py
from ptk_repl.modules.mymodule.module import MyModule

__all__ = ["MyModule"]
```

4. **启用模块**

编辑 `ptk_repl_config.yaml`：

```yaml
core:
  preload_modules:
    - core
    - database
    - ssh
    - mymodule  # ← 添加新模块
```

5. **测试**

```bash
uv run ptk_repl
(ptk) mymodule hello
```

### 状态管理

#### 全局状态（跨模块共享）

```python
# 访问全局状态
global_state = cli.state.global_state
global_state.connected = True
global_state.current_host = "localhost"
```

#### 模块状态（隔离）

```python
# 定义模块状态
# src/ptk_repl/modules/mymodule/state.py
from pydantic import Field
from ptk_repl.state.module_state import ModuleState

class MyModuleState(ModuleState):
    counter: int = Field(default=0, description="计数器")

# 在模块中使用
def initialize(self, state_manager):
    self.state = state_manager.get_module_state("mymodule", MyModuleState)

def do_increment(self, args):
    self.state.counter += 1
    print(f"计数: {self.state.counter}")
```

### 命令参数验证

使用 Pydantic v2 进行类型安全的参数验证：

```python
from pydantic import BaseModel, Field
from ptk_repl.core.decorators import typed_command

class CreateUserArgs(BaseModel):
    """创建用户参数"""
    username: str = Field(description="用户名")
    age: int = Field(ge=0, le=150, description="年龄")
    email: str | None = Field(default=None, description="邮箱")

@typed_command(CreateUserArgs)
def do_create(self, args: CreateUserArgs) -> None:
    """创建新用户"""
    print(f"创建用户: {args.username}, 年龄: {args.age}")
```

## 🏗️ 架构

```
src/ptk_repl/
├── cli.py                  # CLI 入口和主控制器
├── core/                   # 核心框架
│   ├── base.py            # CommandModule 基类
│   ├── registry.py        # 命令注册表
│   ├── state_manager.py   # 状态管理器
│   ├── config_manager.py  # 配置管理器
│   ├── decorators.py      # 命令装饰器
│   ├── completer.py       # 自动补全器
│   └── help_formatter.py  # 帮助格式化
│
├── state/                  # 状态定义
│   ├── global_state.py    # 全局状态
│   └── module_state.py    # 模块状态基类
│
└── modules/                # 内置模块
    ├── core/              # 核心命令
    ├── database/          # 数据库模块
    └── ssh/               # SSH 模块
```

## 🔨 开发

### Pre-commit Hooks

本项目使用 pre-commit 自动化代码检查：

```bash
# 安装 pre-commit hooks
uv sync
uv run pre-commit install

# 手动运行检查
uv run pre-commit run --all-files

# 跳过检查（不推荐）
git commit --no-verify -m "Your message"
```

### 代码质量

```bash
# 代码检查
uv run ruff check src/

# 类型检查
uv run mypy src/

# 代码格式化
uv run ruff format src/

# 运行所有检查
uv run lint
```

### 构建

```bash
# PyInstaller 打包
pip install pyinstaller
uv run pyinstaller src/ptk_repl/__main__.py \
  --name ptk_repl \
  --onefile \
  --console \
  --add-data "ptk_repl_config.yaml:."
```

## 📖 文档

完整文档请查看 [docs/](docs/) 目录。

### 📚 文档中心
**[📚 查看所有文档](docs/README.md)** - 文档导航和快速索引

### 🏗️ 设计文档
- [架构设计](docs/design/architecture.md) - 系统架构和核心组件设计

### 💻 开发文档
- [开发指南](docs/development/development.md) - 开发环境搭建和代码规范
- [模块开发教程](docs/guides/module-development.md) - 如何创建自定义模块
- [API 参考](docs/implementation/api-reference.md) - 核心 API 完整参考

### 📖 使用指南
- [配置文件说明](docs/ptk_repl-config.md) - ptk_repl 配置详解
- [PyInstaller 打包指南](docs/ptk_repl-pyinstaller.md) - 如何打包可执行文件

### 📋 项目信息
- [更新日志](CHANGELOG.md) - 版本变更记录
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) - 强大的交互式命令行库
- [Pydantic](https://github.com/pydantic/pydantic) - 数据验证库
- [uv](https://github.com/astral-sh/uv) - 极速 Python 包管理器

## 📝 归档说明

本项目早期版本（基于 cmd2）已归档到 [archive/myrepl](archive/myrepl/)，仅供参考。
