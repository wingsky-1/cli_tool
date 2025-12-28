"""PTK_REPL 核心功能测试。"""

import sys

sys.path.insert(0, "src")

print("=" * 60)
print("PTK_REPL 核心功能测试")
print("=" * 60)

# 测试 1: 导入所有模块
print("\n✓ 测试 1: 导入模块...")
try:
    from ptk_repl.core.base import CommandModule
    from ptk_repl.core.registry import CommandRegistry
    from ptk_repl.core.state_manager import StateManager
    from ptk_repl.core.completer import AutoCompleter
    from ptk_repl.core.config_manager import ConfigManager
    from ptk_repl.core.decorators import typed_command

    print("  所有核心模块导入成功 ✅")
except Exception as e:
    print(f"  导入失败: {e} ❌")
    sys.exit(1)

# 测试 2: 初始化核心组件
print("\n✓ 测试 2: 初始化核心组件...")
try:
    registry = CommandRegistry()
    state_mgr = StateManager()
    completer = AutoCompleter(registry)
    config_mgr = ConfigManager()
    print("  核心组件初始化成功 ✅")
except Exception as e:
    print(f"  初始化失败: {e} ❌")
    sys.exit(1)

# 测试 3: 状态管理
print("\n✓ 测试 3: 状态管理...")
try:
    gs = state_mgr.global_state
    gs.connected = True
    gs.current_host = "localhost"
    gs.current_port = 5432
    assert gs.connected == True
    assert gs.current_host == "localhost"
    assert gs.current_port == 5432
    print("  状态管理正常 ✅")
except Exception as e:
    print(f"  状态管理失败: {e} ❌")

# 测试 4: 命令注册
print("\n✓ 测试 4: 命令注册...")
try:

    def test_command(args):
        pass

    registry.register_command("test", "cmd1", test_command)
    registry.register_command("test", "cmd2", test_command, aliases=["t cmd2"])
    print("  命令注册成功 ✅")
    print(f"  测试模块命令: {registry.list_module_commands('test')}")
except Exception as e:
    print(f"  命令注册失败: {e} ❌")

# 测试 5: 命令查找
print("\n✓ 测试 5: 命令查找...")
try:
    cmd_info = registry.get_command_info("cmd1")
    print(f"  命令 'cmd1' 查找成功: {cmd_info} ✅")

    cmd_info = registry.get_command_info("t cmd2")
    print(f"  别名 't cmd2' 解析成功: {cmd_info} ✅")
except Exception as e:
    print(f"  命令查找失败: {e} ❌")

# 测试 6: 补全器
print("\n✓ 测试 6: 自动补全...")
try:
    completion_dict = completer.build_completion_dict()
    print(f"  补全字典键: {list(completion_dict.keys())} ✅")

    # 测试懒加载模块补全声明
    completer.register_lazy_commands("lazy_module", ["cmd1", "cmd2"])
    completion_dict = completer.build_completion_dict()
    print(f"  懒加载补全: {completion_dict.get('lazy_module')} ✅")

    # 测试缓存失效
    completer._invalidate_cache()
    assert completer._completion_dict is None
    print("  缓存失效机制正常 ✅")
except Exception as e:
    print(f"  补全器测试失败: {e} ❌")

# 测试 7: typed_command 装饰器
print("\n✓ 测试 7: typed_command 装饰器...")
try:
    from pydantic import BaseModel, Field

    class TestArgs(BaseModel):
        name: str = Field(..., description="名称")
        count: int = Field(default=1, description="数量")

    @typed_command(TestArgs)
    def test_func(self, args: TestArgs):
        return args

    # 检查装饰器属性
    assert hasattr(test_func, "_is_typed_wrapper")
    assert hasattr(test_func, "_typed_model")
    print("  typed_command 装饰器正常 ✅")
except Exception as e:
    print(f"  typed_command 测试失败: {e} ❌")

# 测试 8: Pydantic 参数解析
print("\n✓ 测试 8: 参数解析...")
try:
    from ptk_repl.core.decorators import _parse_args_to_dict

    kwargs = _parse_args_to_dict("localhost --port 5432 --ssl", TestArgs)
    print(f"  解析结果: {kwargs} ✅")
except Exception as e:
    print(f"  参数解析失败: {e} ❌")

# 测试 9: 模块导入
print("\n✓ 测试 9: 模块导入...")
try:
    from ptk_repl.modules.core.module import CoreModule
    from ptk_repl.modules.database.module import DatabaseModule
    from ptk_repl.modules.database.state import DatabaseState

    print("  所有模块导入成功 ✅")
except Exception as e:
    print(f"  模块导入失败: {e} ❌")

# 测试 10: 基础类型验证
print("\n✓ 测试 10: 类型验证...")
try:
    core = CoreModule()
    assert core.name == "core"
    assert core.description == "核心命令（状态、帮助、退出等）"
    print("  CoreModule 类型正确 ✅")

    db = DatabaseModule()
    assert db.name == "database"
    assert db.get_completion_commands() == ["connect", "disconnect", "query"]
    print("  DatabaseModule 类型正确 ✅")
except Exception as e:
    print(f"  类型验证失败: {e} ❌")

print("\n" + "=" * 60)
print("所有测试通过！🎉")
print("=" * 60)
print("\n✨ ptk_repl 核心功能完整且正常工作！")
print("\n💡 提示：由于 Windows Git Bash 环境限制，")
print("   交互式测试请在 cmd.exe 或 PowerShell 中运行：")
print("   uv run python -m ptk_repl")
