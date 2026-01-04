"""核心命令模块。"""

from typing import TYPE_CHECKING

from ptk_repl.core.base import CommandModule
from ptk_repl.core.formatting.help_formatter import HelpFormatter

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI


class CoreModule(CommandModule):
    """核心命令模块。"""

    @property
    def name(self) -> str:
        """模块名称。"""
        return "core"

    @property
    def description(self) -> str:
        """模块描述。"""
        return "核心命令（状态、帮助、退出等）"

    @property
    def aliases(self) -> str | None:
        """模块短别名。"""
        return None  # 核心模块不需要别名

    def register_commands(self, cli: "PromptToolkitCLI") -> None:
        """注册核心命令。

        Args:
            cli: PromptToolkitCLI 实例
        """
        # 创建帮助格式化器
        help_formatter = HelpFormatter(cli)

        # 使用装饰器注册命令（更优雅的方式）
        @cli.command()
        def status(args: str) -> None:
            """显示当前状态。"""
            state = cli.state.global_state
            if state.connected:
                cli.poutput(f"已连接到 {state.current_host}:{state.current_port}")
            else:
                cli.poutput("未连接")

        @cli.command(name="exit")
        def do_exit(args: str) -> None:
            """退出 REPL。"""
            cli.poutput("再见!")
            raise EOFError

        @cli.command(name="quit")
        def do_quit(args: str) -> None:
            """退出 REPL（exit 的别名）。"""
            cli.poutput("再见!")
            raise EOFError

        @cli.command()
        def modules(args: str) -> None:
            """列出所有已加载的模块。"""
            cli.poutput("已加载的模块:")
            for module in cli.registry.list_modules():
                version = module.version
                description = module.description or "无描述"
                cli.poutput(f"  • {module.name} (v{version}): {description}")

            # 显示待加载的模块
            lazy_modules = cli._module_manager.lazy_modules
            if lazy_modules:
                cli.poutput("\n待加载（延迟）:")
                for module_name in lazy_modules:
                    cli.poutput(f"  • {module_name} (首次使用时加载)")

        @cli.command(name="help")
        def do_help(args: str) -> None:
            """显示帮助信息。

            支持以下用法：
            - help              显示总览帮助
            - help <command>    显示命令详细帮助
            - help <module>     显示模块所有命令
            """
            # 如果没有参数，显示总览帮助
            if not args.strip():
                cli.poutput(help_formatter.format_overview_help())
                return

            # 解析参数
            parts = args.strip().split()

            # 尝试解析为命令
            cmd_info = cli.registry.get_command_info(args.strip())

            if cmd_info:
                # 是一个完整命令
                module_name, command_name, _ = cmd_info
                cli.poutput(help_formatter.format_command_help(module_name, command_name))
                return

            # 尝试解析为模块
            if len(parts) == 1:
                module = cli.registry.get_module(parts[0])
                if module:
                    cli.poutput(help_formatter.format_module_help(parts[0]))
                    return

            # 未找到
            cli.poutput(f"未找到命令或模块: {args.strip()}")
            cli.poutput("\n提示:")
            cli.poutput("  • 使用 'help' 查看总览帮助")
            cli.poutput("  • 使用 'help <command>' 查看命令帮助")
            cli.poutput("  • 使用 'help <module>' 查看模块帮助")

        @cli.command()
        def use(args: str) -> None:
            """切换到指定模块上下文。

            用法：
                use <module>    切换到指定模块
                use core       返回全局模式

            示例：
                use ssh        切换到 SSH 模块，之后可直接输入 env, tail 等命令
                use core       返回全局模式，需要输入完整命令（如 ssh env）

            当前模块：
                输入 use（不带参数）可查看当前模块
            """
            if not args.strip():
                # 显示当前模块
                current = cli.state.global_state.get_active_module()
                if current:
                    cli.poutput(f"当前模块: {current}")
                    cli.poutput("提示：直接输入命令将自动匹配该模块的命令")
                    cli.poutput("      输入 'use core' 返回全局模式")
                else:
                    cli.poutput("当前模式: 全局")
                    cli.poutput("提示：输入完整命令（如 'ssh env'）或使用 'use <module>' 切换模块")
                return

            module_name = args.strip()

            # 特殊处理：返回全局模式
            if module_name == "core":
                cli.state.global_state.set_active_module(None)
                cli.poutput("已返回全局模式")
                return

            # 验证模块是否存在
            module = cli.registry.get_module(module_name)
            if not module:
                cli.perror(f"未知模块: {module_name}")
                cli.poutput("可用模块:")
                for m in cli.registry.list_modules():
                    if m.name != "core":
                        cli.poutput(f"  • {m.name}")
                return

            # 切换模块
            cli.state.global_state.set_active_module(module_name)
            cli.poutput(f"已切换到 {module_name} 模块")
            cli.poutput(f"提示：现在可以直接输入 {module_name} 的命令（如 env, tail）")
            cli.poutput("      输入 'use core' 返回全局模式")
