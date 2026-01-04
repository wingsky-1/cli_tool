"""自动补全包。"""

from ptk_repl.core.completion.auto_completer import AutoCompleter
from ptk_repl.core.completion.fuzzy_matcher import (
    FuzzyMatchResult,
    cached_fuzzy_match,
    fuzzy_match,
)

__all__ = ["AutoCompleter", "fuzzy_match", "cached_fuzzy_match", "FuzzyMatchResult"]
