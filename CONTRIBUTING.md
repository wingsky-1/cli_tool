# 贡献指南

感谢您对 MyREPL 项目的关注！我们欢迎各种形式的贡献。

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交信息](#提交信息)
- [问题报告](#问题报告)
- [功能建议](#功能建议)

## 行为准则

- 尊重所有贡献者
- 欢迎不同观点和建设性反馈
- 专注于项目改进

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议：

1. 检查 [Issues](https://github.com/yourusername/myrepl/issues) 是否已存在类似问题
2. 如果没有，创建新 Issue，使用合适的模板
3. 提供尽可能详细的信息：

**Bug 报告应包含**：
- Python 版本
- 操作系统
- 复现步骤
- 预期行为
- 实际行为
- 错误信息（如果有）

**功能建议应包含**：
- 功能描述
- 使用场景
- 预期效果
- 可能的实现方案（可选）

### 提交代码

#### 1. Fork 仓库

```bash
# 在 GitHub 上 Fork 仓库
# 然后克隆您的 Fork
git clone https://github.com/yourusername/myrepl.git
cd myrepl
```

#### 2. 创建分支

```bash
# 从 main 分支创建新分支
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

**分支命名规范**：
- `feature/` - 新功能
- `fix/` - Bug 修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关
- `chore/` - 其他维护工作

#### 3. 设置开发环境

```bash
# 使用 uv 安装依赖
pip install uv
uv sync

# 安装 pre-commit hooks
uv run pre-commit install
```

#### 4. 进行开发

**创建新模块**：
- 参考 [模块开发指南](docs/development/module-development.md)
- 遵循现���代码风格
- 添加类型注解
- 编写文档字符串

**代码规范**：
- 使用类型注解（mypy strict 模式）
- 遵循 PEP 8
- 使用 Pydantic v2 进行数据验证
- 添加清晰的文档字符串

#### 5. 运行检查

```bash
# 代码检查
uv run ruff check src/

# 类型检查
uv run mypy src/

# 代码格式化
uv run ruff format src/

# 运行测试（如果已有）
uv run pytest
```

#### 6. 提交变更

```bash
git add .
git commit -m "feat: add xyz feature"
```

**提交信息规范**（遵循 Conventional Commits）：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**（type）：
- `feat` - 新功能
- `fix` - Bug 修复
- `docs` - 文档更新
- `style` - 代码格式（不影响功能）
- `refactor` - 重构
- `test` - 测试相关
- `chore` - 构建/工具相关

**示例**：
```
feat(database): add connection pooling support

- Implement connection pool manager
- Add pool configuration options
- Update module state to track pool connections

Closes #123
```

#### 7. 推送到 Fork

```bash
git push origin feature/your-feature-name
```

#### 8. 创建 Pull Request

1. 访问原始仓库的 GitHub 页面
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写 PR 模板
5. 等待 CI 检查通过
6. 等待代码审查

## 开发流程

### 项目结构

```
src/myrepl/
├── core/          # 核心框架
├── state/         # 状态管理
└── modules/       # 内置模块
```

### 添加新模块

1. 创建模块目录：
   ```bash
   mkdir -p src/myrepl/modules/mymodule
   ```

2. 创建必需文件：
   - `__init__.py` - 模块导出
   - `module.py` - 模块实现
   - `state.py` - 状态定义（可选）

3. 实现模块类：
   ```python
   from myrepl.core.base import CommandModule

   class MyModule(CommandModule):
       @property
       def name(self) -> str:
           return "mymodule"

       def register_commands(self, cli) -> None:
           # 注册命令
           pass
   ```

4. 更新配置：
   ```yaml
   # myrepl_config.yaml
   core:
     enabled_modules:
       - mymodule
   ```

详细步骤请参考 [模块开发指南](docs/development/module-development.md)。

### 测试

目前项目尚未建立完整的测试套件，但我们鼓励：

1. **手动测试**：
   ```bash
   uv run python -m myrepl.cli
   ```

2. **模块功能测试**：
   - 测试所有命令
   - 测试参数验证
   - 测试错误处理

3. **代码质量检查**：
   ```bash
   uv run lint
   ```

## 代码规范

### Python 代码

- **类型注解**：所有函数必须有完整的类型注解
- **文档字符串**：使用 Google 风格或 NumPy 风格
- **命名规范**：
  - 模块名：小写，`mymodule`
  - 类名：大驼峰，`MyModule`
  - 函数/方法：小写下划线，`my_function`
  - 常量：大写下划线，`MY_CONSTANT`

### Pydantic 模型

```python
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    """模型描述"""

    field1: str = Field(description="字段描述")
    field2: int = Field(default=10, ge=0, le=100)
```

### 命令定义

```python
@typed_command(MyArgs)
def do_mycommand(self, args: MyArgs) -> None:
    """命令描述。

    用法: module command <arg> [--option VALUE]

    示例:
        module command test --option 10
    """
    pass
```

### 错误处理

```python
# 使用友好的错误消息
self.perror("❌ 操作失败")
self.pwarning("⚠️  警告信息")
self.poutput("✅ 成功")
```

## 文档贡献

### 改进文档

文档同样重要！您可以：

1. 修复错别字或语法错误
2. 改进现有内容的清晰度
3. 添加缺失的示例
4. 翻译文档

### 文档位置

- **用户文档**：`docs/guides/`
- **开发文档**：`docs/development/`
- **设计文档**：`docs/design/`
- **实现文档**：`docs/implementation/`

## Pull Request 指南

### PR 标题

使用与提交信息相同的格式：

```
feat: add xyz feature
fix: resolve abc issue
docs: update installation guide
```

### PR 描述

回答以下问题：

1. **这个 PR 做了什么？**
2. **为什么需要这个变更？**
3. **如何测试这些变更？**
4. **相关 Issue**：`Closes #123` 或 `Related to #123`

### 审查反馈

- 及时回应审查意见
- 愉快接受建设性批评
- 解释技术决策（如有必要）

## 发布流程

项目维护者负责发布：

1. 更新版本号（`pyproject.toml`）
2. 更新 `CHANGELOG.md`
3. 创建 Git 标签
4. 构建和发布

## 获取帮助

- 查看 [文档](docs/)
- 搜索 [Issues](https://github.com/yourusername/myrepl/issues)
- 在 Issue 中提问

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下发布。

---

再次感谢您的贡献！🎉
