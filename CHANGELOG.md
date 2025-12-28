# 更新日志

本文件记录项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.0] - 2025-12-28

### 变更
- 将 myrepl（基于 cmd2）归档到 archive/myrepl/
- 主项目聚焦到 ptk_repl（基于 prompt-toolkit）
- 更新项目入口点和配置

### 移除
- myrepl 源代码从主项目移除（已归档）
- myrepl 相关文档已归档
- myrepl 相关测试已归档

## [未发布]

### 新增
- 基于 cmd2 + Pydantic v2 的模块化 CLI 框架
- 双层状态管理（全局状态 + 模块隔离状态）
- 配置驱动的模块加载系统
- 命令别名支持（短命令、多别名）
- YAML 配置文件支持
- 懒加载机制（核心模块立即加载，扩展模块按需加载）

### 内置模块
- **Core 模块** - 核心命令（status, exit, quit）
- **Database 模块** - 数据库操作示例（connect, query, disconnect）
- **File 模块** - 文件操作示例（read, write）

### 开发工具
- Pre-commit hooks（ruff, mypy）
- 代码质量检查（ruff lint + format, mypy strict）
- PyInstaller 打包支持

### 文档
- 模块开发指南
- PyInstaller 打包指南
- 实现阶段文档
- 原始设计文档

## [0.1.0] - 2025-12-27

### 新增
- 项目初始化
- 核心框架实现
- 示例模块（database, file）

---

## 版本说明

- **[未发布]** - 正在开发中的版本
- **[0.1.0]** - 初始发布版本

## 变更类型

- **新增** - 新功能
- **变更** - 现有功能的变更
- **弃用** - 即将移除的功能
- **移除** - 已移除的功能
- **修复** - Bug 修复
- **安全** - 安全相关修复
