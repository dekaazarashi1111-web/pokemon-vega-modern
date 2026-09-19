#!/usr/bin/env python3
"""検証済みfcdaの交換2経路だけを修正する。native受入は別の証拠で行う。"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_bp_exchange_successor.py'
OUT = ROOT / '.local/pr16-bp-exchange-successor'
BASE = 0x08000000
SIZE = 33554432
PARENT_SHA = 'fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879'
OFFSETS = (0x12CF729, 0x12CF775)
BEFORE, AFTER = bytes.fromhex('2f00'), bytes.fromhex('2900')
RUNTIME_SOURCE = 'overlays/facility_runtime/facility_runtime.c'
RUNTIME_SHA = '28603b55a0573dd376e1acdc4310591c017d158c69ade92393020781271e7cb0'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def replace_operands(raw, offsets=OFFSETS):
    """2個のu16 operand以外を完全に保持し、部分一致や再適用は拒否する。"""
    need(type(raw) is bytes, 'immutable bytes required')
    need(type(offsets) is tuple and len(offsets) == 2
         and all(type(x) is int for x in offsets)
         and 0 <= offsets[0] < offsets[0]+2 <= offsets[1]
         and offsets[1]+2 <= len(raw), 'two ordered nonoverlapping operands required')
    need(all(raw[x:x+2] == BEFORE for x in offsets), 'both exchange preimages required')
    left, right = offsets
    result = raw[:left]+AFTER+raw[left+2:right]+AFTER+raw[right+2:]
    need(len(result) == len(raw) and result[:left] == raw[:left]
         and result[left+2:right] == raw[left+2:right]
         and result[right+2:] == raw[right+2:], 'undeclared ROM change')
    return result


def binding(raw):
    need(identity(raw) == dict(size=SIZE, sha256=PARENT_SHA), 'exact fcda parent required')
    def word(address):
        return struct.unpack_from('<I', raw, address-BASE)[0]
    need(word(0x08163068+0x2F*4) == 0x080CBF8D
         and raw[0xCBF8C:0xCBF8E] == bytes.fromhex('7047'), 'null special binding differs')
    need(word(0x08163068+0x29*4) == 0x080A160D
         and raw[0xA160C:0xA1628] == bytes.fromhex('00b5044904488860002086f0e3fb01bc004700003031000329160a08'), 'chooser wrapper differs')
    for offset, target in zip(OFFSETS, (0x092CF680, 0x092CF6BC)):
        expected = bytes.fromhex('252f0027237de92c0905')+struct.pack('<I', target)
        need(raw[offset-1:offset-1+len(expected)] == expected, 'exchange script boundary/consumer/next battle differs')
    for start, menu, skip in ((0x092CF710,0x092CF728,0x092CF738),(0x092CF75C,0x092CF774,0x092CF784)):
        expected = bytes.fromhex('2329e92c09210d8001000601')+struct.pack('<I',menu)+b'\x05'+struct.pack('<I',skip)
        need(raw[start-BASE:start-BASE+len(expected)] == expected, 'BeginExchange rooted branch differs')
    # 既存採取済みのowner byteを再利用し、今回の交換consumerだけを照合する。
    old = json.loads((ROOT/'content/modernization/pr16_bp_candidate_return_audit.json').read_bytes())
    owners = {}
    for name in ('script_native_092CE929','script_native_092CE97D','script_native_092CE8DD'):
        record = old['native_excerpts'][name]
        data = bytes.fromhex(record['hex'])
        need(identity(data) == dict(size=record['size'],sha256=record['sha256']), 'retained owner evidence corrupt')
        at = record['address']-BASE
        need(raw[at:at+len(data)] == data, 'exchange native owner changed')
        owners[name] = dict(address=record['address'], **identity(data))
    source = (ROOT/RUNTIME_SOURCE).read_bytes()
    need(identity(source)['sha256'] == RUNTIME_SHA, 'runtime source changed; rebind ABI')
    need(word(0x0807FC5C) == 0x09FF4681, 'accepted loss-return shim not retained')
    return dict(old_special=0x2F, replacement_special=0x29,
        chooser=0x080A160D, initializer=0x08127DE0,
        begin_exchange=0x092CE929, commit_exchange=0x092CE97D, skip_exchange=0x092CE8DD,
        selection_address=0x0203C6C8, selection_encoding='ONE_BASED_PARTY_SLOT_ZERO_IS_CANCEL',
        single_selection_count=1, valid_slots=[1,2,3], selection_is_special_result=False,
        owner_evidence=owners, runtime_source=identity(source),
        native_exchange_accepted=False)


def allocations(parent, candidate, original):
    plan = copy.deepcopy(original)
    need(plan['summaries']['overlap_count'] == 0, 'parent allocation overlap')
    owners = []
    for index,row in enumerate(plan['allocations']):
        a,b = row['start'],row['end_exclusive']
        need(row['sequence'] == index and 0 <= a < b <= len(parent)
             and b-a == row['size'], 'allocation bounds/order')
        need(identity(parent[a:b])['sha256'] == row['content_sha256'], 'parent allocation identity differs')
        covered = [x for x in OFFSETS if a <= x and x+2 <= b]
        if covered:
            need(len(covered) == 2, 'exchange operands must share one owner')
            owners.append(row['name'])
            row['content_sha256'] = identity(candidate[a:b])['sha256']
        else:
            need(parent[a:b] == candidate[a:b], 'nonowner allocation changed')
    need(len(owners) == 1, 'exactly one allocation owner required')
    return plan,owners[0]


def build(parent, original):
    bound = binding(parent)
    raw = replace_operands(parent)
    plan,owner = allocations(parent, raw, original)
    return raw,dict(schema_version=1,status='PASS_EXCHANGE_ABI_REPAIR_NOT_NATIVE_ACCEPTANCE',
        parent=identity(parent),candidate=identity(raw),crc32=f'{zlib.crc32(raw)&0xffffffff:08X}',
        allocation=plan,binding=bound,owner=owner,
        changes=[dict(offset=x,address=BASE+x,size=2,before=BEFORE.hex(),after=AFTER.hex(),changed_bytes=1) for x in OFFSETS],
        actual_changed_bytes=2,undeclared_changed_bytes=0,new_allocations=0,
        global_special_table_changes=0,save_layout_changes=0,runtime_code_changes=0,
        accepted_native_cases_replayed=0,new_emulator_processes=0,
        native_exchange_accepted=False,native_bp_earning_accepted=False,
        p05_native_bp_gap_closed=False,release_ready=False,active_baseline_changed=False)


def run():
    sys.path[:0] = [str(ROOT/'scripts'),str(ROOT)]
    import pr16_bp_loss_return_successor as previous
    need(not any(p.is_symlink() for p in (OUT,*OUT.parents)), 'unsafe successor output')
    OUT.mkdir(parents=True,exist_ok=True)
    recipe = previous.run()
    parent = (previous.OUT/'candidate.gba').read_bytes()
    left,report = build(parent,recipe['allocation'])
    right,again = build(parent,recipe['allocation'])
    need(left == right and report == again, 'two bounded builds disagree')
    (OUT/'candidate.gba').write_bytes(left)
    report.update(independent_bounded_builds=2,
        clean_rom_dual_build_verified=False,
        sources={p:identity((ROOT/p).read_bytes()) for p in (SELF,previous.SELF,RUNTIME_SOURCE)})
    (OUT/'candidate.json').write_bytes(stable(report))
    need((previous.OUT/'candidate.gba').read_bytes() == parent, 'parent mutated')
    return report


if __name__ == '__main__':
    print(json.dumps(run(),ensure_ascii=False))
