#!/usr/bin/env python3
"""保存中継の未読1targetだけを採取。剰余・閏年・通常取得の受入ではない。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys

BASE = 'f8fa61a0ec62cd4bfa3a32fffc9e0a93b4db30ca'
SLUG = 'pr16-ring-divmod-frontier'
TASK = 'PR-P08-7-RING-DIVMOD-FRONTIER'
TITLE = '保存中継の未読081C85A5だけを固定し再採取を防止'
SELF = 'scripts/pr16_ring_divmod_frontier.py'
TEST = 'tests/test_pr16_ring_divmod_frontier.py'
WORKFLOW = '.github/workflows/pr16-ring-divmod-frontier.yml'
PRIOR = 'content/modernization/pr16_ring_clock_contracts.json'
REPORT = 'content/modernization/pr16_ring_divmod_frontier.json'
KEY = 'latest_ring_diagnostic'
MIN_TESTS = 14
EXTRA_CODE = ()
FRONTIER = 'content/modernization/pr16_ring_branch_frontier.json'
UNREAD = 'content/modernization/pr16_ring_unread_frontier.json'
OWNERS = 'content/modernization/pr16_ring_selector_owners.json'
CALLERS = 'content/modernization/pr16_ring_record_callers.json'
RESTORE = '.github/workflows/pr16-ring-callee-bytes.yml'
SOURCES = (FRONTIER, UNREAD, OWNERS, CALLERS, RESTORE,
    'scripts/pr16_ring_zero_bytes.py', 'scripts/pr16_ring_record_callers.py',
    'scripts/pr16_ring_branch_frontier.py', 'scripts/pr16_ring_flagset_continuation.py')
NO_REPEAT = ('081C85A5の限定512byte窓は保存結果を再利用。同一candidateから再採取しない。'
    'GPIO/月表/既読ABI/mirrored探索/BPは再実行せず、保存命令の剰余・閏年契約へ進む。')
ROM_BASE, ROM_SIZE, TARGET, WINDOW = 0x08000000, 0x02000000, 0x081C85A5, 512


def need(ok, text):
    if not ok:
        raise ValueError(text)


def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def sample(raw, memory, start, length):
    """指定窓だけ照合し、既採取byteを再出力しない。入力は変更しない。"""
    need(type(raw) is bytes and 0 < len(raw) <= ROM_SIZE, 'byte入力範囲')
    need(type(start) is int and start % 2 == 0, '開始位置')
    need(type(length) is int and 0 < length <= WINDOW and length % 2 == 0, '窓上限/整列')
    need(ROM_BASE <= start < start+length <= ROM_BASE+len(raw), 'ROM範囲')
    need(type(memory) is dict, '保存memory型')
    windows, reused = [], 0
    for at in range(start, start+length):
        value = raw[at-ROM_BASE]
        if at in memory:
            need(type(memory[at]) is int and memory[at] == value, '保存byte差分')
            reused += 1
        elif windows and windows[-1][1] == at:
            windows[-1][1] += 1
        else:
            windows.append([at,at+1])
    return ([{'start':lo, 'end':hi, 'hex':raw[lo-ROM_BASE:hi-ROM_BASE].hex(),
              'identity':identity(raw[lo-ROM_BASE:hi-ROM_BASE])} for lo,hi in windows], reused)


def analyze(prior, out):
    import zlib
    import pr16_ring_followup_v2 as s
    import pr16_ring_record_callers as previous
    import pr16_ring_branch_frontier as frontier
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_zero_bytes as restore
    need(prior['analysis']['unread_external_targets'] == [TARGET]
         and prior['analysis']['thunk']['unread_tail_target'] == TARGET, '未読target差分')
    reports = {p:s.load(p) for p in (OWNERS,CALLERS,FRONTIER,UNREAD)}
    for report in reports.values():
        saved.bindings_fresh(s.ROOT, report['source_bindings'])
    memory = previous.saved_memory(reports[OWNERS])
    for path in (CALLERS,FRONTIER,UNREAD):
        frontier.add_windows(memory,reports[path]['analysis']['new_windows'])
    # 復元helperが要求するpreflightを先に作る。旧missing-preflight失敗を再発させない。
    bindings = {p:s.identity((s.ROOT/p).read_bytes()) for p in (SELF,PRIOR,*SOURCES)}
    (out/'preflight.json').write_bytes(s.stable({'head':s.cmd('git','rev-parse','HEAD'),
        'source_bindings':bindings,'only_target':TARGET,'maximum_new_bytes':WINDOW}))
    restore.OUT = out
    restore.restore()
    candidate = s.ROOT/'.local/pr16-bp-party-retention-successor/candidate.gba'
    raw = candidate.read_bytes()
    need(identity(raw) == {k:s.CANDIDATE[k] for k in ('size','sha256')}
         and f'{zlib.crc32(raw):08X}' == s.CANDIDATE['crc32'], '候補identity差分')
    windows,reused = sample(raw,memory,TARGET & ~1,WINDOW)
    need(windows, '全窓既採取: 保存原本を再利用すること')
    need(identity(candidate.read_bytes()) == identity(raw), '候補変更')
    result = {'classification':'UNREAD_SINGLE_THUNK_TARGET_BYTES_NOT_RETURN_OR_LEAP_CONTRACT',
        'candidate':copy.deepcopy(s.CANDIDATE),'target':TARGET,'window':WINDOW,
        'new_windows':windows,'new_window_bytes':sum(w['end']-w['start'] for w in windows),
        'saved_bytes_reused':reused,'old_unread_targets':copy.deepcopy(prior['analysis']['old_unread_targets']),
        'old_frontier_removed':False,'all_callers_resolved':False,'all_runtime_owners_excluded':False,
        'external_return_or_abi_proven':False,'remainder_semantics_proven':False,'leap_year_suffix_proven':False,
        'caller_pointer_size_limit_proven':False,'physical_hardware_behavior_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,
        'new_emulator_processes':0,'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0,
        'candidate_reconstructions':1,'full_rom_scans':0}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(result):
    return (f'保存中継081C85A5の未読{result["new_window_bytes"]}byteだけを固定。'
        'preflight/source/候補identityを検証し、既読GPIO/月表/BPは再実行0。剰余・ABI・閏年はまだ未受入。',
        '新規保存081C85A5命令を解析し、戻値・ABI・閏年suffixを検証する。再採取/既読GPIO/月表/BPを繰り返さない。'
        'initializer08113984のcomputed/RAM caller・pointer/size/LIMITと旧18owner、Ring正規取得・装備実戦・保存は未完。policy/Circus/P08も未受入。')


if __name__ == '__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    support.run(sys.modules[__name__])
