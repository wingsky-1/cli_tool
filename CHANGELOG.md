# Changelog

本文档记录 PTK_REPL 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

---

## [0.2.0] - 2026-01-03

### Added

- 🎉 **Protocol 接口系统** - 7个Protocol接口支持鸭子类型
  - ICliContext - CLI 上下文接口
  - IModuleLoader - 模块加载器接口
  - IModuleRegister - 模块注册器接口
  - IModuleDiscoverer - 模块发现器接口
  - ICommandResolver - 命令解析器接口
  - IPromptProvider - 提示符提供者接口
  - IRegistry - 命令注册表接口

- 🔧 **连接上下文抽象** - ConnectionContext 基类
  - SSHConnectionContext - SSH 连接上下文
  - DatabaseConnectionContext - 数据库连接上下文
  - GlobalState 组合多个连接上下文

- ⚡ **错误处理系统** - 责任链模式
  - CLIException 异常层次结构
  - ErrorHandlerChain 错误处理链
  - CLIErrorHandler 和 BaseErrorHandler

- 📦 **模块加载系统重构** - 4组件架构
  - LazyModuleTracker - 懒加载追踪器（O(1)别名查找）
  - UnifiedModuleLoader - 统一模块加载器
  - ModuleDiscoveryService - 自动发现服务
  - ModuleLifecycleManager - 生命周期管理器（门面模式）

- 🎯 **模块名称解析器** - 策略模式
  - DefaultModuleNameResolver - 默认解析策略
  - ConfigurableResolver - 可配置解析策略

### Changed

- ✨ **架构重构**：core目录按功能域重组（15个子包）
  - 按功能域分类：base/cli/completion/configuration/...
  - 单一职责原则：每个子包一个职责
  - 接口隔离原则：Protocol接口支持鸭子类型
  - 依赖倒置原则：高层依赖接口而非具体实现

- ✨ **模块加载器优化**：
  - 旧 ModuleLoader (183��) → 拆分为4个组件（454行）
  - 别名查找性能：O(n) → O(1)
  - 门面模式统一接口

- ✨ **连接上下文多态**：
  - 使用多态方法替代 isinstance 检查
  - 符合开闭原则（OCP）

- ✨ **AutoCompleter 公共接口扩展**：
  - 新增 `refresh()` 公共方法
  - 支持懒加载后自动刷新补全缓存

- ✨ **CommandRegistry 公共接口扩展**：
  - 新增 `get_module()` 公共方法
  - 支持设置和获取已注册模块

### Fixed

- 修复 ModuleManager 使用旧的 ModuleLoader 导致的运行时错误
- 修复模块名称解析的类型注解问题

### Removed

- 删除旧 ModuleLoader（core/cli/module_loader.py）
- 删除简化版 ModuleLoader（core/loaders/module_loader.py）
- 删除 ModuleManager 适配器（core/loaders/module_manager.py）

### 统计

- **提交数**: 30个
- **文件变更**: 86个文件
- **代码变更**: +3360行，0行删除
- **重构耗时**: 1天

---

## [0.1.0] - 2025-12-28

### Added

- 🎉 初始版本发布
- 基于模块化架构的 CLI 框架
- 支持 SSH 连接管理和日志查看
- Pydantic v2 参数验证
- 自动命令补全系统
- 双层状态管理（全局 + 模块）

### Changed

- ✨ 架构重构：拆分 PromptToolkitCLI
  - cli.py: 526 行 → 246 行（减少 53%）
  - 提取 StyleManager、PromptManager、ModuleLoader、CommandExecutor
  - 单一职责原则，依赖注入

- ✨ 架构重构：拆分 SSH 模块
  - module.py: 327 行 → 136 行（减少 58%）
  - 提取 SSHConnectionManager、SSHLogViewer
  - 消除重复代码，提升可维护性

### Fixed

- 修复类型注解问题
- 完善前向引用处理

---

## 版本说明

- **Added**: 新增功能
- **Changed**: 功能变更
- **Deprecated**: 即将废弃的功能
- **Removed**: 删除的功能
- **Fixed**: Bug 修复
- **Security**: 安全问题修复
