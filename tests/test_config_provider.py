"""测试配置提供者。"""

import os
from pathlib import Path

from ptk_repl.core.configuration.providers import (
    CompositeConfigProvider,
    EnvConfigProvider,
    IConfigProvider,
    YamlConfigProvider,
)


def test_yaml_config_provider() -> None:
    """测试 YAML 配置提供者。"""
    # 创建临时配置文件
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
core:
  preload_modules:
    - ssh
    - database
completions:
  enabled: true
""")
        config_path = f.name

    try:
        provider = YamlConfigProvider(config_path)

        # 测试 get 方法
        assert provider.get("core.preload_modules") == ["ssh", "database"]
        assert provider.get("completions.enabled") is True
        assert provider.get("nonexistent.key", "default") == "default"

        # 测试 has 方法
        assert provider.has("core.preload_modules")
        assert not provider.has("nonexistent.key")

        print("✅ YamlConfigProvider 测试通过")
    finally:
        os.unlink(config_path)


def test_env_config_provider() -> None:
    """测试环境变量配置提供者。"""
    # 设置环境变量
    os.environ["PTK_SSH_ENVIRONMENTS"] = "prod"
    os.environ["PTK_COMPLETIONS_ENABLED"] = "true"

    provider = EnvConfigProvider(prefix="PTK_")

    # 测试 get 方法
    assert provider.get("ssh.environments") == "prod"
    assert provider.get("completions.enabled") == "true"
    assert provider.get("nonexistent.key", "default") == "default"

    # 测试 has 方��
    assert provider.has("ssh.environments")
    assert not provider.has("nonexistent.key")

    # 清理环境变量
    del os.environ["PTK_SSH_ENVIRONMENTS"]
    del os.environ["PTK_COMPLETIONS_ENABLED"]

    print("✅ EnvConfigProvider 测试通过")


def test_composite_config_provider() -> None:
    """测试组合配置提供者。"""
    import tempfile

    # 创建临时 YAML 配置
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
core:
  preload_modules:
    - ssh
""")
        yaml_path = f.name

    # 设置环境变量
    os.environ["PTK_CORE_PRELOAD_MODULES"] = "database"

    try:
        # 创建提供者链：环境变量优先级高于 YAML
        yaml_provider = YamlConfigProvider(yaml_path)
        env_provider = EnvConfigProvider(prefix="PTK_")
        composite = CompositeConfigProvider([yaml_provider, env_provider])

        # 环境变量应该覆盖 YAML 配置
        assert composite.get("core.preload_modules") == "database"

        # 测试 has 方法
        assert composite.has("core.preload_modules")

        print("✅ CompositeConfigProvider 测试通过")
    finally:
        os.unlink(yaml_path)
        del os.environ["PTK_CORE_PRELOAD_MODULES"]


def test_protocol_duck_typing() -> None:
    """测试 Protocol 的鸭子类型。"""
    # 自定义配置提供者
    class CustomProvider:
        def get(self, key: str, default=None):
            return f"custom_{key}"

        def has(self, key: str) -> bool:
            return True

    provider = CustomProvider()
    assert isinstance(provider, IConfigProvider), "应该兼容接口"
    assert provider.get("test") == "custom_test"

    print("✅ Protocol 鸭子类型测试通过")


def test_config_manager_uses_provider() -> None:
    """测试 ConfigManager 使用配置提供者。"""
    from ptk_repl.core.configuration.config_manager import ConfigManager

    # 创建自定义提供者
    custom_provider = YamlConfigProvider(Path.cwd() / "ptk_repl_config.yaml")
    config = ConfigManager(provider=custom_provider)

    # 检查提供者是否正确注入
    assert config._provider is custom_provider

    print("✅ ConfigManager 依赖注入测试通过")


if __name__ == "__main__":
    test_yaml_config_provider()
    test_env_config_provider()
    test_composite_config_provider()
    test_protocol_duck_typing()
    test_config_manager_uses_provider()
    print("\n🎉 所有配置提供者测试通过！")
    print("\n📝 重构总结：")
    print("  - IConfigProvider Protocol 接口定义成功")
    print("  - YamlConfigProvider 实现（从 YAML 文件加载）")
    print("  - EnvConfigProvider 实现（从环境变量加载）")
    print("  - CompositeConfigProvider 实现（优先级合并）")
    print("  - ConfigManager 使用依赖注入")
    print("  - 内置 name_mappings 到 DEFAULT_CONFIG")
    print("\n✨ 阶段 4：配置系统重构（解决 SRP 违反）- 完成！")
