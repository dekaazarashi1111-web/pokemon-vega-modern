"""Circus連勝getterの５引数を保つThumb-1中継。旧builder/ARM再compileは使わない。"""
from __future__ import annotations
import hashlib
import struct

BASE = 0x08000000
SIZE = 33554432
CALL = 0x09103380
PARENT = dict(size=SIZE, sha256='2b107e7ef897844eff810ff0b40f82543640488696e8295194ceb3b66fb2c183')
SAVE = dict(size=131088, sha256='b4846fe3d915f69f7cefb2f58a0c2c0c571d9f96d5d16a295537854d849c2371')
CACHE_KEY = 'pr16-circus-save30-' + PARENT['sha256'] + '-35494023398'
# push {r3}; ldr r3,[pc,#8]; mov ip,r3; pop {r3}; bx ip; nop; .word target
# push/popは戻るため第５引数の位置も維持。NZCV/LR/r0-r3を変更しない。
CODE = bytes.fromhex('08b4024b9c4608bc6047c046')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def decode_bl(address, raw):
    need(type(address) is int and address % 2 == 0 and len(raw) == 4, 'BL shape')
    a, b = struct.unpack('<HH', raw)
    need(a & 0xf800 == 0xf000 and b & 0xf800 == 0xf800, 'Thumb BL required')
    delta = ((a & 0x7ff) << 12) | ((b & 0x7ff) << 1)
    if delta & 0x400000:
        delta -= 0x800000
    return address + 4 + delta


def encode_bl(address, target):
    need(type(address) is type(target) is int and not (address | target) & 1, 'BL alignment')
    delta = target - address - 4
    need(-0x400000 <= delta <= 0x3ffffe, 'BL range')
    value = delta & 0x7fffff
    raw = struct.pack('<HH', 0xf000 | (value >> 12), 0xf800 | ((value >> 1) & 0x7ff))
    need(decode_bl(address, raw) == target, 'BL roundtrip')
    return raw


def veneer(address, target):
    need(type(address) is type(target) is int and address % 4 == 0, 'veneer alignment')
    need(BASE <= address <= BASE + SIZE - 16 and BASE < target < BASE + SIZE and target & 1,
         'Thumb ROM target required')
    # LDR at +2 uses Align(PC+4,4)=address+4, therefore +8 addresses the +12 literal.
    return CODE + struct.pack('<I', target)


def execute_veneer(raw, address, registers, stack):
    """６命令の限定モデル。未知命令を通さず、引数/stack保存をunit testする。"""
    need(len(raw) == 16 and raw[:12] == CODE and address % 4 == 0, 'unrecognized veneer')
    need(len(registers) == 16, 'sixteen registers required')
    r, memory = list(registers), dict(stack)
    original_sp = r[13]
    r[13] -= 4
    memory[r[13]] = r[3]  # push
    r[3] = struct.unpack_from('<I', raw, 12)[0]  # PC-relative LDR
    r[12] = r[3]
    r[3] = memory[r[13]]
    r[13] += 4
    r[15] = r[12] & ~1
    need(r[13] == original_sp, 'stack imbalance')
    return r, memory


def old_veneer(rom, allocation):
    need(identity(rom) == PARENT, 'fixed parent identity')
    rows = [r for r in allocation['allocations'] if r['name'] == 'pr16_circus_streak_get_veneer']
    need(len(rows) == 1 and rows[0]['size'] == 8, 'one historical eight-byte veneer required')
    row = rows[0]; at = row['start']; raw = rom[at:at+8]
    need(identity(raw)['sha256'] == row['content_sha256'] and raw[:4] == bytes.fromhex('004b1847'),
         'historical r3 veneer preimage')
    need(decode_bl(CALL, rom[CALL-BASE:CALL-BASE+4]) == BASE + at, 'getter BL ownership')
    target = struct.unpack_from('<I', raw, 4)[0]
    need(target & 1 and BASE < target < BASE + SIZE, 'historical Thumb getter')
    return dict(address=BASE+at, target=target, bytes=raw.hex(), fourth_argument_clobbered=True,
                callsite=CALL, source='scripts/pr16_circus_streak.py', accepted_parent_unchanged=True)


def patch(rom, old, address):
    """新規16byte中継と既存BL４byteだけ。旧中継/runtime/Save ABIは不変。"""
    need(identity(rom) == PARENT and old['callsite'] == CALL, 'patch parent')
    at = address - BASE
    code = veneer(address, old['target'])
    need(rom[at:at+16] == b'\xff'*16, 'allocation must be erased')
    before = rom[CALL-BASE:CALL-BASE+4]
    need(decode_bl(CALL, before) == old['address'], 'call preimage changed')
    changes = [dict(offset=CALL-BASE, before=before.hex(), after=encode_bl(CALL,address).hex()),
               dict(offset=at, before=(b'\xff'*16).hex(), after=code.hex())]
    out = bytearray(rom); last = 0
    for row in sorted(changes, key=lambda r:r['offset']):
        pos, left, right = row['offset'], bytes.fromhex(row['before']), bytes.fromhex(row['after'])
        need(last <= pos and len(left) == len(right) and rom[pos:pos+len(left)] == left, 'overlap/preimage')
        out[pos:pos+len(right)] = right; last = pos + len(right)
    rollback = bytearray(out)
    for row in changes:
        pos, before = row['offset'], bytes.fromhex(row['before'])
        rollback[pos:pos+len(before)] = before
    need(bytes(rollback) == rom, 'whole-ROM rollback')
    return bytes(out), changes


def validate_cache(provenance, save, expected):
    need(provenance == expected and provenance['verified'] is True, 'cache provenance differs')
    need(provenance['candidate'] == PARENT and provenance['save'] == SAVE and identity(save) == SAVE,
         'normal Save30 identity')
    need(provenance['run_id'] == 35494023398 and provenance['cache_key'] == CACHE_KEY,
         'cache source run')
    need(provenance['tracked'] is False and provenance['artifact_included'] is False,
         'private save boundary')
    return dict(source_run=35494023398, save=SAVE, cache_key=CACHE_KEY,
                prefix_wins_reexecuted=0, host_state_injection=False)


def diagnose_draws(rows):
    need(len(rows) == 64, 'original 64 draws required')
    for i, row in enumerate(rows):
        need(row['attempt'] == i and row['delay'] == 17*i and row['target'] is False,
             'original draw ordering')
        need(row['current'] == row['best'] == 30 and row['bp'] == 90 and row['counter'] == 3,
             'original real Save30 boundary')
        need(0 < row['flags'] < (1 << 19) and row['flags'].bit_count() == 1,
             'original flags not the observed single global effect')
    return dict(draws=64, target_draws=0, observed_owner_current=30,
                only_one_global_effect=True, original_conclusion='failure',
                note_ja='抽選回数を増やさず、getterの第４引数破壊を修復する。')
