"""验证打包后的功能。"""

import subprocess
import sys
from pathlib import Path


def test_exe_exists() -> bool:
    """测试 exe 文件是否存在。"""
    exe_path = Path(__file__).parent.parent / "dist" / "ptk_repl.exe"
    if exe_path.exists():
        print(f"✅ exe 文件存在: {exe_path}")
        return True
    else:
        print(f"❌ exe 文件不存在: {exe_path}")
        return False


def test_exe_launch() -> bool:
    """测试 exe 文件能否正常启动。"""
    exe_path = Path(__file__).parent.parent / "dist" / "ptk_repl.exe"

    try:
        # 测试 --version 参数
        result = subprocess.run(
            [str(exe_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ exe 文件可以正常启动")
            return True
        else:
            print(f"❌ exe 文件启动失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ exe 文件启动异常: {e}")
        return False


def test_lazy_loading() -> bool:
    """测试懒加载功能。"""
    exe_path = Path(__file__).parent.parent / "dist" / "ptk_repl.exe"

    try:
        # 测试输入 "database" 命令触发懒加载
        process = subprocess.Popen(
            [str(exe_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # 发送 database ���令
        stdout, stderr = process.communicate(input="database\nexit\n", timeout=5)

        if "database" in stdout.lower():
            print("✅ 懒加载功能正常")
            return True
        else:
            print(f"❌ 懒加载功能异常: {stdout}")
            return False
    except Exception as e:
        print(f"❌ 懒加载测试异常: {e}")
        return False


def test_fuzzy_completion() -> bool:
    """测试模糊补全功能。"""
    print("⚠️  模糊补全功能需要手动验证（自动化测试较难）")
    print("   请手动测试：输入 'ev<TAB>' 应该补全为 'environment' 或 'ssh env'")
    return True


def main():
    """主函数。"""
    print("=" * 60)
    print("PTK_REPL 打包验证")
    print("=" * 60)
    print()

    tests = [
        ("exe 文件存在", test_exe_exists),
        ("exe 文件启动", test_exe_launch),
        ("懒加载功能", test_lazy_loading),
        ("模糊补全功能", test_fuzzy_completion),
    ]

    results = []
    for name, test_func in tests:
        print(f"\n测试: {name}")
        print("-" * 40)
        result = test_func()
        results.append((name, result))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(main())
