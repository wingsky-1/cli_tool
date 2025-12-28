# PTK_REPL PyInstaller 打包指南

## 问题描述

PTK_REPL 使用懒加载机制优化启动速度，这会导致 PyInstaller 无法通过静态分析发现所有模块。

**懒加载代码**（[cli.py:132](src/ptk_repl/cli.py#L132)）：
```python
module_path = f"ptk_repl.modules.{module_name}"
mod = importlib.import_module(module_path)  # 动态导入
```

PyInstaller 无法检测这种动态导入，导致打包后缺少模块。

## 解决方案

### 方案 1: 自动打包脚本（推荐，零维护）⭐

**优点**：
- ✅ **零维护**：自动发现所有模块
- ✅ 简单：一个命令搞定
- ✅ 可靠：自动更新
- ✅ 添加新模块无需修改任何配置文件！

**使用方法**：

```bash
# 打包（自动发现所有模块）
uv run python scripts/build_ptk_repl.py
```

**工作原理**：
1. 自动扫描 `src/ptk_repl/modules/` 目录
2. 发现所有可用模块（core、database、file 等）
3. 自动生成 PyInstaller 命令并执行

**输出位置**：
- Windows: `dist/ptk_repl.exe`
- Linux/macOS: `dist/ptk_repl`

### 方案 2: 使用 spec 文件（手动维护）

如果需要更精细的控制，可以使用 `ptk_repl.spec` 文件。

**缺点**：
- ❌ 每次添加新模块需要手动更新 `hiddenimports`
- ❌ 容易忘记更新
- ❌ 维护成本高

**不推荐日常开发使用**，仅在需要特殊配置时使用。

### 方案 3: 显式导入（辅助措施）

为了支持 PyInstaller 自动发现，我们在以下位置添加了显式导入：

1. **`src/ptk_repl/modules/__init__.py`**：
   ```python
   from ptk_repl.modules.core.module import CoreModule
   from ptk_repl.modules.database.module import DatabaseModule
   ```

2. **各模块的 `__init__.py`**：
   - `src/ptk_repl/modules/core/__init__.py`
   - `src/ptk_repl/modules/database/__init__.py`

这些导入确保 PyInstaller 能通过静态分析发现模块。

## 添加新模块（超简单！）

使用**自动打包脚本**后，添加新模块非常简单：

### 步骤：

1. **创建新模块目录**：
   ```bash
   mkdir src/ptk_repl/modules/file
   touch src/ptk_repl/modules/file/__init__.py
   touch src/ptk_repl/modules/file/module.py
   ```

2. **实现模块**：
   ```python
   # src/ptk_repl/modules/file/module.py
   from ptk_repl.core.base import CommandModule

   class FileModule(CommandModule):
       # ... 实现模块逻辑
   ```

3. **导出模块类**（推荐）：
   ```python
   # src/ptk_repl/modules/file/__init__.py
   from ptk_repl.modules.file.module import FileModule

   __all__ = ["FileModule"]
   ```

4. **打包**：
   ```bash
   uv run python scripts/build_ptk_repl.py
   ```

**就这么简单！** 打包脚本会自动发现并包含新模块。

### 推荐的模块结构

每个新模块应该遵循以下结构：

```
src/ptk_repl/modules/your_module/
├── __init__.py          # 导出模块类
├── module.py            # 模块实现
└── state.py             # 状态类（可选）
```

**最小 `__init__.py`**：
```python
"""你的模块。"""

from ptk_repl.modules.your_module.module import YourModule

__all__ = ["YourModule"]
```

这样 PyInstaller 就能自动发现并包含你的模块。

## 验证打包

打包后，测试所有模块是否正常工作：

```bash
$ ./dist/ptk_repl
欢迎使用 PTK REPL!
输入 'help' 查看帮助，'exit' 或 Ctrl+D 退出

(ptk) > modules
已加载的模块:
  • core (v1.0.0): 核心命令（状态、帮助、退出等）

(ptk) > database connect
已连接到 localhost:5432

(ptk) > modules
已加载的模块:
  • core (v1.0.0): 核心命令（状态、帮助、退出等）
  • database (v1.0.0): 数据库操作（连接、查询、断开）
```

如果 `database connect` 命令能正常工作，说明打包成功！

## 常见问题

### Q: 打包后运行提示模块未找到

**A**: 检查以下几点：
1. 确认该模块的 `__init__.py` 中有显式导入
2. 确认模块目录结构正确
3. 重新运行 `uv run python scripts/build_ptk_repl.py`

### Q: 如何减小可执行文件大小？

**A**: 修改 `scripts/build_ptk_repl.py`，添加 `excludes` 参数：
```python
cmd = [
    "pyinstaller",
    "--name=ptk_repl",
    "--console",
    "--onefile",
    # 添加排除项
    "--exclude-module=tkinter",
    "--exclude-module=matplotlib",
    # ...
]
```

### Q: 如何添加图标？

**A**: 修改 `scripts/build_ptk_repl.py`，添加图标参数：
```python
cmd = [
    "pyinstaller",
    "--name=ptk_repl",
    "--console",
    "--onefile",
    "--icon=path/to/icon.ico",  # Windows
    # 或
    "--icon=path/to/icon.icns",  # macOS
]
```

## 总结

| 方案 | 推荐度 | 维护成本 | 适用场景 |
|------|-------|---------|----------|
| 自动打包脚本 | ⭐⭐⭐⭐⭐ | **零** | **日常开发、生产环境** |
| spec 文件 | ⭐⭐ | 高 | 需要特殊配置 |
| 手动命令 | ⭐ | 高 | 快速测试 |

**推荐工作流**：
1. 开发阶段：使用 `uv run python -m ptk_repl`
2. 打包发布：使用 `uv run python scripts/build_ptk_repl.py`
3. **添加新模块：只需创建模块目录，无需修改配置文件！**

## 优势

使用自动打包脚本的好处：

✅ **零维护**：添加新模块无需修改任何配置
✅ **自动化**：自动发现所有模块
✅ **可靠**：不会因为忘记更新配置而漏掉模块
✅ **简单**：一个命令完成打包
✅ **开发者友好**：专注于开发，不用关心打包细节
