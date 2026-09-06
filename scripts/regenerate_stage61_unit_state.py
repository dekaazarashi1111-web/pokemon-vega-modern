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


def main() -> int:
    from scripts import build_stage61_display_npc_event_audit as builder
    from scripts.run_full_unit import private_output
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    before = preserved_files(ROOT)
    report = {'schema_version': 1, 'head_sha': head, 'status': 'FAIL',
              'source_drift': source_drift(), 'preserved_file_count': len(before)}
    try:
        # build()は成果をmemoryで返す生成API。_write()は呼ばない。
        with private_output():
            artifacts = builder.build()
        config = builder._load_config(builder.DEFAULT_CONFIG)
        metadata = json.loads(artifacts[config['outputs']['metadata']])
        audit = json.loads(artifacts[config['outputs']['audit']])
        rom = artifacts[config['outputs']['rom']]
        runtime = metadata['runtime']
        source_hash = sha(ROOT / config['runtime_source'])
        if (metadata['audit'] != audit or metadata['output']['sha256'] != hashlib.sha256(rom).hexdigest()
                or runtime['source_sha256'] != source_hash or audit['runtime']['source_sha256'] != source_hash
                or 'stage61_save_normal_copy_on_write' not in runtime['symbols']):
            raise ValueError('regenerated source/metadata/report/ROM binding mismatch')
        write_candidate(artifacts, CANDIDATE / head)
        report.update({'status': 'PASS', 'artifact_count': len(artifacts),
                       'source_sha256': source_hash, 'rom_sha256': hashlib.sha256(rom).hexdigest(),
                       'metadata_sha256': hashlib.sha256(artifacts[config['outputs']['metadata']]).hexdigest(),
                       'cow_symbol_present': True,
                       'same_as_restored_rom': sha(ROOT / config['outputs']['rom']) == hashlib.sha256(rom).hexdigest()})
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
