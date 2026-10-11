#!/usr/bin/env python3
"""Forestの実Thumb呼出列を有限解釈する。native/BIOS本体/解放の受入ではない。"""
from __future__ import annotations
import hashlib
import json
import struct

BASE, ASSET, HIT = 0x08000000, 0x08397188, 0x08397492
STACK, STORAGE, HEAP = (0x03007800, 0x03007F00), 0x02008000, 0x02018000
CANDIDATE = {'size': 33554432, 'sha256': '0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
DECODED = {'size': 1696, 'sha256': '004a48f42202841373162e9732de13007725da29ad997429386cbccf0461a2ea'}
LAYOUT_FIELDS = ('object_size', 'wallpaperOffset', 'wallpaperLoadState', 'wallpaperLoadBoxId',
                 'wallpaperLoadDir', 'wallpaperTilemap', 'wallpaperBgTilemapBuffer')
WIDTHS = dict(wallpaperOffset=1, wallpaperLoadState=1, wallpaperLoadBoxId=1,
              wallpaperLoadDir=1, wallpaperTilemap=720, wallpaperBgTilemapBuffer=4096)
NAMES = {'LoadWallpaperGfx', 'DecompressAndLoadBgGfxUsingHeap', 'MallocAndDecompress',
         'GetBoxWallpaper', 'DrawWallpaper', 'LZ77UnCompWram', 'CpuSet', 'Alloc',
         'CreateTask', 'TaskFreeBufAfterCopyingTileDataToVram', 'gStorage',
         'gPlttBufferUnfaded', 'sWallpapers', 'sWallpaperTiles_Forest',
         'sWallpaperTilemap_Forest', 'sWallpaperPalettes_Forest'}
CLAIMS = dict(conditional_finite_reader_only=True, actual_runtime_execution_observed=False,
              actual_bios_cpu_executed=False, actual_screen_rendered=False,
              allocator_implementation_proven=False, dma_completion_proven=False,
              heap_free_proven=False, universal_heap_or_irq_lifetime_proven=False,
              formal_classification_accepted=False, indirect_reference_completeness_claimed=False,
              donor_eligible=False, donor_leased=False, donor_safe_bytes=0,
              formal_rom_changed=False, formal_save_changed=False, native_processes=0,
              accepted_test_reruns=0, accepted_reader_replays=0)
CONDITIONS = {
    'caller_ja': 'boxId=0、direction=0、wallpaperOffset=0/1の直接entry。固定公開headerをARMでコンパイルしたlayoutの非alias storage割当を条件とする。自然進行/実PC画面の証明ではない。',
    'selection_ja': 'GetBoxWallpaper(0)がForest ID=0を返し、同期AAPCSでstorage対象fieldとcaller stackを保全する条件。選択helper本体/保存データの実行ではない。',
    'opaque_ja': 'tilemap LZ/DrawWallpaper/CpuSetは指定bufferだけへ作用して正常帰還する条件。caller-savedレジスタとNZCVは未定義化。描画成功stubやnative観測とは扱わない。',
    'allocation_ja': 'Alloc(1696)は非alias heapを同一epochで返すかNULL。allocator実装/IRQ/同期保存controllerのheap寿命は未証明。',
    'bios_ja': '実LZ77UnCompWramのSWI11/BXを照合し、呼出引数からLZ10仕様モデルを駆動する。BIOS本体CPUではない。',
    'stop_ja': '成功は実MallocAndDecompress帰還とCreateTask直前、失敗は実DecompressAndLoadBgGfxUsingHeap帰還まで。task/DMA/Freeは別gate。',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    need(type(raw) is bytes, 'bytesのみ')
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def validate_layout(layout):
    need(type(layout) is dict and set(layout) == set(LAYOUT_FIELDS), 'layout閉schema')
    need(all(type(v) is int for v in layout.values()), 'layout整数型')
    need(0 < layout['object_size'] <= 0x8000, 'storage最大extent')
    spans = [(layout[k], layout[k] + width) for k, width in WIDTHS.items()]
    need(all(0 <= lo < hi <= layout['object_size'] for lo, hi in spans), 'field extent')
    need(all(a[1] <= b[0] or b[1] <= a[0] for i, a in enumerate(spans) for b in spans[i + 1:]), 'field非alias')
    need(layout['wallpaperTilemap'] % 2 == 0, 'u16 tilemap整列')
    return layout


def validate_options(allocated, offset):
    need(type(allocated) is bool, 'allocationはbool')
    need(type(offset) is int and offset in (0, 1), 'wallpaper offsetは0/1')


def symbols(raw, expected):
    need(identity(raw) == {k: expected[k] for k in ('size', 'sha256')}, '固定JP symbol全体')
    found = {}
    for line in raw.decode().splitlines():
        row = line.split('\t')
        if len(row) == 8 and row[4] in NAMES:
            need(row[4] not in found, 'symbol重複')
            found[row[4]] = int(row[1], 16)
    need(set(found) == NAMES, 'symbol不足: ' + ','.join(sorted(NAMES - set(found))))
    need(found['sWallpaperTiles_Forest'] == ASSET, 'Forest asset先頭')
    need(0x02000000 <= found['gStorage'] <= 0x0203FFFC and found['gStorage'] % 4 == 0, 'storage global')
    return found


def lz10(memory, src, dst, packed_size, decoded_size):
    """入力read/展開writeを全てmemory経由へ閉じたSWI11仕様モデル。"""
    need(all(type(v) is int for v in (src, dst, packed_size, decoded_size)), 'LZ整数型')
    need(4 <= packed_size <= 16384 and 0 < decoded_size <= 8192, 'LZ有限extent')
    need(0 <= src <= 2**32 - packed_size and 0 <= dst <= 2**32 - decoded_size, 'LZ address範囲')
    need(src % 4 == 0 and dst % 4 == 0, 'SWI11整列')
    need(src + packed_size <= dst or dst + decoded_size <= src, 'LZ非alias')
    pos = 0
    def take():
        nonlocal pos
        need(pos < packed_size, 'LZ入力末尾')
        value = memory.read(src + pos, 1)
        pos += 1
        return value
    need(take() == 16, 'LZ10 header')
    length = take() | take() << 8 | take() << 16
    need(length == decoded_size, 'LZ出力宣言')
    out = bytearray()
    while len(out) < length:
        flags = take()
        for bit in range(8):
            if len(out) == length:
                break
            if flags & (128 >> bit):
                first, second = take(), take()
                count, distance = (first >> 4) + 3, ((first & 15) << 8 | second) + 1
                need(distance <= len(out) and len(out) + count <= length, 'LZ後方参照/過剰出力')
                for _ in range(count):
                    value = memory.read(dst + len(out) - distance, 1)
                    memory.write(dst + len(out), 1, value)
                    out.append(value)
            else:
                value = take()
                memory.write(dst + len(out), 1, value)
                out.append(value)
    need(pos == packed_size, '未消費tailはreader証拠に含めない')
    return {'consumed': pos, 'output': identity(bytes(out))}


class Boundary(Exception):
    def __init__(self, pc):
        self.pc = pc


def pause(machine, pc):
    raise Boundary(pc)


def compose(raw, sym, layout, *, allocated=True, offset=0):
    """共有解釈器のみ再利用。旧consumer/旧試験/PNG生成器は実行しない。"""
    import pr16_dex_hof_runtime_sprite as thumb
    validate_options(allocated, offset)
    validate_layout(layout)
    need(identity(raw) == CANDIDATE, 'exact current candidate')
    need(type(sym) is dict and set(sym) == NAMES, 'closed symbols')
    entry, load, malloc = (sym[n] for n in ('LoadWallpaperGfx', 'DecompressAndLoadBgGfxUsingHeap', 'MallocAndDecompress'))
    # 有限実行窓であり、近傍labelから資源/関数sizeを推定するものではない。
    code = tuple((pc, pc + 512) for pc in (entry, load, malloc))
    table = sym['sWallpapers']
    expected_tuple = tuple(sym[n] for n in ('sWallpaperTiles_Forest', 'sWallpaperTilemap_Forest', 'sWallpaperPalettes_Forest'))
    need(struct.unpack_from('<III', raw, table - BASE) == expected_tuple, '継承Forest tupleの現候補束縛')
    need(raw[sym['LZ77UnCompWram']-BASE:sym['LZ77UnCompWram']-BASE+4] == b'\x11\xdf\x70\x47', '実SWI11/BX')
    need(raw[sym['CpuSet']-BASE:sym['CpuSet']-BASE+4] == b'\x0b\xdf\x70\x47', '実SWI0B/BX')
    storage_fields = tuple((STORAGE + layout[k], STORAGE + layout[k] + 1) for k in WIDTHS if WIDTHS[k] == 1)
    writes = (STACK, *storage_fields, (HEAP, HEAP + DECODED['size']))
    rom_reads = (*code, (table, table+12), (ASSET, ASSET+973),
                 (sym['LZ77UnCompWram'], sym['LZ77UnCompWram']+4), (sym['CpuSet'], sym['CpuSet']+4))
    callbacks = {sym[n]: pause for n in ('GetBoxWallpaper', 'DrawWallpaper', 'LZ77UnCompWram', 'CpuSet',
                                       'Alloc', 'CreateTask', 'DecompressAndLoadBgGfxUsingHeap', 'MallocAndDecompress')}
    class Machine(thumb.Machine):
        def read(self, address, size):
            need(type(address) is int and type(size) is int, 'read型')
            if BASE <= address < BASE + len(self.raw):
                need(any(lo <= address and address+size <= hi for lo, hi in rom_reads), '限定ROM read')
            else:
                self.ram_reads.append({'address': address, 'size': size})
            return super().read(address, size)
    m = Machine(raw, code, writes, callbacks)
    m.ram_reads = []
    m.seed(sym['gStorage'], 4, STORAGE)
    m.seed(STORAGE + layout['wallpaperOffset'], 1, offset)
    m.r[:4] = [0, 0, thumb.UndefinedCallerRegister('entry r2'), thumb.UndefinedCallerRegister('entry r3')]
    m.flags = [thumb.UndefinedCallerRegister('entry NZCV')] * 4
    initial = dict(m.mem)
    def opaque(value=None):
        # 対象caller field/stackと生存heapだけが契約上保存される。観測後の成功書換えではない。
        allowed = (STACK, *storage_fields, (sym['gStorage'], sym['gStorage']+4), (HEAP, HEAP+DECODED['size']))
        need(all(any(lo <= a < hi for lo, hi in allowed) for a in m.mem), 'opaque write frame')
        m.r[:4] = [thumb.UndefinedCallerRegister('caller-saved r'+str(n)) for n in range(4)]
        m.r[12] = thumb.UndefinedCallerRegister('caller-saved r12')
        m.flags = [thumb.UndefinedCallerRegister('caller-saved NZCV')] * 4
        if value is not None:
            m.r[0] = value
        return m.r[14] & ~1
    pc, stop, events = entry, 0x01000000, []
    load_frame = malloc_frame = None
    lz_result = None
    malloc_returned = False
    expected_sequence = ['GetBoxWallpaper', 'tilemap_contract', 'DrawWallpaper', 'CpuSet',
                         'DecompressAndLoadBgGfxUsingHeap', 'MallocAndDecompress', 'Alloc']
    if allocated:
        expected_sequence += ['asset_lz_model', 'malloc_return', 'CreateTask_boundary']
    else:
        expected_sequence += ['malloc_return', 'loader_return']
    while True:
        need(len(m.trace) < 512 and len(events) < 12, '512命令/有限callee予算')
        try:
            m.run(pc, stop, limit=513-len(m.trace))
            need(malloc_frame is not None, '予期しないentry帰還')
            if not malloc_returned:
                need(m.r[4:12]+[m.r[13]] == malloc_frame['saved'], '実malloc callee-saved/SP復元')
                need(m.r[0] == (HEAP if allocated else 0), '実malloc帰還pointer')
                need(m.read(malloc_frame['size_slot'], 4) == DECODED['size'], '実header→sizeOut stack')
                events.append({'kind': 'malloc_return', 'address': stop, 'sp': m.r[13]})
                malloc_returned = True
                pc, stop = stop, load_frame['return']
                continue
            need(not allocated and m.r[4:12]+[m.r[13]] == load_frame['saved'], '実NULL側loader復元')
            events.append({'kind': 'loader_return', 'address': stop, 'sp': m.r[13]})
            break
        except Boundary as boundary:
            address = boundary.pc
            site = (m.r[14] & ~1)-4
            need(m.calls[-1] == {'address': site, 'target': address}, '実BLだけから境界へ')
            name = next(n for n in NAMES if sym[n] == address)
            kind = name
            if name == 'GetBoxWallpaper':
                need(not events and m.r[0] == 0, '実boxId=0引数')
                pc = opaque(0)
            elif name == 'LZ77UnCompWram':
                if m.r[0] == sym['sWallpaperTilemap_Forest']:
                    kind = 'tilemap_contract'
                    need(m.r[1] == STORAGE+layout['wallpaperTilemap'] and len(events) == 1, 'tilemap限定destination')
                    pc = opaque()
                else:
                    kind = 'asset_lz_model'
                    need(allocated and malloc_frame is not None and lz_result is None and m.r[:2] == [ASSET, HEAP], '実heap→LZ引数')
                    lz_result = lz10(m, m.r[0], m.r[1], 973, DECODED['size'])
                    need(lz_result['output'] == DECODED, '継承独立tile hashとモデル出力一致')
                    pc = opaque()
            elif name == 'DrawWallpaper':
                need(m.r[:4] == [STORAGE+layout['wallpaperBgTilemapBuffer'], STORAGE+layout['wallpaperTilemap'], 0, offset], 'Draw引数')
                pc = opaque()
            elif name == 'CpuSet':
                need(m.r[:3] == [sym['sWallpaperPalettes_Forest'], sym['gPlttBufferUnfaded']+128+offset*64, 32], 'palette CpuSet引数')
                pc = opaque()
            elif name == 'DecompressAndLoadBgGfxUsingHeap':
                need(load_frame is None and m.r[:4] == [2, ASSET, 0, offset*256] and m.read(m.r[13], 4) == 0, '実loader全5引数')
                load_frame = {'saved': m.r[4:12]+[m.r[13]], 'return': m.r[14]&~1}
                del m.hooks[address]
                pc = address
            elif name == 'MallocAndDecompress':
                need(load_frame is not None and malloc_frame is None and m.r[0] == ASSET, '実Malloc consumer')
                need(type(m.r[1]) is int and STACK[0] <= m.r[13] <= m.r[1] <= load_frame['saved'][-1]-4, 'sizeOut実caller stack')
                malloc_frame = {'saved': m.r[4:12]+[m.r[13]], 'size_slot': m.r[1]}
                stop = m.r[14]&~1
                del m.hooks[address]
                pc = address
            elif name == 'Alloc':
                need(malloc_frame is not None and m.r[0] == DECODED['size'], '実Alloc(1696)')
                pc = opaque(HEAP if allocated else 0)
            elif name == 'CreateTask':
                need(allocated and malloc_returned and lz_result is not None and
                     m.r[:2] == [sym['TaskFreeBufAfterCopyingTileDataToVram']|1, 0], '成功側実task作成直前')
                events.append({'kind': 'CreateTask_boundary', 'site': site, 'target': address})
                break
            else:
                raise ValueError('未契約callee')
            events.append({'kind': kind, 'site': site, 'target': address})
    need([event['kind'] for event in events] == expected_sequence, '閉じた実call順序')
    table_reads = [dict(row) for (a, n), row in m.reads.items() if table <= a and a+n <= table+12]
    need({r['address'] for r in table_reads} == {table, table+4, table+8}, '実table全3field read')
    source_reads = sorted(a for (a, n) in m.reads if ASSET <= a < ASSET+973 and n == 1)
    heap_writes = [w for w in m.writes if HEAP <= w['address'] < HEAP+DECODED['size']]
    need(len(heap_writes) == (DECODED['size'] if allocated else 0), 'heap write会計')
    need(lz_result is not None if allocated else lz_result is None, 'allocation対照')
    if allocated:
        need(source_reads == list(range(ASSET, ASSET+973)), '入力全973byteを順序付き集合で消費')
        need(set(range(HIT, HIT+4)) <= set(source_reads), '対象全4byte消費')
    else:
        need(set(source_reads) <= {ASSET+1, ASSET+2, ASSET+3}, 'NULL側はheaderだけ')
    return {'allocated': allocated, 'wallpaper_offset': offset, 'status': 'PASS_CONDITIONAL_FINITE_READER',
            'instruction_count': len(m.trace), 'trace': m.trace, 'calls': m.calls,
            'events': events, 'table_reads': table_reads,
            'caller_fixture': {'storage_address': STORAGE, 'layout': layout, 'seeded_bytes': len(initial),
                               'seed_identity': identity(encode(sorted(initial.items()))), 'box_id': 0, 'direction': 0},
            'ram_reads': m.ram_reads, 'writes': [{'address': w['address'], 'size': w['size']} for w in m.writes],
            'asset_lz_consumed': 973 if allocated else 0,
            'target_bytes_consumed': 4 if allocated else 0, 'heap_bytes_written': len(heap_writes),
            'decoded': lz_result['output'] if lz_result else None,
            'malloc_return_frame_proven': True, 'loader_null_return_frame_proven': not allocated,
            'heap_live_at_success_stop': allocated, 'claims': dict(CLAIMS)}
