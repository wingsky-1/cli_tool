"""PTK_REPL 入口点。

运行方式: python -m ptk_repl
"""

from ptk_repl.cli import PromptToolkitCLI


def main() -> None:
    """主入口点。"""
    cli = PromptToolkitCLI()
    cli.run()


if __name__ == "__main__":
    main()
