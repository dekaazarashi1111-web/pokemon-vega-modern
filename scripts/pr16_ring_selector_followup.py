#!/usr/bin/env python3
"""未観測selector/record制御変数の新規参照を採取。到達性や割当証明とは分離する。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE = 'a1d33265c6c46b53a0d351a64bb4b22eef699cbe'
SLUG = 'pr16-ring-selector-followup'
TASK = 'PR-P08-7-RING-SELECTOR-OWNERS'
TITLE = '未観測selectorとrecord制御変数の新規参照・書込候補を固定'
SELF = 'scripts/pr16_ring_selector_followup.py'
TEST = 'tests/test_pr16_ring_selector_followup.py'
WORKFLOW = '.github/workflows/pr16-ring-selector-followup.yml'
PRIOR = 'content/modernization/pr16_ring_caller_snapshot.json'
REPORT = 'content/modernization/pr16_ring_selector_owners.json'
KEY = 'ring_selector_owners'
MIN_TESTS = 12
EXTRA_CODE = ()
SOURCES = ('scripts/pr16_ring_zero_bytes.py', '.github/workflows/pr16-ring-callee-bytes.yml',
           'content/modernization/pr16_ring_snapshot_closeout.json')
NO_REPEAT = ('selector/record制御変数8件の限定literal参照採取は保存原本を再利用する。'
             '既知命令は再decodeせず、未検証のThumb解釈候補を実行可能owner/通常取得へ昇格しない。'
             '次は保存したwriter候補からselector1/2の到達条件とrecord割当契約を結合する。')
ROM_BASE = 0x08000000
GLOBALS = {'selector': 0x03005ED8, 'record_base': 0x0300202C, 'capacity': 0x03002030,
           'count': 0x0203AF10, 'limit': 0x03005EDC, 'index': 0x0203AF96,
           'save_base': 0x03005048, 'pending_id': 0x030050BC}
MAX_REFS = 2000


def literal_references(raw: bytes, targets: dict[str, int]) -> list[dict]:
    """aligned literalとPC相対LDRの一致だけを主張。code/data区別は未証明。"""
    s.need(type(raw) is bytes and len(raw) % 2 == 0, 'ROM入力型/整列')
    s.need(targets and len(set(targets.values())) == len(targets), '重複/空target')
    result = []
    for name, value in sorted(targets.items()):
        s.need(type(value) is int and 0 <= value <= 0xffffffff, 'target範囲')
        needle = struct.pack('<I', value)
        pos = raw.find(needle)
        while pos >= 0:
            if pos % 4 == 0:
                for at in range(max(0, pos-1024), pos, 2):
                    half = struct.unpack_from('<H', raw, at)[0]
                    if half & 0xf800 == 0x4800 and ((at+4) & ~3) + (half & 255)*4 == pos:
                        result.append({'global': name, 'value': value, 'site': ROM_BASE+at,
                                       'register': (half >> 8) & 7, 'literal': ROM_BASE+pos,
                                       'hex': raw[at:at+2].hex(), 'runtime_reachable': False})
                        s.need(len(result) <= MAX_REFS, '新規参照の上限超過')
            pos = raw.find(needle, pos+1)
    return sorted(result, key=lambda r: (r['site'], r['global']))


def node_bytes(value, result=None):
    """保存済みgraphの命令byte集合。先行analyze/ABI/nativeは呼ばない。"""
    result = {} if result is None else result
    if isinstance(value, dict):
        if {'address', 'size', 'hex', 'kind'} <= value.keys():
            at, size = value['address'], value['size']
            data = bytes.fromhex(value['hex'])
            s.need(type(at) is int and size in (2, 4) and len(data) == size, '保存node破損')
            for i, byte in enumerate(data):
                s.need(at+i not in result or result[at+i] == byte, '保存node矛盾')
                result[at+i] = byte
        for child in value.values():
            node_bytes(child, result)
    elif isinstance(value, list):
        for child in value:
            node_bytes(child, result)
    return result


def fresh_windows(refs, known, size):
    """前後の限定windowから既読命令byteを差し引く。既読ABIの再実行を避ける。"""
    points = set()
    for row in refs:
        if row['site'] in known:
            continue
        lo = max(ROM_BASE, row['site']-32)
        hi = min(ROM_BASE+size, row['site']+96)
        points.update(at for at in range(lo, hi, 2) if at not in known and at+1 not in known)
    s.need(len(points)*2 <= 200000, '新規windowの上限超過')
    windows = []
    for at in sorted(points):
        if windows and windows[-1][1] == at:
            windows[-1][1] += 2
        else:
            windows.append([at, at+2])
    return windows


def source_matches(root: Path):
    """対象制御変数のsource根拠のみ。過去の診断文書を自己参照しない。"""
    pattern = re.compile(r'QuestLog|QUEST_LOG|quest_log|(?:0x)?0?3005[eE][dD]8|(?:0x)?0?300202[cC]')
    allowed = {'scripts', 'overlays', 'src', 'include', 'patches', 'config'}
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
    results, bindings = [], {}
    for name in names:
        p = Path(name)
        if not p.parts or p.parts[0] not in allowed or p.suffix not in {'.c','.h','.s','.S','.py','.inc','.json','.csv'}:
            continue
        if p.name.startswith('pr16_ring_'):
            continue
        path = root/p
        s.need(not path.is_symlink(), 'source symlink')
        raw = path.read_bytes()
        s.need(len(raw) <= 12000000 and b'\0' not in raw, 'source byte上限')
        lines = raw.decode('utf-8').splitlines()
        for n, line in enumerate(lines):
            if pattern.search(line):
                results.append({'path':name, 'line':n+1,
                                'context':lines[max(0,n-2):min(len(lines),n+3)]})
                bindings[name] = s.identity(raw)
                s.need(len(results) <= 1200, 'source候補上限')
    return {'matches':results, 'source_bindings':bindings,
            'scope':'TRACKED_SELECTED_SOURCE_ONLY_NOT_ALL_UPSTREAM_OR_ROM'}


def analyze(prior, out):
    import pr16_ring_zero_bytes as restore
    a = prior['analysis']
    s.need(a['observed_calls'] == a['bound_calls'] == 8 and a['candidate'] == s.CANDIDATE, '保存観測差分')
    s.need(all(r['snapshot']['selector'] == 0 for r in a['bindings']), 'selector観測の変更')
    roots, known, evidence = s.ROOT/'content/modernization', {}, {}
    for p in sorted(roots.glob('pr16_ring*.json')):
        value = json.loads(p.read_bytes())
        if p.name == Path(REPORT).name:
            continue
        node_bytes(value, known)
        evidence[str(p.relative_to(s.ROOT))] = s.identity(p.read_bytes())
    fixed = {p:s.identity((s.ROOT/p).read_bytes()) for p in SOURCES}
    (out/'preflight.json').write_bytes(s.stable({'source_bindings':fixed,
          'purpose_ja':'未観測制御変数の参照採取のみ。既存ABI/nativeは再実行しない。'}))
    restore.OUT = out
    restore.restore()
    rom = s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = rom.read_bytes()
    s.need(s.identity(raw) == {k:s.CANDIDATE[k] for k in ('size','sha256')}
           and f'{zlib.crc32(raw):08X}' == s.CANDIDATE['crc32'], 'candidate identity差分')
    for at, byte in known.items():
        s.need(ROM_BASE <= at < ROM_BASE+len(raw) and raw[at-ROM_BASE] == byte, '保存byteとcandidate差分')
    refs = literal_references(raw, GLOBALS)
    for row in refs:
        row['previously_sampled_instruction'] = row['site'] in known
    windows = fresh_windows(refs, known, len(raw))
    excerpts = []
    for lo, hi in windows:
        data = raw[lo-ROM_BASE:hi-ROM_BASE]
        # 関数境界/到達性の証明ではなく、明示した範囲のThumb解釈候補。
        text = subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm',
            '-M','force-thumb',f'--adjust-vma={ROM_BASE}',f'--start-address={lo}',
            f'--stop-address={hi}',str(rom)], text=True, cwd=s.ROOT)
        text = '\n'.join(line for line in text.splitlines() if re.match(r'^\s*[0-9a-f]+:', line))
        excerpts.append({'start':lo,'end':hi, 'hex':data.hex(), 'identity':s.identity(data), 'thumb_interpretation':text})
    s.need(s.identity(rom.read_bytes()) == s.identity(raw), 'candidateが変化')
    result = {'classification':'UNOBSERVED_SELECTOR_GLOBAL_REFERENCES_NOT_REACHABILITY_PROOF',
        'candidate':copy.deepcopy(s.CANDIDATE), 'globals':GLOBALS,
        'literal_references':refs, 'new_reference_sites':sum(not r['previously_sampled_instruction'] for r in refs),
        'saved_references_reused':sum(r['previously_sampled_instruction'] for r in refs),
        'new_windows':excerpts, 'new_window_bytes':sum(hi-lo for lo,hi in windows),
        'saved_evidence_bindings':evidence, 'source_scan':source_matches(s.ROOT),
        'old_unread_targets':copy.deepcopy(a['old_unread_targets']), 'old_frontier_removed':False,
        'selector1_runtime_observed':False,'selector2_runtime_observed':False,
        'active_record_prefix_observed':False,'allocated_storage_extent_proven':False,
        'normal_mapping_proven':False,'synchrony_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
        'new_emulator_processes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0,'candidate_reconstructions':1}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    stop = (f'selector/record制御変数8件のliteral参照を限定採取。新規{result["new_reference_sites"]}候補、'
            f'既読{result["saved_references_reused"]}参照は保存byteを再利用し、'
            f'新規window{result["new_window_bytes"]}byteとsource一致を記録。'
            '候補復元1、native0、旧ABI/BP再実行0。Thumb解釈候補は到達性/割当証明ではない。')
    next_step = ('保存参照とsource一致からselector1/2のwriter・record_base/capacityの割当/終了ownerを結合する。'
                 '実Ring経路のcallerとIRQ/DMA条件、旧18ownerは未解決。保存8件と本工程の採取を繰り返さず、'
                 'Ring通常取得・装備実戦・通常保存を観測するまで受入へ昇格しない。policy/Circus/P08も未完。')
    return stop, next_step


if __name__ == '__main__':
    s.need(sys.argv[1:] == ['run'], 'runだけを許可')
    s.run(sys.modules[__name__])
