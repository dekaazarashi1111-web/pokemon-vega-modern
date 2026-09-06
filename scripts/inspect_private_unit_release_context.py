"""Private Releaseの候補・元metadataを読取専用で照合する。本文はprivate artifactのみ。"""
from __future__ import annotations
import json
from pathlib import Path
from scripts.inspect_private_unit_remaining import digest


def critical_identity(root: Path) -> dict:
    from scripts import build_stage61_display_npc_event_audit as builder
    from tools import stage61_interaction_oracle as oracle
    from scripts.regenerate_stage61_unit_state import exception_record
    paths = builder.CRITICAL_RELEASE_OUTPUTS
    files = {key: {'path': name, 'present': (root / name).is_file()} for key, name in paths.items()}
    for row in files.values():
        if row['present']:
            raw = (root / row['path']).read_bytes()
            row.update(size=len(raw), sha256=digest(raw))
    if not all(files[key]['present'] for key in ('rom', 'semantic_plan', 'event_owner_inventory', 'npc_catalog', 'build_report')):
        return {'status': 'MISSING', 'files': files}
    rom = (root / paths['rom']).read_bytes()
    semantic = json.loads((root / paths['semantic_plan']).read_text())
    inventory = json.loads((root / paths['event_owner_inventory']).read_text())
    report = json.loads((root / paths['build_report']).read_text())
    view = {'files': files, 'status': 'IDENTITY_ONLY_NOT_TEST_PASS',
            'build_status': report.get('status'), 'build_scope': report.get('status_scope'),
            'strict_audit_status': report.get('strict_audit_status'),
            'source_sha256': report.get('runtime', {}).get('source_sha256'),
            'expected_source_sha256': digest((root / 'overlays/stage61_display_npc_event_audit/stage61_display_npc_event_audit.c').read_bytes()),
            'inventory': {key: inventory.get(key) for key in ('kind', 'status', 'rom_sha256', 'owner_count')},
            'inventory_rom_matches': inventory.get('rom_sha256') == digest(rom),
            'create_box_mon_sha256': digest(rom[builder.CREATE_BOX_MON_ENTRY - builder.GBA_BASE:builder.CREATE_BOX_MON_ENTRY - builder.GBA_BASE + builder.CREATE_BOX_MON_SIZE]),
            'oracle_expected_create_box_mon_sha256': oracle.GIFT_STORAGE_CREATE_BOX_MON_SHA256}
    for field in ('flag', 'var'):
        try:
            oracle._namespace_mapping(semantic, field)
            view[field + '_namespace'] = 'PASS'
        except Exception as error:
            view[field + '_namespace'] = exception_record(error)
    # source evidenceを別プロファイルのreportへ移植せず、そのままの内容を照合する。
    policy = semantic.get('stage61_namespace_policy', {})
    view['engine_system_flag'] = {
        'category': policy.get('numeric_categories', {}).get('engine_system_flag'),
        'reserved': policy.get('reserved_state_namespace', {}).get('engine_system_flags'),
    }
    return view


def main() -> None:
    from scripts import inspect_private_unit_remaining as investigation
    root = Path(__file__).resolve().parents[1]
    # 既存のsymlink/secret/path/size/hash検査は維持し、生成器の入力説明も照合する。
    original = investigation.wanted_text
    def wanted(name: str) -> bool:
        path = Path(name)
        return original(name) or (investigation.safe_member(name) and (
            (path.suffix.lower() in {'.md', '.txt'} and any(p.lower() in {'docs', 'tasks', 'prompts', 'templates'} for p in path.parts))
            or path.name in {'README.md', 'README_JA.md', 'KIT_MANIFEST.example.json'}))
    investigation.wanted_text = wanted
    out = root / 'build/private-unit-investigation'
    out.mkdir(parents=True, exist_ok=True)
    try:
        context = investigation.collect_trainer_context(root, out / 'trainer-context-extended.zip')
    finally:
        investigation.wanted_text = original
    result = {'critical_release': critical_identity(root), 'trainer_extended_context': context}
    from scripts.github_private_environment import SECRET_PATTERNS
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if any(pattern.search(raw) for pattern in SECRET_PATTERNS.values()):
        raise ValueError('critical release identity secret candidate rejected')
    (out / 'release-identity.json').write_bytes(raw)
    print('existing critical release identity recorded; no ROM/save writes')


if __name__ == '__main__':
    main()
