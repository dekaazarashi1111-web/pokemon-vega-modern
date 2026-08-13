"""T17/T18の実ROM回帰・release候補生成。"""

from .rom_runtime import RuntimeBuildError, build_runtime_outputs

__all__ = ["RuntimeBuildError", "build_runtime_outputs"]
