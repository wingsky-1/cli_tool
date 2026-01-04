"""自动发现并打包 ptk_repl 的脚本（增强版）。

自动扫描所有依赖和子模块，确保打包完整性。
"""

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


def discover_core_submodules():
    """扫描所有核心框架子模块。"""
    core_dir = Path(__file__).parent / "src" / "ptk_repl" / "core"
    submodules = []

    for item in core_dir.iterdir():
        if item.is_dir() and not item.name.startswith("__"):
            # 扫描子目录中的 Python 文件
            for py_file in item.glob("*.py"):
                if py_file.stem != "__init__":
                    module_path = f"ptk_repl.core.{item.name}.{py_file.stem}"
                    submodules.append(module_path)
            # 添加包本身
            module_path = f"ptk_repl.core.{item.name}"
            submodules.append(module_path)

    return submodules


def discover_module_submodules(module_name: str) -> list[str]:
    """扫描特定模块的所有子文件。"""
    module_dir = Path(__file__).parent / "src" / "ptk_repl" / "modules" / module_name
    submodules: list[str] = []

    if not module_dir.exists():
        return submodules

    # 扫描所有 .py 文件
    for py_file in module_dir.glob("*.py"):
        if py_file.stem != "__init__":
            module_path = f"ptk_repl.modules.{module_name}.{py_file.stem}"
            submodules.append(module_path)

    return submodules


def build_hidden_imports(modules):
    """生成完整的 hidden-imports 列表。"""
    imports = []

    # 1. 第三方库及其子模块
    third_party_libs = [
        # prompt_toolkit
        "prompt_toolkit",
        "prompt_toolkit.completion",
        "prompt_toolkit.completion.fuzzy_matcher",
        "prompt_toolkit.document",
        "prompt_toolkit.filters",
        "prompt_toolkit.formatted_text",
        "prompt_toolkit.history",
        "prompt_toolkit.key_binding",
        "prompt_toolkit.layout",
        "prompt_toolkit.lexers",
        "prompt_toolkit.styles",
        "prompt_toolkit.validation",
        # pydantic
        "pydantic",
        "pydantic_core",
        "pydantic_core.core_schema",
        # paramiko (SSH 库)
        "paramiko",
        "paramiko.auth_handler",
        "paramiko.client",
        "paramiko.config",
        "paramiko.hostkeys",
        "paramiko.ssh_exception",
        "paramiko.transport",
        # questionary (交互式提示)
        "questionary",
        "questionary.prompts",
        "questionary.formats",
        "questionary.themes",
        # 其他
        "yaml",
        "colorama",
        "pyfiglet",
    ]
    imports.extend(third_party_libs)

    # 2. 核心框架子模块（自动发现）
    core_submodules = discover_core_submodules()
    imports.extend(core_submodules)

    # 3. 状态管理
    state_imports = [
        "ptk_repl.state",
        "ptk_repl.state.global_state",
        "ptk_repl.state.module_state",
        "ptk_repl.state.connection_context",
    ]
    imports.extend(state_imports)

    # 4. 所有模块（动态发现）
    for module in modules:
        # 模块包
        imports.append(f"ptk_repl.modules.{module}")

        # module.py
        module_file = Path(__file__).parent / "src" / "ptk_repl" / "modules" / module / "module.py"
        if module_file.exists():
            imports.append(f"ptk_repl.modules.{module}.module")

        # state.py（如果存在）
        state_file = Path(__file__).parent / "src" / "ptk_repl" / "modules" / module / "state.py"
        if state_file.exists():
            imports.append(f"ptk_repl.modules.{module}.state")

        # 扫描模块的所有子文件（如 tail.py, log_viewer.py 等）
        module_submodules = discover_module_submodules(module)
        imports.extend(module_submodules)

    # 5. 接口模块
    interface_imports = [
        "ptk_repl.core.interfaces",
        "ptk_repl.core.interfaces.cli_context",
        "ptk_repl.core.interfaces.module_loader",
        "ptk_repl.core.interfaces.registry",
        "ptk_repl.core.interfaces.prompt_provider",
    ]
    imports.extend(interface_imports)

    return sorted(set(imports))  # 去重并排序


def build_pyinstaller_command(hidden_imports):
    """构建 PyInstaller 命令。"""
    cmd = [
        "pyinstaller",
        "--name=ptk_repl",
        "--console",
        "--onefile",
        "--clean",  # 清理缓存
    ]

    # 添加 hidden-import
    for imp in hidden_imports:
        cmd.append(f"--hidden-import={imp}")

    # 收集整个包（避免遗漏）
    cmd.append("--collect-all=ptk_repl")

    # 入口点
    cmd.append("src/ptk_repl/__main__.py")

    return cmd


def main():
    """主函数。"""
    print("=" * 70)
    print("PTK_REPL 自动打包脚本 (增强版)")
    print("=" * 70)
    print()

    # 发现所有模块
    modules = discover_modules()
    print(f"发现的模块: {modules}")
    print()

    # 生成 hidden-imports
    hidden_imports = build_hidden_imports(modules)
    print(f"生成的 hidden-imports ({len(hidden_imports)} 项):")
    for imp in hidden_imports[:20]:  # 显示前20个
        print(f"  - {imp}")
    if len(hidden_imports) > 20:
        print(f"  ... 还有 {len(hidden_imports) - 20} 项")
    print()

    # 构建命令
    cmd = build_pyinstaller_command(hidden_imports)
    print("PyInstaller 命令:")
    print(" ".join(cmd[:10]) + " ...")  # 显示前10个参数
    print()

    # 执行打包
    print("=" * 70)
    print("开始打包...")
    print("=" * 70)
    print()

    try:
        subprocess.run(cmd, check=True, capture_output=False, text=True)
        print()
        print("=" * 70)
        print("✅ 打包成功!")
        print("=" * 70)
        print()
        print("可执行文件位置: dist/ptk_repl.exe")
        return 0
    except subprocess.CalledProcessError as e:
        print()
        print("=" * 70)
        print("❌ 打包失败!")
        print("=" * 70)
        print()
        print("错误输出:")
        print(e.stdout if e.stdout else "无输出")
        print(e.stderr if e.stderr else "无输出")
        return 1


if __name__ == "__main__":
    sys.exit(main())
