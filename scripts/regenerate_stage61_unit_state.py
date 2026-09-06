#!/usr/bin/env python3
"""現行生成元を実行し、既存成果を上書きせずStage61検証候補を再生成する。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'build/private-unit-focus/stage61-regeneration.json'
CANDIDATE = ROOT / '.local/private-unit-regenerated/stage61'


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def preserved_files(root: Path) -> dict[str, str]:
    """復元済みROM/saveは全て前後照合し、private byteは外へ出さない。"""
    result = {}
    for start in ('build', 'inputs', 'userfile', '.local'):
        base = root / start
        if not base.exists():
            continue
        for path in base.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in {'.gba', '.srm', '.sav', '.ss0'}:
                continue
            if CANDIDATE == path or CANDIDATE in path.parents:
                continue
            result[path.relative_to(root).as_posix()] = sha(path)
    return result


def exception_record(error: BaseException) -> dict:
    # 任意の例外本文、絶対path、ROM byteは記録しない。
    frames = []
    for frame, line in traceback.walk_tb(error.__traceback__):
        try:
            relative = Path(frame.f_code.co_filename).resolve().relative_to(ROOT).as_posix()
        except ValueError:
            continue
        frames.append({'path': relative, 'line': line, 'function': frame.f_code.co_name})
    return {'type': type(error).__name__, 'frames': frames}


def source_drift() -> list[dict]:
    from tools import stage61_cyclic_decision_contracts as cyclic
    result = []
    for name, expected in cyclic._SOURCE_BINDINGS.items():
        path = ROOT / name
        actual = sha(path) if path.is_file() else None
        if actual != expected:
            result.append({'path': name, 'expected_sha256': expected, 'actual_sha256': actual})
    return result


def write_candidate(artifacts: dict[str, bytes], destination: Path) -> None:
    """既存候補も上書きせず、元の相対pathで新しい世代だけを保存する。"""
    if destination.exists() or any(path.is_symlink() for path in (destination, *destination.parents)):
        raise ValueError('candidate destination already exists')
    for name in artifacts:
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name:
            raise ValueError('candidate artifact path rejected')
    destination.mkdir(parents=True)
    for name, raw in artifacts.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(raw)


def _link_read_inputs(source: Path, destination: Path) -> None:
    """生成済み5成果以外は読取参照とし、候補専用のbuild/.localを保つ。"""
    roots = ('config', 'content', 'data', 'generated', 'infra', 'inputs', 'manifests',
             'overlays', 'scripts', 'state', 'tests', 'tools', 'vendor', 'build', 'reports')
    def merge(current: Path, target: Path) -> None:
        if not current.exists():
            return
        if not target.exists() and not target.is_symlink():
            target.symlink_to(current, target_is_directory=current.is_dir())
        elif current.is_dir() and target.is_dir() and not target.is_symlink():
            for child in current.iterdir():
                merge(child, target / child.name)
    for name in roots:
        merge(source / name, destination / name)
    local = destination / '.local'
    local.mkdir(exist_ok=True)
    save = source / '.local/60_wild_species_root_repair.srm'
    if not save.is_file():
        raise ValueError('Stage60 generated fixture is missing')
    (local / save.name).symlink_to(save)


def ensure_stage61_state_fixture() -> Path:
    from scripts import build_stage61_display_npc_event_audit as builder
    from scripts.run_full_unit import private_output
    from tests.fixtures.private_unit_fixtures import ensure_stage60_test_ready_save
    ensure_stage60_test_ready_save()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch(r'[0-9a-f]{40}', head):
        raise ValueError('fixture HEAD identity is invalid')
    target = CANDIDATE / head
    marker = target / 'STATE_FIXTURE_MANIFEST.json'
    sources = {name: sha(ROOT / name) for name in (
        'scripts/build_stage61_display_npc_event_audit.py',
        'scripts/regenerate_stage61_unit_state.py', 'tools/stage61_state_fixture.py',
        'config/stage61_display_npc_event_audit.json',
        'overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c',
    )}
    if target.exists():
        if target.is_symlink() or not marker.is_file() or marker.is_symlink():
            raise ValueError('existing candidate is not a verified generated fixture')
        manifest = json.loads(marker.read_text())
        if manifest.get('head_sha') != head or manifest.get('sources') != sources:
            raise ValueError('existing candidate source identity differs')
        for name, digest in manifest['artifacts'].items():
            path = target / name
            if path.is_symlink() or sha(path) != digest:
                raise ValueError('existing candidate artifact integrity differs')
        return target
    # strictの全配置・全会話auditとは別profile。compiler/patch生成元は共通。
    with private_output():
        artifacts = builder.build(release_profile='STATE_NAMESPACE_FIXTURE')
    config = builder._load_config(builder.DEFAULT_CONFIG)
    metadata = json.loads(artifacts[config['outputs']['metadata']])
    generated = json.loads(artifacts[config['outputs']['audit']])
    raw = artifacts[config['outputs']['rom']]
    if (metadata['audit'] != generated or metadata['output']['sha256'] != hashlib.sha256(raw).hexdigest()
            or metadata['runtime']['source_sha256'] != sources[config['runtime_source']]
            or metadata['runtime'] != generated['runtime']
            or 'stage61_save_normal_copy_on_write' not in metadata['runtime']['symbols']
            or metadata.get('status_scope') != 'STATE_NAMESPACE_UNIT_FIXTURE_ONLY'):
        raise ValueError('generated state fixture source/ROM/report binding mismatch')
    write_candidate(artifacts, target)
    _link_read_inputs(ROOT, target)
    manifest = {'head_sha': head, 'sources': sources,
                'artifacts': {name: hashlib.sha256(raw).hexdigest() for name, raw in artifacts.items()}}
    with marker.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, sort_keys=True, indent=2)
    return target


def main() -> int:
    from tools import stage61_state_namespace_collision_audit as audit
    from scripts.run_full_unit import private_output
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    before = preserved_files(ROOT)
    report = {'schema_version': 1, 'head_sha': head, 'status': 'FAIL',
              'source_drift': source_drift(), 'preserved_file_count': len(before)}
    try:
        with private_output():
            target = ensure_stage61_state_fixture()
            state_audit = audit.build_stage61_state_namespace_collision_audit(target)
            installed = audit._build_stage61_installed_state_namespace_audit(target, state_audit)
            audit.require_ready(installed)
        metadata = json.loads((target / audit.STAGE61_METADATA_RELATIVE).read_text())
        report.update({'status': 'PASS', 'status_scope': metadata['status_scope'],
                       'source_sha256': metadata['runtime']['source_sha256'],
                       'rom_sha256': metadata['output']['sha256'],
                       'metadata_sha256': sha(target / audit.STAGE61_METADATA_RELATIVE),
                       'cow_symbol_present': True, 'namespace_audit_ready': True,
                       'same_as_restored_rom': sha(ROOT / audit.STAGE61_ROM_RELATIVE) == metadata['output']['sha256']})
    except Exception as error:
        report['error'] = exception_record(error)
    after = {name: sha(ROOT / name) for name in before}
    report['existing_rom_save_unchanged'] = before == after
    if before != after:
        report['status'] = 'FAIL'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
