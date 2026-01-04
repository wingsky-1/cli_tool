"""修复参数补全和集成模糊匹配的 AutoCompleter 增强版本。

关键修改：
1. 修复 get_completions() 中的参数补全逻辑（L272-293）
2. 集成 FuzzyMatcher 进行模糊匹配（L280-290）
3. 增强懒加载模块补全（L130-155）
4. 优化性能和缓存策略
"""

from collections.abc import Generator
from typing import TYPE_CHECKING

from ptk_repl.core.completion.fuzzy_matcher import FuzzyMatcher, MatchResult
from ptk_repl.core.interfaces.registry import IRegistry

if TYPE_CHECKING:
    from prompt_toolkit.completion import CompleteEvent, Completer, Completion
    from prompt_toolkit.document import Document


class AutoCompleter:
    """自动命令补全器（增强版）。

    新增功能：
        - ✅ 参数补全（修复）
        - ✅ 模糊匹配（前缀 + 子序列 + Levenshtein）
        - ✅ 懒加载模块补全（增强）

    Example:
        ```python
        completer = AutoCompleter(registry)
        completer.enable_fuzzy_matching = True
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

        # 模糊匹配器
        self._enable_fuzzy = enable_fuzzy
        self._fuzzy_matcher = FuzzyMatcher(
            enable_prefix=True,
            enable_subsequence=True,
            enable_levenshtein=True,
            max_levenshtein_distance=3,
        )

    # ===== 保持原有方法不变 =====

    def register_lazy_commands(self, module_name: str, commands: list[str]) -> None:
        """注册懒加载模块的命令列表（用于补全）。"""
        if module_name not in self._lazy_module_commands:
            self._lazy_module_commands[module_name] = []

        existing = set(self._lazy_module_commands[module_name])
        new_commands = set(commands)
        self._lazy_module_commands[module_name] = sorted(existing | new_commands)

        self.refresh()

    def refresh(self) -> None:
        """刷新补全缓存。"""
        self._invalidate_cache()

    def _invalidate_cache(self) -> None:
        """使缓存失效。"""
        self._completion_dict = None

    # ===== 增强的 build_completion_dict() =====

    def build_completion_dict(self) -> dict[str, list[str]]:
        """从注册表构建补全字典（增强版）。

        新增：
        - 懒加载模块的完整集成
        - 参数补全字典的优化生成

        Returns:
            补全字典 {command_prefix: [completions]}
        """
        if self._completion_dict is not None:
            return self._completion_dict

        completion_dict: dict[str, list[str]] = {}

        # 1. 核心命令补全
        core_commands = self._registry.list_module_commands("core")
        completion_dict[""] = sorted(core_commands)

        # 2. 添加所有模块名到顶层补全（包括懒加载模块）
        all_modules = set()

        # 已加载模块
        for module in self._registry.list_modules():
            if module.name != "core":
                all_modules.add(module.name)
                short_name = self._get_short_alias(module.name)
                if short_name:
                    all_modules.add(short_name)

        # 懒加载模块（未加载但已知）
        for module_name in self._lazy_module_commands.keys():
            all_modules.add(module_name)
            short_name = self._get_short_alias(module_name)
            if short_name:
                all_modules.add(short_name)

        # 合并到顶层补全
        completion_dict[""].extend(sorted(all_modules))

        # 3. 模块命令补全（已加载 + 懒加载）
        for module_name in all_modules:
            # 解析完整模块名（如果是别名）
            full_module_name = self._resolve_module_alias(module_name) or module_name

            # 获取命令列表
            if self._registry.get_module(full_module_name):
                # 已加载模块
                commands = self._registry.list_module_commands(full_module_name)
            else:
                # 懒加载模块
                commands = self._lazy_module_commands.get(full_module_name, [])

            if commands:
                completion_dict[module_name] = sorted(commands)

        # 4. 命令别名补全
        aliases = self._registry.get_all_aliases()
        for alias, full_cmd in aliases.items():
            if " " in alias:
                parts: list[str] = alias.split(maxsplit=1)
                if len(parts) == 2:
                    alias_module: str = parts[0]
                    alias_cmd: str = parts[1]
                    if alias_module not in completion_dict:
                        completion_dict[alias_module] = []
                    if alias_cmd not in completion_dict[alias_module]:
                        completion_dict[alias_module].append(alias_cmd)

        # 5. 参数补全（基于 Pydantic）
        param_completions = self._build_parameter_completions()
        completion_dict.update(param_completions)

        self._completion_dict = completion_dict
        return completion_dict

    # ===== 保持原有辅助方法不变 =====

    def _get_short_alias(self, module_name: str) -> str | None:
        """获取模块的短别名。"""
        module = self._registry.get_module(module_name)
        if module and hasattr(module, "aliases") and module.aliases:
            return module.aliases
        return None

    def _resolve_module_alias(self, alias: str) -> str | None:
        """解析模块短别名。"""
        for module in self._registry.list_modules():
            short_alias = self._get_short_alias(module.name)
            if short_alias == alias:
                return module.name
        return None

    def _build_parameter_completions(self) -> dict[str, list[str]]:
        """构建基于 Pydantic 的参数补全。"""
        param_dict: dict[str, list[str]] = {}

        commands = self._registry.get_all_commands()
        for full_cmd, (_module, _cmd, handler) in commands.items():
            if hasattr(handler, "_original_func"):
                original_func = handler._original_func
                if hasattr(original_func, "_typed_model"):
                    model_cls = original_func._typed_model
                    model_fields = model_cls.model_fields

                    params = []
                    for field_name in model_fields:
                        long_opt = f"--{field_name.replace('_', '-')}"
                        params.append(long_opt)

                        if len(field_name) > 0:
                            short_opt = f"-{field_name[0]}"
                            params.append(short_opt)

                    if params:
                        param_dict[full_cmd] = params

                        # 为别名生成参数补全
                        aliases = self._registry.get_all_aliases()
                        for alias, full in aliases.items():
                            if full == full_cmd:
                                param_dict[alias] = params

        return param_dict

    # ===== 核心修改：get_completions() =====

    def get_completions(
        self, document: "Document", complete_event: "CompleteEvent"
    ) -> Generator["Completion", None, None]:
        """获取补全建议（增强版 - 支持参数补全和模糊匹配）。

        关键修改：
        1. 修复参数补全的上下文判断逻辑
        2. 集成模糊匹配算法
        3. 优化性能和准确性

        Args:
            document: 当前文档
            complete_event: 补全事件

        Yields:
            补全建议
        """
        from prompt_toolkit.completion import Completion

        text = document.text_before_cursor
        words = text.split()

        if not words:
            return

        completion_dict = self.build_completion_dict()

        # ===== 核心修改：参数补全上下文判断 =====

        # 检查是否在输入参数（以 -- 或 - 开头）
        if words[-1].startswith("-"):
            # 参数补全模式
            param_completions = self._get_parameter_completions_for_context(
                words[:-1], words[-1], completion_dict
            )

            for match in sorted(param_completions):
                if match.startswith(words[-1]):  # 前缀过滤
                    yield Completion(
                        text=match,
                        start_position=-len(words[-1]),
                        display=match,
                        display_meta=self._get_parameter_description(
                            match, " ".join(words[:-1])
                        ),
                    )
            return

        # ===== 原有逻辑：命令和模块补全 =====

        ends_with_space = text.endswith(" ")

        if len(words) == 1:
            if ends_with_space:
                prefix = words[0]
                word = ""
            else:
                prefix = ""
                word = words[0]
        elif len(words) == 2:
            prefix = words[0]
            word = words[1]
        else:
            prefix = " ".join(words[:-1])
            word = words[-1]

        candidates = completion_dict.get(prefix, [])

        # ===== 核心修改：模糊匹配集成 =====

        if self._enable_fuzzy and word:
            # 使用模糊匹配
            match_results = self._fuzzy_matcher.match(word, candidates)
            matches = [r.candidate for r in match_results if r.score > 50]  # 阈值 50 分
        else:
            # 传统前缀匹配
            matches = [c for c in candidates if c.startswith(word)]

        # 生成 Completion 对象
        for match in sorted(matches):
            yield Completion(
                text=match,
                start_position=-len(word),
                display=match,
                display_meta=self._get_completion_meta(match, prefix),
            )

    def _get_parameter_completions_for_context(
        self, context_words: list[str], current_param: str, completion_dict: dict[str, list[str]]
    ) -> list[str]:
        """获取参数补全列表（上下文感知）。

        Args:
            context_words: 上下文单词列表（如 ["database", "connect"]）
            current_param: 当前输入的参数（如 "--h"）
            completion_dict: 补全字典

        Returns:
            匹配的参数列表
        """
        if not context_words:
            return []

        # 构建完整命令（如 "database connect"）
        full_command = " ".join(context_words)

        # 解析别名
        full_command = self._resolve_alias(full_command)

        # 获取参数补全
        params = completion_dict.get(full_command, [])

        # 过滤：只返回参数（以 -- 或 - 开头）
        return [p for p in params if p.startswith("-")]

    # ===== 保持原有元数据方法不变 =====

    def _get_completion_meta(self, match: str, prefix: str) -> str:
        """获取补全项的元数据描述。"""
        if match.startswith("--"):
            return self._get_parameter_description(match, prefix)

        if prefix == "":
            module = self._registry.get_module(match)
            if not module:
                full_module_name = self._resolve_module_alias(match)
                if full_module_name:
                    module = self._registry.get_module(full_module_name)

            if module:
                return module.description if module.description else "模块"
            else:
                cmd_info = self._registry.get_command_info(match)
                if cmd_info:
                    _, _, handler = cmd_info
                    return self._extract_command_description(handler)
                return "命令"

        candidate_command = f"{prefix} {match}"
        full_command = self._resolve_alias(candidate_command)
        cmd_info = self._registry.get_command_info(full_command)

        if cmd_info:
            _, _, handler = cmd_info
            return self._extract_command_description(handler)

        return ""

    def _resolve_alias(self, command: str) -> str:
        """解析命令别名。"""
        aliases = self._registry.get_all_aliases()
        if command in aliases:
            return aliases[command]
        return command

    def _get_parameter_description(self, param: str, prefix: str) -> str:
        """从 Pydantic 模型提取参数描述。"""
        if " " not in prefix:
            return "参数"

        command_prefix = prefix
        full_command = self._resolve_alias(command_prefix)
        cmd_info = self._registry.get_command_info(full_command)

        if not cmd_info:
            return "参数"

        _module, _cmd, handler = cmd_info

        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            if hasattr(original_func, "_typed_model"):
                model_cls = original_func._typed_model
                model_fields = model_cls.model_fields

                param_name = param[2:].replace("-", "_")

                if param_name in model_fields:
                    field_info = model_fields[param_name]
                    if field_info.description:
                        desc = field_info.description
                        if isinstance(desc, str):
                            return desc
                        return "参数"

        return "参数"

    def _extract_command_description(self, handler: object) -> str:
        """从命令处理函数提取描述。"""
        if hasattr(handler, "_original_func"):
            original_func = handler._original_func
            doc = original_func.__doc__
        else:
            doc = handler.__doc__

        if doc:
            lines: list[str] = doc.strip().split("\n")
            text: str = lines[0]
            return text

        return "无描述"

    def to_prompt_toolkit_completer(self) -> "Completer":
        """转换为 prompt_toolkit 的 Completer 接口。"""
        from prompt_toolkit.completion import Completer as PTCompleter

        class _PromptToolkitCompleter(PTCompleter):
            """prompt_toolkit 兼容的补全器适配器。"""

            def __init__(self, auto_completer: "AutoCompleter") -> None:
                self._auto_completer = auto_completer

            def get_completions(self, document: "Document", complete_event: "CompleteEvent"):
                return self._auto_completer.get_completions(document, complete_event)

        return _PromptToolkitCompleter(self)
