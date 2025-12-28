"""命令执行器。"""

import shlex
from collections.abc import Callable
from typing import TYPE_CHECKING

from ptk_repl.core.registry import CommandRegistry

if TYPE_CHECKING:
    from ptk_repl.core.cli.module_loader import ModuleLoader


class CommandExecutor:
    """命令执行器。

    负责解析和执行用户输入的命令。
    """

    def __init__(
        self,
        registry: CommandRegistry,
        module_loader: "ModuleLoader",
        output_callback: Callable[[str], None],
        error_callback: Callable[[str], None],
    ) -> None:
        """初始化命令执行器。

        Args:
            registry: 命令注册表
            module_loader: 模块加载器
            output_callback: 输出回调函数
            error_callback: 错误回调函数
        """
        self.registry = registry
        self.module_loader = module_loader
        self.output_callback = output_callback
        self.error_callback = error_callback

    def execute(self, command_str: str) -> None:
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
            if module_name not in self.module_loader.loaded_modules:
                self.module_loader.ensure_module_loaded(module_name)

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
                # handler 期望 (cli, args_str)
                # 由于我们无法直接传递 cli，这里需要调整
                # 暂时保持原样，需要在主类中处理
                handler(self._get_cli_context(), remaining)
            else:
                # 普通命令处理
                handler(remaining)
        else:
            # 检查是否是模块名/别名
            if len(tokens) == 1:
                self._handle_module_only(tokens[0])
            else:
                self.error_callback(f"未知命令: {tokens[0]}")

    def _handle_module_only(self, module_name: str) -> None:
        """处理仅输入模块名的情况。

        Args:
            module_name: 模块名称或别名
        """
        # 1. 尝试从已加载模块的注册表查找
        module = self.registry.get_module(module_name)
        if module:
            # 触发懒加载并显示帮助（虽然已经在 registry 中）
            if module.name not in self.module_loader.loaded_modules:
                self.module_loader.ensure_module_loaded(module.name)

            commands = self.registry.list_module_commands(module.name)
            self.output_callback(f"{module.name} 模块 - {module.description}")
            self.output_callback("\n可用命令:")
            for cmd in commands:
                if module.name == "core":
                    full_cmd = cmd
                else:
                    full_cmd = f"{module.name} {cmd}"
                self.output_callback(f"  • {full_cmd}")
            return

        # 2. 尝试从懒加载模块中查找（通过别名）
        for lazy_module_name, module_cls in self.module_loader.lazy_modules.items():
            # 创建临时模块实例来检查别名
            temp_module = module_cls()
            if hasattr(temp_module, "aliases") and module_name in temp_module.aliases:
                # 找到了！触发懒加载
                self.module_loader.ensure_module_loaded(lazy_module_name)

                # 重新从 registry 获取模块（现在已加载）
                module = self.registry.get_module(lazy_module_name)
                if module:
                    commands = self.registry.list_module_commands(lazy_module_name)
                    self.output_callback(f"{module.name} 模块 - {module.description}")
                    self.output_callback("\n可用命令:")
                    for cmd in commands:
                        if lazy_module_name == "core":
                            full_cmd = cmd
                        else:
                            full_cmd = f"{lazy_module_name} {cmd}"
                        self.output_callback(f"  • {full_cmd}")
                return

        self.error_callback(f"未知命令: {module_name}")

    def _get_cli_context(self) -> object:
        """获取 CLI 上下文对象。

        Returns:
            CLI 上下文对象（用于传递给命令处理器）

        注意：
            这是一个临时方法，实际实现需要更复杂的设计。
            目前返回一个简单的对象，包含必要的方法。
        """

        # 创建一个简单的上下文对象
        class CLIContext:
            def __init__(self, output_cb: Callable, error_cb: Callable):
                self.poutput = output_cb
                self.perror = error_cb

        return CLIContext(self.output_callback, self.error_callback)
