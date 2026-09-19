#!/usr/bin/env python3
"""保存済み差分だけを適用する再構成核。compiler/native/旧builderは呼ばない。"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path


class RecipeError(ValueError):
    """原本・境界・順序・出力identityが固定契約と異なる。"""


def need(ok, message):
    if not ok:
        raise RecipeError(message)


def identity(raw):
    need(type(raw) is bytes, 'immutable bytes required')
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def strict(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            need(key not in out, 'duplicate JSON key: '+key)
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(RecipeError('nonfinite JSON')))


def binding(value):
    need(type(value) is dict and set(value) == {'size', 'sha256'}, 'identity keys differ')
    need(type(value['size']) is int and value['size'] > 0, 'identity size differs')
    need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'identity digest differs')
    return value


def hex_bytes(value):
    need(type(value) is str and re.fullmatch('(?:[0-9a-f]{2})+', value), 'canonical nonempty hex required')
    return bytes.fromhex(value)


def safe(root, name):
    need(type(name) is str and name and '\\' not in name, 'invalid path')
    p = Path(name)
    need(not p.is_absolute() and '..' not in p.parts and str(p) == name, 'unsafe/noncanonical path')
    root = Path(root).resolve()
    current = root
    for part in p.parts:
        current /= part
        need(not current.is_symlink(), 'symlink path rejected')
    current.resolve().relative_to(root)
    return current


def allocations(raw, plan):
    need(type(plan) is dict and type(plan.get('allocations')) is list, 'allocation rows missing')
    need(plan.get('summaries', {}).get('overlap_count') == 0, 'allocation overlap summary')
    spans, names = [], set()
    for i, row in enumerate(plan['allocations']):
        a, b, size = row['start'], row['end_exclusive'], row['size']
        need(type(a) is type(b) is type(size) is int and 0 <= a < b <= len(raw) and b-a == size,
             'allocation outside candidate')
        need(type(row['sequence']) is int and row['sequence'] == i, 'allocation sequence differs')
        need(type(row['name']) is str and row['name'] not in names, 'duplicate allocation owner')
        names.add(row['name'])
        need(identity(raw[a:b])['sha256'] == row['content_sha256'], 'allocation content differs: '+row['name'])
        spans.append((a, b))
    ordered = sorted(spans)
    need(all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:])), 'actual allocation overlap')
    return len(spans)


def patch(raw, rows):
    need(type(raw) is bytes and type(rows) is list and rows, 'bytes/nonempty patch list required')
    prepared = []
    for row in rows:
        need(type(row) is dict and type(row.get('offset')) is int, 'integer patch offset required')
        before, after = hex_bytes(row['before']), hex_bytes(row['after'])
        need(len(before) == len(after) and before != after, 'fixed-size nonempty change required')
        prepared.append((row['offset'], before, after))
    prepared.sort(key=lambda x: x[0])
    cursor = 0
    out = bytearray(raw)
    for at, before, after in prepared:
        need(cursor <= at <= len(raw)-len(before), 'patch overlap/outside candidate')
        need(raw[at:at+len(before)] == before, 'patch preimage differs')
        out[at:at+len(after)] = after
        cursor = at+len(after)
    restored = bytearray(out)
    for at, before, after in reversed(prepared):
        need(restored[at:at+len(after)] == after, 'reverse preimage differs')
        restored[at:at+len(before)] = before
    need(bytes(restored) == raw, 'whole-ROM rollback differs')
    return bytes(out)


def apply_recipe(raw, recipe):
    need(type(recipe) is dict, 'recipe object required')
    need(identity(raw) == binding(recipe['parent']), 'parent identity differs')
    out = patch(raw, recipe['patches'])
    need(identity(out) == binding(recipe['candidate']), 'candidate identity differs')
    count = allocations(out, recipe['allocation']) if 'allocation' in recipe else 0
    reverse = [dict(offset=r['offset'], before=r['after'], after=r['before']) for r in recipe['patches']]
    need(patch(out, reverse) == raw, 'independent whole-ROM reverse differs')
    return out, dict(parent=identity(raw), candidate=identity(out), patches=len(recipe['patches']),
                     allocations=count, whole_rom_rollback_matches_parent=True)


def chain(raw, recipes, expected):
    need(type(recipes) is list and recipes, 'ordered nonempty recipe chain required')
    original, reports, seen = raw, [], {identity(raw)['sha256']}
    for recipe in recipes:
        out, report = apply_recipe(raw, recipe)
        need(report['candidate']['sha256'] not in seen, 'duplicate/cyclic candidate')
        seen.add(report['candidate']['sha256'])
        reports.append(report)
        raw = out
    need(identity(raw) == binding(expected), 'terminal candidate differs')
    restored = raw
    for recipe in reversed(recipes):
        reverse = dict(parent=recipe['candidate'], candidate=recipe['parent'],
                       patches=[dict(offset=r['offset'], before=r['after'], after=r['before']) for r in recipe['patches']])
        restored, _ = apply_recipe(restored, reverse)
    need(restored == original, 'whole-chain rollback differs')
    return raw, dict(parent=identity(original), candidate=identity(raw), layers=reports,
                     whole_chain_rollback_matches_parent=True, arm_compiles=0,
                     native_processes=0, accepted_native_cases_replayed=0)


def disassembly_bytes(text, address, expected):
    """固定objdumpのbyte欄だけ復元。推測した命令/穴埋めは一切しない。"""
    binding(expected)
    need(type(text) is str and type(address) is int and address >= 0, 'disassembly input differs')
    memory = {}
    for line in text.splitlines():
        match = re.match(r'^\s*([0-9a-fA-F]+):\s*\t([^\t]+)\t', line)
        if not match:
            continue
        at = int(match[1], 16)
        tokens = match[2].split()
        need(tokens and all(re.fullmatch(r'(?:[0-9a-fA-F]{2}|[0-9a-fA-F]{4}|[0-9a-fA-F]{8})', t) for t in tokens),
             'unrecognized disassembly byte field')
        data = b''.join(int(t, 16).to_bytes(len(t)//2, 'little') for t in tokens)
        for i, byte in enumerate(data):
            need(at+i not in memory, 'duplicate disassembly address')
            memory[at+i] = byte
    need(set(memory) == set(range(address, address+expected['size'])), 'disassembly holes/outside payload')
    out = bytes(memory[a] for a in range(address, address+expected['size']))
    need(identity(out) == expected, 'saved code digest differs')
    return out
