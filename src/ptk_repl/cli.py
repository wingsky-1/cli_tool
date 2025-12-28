"""基于 prompt_toolkit 的模块化 CLI 主类。"""

import shlex
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import Style

from ptk_repl.core.completer import AutoCompleter
from ptk_repl.core.config_manager import ConfigManager
from ptk_repl.core.registry import CommandRegistry
from ptk_repl.core.state_manager import StateManager

if TYPE_CHECKING:
    from ptk_repl.core.base import CommandModule


class PromptToolkitCLI:
    """基于 prompt_toolkit 的模块化 CLI。

    使用 AutoCompleter 自动发现命令并提供补全。
    """

    def __init__(self, config_path: str | None = None, history_path: str | None = None) -> None:
        """初始化 CLI。

        Args:
            config_path: 配置文件路径（可选）
            history_path: 历史记录文件路径（可选）
        """
        # 初始化核心组件
        self.config = ConfigManager(config_path)
        self.state = StateManager()
        self.registry = CommandRegistry()

        # PromptSession 配置
        self.history_path = history_path or Path.home() / ".ptk_repl_history"
        self.session: PromptSession[str] = PromptSession(
            history=FileHistory(str(self.history_path)),
            style=self._create_style(),
            completer=NestedCompleter.from_nested_dict({}),  # 初始为空
            enable_history_search=False,  # 禁用历史搜索（与实时补全冲突）
            complete_while_typing=True,  # 实时补全
            complete_in_thread=True,  # 在后台线程中补全（避免阻塞）
            complete_style=CompleteStyle.COLUMN,  # 多列菜单显示（在下方展示候选项）
        )

        # 初始化自动补全器
        self.auto_completer = AutoCompleter(self.registry)
        self.registry.set_completer(self.auto_completer)
        self.session.completer = self.auto_completer.to_prompt_toolkit_completer()

        # 懒加载支持
        self._lazy_modules: dict[str, type] = {}
        self._loaded_modules: set[str] = set()

        # 命令注册上下文
        self._current_module: str | None = None

        # 加载核心模块
        self._load_modules()
        self._update_completer()

    def _create_style(self) -> Style:
        """创建 CLI 样式。

        Returns:
            Style 对象
        """
        return Style.from_dict(
            {
                "prompt": "ansigreen bold",
                # 补全菜单样式
                "completion-menu.completion": "bg:#008888 #ffffff",
                "completion-menu.completion.current": "bg:#00aaaa #000000",
                # 滚动条样式（增强视觉效果）
                "scrollbar.background": "bg:#88aaaa",
                "scrollbar.button": "bg:#222222",
                "scrollbar.arrow": "bg:#00aaaa #000000",
            }
        )

    def _get_prompt(self) -> str:
        """动态生成提示符。

        Returns:
            提示符字符串
        """
        gs = self.state.global_state
        if gs.connected:
            if gs.connection_type == "ssh" and gs.current_ssh_env:
                # SSH 连接：显示环境名称
                return f"(ptk:{gs.current_ssh_env}) > "
            elif gs.connection_type == "database" and gs.current_host:
                # Database 连接：显示主机和端口
                return f"(ptk:{gs.current_host}:{gs.current_port}) > "
            elif gs.current_host:
                # 兼容旧版本：显示主机和端口
                return f"(ptk:{gs.current_host}:{gs.current_port}) > "
        return "(ptk) > "

    def _load_modules(self) -> None:
        """加载模块（core 立即加载，其他根据配置预加载或懒加载）。"""
        # 1. 自动发现所有可用模块并注册到懒加载系统
        self._discover_all_modules()

        # 2. Core 模块总是立即加载
        self._load_module_immediately("core")

        # 3. 从配置获取预加载模块列表
        preload_modules = self.config.get("core.preload_modules", [])

        # 4. 预加载配置中指定的模块
        for module_name in preload_modules:
            if module_name != "core" and module_name not in self._loaded_modules:
                self._load_module_immediately(module_name)

    def _discover_all_modules(self) -> None:
        """自动发现所有可用模块并注册到懒加载系统。"""
        import importlib
        import pkgutil

        try:
            # 导入 modules 包
            modules_package = importlib.import_module("ptk_repl.modules")

            # 遍历 modules 包中的所有模块
            for _, module_name, _ in pkgutil.iter_modules(modules_package.__path__):
                # 跳过 core 模块（它会被立即加载）
                if module_name == "core":
                    continue

                # 跳过已经在懒加载列表中的模块
                if module_name in self._lazy_modules:
                    continue

                # 预加载模块（添加到 _lazy_modules）
                self._preload_module(module_name)
        except Exception as e:
            self.perror(f"发现模块失败: {e}")

    def _load_module_immediately(self, module_name: str) -> None:
        """立即加载模块。

        Args:
            module_name: 模块名称
        """
        if module_name == "core":
            from ptk_repl.modules.core.module import CoreModule

            module = CoreModule()
            self.registry.register_module(module)
            module.initialize(self.state)
            self.register_module_commands(module)
            self._loaded_modules.add(module_name)
        else:
            # 加载其他模块
            # 如果模块已经在 _lazy_modules 中，直接使用
            if module_name in self._lazy_modules:
                module_cls = self._lazy_modules[module_name]
                module = module_cls()
                self.registry.register_module(module)
                module.initialize(self.state)
                self.register_module_commands(module)
                self._loaded_modules.add(module_name)
                del self._lazy_modules[module_name]
            else:
                # 否则，先导入模块再加载
                import importlib

                try:
                    module_path = f"ptk_repl.modules.{module_name}"
                    mod = importlib.import_module(module_path)

                    # 特殊模块名称映射（处理缩写词）
                    special_casing = {"ssh": "SSH"}
                    class_name_prefix = special_casing.get(module_name, module_name.capitalize())
                    module_cls = getattr(mod, f"{class_name_prefix}Module")
                    module = module_cls()
                    self.registry.register_module(module)
                    module.initialize(self.state)
                    self.register_module_commands(module)
                    self._loaded_modules.add(module_name)
                except Exception as e:
                    self.perror(f"加载��块 '{module_name}' 失败: {e}")

    def _preload_module(self, module_name: str) -> None:
        """预加载模块（懒加载）。

        Args:
            module_name: 模块名称
        """
        import importlib

        try:
            module_path = f"ptk_repl.modules.{module_name}"
            mod = importlib.import_module(module_path)

            # 特殊模块名称映射（处理缩写词）
            special_casing = {"ssh": "SSH"}
            class_name_prefix = special_casing.get(module_name, module_name.capitalize())
            module_cls = getattr(mod, f"{class_name_prefix}Module")

            self._lazy_modules[module_name] = module_cls
        except Exception as e:
            self.perror(f"预加载模块 '{module_name}' 失败: {e}")

    def _update_completer(self) -> None:
        """更新补全器（动态）。"""
        self.auto_completer._invalidate_cache()

    def _ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载。

        Args:
            module_name: 模块名称
        """
        if module_name in self._loaded_modules:
            return

        if module_name in self._lazy_modules:
            module_cls = self._lazy_modules[module_name]
            module = module_cls()
            self.registry.register_module(module)
            module.initialize(self.state)
            self.register_module_commands(module)
            self._loaded_modules.add(module_name)
            del self._lazy_modules[module_name]
            self._update_completer()

    def run(self) -> None:
        """运行 REPL 主循环。"""
        self._print_welcome()

        while True:
            try:
                user_input = self.session.prompt(self._get_prompt())
                if not user_input.strip():
                    continue

                self._execute_command(user_input)

            except KeyboardInterrupt:
                self._print_info("\n使用 'exit' 或 Ctrl+D 退出")
                continue
            except EOFError:
                self._print_info("\n再见!")
                break
            except Exception as e:
                self.perror(f"错误: {e}")

    def _execute_command(self, command_str: str) -> None:
        """执行命令。

        Args:
            command_str: 命令字符串
        """
        tokens = shlex.split(command_str)
        if not tokens:
            return

        # 解析命令
        cmd_info = self.registry.get_command_info(command_str)
        if cmd_info:
            module_name, command_name, handler = cmd_info

            # 懒加载检查
            if module_name not in self._loaded_modules:
                self._ensure_module_loaded(module_name)

            # 计算参数部分
            if module_name == "core":
                # core 命令: status -> tokens[0]
                # 参数: tokens[1:]
                remaining = " ".join(tokens[1:]) if len(tokens) > 1 else ""
            else:
                # 模块命令: database query -> tokens[0:2]
                # 参数: tokens[2:]
                remaining = " ".join(tokens[2:]) if len(tokens) > 2 else ""

            # 调用处理器
            if getattr(handler, "_is_typed_wrapper", False):
                # typed_command 处理
                handler(self, remaining)  # 传递 (cli, args_str)
            else:
                # 普通命令处理
                handler(remaining)
        else:
            # 检查是否是模块名/别名
            if len(tokens) == 1:
                # 1. 尝试从已加载模块的注册表查找
                module = self.registry.get_module(tokens[0])
                if module:
                    # 触发懒加载并显示帮助（虽然已经在 registry 中）
                    if module.name not in self._loaded_modules:
                        self._ensure_module_loaded(module.name)

                    commands = self.registry.list_module_commands(module.name)
                    self.poutput(f"{module.name} 模块 - {module.description}")
                    self.poutput("\n可用命令:")
                    for cmd in commands:
                        if module.name == "core":
                            full_cmd = cmd
                        else:
                            full_cmd = f"{module.name} {cmd}"
                        self.poutput(f"  • {full_cmd}")
                    return

                # 2. 尝试从懒加载模块中查找（通过别名）
                for module_name, module_cls in self._lazy_modules.items():
                    # 创建临时模块实例来检查别名
                    temp_module = module_cls()
                    if hasattr(temp_module, "aliases") and tokens[0] in temp_module.aliases:
                        # 找到了！触发懒加载
                        self._ensure_module_loaded(module_name)

                        # 重新从 registry 获取模块（现在已加载）
                        module = self.registry.get_module(module_name)
                        if module:
                            commands = self.registry.list_module_commands(module_name)
                            self.poutput(f"{module.name} 模块 - {module.description}")
                            self.poutput("\n可用命令:")
                            for cmd in commands:
                                if module_name == "core":
                                    full_cmd = cmd
                                else:
                                    full_cmd = f"{module_name} {cmd}"
                                self.poutput(f"  • {full_cmd}")
                        return

            self.perror(f"未知命令: {tokens[0]}")

    def register_command(
        self,
        module_name: str,
        command_name: str,
        handler: Callable,
        aliases: list[str] | None = None,
    ) -> None:
        """注册命令。

        Args:
            module_name: 模块名称
            command_name: 命令名称
            handler: 命令处理函数
            aliases: 命令别名列表（可选）
        """
        self.registry.register_command(module_name, command_name, handler, aliases)
        self._update_completer()

    def command(
        self,
        name: str | None = None,
        alias: str | list[str] | None = None,
        module: str | None = None,
    ) -> Callable[[Callable], Callable]:
        """命令装饰器工厂。

        提供优雅的命令注册方式，替代手动调用 register_command()。
        命令名称默认从函数名获取。

        Args:
            name: 命令名称（可选，默认使用函数名）
            alias: 命令别名（字符串或列表，可选）
            module: 模块名称（可选，默认使用当前注册的模块）

        Returns:
            装饰器函数

        Example:
            >>> # 使用函数名作为命令名
            >>> @cli.command()
            >>> def status(args: str) -> None:
            ...     '''显示当前状态。'''
            ...     cli.poutput("状态")
            >>>
            >>> # 指定命令名（避免与内置函数冲突）
            >>> @cli.command(name="exit")
            >>> def do_exit(args: str) -> None:
            ...     '''退出 REPL。'''
            ...     cli.poutput("再见!")
            >>>
            >>> # 命令名 + 别名
            >>> @cli.command(name="help", alias=["h", "?"])
            >>> def do_help(args: str) -> None:
            ...     '''显示帮助。'''
            ...     cli.poutput("帮助")
        """

        def decorator(func: Callable) -> Callable:
            # 使用指定的 name 或从函数名获取
            command_name = name or func.__name__

            # 如果没有指定模块，使用当前注册的模块
            module_name = module or self._current_module

            if module_name is None:
                raise ValueError(
                    "无法确定模块名。请显式指定 module 参数，"
                    "或确保在 register_commands() 上下文中使用此装饰器。"
                )

            # 获取模块实例
            module_instance = self.registry.get_module(module_name)
            if not module_instance:
                raise ValueError(f"未找到模块: {module_name}")

            # 标准化 alias 参数为列表
            command_aliases: list[str] = []
            if isinstance(alias, str):
                command_aliases = [alias]
            elif isinstance(alias, list):
                command_aliases = alias
            elif alias is not None:
                raise TypeError("alias 参数必须是字符串或列表")

            # 构建完整的别名列表
            all_aliases: list[str] = []

            # 1. 添加命令自身的别名（手动指定的）
            if command_aliases:
                all_aliases.extend(command_aliases)

            # 2. 自动生成：模块别名 + 命令名
            if hasattr(module_instance, "aliases") and module_instance.aliases:
                for module_alias in module_instance.aliases:
                    # 对于 core 模块，只使用命令名
                    if module_name == "core":
                        combined = command_name
                    else:
                        combined = f"{module_alias} {command_name}"

                    # 避免重复添加
                    if combined not in all_aliases:
                        all_aliases.append(combined)

            # 注册命令（包含所有别名）
            self.register_command(module_name, command_name, func, all_aliases)

            # 自动注册到补全系统（替代 get_completion_commands）
            self.auto_completer.register_lazy_commands(module_name, [command_name])

            return func

        return decorator

    def register_module_commands(self, module: "CommandModule") -> None:
        """注册模块的所有命令（带上下文管理）。

        这个方法会设置当前模块上下文，使得 @cli.command 装饰器
        可以自动使用当前模块名。

        Args:
            module: 命令模块实例

        Example:
            >>> class DatabaseModule(CommandModule):
            ...     def register_commands(self, cli):
            ...         @cli.command("connect", aliases=["conn"])
            ...         def connect(args: str):
            ...             '''连接到数据库。'''
            ...             cli.poutput("已连接")
        """

        # 设置当前模块上下文
        self._current_module = module.name

        try:
            # 调用模块的注册方法
            module.register_commands(self)
        finally:
            # 清除模块上下文
            self._current_module = None

    def poutput(self, text: str) -> None:
        """输出信息。

        Args:
            text: 输出文本
        """
        print(text)

    def perror(self, text: str) -> None:
        """输出错误。

        Args:
            text: 错误文本
        """
        print(f"[错误] {text}")

    def _print_welcome(self) -> None:
        """打印欢迎信息。"""
        from colorama import Fore, Style, init
        from pyfiglet import Figlet

        # 初始化 colorama（Windows 需要）
        init(autoreset=True)

        # 创建 Figlet 对象
        f = Figlet(font="block")  # 其他流行字体: 'banner', 'block', 'bubble', 'digital'

        # 生成 ASCII 艺术字
        cli_art = f.renderText("CLI TOOL")

        # 打印彩色横幅
        print(f"{Fore.LIGHTBLUE_EX}{cli_art}{Style.RESET_ALL}")

        # 欢迎信息
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  📖 输入 'help' 查看帮助{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  🚀 输入 'modules' 查看可用模块{Style.RESET_ALL}")
        print(f"{Fore.WHITE}  ❌ 输入 'exit' 或按 Ctrl+D 退出{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")

    def _print_info(self, text: str) -> None:
        """打印信息。

        Args:
            text: 信息文本
        """
        print(text)
