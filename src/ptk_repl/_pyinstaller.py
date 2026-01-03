"""PyInstaller 打包辅助模块。

此模块用于帮助 PyInstaller 发现所有懒加载的模块。

使用方法：
    在打包时，PyInstaller 会分析此文件并包含所有导入的模块。
"""

# 显式导入所有可用的模块，确保 PyInstaller 能发现它们
# 这些导入在运行时不会被执行（通过 if False 保护）

if False:
    # PyInstaller 会分析这些导入，即使它们在 if False 块中
    from ptk_repl.modules.core import CoreModule
    from ptk_repl.modules.database import DatabaseModule
    from ptk_repl.modules.ssh import SSHModule

    # 未来添加的模块也要在这里列出
    # from ptk_repl.modules.file import FileModule
    # from ptk_repl.modules.network import NetworkModule

# 导出所有模块类（供 PyInstaller 使用）
__all__ = [
    "CoreModule",
    "DatabaseModule",
    "SSHModule",
]
