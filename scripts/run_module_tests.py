#!/usr/bin/env python3
"""Run unittest cases and argument-free module-level test_* functions."""
from __future__ import annotations

import importlib
import importlib.util
import inspect
from pathlib import Path
import sys
import traceback
import unittest


def load_target(target: str):
    path = Path(target)
    if not path.is_file():
        return importlib.import_module(target)
    module_name = f"_plain_tests_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load test file: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_target(target: str) -> bool:
    module = load_target(target)
    ok = True

    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    if suite.countTestCases():
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        ok = result.wasSuccessful() and ok

    functions = [
        (name, value)
        for name, value in sorted(vars(module).items())
        if name.startswith("test_") and inspect.isfunction(value)
    ]
    for name, function in functions:
        required = [
            parameter
            for parameter in inspect.signature(function).parameters.values()
            if parameter.default is inspect.Parameter.empty
            and parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ]
        if required:
            names = ", ".join(parameter.name for parameter in required)
            print(
                f"ERROR {target}:{name}: unsupported required arguments: {names}",
                file=sys.stderr,
            )
            ok = False
            continue
        try:
            function()
        except Exception:
            print(f"FAIL {target}:{name}", file=sys.stderr)
            traceback.print_exc()
            ok = False
        else:
            print(f"PASS {target}:{name}")
    return ok


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "usage: run_module_tests.py MODULE_OR_PATH [MODULE_OR_PATH ...]",
            file=sys.stderr,
        )
        return 2
    ok = True
    for target in argv[1:]:
        ok = run_target(target) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
