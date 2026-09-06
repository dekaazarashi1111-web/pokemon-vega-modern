#!/usr/bin/env python3
"""復元済み正本と固定契約の差だけを採取する。入力やROMは更新しない。"""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import traceback

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ('battle_core', 'battle_ui', 'move_memory', 'species_port', 'species_surface',
           'move_distribution_v4', 'reward_encounters_v2', 'factory_high_modes_v2',
           'mirage_production', 'research_economy_v1', 'codex_battle_bridge')
HEX = re.compile(r'^[0-9a-f]{64}$')


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(name, value):
    path = ROOT / 'build/private-unit-focus' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n')


def main():
    mismatches, validators, fingerprints = [], [], []
    def visit(value, config_name, pointer):
        if isinstance(value, dict):
            rel, expected = value.get('path'), value.get('sha256')
            if isinstance(rel, str) and isinstance(expected, str) and HEX.fullmatch(expected):
                p = Path(rel)
                if p.is_absolute() or '..' in p.parts:
                    return
                path = ROOT / p
                actual = sha(path) if path.is_file() else None
                if actual != expected:
                    mismatches.append({'config': config_name, 'pointer': pointer,
                        'path': rel, 'expected_sha256': expected, 'actual_sha256': actual,
                        'actual_size': path.stat().st_size if actual else None})
            for key, sub in value.items():
                visit(sub, config_name, pointer + '/' + key)
        elif isinstance(value, list):
            for i, sub in enumerate(value):
                visit(sub, config_name, pointer + '/' + str(i))
    for name in CONFIGS:
        path = ROOT / f'config/{name}.json'
        if not path.is_file():
            continue
        config = json.loads(path.read_text())
        visit(config, f'config/{name}.json', '')
        inputs = config.get('inputs', {})
        if isinstance(inputs.get('validator'), str):
            template = ROOT / inputs['validator']
            packaged = ROOT / inputs['packet_root'] / 'tools/validate_submission.py'
            validators.append({'config': f'config/{name}.json',
                'expected_sha256': inputs.get('validator_sha256'),
                'current_template_sha256': sha(template) if template.is_file() else None,
                'packaged_validator': str(packaged.relative_to(ROOT)),
                'packaged_sha256': sha(packaged) if packaged.is_file() else None})
    for name in ('06_battle_core', '07_species', '09_species_surface'):
        path = ROOT / f'build/stages/{name}.json'
        value = json.loads(path.read_text())
        rows = []
        for rel, identity in value.get('fingerprint_inputs', {}).get('files', {}).items():
            actual = sha(ROOT / rel) if (ROOT / rel).is_file() else None
            if actual != identity['sha256']:
                rows.append({'path': rel, 'recorded_sha256': identity['sha256'], 'current_sha256': actual})
        fingerprints.append({'metadata': str(path.relative_to(ROOT)), 'source_drift': rows})
    from scripts.build_battle_ui import _battle_core_contract
    core = json.loads((ROOT / 'build/stages/06_battle_core.json').read_text())
    write('fixed-contract-drift.json', {'mismatches': mismatches, 'validators': validators,
                                      'fingerprints': fingerprints, 'battle_core_contract': _battle_core_contract(core)})
    # Vendor差分はGit固定objectと現行sourceのhash/行数だけを記録する。
    vendor = ROOT / 'vendor/upstream/CFRU-JP'
    changed = subprocess.check_output(['git', '-C', str(vendor), 'diff', '--name-only'], text=True).splitlines()
    source_rows = []
    for name in changed:
        if name != 'src/dynamax.c':
            continue
        original = subprocess.check_output(['git', '-C', str(vendor), 'show', 'HEAD:' + name])
        current = (vendor / name).read_bytes()
        diff = subprocess.check_output(['git', '-C', str(vendor), 'diff', '--', name])
        from scripts.github_private_environment import SECRET_PATTERNS
        if any(pattern.search(diff) for pattern in SECRET_PATTERNS.values()):
            raise ValueError('vendor code diff contains a secret candidate')
        source_rows.append({'path': name, 'git_sha256': hashlib.sha256(original).hexdigest(),
                            'current_sha256': hashlib.sha256(current).hexdigest(),
                            'diff_sha256': hashlib.sha256(diff).hexdigest(), 'source_patch': diff.decode()})
    write('vendor-source-review.json', {'changed_files': changed, 'review': source_rows})
    # checkcoins実装の未解決codeだけを取得し、private byteや例外本文は出さない。
    from scripts.run_full_unit import private_output
    from tests.test_stage61_interaction_oracle import Stage61CoinsABIFocusedTests as Coins
    from tools import stage61_interaction_oracle as oracle
    from tools.stage61_event_semantic_relocator import SemanticScriptGraph
    result = {}
    try:
        with private_output():
            Coins.setUpClass()
            case = Coins('test_product_prize_room_checkcoins_result_is_path_exact')
            case.test_product_prize_room_checkcoins_result_is_path_exact()
        result['status'] = 'PASS'
    except Exception as error:
        result['status'] = 'FAIL'
        result['exception_type'] = type(error).__name__
        literals = set()
        tree = ast.parse((ROOT / 'tools/stage61_interaction_oracle.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.update(re.findall(r'\b[A-Z][A-Z0-9_]{5,}\b', node.value))
        result['diagnostic_codes'] = sorted(code for code in literals if code in str(error))
        result['frames'] = []
        for frame, line in traceback.walk_tb(error.__traceback__):
            try:
                relative = Path(frame.f_code.co_filename).resolve().relative_to(ROOT).as_posix()
            except ValueError:
                continue
            result['frames'].append({'path': relative, 'line': line})
    write('checkcoins-diagnostic.json', result)
    print('fixed contracts and current source diagnostics recorded; no input modified')


if __name__ == '__main__':
    main()
