"""测试 Protocol 接口的鸭子类型支持。"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from ptk_repl.core.interfaces import (
    ICliContext,
    ICommandResolver,
    IModuleDiscoverer,
    IModuleLoader,
    IModuleRegister,
    IPromptProvider,
    IRegistry,
)
from ptk_repl.core.base.command_module import CommandModule
from ptk_repl.core.state.state_manager import StateManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ptk_repl.cli.cli import PromptToolkitCLI


# ===== Mock 实现类 =====


class MockCliContext:
    """模拟 CLI 上下文（实现 ICliContext）。"""

    def __init__(self) -> None:
        self.output_log: list[str] = []
        self.error_log: list[str] = []
        self._state = StateManager()
        self._registry = None  # 简化

    def poutput(self, text: str) -> None:
        """输出普通消息。"""
        self.output_log.append(text)

    def perror(self, text: str) -> None:
        """输出错误消息。"""
        self.error_log.append(text)

    @property
    def state(self) -> StateManager:
        return self._state

    @property
    def registry(self):
        return self._registry


class MockModuleLoader:
    """模拟模块加载器（实现 IModuleLoader）。"""

    def __init__(self) -> None:
        self._loaded: dict[str, CommandModule] = {}
        self._lazy: dict[str, type] = {}

    def load(self, module_name: str) -> CommandModule | None:
        """加载模块。"""
        return self._loaded.get(module_name)

    def is_loaded(self, module_name: str) -> bool:
        """检查模块是否已加载。"""
        return module_name in self._loaded

    def ensure_module_loaded(self, module_name: str) -> None:
        """确保模块已加载。"""
        if not self.is_loaded(module_name):
            self.load(module_name)

    @property
    def loaded_modules(self) -> dict[str, CommandModule]:
        return self._loaded.copy()

    @property
    def lazy_modules(self) -> dict[str, type]:
        return self._lazy.copy()


class MockModuleRegister:
    """模拟模块注册器（实现 IModuleRegister）。"""

    def __init__(self) -> None:
        self._modules: dict[str, CommandModule] = {}

    def register(self, module: CommandModule) -> None:
        """注册模块。"""
        self._modules[module.name] = module

    def is_registered(self, module_name: str) -> bool:
        """检查模块是否已注册。"""
        return module_name in self._modules

    def get_module(self, module_name: str) -> CommandModule | None:
        """获取模块。"""
        return self._modules.get(module_name)


class MockModuleDiscoverer:
    """模拟模块发现器（实现 IModuleDiscoverer）。"""

    def discover(self) -> list[str]:
        """发现所有可用模块。"""
        return ["core", "ssh", "database"]

    def is_available(self, module_name: str) -> bool:
        """检查模块是否可用。"""
        return module_name in ["core", "ssh", "database"]


class MockCommandResolver:
    """模拟命令解析器（实现 ICommandResolver）。"""

    def resolve(self, module_name: str) -> str:
        """解析模块名称为类名。"""
        return f"{module_name.capitalize()}Module"


class MockPromptProvider:
    """模拟提示符提供者（实现 IPromptProvider）。"""

    def get_prompt(self) -> str:
        """获取提示符字符串。"""
        return "(ptk) "


class MockRegistry:
    """模拟命令注册表（实现 IRegistry）。"""

    def __init__(self) -> None:
        self._modules: dict[str, CommandModule] = {}
        self._commands: dict[str, tuple] = {}
        self._aliases: dict[str, str] = {}

    def register_command(
        self,
        module_name: str,
        command_name: str,
        handler,
        aliases: list[str] | None,
    ) -> None:
        """注册命令。"""
        self._commands[command_name] = (module_name, command_name, handler)
        if aliases:
            for alias in aliases:
                self._aliases[alias] = command_name

    def get_command_info(self, command_path: str) -> tuple | None:
        """获取命令信息。"""
        return self._commands.get(command_path)

    def get_module(self, module_name: str) -> CommandModule | None:
        """获取模块。"""
        return self._modules.get(module_name)

    def get_all_commands(self) -> dict:
        """获取所有命令。"""
        return self._commands.copy()

    def get_all_aliases(self) -> dict[str, str]:
        """获取所有别名。"""
        return self._aliases.copy()

    def list_modules(self) -> list:
        """列出所有模块。"""
        return list(self._modules.values())

    def list_module_commands(self, module_name: str) -> list[str]:
        """列出模块命令。"""
        return [
            cmd for cmd, (mod, _, _) in self._commands.items()
            if mod == module_name
        ]

    def set_completer(self, completer: object) -> None:
        """设置补全器。"""
        pass


# ===== 测试类 =====


class TestProtocolInterfaces:
    """Protocol 接口鸭子类型测试。"""

    def test_iclicontext_duck_typing(self) -> None:
        """测试 ICliContext 鸭子类型。"""
        mock_cli = MockCliContext()

        # 类型注解（静态类型检查）
        cli: ICliContext = mock_cli

        # 运行时检查
        assert isinstance(cli, ICliContext)

        # 调用方法
        cli.poutput("test message")
        cli.perror("error message")

        # 验证
        assert "test message" in mock_cli.output_log
        assert "error message" in mock_cli.error_log

    def test_imoduleloader_duck_typing(self) -> None:
        """测试 IModuleLoader 鸭子类型。"""
        mock_loader = MockModuleLoader()

        # 类型注解
        loader: IModuleLoader = mock_loader

        # 运行时检查
        assert isinstance(loader, IModuleLoader)

        # 调用方法
        assert not loader.is_loaded("test")
        assert loader.load("test") is None
        loader.ensure_module_loaded("test")

        # 访问属性
        assert isinstance(loader.loaded_modules, dict)
        assert isinstance(loader.lazy_modules, dict)

    def test_imoduleregister_duck_typing(self) -> None:
        """测试 IModuleRegister 鸭子类型。"""
        mock_register = MockModuleRegister()

        # 类型注解
        register: IModuleRegister = mock_register

        # 运行时检查
        assert isinstance(register, IModuleRegister)

        # 创建模拟模块
        class TestModule(CommandModule):
            @property
            def name(self) -> str:
                return "test"

            @property
            def description(self) -> str:
                return "Test"

            def register_commands(self, cli) -> None:
                pass

        module = TestModule()

        # 调用方法
        assert not register.is_registered("test")
        register.register(module)
        assert register.is_registered("test")
        assert register.get_module("test") is module

    def test_imodulediscoverer_duck_typing(self) -> None:
        """测试 IModuleDiscoverer 鸭子类型。"""
        mock_discoverer = MockModuleDiscoverer()

        # 类型注解
        discoverer: IModuleDiscoverer = mock_discoverer

        # 运行时检查
        assert isinstance(discoverer, IModuleDiscoverer)

        # 调用方法
        modules = discoverer.discover()
        assert "core" in modules
        assert "ssh" in modules
        assert "database" in modules

        # 测试 is_available
        assert discoverer.is_available("ssh")
        assert not discoverer.is_available("nonexistent")

    def test_icommandresolver_duck_typing(self) -> None:
        """测试 ICommandResolver 鸭子类型。"""
        mock_resolver = MockCommandResolver()

        # 类型注解
        resolver: ICommandResolver = mock_resolver

        # 运行时检查
        assert isinstance(resolver, ICommandResolver)

        # 调用方法
        assert resolver.resolve("ssh") == "SshModule"
        assert resolver.resolve("database") == "DatabaseModule"

    def test_ipromptprovider_duck_typing(self) -> None:
        """测试 IPromptProvider 鸭子类型。"""
        mock_provider = MockPromptProvider()

        # 类型注解
        provider: IPromptProvider = mock_provider

        # 运行时检查
        assert isinstance(provider, IPromptProvider)

        # 调用方法
        prompt = provider.get_prompt()
        assert prompt == "(ptk) "

    def test_incomplete_implementation(self) -> None:
        """测试不完整实现的识别。"""

        class IncompleteCli:
            """不完整的 CLI 实现（缺少 perror）。"""

            def poutput(self, text: str) -> None:
                print(text)

            @property
            def state(self):
                return None

            @property
            def registry(self):
                return None

        incomplete = IncompleteCli()

        # 运行时检查应该失败
        assert not isinstance(incomplete, ICliContext)

    def test_all_interfaces_runtime_checkable(self) -> None:
        """测试所有接口都是 runtime_checkable。"""
        # 所有 Protocol 接口都应该支持 isinstance 检查
        mock_cli = MockCliContext()
        mock_loader = MockModuleLoader()
        mock_register = MockModuleRegister()
        mock_discoverer = MockModuleDiscoverer()
        mock_resolver = MockCommandResolver()
        mock_provider = MockPromptProvider()
        mock_registry = MockRegistry()

        # 验证所有接口都支持运行时检查
        assert isinstance(mock_cli, ICliContext)
        assert isinstance(mock_loader, IModuleLoader)
        assert isinstance(mock_register, IModuleRegister)
        assert isinstance(mock_discoverer, IModuleDiscoverer)
        assert isinstance(mock_resolver, ICommandResolver)
        assert isinstance(mock_provider, IPromptProvider)
        assert isinstance(mock_registry, IRegistry)
