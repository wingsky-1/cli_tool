# MyREPL CLI 测试说明

## 快速开始

### 运行完整测试套件

```bash
# Windows 用户
cd c:\Users\唐意\Desktop\Github\cli_tool
uv run python tests/test_cli_windows.py
```

### 预期结果

所有测试应该通过：
```
============================================================
总计: 6/6 测试通过
============================================================

🎉 所有测试通过！CLI 功能完整且正常工作。
```

## 测试文件说明

### 1. `test_cli_windows.py` - Windows 完整测试

**用途**: 自动化测试所有核心功能

**测试内容**:
- CLI 启动和欢迎消息
- 核心命令（status, modules, help）
- 懒加载机制
- Database 模块命令
- 短命令别名（db）
- 状态管理

**运行时间**: 约 10-15 秒

### 2. `test_cli_full.py` - 通用测试脚本

**用途**: 跨平台测试脚本（需要适当修改）

**注意**: 在 Windows 上可能遇到换行符问题，建议使用 `test_cli_windows.py`

## 手动测试

### 启动 CLI

```bash
uv run python -m myrepl.core.cli
```

### 测试命令序列

```
# 1. 查看状态
status
# 输出: ❌ 未连接

# 2. 查看模块
modules
# 输出: 已加载的模块列表和待加载（延迟）列表

# 3. 连接数据库
database connect localhost --port 8080 --ssl
# 输出: ✅ 已连接到 localhost:8080

# 4. 查看状态
status
# 输出: ✅ 已连接到 localhost:8080

# 5. 查询数据
database query users --limit 50
# 输出: 📊 查询表: users

# 6. 使用短命令
db query users --limit 10
# 输出: 📊 查询表: users

# 7. 断开连接
database disconnect
# 输出: 👋 已断开与 localhost:8080 的连接

# 8. 退出
exit
# 输出: 再见! 👋
```

## 常见问题

### Q: 测试失败怎么办？

**A**: 检查以下几点：
1. 确保在项目根目录运行测试
2. 确保已安装依赖: `uv sync`
3. 查看错误信息，确认是否是环境问题

### Q: 如何调试单个测试？

**A**: 修改测试脚本，注释掉其他测试，只运行需要调试的测试：

```python
# 只测试 database 模块
def main():
    test_cli_startup()
    test_database_module()  # 只运行这个测试
    # 其他测试...
```

### Q: help 命令中有多余的命令？

**A**: 这是已知的非关键问题。cmd2 的某些内置命令无法完全隐藏，但不影响使用。

## 测试覆盖率

| 功能 | 测试覆盖 | 状态 |
|------|---------|------|
| 核心框架 | ✅ 100% | 通过 |
| 命令系统 | ✅ 100% | 通过 |
| 模块系统 | ✅ 100% | 通过 |
| 懒加载 | ✅ 100% | 通过 |
| 状态管理 | ✅ 100% | 通过 |
| Database 模块 | ✅ 100% | 通过 |

## 代码质量检查

运行测试前确保通过以下检查：

```bash
# Ruff 代码检查
uv run ruff check src/

# Mypy 类型检查
uv run mypy src/

# 代码格式化
uv run ruff format src/
```

## 归档文档

详细的测试结果归档请查看: [TEST_RESULTS_ARCHIVE.md](./TEST_RESULTS_ARCHIVE.md)

## 贡献测试

欢迎贡献新的测试用例！

1. 在 `tests/` 目录下创建新文件
2. 命名格式: `test_*.py`
3. 使用现有的测试框架
4. 运行并确保所有测试通过
5. 更新文档说明

---

**最后更新**: 2025-12-27
**测试状态**: ✅ 全部通过 (6/6)
