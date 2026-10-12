#!/usr/bin/env python3
"""Offline, deterministic owner adjudication. Never rewrite capture or runtime inputs."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

EVIDENCE = Path('content/modernization/pr16_vega_original_evidence')
DECISION = Path('content/modernization/pr16_vega_original_source_decision.json')
OUTPUT = Path('content/modernization/pr16_vega_adjudication')
ROM_SHA = 'f600fb3faa565bd335ea75114f9233f9a4fe97c12cfed145e0a7b48784d0c9d5'
DECISION_ID = 'VEGA_ORIGINAL_SOURCE_PRIORITY_20260921'
# Numeric rows of the owner's five explicit choices; names are display-only.
EXPECTED = {
    ('SPECIES_KEY_VEGA_003', 'level_up'): ([(32, 348), (46, 235)], [(32, 63), (46, 105)]),
    ('SPECIES_KEY_VEGA_053', 'tutor'): ([(None, 465), (None, 436)], []),
    ('SPECIES_KEY_VEGA_090', 'level_up'): ([(18, 44)], [(20, 44)]),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def encoded(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def signature(row: dict) -> tuple:
    return (row.get('level'), row['move_id'])


def difference(left: list[dict], right: list[dict]) -> list[dict]:
    """Multiset difference preserves original order and duplicate observations."""
    remaining = Counter(signature(row) for row in right)
    result = []
    for row in left:
        key = signature(row)
        if remaining[key]:
            remaining[key] -= 1
        else:
            result.append(copy.deepcopy(row))
    return result


def verify_inputs(root: Path) -> tuple[dict, dict]:
    evidence = root / EVIDENCE
    receipt = load(evidence / 'receipt.json')
    for name, identity in receipt['outputs'].items():
        require(Path(name).name == name, 'unsafe receipt path')
        path = evidence / name
        require(path.stat().st_size == identity['size'], f'input size drift: {name}')
        require(digest(path) == identity['sha256'], f'input hash drift: {name}')
    decision = load(root / DECISION)
    lock = load(evidence / 'source_lock.json')
    require(decision['decision_id'] == DECISION_ID, 'unsupported owner decision')
    require(decision['status'] == 'OWNER_DECIDED', 'owner decision is not final')
    require(decision['priority_rule'] == 'FROZEN_VEGA_ROM_WINS', 'owner precedence changed')
    require(lock['rom']['sha256'] == decision['frozen_rom']['sha256'] == ROM_SHA,
            'frozen ROM hash mismatch')
    require(lock['rom']['size'] == decision['frozen_rom']['size'] == 16777216,
            'frozen ROM size mismatch')
    return decision, lock


def build(root: Path) -> dict[str, bytes]:
    decision, lock = verify_inputs(root)
    evidence = root / EVIDENCE
    baseline = [json.loads(line) for line in (evidence / 'vega_original_baseline.jsonl').read_text(encoding='utf-8').splitlines()]
    by_species = {row['species_key']: row for row in baseline}
    require(len(by_species) == len(baseline) == 181, 'baseline species drift or duplicate')
    require(sum(len(rows) for record in baseline for rows in record['methods'].values()) == 9923,
            'baseline method row count drift')
    conflicts = load(evidence / 'source_conflicts.json')
    require(len(conflicts) == len(EXPECTED), 'conflict group count drift')
    seen = set()
    groups, decisions = [], []
    for group_index, group in enumerate(conflicts):
        key = (group['species_key'], group['method'])
        require(key in EXPECTED and key not in seen, f'unknown/duplicate conflict: {key}')
        seen.add(key)
        require(group['rom_rows'] == by_species[key[0]]['methods'][key[1]], 'ROM evidence differs from baseline')
        adopted = difference(group['rom_rows'], group['wiki_rows'])
        rejected = difference(group['wiki_rows'], group['rom_rows'])
        expected_rom, expected_wiki = EXPECTED[key]
        require([signature(row) for row in adopted] == expected_rom, f'owner ROM scope drift: {key}')
        require([signature(row) for row in rejected] == expected_wiki, f'owner wiki scope drift: {key}')
        pages = [page for page in lock['pages'].values() if page['url'] == group['url']]
        require(len(pages) == 1, 'missing/ambiguous frozen wiki page')
        groups.append({'source_group_index': group_index, 'original_conflict': group,
                       'selected_source': 'FROZEN_VEGA_ROM', 'wiki_source_identity': pages[0],
                       'rom_only_rows': adopted, 'wiki_only_rows': rejected})
        for row in adopted:
            decisions.append({'decision_row_key': f"{key[0]}:{key[1]}:{row['order']}",
                              'species_key': key[0], 'method': key[1], 'source_group_index': group_index,
                              'selected_row': row, 'selected_source': 'FROZEN_VEGA_ROM',
                              'decision_id': decision['decision_id'],
                              'reason': 'OWNER_EXPLICIT_FROZEN_ROM_PRIORITY',
                              'unselected_evidence': f'groups/{group_index}/original_conflict/wiki_rows'})
    require(len(decisions) == 5, 'expected exactly five owner-adjudicated rows')
    projection = copy.deepcopy(baseline)
    for row in projection:
        row['adoption_status'] = 'SOURCE_ADJUDICATED_RUNTIME_PENDING'
        row['source_decision'] = DECISION.as_posix()
    ledger = {'schema_version': 1, 'task': decision['task'], 'decision_id': decision['decision_id'],
              'decision_path': DECISION.as_posix(), 'decision_sha256': digest(root / DECISION),
              'source_conflicts_sha256': digest(evidence / 'source_conflicts.json'),
              'source_lock_sha256': digest(evidence / 'source_lock.json'),
              'baseline_sha256': digest(evidence / 'vega_original_baseline.jsonl'),
              'rom_identity': lock['rom'], 'groups': groups, 'rows': decisions,
              'summary': {'conflict_groups': 3, 'adopted_rom_rows': 5, 'unselected_wiki_rows': 3,
                          'source_projection_species': 181, 'source_projection_rows': 9923,
                          'runtime_applied': False, 'owner_overlay_rows': 0,
                          'issue19_complete': False, 'release_ready': False}}
    return {'source_collisions.json': encoded(ledger),
            'adopted_vega_original_baseline.jsonl': ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in projection).encode('utf-8')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate', 'check'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or args.root / OUTPUT
    result = build(args.root)
    if args.command == 'generate':
        output.mkdir(parents=True, exist_ok=True)
        for name, data in result.items():
            (output / name).write_bytes(data)
    else:
        for name, data in result.items():
            require((output / name).read_bytes() == data, f'generated output drift: {name}')
    print(json.dumps({'status': 'PASS', 'command': args.command, 'conflict_groups': 3,
                      'adopted_rom_rows': 5, 'runtime_applied': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
