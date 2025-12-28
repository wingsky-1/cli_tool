# Git Hooks Setup

本项目使用 `pre-commit` 框架（通过 uv 管理）来自动化代码检查。

## 安装 Pre-commit Hooks

```bash
# 确保已安装依赖
uv sync

# 安装 git hooks
uv run pre-commit install
```

现在每次提交前，会自动运行：
- `ruff check` - 代码检查
- `ruff format` - 代码格式化
- `mypy` - 类型检查

## 手动运行检查

```bash
# 在所有文件上运行 pre-commit
uv run pre-commit run --all-files

# 只运行特定检查
uv run pre-commit run ruff-check --all-files
uv run pre-commit run mypy --all-files
```

## 跳过 Pre-commit

如果需要跳过 pre-commit 检查（不推荐）：

```bash
git commit --no-verify -m "Your commit message"
```

## 更新 Hooks

当 `.pre-commit-config.yaml` 更新后：

```bash
uv run pre-commit autoupdate
```

## 可用的 uv 脚本

在 `pyproject.toml` 中配置了以下快捷命令：

```bash
# 格式化代码
uv run format

# 检查代码
uv run check

# 类型检查
uv run typecheck

# 运行所有检查
uv run lint
```

