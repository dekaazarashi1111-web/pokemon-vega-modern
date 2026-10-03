"""Issue19: ZIPの採用行を無損失で隔離する。既存runtime/P03/P07は変更しない。"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from tools.modernization_identity import CheckedArchive, stable_json
from tools.modernization_learnsets import (
    ARCHIVE_ROOT, _ReferenceMeta, _compile_route_row, _csv_member,
    _iter_jsonl_member, _json_member, _load_crosswalk, _load_identity,
    _load_runtime_supply, _object_sha, _validate_adopted_record,
    _validate_decisions, _validate_policy, _validate_route,
)

TASK = 'USER-20260921-LEARNSET-BASELINE-RESET'
LOCK = 'config/pr16_learnset_baseline_source_lock.json'
HISTORY = 'content/modernization/pr16_candidate_wiki_p07_source_rows.json'
CODE = ('tools/pr16_learnset_baseline.py', 'scripts/pr16_learnset_baseline.py')
KINDS = {'direct': 78239, 'pre_evolution': 35183, 'shared_egg': 5041, 'form_change': 61}
CSV_PARTITIONS = {
    'direct': 'data/direct_learning_routes.csv',
    'pre_evolution': 'data/pre_evolution_routes.csv',
    'shared_egg': 'data/shared_egg_routes.csv',
    'form_change': 'data/form_change_routes.csv',
}
META_COLUMNS = {'reference_id', 'target_national_no', 'target_source_form',
                'target_name_ja', 'selected_game'}
CONTAINER_COLUMNS = {'inheritance_chain_names_ja', 'form_change_chain',
                     'form_change_chain_names_ja', 'inheritance_path',
                     'inheritance_chain', 'via_form', 'table_alias_for'}


class BaselineError(ValueError):
    """入力・経路・隔離境界が不正。代用品を採用しない。"""


def require(ok: Any, message: str) -> None:
    if not ok:
        raise BaselineError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':')) + '\n').encode('utf-8')


def file_identity(path: Path) -> dict[str, Any]:
    require(path.is_file() and not path.is_symlink(), '通常ファイルでない入力')
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            digest.update(block)
    return {'size': path.stat().st_size, 'sha256': digest.hexdigest()}


def validate_lock(root: Path, archive: CheckedArchive) -> dict[str, Any]:
    lock = json.loads((root / LOCK).read_bytes())
    require(lock['task'] == TASK and lock['schema_version'] == 1, 'source-lock schema')
    identity = archive.identity()
    for key in ('size', 'sha256', 'archive_root'):
        require(identity[key] == lock['archive'][key], 'ZIP source-lock不一致: ' + key)
    for path, expected in lock['repository_sources'].items():
        require(file_identity(root / path) == expected, '固定source不一致: ' + path)
    # 原本memberは展開/実行しない。readme/policy/CSV/JSONLの全byteを固定する。
    for path, expected in lock['members'].items():
        name, stream = archive.lines(f'{ARCHIVE_ROOT}/{path}')
        require(name == f'{ARCHIVE_ROOT}/{path}', '原本member root不一致')
        digest, size = hashlib.sha256(), 0
        with stream:
            for block in iter(lambda: stream.read(1048576), b''):
                digest.update(block)
                size += len(block)
        require({'size': size, 'sha256': digest.hexdigest()} == expected,
                '原本member不一致: ' + path)
    return lock


def csv_value(value: Any) -> str:
    if value is None:
        return ''
    if isinstance(value, (dict, list)):
        return encode(value).decode().rstrip('\n')
    return str(value)


def normalize_csv_row(row: dict[str, str], columns: list[str]) -> dict[str, str]:
    require(set(row) == set(columns) and None not in row.values(), 'CSV列欠落/余剰')
    result = dict(row)
    for key in CONTAINER_COLUMNS & set(row):
        if row[key]:
            try:
                value = json.loads(row[key])
            except json.JSONDecodeError:
                # 原本の一部はscalar注記。勝手に分解しない。
                continue
            if isinstance(value, (dict, list)):
                result[key] = csv_value(value)
    return result


def project_csv(reference: dict, route: dict, columns: list[str]) -> dict[str, str]:
    metadata = {
        'reference_id': reference['reference_id'],
        'target_national_no': reference['national_no'],
        'target_source_form': reference['source_form'],
        'target_name_ja': reference['species_name_ja'],
        'selected_game': reference['selected_game'],
    }
    require(set(route) <= set(columns), 'CSVに表現されない原本field')
    return {key: csv_value(metadata[key] if key in metadata else route.get(key))
            for key in columns}


def consume_csv(rows: Iterable[dict[str, str]], columns: list[str], expected: dict,
                *, kind: str | None = None) -> int:
    """同一route_idでも内容改変・参照先違い・二重出現を拒否する。"""
    seen: set[str] = set()
    for raw in rows:
        row = normalize_csv_row(raw, columns)
        rid = row.get('route_id', '')
        require(rid in expected and rid not in seen, '未知/重複CSV route_id: ' + rid)
        require(expected[rid][0] == sha(encode(row)), 'CSV/JSONL意味差分: ' + rid)
        require(kind is None or row['route_kind'] == kind, 'CSV経路partition違反')
        seen.add(rid)
    wanted = {rid for rid, (_, rk) in expected.items() if kind is None or rk == kind}
    require(seen == wanted, 'CSV partitionの欠落/余剰')
    return len(seen)


def archive_csv(archive: CheckedArchive, name: str):
    actual, stream = archive.lines(f'{ARCHIVE_ROOT}/{name}')
    require(actual == f'{ARCHIVE_ROOT}/{name}', 'CSV path不一致')
    return io.TextIOWrapper(stream, encoding='utf-8-sig', newline='')


def ensure_output(root: Path, output: Path) -> Path:
    root, output = root.resolve(), output.absolute()
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'output symlink禁止')
    output = output.resolve()
    require(output.is_relative_to(root / '.local') and output != root / '.local',
            '出力先は専用.local配下だけ。tracked/source領域は変更しない')
    return output


def compare_outputs(output: Path, expected: dict[str, dict]) -> None:
    entries = list(output.iterdir())
    require(all(p.is_file() and not p.is_symlink() for p in entries), '生成物にdirectory/symlink混入')
    actual = {p.name: file_identity(p) for p in entries}
    require(actual == expected, '生成物hash/集合の差分。checkは修正しない')


def history_inventory(root: Path, targets: dict) -> dict:
    document = json.loads((root / HISTORY).read_bytes())
    groups, counts = {}, Counter()
    for group, rows in document['groups'].items():
        out = []
        for row in rows:
            target = targets[row['species_key']]
            require(row['species_id'] == target['canonical_id'], '履歴ID衝突')
            official = target['input']['apply']
            state = ('OFFICIAL_BASELINE_MEMBERSHIP_REQUIRED' if official
                     else 'VEGA_ORIGINAL_SOURCE_COMPARISON_REQUIRED')
            out.append({'source_row': row, 'baseline_imported': False, 'disposition': state})
            counts[state] += 1
        groups[group] = out
    require(sum(counts.values()) == 1572, 'P07原本1572件を保持できていない')
    return {'source': HISTORY, 'source_identity': file_identity(root / HISTORY),
            'active_input': False, 'counts': dict(sorted(counts.items())), 'groups': groups}


def baseline_row(target: dict, route: dict, crosswalk: dict, catalog: dict, identity: dict) -> dict:
    require(target['input']['apply'] is True, '非採用/保存layerの直接混入')
    compiled = _compile_route_row(target, route, crosswalk, catalog)
    compiled['layer'] = 'official_baseline'
    compiled['source_identity'] = identity
    compiled['runtime_adoption'] = 'NOT_ACTIVATED'
    return compiled


def source_gate(*, vega_complete: bool, exceptions_resolved: bool,
                runtime_complete: bool) -> dict:
    reasons = []
    for ok, name in ((vega_complete, 'VEGA_ORIGINAL_BASELINE_REQUIRED'),
                     (exceptions_resolved, 'EXPLICIT_ENGINE_ADJUDICATION_REQUIRED'),
                     (runtime_complete, 'SUCCESSOR_ROM_WIKI_NATIVE_REQUIRED')):
        if not ok:
            reasons.append(name)
    return {'ready': not reasons, 'blockers': reasons}


def prepare(root: Path, zip_path: Path, output: Path) -> dict:
    """全採用1299件を隔離生成。既存P03訂正/保存layerは一切unionしない。"""
    root = root.resolve()
    output = ensure_output(root, output)
    require(not output.exists(), '出力先が既存。別の空出力先で生成する')
    _, targets, manifests = _load_identity(root)
    source_targets = {k: t for k, t in targets.items() if t['input']['apply']}
    require(len(source_targets) == 1299, '公式採用対象1299件不一致')
    with CheckedArchive(zip_path, 'learnsets') as archive:
        lock = validate_lock(root, archive)
        _validate_policy(_json_member(archive, 'config/policy.json'))
        _validate_decisions(_csv_member(archive, 'data/stage61_record_decisions.csv'), targets)
        crosswalk = _load_crosswalk(_csv_member(archive, 'data/move_id_crosswalk.csv'), manifests['moves'])
        catalog, _, _ = _load_runtime_supply(
            _csv_member(archive, 'implementation/existing_runtime_slot_projection.csv'),
            _csv_member(archive, 'implementation/moves_without_existing_slot.csv'),
            targets, manifests['species'])
        with archive_csv(archive, 'data/all_routes.csv') as f:
            columns = next(csv.reader(f))
        require(len(columns) == len(set(columns)) and META_COLUMNS <= set(columns), 'CSV header不正')
        references, csv_expected, kinds = {}, {}, Counter()
        for ref in _iter_jsonl_member(archive, 'data/reference_learnsets.jsonl'):
            rid = ref['reference_id']
            require(rid not in references, 'reference重複')
            routes = ref['routes']
            references[rid] = _ReferenceMeta(rid, _object_sha(ref), _object_sha(routes), len(routes),
                tuple(ref['all_official_move_ids']), tuple(ref['all_project_move_ids']),
                tuple(ref['unimplemented_official_move_ids']))
            for route in routes:
                _validate_route(route, crosswalk)
                route_id = route['route_id']
                require(route_id not in csv_expected, 'reference route重複')
                csv_expected[route_id] = (sha(encode(project_csv(ref, route, columns))), route['route_kind'])
                kinds[route['route_kind']] += 1
        require(len(references) == 1377 and len(csv_expected) == 125746, '参考表coverage違反')
        csv_counts = {}
        for kind, name in [(None, 'data/all_routes.csv'), *CSV_PARTITIONS.items()]:
            with archive_csv(archive, name) as f:
                reader = csv.DictReader(f)
                require(reader.fieldnames == columns, 'partition CSV header不一致')
                csv_counts[name] = consume_csv(reader, columns, csv_expected, kind=kind)
        del csv_expected
        # 入力検証が済むまでファイルを作らない。失敗出力にPASS receiptは置かない。
        output.mkdir(parents=True)
        counts, methods, consumers = Counter(), Counter(), Counter()
        seen, index, blocked, supply = set(), [], [], Counter()
        with (output / 'official_baseline.jsonl').open('wb') as out:
            for record in _iter_jsonl_member(archive, 'data/adopted_stage61_learnsets.jsonl'):
                key = record['stage61_key']
                require(key in source_targets and key not in seen, '採用対象未知/重複')
                target = source_targets[key]
                _validate_adopted_record(record, target, references[record['reference_id']], crosswalk)
                framed = hashlib.sha256()
                rc = Counter()
                for route in record['routes']:
                    compiled = baseline_row(target, route, crosswalk, catalog,
                        lock['members']['data/adopted_stage61_learnsets.jsonl'])
                    raw = encode(compiled)
                    out.write(raw); framed.update(raw)
                    counts[route['route_kind']] += 1
                    methods[route['method']] += 1
                    consumers[compiled['consumer']] += 1
                    rc[route['route_kind']] += 1
                    if route['project_move_id'] == 1063:
                        blocked.append({'species_key': key, 'route_id': route['route_id'],
                            'move_key': compiled['move_key'], 'method': route['method'],
                            'disposition': 'SOURCE_RETAINED_ENGINE_EXCEPTION_UNRESOLVED'})
                    if 'runtime_supply' in compiled:
                        supply[compiled['runtime_supply']['status']] += 1
                index.append({'species_key': key, 'species_id': target['canonical_id'],
                    'form_key': target['form_key'], 'national_no': target['national_no'],
                    'source_form': target['source_form'], 'reference_id': target['reference_id'],
                    'routes': len(record['routes']), 'route_kinds': dict(sorted(rc.items())),
                    'normalized_routes_sha256': framed.hexdigest()})
                seen.add(key)
        require(seen == set(source_targets) and dict(counts) == KINDS, '公式採用coverage差分')
        vega = [{'species_key': k, 'species_id': t['canonical_id'],
                 'vega_id': int(manifests['species'].by_key[k]['vega_id']),
                 'source_state': 'ORIGINAL_VEGA_SOURCE_REQUIRED'}
                for k, t in targets.items()
                if t['input']['target_status'] == 'REQUIRED_VEGA_ORIGINAL']
        require(len(vega) == 181, 'Vega181種の分離不一致')
        adjudication = {
            'source_rows_not_silently_dropped': blocked,
            'existing_decision': {'path': 'config/modernization_adoption_decisions.json',
                'action': 'NOT_AUTO_INHERITED_IN_ISSUE19_BASELINE'},
            'target_correction': {'species_key': 'SPECIES_KEY_CATERPIE', 'species_id': 649,
                'reference_id': 'swordshield:0010.00', 'source_adopted': False,
                'existing_p01_corrected_adoption': True,
                'action': 'KEEP_HISTORY_REQUIRE_EXPLICIT_BASELINE_ADJUDICATION'},
            'existing_runtime_slots_are_projections_not_supply_acceptance': True,
        }
        documents = {
            'official_index.json': {'schema_version': 1, 'records': index},
            'vega_original_pending.json': {'records': vega, 'imported_from_preservation_rows': 0},
            'owner_approved_overlay.json': {'schema_version': 1, 'rows': []},
            'historical_layers.json': history_inventory(root, targets),
            'adjudication.json': adjudication,
        }
        for name, value in documents.items():
            (output / name).write_bytes(stable_json(value))
        receipt = {
            'schema_version': 1, 'task': TASK, 'status': 'OFFICIAL_SOURCE_ISOLATION_PASS_RUNTIME_OPEN',
            'source_lock': {'path': LOCK, **file_identity(root / LOCK)},
            'code_identity': {p: file_identity(root / p) for p in CODE},
            'zip_identity': lock['archive'], 'reference_records': len(references),
            'reference_routes': sum(kinds.values()), 'csv_row_counts': csv_counts,
            'official_records': len(index), 'official_routes': sum(counts.values()),
            'route_kinds': dict(sorted(counts.items())), 'methods': dict(sorted(methods.items())),
            'consumers': dict(sorted(consumers.items())), 'supply_projection': dict(sorted(supply.items())),
            'unknown_species_or_ambiguous_mapping': 0, 'source_semantic_differences': 0,
            'vega_pending_species': len(vega), 'vega_baseline_rows_imported': 0,
            'owner_overlay_rows': 0, 'p07_historical_rows_preserved': 1572,
            'spec_only_routes': len(blocked), 'spec_only_species': len({r['species_key'] for r in blocked}),
            'activation_gate': source_gate(vega_complete=False, exceptions_resolved=False, runtime_complete=False),
            'rom_changed': False, 'new_native_runs': 0, 'release_ready': False,
            'outputs': {p.name: file_identity(p) for p in sorted(output.iterdir())},
        }
        (output / 'receipt.json').write_bytes(stable_json(receipt))
        return receipt


def check(root: Path, output: Path) -> dict:
    """検証済み隔離出力だけをread-only再照合。再生成/時刻更新はしない。"""
    output = ensure_output(root, output)
    receipt = json.loads((output / 'receipt.json').read_bytes())
    require(receipt['task'] == TASK and receipt['status'] == 'OFFICIAL_SOURCE_ISOLATION_PASS_RUNTIME_OPEN', 'receipt境界不一致')
    require(receipt['source_lock'] == {'path': LOCK, **file_identity(root / LOCK)}, 'source-lockが変化')
    require(receipt['code_identity'] == {p: file_identity(root / p) for p in CODE}, '生成器が変化')
    for name, expected in json.loads((root / LOCK).read_bytes())['repository_sources'].items():
        require(file_identity(root / name) == expected, '依存sourceが変化: ' + name)
    require(receipt['activation_gate']['ready'] is False and receipt['rom_changed'] is False
            and receipt['release_ready'] is False, 'source-onlyを製品受入へ昇格しない')
    require(receipt['official_records'] == 1299 and receipt['route_kinds'] == KINDS, 'receipt coverage不一致')
    expected = dict(receipt['outputs'])
    expected['receipt.json'] = file_identity(output / 'receipt.json')
    compare_outputs(output, expected)
    require(json.loads((output / 'owner_approved_overlay.json').read_bytes())['rows'] == [], '未承認overlay混入')
    return receipt
