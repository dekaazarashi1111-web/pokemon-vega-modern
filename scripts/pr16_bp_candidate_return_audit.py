#!/usr/bin/env python3
"""固定bffdの敗北callback/scriptを有限監査。参照候補をowner確定へ昇格しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
SHA = 'bffd0b83e3724c2fba216052a3ff45afd3ab194ca2168244874746ce0e4a9e92'
SIZE = 33554432
WHITEOUT = 0x08055F65
OUT = ROOT / '.local/pr16-bp-candidate-return-audit'


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def references(raw: bytes, value: int) -> list[int]:
    """命令とデータはここでは区別しない。全byte offsetを検査する。"""
    needle = struct.pack('<I', value)
    result, at = [], 0
    while True:
        at = raw.find(needle, at)
        if at < 0:
            return result
        require(len(result) < 128, 'reference bound exceeded')
        result.append(BASE + at)
        at += 1


def literal_loads(raw: bytes, address: int) -> list[dict]:
    """Thumb-1 LDR literalのPC相対計算だけ。実行到達性は別途要求する。"""
    require(BASE <= address <= BASE + len(raw) - 4, 'literal outside input')
    if address & 3:
        return []
    rows = []
    for pc in range(max(BASE, address - 1024) & ~1, address, 2):
        insn = struct.unpack_from('<H', raw, pc - BASE)[0]
        if insn & 0xF800 == 0x4800 and ((pc + 4) & ~3) + ((insn & 255) << 2) == address:
            rows.append({'address': pc, 'register': (insn >> 8) & 7,
                         'instruction_hex': raw[pc-BASE:pc-BASE+2].hex(),
                         'literal_address': address,
                         'classification': 'ENCODED_LDR_CANDIDATE_NOT_REACHABILITY_PROOF'})
    return rows


def excerpt(raw: bytes, start: int, size: int) -> dict:
    require(type(start) is int and type(size) is int and 0 < size <= 1024, 'excerpt size')
    require(BASE <= start and start + size <= BASE + len(raw), 'excerpt outside input')
    data = raw[start-BASE:start-BASE+size]
    return {'address': start, **identity(data), 'hex': data.hex()}


def audit(raw: bytes) -> dict:
    require(identity(raw) == {'size': SIZE, 'sha256': SHA}, 'exact bffd candidate required')
    import sys
    sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
    from pr16_bp_trial_route import graph, GraphError
    magic = b'VEGAF20\0'
    at = raw.find(magic)
    require(at >= 0 and raw.find(magic, at+1) == -1, 'facility header is not unique')
    header = struct.unpack_from('<12I', raw, at+8)
    version, size, code_size, battles, candidates, selected, reward, mon_size = header[:8]
    require((version, battles, candidates, selected, reward, mon_size) == (1, 3, 6, 3, 9, 100), 'facility ABI differs')
    require(56 <= code_size < size <= 40000 and at+size <= len(raw), 'facility bounds differ')
    probe, npc, events, scripts = header[8:]
    require(all(BASE+at <= x < BASE+at+size for x in header[8:]), 'facility pointers outside owner')
    graphs, failures = {}, {}
    for name, root in {'observed_after_5d': 0x092CF669, 'facility_npc': npc}.items():
        try:
            graphs[name] = graph(raw, [root])
        except GraphError as exc:
            failures[name] = exc.detail
    require(not failures, 'rooted script decoding failed; do not resynchronize')
    # BPRJ.ldの既知symbolは、実ROMの命令一致・逆アセンブルと分けて扱う。
    symbols = {'CB2_EndTrainerBattle': 0x0807FBCC, 'CB2_WhiteOut': 0x08055F64,
               'CB2_ReturnToFieldContinueScript': 0x08056184,
               'CB2_ReturnToFieldContinueScriptPlayMapMusic': 0x080561A0,
               'SetMainCallback2': 0x08000544}
    pointers = {'CB2_WhiteOut': WHITEOUT, 'CB2_EndTrainerBattle': 0x0807FBCD,
                'CB2_ReturnToFieldContinueScript': 0x08056185,
                'CB2_ReturnToFieldContinueScriptPlayMapMusic': 0x080561A1}
    refs = {name: [{'address': p, 'literal_loads': literal_loads(raw, p)}
                   for p in references(raw, value)] for name, value in pointers.items()}
    require(refs['CB2_WhiteOut'], 'WhiteOut reference absent in fixed candidate')
    spans = {name: excerpt(raw, address, 384) for name, address in symbols.items()}
    for i, ref in enumerate(refs['CB2_WhiteOut']):
        start = max(BASE, ref['address']-512) & ~1
        spans['whiteout_reference_'+str(i)] = excerpt(raw, start, 768)
    native = sorted({row['native'] for nodes in graphs.values()
                     for node in nodes for row in node['instructions'] if 'native' in row})
    require(len(native) <= 32, 'native target bound exceeded')
    for ptr in native:
        spans['script_native_'+f'{ptr:08X}'] = excerpt(raw, ptr & ~1, 384)
    require(sum(s['size'] for s in spans.values()) <= 32768, 'bounded code budget exceeded')
    return {'schema_version': 1, 'classification': 'CANDIDATE_BYTES_READ_ONLY_NOT_NATIVE_ACCEPTANCE',
            'candidate': identity(raw), 'facility_header': excerpt(raw, BASE+at, 56),
            'symbol_addresses_from_locked_BPRJ_ld': symbols,
            'references': refs, 'script_graphs': graphs, 'native_excerpts': spans,
            'owner_resolved': False, 'owner_resolution_requires_review': True,
            'candidate_rom_changed': False, 'new_emulator_processes': 0,
            'accepted_native_cases_replayed': 0, 'native_return_fix_complete': False,
            'native_bp_earning_accepted': False, 'release_ready': False}


def run(rom: Path, out: Path) -> dict:
    require(not any(p.is_symlink() for p in (rom, *rom.parents, out, *out.parents)), 'symlink rejected')
    before = rom.read_bytes()
    report = audit(before)
    out.mkdir(parents=True, exist_ok=True)
    texts = []
    with tempfile.TemporaryDirectory() as directory:
        code = Path(directory) / 'excerpt.bin'
        for name, span in report['native_excerpts'].items():
            code.write_bytes(bytes.fromhex(span['hex']))
            text = subprocess.check_output(['arm-none-eabi-objdump', '-D', '-b', 'binary', '-m', 'arm',
                                            '-M', 'force-thumb', '--adjust-vma='+str(span['address']), str(code)], text=True)
            texts.append('\n## '+name+'\n'+text.replace(str(code), 'bounded-code-excerpt'))
    report['objdump_version'] = subprocess.check_output(['arm-none-eabi-objdump', '--version'], text=True).splitlines()[0]
    require(rom.read_bytes() == before, 'audit mutated candidate')
    (out / 'candidate-return.json').write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
    (out / 'candidate-return-disassembly.txt').write_text('\n'.join(texts))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'.local/pr16-bp-chooser-successor/candidate.gba')
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    result = run(args.rom, args.out)
    print(json.dumps({k: result[k] for k in ('classification', 'candidate', 'references', 'owner_resolved', 'new_emulator_processes')}))
