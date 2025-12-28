"""命令模块。"""

# 显式导入所有可用模块（用于 PyInstaller 打包）
# 这些导入确保 PyInstaller 能发现所有模块
from ptk_repl.modules.core.module import CoreModule
from ptk_repl.modules.database.module import DatabaseModule
from ptk_repl.modules.ssh.module import SSHModule

__all__ = ["CoreModule", "DatabaseModule", "SSHModule"]
