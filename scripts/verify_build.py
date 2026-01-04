"""自动化验证 PyInstaller 打包后的可执行文件。

测试核心功能和懒加载模块。
"""

import subprocess
import sys
from pathlib import Path


def run_command(exe_path: Path, input_text: str, timeout: int = 10) -> tuple[bool, str]:
    """运行可执行文件并发送输入。

    Args:
        exe_path: 可执行文件路径
        input_text: 输入文本
        timeout: 超时时间（秒）

    Returns:
        (成功标志, 输出内容)
    """
    try:
        result = subprocess.run(
            [str(exe_path)],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",  # 替换无法解码的字符
        )
        output = result.stdout + result.stderr
        return True, output
    except subprocess.TimeoutExpired:
        return False, "超时"
    except Exception as e:
        return False, str(e)


def test_help(exe_path: Path) -> bool:
    """测试 help 命令。

    Args:
        exe_path: 可执行文件路径

    Returns:
        是否测试通过
    """
    print("测试 1: help 命令", end=" ... ")
    success, output = run_command(exe_path, "help\nexit\n")

    if not success:
        print("❌ (失败)")
        print(f"  错误: {output}")
        return False

    # 检查关键字
    keywords = ["核心命令", "状态", "帮助", "退出"]
    missing = [kw for kw in keywords if kw not in output]

    if missing:
        print("❌ (失败)")
        print(f"  缺少关键字: {missing}")
        print(f"  输出片段: {output[:500]}")
        return False

    print("✅ (通过)")
    return True


def test_status(exe_path: Path) -> bool:
    """测试 status 命令。

    Args:
        exe_path: 可执行文件路径

    Returns:
        是否测试通过
    """
    print("测试 2: status 命令", end=" ... ")
    success, output = run_command(exe_path, "status\nexit\n")

    if not success:
        print("❌ (失败)")
        print(f"  错误: {output}")
        return False

    if "未连接" not in output and "已连接" not in output:
        print("❌ (失败)")
        print("  未找到状态信息")
        print(f"  输出片段: {output[:500]}")
        return False

    print("✅ (通过)")
    return True


def test_modules(exe_path: Path) -> bool:
    """测试 modules 命令。

    Args:
        exe_path: 可执行文件路径

    Returns:
        是否测试通过
    """
    print("测试 3: modules 命令", end=" ... ")
    success, output = run_command(exe_path, "modules\nexit\n")

    if not success:
        print("❌ (失败)")
        print(f"  错误: {output}")
        return False

    # 检查核心模块
    if "core" not in output:
        print("❌ (失败)")
        print("  未找到 core 模块")
        print(f"  输出片段: {output[:500]}")
        return False

    print("✅ (通过)")
    return True


def test_lazy_loading(exe_path: Path) -> bool:
    """测试懒加载模块。

    Args:
        exe_path: 可执行文件路径

    Returns:
        是否测试通过
    """
    print("测试 4: 懒加载模块（ssh）", end=" ... ")
    success, output = run_command(exe_path, "ssh\nexit\n")

    if not success:
        print("❌ (失败)")
        print(f"  错误: {output}")
        return False

    # 检查是否显示帮助信息
    keywords = ["SSH", "环境", "日志"]
    missing = [kw for kw in keywords if kw not in output]

    if missing:
        print("❌ (失败)")
        print(f"  缺少关键字: {missing}")
        print(f"  输出片段: {output[:500]}")
        return False

    print("✅ (通过)")
    return True


def test_module_context(exe_path: Path) -> bool:
    """测试模块上下文切换。

    Args:
        exe_path: 可执行文件路径

    Returns:
        是否测试通过
    """
    print("测试 5: 模块上下文切换（use）", end=" ... ")
    success, output = run_command(exe_path, "use core\nexit\n")

    if not success:
        print("❌ (失败)")
        print(f"  错误: {output}")
        return False

    # 检查是否返回全局模式
    if "全局模式" not in output and "已返回" not in output:
        print("❌ (失败)")
        print("  未找到全局模式提示")
        print(f"  输出片段: {output[:500]}")
        return False

    print("✅ (通过)")
    return True


def main() -> int:
    """主函数。

    Returns:
        退出码
    """
    print("=" * 70)
    print("PTK_REPL 打包验证脚本")
    print("=" * 70)
    print()

    # 检查可执行文件是否存在
    exe_path = Path(__file__).parent.parent / "dist" / "ptk_repl.exe"

    if not exe_path.exists():
        print(f"❌ 可执行文件不存在: {exe_path}")
        print()
        print("请先运行打包脚本:")
        print("  uv run python scripts/build_ptk_repl.py")
        return 1

    print(f"可执行文件: {exe_path}")
    print(f"文件大小: {exe_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()

    # 运行测试
    tests = [
        test_help,
        test_status,
        test_modules,
        test_lazy_loading,
        test_module_context,
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test(exe_path):
            passed += 1
        else:
            failed += 1

    # 输出总结
    print()
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print(f"总计: {passed + failed} 个测试")
    print(f"通过: {passed} 个 ✅")
    print(f"失败: {failed} 个 ❌")
    print()

    if failed == 0:
        print("🎉 所有测试通过!")
        return 0
    else:
        print("⚠️  部分测试失败，请检查日志")
        return 1


if __name__ == "__main__":
    sys.exit(main())
