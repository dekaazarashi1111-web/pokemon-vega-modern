#!/usr/bin/env python3
"""Berryの現Task→MultiBoot引数を有限解釈する。BIOS payload readerとは区別する。"""
from __future__ import annotations

import hashlib
import json
import struct

import pr16_berry_origin as parent

BASE, START, END, HIT = 0x08000000, parent.START, parent.END, parent.HIT
STACK, STOP = (0x03007800, 0x03007F00), 0x01000000
RAM_NAMES = {'gTasks', 'gMultibootStart', 'gMultibootSize', 'gMultibootStatus', 'gMultibootParam'}
CODE_NAMES = {'Task_BerryFixMain', 'MultiBootInit', 'MultiBootStartMaster', 'MultiBootMain',
              'MultiBootCheckComplete', 'MultiBoot', 'SetScene'}
FIELDS = ('size', 'probe_count', 'client_data', 'palette_data', 'response_bit', 'client_bit',
          'boot_srcp', 'boot_endp', 'masterp', 'sendflag', 'probe_target_bit', 'check_wait',
          'server_type', 'task_size', 'task_data')
EXPECTED_LAYOUT = dict(zip(FIELDS, (76, 24, 25, 28, 29, 30, 32, 36, 40, 72, 73, 74, 75, 40, 8)))
CLAIMS = {'conditional_actual_thumb_interpretation': True, 'native_processes': 0,
          'actual_bios_cpu_executed': False, 'serial_transfer_observed': False,
          'child_program_executed': False, 'natural_task_entry_proven': False,
          'target_actual_reader_proven': False, 'formal_classification_changes': 0,
          'donor_safe_bytes': 0, 'retirement_or_transfer_complete': False}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def interval(start, end, header=192):
    """sourceのlabel extentとABIの16byte切上げextentを混ぜない。"""
    need(all(type(n) is int for n in (start, end, header)), '範囲は厳密な整数')
    need(BASE <= start < end <= 0x0A000000 and start % 4 == 0 and header == 192, 'ROM/header整列')
    length = end - start - header
    rounded = (length + 15) & ~15
    need(0 < length and 256 <= rounded <= 262144, '有限MultiBoot payload長')
    payload = start + header
    need(payload + rounded <= 0x0A000000, 'ROM上限を越える転送extent')
    return {'asset_start': start, 'label_end_exclusive': end, 'header_size': header,
            'payload_start': payload, 'payload_size': length, 'rounded_payload_size': rounded,
            'transfer_end_exclusive': payload + rounded, 'tail_beyond_label_bytes': rounded - length,
            'rounded_tail_reader_proven': False}


def layout_checked(layout):
    need(type(layout) is dict and set(layout) == set(FIELDS), '閉layout schema')
    need(all(type(v) is int for v in layout.values()) and layout == EXPECTED_LAYOUT, 'ARM固定header ABI')
    return dict(layout)


def parse_symbols(raw):
    """必要なROM/RAM名だけ束縛。近傍symbolを命令/owner証明として採用しない。"""
    wanted, found, addresses = RAM_NAMES | CODE_NAMES, {}, set()
    for line, text in enumerate(raw.decode().splitlines(), 1):
        cells = text.split('\t')
        if len(cells) != 8:
            continue
        try:
            address = int(cells[1], 16)
        except ValueError:
            continue
        if BASE <= address < 0x0A000000:
            addresses.add(address & ~1)
        if cells[4] not in wanted:
            continue
        name = cells[4]
        need(name not in found, '必要symbol重複: ' + name)
        valid = 0x02000000 <= address < 0x02040000 or 0x03000000 <= address < 0x03008000
        need(valid if name in RAM_NAMES else BASE <= address < 0x0A000000, 'symbol領域: ' + name)
        found[name] = {'address': address, 'line': line, 'row_sha256': identity(text.encode())['sha256']}
    need(set(found) == wanted, '必要symbol不足: ' + ','.join(sorted(wanted - set(found))))
    for name in CODE_NAMES:
        start = found[name]['address'] & ~1
        end = min((a for a in addresses if a > start), default=start)
        need(start % 2 == 0 and 0 < end - start <= 2048, '有限code extent: ' + name)
        found[name]['end_exclusive'] = end
    need(all(found[n]['address'] % 4 == 0 for n in RAM_NAMES), 'global整列')
    return found


def public_profile(machine, label, result, extra=None):
    payload_reads = [dict(v) for (a, n), v in machine.reads.items()
                     if a < END + 4 and START < a + n]
    touched = {a for row in payload_reads for a in range(row['address'], row['address'] + row['size'])}
    # 引数準備の成功から実readerを先取りしない。
    need(not touched, 'このscopeはpayload readを受入対象にしていない')
    return {'id': label, 'result': result, 'instruction_count': len(machine.trace),
            'trace': machine.trace, 'calls': machine.calls, 'edges': machine.edges,
            'rom_reads': sorted(machine.reads.values(), key=lambda v: (v['address'], v['size'])),
            'writes': [{'address': w['address'], 'size': w['size']} for w in machine.writes],
            'payload_reads': payload_reads, 'target_bytes_read': 0, 'claims': dict(CLAIMS),
            **(extra or {})}


class Boundary(Exception):
    def __init__(self, address):
        self.address = address


def pause(machine, address):
    raise Boundary(address)


def measure(raw, symbols, layout, saved):
    """実候補の新Task/転送引数scopeだけを走らせ、旧測定/旧試験は呼ばない。"""
    import pr16_dex_hof_runtime_sprite as thumb
    layout = layout_checked(layout)
    need(identity(raw) == parent.CANDIDATE, 'exact candidate全SHA')
    need(identity(parent.section(raw, BASE, HIT, 4)) == parent.HIT_ID, '継承対象4byte')
    span = interval(START, END)
    for name, previous in saved['consumer_frontier'].items():
        if name not in symbols:
            continue
        start, end = previous['region_start'], previous['region_end_exclusive']
        need((symbols[name]['address'] & ~1) == start and
             identity(parent.section(raw, BASE, start, end - start)) == previous['region_identity'],
             '保存consumer全hash継承: ' + name)
    s = {n: value['address'] & (~1 if n in CODE_NAMES else -1) for n, value in symbols.items()}
    code = tuple((s[n], symbols[n]['end_exclusive']) for n in CODE_NAMES if n != 'SetScene')
    stub_start, stub_end = s['MultiBoot'], symbols['MultiBoot']['end_exclusive']
    need(0 < stub_end - stub_start <= 32, '有限BIOS veneer')
    swi = [a for a in range(stub_start, stub_end - 1, 2)
           if int.from_bytes(parent.section(raw, BASE, a, 2), 'little') == 0xDF25]
    need(len(swi) == 1 and parent.section(raw, BASE, swi[0] + 2, 2) == b'\x70\x47', '実SWI25/BX veneer')
    mp, task = s['gMultibootParam'], s['gTasks']
    globals_ = tuple((s[n], s[n] + 4) for n in RAM_NAMES - {'gTasks', 'gMultibootParam'})
    ram = ((mp, mp + layout['size']), (task, task + layout['task_size']), *globals_)
    need(all(a[1] <= b[0] or b[1] <= a[0] for i, a in enumerate(ram) for b in ram[i + 1:]), 'fixture非alias')
    writes = (STACK, *ram, (0x04000120, 0x04000130), (0x04000134, 0x04000136))
    allowed_rom = (*code, (START, span['transfer_end_exclusive']))

    class Machine(thumb.Machine):
        def read(self, address, size):
            if type(address) is int and BASE <= address < BASE + len(self.raw):
                need(any(lo <= address and address + size <= hi for lo, hi in allowed_rom), '限定ROM read')
            return super().read(address, size)

    def fresh():
        machine = Machine(raw, code, writes, {s['SetScene']: pause, swi[0]: pause})
        for lo, hi in ram:
            for address in range(lo, hi):
                machine.seed(address, 1, 0)
        for address in range(0x04000120, 0x04000130, 2):
            machine.seed(address, 2, 0xFFFF)
        machine.seed(0x04000128, 2, 8)
        machine.seed(0x04000134, 2, 0)
        machine.seed(s['gMultibootStart'], 4, START)
        machine.seed(s['gMultibootSize'], 4, END - START)
        machine.seed(mp + layout['masterp'], 4, START)
        return machine

    def seedfield(machine, name, value, size=1):
        machine.seed(mp + layout[name], size, value)

    def readfield(machine, name, size=1):
        return machine.read(mp + layout[name], size)

    def drive(machine, entry, allow_scene=False, stop_at_main=False):
        pc, events = entry, []
        frame = machine.r[4:12] + [machine.r[13]]
        if stop_at_main:
            machine.hooks[s['MultiBootMain']] = pause
        while True:
            need(len(machine.trace) < 1600 and len(events) < 4, '有限命令/外部境界予算')
            try:
                machine.run(pc, STOP, limit=1601 - len(machine.trace))
                need(machine.r[4:12] + [machine.r[13]] == frame, '実帰還callee-saved/SP')
                return 'RETURNED', events
            except Boundary as boundary:
                address = boundary.address
                if address == s['SetScene']:
                    need(allow_scene and not events and machine.r[0] == 2 and
                         machine.calls[-1]['target'] == address, 'SetScene(2)同期ABI条件')
                    events.append({'boundary': 'SetScene', 'scene': 2, 'actual_graphics_executed': False})
                    pc = machine.r[14] & ~1
                    machine.r[:4] = [thumb.UndefinedCallerRegister('scene r' + str(i)) for i in range(4)]
                    machine.r[12] = thumb.UndefinedCallerRegister('scene r12')
                    machine.flags = [thumb.UndefinedCallerRegister('scene NZCV')] * 4
                elif address == swi[0]:
                    need(machine.calls[-1]['target'] == s['MultiBoot'] and machine.r[:2] == [mp, 1],
                         '実MultiBoot call→SWI25 r0/r1')
                    events.append({'boundary': 'SWI25_BEFORE_BIOS', 'address': address,
                                   'parameter_address': mp, 'mode': 1})
                    return 'STOP_BEFORE_BIOS', events
                elif stop_at_main and address == s['MultiBootMain']:
                    need(machine.calls[-1]['target'] == address and machine.r[0] == mp, '実wait側call')
                    return 'STOP_BEFORE_MULTIBOOT_MAIN', events
                else:
                    raise ValueError('未契約の実call')

    profiles = []
    machine = fresh()
    machine.r[0] = 0
    machine.seed(task + layout['task_data'], 2, 4)
    result, events = drive(machine, s['Task_BerryFixMain'])
    need(result == 'RETURNED' and machine.read(s['gMultibootStart'], 4) == START and
         machine.read(s['gMultibootSize'], 4) == END - START and readfield(machine, 'masterp', 4) == START,
         '実Taskのstart/size/masterp書込')
    need(machine.read(task + layout['task_data'], 2) == 5 and readfield(machine, 'check_wait') == 15 and
         any(call['target'] == s['MultiBootInit'] for call in machine.calls), '実Task→Init→state5')
    profiles.append(public_profile(machine, 'task-init', result, {'events': events}))

    for timer in (179, 180):
        machine = fresh()
        machine.r[0] = 0
        machine.seed(task + layout['task_data'], 2, 5)
        machine.seed(task + layout['task_data'] + 2, 2, timer)
        seedfield(machine, 'client_bit', 2)
        seedfield(machine, 'response_bit', 2)
        result, events = drive(machine, s['Task_BerryFixMain'], allow_scene=True, stop_at_main=(timer == 179))
        if timer == 180:
            need(result == 'RETURNED' and readfield(machine, 'boot_srcp', 4) == span['payload_start'] and
                 readfield(machine, 'boot_endp', 4) == span['transfer_end_exclusive'] and
                 readfield(machine, 'probe_count') == 0xD0 and
                 machine.read(task + layout['task_data'], 2) == 6 and
                 machine.read(task + layout['task_data'] + 2, 2) == 0,
                 '実Task→StartMaster→整列extent/state6')
        else:
            need(result == 'STOP_BEFORE_MULTIBOOT_MAIN' and
                 machine.read(task + layout['task_data'] + 2, 2) == 180 and
                 not any(call['target'] == s['MultiBootStartMaster'] for call in machine.calls), '180境界で未転送')
        profiles.append(public_profile(machine, 'task-timer-' + str(timer), result, {'events': events}))

    cases = [('actual-length', 0, 2, 0, span['payload_size'], True),
             ('busy-probe', 1, 2, 0, span['payload_size'], False),
             ('no-client', 0, 0, 0, span['payload_size'], False),
             ('connection-wait', 0, 2, 1, span['payload_size'], False),
             ('too-small', 0, 2, 0, 240, False), ('minimum-rounded', 0, 2, 0, 241, True),
             ('maximum', 0, 2, 0, 262144, True), ('too-large', 0, 2, 0, 262145, False)]
    for label, probe, clients, wait, length, accepted in cases:
        machine = fresh()
        seedfield(machine, 'probe_count', probe)
        seedfield(machine, 'client_bit', clients)
        seedfield(machine, 'check_wait', wait)
        machine.r[:4] = [mp, span['payload_start'], length, 4]
        machine.seed(machine.r[13], 4, 1)
        result, events = drive(machine, s['MultiBootStartMaster'])
        need(result == 'RETURNED', 'StartMasterの実帰還')
        if accepted:
            need(readfield(machine, 'boot_srcp', 4) == span['payload_start'] and
                 readfield(machine, 'boot_endp', 4) == span['payload_start'] + ((length + 15) & ~15) and
                 readfield(machine, 'probe_count') == 0xD0 and readfield(machine, 'palette_data') == 0xC1,
                 '実転送引数とpalette')
        else:
            need(readfield(machine, 'probe_count') == 0 and readfield(machine, 'client_bit') == 0 and
                 readfield(machine, 'check_wait') == 15 and readfield(machine, 'boot_endp', 4) == 0,
                 '異常条件を実Initで拒否')
        profiles.append(public_profile(machine, 'start-' + label, result, {'arguments_accepted': accepted,
                                       'payload_length_argument': length, 'events': events}))

    for ready in (True, False):
        machine = fresh()
        seedfield(machine, 'probe_count', 0xD1)
        seedfield(machine, 'client_bit', 2)
        seedfield(machine, 'probe_target_bit', 2)
        seedfield(machine, 'boot_srcp', span['payload_start'], 4)
        seedfield(machine, 'boot_endp', span['transfer_end_exclusive'], 4)
        machine.seed(0x04000122, 2, 0x7302 if ready else 0x7202)
        machine.r[0] = mp
        result, events = drive(machine, s['MultiBootMain'])
        need(result == ('STOP_BEFORE_BIOS' if ready else 'RETURNED'), '実client-ready境界')
        if not ready:
            need(machine.r[0] == 0x60 and readfield(machine, 'client_bit') == 0 and
                 not any(call['target'] == s['MultiBoot'] for call in machine.calls), '未readyはBIOSを呼ばず拒否')
        profiles.append(public_profile(machine, 'main-ready-' + str(ready).lower(), result, {'events': events}))
    need(len(profiles) == 13 and all(p['target_bytes_read'] == 0 for p in profiles), '有限13profile会計')
    return {'schema_version': 1, 'status': 'PASS_ACTUAL_TASK_TO_BIOS_BOUNDARY_READER_PENDING',
            'candidate': parent.CANDIDATE, 'origin': {'address': HIT, **parent.HIT_ID},
            'transfer_interval': span, 'layout': layout, 'symbols': symbols, 'profiles': profiles,
            'profile_count': len(profiles), 'claims': dict(CLAIMS),
            'current_task_payload_binding_proven': True, 'formal_classified': 788,
            'formal_unclassified': 86, 'selected_unknown_origins': 7,
            'conditions_ja': ['Task ID0のstate4/5・timer179/180、非alias global/stackを直接fixtureとする。自然画面到達ではない。',
                'SetScene(2)だけは同期ABIの不透明callee。caller-saved/NZCVを未定義化し描画成功は主張しない。',
                'MultiBootMainのclient-ready serial値は入力fixture。実リンク相手や転送成功ではない。',
                '実SWI25の直前で停止する。BIOS本体・4byte payload read・子機instruction fetchは未証明。',
                '16byte切上げでlabel外4byteが転送要求に含まれるが、その読取/ownerは受入しない。']}
