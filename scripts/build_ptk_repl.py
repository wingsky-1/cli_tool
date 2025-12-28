"""自动发现并打包 ptk_repl 的脚本。

自动扫描 modules 目录并生成 PyInstaller 命令。
"""

import os
import subprocess
import sys
from pathlib import Path


def discover_modules():
    """自动发现所有模块。"""
    modules_dir = Path(__file__).parent / "src" / "ptk_repl" / "modules"
    modules = []

    for item in modules_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            modules.append(item.name)

    return modules


def build_hidden_imports(modules):
    """生成 hidden-import 列表。"""
    imports = []

    # 核心依赖
    core_imports = [
        "prompt_toolkit",
        "prompt_toolkit.completion",
        "prompt_toolkit.history",
        "prompt_toolkit.styles",
        "pydantic",
        "yaml",
    ]
    imports.extend(core_imports)

    # 基础模块
    base_imports = [
        "ptk_repl.core",
        "ptk_repl.core.base",
        "ptk_repl.core.registry",
        "ptk_repl.core.completer",
        "ptk_repl.core.state_manager",
        "ptk_repl.core.config_manager",
        "ptk_repl.core.decorators",
        "ptk_repl.state",
        "ptk_repl.state.global_state",
        "ptk_repl.state.module_state",
    ]
    imports.extend(base_imports)

    # 动态发现的模块
    for module in modules:
        imports.append(f"ptk_repl.modules.{module}")
        imports.append(f"ptk_repl.modules.{module}.module")

        # 检查是否有 state.py
        state_file = Path(__file__).parent / "src" / "ptk_repl" / "modules" / module / "state.py"
        if state_file.exists():
            imports.append(f"ptk_repl.modules.{module}.state")

    return imports


def build_command(hidden_imports):
    """构建 PyInstaller 命令。"""
    cmd = [
        "pyinstaller",
        "--name=ptk_repl",
        "--console",
        "--onefile",  # 打包成单个文件
    ]

    # 添加 hidden-import
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # 入口点
    cmd.append("src/ptk_repl/__main__.py")

    return cmd


def main():
    """主函数。"""
    print("=" * 60)
    print("PTK_REPL 自动打包脚本")
    print("=" * 60)
    print()

    # 发现模块
    modules = discover_modules()
    print(f"发现的模块: {modules}")
    print()

    # 生成 hidden-imports
    hidden_imports = build_hidden_imports(modules)
    print(f"生成的 hidden-imports ({len(hidden_imports)} 项):")
    for imp in hidden_imports:
        print(f"  - {imp}")
    print()

    # 构建命令
    cmd = build_command(hidden_imports)
    print("PyInstaller 命令:")
    print(" ".join(cmd))
    print()

    # 执行
    print("=" * 60)
    print("开始打包...")
    print("=" * 60)
    print()

    result = subprocess.run(cmd, check=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
