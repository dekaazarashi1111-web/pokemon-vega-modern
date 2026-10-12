"""Eternal専用参考の明示採用と親を変更しない差分payload。ROM書込はしない。"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import copy
import hashlib
import struct

from tools import pr16_learnset_successor as s
from tools import pr16_learnset_payloads as p
from tools import pr16_learnset_species_binding as b
from tools.modernization_learnsets import _compile_route_row
from tools.pr16_learnset_baseline import ensure_output

DECISION = s.BASE + 'pr16_floette_learnset_adoption.json'
SOURCE_EVIDENCE = s.BASE + 'pr16_learnset_floette_evidence/source'
SID, KEY, REF = 1029, 'SPECIES_KEY_FLOETTE_ETERNAL', 'legendsza:0670.05'
PHASE = 'FLOETTE_EXPLICIT_REFERENCE_DELTA_V1'
EXPECTED = {'level_up': 13, 'evolution': 1, 'machine': 23}


def require(ok, message):
    s.require(ok, message)


def check_decision(decision: dict) -> None:
    require(decision['schema_version'] == 1
            and decision['decision'] == 'EXPLICIT_GIFT_REFERENCE_ADOPTION'
            and type(decision['species_id']) is int and decision['species_id'] == SID
            and decision['species_key'] == KEY and decision['reference_id'] == REF,
            'Eternalの明示裁定が必要')
    require(decision['source_selection'] == {'original_p01_apply': False,
            'successor_selected': True, 'layer': 'official_baseline'}, '旧P01を改作しない')
    for field in ('preserve_original_p01', 'preserve_gift_contract', 'preserve_saved_four_moves'):
        require(decision[field] is True, '贈呈/identity/既存4技の保全が必要')
    for field in ('automatic_fallback', 'side_change_adopted', 'runtime_applied',
                  'physical_supply_verified', 'release_ready'):
        require(decision[field] is False, '未受入/非採用境界の昇格禁止')
    require(decision['owner_approved_overlay'] == [] and decision['expected_routes'] == 37
            and decision['expected_consumers'] == EXPECTED and bool(decision['reason_ja']),
            '追加overlay/参考coverage不一致')


def catalog_bits(catalogs: dict, moves: dict) -> dict:
    result = {}
    require(set(catalogs) == set(p.SLOT_COUNTS), '親catalog family集合不一致')
    for family, maximum in p.SLOT_COUNTS.items():
        table = catalogs[family]
        require(table['slot_numbering'] == 'ZERO_BASED_FOR_BINARY_ONLY'
                and table['slot_count'] == maximum and table['observed_slots'] == len(table['slots']),
                '親catalogは受入済み0始まり版だけ')
        by_move, seen = defaultdict(list), set()
        for row in table['slots']:
            bit, mid = row['bit_index'], row['move_id']
            require(type(bit) is int and 0 <= bit < maximum and bit not in seen
                    and type(row['wiki_ordinal']) is int and row['wiki_ordinal'] == bit + 1,
                    'slot重複/範囲/1始まり混入')
            s.move_guard(mid, row['move_key'], moves)
            seen.add(bit); by_move[mid].append(bit)
        # Tutorは受入表に現れる54slotだけ。未観測の10slotを捏造しない。
        require(len(seen) == {'machine': 128, 'tutor': 54}[family], '受入catalog件数不一致')
        result[family] = {mid: sorted(bits) for mid, bits in by_move.items()}
    return result


def adopt(reference: dict, target: dict, crosswalk: dict, gift: dict,
          decision: dict, moves: dict, catalogs: dict) -> list[dict]:
    """全入力は不変。原本から当該姿の37経路だけを後継層へ採用する。"""
    check_decision(decision)
    require(target['canonical_id'] == SID and target['species_key'] == KEY
            and target['form_key'] == 'FORM_KEY_FLOETTE_ETERNAL'
            and target['reference_id'] == REF and target['source_form'] == 5
            and target['input']['apply'] is False and target['normalized']['apply'] is False,
            '通常Floette/旧採用targetへの置換禁止')
    require(reference['reference_id'] == REF and reference['source_form'] == 5
            and reference['national_no'] == 670 and reference['selected_game'] == 'legendsza',
            '参考元のSpecies/Form/作品不一致')
    expected = decision['source_files']['reference.json']
    raw = s.encode(reference)
    require({'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} == expected,
            '固定参考原本のhash不一致')
    require(gift['gift'] == decision['gift_policy'] and gift['map'] == decision['gift_map']
            and gift['gift']['species_id'] == SID and gift['gift']['species_key'] == KEY
            and gift['gift']['repeatability'] == 'ONCE_PER_SAVE', '既存贈呈契約を変更しない')
    slots = catalog_bits(catalogs, moves)
    seen, rows = set(), []
    for order, source in enumerate(reference['routes']):
        require(source['route_id'] not in seen, 'route重複')
        seen.add(source['route_id'])
        item = _compile_route_row(target, source, crosswalk, {})
        mid, key, family = source['project_move_id'], item['move_key'], item['consumer']
        active = s.move_guard(mid, key, moves, official=True)
        # 今回の固定Eternal原本には未実装技も条件付き経路も存在しない。
        require(active and family in EXPECTED and source['route_kind'] == 'direct',
                '固定参考の範囲外/Side Change/条件経路混入')
        if family == 'level_up':
            require(type(source['target_learning_level']) is int
                    and 1 <= source['target_learning_level'] <= 100, 'level0/型/範囲違反')
        positions = slots[family].get(mid, []) if family in p.SLOT_COUNTS else None
        rows.append({'species_id': SID, 'species_key': KEY, 'form_key': target['form_key'],
            'consumer': family, 'move_id': mid, 'move_key': key, 'source_order': order,
            'source_id': 'official-reference:' + REF + ':' + source['route_id'],
            'layer': 'official_baseline', 'adoption': decision['decision'],
            'disposition': 'BASELINE_SELECTED', 'conditional_egg': False,
            'runtime_binding': {'status': 'PREPARED_NOT_INSTALLED',
                'bit_indexes_zero_based': positions, 'physical_supply_verified': False},
            'provenance': dict(item, source_identity=decision['reference_member'],
                archive_identity=decision['archive'], original_p01_apply=False),
            'rewrite_existing_moves': False, 'runtime_applied': False})
    require(len(rows) == 37 and dict(Counter(r['consumer'] for r in rows)) == EXPECTED,
            'Eternalの37経路coverage不一致')
    return rows


def prepare_delta(rows: list[dict], catalogs: dict, moves: dict) -> tuple[dict, list]:
    """学習表だけを生成。level0の進化技はlevel表/贈呈初期4技へ展開しない。"""
    require(dict(Counter(r['consumer'] for r in rows)) == EXPECTED
            and all(r['species_id'] == SID and r['species_key'] == KEY for r in rows), '差分owner不一致')
    slots = catalog_bits(catalogs, moves)
    files, indexes = {}, []
    for family in b.CONSUMERS:
        selected = [row for row in rows if row['consumer'] == family]
        entry = {'species_id': SID, 'species_key': KEY, 'consumer': family,
                 'status': 'PAYLOAD_PREPARED_NOT_INSTALLED', 'routes': len(selected)}
        raw = b''
        if family == 'level_up':
            raw = p.pack_levels(selected)
        elif family in p.SLOT_COUNTS:
            raw, archive, positions = p.compatibility(selected, family, slots[family])
            for row, bits in zip(selected, positions):
                require(bits == row['runtime_binding']['bit_indexes_zero_based'], 'binary slot対応不一致')
            name = 'floette.' + family + '_archive.bin'
            files[name] = p.pack_moves(archive)
            entry['archive'] = {'file': name, 'offset': 0, 'size': len(files[name]), 'moves': len(archive)}
        elif family == 'egg':
            require(not selected, '参考にないegg技を新設しない')
            raw = struct.pack('<HH', 20000 + SID, 65535)
        elif family in ('evolution', 'reminder', 'shared_egg'):
            raw = p.pack_moves(list(dict.fromkeys(r['move_id'] for r in selected)))
        else:
            require(not selected, '参考にない条件付き習得の新設禁止')
        name = 'floette.' + family + '.bin'
        if family in ('pre_evolution_carry', 'form_change'):
            entry['payload'] = None
        else:
            files[name] = raw
            entry['payload'] = {'file': name, 'offset': 0, 'size': len(raw)}
        indexes.append(entry)
    return files, indexes


def compose_index(parent: list[dict], delta: list[dict]) -> list[dict]:
    """既存1670 ownerのJSONは同一内容。置換を許すのは未裁定1029の9枠だけ。"""
    mapping = {}
    for entry in parent:
        key = entry['species_id'], entry['consumer']
        require(type(key[0]) is int and 0 <= key[0] < 1671
                and key[1] in b.CONSUMERS and key not in mapping, '親indexのidentity/重複')
        mapping[key] = entry
    require(len(mapping) == 1671 * 9 and len(delta) == 9, 'index coverage不一致')
    replacement = {}
    for entry in delta:
        key = entry['species_id'], entry['consumer']
        require(key[0] == SID and key[1] in b.CONSUMERS and key not in replacement
                and entry['species_key'] == KEY and entry['status'] == 'PAYLOAD_PREPARED_NOT_INSTALLED',
                '差分の対象拡張/重複禁止')
        before = mapping[key]
        require(before['status'] == 'BLOCKED_SOURCE_ADOPTION' and before['payload'] is None
                and before['policy'] == 'GIFT_LEARNSET_ADOPTION_REQUIRED' and before['species_key'] == KEY,
                '受入親の未裁定枠以外を上書きしない')
        replacement[key] = entry
    return [copy.deepcopy(replacement.get((e['species_id'], e['consumer']), e)) for e in parent]


@dataclass(frozen=True)
class PayloadOwner:
    species_id: int
    consumer: str
    action: str
    arena: str | None = None
    payload: dict | None = None
    archive: dict | None = None
    preserve_existing_moves: bool = True


def resolve_owner(entry: dict, species_id: int, consumer: str) -> PayloadOwner:
    """空表やbase種へのfallbackと、非学習identity/条件consumerを区別する。"""
    require(type(species_id) is int and 0 <= species_id < 1671 and consumer in b.CONSUMERS,
            'owner queryの範囲/型不正')
    require(entry['species_id'] == species_id and entry['consumer'] == consumer, 'owner query不一致')
    status = entry['status']
    if status == 'IDENTITY_ONLY_NO_REPLACEMENT':
        identity = entry['identity']
        require(entry['payload'] is None and identity['species_id'] == species_id
                and identity['species_key'] == entry['species_key'] and identity['policy'] in b.NONPERMANENT
                and identity['preserve_identity'] is True and identity['preserve_current_moves'] is True
                and identity['automatic_fallback'] is False, '非学習identityの保全契約不一致')
        return PayloadOwner(species_id, consumer, identity['policy'])
    require(status == 'PAYLOAD_PREPARED_NOT_INSTALLED', '未裁定/未知ownerのfallback禁止')
    if consumer in ('pre_evolution_carry', 'form_change'):
        require(entry['payload'] is None, '条件付き経路のflat table混入')
        return PayloadOwner(species_id, consumer, 'CONDITIONAL_CONSUMER_NOT_CONNECTED')
    require(isinstance(entry['payload'], dict), '学習ownerのpayload欠落')
    return PayloadOwner(species_id, consumer, 'EXPLICIT_OWNER_PAYLOAD_NOT_INSTALLED',
        'FLOETTE_DELTA' if species_id == SID else 'ACCEPTED_PARENT',
        copy.deepcopy(entry['payload']), copy.deepcopy(entry.get('archive')))


# C headerと同じ固定ABI。静的照合と全1671x9 queryのC実行で検証する。
OWNER_POLICIES = {
    'EXPLICIT_OWNER_PAYLOAD_NOT_INSTALLED': 1,
    'INTERNAL_IDENTITY_ONLY': 2,
    'EXCLUDED_REMAKE_FORM_IDENTITY_ONLY': 3,
    'NON_BATTLING_FORM_IDENTITY_ONLY': 4,
    'BATTLE_COPY_CARRY_ONLY': 5,
    'BATTLE_FORM_CARRY_ONLY': 6,
    'P04_MEGA_CARRY_ONLY': 7,
}


def owner_policies(indexes: list[dict]) -> bytes:
    policies = {}
    seen = set()
    for entry in indexes:
        sid, family = entry['species_id'], entry['consumer']
        require((sid, family) not in seen, 'owner policy重複')
        seen.add((sid, family))
        action = resolve_owner(entry, sid, family).action
        policy = 1 if action == 'CONDITIONAL_CONSUMER_NOT_CONNECTED' else OWNER_POLICIES[action]
        require(policies.get(sid, policy) == policy, '同種のconsumer間owner policy衝突')
        policies[sid] = policy
    require(len(seen) == 1671 * 9 and set(policies) == set(range(1671)), 'owner全species/consumer coverage')
    require(Counter(policies.values()) == {1: 1483, 2: 21, 3: 7, 4: 3, 5: 6, 6: 102, 7: 49},
            '受入188非学習/戦闘姿のpolicyを変更しない')
    return bytes(policies[sid] for sid in range(1671))


def build(root: Path, source: Path, parent: Path, destination: Path) -> dict:
    root, source, parent = Path(root).resolve(), Path(source), Path(parent)
    destination = ensure_output(root, Path(destination))
    require(not destination.exists(), '新規.local出力先が必要')
    decision = s.read_json(root / DECISION); check_decision(decision)
    s.bound(source / 'receipt.json', decision['source_receipt'])
    receipt = s.read_json(source / 'receipt.json')
    require(receipt['files'] == decision['source_files'] and receipt['archive'] == decision['archive']
            and receipt['run_id'] == decision['source_run']['id'], '原本採取receipt不一致')
    for name, ident in decision['source_files'].items(): s.bound(source / name, ident)
    for name, ident in decision['repository_sources'].items(): s.bound(root / name, ident)
    checkpoint = s.read_json(root / decision['parent_checkpoint'])
    require(checkpoint['status'] == 'ACCEPTED_BINDING_PAYLOADS_ONLY_ROM_PENDING'
            and checkpoint['actions_completion_confirmed'] is True
            and checkpoint['run_id'] == 35659593954, '受入済み親payloadを指定する')
    s.bound(parent / 'receipt.json', checkpoint['proof_bindings']['receipt.json'])
    for name, ident in checkpoint['summary']['files'].items(): s.bound(parent / name, ident)
    moves = s.manifest(root / 'manifests/move_ids.csv', 'move_key')
    catalogs = s.read_json(parent / 'catalogs.json')
    reference, target = s.read_json(source / 'reference.json'), s.read_json(source / 'target.json')
    crosswalk = {int(k): v for k, v in s.read_json(source / 'crosswalk.json').items()}
    rows = adopt(reference, target, crosswalk, s.read_json(root / p.CONTRACT_PATHS['gift']), decision, moves, catalogs)
    files, delta = prepare_delta(rows, catalogs, moves)
    original = list(s.rows(parent / 'consumer-index.jsonl'))
    combined = compose_index(original, delta)
    counts = Counter(resolve_owner(e, e['species_id'], e['consumer']).action for e in combined)
    require(sum(counts[x] for x in b.NONPERMANENT) == 188 * 9, '188枠の保全coverage不一致')
    files['owner-policies.bin'] = owner_policies(combined)
    files['floette-routes.jsonl'] = b''.join(s.encode(r) for r in rows)
    files['consumer-index.jsonl'] = b''.join(s.encode(e) for e in combined)
    files['floette-index.jsonl'] = b''.join(s.encode(e) for e in delta)
    files['owner_approved_overlay.json'] = s.encode({'rows': []})
    report = {'phase': PHASE, 'status': 'FLOETTE_ADOPTED_PAYLOAD_PREPARED_RUNTIME_OPEN',
        'decision': s.identity(root / DECISION), 'source_receipt': decision['source_receipt'],
        'parent_receipt': checkpoint['proof_bindings']['receipt.json'], 'parent_run_id': checkpoint['run_id'],
        'source_reference_routes': len(rows), 'consumer_counts': dict(Counter(r['consumer'] for r in rows)),
        'parent_routes_preserved': 128352, 'total_accounted_routes': 128389,
        'parent_payloads_modified': 0, 'parent_payloads_regenerated': 0,
        'source_official_records_regenerated': 0, 'source_vega_records_regenerated': 0,
        'index_entries_changed': 9, 'identity_only_species_preserved': 188,
        'owner_dispatch_counts': dict(sorted(counts.items())), 'owner_policy_records': 1671, 'unresolved_source_adoption_species': [],
        'gift_contract_preserved': True, 'saved_four_moves_rewritten': False, 'automatic_fallback': False,
        'side_change_routes': 0, 'temporary_placeholders': 0, 'owner_overlay_routes': 0,
        'conditional_runtime_connected': False, 'physical_supply_verified': False,
        'install_ready': False, 'runtime_applied': False, 'rom_changes': 0, 'native_runs': 0,
        'issue19_complete': False, 'release_ready': False,
        'storage_arenas': {'ACCEPTED_PARENT': checkpoint['payload_artifact']['id'], 'FLOETTE_DELTA': 'this artifact'},
        'files': {name: {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in sorted(files.items())}}
    destination.mkdir(parents=True)
    for name, raw in files.items(): (destination / name).write_bytes(raw)
    (destination / 'receipt.json').write_bytes(s.encode(report))
    return report
