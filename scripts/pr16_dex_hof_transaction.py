#!/usr/bin/env python3
"""HOF/main世代結合の実行可能な参照実装。実ROM形式・Flash driverには未接続。

二重HOF bankと正確なmain bindingを必須にする。現128KiB配置は拒否する。
テスト用形式を既存saveのparserや暗黙migrationとして使用しない。
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import struct
import zlib

SECTOR = 4096
HOF_PAYLOAD = 7936
HOF_BANK = 2 * SECTOR
MAIN_BANK = 14 * SECTOR
HEADER = 64
MAIN_PAYLOAD = MAIN_BANK - HEADER - 1
COMMIT = 0xA5
MAX_EPOCH = (1 << 64) - 1


class ContractError(ValueError):
    pass


class PowerCut(BaseException):
    """通常のI/O errorと分離し、同processの回復処理を実行しない。"""


class FlashError(IOError):
    pass


@dataclass(frozen=True)
class Binding:
    epoch: int
    digest: bytes

    def __post_init__(self):
        if not 0 < self.epoch <= MAX_EPOCH or len(self.digest) != 32:
            raise ContractError('exact nonzero u64 epoch and SHA256 required')


@dataclass(frozen=True)
class Layout:
    capacity: int
    main: tuple[int, int] = (0, 14 * SECTOR)
    hof: tuple[int, int] = (28 * SECTOR, 32 * SECTOR)
    auxiliary: tuple[int, int] = (30 * SECTOR, 2 * SECTOR)

    def validate(self):
        regions = [(a, MAIN_BANK, 'main') for a in self.main]
        regions += [(a, HOF_BANK, 'hof') for a in self.hof]
        regions += [(*self.auxiliary, 'existing auxiliary')]
        if len(set(self.main)) != 2 or len(set(self.hof)) != 2:
            raise ContractError('two distinct main and HOF banks required')
        for a, size, _ in regions:
            if a < 0 or a % SECTOR or size <= 0 or size % SECTOR or a + size > self.capacity:
                raise ContractError('persistent shadow lease exceeds physical capacity')
        regions.sort()
        for left, right in zip(regions, regions[1:]):
            if left[0] + left[1] > right[0]:
                raise ContractError('persistent owners overlap')
        return self


class Flash:
    """NOR 1->0のhost model。erase前後と全program byte直後を観測できる。"""
    def __init__(self, layout: Layout):
        self.layout = layout.validate()
        self.data = bytearray(b'\xff' * layout.capacity)
        self.operations = 0
        self.observe = None
        self.fault = None

    def _event(self, kind, address):
        self.operations += 1
        if self.observe:
            self.observe(self, kind, address)

    def erase(self, address):
        if address % SECTOR or not 0 <= address <= len(self.data) - SECTOR:
            raise ContractError('aligned erase inside lease')
        self._event('before_erase', address)
        mode = self.fault('erase', address) if self.fault else None
        if isinstance(mode, str) and mode.startswith('partial:'):
            count = int(mode.split(':', 1)[1])
            if not 0 <= count <= SECTOR:
                raise ContractError('partial erase prefix inside one sector')
            self.data[address:address + count] = b'\xff' * count
            self._event('partial_erase', address)
            raise PowerCut()
        if mode not in (None, 'raise', 'omit'):
            raise ContractError('unknown erase fault mode')
        if mode == 'raise':
            raise FlashError('erase rejected')
        if mode != 'omit':
            self.data[address:address + SECTOR] = b'\xff' * SECTOR
        self._event('after_erase', address)

    def program(self, address, value):
        if not 0 <= address < len(self.data) or not 0 <= value <= 255:
            raise ContractError('program inside lease')
        if self.data[address] & value != value:
            raise FlashError('NOR cannot change zero to one')
        mode = self.fault('program', address) if self.fault else None
        if mode not in (None, 'raise', 'omit', 'after_raise'):
            raise ContractError('unknown program fault mode')
        if mode == 'raise':
            raise FlashError('program rejected')
        if mode != 'omit':
            self.data[address] &= value
        self._event('program', address)
        if mode == 'after_raise':
            raise FlashError('durable write reported failure')


def crc(data):
    return zlib.crc32(data) & 0xffffffff


def encode(kind: bytes, binding: Binding, counter: int, body: bytes, size: int):
    expected = HOF_PAYLOAD if kind == b'HFT1' else MAIN_PAYLOAD
    if kind not in (b'HFT1', b'MFT1') or len(body) != expected:
        raise ContractError('closed synthetic record kind and exact payload')
    if size != (HOF_BANK if kind == b'HFT1' else MAIN_BANK):
        raise ContractError('closed bank size')
    if not 0 <= counter <= 0xffffffff:
        raise ContractError('u32 counter')
    if kind == b'HFT1' and hashlib.sha256(body).digest() != binding.digest:
        raise ContractError('HOF bytes must match exact binding digest')
    header = bytearray(struct.pack('<4sHHQ32sIII', kind, 1, HEADER, binding.epoch,
                                  binding.digest, len(body), counter, crc(body)))
    header += struct.pack('<I', crc(header))
    assert len(header) == HEADER
    result = header + body + b'\xff' * (size - HEADER - len(body) - 1) + bytes([COMMIT])
    return bytes(result)


def parse(data: bytes | bytearray, kind: bytes):
    if kind not in (b'HFT1', b'MFT1'):
        return None
    size = HOF_BANK if kind == b'HFT1' else MAIN_BANK
    length = HOF_PAYLOAD if kind == b'HFT1' else MAIN_PAYLOAD
    if len(data) != size or data[-1] != COMMIT:
        return None
    magic, version, hlen, epoch, digest, blen, counter, check = struct.unpack_from('<4sHHQ32sIII', data)
    if magic != kind or version != 1 or hlen != HEADER or blen != length or not epoch:
        return None
    if crc(data[:60]) != struct.unpack_from('<I', data, 60)[0]:
        return None
    body = bytes(data[HEADER:HEADER + blen])
    if crc(body) != check or any(v != 255 for v in data[HEADER + blen:-1]):
        return None
    if kind == b'HFT1' and hashlib.sha256(body).digest() != digest:
        return None
    return Binding(epoch, digest), counter, body


def main_select(flash: Flash):
    rows = []
    for index, address in enumerate(flash.layout.main):
        parsed = parse(flash.data[address:address + MAIN_BANK], b'MFT1')
        if parsed:
            rows.append((index, *parsed))
    if not rows:
        raise ContractError('no complete main authority')
    if len(rows) == 1:
        return rows[0]
    a, b = rows
    delta = (b[2] - a[2]) & 0xffffffff
    if delta == 0:
        if a[1:] != b[1:]:
            raise ContractError('equal-counter divergent main authorities')
        return a
    if delta == 0x80000000:
        raise ContractError('ambiguous serial distance')
    return b if delta < 0x80000000 else a


def recover(flash: Flash):
    """mainを先に選び、その完全tokenと一致するHOFだけを返す。counter順だけでは結合しない。"""
    main = main_select(flash)
    matches = []
    for index, address in enumerate(flash.layout.hof):
        parsed = parse(flash.data[address:address + HOF_BANK], b'HFT1')
        if parsed and parsed[0] == main[1]:
            matches.append((index, parsed[2]))
    if not matches or any(p != matches[0][1] for _, p in matches):
        raise ContractError('selected main has no exact durable HOF binding')
    return dict(main_bank=main[0], binding=main[1], counter=main[2], main=main[3],
                hof_bank=matches[0][0], hof=matches[0][1])


def _write(flash: Flash, address: int, image: bytes):
    for offset in range(0, len(image), SECTOR):
        flash.erase(address + offset)
    for offset, value in enumerate(image[:-1]):
        if value != 255:
            flash.program(address + offset, value)
    expected = image[:-1] + b'\xff'
    if bytes(flash.data[address:address + len(image)]) != expected:
        raise FlashError('full prepared-bank readback differs')
    flash.program(address + len(image) - 1, COMMIT)
    if bytes(flash.data[address:address + len(image)]) != image:
        raise FlashError('full committed-bank readback differs')


def save(flash: Flash, main_body: bytes, hof_body: bytes | None = None):
    """全preflight後のみ書込。通常SaveはHOF tokenをそのまま継承。"""
    flash.layout.validate()
    old = recover(flash)
    if len(main_body) != MAIN_PAYLOAD:
        raise ContractError('exact main payload before any write')
    new_binding = old['binding']
    new_hof = old['hof']
    if hof_body is not None:
        if len(hof_body) != HOF_PAYLOAD or old['binding'].epoch == MAX_EPOCH:
            raise ContractError('HOF exact payload and nonwrapping epoch before any write')
        new_hof = hof_body
        new_binding = Binding(old['binding'].epoch + 1, hashlib.sha256(hof_body).digest())
    counter = (old['counter'] + 1) & 0xffffffff
    main_image = encode(b'MFT1', new_binding, counter, main_body, MAIN_BANK)
    hof_image = encode(b'HFT1', new_binding, counter, new_hof, HOF_BANK) if hof_body is not None else None
    target_main = flash.layout.main[1 - old['main_bank']]
    try:
        if hof_image is not None:
            _write(flash, flash.layout.hof[1 - old['hof_bank']], hof_image)
        _write(flash, target_main, main_image)
    except FlashError:
        # 最後のcommit byteが実際に残った場合も、Flash返値だけで旧世代と断言しない。
        got = recover(flash)
        if (got['binding'], got['counter'], got['main'], got['hof']) == (new_binding, counter, main_body, new_hof):
            return 'COMMITTED_AFTER_IO_ERROR'
        if (got['binding'], got['counter'], got['main'], got['hof']) != (old['binding'], old['counter'], old['main'], old['hof']):
            raise ContractError('failure produced a third or mixed generation')
        return 'OLD_GENERATION_RETAINED'
    got = recover(flash)
    if (got['binding'], got['counter'], got['main'], got['hof']) != (new_binding, counter, main_body, new_hof):
        raise ContractError('commit did not bind exact new pair')
    return 'COMMITTED'


def fixture(counter=101, epoch=1):
    """34sectorは明示的な合成fixture。現32sector saveを拡張・変換しない。"""
    flash = Flash(Layout(34 * SECTOR))
    hof = bytes((i * 7 + 11) % 251 for i in range(HOF_PAYLOAD))
    main = bytes((i * 13 + 3) % 251 for i in range(MAIN_PAYLOAD))
    binding = Binding(epoch, hashlib.sha256(hof).digest())
    flash.data[:MAIN_BANK] = encode(b'MFT1', binding, counter, main, MAIN_BANK)
    address = flash.layout.hof[0]
    flash.data[address:address + HOF_BANK] = encode(b'HFT1', binding, counter, hof, HOF_BANK)
    return flash
