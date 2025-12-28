"""模块状态基类。"""

from pydantic import BaseModel


class ModuleState(BaseModel):
    """模块状态基类。

    所有模块的状态类应继承此类。
    """

    def reset(self) -> None:
        """重置模块状态。"""
        pass
