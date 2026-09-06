#!/usr/bin/env python3
"""残るfixture不一致の読取専用診断。ROM/save本文は記録しない。"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_TEXT = 4 * 1024 * 1024
MAX_NESTED = 256 * 1024 * 1024
TEXT_NAMES = {'KIT_MANIFEST.json', 'AUTHORING_MANIFEST_SHA256.tsv', 'TASK_SEQUENCE.json', 'BASELINE.json'}
SOURCE_TABLES = {'coverage.csv', 'trainer_encounters.csv', 'trainer_physical_bindings.csv'}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and '..' not in path.parts and '\\' not in name


def wanted_text(name: str) -> bool:
    path = PurePosixPath(name)
    return safe_member(name) and (path.name in TEXT_NAMES or (
        'source' in path.parts and 'v5' in path.parts and path.name in SOURCE_TABLES
    ) or ('tools' in path.parts and path.suffix == '.py'))


def collect_trainer_context(root: Path, output: Path) -> dict:
    """私有入力の小さな生成器/manifest/正規化前表だけをprivate artifactへ保存。"""
    from scripts.github_private_environment import SECRET_PATTERNS
    rows, seen = [], set()
    members: dict[str, bytes] = {}
    def consider(name: str, raw: bytes, parent_sha: str) -> None:
        if not wanted_text(name) or len(raw) > MAX_TEXT:
            return
        identity = (PurePosixPath(name).name, digest(raw))
        if identity in seen:
            return
        try:
            raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            return
        if any(pattern.search(raw) for pattern in SECRET_PATTERNS.values()):
            raise ValueError('private context secret candidate rejected')
        seen.add(identity)
        destination = identity[1] + '/' + identity[0]
        members[destination] = raw
        rows.append({'path': destination, 'source_member': name, 'parent_sha256': parent_sha,
                     'size': len(raw), 'sha256': identity[1]})
    def scan(source: object, parent_sha: str, depth: int = 0) -> None:
        with zipfile.ZipFile(source) as archive:
            for info in archive.infolist():
                if not safe_member(info.filename) or stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError('unsafe trainer archive member')
                if info.is_dir():
                    continue
                name = PurePosixPath(info.filename)
                trainer = any('TRAINER' in p.upper() and ('KIT' in p.upper() or 'CHANGE' in p.upper()) for p in name.parts)
                if wanted_text(info.filename) and info.file_size <= MAX_TEXT and (trainer or depth > 0):
                    consider(info.filename, archive.read(info), parent_sha)
                elif name.suffix.lower() == '.zip' and info.file_size <= MAX_NESTED and depth < 4 and (trainer or depth > 0):
                    raw = archive.read(info)
                    if zipfile.is_zipfile(io.BytesIO(raw)):
                        scan(io.BytesIO(raw), digest(raw), depth + 1)
    for relative in ('userfile', '.local/github-private-environment/PRIVATE_INPUTS', 'build/validated_inputs', 'dist'):
        base = root / relative
        if not base.is_dir():
            continue
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            name = path.relative_to(base).as_posix()
            trainer = 'TRAINER' in name.upper() and ('KIT' in name.upper() or 'CHANGE' in name.upper())
            if not trainer:
                continue
            if wanted_text(name) and path.stat().st_size <= MAX_TEXT:
                consider(name, path.read_bytes(), digest(path.read_bytes()))
            elif path.suffix.lower() == '.zip' and zipfile.is_zipfile(path):
                scan(path, digest(path.read_bytes()), 1)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            archive.writestr(name, raw)
        archive.writestr('CONTEXT_MANIFEST.json', json.dumps({'scope': 'PRIVATE_TRAINER_TEXT_ONLY_NOT_FOR_GIT', 'files': rows}, sort_keys=True))
    return {'file_count': len(rows), 'sha256': digest(output.read_bytes()), 'scope': 'PRIVATE_TRAINER_TEXT_ONLY_NOT_FOR_GIT'}


def fixture_identity(root: Path) -> dict:
    from scripts import build_stage61_display_npc_event_audit as builder
    from tools import stage61_interaction_oracle as oracle
    rom = (root / 'build/stages/61_display_npc_event_audit.gba').read_bytes()
    semantic = json.loads((root / 'reports/generated/stage61_event_semantic_relocation.json').read_text())
    inventory = json.loads((root / 'reports/generated/stage61_event_owner_inventory.json').read_text())
    offset = builder.CREATE_BOX_MON_ENTRY - builder.GBA_BASE
    actual = digest(rom[offset:offset + builder.CREATE_BOX_MON_SIZE])
    policy = semantic.get('stage61_namespace_policy', {})
    return {
        'stage61_rom_sha256': digest(rom),
        'create_box_mon': {'rom_sha256': actual, 'stage60_sha256': builder.CREATE_BOX_MON_STAGE60_SHA256,
                           'generator_output_sha256': builder.CREATE_BOX_MON_STAGE61_SHA256,
                           'oracle_expected_sha256': oracle.GIFT_STORAGE_CREATE_BOX_MON_SHA256},
        'inventory': {'kind': inventory.get('kind'), 'status': inventory.get('status'),
                      'owner_count': inventory.get('owner_count'), 'expected_owner_count': oracle.EVENT_OWNER_COUNT,
                      'rom_sha256': inventory.get('rom_sha256'), 'rom_matches': inventory.get('rom_sha256') == digest(rom),
                      'finding_count': len(inventory.get('findings', []))},
        'namespace': {'engine_category_present': 'engine_system_flag' in policy.get('numeric_categories', {}),
                      'engine_reserved_present': 'engine_system_flags' in policy.get('reserved_state_namespace', {})},
    }


def placement_failure_evidence(error: Exception) -> dict:
    """特定のbuilder停止点から数値座標・CFG識別子だけを採取する。"""
    from scripts.github_private_environment import SECRET_PATTERNS
    def safe(value):
        if type(value) in (int, bool) or value is None:
            return value
        if isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_:/().+\- ]{1,240}', value):
            return value
        if isinstance(value, (list, tuple)) and len(value) <= 16 and all(type(item) is int for item in value):
            return list(value)
        return None
    trace = error.__traceback__
    while trace is not None:
        frame = trace.tb_frame
        if frame.f_code.co_name == '_interaction_contracts' and Path(frame.f_code.co_filename).name == 'build_stage61_display_npc_event_audit.py':
            values = frame.f_locals
            operations = []
            allowed = {'root_map', 'root_label', 'root_pointer', 'root_owner_id', 'instruction_address', 'opcode', 'operation', 'target_owner_id', 'external_to_owner', 'literal_position', 'literal_movement_type', 'target_map', 'local_id'}
            for row in values.get('external', []):
                operations.append({key: safe(value) for key, value in row.items() if key in allowed})
            npc_keys = {'npc_id', 'group', 'map', 'object_index', 'local_id', 'x', 'y', 'movement_type', 'script_pointer', 'flag'}
            result = {'npc_id': safe(values.get('npc_id')), 'permanent_positions': [safe(row) for row in values.get('permanent_positions', [])],
                      'npc': {key: safe(value) for key, value in values.get('npc', {}).items() if key in npc_keys},
                      'external_operations': operations}
            raw = json.dumps(result, sort_keys=True).encode()
            if any(pattern.search(raw) for pattern in SECRET_PATTERNS.values()):
                raise ValueError('placement evidence secret candidate rejected')
            return result
        trace = trace.tb_next
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe-critical', action='store_true')
    args = parser.parse_args()
    from scripts.regenerate_stage61_unit_state import preserved_files, sha, write_candidate, exception_record
    from scripts.run_full_unit import private_output
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if not re.fullmatch('[0-9a-f]{40}', head):
        raise ValueError('invalid HEAD')
    before = preserved_files(ROOT)
    out = ROOT / 'build/private-unit-investigation'
    out.mkdir(parents=True, exist_ok=True)
    result = {'head_sha': head, 'restored_fixture': fixture_identity(ROOT)}
    result['trainer_context'] = collect_trainer_context(ROOT, out / 'trainer-context.zip')
    (out / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    if args.probe_critical:
        from scripts import build_stage61_display_npc_event_audit as builder
        try:
            with private_output():
                artifacts = builder.build(release_profile='CRITICAL_RELEASE')
                target = ROOT / '.local/private-unit-investigation/critical' / head
                write_candidate(artifacts, target)
            result['critical_generator'] = {'status': 'PASS', 'scope': 'DIAGNOSTIC_BUILD_NOT_FULL_UNIT',
                'artifacts': {name: digest(raw) for name, raw in artifacts.items()}}
        except Exception as error:
            result['critical_generator'] = {'status': 'FAIL', 'error': exception_record(error),
                'placement_evidence': placement_failure_evidence(error)}
    result['existing_rom_save_unchanged'] = before == {name: sha(ROOT / name) for name in before}
    (out / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    if not result['existing_rom_save_unchanged']:
        raise ValueError('existing ROM/save changed during diagnostic')
    print('remaining fixture diagnostic recorded; this is not a validation success')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
