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
