#!/usr/bin/env python3
"""PR16 NPC実装用の限定tracked-text snapshot。ROM/native/受入状態は変更しない。"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/pr16-ring-npc-workbench'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
PATHS = (
    'overlays/cfru/rom_bridge.c', 'overlays/cfru/rom_bridge.h',
    'overlays/cfru/integration.h', 'overlays/cfru/runtime.c', 'overlays/cfru/runtime.h',
    'overlays/event_design/event_design.c',
    'overlays/acquisition_runtime/acquisition_engine_adapter_rom.c',
    'overlays/acquisition_runtime/acquisition_engine_adapter_rom.h',
    'scripts/pr16_purchased_gear.py', 'scripts/pr16_purchased_gear_evidence.py',
    'scripts/pr16_purchased_gear_checkpoint.py', 'scripts/pr16_integrated_native.py',
    'scripts/pr16_bp_spending_native.py', 'scripts/pr16_bp_spending_native_impl.py',
    'scripts/pr16_bp_party_retention_successor.py', 'scripts/pr16_bp_party_retention_native.py',
    'scripts/pr16_bp_party_retention_record.py',
    'scripts/pr16_bp_spending_closeout.py', 'scripts/pr16_bp_three_win_reward_native.py',
    'tools/mgba_pr16_purchased_gear.c', 'tools/mgba_pr16_bp_spending.c',
    'tools/mgba_battle_policy_smoke.c',
    'tests/test_pr16_purchased_gear.py', 'tests/test_mgba_battle_policy_smoke.py',
    'tests/test_pr16_resume.py', 'tests/test_pr16_ring_npc_plan.py',
    '.github/workflows/pr16-purchased-gear.yml',
    '.github/workflows/pr16-bp-spending-native.yml',
    '.github/workflows/pr16-bp-party-retention-native.yml',
    'content/event_design_implementation/event_plan.json',
    'config/event_design_bindings.csv',
    'content/collection_supply_v1/canonical_model.json',
    'scripts/build_event_design_stage.py', 'scripts/build_acquisition_events.py',
    'tools/rom_allocator.py',
)


def collect() -> dict:
    if (os.environ.get('GITHUB_REPOSITORY') != REPO
            or os.environ.get('GITHUB_REF') != 'refs/heads/' + BRANCH):
        raise ValueError('repository/branch boundary')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != os.environ['GITHUB_SHA']:
        raise ValueError('checkout boundary')
    tracked = {}
    listing = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=ROOT)
    for entry in listing.split(b'\0'):
        if not entry:
            continue
        metadata, name = entry.decode('utf-8').split('\t', 1)
        mode, blob, stage = metadata.split()
        if stage != '0':
            raise ValueError('unmerged source')
        tracked[name] = {'mode': mode, 'blob': blob}
    OUT.mkdir(parents=True, exist_ok=True)
    # Only path names, not contents of private inputs or binary assets, enter this index.
    index = [p for p in sorted(tracked) if p.startswith(
        ('scripts/', 'tools/', 'overlays/', 'tests/', '.github/workflows/', 'config/'))
        and PurePosixPath(p).suffix in {'.py', '.c', '.h', '.s', '.S', '.json', '.yml'}]
    (OUT / 'tracked-paths.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')
    files, absent = {}, []
    for name in PATHS:
        if name not in tracked:
            absent.append(name)
            continue
        if tracked[name]['mode'] not in {'100644', '100755'}:
            raise ValueError('non-regular tracked source: ' + name)
        raw = subprocess.check_output(['git', 'show', head + ':' + name], cwd=ROOT)
        raw.decode('utf-8')
        if b'\0' in raw or len(raw) > 2_000_000:
            raise ValueError('source is binary or oversized: ' + name)
        path = OUT / 'source' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        files[name] = {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                       'git_blob': tracked[name]['blob']}
    result = {'schema_version': 1, 'source_head': head,
              'run_id': int(os.environ['GITHUB_RUN_ID']), 'files': files,
              'absent_optional_paths': absent, 'rom_changes': 0,
              'new_emulator_processes': 0, 'ring_acquisition_accepted': False}
    (OUT / 'source-manifest.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    subprocess.run(['git', 'diff', '--exit-code'], cwd=ROOT, check=True)
    subprocess.run(['git', 'diff', '--cached', '--exit-code'], cwd=ROOT, check=True)
    print(json.dumps({'source_head': head, 'files': len(files), 'rom_changes': 0}))
    return result


if __name__ == '__main__':
    collect()
