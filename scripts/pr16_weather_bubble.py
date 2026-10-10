#!/usr/bin/env python3
"""Bubbles_InitVars→実sheet→LoadSpriteSheet→CpuSetの有限・条件付きreader。

旧consumerは呼ばず、純粋なThumb命令解釈器だけを再利用する。既受入runの再走ではない。
asset/命令/ROM/save byteは返さずaddress-size-SHAと公開source由来の契約を返す。
"""
from __future__ import annotations
import copy
import json
import struct
import pr16_dex_hof_runtime_sprite as thumb
import pr16_weather_bubble_sources as sources

need, identity = sources.need, sources.identity
BASE = 0x08000000
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
HIT, ASSET, SHEET = 0x0838B32F, 0x0838B304, 0x0838D5F4
ENTRY, LOAD, FOG = 0x0807D034, 0x08008258, 0x0807C060
ALLOC, REGISTER, CPU = 0x08006FB0, 0x08008424, 0x081C7A88
WEATHER_PTR, CREATED_OFFSET = 0x08389940, 0x72E
TAG = 0x1205
STACK, VRAM, STOP = (0x03007800, 0x03007F00), 0x06010000, 0x01000000
CODE = ((ENTRY, ENTRY + 0x54), (LOAD, LOAD + 0x44))
ROM_READS = (*CODE, (WEATHER_PTR, WEATHER_PTR + 4), (SHEET, SHEET + 8),
             (ASSET, ASSET + 64), (CPU, CPU + 4))
CLAIMS = dict(conditional_finite_reader_only=True, actual_runtime_execution_observed=False,
 actual_bios_cpu_executed=False, actual_screen_rendered=False, full_story_reachability_claimed=False,
 opaque_callee_effects_proven=False, universal_heap_or_irq_lifetime_proven=False,
 indirect_reference_completeness_claimed=False, donor_eligible=False, donor_leased=False,
 formal_rom_changed=False, formal_save_changed=False)
CONTRACT = dict(
 entry_ja='固定JP候補Bubbles_InitVarsの有限prefix。天候選択/task/自然story到達ではない。',
 weather_ja='実gWeatherPtrが非alias EWRAM Weatherを指し、FogHorizontal_InitVarsの正常同期ABI帰還がbubblesSpritesCreated(offset0x72E)を保存する条件。Fog本体とproducerは未証明。',
 allocation_ja='AllocSpriteTiles(2)の正常同期ABI帰還がtileStart0..1022の連続2tileを確保する条件。AllocSpriteTileRange(tag0x1205,start,2)が同epochを保存する条件。両helper実装/普遍heap/IRQは未証明。',
 copy_ja='実LoadSpriteSheetのLDR/BLが独立64byteをCpuSetへ渡す。実SWI0B/BX stubと16bit非fill32単位の仕様モデル。BIOS本体CPU実行ではない。',
 stop_ja='LoadSpriteSheetがBubbles_InitVarsへ帰還した直後まで。VRAMはモデル上の書込のみ、描画/残初期化/削除は未証明。')


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def exact(a, b):
    return canonical(a) == canonical(b)


def chunk(raw, address, size):
    need(type(raw) is bytes and type(address) is int and type(size) is int and size > 0 and
         BASE <= address <= BASE + len(raw) - size, 'ROM範囲')
    return raw[address - BASE:address - BASE + size]


def call_target(raw, pc):
    first, second = struct.unpack('<HH', chunk(raw, pc, 4))
    if first & 0xF800 != 0xF000 or second & 0xF800 != 0xF800:
        return None
    offset = (first & 2047) << 12 | (second & 2047) << 1
    if offset & (1 << 22):
        offset -= 1 << 23
    return pc + 4 + offset


def loader_return(raw):
    sites = [pc for pc in range(ENTRY, ENTRY + 0x50, 2) if call_target(raw, pc) == LOAD]
    need(len(sites) == 1, '候補窓内に唯一のLoadSpriteSheet BL。実到達は別途解釈')
    return sites[0] + 4


class Boundary(Exception):
    def __init__(self, pc):
        self.pc = pc


def pause(machine, pc):
    raise Boundary(pc)


class Machine(thumb.Machine):
    def __init__(self, raw, weather, tile_start, created):
        super().__init__(raw, CODE, (STACK, (VRAM, VRAM + 0x8000)),
                         {pc: pause for pc in (FOG, LOAD, ALLOC, REGISTER, CPU)})
        self.weather = weather
        self.ram_reads = []
        self.seed(weather + CREATED_OFFSET, 1, int(created))
        self.r[:4] = [thumb.UndefinedCallerRegister('entry r' + str(n)) for n in range(4)]
        self.flags = [thumb.UndefinedCallerRegister('entry NZCV')] * 4

    def read(self, address, size):
        need(type(address) is int and type(size) is int, 'read整数型')
        if BASE <= address < BASE + len(self.raw):
            need(any(lo <= address and address + size <= hi for lo, hi in ROM_READS), '限定ROM read以外を拒否')
        else:
            self.ram_reads.append((address, size))
        return super().read(address, size)


def opaque_return(machine, value=None, preserve_weather=False):
    """calleeの効果を実行したことにせず、呼出元保存領域だけを条件として残す。"""
    keep = {a for a in machine.mem if STACK[0] <= a < STACK[1] or VRAM <= a < VRAM + 0x8000}
    if preserve_weather:
        keep.add(machine.weather + CREATED_OFFSET)
    machine.mem = {a: v for a, v in machine.mem.items() if a in keep}
    machine.r[:4] = [thumb.UndefinedCallerRegister('caller-saved r' + str(n)) for n in range(4)]
    machine.r[12] = thumb.UndefinedCallerRegister('caller-saved r12')
    machine.flags = [thumb.UndefinedCallerRegister('caller-saved NZCV')] * 4
    if value is not None:
        machine.r[0] = value
    return machine.r[14] & ~1


def compose(raw, *, tile_start=7, created=False, invalidated=(), contract=None):
    need(type(tile_start) is int and (tile_start == -1 or 0 <= tile_start <= 1022), '2tile容量とs16失敗値')
    need(type(created) is bool, 'createdはboolのみ')
    need(type(invalidated) in (tuple, list) and not invalidated, '同期資源epochを失った経路は証明しない')
    need(contract is None or exact(contract, CONTRACT), '条件契約を変更しない')
    expected_sheet = struct.pack('<IHH', ASSET, 64, TAG)
    need(chunk(raw, SHEET, 8) == expected_sheet, '独立公開sheet data/size/tag全8byte')
    need(chunk(raw, CPU, 4) == b'\x0b\xdf\x70\x47', '実SWI0B/BX LR stub')
    weather = int.from_bytes(chunk(raw, WEATHER_PTR, 4), 'little')
    need(0x02000000 <= weather and weather % 4 == 0 and weather + 0x750 <= 0x02040000,
         '実Weather pointerのEWRAM非alias範囲')
    m = Machine(raw, weather, tile_start, created)
    target = STOP if created else loader_return(raw)
    pc, events, asset_reads = ENTRY, [], []
    loader_state = None
    while pc != target:
        need(len(m.trace) < 128 and len(events) < 5, '128命令/4callee有限予算')
        try:
            m.run(pc, target, limit=129 - len(m.trace))
            pc = target
        except Boundary as event:
            boundary = event.pc
            site = (m.r[14] & ~1) - 4
            need(m.calls[-1] == {'address': site, 'target': boundary}, '実BLからのみ外部境界へ')
            if boundary == FOG:
                need(not events and ENTRY <= site < ENTRY + 0x10, '先頭の実Fog caller')
                events.append(dict(kind='conditional_fog_return', site=site, target=FOG))
                pc = opaque_return(m, preserve_weather=True)
            elif boundary == LOAD:
                need(loader_state is None and not created and site + 4 == target and
                     m.r[0] == SHEET and [e['kind'] for e in events] == ['conditional_fog_return'],
                     '実root BLでsheetを渡してreaderへ入る瞬間だけを記録')
                need(type(m.r[13]) is int and STACK[0] <= m.r[13] < STACK[1] and m.r[13] % 4 == 0,
                     '実root stack frameの範囲/alignment')
                loader_state = (m.r[13], m.r[4:12].copy())
                del m.hooks[LOAD]
                pc = LOAD  # 外部ABIで代用せず、ここから実readerの全命令を解釈する。
            elif boundary == ALLOC:
                need([e['kind'] for e in events] == ['conditional_fog_return'] and m.r[0] == 2,
                     '実size64からAllocSpriteTiles(2)')
                events.append(dict(kind='conditional_tile_allocation', site=site, target=ALLOC,
                                   tiles=2, result=tile_start))
                pc = opaque_return(m, tile_start & 0xFFFFFFFF)
            elif boundary == REGISTER:
                need(tile_start >= 0 and len(events) == 2 and m.r[:3] == [TAG, tile_start, 2],
                     '同sheet tag/同allocation/2tileの実登録引数')
                events.append(dict(kind='conditional_tile_registration', site=site, target=REGISTER,
                                   tag=TAG, tile_start=tile_start, tiles=2))
                pc = opaque_return(m)
            else:
                need(len(events) == 3 and m.r[:3] == [ASSET, VRAM + tile_start * 32, 32],
                     '同source/VRAM配置/16bit32単位・非fillの実CpuSet引数')
                for offset in range(0, 64, 2):
                    value = m.read(ASSET + offset, 2)
                    asset_reads.append(dict(address=ASSET + offset, size=2))
                    m.write(VRAM + tile_start * 32 + offset, 2, value)
                events.append(dict(kind='cpuset_16bit_model', site=site, target=CPU, source=ASSET,
                    destination=VRAM + tile_start * 32, control=32, halfwords=32, bytes=64,
                    input_identity=identity(chunk(raw, ASSET, 64))))
                pc = opaque_return(m)
    expected_targets = [FOG] if created else [FOG, LOAD, ALLOC] + ([] if tile_start == -1 else [REGISTER, CPU])
    need([row['target'] for row in m.calls] == expected_targets, '根からの全call順序を閉じる')
    copied = not created and tile_start >= 0
    need(len(asset_reads) == (32 if copied else 0), '陰性分岐はasset非消費')
    if copied:
        actual = bytes(m.mem[VRAM + tile_start * 32 + i] for i in range(64))
        need(actual == chunk(raw, ASSET, 64), '全64byteの入力→出力一致')
        need(ASSET <= HIT and HIT + 4 <= ASSET + 64, '4byte全体包含')
    need(m.r[13] == (STACK[1] if created else loader_state[0]),
         'root全帰還または実reader entry/return間の正確なstack保存')
    if not created:
        need(m.r[4:12] == loader_state[1], '実readerのcallee-saved r4..r11保存')
    return dict(status='PASS_CONDITIONAL_BUBBLE_READER' if copied else 'PASS_BUBBLE_NO_READ_CONTROL',
        created=created, tile_start=tile_start, root=ENTRY, stop=target, code_steps=len(m.trace),
        calls=m.calls, events=events, code_reads=m.trace,
        reader_stack_frame=dict(entry_sp=loader_state[0], return_sp=m.r[13],
            root_frame_bytes=STACK[1] - loader_state[0]) if loader_state else None,
        protected_reads=sorted(m.reads.values(), key=lambda row: (row['address'], row['size'])),
        asset_reads=asset_reads, consumed_bytes=64 if copied else 0,
        output_identity=identity(actual) if copied else None, contract=copy.deepcopy(CONTRACT),
        claims=copy.deepcopy(CLAIMS))


def measure(raw, parent, public_sources):
    need(identity(raw) == CANDIDATE, '現0641候補の全byte identity')
    sources.bind_sources(public_sources)
    independent = sources.tiles(public_sources[sources.PNG])
    current = chunk(raw, ASSET, 64)
    controls = [compose(raw, tile_start=7), compose(raw, tile_start=-1), compose(raw, created=True)]
    whole_match = current == independent
    return dict(schema_version=1, status='PASS_BUBBLE_CONDITIONAL_READER_MEASUREMENT', candidate=identity(raw),
        target=HIT, asset=dict(address=ASSET, **identity(current)), independent_asset=identity(independent),
        whole_asset_equal=whole_match, finite_reader=controls[0], no_allocation_control=controls[1],
        already_created_control=controls[2], target_identity=identity(chunk(raw, HIT, 4)),
        type_candidate=whole_match, formal_classification_accepted=False,
        inherited=dict(classified=parent['classified'], unclassified=parent['unclassified'], hits=len(parent['hits'])),
        native_processes=0, old_scope_test_reruns=0, old_full_rom_scan_runs=0, donor_safe_bytes=0,
        claims=copy.deepcopy(CLAIMS))
