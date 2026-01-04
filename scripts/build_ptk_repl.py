"""自动发现并打包 ptk_repl 的脚本。

自动扫描 modules 目录并生成 PyInstaller 命令。
"""

import os
import subprocess
import sys
from pathlib import Path


def discover_modules():
    """自动发现所有模块（包括子模块）。"""
    base_dir = Path(__file__).parent.parent
    modules_dir = base_dir / "src" / "ptk_repl" / "modules"
    modules = []

    for item in modules_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            modules.append(item.name)

            # 递归发现子模块
            for subitem in item.iterdir():
                if subitem.is_dir() and not subitem.name.startswith("_"):
                    modules.append(f"{item.name}.{subitem.name}")

    return modules


def build_hidden_imports(modules):
    """生成 hidden-import 列表。"""
    imports = []

    # 核心依赖
    core_imports = [
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
        "pydantic",
        "pydantic_core",
        "pydantic_core.core_schema",
        "yaml",
        "pyfiglet",
        "questionary",
        "questionary.formats",
        "questionary.prompts",
        "questionary.themes",
        "colorama",
        "paramiko",
        "paramiko.auth_handler",
        "paramiko.client",
        "paramiko.config",
        "paramiko.hostkeys",
        "paramiko.ssh_exception",
        "paramiko.transport",
    ]
    imports.extend(core_imports)

    # 基础模块
    base_imports = [
        "ptk_repl.core",
        "ptk_repl.core.base",
        "ptk_repl.core.base.command_module",
        "ptk_repl.core.cli",
        "ptk_repl.core.cli.style_manager",
        "ptk_repl.core.completion",
        "ptk_repl.core.completion.auto_completer",
        "ptk_repl.core.completion.fuzzy_matcher",  # 新增
        "ptk_repl.core.configuration",
        "ptk_repl.core.configuration.config_manager",
        "ptk_repl.core.decoration",
        "ptk_repl.core.decoration.typed_command",
        "ptk_repl.core.error_handling",
        "ptk_repl.core.error_handling.error_handlers",
        "ptk_repl.core.exceptions",
        "ptk_repl.core.exceptions.cli_exceptions",
        "ptk_repl.core.execution",
        "ptk_repl.core.execution.command_executor",
        "ptk_repl.core.formatting",
        "ptk_repl.core.formatting.help_formatter",
        "ptk_repl.core.interfaces",
        "ptk_repl.core.interfaces.cli_context",
        "ptk_repl.core.interfaces.command_resolver",
        "ptk_repl.core.interfaces.module_discoverer",
        "ptk_repl.core.interfaces.module_loader",
        "ptk_repl.core.interfaces.module_register",
        "ptk_repl.core.interfaces.prompt_provider",
        "ptk_repl.core.interfaces.registry",
        "ptk_repl.core.loaders",
        "ptk_repl.core.loaders.lazy_module_tracker",
        "ptk_repl.core.loaders.module_discoverer",
        "ptk_repl.core.loaders.module_discovery_service",
        "ptk_repl.core.loaders.module_lifecycle_manager",
        "ptk_repl.core.loaders.module_register",
        "ptk_repl.core.loaders.unified_module_loader",
        "ptk_repl.core.prompts",
        "ptk_repl.core.prompts.prompt_provider",
        "ptk_repl.core.registry",
        "ptk_repl.core.registry.command_registry",
        "ptk_repl.core.resolvers",
        "ptk_repl.core.resolvers.module_name_resolver",
        "ptk_repl.core.state",
        "ptk_repl.core.state.state_manager",
        "ptk_repl.state",
        "ptk_repl.state.connection_context",
        "ptk_repl.state.global_state",
        "ptk_repl.state.module_state",
    ]
    imports.extend(base_imports)

    # 动态发现的模块
    for module in modules:
        if "." in module:
            # 子模块
            imports.append(f"ptk_repl.modules.{module}")
        else:
            # 顶层模块
            imports.append(f"ptk_repl.modules.{module}")
            imports.append(f"ptk_repl.modules.{module}.module")

            # 检查是否有 state.py
            base_dir = Path(__file__).parent.parent
            state_file = base_dir / "src" / "ptk_repl" / "modules" / module / "state.py"
            if state_file.exists():
                imports.append(f"ptk_repl.modules.{module}.state")

    # SSH 模块的特殊导入
    ssh_imports = [
        "ptk_repl.modules.ssh.config",
        "ptk_repl.modules.ssh.connection",
        "ptk_repl.modules.ssh.dialogs",
        "ptk_repl.modules.ssh.log_viewer",
        "ptk_repl.modules.ssh.ssh_client",
        "ptk_repl.modules.ssh.tail",  # 新增
        "ptk_repl.modules.ssh.state",
    ]
    imports.extend(ssh_imports)

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
