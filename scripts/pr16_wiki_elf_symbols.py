#!/usr/bin/env python3
"""保存ARM ELF32のsymbolと有界sectionを読む。link・実行・名前の推測はしない。"""
from __future__ import annotations
from collections import defaultdict
import re
import struct
from pr16_candidate_wiki_inputs import BASE, digest, need


class Elf:
    def __init__(self, raw: bytes):
        self.raw = raw
        need(len(raw) >= 52 and raw[:7] == b'\x7fELF\x01\x01\x01', 'ELF32 little endian/version不正')
        kind, machine, version = struct.unpack_from('<HHI', raw, 16)
        need(kind in (1, 2) and machine == 40 and version == 1, 'ARM ELF形式不正')
        off = struct.unpack_from('<I', raw, 32)[0]
        header = struct.unpack_from('<H', raw, 40)[0]
        stride, count = struct.unpack_from('<HH', raw, 46)
        need(header == 52 and stride == 40 and 0 < count <= 4096, 'ELF section header不正')
        need(off >= 52 and off <= len(raw) - count * stride, 'ELF section table範囲外')
        self.sections = []
        for i in range(count):
            values = struct.unpack_from('<10I', raw, off + stride * i)
            row = dict(zip(('name', 'kind', 'flags', 'address', 'offset', 'size', 'link', 'info', 'align', 'stride'), values))
            need(row['address'] + row['size'] <= 1 << 32, 'ELF section address overflow')
            if row['kind'] != 8:
                need(row['offset'] <= len(raw) - row['size'], 'ELF section byte範囲外')
            self.sections.append(row)
        found = defaultdict(list)
        for table in self.sections:
            if table['kind'] != 2:
                continue
            need(table['stride'] == 16 and table['size'] % 16 == 0, 'ELF symbol stride不正')
            need(table['size'] <= 16 * 100000 and 0 < table['link'] < count, 'ELF symbol table上限/strtab不正')
            strings = self.sections[table['link']]
            need(strings['kind'] == 3, 'ELF symbol名がstrtabを参照しない')
            names = raw[strings['offset']:strings['offset'] + strings['size']]
            for off in range(table['offset'], table['offset'] + table['size'], 16):
                name_at, address, size, info, other, section = struct.unpack_from('<IIIBBH', raw, off)
                need(name_at < len(names), 'ELF symbol名の範囲外')
                end = names.find(b'\0', name_at)
                need(end >= name_at and end - name_at <= 1024, 'ELF symbol名終端/上限不正')
                name = names[name_at:end].decode('utf-8')
                if not name or name.startswith('$'):
                    continue
                need(section == 0 or section < count or section in (0xFFF1, 0xFFF2), 'ELF symbol section不正')
                row = dict(symbol=name, address=address, size=size, type=info & 15, binding=info >> 4,
                           section=section, visibility=other & 3)
                if row not in found[name]:
                    found[name].append(row)
        need(bool(found), 'ELF named symbolなし')
        self.symbols = dict(sorted(found.items()))

    def span(self, row: dict, size: int | None = None) -> bytes:
        length = row['size'] if size is None else size
        need(type(length) is int and 0 < length <= 65536, 'ELF symbol byte範囲不正')
        section = row['section']
        need(0 < section < len(self.sections), 'ELF symbol実体sectionなし')
        owner = self.sections[section]
        need(owner['kind'] != 8 and owner['flags'] & 2, 'ELF非alloc/NOBITS実体')
        address = row['address'] & ~1 if row['type'] == 2 else row['address']
        need(owner['address'] <= address and address + length <= owner['address'] + owner['size'], 'ELF symbolが所属sectionを超過')
        matches = [s for s in self.sections if s['kind'] != 8 and s['flags'] & 2
                   and s['address'] <= address and address + length <= s['address'] + s['size']]
        need(len(matches) == 1, 'ELF allocated span重複')
        at = owner['offset'] + address - owner['address']
        return self.raw[at:at + length]

    def bind(self, symbol: str, candidate: bytes) -> dict:
        rows = self.symbols.get(symbol, [])
        result = {'symbol': symbol, 'native_acceptance': 'DEFERRED_AUDIT', 'source_equivalence_proven': False}
        if not rows:
            return dict(result, status='MISSING_SAVED_SYMBOL')
        if len(rows) != 1:
            return dict(result, status='AMBIGUOUS_SAVED_SYMBOL', definitions=rows)
        row = rows[0]
        result.update(elf_symbol=row)
        if row['size'] == 0:
            return dict(result, status='SYMBOL_WITHOUT_PROVEN_EXTENT')
        if row['section'] in (0, 0xFFF1, 0xFFF2):
            return dict(result, status='SYMBOL_WITHOUT_ALLOCATED_BODY')
        if row['type'] not in (1, 2):
            return dict(result, status='UNSUPPORTED_SYMBOL_TYPE')
        address = row['address'] & ~1 if row['type'] == 2 else row['address']
        size = row['size']
        result.update(address=address, size=size)
        if not BASE <= address <= BASE + len(candidate) - size:
            return dict(result, status='SYMBOL_OUTSIDE_CANDIDATE')
        data = self.span(row)
        actual = candidate[address-BASE:address-BASE+size]
        result.update(saved_sha256=digest(data), candidate_sha256=digest(actual))
        return dict(result, status='EXACT_CANDIDATE_SYMBOL_BODY' if data == actual else 'CANDIDATE_BODY_DIFFERS')
