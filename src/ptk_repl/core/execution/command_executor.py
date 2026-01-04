"""命令执行器。"""

import shlex
from typing import TYPE_CHECKING

from ptk_repl.core.interfaces.cli_context import ICliContext
from ptk_repl.core.interfaces.module_loader import IModuleLoader
from ptk_repl.core.registry import CommandRegistry

if TYPE_CHECKING:
    pass


class CommandExecutor:
    """命令执行器。

    负责解析和执行用户输入的命令。

    现在使用 IModuleLoader 接口，符合依赖倒置原则（DIP）。
    """

    def __init__(
        self,
        registry: CommandRegistry,
        module_loader: "IModuleLoader",
        cli_context: ICliContext,
    ) -> None:
        """初始化命令执行器。

        Args:
            registry: 命令注册表
            module_loader: 模块加载器接口
            cli_context: CLI 上下文对象
        """
        self._registry = registry
        self._module_loader = module_loader
        self._cli_context = cli_context

    def execute(self, command_str: str) -> None:
        """执行命令。

        Args:
            command_str: 命令字符串
        """
        tokens = shlex.split(command_str)
        if not tokens:
            return

        # 解析命令
        cmd_info = self._registry.get_command_info(command_str)
        if cmd_info:
            module_name, command_name, handler = cmd_info

            # 懒加载检查
            if module_name not in self._module_loader.loaded_modules:
                self._module_loader.ensure_module_loaded(module_name)

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
                # typed_command 处理 - 直接传递 cli_context
                handler(self._cli_context, remaining)
            else:
                # 普通命令处理
                handler(remaining)
        else:
            # 检查是否是模块名/别名
            if len(tokens) == 1:
                self._handle_module_only(tokens[0])
            else:
                self._cli_context.perror(f"未知命令: {tokens[0]}")

    def _handle_module_only(self, module_name: str) -> None:
        """处理仅输入模块名的情况。

        Args:
            module_name: 模块名称或别名
        """
        # 1. 尝试从已加载模块的注册表查找
        module = self._registry.get_module(module_name)
        if module:
            # 触发懒加载并显示帮助（虽然已经在 registry 中）
            if module.name not in self._module_loader.loaded_modules:
                self._module_loader.ensure_module_loaded(module.name)

            commands = self._registry.list_module_commands(module.name)
            self._cli_context.poutput(f"{module.name} 模块 - {module.description}")
            self._cli_context.poutput("\n可用命令:")
            for cmd in commands:
                if module.name == "core":
                    full_cmd = cmd
                else:
                    full_cmd = f"{module.name} {cmd}"
                self._cli_context.poutput(f"  • {full_cmd}")
            return

        # 2. 尝试从懒加载模块中查找（通过模块名或别名）
        for lazy_module_name, module_cls in self._module_loader.lazy_modules.items():
            # 创建临时模块实例来检查
            temp_module = module_cls()
            # 同时检查模块名和别名
            if temp_module.name == module_name or (
                hasattr(temp_module, "aliases") and temp_module.aliases == module_name
            ):
                # 找到了！触发懒加载
                self._module_loader.ensure_module_loaded(lazy_module_name)

                # 重新从 registry 获取模块（现在已加载）
                module = self._registry.get_module(lazy_module_name)
                if module:
                    commands = self._registry.list_module_commands(lazy_module_name)
                    self._cli_context.poutput(f"{module.name} 模块 - {module.description}")
                    self._cli_context.poutput("\n可用命令:")
                    for cmd in commands:
                        if lazy_module_name == "core":
                            full_cmd = cmd
                        else:
                            full_cmd = f"{lazy_module_name} {cmd}"
                        self._cli_context.poutput(f"  • {full_cmd}")
                return

        self._cli_context.perror(f"未知命令: {module_name}")
