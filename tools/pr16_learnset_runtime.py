"""受入済みbinaryを再生成せず、明示owner付きのROM配置imageへ結合する。

v1の接続範囲はGetLevelUpMovesBySpecies/CanMonLearnTMHMの2入口だけ。
自然level-up/初期技/進化/孵化/姿/共有/思い出し/追加archiveは別境界。
"""
from __future__ import annotations
import json
from pathlib import Path
import struct
from tools import pr16_learnset_successor as source

COUNT = 1671
HEADER = struct.Struct('<4sHHIIIIII')
ENTRY = struct.Struct('<IHH')
CONSUMERS = ('level_up', 'machine')
NONE = 0xFFFFFFFF
BASE = 'content/modernization/'
PARENT = BASE + 'pr16_learnset_payload_checkpoint.json'
FLOETTE = BASE + 'pr16_learnset_floette_checkpoint.json'
ALLOCATION = BASE + 'pr16_circus_getter_followup.json'
OWNER_COUNT = 1483


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def aligned(n: int) -> int:
    return (n + 3) & ~3


def accepted_files(root: Path, directory: Path, checkpoint: str) -> dict:
    cp = source.read_json(root / checkpoint)
    need(cp['runtime_applied'] is False and cp['release_ready'] is False,
         '受入親のscopeが変化')
    files = dict(cp['summary']['files'], **{'receipt.json': cp['proof_bindings']['receipt.json']})
    need({p.name for p in directory.iterdir()} == set(files), '受入member集合が不一致')
    for name, binding in files.items():
        source.bound(directory / name, binding)
    return cp


def compose(root: Path, parent: Path, floette: Path) -> tuple[bytes, dict]:
    """原本抽出/採用/packingは行わない。コピー元・コピー先をreceiptへ残す。"""
    cp = accepted_files(root, parent, PARENT)
    fc = accepted_files(root, floette, FLOETTE)
    need(fc['summary']['identity_only_species_preserved'] == 188, '保全枠が変化')
    policies = (floette / 'owner-policies.bin').read_bytes()
    need(len(policies) == COUNT and policies.count(1) == OWNER_COUNT
         and all(1 <= n <= 7 for n in policies), 'owner policy不正')
    rows = list(source.rows(floette / 'consumer-index.jsonl'))
    need(len(rows) == COUNT * 9, 'index件数不正')
    index = {(r['species_id'], r['consumer']): r for r in rows}
    need(len(index) == len(rows), 'index重複')
    policy_at = HEADER.size
    index_at = aligned(policy_at + COUNT)
    level_at = index_at + COUNT * ENTRY.size
    level_parent = (parent / 'level_up.bin').read_bytes()
    level_delta = (floette / 'floette.level_up.bin').read_bytes()
    machine_parent = (parent / 'machine.bin').read_bytes()
    machine_delta = (floette / 'floette.machine.bin').read_bytes()
    machine_at = aligned(level_at + len(level_parent) + len(level_delta))
    total = machine_at + len(machine_parent) + len(machine_delta)
    need(len(machine_parent) == 1482 * 16 and len(machine_delta) == 16, 'machine pool容量違反')
    image = bytearray(total)
    image[:HEADER.size] = HEADER.pack(b'PLR1', 1, COUNT, policy_at, index_at,
                                      level_at, machine_at, total, 0)
    image[policy_at:policy_at + COUNT] = policies
    copies = []
    for arena, directory, filename, dest in (
        ('ACCEPTED_PARENT', parent, 'level_up.bin', level_at),
        ('FLOETTE_DELTA', floette, 'floette.level_up.bin', level_at + len(level_parent)),
        ('ACCEPTED_PARENT', parent, 'machine.bin', machine_at),
        ('FLOETTE_DELTA', floette, 'floette.machine.bin', machine_at + len(machine_parent))):
        data = (directory / filename).read_bytes()
        image[dest:dest + len(data)] = data
        copies.append({'arena': arena, 'file': filename, 'image_offset': dest,
                       **source.identity(directory / filename)})
    owners = []
    for sid, policy in enumerate(policies):
        level = index[(sid, 'level_up')]
        machine = index[(sid, 'machine')]
        if policy != 1:
            need(all(r['status'] == 'IDENTITY_ONLY_NO_REPLACEMENT' and r['payload'] is None
                     for r in (level, machine)), '188枠へのpayload/fallback禁止')
            entry = (NONE, 0, 0xFFFF)
        else:
            directory = floette if sid == 1029 else parent
            prefix = 'floette.' if sid == 1029 else ''
            need(all(r['status'] == 'PAYLOAD_PREPARED_NOT_INSTALLED' for r in (level, machine)), '未採用owner')
            lp, mp = level['payload'], machine['payload']
            need(lp['file'] == prefix + 'level_up.bin' and mp['file'] == prefix + 'machine.bin', 'arena/consumer混同')
            for span in (lp, mp):
                size = (directory / span['file']).stat().st_size
                need(type(span['offset']) is int and type(span['size']) is int
                     and 0 <= span['offset'] <= size and 0 <= span['size'] <= size - span['offset'], 'span範囲不正')
            data = (directory / lp['file']).read_bytes()[lp['offset']:lp['offset'] + lp['size']]
            need(len(data) >= 3 and len(data) % 3 == 0 and data[-3:] == b'\0\0\xff', 'level終端/stride違反')
            pairs = list(struct.iter_unpack('<HB', data[:-3]))
            need(len(pairs) <= 40 and all(1 <= move <= 1062 and 1 <= lv <= 100 for move, lv in pairs), 'level buffer/Side Change/進化時平坦化違反')
            need(mp['size'] == 16 and mp['offset'] % 16 == 0, 'machine stride違反')
            level_pos = level_at + (len(level_parent) if sid == 1029 else 0) + lp['offset']
            machine_pos = (len(machine_parent) if sid == 1029 else 0) + mp['offset']
            entry = (level_pos, len(pairs), machine_pos // 16)
            owners.append({'species_id': sid, 'level_count': len(pairs), 'level_offset': level_pos,
                           'machine_offset': machine_at + machine_pos})
        ENTRY.pack_into(image, index_at + sid * ENTRY.size, *entry)
    receipt = {'schema_version': 1, 'format': 'PLR1', 'species_count': COUNT,
               'learning_owners': len(owners), 'identity_only_preserved': 188,
               'max_level_rows': max(x['level_count'] for x in owners),
               'copies': copies, 'size': total, 'header_size': HEADER.size, 'entry_size': ENTRY.size,
               'policy_offset': policy_at, 'index_offset': index_at,
               'level_offset': level_at, 'machine_offset': machine_at,
               'parent_run': cp['run_id'], 'floette_run': fc['run_id'],
               'entrypoints_in_scope': ['GetLevelUpMovesBySpecies', 'CanMonLearnTMHM'],
               'not_connected': ['GiveBoxMonInitialMoveset', 'MonTryLearningNewMove',
                   'evolution', 'reminder', 'egg', 'shared_egg', 'pre_evolution_carry', 'form_change', 'tutor', 'archive_supply'],
               'archive_moves_granted': 0, 'accepted_payload_regenerations': 0,
               'accepted_source_regenerations': 0, 'global_table_roots_changed': False,
               'existing_moves_rewritten': False, 'runtime_applied': False,
               'issue19_complete': False, 'release_ready': False}
    return bytes(image), receipt


def free_span(allocation: dict, size: int) -> tuple[int, str]:
    """既存allocationを再利用/破棄しない。declared free範囲だけを選ぶ。"""
    need(type(size) is int and size > 0, '配置size不正')
    occupied = sorted(allocation['allocations'], key=lambda row: row['start'])
    for region in allocation['regions']:
        if region['kind'] != 'allocatable':
            continue
        cursor = aligned(region['start'])
        rows = [a for a in occupied if a['region'] == region['name']]
        for row in rows:
            need(region['start'] <= row['start'] < row['end_exclusive'] <= region['end_exclusive'], 'allocation範囲不正')
            if cursor + size <= row['start']:
                return cursor, region['name']
            cursor = max(cursor, aligned(row['end_exclusive']))
        if cursor + size <= region['end_exclusive']:
            return cursor, region['name']
    raise ValueError('既存ownerを侵害しない連続空間が不足')


def build(root: Path, parent: Path, floette: Path, output: Path) -> dict:
    need(not output.exists(), '検証出力の上書き/重複生成禁止')
    image, receipt = compose(root, parent, floette)
    allocation = source.read_json(root / ALLOCATION)['build']['allocation']
    # 追加ARM code用に8KiBを予約。全9consumerが収まったとはみなさない。
    start, region = free_span(allocation, aligned(len(image)) + 8192)
    output.mkdir(parents=True)
    (output / 'runtime-image.bin').write_bytes(image)
    receipt.update(image=source.identity(output / 'runtime-image.bin'),
                   planned_rom_offset=start, planned_region=region, code_reserve=8192,
                   allocation_input=source.identity(root / ALLOCATION))
    (output / 'receipt.json').write_bytes(source.encode(receipt))
    return receipt
