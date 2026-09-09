#!/usr/bin/env python3
"""Apply the unchanged Stage79 seven-domain contracts to the exact Stage81 child.

The original Stage78/80 chain, sources and gates stay historical. Only the
candidate-validation boundary is composed: validate Stage80 first, then rebuild
and compare the separately materialized Stage81 child. No runner/expectation,
exit-code validation or cache validation is replaced. `prepare` is the only
input-writing command; plan/validate are read-only. Merge restores the historical
gate after the unmodified engine has checked and exported the new gate.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/run_modernization_stage81_github_domain.py'
BASE = 'config/modernization_stage79_cumulative_mgba.json'
HELPER = 'scripts/run_modernization_stage79_github_domain.py'
ENGINE = 'scripts/run_modernization_stage79_cumulative_mgba.py'
RECIPE = 'tools/modernization_p03_native_pp_repair.py'
WORK = '.local/stage81-native-pp'
CONFIG = WORK + '/config.json'
ROM = WORK + '/candidate.gba'
REPORT = WORK + '/candidate.json'
GATE = 'content/modernization/stage79_cumulative_mgba_runtime_gate.json'
SHA = '521624a5e6065bd969b7c3143044f1d96491b8af05a0231827ba2e709d04d579'
PINS = {
    BASE: 'ee6c6326e0c96445b113e9cd0d73f5b3b7a1d5c907789e58d88ea3878abca5d6',
    HELPER: '40be67f28c55b9f338e8d671702e11e290362b0cf774dc6630330932c30a5f47',
    ENGINE: 'fc5eff879d6bfc9d0d9232162c47de26b44957bf8a897e19997afec6dbe793fb',
    RECIPE: 'bfa4a1f2c8d470bafdb705d57fdd73a55a7885cfacb1dca6c392576a38f51e17',
}


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()


def safe_path(relative: str) -> Path:
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe path')
    current = ROOT
    for part in p.parts:
        current /= part
        require(not current.is_symlink(), 'symlink path: ' + relative)
    current.resolve().relative_to(ROOT.resolve())
    return current


def raw(relative: str) -> bytes:
    return safe_path(relative).read_bytes()


def identity(relative: str) -> dict:
    data = raw(relative)
    return {'path': relative, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def load(relative: str):
    spec = importlib.util.spec_from_file_location(Path(relative).stem, safe_path(relative))
    require(spec is not None and spec.loader is not None, 'cannot load ' + relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def derived_config() -> dict:
    for path, expected in PINS.items():
        require(identity(path)['sha256'] == expected, 'historical source changed: ' + path)
    cfg = json.loads(raw(BASE))
    cfg['execution']['state_root'] = WORK + '/state'
    cfg['stage81_native_pp'] = {
        'stage': 81,
        'rom': {'path': ROM, 'size': 33554432, 'sha256': SHA},
        'report_sha256': '48338a41f36287f618ab8d4506e23093aedd054cbd36df1868937e23085197cc',
        'sources': {p: identity(p) for p in (*PINS, SELF)},
        'full_p03_acceptance': False, 'release_ready': False,
    }
    return cfg


def prepare() -> dict:
    """Explicitly materialize reproducible private inputs, never overwrite Stage80."""
    cfg = derived_config()
    directory = safe_path(WORK)
    directory.mkdir(parents=True, exist_ok=True)
    # Never retain an old apparently valid config if preparation fails.
    for name in (CONFIG, ROM, REPORT):
        safe_path(name).unlink(missing_ok=True)
    recipe = load(RECIPE)
    child, report = recipe.build(raw(recipe.PARENT_PATH))
    report_bytes = (json.dumps(report, indent=2) + '\n').encode()
    require(hashlib.sha256(report_bytes).hexdigest() == cfg['stage81_native_pp']['report_sha256'],
            'Stage81 report serialization changed')
    safe_path(ROM).write_bytes(child)
    safe_path(REPORT).write_bytes(report_bytes)
    safe_path(CONFIG).write_bytes(stable(cfg))
    return {'status': 'PREPARED_NOT_EXECUTED', 'candidate': identity(ROM), 'config': identity(CONFIG)}


def load_engine():
    cfg = derived_config()
    # Byte equality rejects duplicate JSON keys, unexpected fields and bool/int substitutions.
    require(raw(CONFIG) == stable(cfg), 'derived config differs from exact parent contracts')
    engine = load(ENGINE)
    original = engine._validate_runtime_candidate

    def validate_child(config, stage78, stage78_audit):
        require(stable(config) == stable(cfg), 'unexpected Stage81 config')
        parent, parent_audit = original(config, stage78, stage78_audit)
        child, report = load(RECIPE).build(parent)
        require(identity(ROM) == cfg['stage81_native_pp']['rom'], 'Stage81 candidate identity mismatch')
        require(raw(ROM) == child, 'Stage81 bytes differ from classified repair')
        require(identity(REPORT)['sha256'] == cfg['stage81_native_pp']['report_sha256'],
                'Stage81 report identity mismatch')
        require(raw(REPORT) == (json.dumps(report, indent=2) + '\n').encode(), 'Stage81 report mismatch')
        return child, {
            'stage': 81, 'task': 'USER-MODERNIZATION-STAGE81-NATIVE-PP-ACCEPTANCE',
            'rom': identity(ROM), 'repair_recipe': identity(RECIPE),
            'repair_report': identity(REPORT), 'parent': parent_audit,
            'patches': report['patches'], 'changed_bytes_from_parent': report['modified_bytes'],
            'allocation_layout_unchanged': True,
            'parent_allocation_content_hashes_reused_as_candidate': False,
            'acceptance_adapter_sources': cfg['stage81_native_pp']['sources'],
        }

    engine._validate_runtime_candidate = validate_child
    return engine


@contextmanager
def preserve_historical_gate():
    path = safe_path(GATE)
    before = path.read_bytes()
    try:
        yield
    finally:
        path.write_bytes(before)
        require(path.read_bytes() == before, 'historical gate restoration failed')


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args == ['prepare']:
            print(stable(prepare()).decode(), end='')
            return 0
        require(bool(args) and args[0] in ('plan', 'run-domain', 'validate-domain', 'merge'),
                'expected prepare/plan/run-domain/validate-domain/merge')
        require('--config' not in args, 'only the exact derived Stage81 config is accepted')
        helper = load(HELPER)
        helper._load_orchestrator = load_engine
        if args[0] == 'merge':
            with preserve_historical_gate():
                return helper.main(['--config', CONFIG, *args])
        return helper.main(['--config', CONFIG, *args])
    except (OSError, ValueError, RuntimeError) as error:
        print('ERROR: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
