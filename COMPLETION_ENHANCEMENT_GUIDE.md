# 补全系统增强 - 完整实现指南

## 目录

1. [架构分析](#架构分析)
2. [实现方案](#实现方案)
3. [性能优化](#性能优化)
4. [测试策略](#测试策略)
5. [部署计划](#部署计划)

---

## 架构分析

### 当前补全系统架构

```
PromptToolkitCLI (cli.py)
    ↓
AutoCompleter (core/completion/auto_completer.py)
    ↓
CommandRegistry (core/registry/command_registry.py)
    ↓
PromptSession (prompt_toolkit)
```

#### 现有组件

| 组件 | 文件 | 职责 | 状态 |
|------|------|------|------|
| **AutoCompleter** | `auto_completer.py` | 自动补全逻辑 | ✅ 已实现 |
| **CommandRegistry** | `command_registry.py` | 命令注册和管理 | ✅ 已实现 |
| **TypedCommand** | `decoration/typed_command.py` | 类型安全命令装饰器 | ✅ 已实现 |
| **FuzzyMatcher** | ❌ 不存在 | 模糊匹配算法 | ❌ 需实现 |

#### 补全流程

```
用户输入 → PromptSession
         → AutoCompleter.get_completions()
         → build_completion_dict()
         → 上下文判断（命令/模块/参数）
         → 前缀匹配（startswith）
         → 生成 Completion 对象
         → 显示给用户
```

### 问题诊断

#### 问题 1：参数补全未生效

**根本原因**：
```python
# L272-278: 上下文判断逻辑有误
else:
    # 更多词 - 可能是参数补全
    prefix = " ".join(words[:-1])
    word = words[-1]

# 问题：没有检查 word 是否以 -- 或 - 开头
# 导致参数补全字典已生成，但未正确触发
```

**修复方案**：
```python
# 修复后：在开头检查参数输入模式
if words[-1].startswith("-"):
    # 参数补全模式
    param_completions = self._get_parameter_completions_for_context(...)
    # ... 生成参数补全
    return
```

#### 问题 2：无模糊匹配

**当前实现**：
```python
# L284: 只有前缀匹配
matches = [c for c in candidates if c.startswith(word)]
```

**限制**：
- 无法处理子序列匹配（`ev` → `ssh env`）
- 无法容错输入错误（`envm` → `env`）
- 用户体验不友好

**解决方案**：集成 `FuzzyMatcher`

#### 问题 3：懒加载模块补全不完整

**当前实现**：
```python
# L130-155: 懒加载模块补全
for module_name, commands in self._lazy_module_commands.items():
    if module_name not in completion_dict:
        completion_dict[module_name] = sorted(commands)
```

**问题**：
- 未集成到顶层补全（`""`）
- 需要手动调用 `register_lazy_commands()`

**优化**：自动发现懒加载模块名

---

## 实现方案

### 文件结构

```
src/ptk_repl/core/completion/
├── __init__.py                         # 导出 FuzzyMatcher 和 AutoCompleter
├── auto_completer.py                   # 修改：集成模糊匹配和修复参数补全
└── fuzzy_matcher.py                    # 新建：模糊匹配算法

tests/
├── test_auto_completer.py              # 更新：集成测试
└── test_fuzzy_matcher.py               # 新建：模糊匹配单元测试
```

### 步骤 1：创建 FuzzyMatcher

**文件**：`src/ptk_repl/core/completion/fuzzy_matcher.py`

**关键类和方法**：

```python
class FuzzyMatcher:
    def match(self, query: str, candidates: Sequence[str]) -> list[MatchResult]:
        """主入口：返回排序后的匹配结果"""

    def _subsequence_match(self, query: str, candidate: str) -> float:
        """子序列匹配评分（50-90 分）"""

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """编辑距离计算（动态规划）"""
```

**算法复杂度**：
- 前缀匹配：O(n * m)，n=候选数，m=字符串长度
- 子序列匹配：O(n * m * k)，k=子序列长度
- Levenshtein：O(n * m * k²)，最坏情况

**代码位置**：见 `fuzzy_matcher_implementation.py`

### 步骤 2：修复 AutoCompleter 参数补全

**文件**：`src/ptk_repl/core/completion/auto_completer.py`

**修改点**：

#### 修改 1：添加模糊匹配器初始化

```python
# L34-50: __init__() 方法
def __init__(self, registry: IRegistry, enable_fuzzy: bool = True) -> None:
    self._registry = registry
    self._enable_fuzzy = enable_fuzzy
    self._fuzzy_matcher = FuzzyMatcher(...)
```

#### 修改 2：增强 get_completions() 方法

```python
# L234-293: get_completions() 方法

# ===== 在开头添加参数补全检查 =====
def get_completions(self, document, complete_event):
    text = document.text_before_cursor
    words = text.split()

    if not words:
        return

    # ===== 核心修改：参数补全 =====
    if words[-1].startswith("-"):
        param_completions = self._get_parameter_completions_for_context(...)
        for match in sorted(param_completions):
            if match.startswith(words[-1]):
                yield Completion(...)
        return

    # ===== 原有逻辑：命令和模块补全 =====
    # ...
```

#### 修改 3：集成模糊匹配

```python
# ===== 替换 L284 的前缀匹配 =====
if self._enable_fuzzy and word:
    match_results = self._fuzzy_matcher.match(word, candidates)
    matches = [r.candidate for r in match_results if r.score > 50]
else:
    matches = [c for c in candidates if c.startswith(word)]
```

#### 修改 4：新增辅助方法

```python
# 新增方法：获取参数补全（上下文感知）
def _get_parameter_completions_for_context(
    self, context_words: list[str], current_param: str, completion_dict: dict
) -> list[str]:
    """获取参数补全列表"""
    if not context_words:
        return []

    full_command = " ".join(context_words)
    full_command = self._resolve_alias(full_command)
    params = completion_dict.get(full_command, [])
    return [p for p in params if p.startswith("-")]
```

### 步骤 3：增强懒加载模块补全

**修改位置**：`build_completion_dict()` 方法（L90-175）

**修改点**：

```python
# L130-155: 增强懒加载模块集成

# 收集所有模块名（已加载 + 懒加载）
all_modules = set()

# 已加载模块
for module in self._registry.list_modules():
    if module.name != "core":
        all_modules.add(module.name)
        short_name = self._get_short_alias(module.name)
        if short_name:
            all_modules.add(short_name)

# 懒加载模块
for module_name in self._lazy_module_commands.keys():
    all_modules.add(module_name)
    short_name = self._get_short_alias(module_name)
    if short_name:
        all_modules.add(short_name)

# 合并到顶层补全
completion_dict[""].extend(sorted(all_modules))
```

### 步骤 4：更新导出

**文件**：`src/ptk_repl/core/completion/__init__.py`

```python
"""自动补全包。"""

from ptk_repl.core.completion.auto_completer import AutoCompleter
from ptk_repl.core.completion.fuzzy_matcher import FuzzyMatcher, fuzzy_match

__all__ = ["AutoCompleter", "FuzzyMatcher", "fuzzy_match"]
```

---

## 性能优化

### 性能分析

#### 当前性能

| 操作 | 复杂度 | 耗时（估算） |
|------|--------|--------------|
| 构建补全字典 | O(n) | ~10ms（100个命令） |
| 前缀匹配 | O(n * m) | ~1ms |
| 模糊匹配（子序列） | O(n * m * k) | ~5-10ms |
| Levenshtein 距离 | O(n * m * k²) | ~20-50ms |

#### 优化策略

1. **分层匹配**（优先级策略）
   ```
   前缀匹配（最快） → 子序列匹配（中等） → Levenshtein（最慢）
   ```

2. **缓存优化**
   ```python
   # 缓存补全字典
   self._completion_dict: dict[str, list[str]] | None = None

   # 缓存模糊匹配结果（可选）
   self._fuzzy_match_cache: dict[tuple[str, str], list[MatchResult]] = {}
   ```

3. **惰性计算**
   ```python
   # 只在首次补全时触发模块发现
   if self._lazy_module_discovered is False:
       self._discover_lazy_modules()
       self._lazy_module_discovered = True
   ```

4. **并行处理**
   ```python
   # 利用 prompt_toolkit 的 complete_in_thread=True
   # 在后台线程中执行模糊匹配
   ```

### 性能目标

| 场景 | 目标延迟 | 优化措施 |
|------|----------|----------|
| 命令补全（前缀） | < 5ms | 无需优化（已达标） |
| 模糊匹配（子序列） | < 15ms | 缓存 + 并行 |
| Levenshtein 距离 | < 50ms | 限制候选数 + 距离阈值 |

---

## 测试策略

### 单元测试

#### FuzzyMatcher 测试

**文件**：`tests/test_fuzzy_matcher.py`

```python
class TestFuzzyMatcher:
    def test_prefix_match(self):
        """测试前缀匹配"""

    def test_subsequence_match(self):
        """测试子序列匹配"""

    def test_levenshtein_match(self):
        """测试编辑距离匹配"""

    def test_scoring_priority(self):
        """测试评分优先级"""

    def test_case_insensitive(self):
        """测试大小写不敏感"""
```

#### AutoCompleter 测试（更新）

**文件**：`tests/test_auto_completer.py`

```python
class TestAutoCompleter:
    def test_parameter_completion_trigger(self):
        """测试参数补全触发"""

    def test_fuzzy_matching_integration(self):
        """测试模糊匹配集成"""

    def test_lazy_module_completion(self):
        """测试懒加载模块补全"""
```

### 集成测试

**场景**：
1. 输入 `database connect --h` → 显示 `--host`
2. 输入 `ev` → 显示 `environment`, `ssh env`
3. 输入 `db` → 显示 `database`（模块名）
4. 输入 `envm` → 显示 `env`（编辑距离）

### 性能测试

```python
def test_performance():
    """测试补全性能"""
    completer = AutoCompleter(registry, enable_fuzzy=True)

    # 1000 次补全操作
    start = time.time()
    for _ in range(1000):
        completions = list(completer.get_completions(mock_doc, mock_event))

    elapsed = time.time() - start
    assert elapsed < 1.0  # 平均每次 < 1ms
```

---

## 部署计划

### 阶段 1：实现和测试（第 1-2 天）

- [ ] 创建 `fuzzy_matcher.py`
- [ ] 修改 `auto_completer.py`
- [ ] 编写单元测试
- [ ] 运行测试并修复 bug

### 阶段 2：集成和优化（第 3 天）

- [ ] 集成到现有系统
- [ ] 性能测试和优化
- [ ] 更新文档

### 阶段 3：验证和发布（第 4 天）

- [ ] 手动测试所有场景
- [ ] 代码审查
- [ ] 合并到主分支

### 回滚计划

如果出现问题：
1. 禁用模糊匹配：`AutoCompleter(registry, enable_fuzzy=False)`
2. 回退到原始 `auto_completer.py`
3. 禁用参数补全（注释掉 L300-310）

---

## 配置选项

### 可通过配置文件控制

```yaml
# ptk_repl_config.yaml
completion:
  enable_fuzzy: true          # 是否启用模糊匹配
  enable_prefix: true         # 是否启用前缀匹配
  enable_subsequence: true    # 是否启用子序列匹配
  enable_levenshtein: true    # 是否启用编辑距离
  max_levenshtein_distance: 3 # 最大编辑距离
  fuzzy_threshold: 50         # 模糊匹配分数阈值
```

### 运行时配置

```python
# 禁用模糊匹配
completer = AutoCompleter(registry, enable_fuzzy=False)

# 自定义编辑距离限制
completer._fuzzy_matcher.max_levenshtein_distance = 2
```

---

## 总结

### 实现文件清单

| 文件 | 操作 | 行数（估算） |
|------|------|--------------|
| `fuzzy_matcher.py` | 新建 | ~350 行 |
| `auto_completer.py` | 修改 | ~50 行改动 |
| `__init__.py` | 修改 | +2 行 |
| `test_fuzzy_matcher.py` | 新建 | ~200 行 |
| `test_auto_completer.py` | 更新 | +50 行 |

### 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 性能问题 | 中 | 高 | 缓存 + 可配置禁用 |
| 兼容性问题 | 低 | 中 | 完整测试 + 回滚计划 |
| 用户体验 | 低 | 高 | A/B 测试 + 收集反馈 |

### 后续改进

1. **机器学习排序**：根据用户历史优化排序
2. **上下文感知**：根据当前状态调整补全建议
3. **实时发现**：动态发现新模块（无需重启）
4. **多语言支持**：支持中英文混合输入
