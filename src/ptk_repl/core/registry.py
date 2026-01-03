"""命令注册表。"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from ptk_repl.core.completer import AutoCompleter


class CommandRegistry:
    """命令注册表。

    管理所有模块和命令的注册。
    """

    def __init__(self) -> None:
        """初始化命令注册表。"""
        self._modules: dict[str, Any] = {}
        self._command_map: dict[str, tuple[str, str, Callable]] = {}
        self._alias_map: dict[str, str] = {}
        self._completer: AutoCompleter | None = None

    def set_completer(self, completer: "AutoCompleter") -> None:
        """设置补全器。

        Args:
            completer: AutoCompleter 实例
        """
        self._completer = completer

    def register_module(self, module: Any) -> None:
        """注册模块。

        Args:
            module: CommandModule 实例

        Raises:
            ValueError: 如果模块已存在
        """
        if module.name in self._modules:
            raise ValueError(f"模块 '{module.name}' 已存在")
        self._modules[module.name] = module

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

        Raises:
            ValueError: 如果命令已存在
        """
        full_command = f"{module_name} {command_name}" if module_name != "core" else command_name

        if full_command in self._command_map:
            raise ValueError(f"命令 '{full_command}' 已存在")

        self._command_map[full_command] = (module_name, command_name, handler)

        # 注册别名
        if aliases:
            for alias in aliases:
                self._alias_map[alias] = full_command

        # 自动通知补全器更新
        if self._completer:
            self._completer._invalidate_cache()

    def get_command_info(self, command_str: str) -> tuple[str, str, Callable] | None:
        """获取命令信息。

        Args:
            command_str: 命令字符串

        Returns:
            (模块名, 命令名, 处理器) 元组，如果未找到则返回 None
        """
        # 检查别名
        if command_str in self._alias_map:
            command_str = self._alias_map[command_str]

        # 解析命令（最多分割成3部分：模块名 命令名 参数...）
        parts = command_str.strip().split(maxsplit=2)

        if len(parts) >= 2:
            module_name, cmd_name = parts[0], parts[1]
            full_module = self._resolve_module_name(module_name)
            if full_module:
                full_cmd = f"{full_module} {cmd_name}"
                if full_cmd in self._command_map:
                    return self._command_map[full_cmd]

        if command_str in self._command_map:
            return self._command_map[command_str]

        return None

    def _resolve_module_name(self, short_name: str) -> str | None:
        """解析短模块名。

        Args:
            short_name: 短模块名或别名

        Returns:
            完整模块名，如果未找到则返回 None
        """
        # 1. 精确匹配模块名
        if short_name in self._modules:
            module = self._modules[short_name]
            # 返回模块的真实名称（不是别名）
            return module.name if hasattr(module, "name") else short_name

        # 2. 遍历所有模块，检查别名（动态读取）
        for module in self._modules.values():
            if hasattr(module, "aliases") and short_name in module.aliases:
                return cast(str, module.name)

        # 3. 前缀匹配（保留现有能力）
        for module_name in self._modules:
            if module_name.startswith(short_name):
                return module_name

        return None

    def get_module(self, name: str) -> Any:
        """获取模块。

        Args:
            name: 模块名称

        Returns:
            模块实例，如果未找到则返回 None
        """
        return self._modules.get(name)

    def list_module_commands(self, module_name: str) -> list[str]:
        """列出模块的所有命令。

        Args:
            module_name: 模块名称

        Returns:
            命令列表
        """
        result: list[str] = []
        for _full_cmd, (mod_name, cmd_name, _) in self._command_map.items():
            if mod_name == module_name:
                result.append(cmd_name)
        return result

    def list_modules(self) -> list[Any]:
        """列出所有模块。

        Returns:
            模块列表
        """
        return list(self._modules.values())

    def get_all_commands(self) -> dict[str, tuple[str, str, Callable]]:
        """获取所有命令的副本（避免直接访问私有成员）。

        Returns:
            命令字典的副本 {full_command: (module_name, command_name, handler)}
            - full_command: 完整命令（如 "database connect" 或 "help"）
            - module_name: 模块名称
            - command_name: 命令名称
            - handler: 命令处理函数

        Note:
            返回的是副本，修改返回值不会影响原始注册表。

        Examples:
            >>> commands = registry.get_all_commands()
            >>> "help" in commands
            True
        """
        return self._command_map.copy()

    def get_all_aliases(self) -> dict[str, str]:
        """获取所有别名的副本（避免直接访问私有成员）。

        Returns:
            别名字典的副本 {alias: full_command}
            - alias: 别名（如 "h"）
            - full_command: 对应的完整命令（如 "help"）

        Note:
            返回的是副本，修改返回值不会影响原始注册表。

        Examples:
            >>> aliases = registry.get_all_aliases()
            >>> aliases["h"]
            "help"
        """
        return self._alias_map.copy()
