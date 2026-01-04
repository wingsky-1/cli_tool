"""PTK_REPL 入口点。

运行方式: python -m ptk_repl
"""

# ruff: noqa: I001  # 允许自定义导入顺序（_pyinstaller 必须在最先）

# 导入 PyInstaller 运行时配置（必须在其他导入之前）
from ptk_repl import _pyinstaller  # noqa: F401  # 设置环境变量

from ptk_repl.cli import PromptToolkitCLI


def main() -> None:
    """主入口点。"""
    cli = PromptToolkitCLI()
    cli.run()


if __name__ == "__main__":
    main()
