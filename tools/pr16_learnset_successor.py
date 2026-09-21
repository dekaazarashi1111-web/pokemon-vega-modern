#!/usr/bin/env python3
"""Issue19の裁定済み原本を9 consumerへlosslessに分割し、旧候補との差分を作る。

ROMを変更する器ではない。未選択Species/Formや条件を旧表で補わず、
後継ROM adapterが解決すべき境界を明示する。checkは一切書き込まない。
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
BASE = 'content/modernization/'
OFFICIAL = BASE + 'pr16_learnset_baseline_evidence/'
VEGA = BASE + 'pr16_vega_adjudication/'
WIKI = 'docs/wiki/p08-candidate-46487d98/data/'
CONSUMERS = ('level_up', 'evolution', 'reminder', 'machine', 'tutor', 'egg',
             'pre_evolution_carry', 'shared_egg', 'form_change')
DIRECT_COMPARE = {'level_up', 'egg', 'machine', 'tutor', 'reminder', 'shared_egg'}
DECLINED = 'OWNER_DECLINED_NO_ENGINE_IMPLEMENTATION'
PHASE = 'learnset-successor-consumer-tables-v1'
CODE = 'tools/pr16_learnset_successor.py'


def require(ok: Any, message: str) -> None:
    if not ok:
        raise ValueError(message)


def encode(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def regular(path: Path) -> Path:
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symlinkは禁止')
    require(path.is_file(), '入力regular fileがない: ' + str(path))
    return path


def identity(path: Path) -> dict:
    path = regular(path)
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
            size += len(block)
    return {'sha256': digest.hexdigest(), 'size': size}


def read_json(path: Path) -> Any:
    return json.loads(regular(path).read_text(encoding='utf-8'))


def bound(path: Path, expected: Mapping) -> None:
    require(identity(path) == dict(expected), '入力hash/size不一致: ' + path.name)


def rows(path: Path) -> Iterable[dict]:
    with regular(path).open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            value = json.loads(line)
            require(isinstance(value, dict), f'JSONL object不正: {path.name}:{number}')
            yield value


def manifest(path: Path, key: str) -> dict[int, dict]:
    with regular(path).open(encoding='utf-8-sig', newline='') as stream:
        data = list(csv.DictReader(stream))
    result = {int(row['id']): row for row in data}
    require(len(result) == len(data) == len({row[key] for row in data}), 'manifest重複')
    return result


def consumer(route: Mapping) -> str:
    kind, method = route.get('route_kind'), route.get('method')
    if kind == 'pre_evolution':
        require(route.get('target_learning_level') is None, '進化前技を対象levelへ転記')
        return 'pre_evolution_carry'
    if kind == 'form_change':
        require(bool(route.get('form_change_condition_ja')), '姿変更条件がない')
        return 'form_change'
    if kind == 'shared_egg':
        require(method == 'shared_egg' and bool(route.get('acquisition_condition_ja')),
                '共有タマゴの方法/条件がない')
        return 'shared_egg'
    mapping = {'level_up': 'level_up', 'evolution': 'evolution', 'reminder': 'reminder',
               'tm': 'machine', 'tr': 'machine', 'tutor': 'tutor', 'egg': 'egg',
               'special_breeding': 'egg', 'form_move': 'form_change',
               'battle_transform': 'form_change'}
    require(kind == 'direct' and method in mapping, '未知の習得方法/経路')
    return mapping[method]


def move_guard(move_id: int, key: str, moves: Mapping[int, Mapping], *, official=False) -> bool:
    if move_id == 1063:
        require(official and key == 'MOVE_KEY_ALLYSWITCH' and move_id not in moves,
                'サイドチェンジの予約identityが不正')
        return False
    require(type(move_id) is int and move_id > 0 and move_id in moves
            and moves[move_id]['move_key'] == key, '未知move/ID-key不一致')
    return True


def candidate_catalog(old: Mapping[int, dict]) -> dict[tuple[str, int], list[int]]:
    slots: dict[tuple[str, int], tuple[int, str]] = {}
    for species in old.values():
        for route in species['routes']:
            family = route['route']
            if family not in ('machine', 'tutor'):
                continue
            slot = route['slot']
            require(type(slot) is int and slot >= 0, '候補slotが非負整数でない')
            value = (route['move_id'], route['move_key'])
            require(slots.get((family, slot), value) == value, '候補catalog slot衝突')
            slots[family, slot] = value
    result: dict[tuple[str, int], list[int]] = collections.defaultdict(list)
    for (family, slot), (mid, _) in sorted(slots.items()):
        result[family, mid].append(slot)
    return dict(result)


def binding(family: str, mid: int, catalog: Mapping) -> dict:
    """原作TM番号や旧sourceのslotを現在候補のslotと取り違えない。"""
    if family not in ('machine', 'tutor'):
        return {'status': 'CONSUMER_ADAPTER_REQUIRED'}
    slots = catalog.get((family, mid), [])
    return {'status': 'CANDIDATE_SLOT_REBIND_REQUIRED' if slots else 'ARCHIVE_ADAPTER_REQUIRED',
            'candidate_slots_zero_based': list(slots), 'family': family,
            'compatibility_granted': False, 'physical_supply_verified': False}


def official_row(row: dict, order: int, moves: Mapping, catalog: Mapping) -> dict:
    route = row['source_route']
    family = consumer(route)
    require(row['layer'] == 'official_baseline' and row['consumer'] == family,
            '公式原本layer/consumer不一致')
    mid, key = route['project_move_id'], row['move_key']
    active = move_guard(mid, key, moves, official=True)
    require(row['runtime_move_ready'] is active, '原本move-ready不一致')
    if family == 'level_up':
        require(type(route['target_learning_level']) is int and 1 <= route['target_learning_level'] <= 100,
                '通常level範囲不正')
    conditional = route['method'] == 'special_breeding'
    return {'species_id': row['target_species_id'], 'species_key': row['target_species_key'],
            'form_key': row['target_form_key'], 'consumer': family, 'move_id': mid, 'move_key': key,
            'source_order': order, 'source_id': 'official:' + route['route_id'],
            'layer': 'official_baseline', 'disposition': 'BASELINE_SELECTED' if active else DECLINED,
            'conditional_egg': conditional,
            'runtime_binding': binding(family, mid, catalog) if active else {'status': DECLINED},
            'provenance': row}


def vega_row(species: dict, family: str, route: dict, moves: Mapping, catalog: Mapping) -> dict:
    require(family in ('level_up', 'machine', 'tutor', 'egg'), 'Vega method不正')
    mid, key = route['move_id'], route['move_key']
    move_guard(mid, key, moves)
    if family == 'level_up':
        require(type(route['level']) is int and 1 <= route['level'] <= 100, 'Vega level範囲不正')
    return {'species_id': species['species_id'], 'species_key': species['species_key'],
            'form_key': '', 'consumer': family, 'move_id': mid, 'move_key': key,
            'source_order': route['order'],
            'source_id': f"vega:{species['species_id']}:{family}:{route['order']}",
            'layer': 'vega_original_baseline', 'disposition': 'BASELINE_SELECTED',
            'conditional_egg': False, 'runtime_binding': binding(family, mid, catalog),
            'provenance': {'source_decision': species['source_decision'],
                           'source_kind': species['source_kind'], 'dex_no': species['dex_no'],
                           'vega_id': species['vega_id'], 'source_route': route}}


def signature(row: dict, *, old=False) -> tuple | None:
    """比較できるのは直接習得のmembershipのみ。条件同値を捏造しない。"""
    family = row['route'] if old else row['consumer']
    family = {'machine_archive': 'machine', 'tutor_archive': 'tutor',
              'move_memory_reminder': 'reminder'}.get(family, family)
    if family not in DIRECT_COMPARE or (not old and row['conditional_egg']):
        return None
    level = None
    if family == 'level_up':
        source = row if old else row['provenance']['source_route']
        level = source.get('target_learning_level', source.get('level'))
        if not isinstance(level, int) or level < 1:
            return None
    return family, row['move_id'], level


def compare_species(old: dict, active: list[dict], selected: bool) -> dict:
    new_signatures = collections.Counter(s for row in active if (s := signature(row)) is not None)
    old_signatures = collections.Counter(s for row in old['routes'] if (s := signature(row, old=True)) is not None)
    common = old_signatures & new_signatures
    remaining = common.copy()
    entries = []
    for order, row in enumerate(old['routes']):
        sig = signature(row, old=True)
        if not selected:
            disposition = 'SOURCE_NOT_SELECTED_NO_AUTOMATIC_FALLBACK_OR_DELETION'
        elif sig is None:
            disposition = 'LEGACY_CONDITIONAL_OR_PRESERVATION_REQUIRES_ADAPTER_REVIEW'
        elif remaining[sig]:
            disposition = 'SAME_MEMBERSHIP_ONLY_CONDITION_ORDER_UNPROVEN'
            remaining[sig] -= 1
        else:
            disposition = 'NOT_IN_SELECTED_DIRECT_BASELINE'
        entries.append({'old_order': order, 'old_route': row['route'], 'move_id': row['move_id'],
                        'move_key': row['move_key'], 'disposition': disposition})
    level_before = [s for row in old['routes'] if (s := signature(row, old=True)) and s[0] == 'level_up']
    level_after = [s for row in active if (s := signature(row)) and s[0] == 'level_up']
    return {'species_id': old['species_id'], 'species_key': old['species_key'],
            'source_selected': selected, 'old_routes': len(entries), 'selected_routes': len(active),
            'common_direct_membership': sum(common.values()) if selected else None,
            'old_direct_not_selected': sum((old_signatures - new_signatures).values()) if selected else None,
            'new_direct_not_in_old': sum((new_signatures - old_signatures).values()) if selected else None,
            'level_up_sequence_equal': level_before == level_after if selected else None,
            'old_entries': entries, 'runtime_applied': False}


def hatch_link(row: dict, families: Mapping, selected: Mapping, moves: Mapping) -> dict:
    """原作孵化根拠と新baselineのmembershipを分離し、技を勝手に追加しない。"""
    require(row['classification'] == 'PRE_EVOLUTION_EGG'
            and row['adopt_as_receiver_direct_egg'] is False and row['add_as_shared_egg'] is False,
            'Vega非直接eggをdirect/sharedへ展開')
    move_guard(row['move_id'], row['move_key'], moves)
    family = families[row['species_id'], row['source_group_index']]
    original_rows = row['original_direct_egg_rows']
    require(family['hatch_species_id'] == row['hatch_species_id'] and original_rows
            and all(r in family['direct_egg_rows'] and r['move_id'] == row['move_id'] for r in original_rows),
            '裁定済み原作孵化種direct eggに行がない')
    present = row['move_id'] in selected.get(row['hatch_species_id'], set())
    return {'receiver_species_id': row['species_id'], 'hatch_species_id': row['hatch_species_id'],
            'move_id': row['move_id'], 'consumer': 'pre_evolution_carry',
            'direct_grant': False, 'shared_grant': False,
            'hatch_selected_direct_egg_membership': present,
            'cross_source_status': 'MEMBERSHIP_ONLY_NATIVE_PENDING' if present
            else 'HATCH_BASELINE_DIFFERENCE_REQUIRES_ADAPTER_REVIEW', 'provenance': row}


class Sink:
    """生成時だけ書込み、check時は同じbyte列のhashをメモリで集計する。"""
    def __init__(self, output: Path | None):
        self.output = output
        self.hashes: dict[str, Any] = {}
        self.sizes: dict[str, int] = collections.defaultdict(int)
        self.handles: dict[str, Any] = {}

    def emit(self, name: str, value: Any) -> None:
        raw = encode(value)
        self.hashes.setdefault(name, hashlib.sha256()).update(raw)
        self.sizes[name] += len(raw)
        if self.output is not None:
            if name not in self.handles:
                self.handles[name] = (self.output / name).open('xb')
            self.handles[name].write(raw)

    def close(self) -> dict:
        for stream in self.handles.values():
            stream.close()
        return {name: {'sha256': digest.hexdigest(), 'size': self.sizes[name]}
                for name, digest in sorted(self.hashes.items())}


def compile_tables(root: Path, official: Path, output: Path | None = None) -> dict:
    """受入済み入力を検査し、原本採取・旧generator・nativeを呼ばず後継表を作る。"""
    proof = read_json(root / (BASE + 'pr16_learnset_baseline_checkpoint.json'))
    vp = read_json(root / (BASE + 'pr16_vega_adjudication_checkpoint.json'))
    require(proof['status'] == 'ACCEPTED_OFFICIAL_SOURCE_ISOLATION_ONLY'
            and vp['status'] == 'ACCEPTED_SOURCE_ADJUDICATION_ONLY_RUNTIME_PENDING', '入力受入scope不一致')
    receipt = read_json(root / (OFFICIAL + 'receipt.json'))
    bound(root / (OFFICIAL + 'receipt.json'), proof['proof_bindings']['receipt.json'])
    for name in ('official_baseline.jsonl', 'official_index.json', 'owner_approved_overlay.json'):
        bound(official / name, receipt['outputs'][name])
    overlay = read_json(official / 'owner_approved_overlay.json')
    require(overlay == {'rows': [], 'schema_version': 1}, 'owner overlayは空でなければならない')
    for name in ('adopted_vega_original_baseline.jsonl', 'nondirect_egg.jsonl', 'breeding_families.json'):
        bound(root / (VEGA + name), vp['files'][name])
    index = read_json(official / 'official_index.json')['records']
    by_official = {r['species_id']: r for r in index}
    require(len(by_official) == len(index) == proof['official_records'], '公式index件数/重複')
    species = manifest(root / 'manifests/species_ids.csv', 'species_key')
    moves = manifest(root / 'manifests/move_ids.csv', 'move_key')
    identity_contract = read_json(root / (BASE + 'identity_contract.json'))
    require(identity_contract['status'] == 'PASS', 'identity contract未検証')
    for name in ('species', 'moves'):
        m = identity_contract['manifests'][name]
        require(identity(root / m['path'])['sha256'] == m['sha256'], 'manifest固定hash不一致')
    targets = {r['canonical_id']: r for r in identity_contract['target_normalization']['records']}
    original = {r['species_id']: r for r in rows(root / (VEGA + 'adopted_vega_original_baseline.jsonl'))}
    require(len(original) == 181 and not set(original) & set(by_official), '公式/Vegaの重複または欠落')
    wi = read_json(root / (WIKI + 'index.json'))
    bound(root / (WIKI + 'learnsets.jsonl'), wi['files']['data/learnsets.jsonl'])
    current = read_json(root / (BASE + 'pr16_native_supply_resume_20260913.json'))['current_p08_candidate']
    require(all(wi['candidate'][k] == current[k] for k in ('sha256', 'size', 'crc32')), '比較候補identity不一致')
    old_list = list(rows(root / (WIKI + 'learnsets.jsonl')))
    old = {r['species_id']: r for r in old_list}
    require(len(old) == len(old_list) and set(by_official) | set(original) <= set(old), '候補種の重複/欠落')
    for sid, row in old.items():
        require(sid not in species or row['species_key'] == species[sid]['species_key'], '旧候補Species key不一致')
        for route in row['routes']:
            move_guard(route['move_id'], route['move_key'], moves)
    catalog = candidate_catalog(old)
    official_groups = iter(itertools.groupby(rows(official / 'official_baseline.jsonl'),
                                             key=lambda r: r['target_species_id']))
    pending = next(official_groups, None)
    sink = Sink(output)
    totals, exclusions, supplies, coverage = (collections.Counter() for _ in range(4))
    side_species: set[int] = set()
    official_rows = vega_rows = matched = removed = added = 0
    changed_level = []
    seen_official = set()
    hatch_selected: dict[int, set[int]] = {}
    hatch_gaps = 0
    inputs = {
        'official_baseline.jsonl': identity(official / 'official_baseline.jsonl'),
        'official_index.json': identity(official / 'official_index.json'),
        'owner_approved_overlay.json': identity(official / 'owner_approved_overlay.json'),
    }
    tracked = [CODE, 'manifests/species_ids.csv', 'manifests/move_ids.csv',
               BASE + 'identity_contract.json', OFFICIAL + 'receipt.json',
               BASE + 'pr16_learnset_baseline_checkpoint.json',
               BASE + 'pr16_vega_adjudication_checkpoint.json', WIKI + 'index.json', WIKI + 'learnsets.jsonl',
               *(VEGA + name for name in ('adopted_vega_original_baseline.jsonl', 'nondirect_egg.jsonl', 'breeding_families.json'))]
    inputs.update({name: identity(root / name) for name in tracked})
    try:
        for sid, old_species in sorted(old.items()):
            active = []
            if sid in by_official:
                require(pending is not None and pending[0] == sid and sid not in seen_official,
                        '公式原本の順序/Species grouping不一致')
                raw_rows = list(pending[1])
                require(len(raw_rows) == by_official[sid]['routes'], '公式種別行数不一致')
                digest = hashlib.sha256(b''.join(encode(r) for r in raw_rows)).hexdigest()
                require(digest == by_official[sid]['normalized_routes_sha256'], '公式種別route hash不一致')
                require(species[sid]['species_key'] == by_official[sid]['species_key']
                        and species[sid]['form_key'] == by_official[sid]['form_key'], '公式Species/Form identity不一致')
                require(all(r['target_species_key'] == by_official[sid]['species_key']
                            and r['target_form_key'] == by_official[sid]['form_key'] for r in raw_rows), '公式row identity不一致')
                projected = [official_row(r, order, moves, catalog) for order, r in enumerate(raw_rows)]
                official_rows += len(projected)
                seen_official.add(sid)
                pending = next(official_groups, None)
                state = 'OFFICIAL_SOURCE_SELECTED'
            elif sid in original:
                source = original[sid]
                require(source['species_key'] == species[sid]['species_key'], 'Vega Species identity不一致')
                require(set(source['methods']) == {'level_up', 'egg', 'machine', 'tutor'}, 'Vega methods欠落/追加')
                projected = []
                for family, source_rows in source['methods'].items():
                    require([r['order'] for r in source_rows] == list(range(len(source_rows))), 'Vega元順序不一致')
                    projected.extend(vega_row(source, family, r, moves, catalog) for r in source_rows)
                vega_rows += len(projected)
                state = 'VEGA_SOURCE_SELECTED'
            else:
                projected = []
                state = 'SOURCE_NOT_SELECTED' if sid in species else 'RUNTIME_EXTENSION_NOT_SELECTED'
            ids = [row['source_id'] for row in projected]
            require(len(ids) == len(set(ids)), '種別source route ID重複')
            for row in projected:
                if row['disposition'] == DECLINED:
                    exclusions[row['consumer']] += 1
                    side_species.add(sid)
                    sink.emit('excluded_routes.jsonl', row)
                else:
                    active.append(row)
                    totals[row['consumer']] += 1
                    supplies[row['runtime_binding']['status']] += 1
            for family in CONSUMERS:
                part = [r for r in active if r['consumer'] == family]
                sink.emit(f'{family}.jsonl', {'species_id': sid, 'species_key': old_species['species_key'],
                          'selection': state, 'routes': part, 'runtime_applied': False})
            hatch_selected[sid] = {r['move_id'] for r in active if r['consumer'] == 'egg' and not r['conditional_egg']}
            coverage[state] += 1
            sink.emit('species_coverage.jsonl', {'species_id': sid, 'species_key': old_species['species_key'],
                      'selection': state, 'active_routes': len(active), 'automatic_fallback': False,
                      'source_target': targets.get(sid), 'requires_runtime_adapter': True})
            selected = sid in seen_official or sid in original
            diff = compare_species(old_species, active, selected)
            sink.emit('candidate_diff.jsonl', diff)
            if selected:
                matched += diff['common_direct_membership']
                removed += diff['old_direct_not_selected']
                added += diff['new_direct_not_in_old']
                if not diff['level_up_sequence_equal']:
                    changed_level.append(sid)
        require(pending is None and seen_official == set(by_official), '公式原本の余剰/欠落')
        require(official_rows == proof['official_routes'] and vega_rows == 9923, '原本全数不一致')
        require(sum(exclusions.values()) == 159 and len(side_species) == 103, 'Side Change全数不一致')
        nondirect = list(rows(root / (VEGA + 'nondirect_egg.jsonl')))
        require(len(nondirect) == 2394 and len({r['species_id'] for r in nondirect}) == 92, 'Vega非直接egg全数不一致')
        families = {(r['species_id'], r['source_group_index']): r for r in
                    read_json(root / (VEGA + 'breeding_families.json'))['families']}
        require(len({r['row_key'] for r in nondirect}) == len(nondirect), '非直接egg row key重複')
        for row in nondirect:
            link = hatch_link(row, families, hatch_selected, moves)
            hatch_gaps += not link['hatch_selected_direct_egg_membership']
            sink.emit('vega_hatch_links.jsonl', link)
    finally:
        files = sink.close()
    return {'schema_version': 1, 'phase': PHASE, 'inputs': inputs, 'files': files,
            'candidate': wi['candidate'], 'official_species': len(by_official), 'vega_species': len(original),
            'official_source_routes': official_rows, 'vega_source_routes': vega_rows,
            'selected_routes': sum(totals.values()), 'consumers': dict(sorted(totals.items())),
            'exclusions': dict(sorted(exclusions.items())), 'side_change_excluded': sum(exclusions.values()),
            'side_change_species': len(side_species), 'active_side_change': 0, 'placeholder_rows': 0,
            'owner_overlay_rows': 0, 'vega_nondirect_egg_rows': len(nondirect),
            'vega_nondirect_direct_grants': 0, 'vega_nondirect_shared_grants': 0, 'hatch_baseline_membership_gaps': hatch_gaps,
            'coverage': dict(sorted(coverage.items())), 'runtime_binding_states': dict(sorted(supplies.items())),
            'comparison': {'membership_only': True, 'common_direct_membership': matched,
                           'old_direct_not_selected': removed, 'new_direct_not_in_old': added,
                           'changed_level_sequences': changed_level},
            'runtime_applied': False, 'rom_changes': 0, 'new_native_runs': 0,
            'issue19_complete': False, 'release_ready': False,
            'remaining': ['UNSELECTED_SPECIES_FORM_DISPOSITIONS', 'BINARY_CONSUMER_ADAPTERS', 'CROSS_SOURCE_HATCH_BASELINE_DIFFERENCES',
                          'SUCCESSOR_ROM_WIKI_IMPACT_NATIVE']}


def output_path(root: Path, path: Path, *, create: bool) -> Path:
    root = root.resolve()
    path = path.absolute()
    require(path.is_relative_to(root / '.local'), '出力先はrepository .local内限定')
    require(not any(p.is_symlink() for p in (path, *path.parents)), '出力symlinkは禁止')
    require('..' not in path.parts, '出力path traversalは禁止')
    if create:
        require(not path.exists(), '既存出力への上書きは禁止')
    else:
        require(path.is_dir(), 'check対象出力がない')
    return path


def generate(root: Path, official: Path, output: Path) -> dict:
    output = output_path(root, output, create=True)
    output.mkdir(parents=True)
    receipt = compile_tables(root, official, output)
    (output / 'receipt.json').write_bytes(encode(receipt))
    return receipt


def check(root: Path, official: Path, output: Path) -> dict:
    output = output_path(root, output, create=False)
    expected = compile_tables(root, official)
    require(read_json(output / 'receipt.json') == expected, '後継receipt不一致')
    require({p.name for p in output.iterdir()} == set(expected['files']) | {'receipt.json'}, '出力集合不一致')
    for name, ident in expected['files'].items():
        bound(output / name, ident)
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('generate', 'check'))
    parser.add_argument('--official', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = (generate if args.command == 'generate' else check)(ROOT, args.official, args.output)
    print(json.dumps({k: v for k, v in result.items() if k not in ('inputs', 'files', 'comparison')}, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
