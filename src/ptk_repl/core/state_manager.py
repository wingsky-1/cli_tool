"""状态管理器。"""

from typing import TypeVar

from ptk_repl.state.global_state import GlobalState
from ptk_repl.state.module_state import ModuleState

T = TypeVar("T", bound=ModuleState)


class StateManager:
    """状态管理器。

    管理全局状态和模块隔离状态。
    """

    def __init__(self) -> None:
        """初始化状态管理器。"""
        self._global_state = GlobalState()
        self._module_states: dict[str, ModuleState] = {}

    @property
    def global_state(self) -> GlobalState:
        """获取全局状态。"""
        return self._global_state

    def get_module_state(self, module_name: str, state_cls: type[T]) -> T:
        """获取或创建模块状态。

        Args:
            module_name: 模块名称
            state_cls: 状态类

        Returns:
            模块状态实例
        """
        if module_name not in self._module_states:
            self._module_states[module_name] = state_cls()

        state = self._module_states[module_name]

        if not isinstance(state, state_cls):
            raise TypeError(
                f"模块 '{module_name}' 状态类型不匹配: "
                f"期望 {state_cls.__name__}, 实际 {type(state).__name__}"
            )

        return state

    def reset_module_state(self, module_name: str) -> None:
        """重置模块状态。

        Args:
            module_name: 模块名称
        """
        if module_name in self._module_states:
            self._module_states[module_name].reset()

    def reset_all(self) -> None:
        """重置所有状态（全局和模块）。"""
        self._global_state.reset()
        for state in self._module_states.values():
            state.reset()
