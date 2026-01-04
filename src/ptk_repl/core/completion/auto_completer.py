"""自动命令补全系统 - 从 CommandRegistry 自动发现命令。"""

from collections.abc import Generator
from typing import TYPE_CHECKING

from ptk_repl.core.interfaces.registry import IRegistry

if TYPE_CHECKING:
    from prompt_toolkit.completion import CompleteEvent, Completer, Completion
    from prompt_toolkit.document import Document


class AutoCompleter:
    """自动命令补全器。

    从 CommandRegistry 自动读取命令信息并提供智能补全。
    无需手动维护补全字典，注册命令后自动生效。

    Features:
        - 自动发现已注册的命令
        - 支持短别名补全（如 db -> database）
        - 基于 Pydantic 的参数补全
        - 懒加载模块的预声明补全
        - 智能缓存机制

    Example:
        ```python
        # 在 PromptToolkitCLI 中集成
        cli = PromptToolkitCLI()
        completer = AutoCompleter(cli.registry)
        cli.session.completer = completer.to_prompt_toolkit_completer()
        ```
    """

    def __init__(self, registry: IRegistry, enable_fuzzy: bool = True) -> None:
        """初始化自动补全器。

        Args:
            registry: 命令注册表实例
            enable_fuzzy: 是否启用模糊匹配（默认 True）
        """
        self._registry = registry
        self._completion_dict: dict[str, list[str]] | None = None
        self._lazy_module_commands: dict[str, list[str]] = {}
        self._enable_fuzzy = enable_fuzzy

        # 延迟导入（避免循环依赖）
        from ptk_repl.core.completion.fuzzy_matcher import FuzzyMatcher

        self._fuzzy_matcher = FuzzyMatcher()

    def register_lazy_commands(self, module_name: str, commands: list[str]) -> None:
        """注册懒加载模块的命令列表（用于补全）。

        当模块尚未加载时，仍然可以提供补全建议。

        Args:
            module_name: 模块名称
            commands: 命令列表（不含模块前缀）

        Example:
            ```python
            # 在模块类中声��
            class DatabaseModule(CommandModule):
                def register_commands(self, cli):
                    # 注册命令前先声明
                    cli.completer.register_lazy_commands("database", [
                        "connect", "query", "disconnect"
                    ])
            ```
        """
        if module_name not in self._lazy_module_commands:
            self._lazy_module_commands[module_name] = []

        # 合并命令列表（去重）
        existing = set(self._lazy_module_commands[module_name])
        new_commands = set(commands)
        self._lazy_module_commands[module_name] = sorted(existing | new_commands)

        self.refresh()

    def refresh(self) -> None:
        """刷新补全缓存。

        在命令注册或模块加载后调用此方法，
        强制重新生成补全字典。

        Example:
            >>> completer.refresh()
        """
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        """使缓存失效，强制下次访问时重新生成。"""
        self._completion_dict = None

    def build_completion_dict(self) -> dict[str, list[str]]:
        """从注册表构建补全字典。

        Returns:
            补全字典 {command_prefix: [completions]}

        Example:
            {
                '': ['status', 'exit', 'modules', 'database', 'db', ...],
                'database': ['connect', 'query', 'disconnect'],
                'db': ['connect', 'query', 'disconnect'],
                'database connect': ['localhost', '192.168.1.1'],
            }
        """
        if self._completion_dict is not None:
            return self._completion_dict

        completion_dict: dict[str, list[str]] = {}

        # 1. 核心命令补全
        core_commands = self._registry.list_module_commands("core")
        completion_dict[""] = sorted(core_commands)

        # 2. 添加所有模块名到顶层补全（包括懒加载模块）
        all_modules = set()

        # 2.1 已加载模块
        for module in self._registry.list_modules():
            if module.name != "core":
                all_modules.add(module.name)
                # 短别名
                short_name = self._get_short_alias(module.name)
                if short_name:
                    all_modules.add(short_name)

        # 2.2 懒加载模块（如果有 lazy_tracker）
        if hasattr(self._registry, "_lazy_tracker") and self._registry._lazy_tracker:
            lazy_modules = self._registry._lazy_tracker.lazy_modules
            for module_name in lazy_modules:
                all_modules.add(module_name)
                short_name = self._get_short_alias(module_name)
                if short_name:
                    all_modules.add(short_name)

            # 从 alias_map 获取别名
            alias_map = getattr(self._registry._lazy_tracker, "_alias_to_module", {})
            for alias in alias_map.keys():
                all_modules.add(alias)

        completion_dict[""] = sorted(all_modules)

        # 5. 模块命令补全
        for module in self._registry.list_modules():
            if module.name == "core":
                continue

            commands = self._registry.list_module_commands(module.name)

            # 完整模块名补全（如 "database"）
            completion_dict[module.name] = sorted(commands)

            # 短别名补全（如 "db"）
            short_name = self._get_short_alias(module.name)
            if short_name:
                completion_dict[short_name] = sorted(commands)

        # 6. 懒加载模块补全（未加载的模块的子命令）
        for module_name, commands in self._lazy_module_commands.items():
            if module_name not in completion_dict:
                completion_dict[module_name] = sorted(commands)
                short_name = self._get_short_alias(module_name)
                if short_name:
                    completion_dict[short_name] = sorted(commands)

        # 7. 命令别名补全（使用公共接口）
        aliases = self._registry.get_all_aliases()
        for alias, _full_cmd in aliases.items():
            if " " in alias:  # 处理 "db connect" 这样的别名
                parts: list[str] = alias.split(maxsplit=1)
                if len(parts) == 2:
                    alias_module: str = parts[0]
                    alias_cmd: str = parts[1]
                    if alias_module not in completion_dict:
                        completion_dict[alias_module] = []
                    # 确保模块补全包含别名
                    if alias_cmd not in completion_dict[alias_module]:
                        completion_dict[alias_module].append(alias_cmd)

        # 8. 参数补全（基于 Pydantic）
        param_completions = self._build_parameter_completions()
        completion_dict.update(param_completions)

        self._completion_dict = completion_dict
        return completion_dict

    def _get_short_alias(self, module_name: str) -> str | None:
        """获取模块的短别名。

        Args:
            module_name: 完整模块名

        Returns:
            短别名，如果未定义则返回 None
        """
        # 从模块实例读取别名（动态）
        module = self._registry.get_module(module_name)
        if module and hasattr(module, "aliases") and module.aliases:
            return module.aliases

        return None

    def _build_parameter_completions(self) -> dict[str, list[str]]:
        """构建基于 Pydantic 的参数补全。

        Returns:
            参数补全字典
        """
        param_dict: dict[str, list[str]] = {}

        # 遍历所有命令，检查是否使用 typed_command（使用公共接口）
        commands = self._registry.get_all_commands()
        for full_cmd, (_module, _cmd, handler) in commands.items():
            if hasattr(handler, "_original_func"):
                original_func = handler._original_func
                if hasattr(original_func, "_typed_model"):
                    # 获取 Pydantic 模型
                    model_cls = original_func._typed_model
                    model_fields = model_cls.model_fields

                    # 生成参数补全
                    params = []
                    for field_name in model_fields:
                        # 添加长选项
                        long_opt = f"--{field_name.replace('_', '-')}"
                        params.append(long_opt)

                        # 添加短选项（首字母）
                        if len(field_name) > 0:
                            short_opt = f"-{field_name[0]}"
                            params.append(short_opt)

                    if params:
                        param_dict[full_cmd] = params

                        # 为别名也生成参数补全（使用公共接口）
                        aliases = self._registry.get_all_aliases()
                        for alias, full in aliases.items():
                            if full == full_cmd:
                                param_dict[alias] = params

        return param_dict

    def get_completions(
        self, document: "Document", complete_event: "CompleteEvent"
    ) -> Generator["Completion", None, None]:
        """获取补全建议（生成器）。

        Args:
            document: 当前文档
            complete_event: 补全事件

        Yields:
            补全建议
        """
        from prompt_toolkit.completion import Completion

        # 获取当前文本
        text = document.text_before_cursor
        words = text.split()

        if not words:
            return

        # 检查参数输入（-- 前缀）
        if words and words[-1].startswith("-"):
            # 参数补全模式
            param_completions = self._get_parameter_completions_for_context(words)
            if param_completions:
                word = words[-1]
                matches = [p for p in param_completions if p.startswith(word)]
                for match in sorted(matches):
                    yield Completion(
                        text=match,
                        start_position=-len(word),
                        display=match,
                        display_meta="参数",
                    )
            return

        # 构建补全字典
        completion_dict = self.build_completion_dict()

        # 确定补全上下文
        # 检查是否在空格之后（text 以空格结尾）
        ends_with_space = text.endswith(" ")

        if len(words) == 1:
            if ends_with_space:
                # "database " -> 补全子命令
                prefix = words[0]
                word = ""
            else:
                # "data" -> 补全命令或模块
                prefix = ""
                word = words[0]
        elif len(words) == 2:
            # "database conn" -> 补全模块的子命令
            prefix = words[0]
            word = words[1]
        else:
            # 更多词 - 可能是参数补全
            prefix = " ".join(words[:-1])
            word = words[-1]

        # 获取候选项
        candidates = completion_dict.get(prefix, [])

        # 模糊匹配或前缀匹配
        if self._enable_fuzzy and word:
            # 使用模糊匹配
            match_results = self._fuzzy_matcher.match(word, candidates)
            matches = [r.candidate for r in match_results if r.score >= 50]
        else:
            # 前缀匹配（向后兼容）
            matches = [c for c in candidates if c.startswith(word)]

        # 生成 Completion 对象（使用 yield）
        for match in sorted(matches):
            yield Completion(
                text=match,
                start_position=-len(word),
                display=match,
                display_meta=self._get_completion_meta(match, prefix),
            )

    def _get_completion_meta(self, match: str, prefix: str) -> str:
        """获取补全项的元数据描述（从 docstring 提取）。

        Args:
            match: 匹配的补全项
            prefix: 前缀

        Returns:
            元数据描述（实际命令描述）
        """
        # 1. 参数补全
        if match.startswith("--"):
            return self._get_parameter_description(match, prefix)

        # 2. 核心命令补全（prefix 为空）
        if prefix == "":
            # 判断是模块名还是命令
            # 先尝试直接获取模块
            module = self._registry.get_module(match)

            # 如果没找到，检查是否是短别名
            if not module:
                full_module_name = self._resolve_module_alias(match)
                if full_module_name:
                    module = self._registry.get_module(full_module_name)

            if module:
                # 是模块名 - 返回模块描述
                return module.description if module.description else "模块"
            else:
                # 是核心命令 - 返回命令描述
                cmd_info = self._registry.get_command_info(match)
                if cmd_info:
                    _, _, handler = cmd_info
                    return self._extract_command_description(handler)
                return "命令"

        # 3. 模块子命令补全
        # 构建 "module command" 形式
        candidate_command = f"{prefix} {match}"

        # 先检查是否是别名，如果是则获取原始命令
        full_command = self._resolve_alias(candidate_command)

        # 获取命令信息
        cmd_info = self._registry.get_command_info(full_command)

        if cmd_info:
            _, _, handler = cmd_info
            return self._extract_command_description(handler)

        # 4. 默认返回空字符串
        return ""

    def _resolve_module_alias(self, alias: str) -> str | None:
        """解析模块短别名，返回完整模块名。

        Args:
            alias: 可能是短别名的模块名

        Returns:
            完整模块名，如果不是别名则返回 None
        """
        # 遍历所有模块，查找匹配的短别名
        for module in self._registry.list_modules():
            short_alias = self._get_short_alias(module.name)
            if short_alias == alias:
                return module.name

        return None

    def _resolve_alias(self, command: str) -> str:
        """解析命令别名，返回完整命令。

        Args:
            command: 可能是别名的命令

        Returns:
            完整命令（如果是别名则解析，否则原样返回）
        """
        # 检查是否在别名映射中（使用公共接口）
        aliases = self._registry.get_all_aliases()
        if command in aliases:
            return aliases[command]

        return command

    def _get_parameter_description(self, param: str, prefix: str) -> str:
        """从 Pydantic 模型提取参数描述。

        Args:
            param: 参数名（如 "--host"）
            prefix: 前缀

        Returns:
            参数描述
        """
        # 构建可能的命令名（如 "database connect"）
        if " " not in prefix:
            # 如果前缀没有空格，可能是正在输入命令的第一个参数
            return "参数"

        command_prefix = prefix

        # 先解析别名（如 "db connect" -> "database connect"）
        full_command = self._resolve_alias(command_prefix)

        # 获取命令信息
        cmd_info = self._registry.get_command_info(full_command)
        if not cmd_info:
            return "参数"

        _module, _cmd, handler = cmd_info

        # 检查是否使用 typed_command
        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            if hasattr(original_func, "_typed_model"):
                # 获取 Pydantic 模型
                model_cls = original_func._typed_model
                model_fields = model_cls.model_fields

                # 提取参数名（去掉 "--" 并转换下划线）
                param_name = param[2:].replace("-", "_")

                # 获取字段描述
                if param_name in model_fields:
                    field_info = model_fields[param_name]
                    if field_info.description:
                        # field_info.description 在 Pydantic 中是 str | None
                        # 这里已经检查了不为 None，可以直接使用
                        desc = field_info.description
                        if isinstance(desc, str):
                            return desc
                        # 如果是 None（理论上不应该，因为已经检查了）
                        return "参数"

        return "参数"

    def _extract_command_description(self, handler: object) -> str:
        """从命令处理函数提取描述。

        Args:
            handler: 命令处理函数

        Returns:
            命令描述
        """
        # 1. 尝试从 typed_command 包装器提取原始函数
        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            doc = original_func.__doc__
        else:
            doc = handler.__doc__

        # 2. 清理文档字符串
        if doc:
            lines: list[str] = doc.strip().split("\n")
            text: str = lines[0]
            return text  # 取第一行

        return "无描述"

    def _get_parameter_completions_for_context(self, words: list[str]) -> list[str]:
        """根据上下文获取参数补全列表。

        Args:
            words: 已输入的单词列表

        Returns:
            参数补全列表
        """
        if len(words) < 2:
            return []

        # 构建命令前缀（如 "database connect"）
        command_prefix = " ".join(words[:-1])

        # 解析别名
        full_command = self._resolve_alias(command_prefix)

        # 获取参数补全字典
        param_dict = self._build_parameter_completions()

        # 返回该命令的参数列表
        return param_dict.get(full_command, [])

    def to_prompt_toolkit_completer(self) -> "Completer":
        """转换为 prompt_toolkit 的 Completer 接口。

        Returns:
            prompt_toolkit 兼容的 Completer
        """
        from prompt_toolkit.completion import Completer as PTCompleter

        class _PromptToolkitCompleter(PTCompleter):
            """prompt_toolkit 兼容的补全器适配器。"""

            def __init__(self, auto_completer: "AutoCompleter") -> None:
                self._auto_completer = auto_completer

            def get_completions(self, document: "Document", complete_event: "CompleteEvent"):
                return self._auto_completer.get_completions(document, complete_event)

        return _PromptToolkitCompleter(self)
