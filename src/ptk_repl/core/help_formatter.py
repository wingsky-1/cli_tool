"""帮助信息格式化工具。

提供统一的帮助信息格式化功能，包括：
- 提取命令描述
- 提取参数信息
- 格式化输出
- 颜色渲染
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from colorama import init

from ptk_repl.core.config.theme import ColorScheme

# 初始化 colorama
init(autoreset=True)

if TYPE_CHECKING:
    from ptk_repl.cli import PromptToolkitCLI


class HelpFormatter:
    """帮助信息格式化器。

    提供统一的帮助信息格式化功能，包括：
    - 提取命令描述
    - 提取参数信息
    - 格式化输出
    - 颜色渲染
    """

    def __init__(self, cli: "PromptToolkitCLI", color_scheme: ColorScheme | None = None) -> None:
        """初始化帮助格式化器。

        Args:
            cli: PromptToolkitCLI 实例
            color_scheme: 颜色方案（可选，默认使用默认方案）
        """
        self.cli = cli
        self.registry = cli.registry
        self.color_scheme = color_scheme or ColorScheme.default()

    def extract_command_description(self, handler: Callable) -> str:
        """提取命令描述。

        Args:
            handler: 命令处理函数

        Returns:
            命令描述字符串
        """
        # 1. 尝试从 typed_command 包装器提取原始函数
        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            doc = original_func.__doc__
        else:
            doc = handler.__doc__

        # 2. 清理文档字符串
        if doc:
            text = doc.strip().split("\n")[0]
            return cast(str, text)  # 取第一行
        return "无描述"

    def extract_parameter_info(self, handler: Callable) -> list[dict[str, Any]]:
        """提取参数信息（从 Pydantic 模型）。

        Args:
            handler: 命令处理函数

        Returns:
            参数信息列表 [{name, description, required, default}, ...]
        """
        params = []

        # 检查是否使用 typed_command
        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            if hasattr(original_func, "_typed_model"):
                model_cls = original_func._typed_model

                for field_name, field_info in model_cls.model_fields.items():
                    param = {
                        "name": field_name,
                        "description": field_info.description or "无描述",
                        "required": field_info.is_required(),
                        "default": field_info.default if not field_info.is_required() else None,
                    }
                    params.append(param)

        return params

    def get_command_aliases(self, module_name: str, command_name: str) -> list[str]:
        """获取命令的别名列表。

        Args:
            module_name: 模块名称
            command_name: 命令名称

        Returns:
            别名列表
        """
        full_command = f"{module_name} {command_name}" if module_name != "core" else command_name
        aliases = []

        for alias, target in self.registry._alias_map.items():
            if target == full_command:
                aliases.append(alias)

        return aliases

    def format_overview_help(self) -> str:
        """格式化总览帮助。

        Returns:
            格式化后的帮助字符串
        """
        lines = []

        # 核心命令
        lines.append(self._section_header("核心命令"))
        core_commands = self.registry.list_module_commands("core")

        for cmd in sorted(core_commands):
            cmd_info = self.registry.get_command_info(cmd)
            if cmd_info:
                _, _, handler = cmd_info
                description = self.extract_command_description(handler)
                aliases = self.get_command_aliases("core", cmd)
                lines.append(self._format_command_item(cmd, description, aliases))

        lines.append("")

        # 模块命令
        modules = [m for m in self.registry.list_modules() if m.name != "core"]
        if modules:
            lines.append(self._section_header("模块命令"))

            for module in sorted(modules, key=lambda m: m.name):
                commands = self.registry.list_module_commands(module.name)
                if not commands:
                    continue

                # 模块描述
                module_desc = module.description or "无描述"
                short_alias = self._get_short_module_alias(module.name)

                # 模块标题
                if short_alias:
                    module_title = f"{module.name} ({short_alias})"
                else:
                    module_title = module.name

                lines.append(f"  {self._color_text(module_title, 'module'):<20} {module_desc}")

                # 模块子命令
                for cmd in sorted(commands):
                    cmd_info = self.registry.get_command_info(f"{module.name} {cmd}")
                    if cmd_info:
                        _, _, handler = cmd_info
                        description = self.extract_command_description(handler)
                        aliases = self.get_command_aliases(module.name, cmd)

                        # 格式化命令项（缩进）
                        cmd_line = self._format_command_item(cmd, description, aliases, indent=4)
                        lines.append(cmd_line)

                lines.append("")

        # 提示
        lines.append(self._separator())
        lines.append("提示:")
        lines.append("  • 使用 'help <command>' 查看命令详细帮助")
        lines.append("  • 使用 'help <module>' 查看模块所有命令")
        lines.append("  • 输入 'exit' 或按 Ctrl+D 退出")
        lines.append(self._separator())

        return "\n".join(lines)

    def format_command_help(self, module_name: str, command_name: str) -> str:
        """格式化单个命令的详细帮助。

        Args:
            module_name: 模块名称
            command_name: 命令名称

        Returns:
            格式化后的帮助字符串
        """
        # 获取命令信息
        full_command = f"{module_name} {command_name}" if module_name != "core" else command_name
        cmd_info = self.registry.get_command_info(full_command)

        if not cmd_info:
            return self._error(f"未找到命令: {full_command}")

        _, _, handler = cmd_info
        description = self.extract_command_description(handler)
        parameters = self.extract_parameter_info(handler)
        aliases = self.get_command_aliases(module_name, command_name)

        lines = []

        # 标题
        lines.append(self._separator())
        lines.append(self._title(f"{full_command} - {description}"))
        lines.append(self._separator())
        lines.append("")

        # 描述
        lines.append(self._label("描述"))
        lines.append(f"  {description}")
        lines.append("")

        # 参数
        if parameters:
            lines.append(self._label("参数"))
            for param in parameters:
                param_str = f"  --{param['name']:<15} "
                param_str += f"{param['description']:<30}"

                if param["required"]:
                    param_str += " [必需]"
                else:
                    default_str = str(param["default"]) if param["default"] is not None else "None"
                    param_str += f" [默认: {default_str}]"

                lines.append(self._color_text(param_str, "param"))
            lines.append("")

        # 别名
        if aliases:
            lines.append(self._label("别名"))
            for alias in aliases:
                lines.append(f"  • {self._color_text(alias, 'alias')}")
            lines.append("")
        else:
            lines.append(self._label("别名"))
            lines.append("  无")
            lines.append("")

        # 示例
        lines.append(self._label("使用示例"))
        lines.append(f"  {self._color_text(full_command, 'command')}")
        if parameters:
            # 生成带参数的示例
            required_params = [p for p in parameters if p["required"]]
            if required_params:
                example = "  " + full_command
                for param in required_params[:2]:  # 最多显示2个必需参数
                    example += f" <{param['name']}>"
                lines.append(self._color_text(example, "example"))

        lines.append("")
        lines.append(self._separator())

        return "\n".join(lines)

    def format_module_help(self, module_name: str) -> str:
        """格式化模块帮助。

        Args:
            module_name: 模块名称

        Returns:
            格式化后的帮助字符串
        """
        # 获取模块
        module = self.registry.get_module(module_name)
        if not module:
            return self._error(f"未找到模块: {module_name}")

        commands = self.registry.list_module_commands(module_name)
        if not commands:
            return self._error(f"模块 '{module_name}' 没有可用命令")

        lines = []

        # 标题
        module_title = f"{module.name} 模块 - {module.description or '无描述'}"
        lines.append(self._separator())
        lines.append(self._title(module_title))
        lines.append(self._separator())
        lines.append("")

        # 命令列表
        lines.append(self._label("可用命令"))

        for cmd in sorted(commands):
            cmd_info = self.registry.get_command_info(f"{module_name} {cmd}")
            if cmd_info:
                _, _, handler = cmd_info
                description = self.extract_command_description(handler)
                aliases = self.get_command_aliases(module_name, cmd)
                parameters = self.extract_parameter_info(handler)

                # 格式化命令
                cmd_display = cmd
                if aliases:
                    cmd_display += f" ({', '.join(aliases)})"

                # 参数签名
                param_str = ""
                if parameters:
                    required_params = [p for p in parameters if p["required"]]
                    optional_params = [p for p in parameters if not p["required"]]

                    if required_params:
                        param_str += " " + " ".join([f"<{p['name']}>" for p in required_params])
                    if optional_params:
                        param_str += " " + " ".join([f"[--{p['name']}]" for p in optional_params])

                lines.append(f"  • {self._color_text(cmd_display, 'command')}")
                lines.append(f"      {description}{param_str}")
                lines.append("")

        # 模块版本
        lines.append(self._separator())
        lines.append(f"模块版本: {module.version}")
        lines.append(self._separator())

        return "\n".join(lines)

    # 辅助格式化方法

    def _separator(self) -> str:
        """生成分隔线。"""
        return self._color_text("━" * 65, "separator")

    def _title(self, text: str) -> str:
        """生成标题。"""
        centered = text.center(65)
        return self._color_text(f"  {centered}", "title")

    def _section_header(self, text: str) -> str:
        """生成小节标题。"""
        return f"  {self._color_text(text, 'section')}"

    def _label(self, text: str) -> str:
        """生成标签。"""
        return f"  {self._color_text(text, 'label')}"

    def _format_command_item(
        self, command: str, description: str, aliases: list[str] | None = None, indent: int = 2
    ) -> str:
        """格式化命令项。

        Args:
            command: 命令名
            description: 命令描述
            aliases: 别名列表
            indent: 缩进空格数

        Returns:
            格式化后的命令行
        """
        import re

        # 用于计算去除 ANSI 码后的实际显示长度
        ansi_escape = re.compile(r"\x1B\[@-_][0-9;]*[0-9;]*[0-9;]*m")

        def visible_length(text: str) -> int:
            """��算文本的可见长度（去除 ANSI 颜色码）。"""
            return len(ansi_escape.sub("", text))

        prefix = " " * indent

        # 命令名（带颜色）
        cmd_colored = self._color_text(command, "command")

        # 别名（带颜色）
        alias_str = ""
        if aliases:
            colored_aliases = [self._color_text(a, "alias") for a in aliases]
            alias_str = f" ({', '.join(colored_aliases)})"

        # 计算实际显示宽度
        cmd_visible_len = len(command)
        alias_visible_len = len(f" ({', '.join(aliases)})") if aliases else 0
        total_visible_len = cmd_visible_len + alias_visible_len

        # 计算需要填充的空格数（目标宽度 30）
        target_width = 30
        padding = " " * max(0, target_width - total_visible_len)

        # 组合最终字符串
        return f"{prefix}{cmd_colored}{alias_str}{padding} {description}"

    def _color_text(self, text: str, color_type: str) -> str:
        """为文本添加颜色。

        Args:
            text: 文本
            color_type: 颜色类型

        Returns:
            带颜色代码的文本
        """
        return self.color_scheme.color_text(text, color_type)

    def _error(self, text: str) -> str:
        """生成错误消息。

        Args:
            text: 错误文本

        Returns:
            格式化的错误消息
        """
        return self._color_text(f"[错误] {text}", "error")

    def _get_short_module_alias(self, module_name: str) -> str | None:
        """获取模块短别名。

        Args:
            module_name: 完整模块名

        Returns:
            短别名，如果未定义则返回 None
        """
        short_aliases = {
            "database": "db",
            "file": "fs",
        }
        return short_aliases.get(module_name)
