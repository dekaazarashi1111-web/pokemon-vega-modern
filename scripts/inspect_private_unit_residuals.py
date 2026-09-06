#!/usr/bin/env python3
"""残存4件を読取専用で診断する。ROM/save/CSV本文や任意の例外本文は出力しない。"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(relative: str):
    return json.loads((ROOT / relative).read_text())


def main() -> None:
    from tools import stage61_interaction_oracle as oracle
    stage_paths = ('inputs/private/FireRed_JPN_Rev0_clean.gba',
                   'build/stages/60_wild_species_root_repair.gba',
                   'build/stages/61_display_npc_event_audit.gba',
                   'build/stages/62_npc_placement_integrity_repair.gba')
    spans = (('CreateMon', oracle.GIFT_STORAGE_CREATE_MON_ENTRY, oracle.GIFT_STORAGE_CREATE_MON_SIZE, oracle.GIFT_STORAGE_CREATE_MON_SHA256),
             ('CreateBoxMon', oracle.GIFT_STORAGE_CREATE_BOX_MON_ENTRY, oracle.GIFT_STORAGE_CREATE_BOX_MON_SIZE, oracle.GIFT_STORAGE_CREATE_BOX_MON_SHA256),
             ('InitialMoveset', oracle.GIFT_STORAGE_LEVEL_UP_DISPATCH, oracle.GIFT_STORAGE_LEVEL_UP_DISPATCH_SIZE, oracle.GIFT_STORAGE_LEVEL_UP_DISPATCH_SHA256))
    roms = {}
    for relative in stage_paths:
        raw = (ROOT / relative).read_bytes()
        roms[relative] = {'sha256': sha(raw), 'size': len(raw), 'spans': [
            {'label': label, 'address': address, 'size': size, 'expected_sha256': expected,
             'actual_sha256': sha(raw[address - 0x08000000:address - 0x08000000 + size])}
            for label, address, size, expected in spans]}
    inventory = load('reports/generated/stage61_event_owner_inventory.json')
    semantic = load('reports/generated/stage61_event_semantic_relocation.json')
    inventory_view = {key: inventory.get(key) for key in ('kind', 'status', 'rom_sha256', 'owner_count', 'inventory_sha256')}
    inventory_view['expected_owner_count'] = oracle.EVENT_OWNER_COUNT
    inventory_view['findings_count'] = len(inventory.get('findings', []))
    policy = semantic.get('stage61_namespace_policy', {})
    flag_view = {key: policy.get(key, {}).get('special_flag' if key == 'numeric_categories' else 'engine_special_flags')
                 for key in ('numeric_categories', 'reserved_state_namespace')}
    flag_view['source_abi'] = oracle.ENGINE_SPECIAL_FLAG_SOURCE
    expected_paths = {oracle.ENGINE_SPECIAL_FLAG_SOURCE['constants_path'], oracle.ENGINE_SPECIAL_FLAG_SOURCE['consumer_path']}
    evidence = policy.get('reserved_state_namespace', {}).get('engine_special_flags', {}).get('source_evidence', [])
    flag_view['required_ids'] = semantic.get('full_cfg_relocation', {}).get('namespace_requirements', {}).get('source_engine_special_flag_ids')
    bill = semantic.get('stage61_bill_sevii_scope_guard', {})
    flag_view['bill_guard'] = {key: bill.get(key) for key in ('kind', 'status', 'owner_id')}
    flag_view['bill_product_policy'] = bill.get('product_contract', {}).get('policy')
    flag_view['bill_suppressed_classes'] = bill.get('product_contract', {}).get('suppressed_source_effect_classes')
    flag_view['source_evidence'] = [row for row in evidence if isinstance(row, dict) and row.get('path') in expected_paths]
    flag_view['workspace_sha256'] = {p: sha((ROOT / p).read_bytes()) for p in expected_paths}
    literals = {node.value for node in ast.walk(ast.parse((ROOT / 'tools/stage61_interaction_oracle.py').read_text()))
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    try:
        oracle._namespace_mapping(semantic, 'flag')
        flag_view['validation'] = 'PASS'
    except oracle.Stage61InteractionOracleError as error:
        flag_view['validation'] = str(error) if str(error) in literals else type(error).__name__
    # CreateBoxMon近傍を宣言するmetadata/configのキーとhashだけを採取する。
    sites = []
    def visit(value, path, pointer):
        if isinstance(value, dict):
            hit = False
            for key, item in value.items():
                number = item if type(item) is int else int(item, 16) if isinstance(item, str) and re.fullmatch('0x[0-9a-fA-F]{5,8}', item) else -1
                if 0x3D230 <= number < 0x3D504 or 0x0803D230 <= number < 0x0803D504:
                    hit = True
            if hit:
                safe = {k: v for k, v in value.items() if type(v) in (bool, int) or (isinstance(v, str) and (re.fullmatch('[0-9a-fA-F]{64}|0x[0-9a-fA-F]{5,8}', v) or k in {'name', 'symbol', 'kind', 'label', 'hook', 'source'}))}
                sites.append({'path': path, 'pointer': pointer, 'fields': safe, 'keys': sorted(value)})
            for key, child in value.items():
                visit(child, path, pointer + '/' + str(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path, pointer + '/' + str(index))
    for pattern in ('build/stages/*.json', 'config/*.json', 'reports/generated/stage61*.json'):
        for path in sorted(ROOT.glob(pattern)):
            try:
                visit(json.loads(path.read_text()), path.relative_to(ROOT).as_posix(), '')
            except (UnicodeError, json.JSONDecodeError):
                continue
    result = {'head_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'roms': roms, 'inventory': inventory_view, 'engine_special_flag': flag_view, 'create_box_mon_sites': sites}
    for relative, record in roms.items():
        if sha((ROOT / relative).read_bytes()) != record['sha256']:
            raise RuntimeError('Read-only residual diagnostic changed a ROM')
    from scripts.github_private_environment import SECRET_PATTERNS
    raw = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if any(pattern.search(raw) for pattern in SECRET_PATTERNS.values()):
        raise RuntimeError('Residual diagnostic contains a secret candidate')
    output = ROOT / 'build/private-unit-focus/residual-diagnostic.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    print('residual diagnosis recorded; ROMs unchanged; private bytes not included')


if __name__ == '__main__':
    main()
