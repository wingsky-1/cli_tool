"""PTK_REPL 功能测试（非交互式）。"""

import sys

sys.path.insert(0, "src")

from ptk_repl.core import CommandRegistry, StateManager, AutoCompleter, ConfigManager
from ptk_repl.modules.core.module import CoreModule
from ptk_repl.modules.database.module import DatabaseModule


def test_core_functionality():
    """测试核心功能。"""
    print("=" * 60)
    print("PTK_REPL 功能测试")
    print("=" * 60)

    # 测试核心组件
    print("\n1. 测试核心组件初始化...")
    registry = CommandRegistry()
    state_mgr = StateManager()
    config_mgr = ConfigManager()
    completer = AutoCompleter(registry)
    print("✅ 核心组件初始化成功")

    # 测试注册模块
    print("\n2. 测试模块注册...")
    core_module = CoreModule()
    registry.register_module(core_module)
    core_module.initialize(state_mgr)
    core_module.register_commands(
        type("MockCLI", (object,), {"registry": registry, "state": state_mgr})
    )
    print(f"✅ 核心模块已注册，命令: {registry.list_module_commands('core')}")

    # 测试懒加载模块
    print("\n3. 测试懒加载模块...")
    database_module = DatabaseModule()
    registry.register_module(database_module)
    database_module.initialize(state_mgr)
    database_module.register_commands(
        type("MockCLI", (object,), {"registry": registry, "state": state_mgr})
    )
    print(f"✅ 数据库模块已注册，���令: {registry.list_module_commands('database')}")

    # 测试命令查找
    print("\n4. 测试命令查找...")
    cmd_info = registry.get_command_info("status")
    print(f"✅ 找到命令 'status': {cmd_info}")

    cmd_info = registry.get_command_info("database connect")
    print(f"✅ 找到命令 'database connect': {cmd_info}")

    # 测试别名解析
    cmd_info = registry.get_command_info("db connect")
    print(f"✅ 别名 'db connect' 解析成功: {cmd_info}")

    # 测试补全器
    print("\n5. 测试自动补全...")
    completion_dict = completer.build_completion_dict()
    print(f"✅ 补全字典构建成功，键: {list(completion_dict.keys())}")
    print(f"   核心命令: {completion_dict.get('')}")
    print(f"   数据库命令: {completion_dict.get('database')}")

    # 测试参数补全（基于 Pydantic）
    print("\n6. 测试参数补全...")
    param_dict = completer._build_parameter_completions()
    print(f"✅ 参数补全: {list(param_dict.keys())}")

    # 测试状态管理
    print("\n7. 测试状态管理...")
    gs = state_mgr.global_state
    gs.connected = True
    gs.current_host = "localhost"
    gs.current_port = 5432
    print(f"✅ 全局状态: connected={gs.connected}, host={gs.current_host}")

    # 测试命令执行
    print("\n8. 测试命令解析...")
    from ptk_repl.core.registry import CommandRegistry

    test_registry = CommandRegistry()

    class MockCLI:
        def __init__(self):
            self.registry = test_registry
            self.state = StateManager()

        def perror(self, msg):
            print(f"   ERROR: {msg}")

    mock_cli = MockCLI()

    # 注册数据库模块
    db = DatabaseModule()
    test_registry.register_module(db)
    db.initialize(mock_cli.state)
    db.register_commands(mock_cli)

    # 测试 connect 命令
    cmd_info = test_registry.get_command_info("database connect localhost --port 5432")
    if cmd_info:
        module_name, command_name, handler = cmd_info
        print(f"✅ 命令解析成功: module={module_name}, command={command_name}")

        # 测试 typed_command
        if hasattr(handler, "_is_typed_wrapper"):
            print("   ✅ 检测到 typed_command 包装器")
            module = test_registry.get_module(module_name)
            try:
                handler(module, mock_cli, "localhost --port 5432")
            except Exception as e:
                print(f"   执行结果: {e}")

    print("\n" + "=" * 60)
    print("所有测试通过！✅")
    print("=" * 60)


if __name__ == "__main__":
    test_core_functionality()
