"""测试模块名称解析器。"""

from ptk_repl.core.resolvers import (
    ConfigurableResolver,
    DefaultModuleNameResolver,
    IModuleNameResolver,
)


def test_default_resolver():
    """测试默认解析器。"""
    resolver = DefaultModuleNameResolver()

    # 首字母大写
    assert resolver.resolve_class_name("database") == "Database"
    assert resolver.resolve_class_name("ssh") == "Ssh"
    assert resolver.resolve_class_name("api") == "Api"

    print("✅ DefaultModuleNameResolver 测试通过")


def test_configurable_resolver():
    """测试可配置解析器。"""
    # 默认映射
    resolver = ConfigurableResolver()
    assert resolver.resolve_class_name("ssh") == "SSH"
    assert resolver.resolve_class_name("api") == "API"
    assert resolver.resolve_class_name("database") == "Database"  # 默认规则

    # 自定义映射
    custom_resolver = ConfigurableResolver({"ssh": "SSH", "db": "DB"})
    assert custom_resolver.resolve_class_name("ssh") == "SSH"
    assert custom_resolver.resolve_class_name("db") == "DB"
    assert custom_resolver.resolve_class_name("api") == "Api"  # 默认规则

    print("✅ ConfigurableResolver 测试通过")


def test_protocol_duck_typing():
    """测试 Protocol 的鸭子类型。"""
    # 自定义解析器
    class CustomResolver:
        def resolve_class_name(self, module_name: str) -> str:
            return module_name.upper()

    resolver = CustomResolver()
    assert isinstance(resolver, IModuleNameResolver), "应该兼容接口"
    assert resolver.resolve_class_name("ssh") == "SSH"

    print("✅ Protocol 鸭子类型测试通过")


def test_module_loader_uses_resolver():
    """测试 ModuleLoader 使用解析器。"""
    from ptk_repl.core.cli.module_loader import ModuleLoader
    from ptk_repl.core import AutoCompleter, ConfigManager, CommandRegistry, StateManager

    # 创建带有自定义解析器的 ModuleLoader
    custom_resolver = ConfigurableResolver({"ssh": "SSH"})
    loader = ModuleLoader(
        registry=CommandRegistry(),
        state_manager=StateManager(),
        config=ConfigManager(),
        auto_completer=AutoCompleter(CommandRegistry()),
        register_commands_callback=lambda m: None,
        error_callback=lambda e: None,
        name_resolver=custom_resolver,
    )

    # 检查解析器是否正确注入
    assert loader._name_resolver is custom_resolver
    assert loader._name_resolver.resolve_class_name("ssh") == "SSH"

    print("✅ ModuleLoader 依赖注入测试通过")


if __name__ == "__main__":
    test_default_resolver()
    test_configurable_resolver()
    test_protocol_duck_typing()
    test_module_loader_uses_resolver()
    print("\n🎉 所有解析器测试通过！")
    print("\n📝 重构总结：")
    print("  - IModuleNameResolver Protocol 接口定义成功")
    print("  - DefaultModuleNameResolver 实现（首字母大写）")
    print("  - ConfigurableResolver 实现（可配置映射）")
    print("  - ModuleLoader 使用依赖注入")
    print("  - 配置文件支持 name_mappings")
    print("\n✨ 阶段 2：模块名称解析策略（解决 OCP 违反）- 完成！")
