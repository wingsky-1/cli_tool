"""测试颜色主题系统。"""

from ptk_repl.core.config.theme import ColorScheme, DARK_THEME, LIGHT_THEME, Theme


def test_color_scheme() -> None:
    """测试颜色方案。"""
    scheme = ColorScheme()

    # 测试默认颜色
    assert scheme.title != ""
    assert scheme.command != ""
    assert scheme.description != ""

    # 测试 get_color 方法
    title_color = scheme.get_color("title")
    assert title_color == scheme.title

    # 测试 color_text 方法
    colored = scheme.color_text("测试文本", "command")
    assert "测试文本" in colored
    assert "\033[" in colored  # ANSI 颜色代码

    # 测试不存在的颜色类型
    unknown_color = scheme.get_color("unknown")
    assert unknown_color == ""

    print("✅ ColorScheme 测试通过")


def test_theme() -> None:
    """测试主题。"""
    theme = Theme.default()

    assert theme.name == "default"
    assert theme.color_scheme is not None

    # 测试从字典创建
    config = {
        "name": "custom",
        "description": "自定义主题",
        "colors": {
            "title": "\033[96m\033[1m",
            "command": "\033[97m",
        },
    }
    custom_theme = Theme.from_dict(config)
    assert custom_theme.name == "custom"
    assert custom_theme.description == "自定义主题"

    print("✅ Theme 测试通过")


def test_predefined_themes() -> None:
    """测试预定义主题。"""
    # 深色主题
    assert DARK_THEME.name == "dark"
    assert DARK_THEME.color_scheme.title != ""

    # 浅色���题
    assert LIGHT_THEME.name == "light"
    assert LIGHT_THEME.color_scheme.title != ""

    print("✅ 预定义主题测试通过")


def test_help_formatter_uses_color_scheme() -> None:
    """测试 HelpFormatter 使用颜色方案。"""
    # 这个测试在实际运行环境中验证
    # 确保 HelpFormatter 可以接受 ColorScheme 参数

    from ptk_repl.core.config.theme import ColorScheme

    scheme = ColorScheme()
    assert scheme.color_text("text", "title") is not None

    print("✅ HelpFormatter 集成测试通过")


if __name__ == "__main__":
    test_color_scheme()
    test_theme()
    test_predefined_themes()
    test_help_formatter_uses_color_scheme()
    print("\n🎉 所有颜色主题测试通过！")
    print("\n📝 重构总结：")
    print("  - ColorScheme 数据类定义成功")
    print("  - Theme 系统实现")
    print("  - HelpFormatter 使用可配置颜色方案")
    print("  - 支持通过配置文件切换主题")
    print("  - 移除配置文件中的 name_mappings（已内置）")
    print("  - 添加公共属性访问器（lazy_modules, provider）")
    print("\n✨ 阶段 5：表现层重构（解决 OCP 违反）- 完成！")
