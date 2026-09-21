#!/usr/bin/env python3
"""固定ZIPのEternal参考1件だけを隔離。採用済み1299件を再生成しない。"""
from __future__ import annotations
import csv
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_learnset_baseline import (
    LOCK, TASK, CSV_PARTITIONS, archive_csv, consume_csv, encode,
    ensure_output, file_identity, project_csv, require, sha,
)
from tools.modernization_identity import CheckedArchive
from tools.modernization_learnsets import (
    _compile_route_row, _csv_member, _iter_jsonl_member, _load_crosswalk,
    _load_identity, _validate_route,
)

REFERENCE = 'legendsza:0670.05'
KEY = 'SPECIES_KEY_FLOETTE_ETERNAL'
GIFT = 'config/modernization_floette_gift.json'


def extract(source: Path, output: Path) -> dict:
    output = ensure_output(ROOT, output)
    require(not output.exists(), '新しい出力先が必要')
    lock = json.loads((ROOT / LOCK).read_bytes())
    _, targets, manifests = _load_identity(ROOT)
    target = targets[KEY]
    require(target['canonical_id'] == 1029 and target['reference_id'] == REFERENCE
            and target['source_form'] == 5 and target['national_no'] == 670
            and target['input']['apply'] is False and target['normalized']['apply'] is False,
            '明示裁定前のEternal identity不一致')
    sources = {name: file_identity(ROOT / name) for name in
               (LOCK, GIFT, 'content/modernization/identity_contract.json',
                'manifests/species_ids.csv', 'manifests/move_ids.csv')}
    with CheckedArchive(source, 'learnsets') as archive:
        require(all(archive.identity()[k] == lock['archive'][k]
                    for k in ('size', 'sha256', 'archive_root')), 'ZIP identity不一致')
        crosswalk = _load_crosswalk(_csv_member(archive, 'data/move_id_crosswalk.csv'), manifests['moves'])
        selected = []
        # 全byte hash終端まで読むが、非対象の検証・成果再生成は行わない。
        for reference in _iter_jsonl_member(archive, 'data/reference_learnsets.jsonl'):
            if reference['reference_id'] == REFERENCE:
                selected.append(reference)
        require(len(selected) == 1, '参考原本の欠落/重複')
        reference = selected[0]
        require(reference['national_no'] == 670 and reference['source_form'] == 5
                and reference['selected_game'] == 'legendsza', '参考原本の姿不一致')
        routes = reference['routes']
        require(bool(routes), '空の参考原本')
        with archive_csv(archive, 'data/all_routes.csv') as stream:
            columns = next(csv.reader(stream))
        expected = {}
        for route in routes:
            _validate_route(route, crosswalk)
            rid = route['route_id']
            require(rid not in expected, '対象route重複')
            expected[rid] = (sha(encode(project_csv(reference, route, columns))), route['route_kind'])
        counts = {}
        # partition原本も対象referenceだけ照合。source ZIP自体のhashは検証済み。
        for kind, name in [(None, 'data/all_routes.csv'), *CSV_PARTITIONS.items()]:
            with archive_csv(archive, name) as stream:
                reader = csv.DictReader(stream)
                require(reader.fieldnames == columns, 'partition header不一致')
                counts[name] = consume_csv(
                    (row for row in reader if row['reference_id'] == REFERENCE), columns, expected, kind=kind)
        compiled = [_compile_route_row(target, route, crosswalk, {}) for route in routes]
        result = {
            'status': 'PASS_FIXED_REFERENCE_ONLY_NOT_RUNTIME_ADOPTED', 'task': TASK,
            'source_head': os.environ.get('GITHUB_SHA'), 'run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
            'archive': lock['archive'], 'reference_id': REFERENCE,
            'reference_member': lock['members']['data/reference_learnsets.jsonl'],
            'crosswalk_member': lock['members']['data/move_id_crosswalk.csv'],
            'repository_sources': sources, 'reference_sha256': sha(encode(reference)),
            'routes': len(routes), 'csv_counts': counts,
            'original_target_apply': False, 'accepted_official_records_regenerated': 0,
            'accepted_payload_regenerations': 0, 'rom_changes': 0, 'native_runs': 0,
            'issue19_complete': False, 'release_ready': False,
        }
        require(sources == {name: file_identity(ROOT / name) for name in sources}, '入力変更')
        output.mkdir(parents=True)
        for name, value in [('reference.json', reference), ('target.json', target),
                            ('compiled.json', compiled),
                            ('crosswalk.json', {str(r['official_move_id']): crosswalk[r['official_move_id']] for r in routes})]:
            (output / name).write_bytes(encode(value))
        result['files'] = {p.name: file_identity(p) for p in sorted(output.iterdir())}
        (output / 'receipt.json').write_bytes(encode(result))
        return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(extract(args.zip, args.output), ensure_ascii=False, sort_keys=True))
