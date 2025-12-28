# PTK_REPL 配置指南

## 配置文件位置

PTK_REPL 会按以下顺序查找配置文件：

1. `ptk_repl_config.yaml` - 当前工作目录
2. `config/ptk_repl.yaml` - 当前工作目录的 config 子目录
3. `~/.ptk_repl/config.yaml` - 用户主目录

如果未找到配置文件，将使用内置的默认配置。

## 默认配置

### 默认行为

```yaml
core:
  preload_modules: []  # 空：所有模块懒加载（除了 core）
```

**默认行为**：
- `core` 模块总是立即加载
- 其他模块（`database`、`file` 等）默认懒加载（按需加载）
- 启动速度快，只有在使用时才加载模块

## 配置选项

### 核心配置 (`core`)

```yaml
core:
  # 预加载的模块列表（可选）
  # 这些模块会在启动时立即加载，而不是懒加载
  preload_modules:
    - database  # 数据库模块在启动时加载
    - file      # 文件模块在启动时加载（如果已实现）
```

**说明**：
- `core` 模块不需要在 `preload_modules` 中指定，它总是立即加载
- 只有需要预加载的非 core 模块才需要在这里列出
- 空列表 `[]` 表示所有模块懒加载（默认行为）

### 补全配置 (`completions`)

```yaml
completions:
  # 启用自动补全
  enabled: true

  # 显示描述信息
  show_descriptions: true

  # 性能选项
  cache:
    # 启用缓存（提高补全响应速度）
    enabled: true
```

## 配置示例

### 示例 1: 全懒加载模式（最快启动）

```yaml
core:
  preload_modules: []  # 所有模块懒加载
```

**效果**：
- 启动最快
- 所有模块按需加载
- 第一次使用某模块时有轻微加载延迟

### 示例 2: 预加载 database 模块

```yaml
core:
  preload_modules:
    - database
```

**效果**：
- 启动时加载 `core` 和 `database`
- 其他模块（如 `file`）懒加载

### 示例 3: 预加载多个模块

```yaml
core:
  preload_modules:
    - database
    - file
```

**效果**：
- 启动时加载 `core`、`database` 和 `file`
- 适合需要频繁使用这些模块的场景

### 示例 4: 自定义补全行为

```yaml
completions:
  enabled: true
  show_descriptions: true
  cache:
    enabled: true
```

## 配置合并规则

用户配置会与默认配置**合并**，而不是完全替换：

- 如果用户配置中存在某个键，则使用用户配置的值
- 如果用户配置中不存在某个键，则使用默认配置的值
- 嵌套配置会递归合并

**示例**：

默认配置：
```yaml
core:
  preload_modules: []
completions:
  enabled: true
```

用户配置 (`ptk_repl_config.yaml`)：
```yaml
core:
  preload_modules:
    - database
```

最终配置：
```yaml
core:
  preload_modules: ["database"]  # 用户配置覆盖默认值
completions:
  enabled: true  # 默认配置保留
```

## 验证配置

运行 PTK_REPL 后，可以使用 `modules` 命令查看已加载的模块：

### 全懒加载模式

```bash
$ uv run python -m ptk_repl
欢迎使用 PTK REPL!
输入 'help' 查看帮助，'exit' 或 Ctrl+D 退出

(ptk) > modules
已加载的模块:
  • core (v1.0.0): 核心命令（状态、帮助、退出等）

(ptk) > database connect
# 此时 database 模块被懒加载
已连接到 localhost:5432

(ptk) > modules
已加载的模块:
  • core (v1.0.0): 核心命令（状态、帮助、退出等）
  • database (v1.0.0): 数据库操作（连接、查询、断开）
```

### 预加载模式

```bash
# ptk_repl_config.yaml:
# core:
#   preload_modules:
#     - database

$ uv run python -m ptk_repl
欢迎使用 PTK REPL!
输入 'help' 查看帮助，'exit' 或 Ctrl+D 退出

(ptk) > modules
已加载的模块:
  • core (v1.0.0): 核心命令（状态、帮助、退出等）
  • database (v1.0.0): 数据库操作（连接、查询、断开）
  # database 在启动时就已加载
```

## 无配置文件运行

如果没有配置文件，PTK_REPL 会使用默认配置：
- `core` 模块立即加载
- 所有其他模块懒加载
- 自动补全启用

这意味着您可以**零配置**开始使用 PTK_REPL！

## 性能考虑

| 配置 | 启动速度 | 首次命令延迟 | 适用场景 |
|------|---------|-------------|----------|
| 全懒加载 `[]` | ⭐⭐⭐⭐⭐ 最快 | 有轻微延迟 | 临时使用、偶尔使用模块 |
| 预加载部分模块 | ⭐⭐⭐ 中等 | 无延迟 | 频繁使用特定模块 |
| 预加载所有模块 | ⭐⭐ 较慢 | 无延迟 | 生产环境、需要所有模块就绪 |

**建议**：
- 开发/测试：使用全懒加载（默认）
- 生产环境：根据实际使用情况预加载常用模块
