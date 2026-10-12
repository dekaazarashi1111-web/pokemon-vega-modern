#!/usr/bin/env python3
"""完了済みSave18の保存領域だけを独立照合。native/旧55試験は呼ばない。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import zipfile

TASK = 'USER-20260929-STORY-AYAME-PERSISTENCE-AUDIT'
SOURCE = '2577d253823bdca94bf3dfac0a67dea9776a6d8a'
RUN, JOB, ARTIFACT = 36522150353, 109257152262, 11012768108
ARCHIVE = dict(size=18101058, sha256='4e7a2e5d25dbf01284fdd992327971b7a0d84df2e86022ea6cefc685b2dd064b')
ROM_SHA = '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'
INPUT_SHA = '6bd7a37962e31b3c3c553a882903c766b7146f016cdf00a62036273789ab6f2a'
OUTPUT_SHA = 'dc1f690f0616affc61b6d45632924e4c81995c91c7c1939994f37bbe8527432d'
LAYOUT = [(0,3876),(0,3968),(3968,3968),(7936,3968),(11904,3776),
          (0,3968),(3968,3968),(7936,3968),(11904,3968),(15872,3968),
          (19840,3968),(23808,3968),(27776,3968),(31744,2000)]
TABLE_SHA = '1a5540bb6f62693af40e6c8375199a9bd4d148f71188277eb7b19a3696733c24'
STEPS = ['Set up job','Run actions/checkout@v4','New Save18 interval and independent Continue only',
         'Lightweight task graph','Run actions/upload-artifact@v4','Post Run actions/checkout@v4','Complete job']


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def checksum(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 0xff4 and len(raw) % 4 == 0, 'checksum対象の長さ')
    total = sum(struct.unpack('<'+'I'*(len(raw)//4), raw)) & 0xffffffff
    return ((total >> 16) + (total & 0xffff)) & 0xffff


def layout_table(raw):
    need(type(raw) is bytes and len(raw) == 56, 'ROM section table全56bytes')
    words = struct.unpack('<28H', raw)
    rows = list(zip(words[::2],words[1::2]))
    need(rows == LAYOUT, '現候補のstock section配置。S61EをPC長へ含めない')
    return rows


def bank(raw, offset, counter, layout):
    need(type(raw) is bytes and len(raw) == 131088 and type(offset) is int and offset in (0,0xe000)
         and type(counter) is int and 0 <= counter <= 0xffffffff and layout == LAYOUT, '完全Saveとbank条件')
    table, report = {}, []
    for pos in range(offset,offset+0xe000,0x1000):
        sid, stored, signature, found_counter = struct.unpack_from('<HHII',raw,pos+0xff4)
        need(sid not in table and sid < 14 and signature == 0x08012025 and found_counter == counter,
             '一意section/署名/世代。部分書込みを成功にしない')
        size = layout[sid][1]
        calculated = checksum(raw[pos:pos+size])
        need(stored == calculated, 'ROM宣言payload checksum不一致')
        table[sid] = pos
        report.append(dict(section=sid,physical_offset=pos,payload_bytes=size,checksum=stored,counter=counter))
    need(set(table) == set(range(14)), '全14section')
    return table, report


def trainer_mapping(raw):
    need(type(raw) is bytes and len(raw) == 372*4, 'trainer remap全372行')
    words = struct.unpack('<744H',raw)
    rows = list(zip(words[::2],words[1::2]))
    need(rows == sorted(rows) and len(dict(rows)) == 372, '一意昇順のexternal→physical表')
    mapping = dict(rows)
    result = [(t,t+0x500,mapping.get(t+0x500,t+0x500)) for t in (1,1200,1203)]
    need(result == [(1,0x501,0x501),(1200,0x9b0,0x63d),(1203,0x9b3,0x63f)], '三兄弟の実physical flag対応')
    return result


def legacy_state(raw, table):
    # ROM table: section1はSaveBlock1+0、section2は+0xF80。
    flags = raw[table[1]+0xee0:table[1]+0xf80]+raw[table[2]:table[2]+0x80]
    variables = struct.unpack_from('<256H',raw,table[2]+0x80)
    need(len(flags) == 0x120, 'legacy bitmapの跨section境界')
    return flags, variables


def state_delta(old, new):
    fa, va = old
    fb, vb = new
    need(type(fa) is bytes and type(fb) is bytes and len(fa) == len(fb) == 0x120 and
         len(va) == len(vb) == 256 and all(type(v) is int for v in (*va,*vb)), '全legacy flags/vars')
    flags = [(8*i+j,(u>>j)&1,(v>>j)&1) for i,(u,v) in enumerate(zip(fa,fb))
             for j in range(8) if (u^v)&(1<<j)]
    variables = [(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u != v]
    need(flags == [(0x501,0,1),(0x63d,0,1),(0x63f,0,1)], '勝利3flagsのみ、他legacy flag保持')
    need(variables == [(0x4021,93,5),(0x4022,1,2),(0x404d,0,8),(0x4071,1,3)], '保存var差分全4件')
    need(va[0x4e] == vb[0x4e] == va[0x72] == vb[0x72] == 0 and
         fa[0x840//8] & 1 == fb[0x840//8] & 1 == 0, '全国図鑑var404E/flag840と後続4072は未解禁')
    return dict(physical_flag_deltas=flags,legacy_var_deltas=variables,gate_var4071=[1,3],
                national_var404e=0,national_flag840=0,later_story_var4072=0,
                auxiliary_vars_owner_claimed=False,legacy_namespace_runtime_abi_retested=False)


def terminal(run, jobs):
    need(run.get('id') == RUN and run.get('head_sha') == SOURCE and
         run.get('head_branch') == 'codex/modernization-followup-20260908' and
         run.get('path') == '.github/workflows/pr16-story-ayame.yml' and
         type(run.get('run_attempt')) is int and run['run_attempt'] == 1 and
         run.get('status') == 'completed' and run.get('conclusion') == 'success', '固定完了run')
    need(type(jobs.get('total_count')) is int and jobs['total_count'] == 1 and len(jobs.get('jobs',[])) == 1,
         'job一覧の完全性')
    job = jobs['jobs'][0]
    need(job.get('id') == JOB and job.get('run_id') == RUN and job.get('name') == 'continuation' and
         job.get('status') == 'completed' and job.get('conclusion') == 'success', '固定完了job')
    need([s.get('name') for s in job.get('steps',[])] == STEPS and
         all(s.get('status') == 'completed' and s.get('conclusion') == 'success' for s in job['steps']),
         'upload/post/Completeまで全7step成功')
    return dict(run={k:run[k] for k in ('id','head_sha','head_branch','path','status','conclusion','run_attempt')},
                job={k:job[k] for k in ('id','run_id','name','status','conclusion','steps')})


def audit(z):
    manifest = json.loads(z.read('manifest.json'))
    need(len(manifest) == 170 and len(z.namelist()) == 171 and
         set(z.namelist()) == set(manifest)|{'manifest.json'}, '全170member、重複も拒否')
    for name, binding in manifest.items():
        need(identity(z.read(name)) == binding, 'member全byte: '+name)
    rom, before, after, cold = [z.read(n) for n in ('candidate.gba','input.srm','story-fast.srm','cold.srm')]
    for raw, size, sha in ((rom,33554432,ROM_SHA),(before,131088,INPUT_SHA),(after,131088,OUTPUT_SHA)):
        need(identity(raw) == dict(size=size,sha256=sha), '別Save/別ROMを正式原本へ混ぜない')
    need(after == cold, '独立Continue後の全Save/RTC一致')
    pointer, = struct.unpack_from('<I',rom,0xdb224)
    need(pointer == 0x083c4b28, '実ROMのsection table pointer')
    layout = layout_table(rom[pointer-0x08000000:pointer-0x08000000+56])
    reports, tables = {}, {}
    for name, raw, offset, counter in [('input16',before,0,16),('input17',before,0xe000,17),
                                      ('output18',after,0,18),('output17',after,0xe000,17)]:
        tables[name], reports[name] = bank(raw,offset,counter,layout)
    need(before[0xe000:0x1c000] == after[0xe000:0x1c000], '前世代bank全57344bytesを保持')
    remap = rom[0x1303ca8:0x1303ca8+1488]
    need(identity(remap)['sha256'] == TABLE_SHA, '現候補のremap table全byte')
    mapping = trainer_mapping(remap)
    delta = state_delta(legacy_state(before,tables['input17']),legacy_state(after,tables['output18']))
    need(before[tables['input17'][0]+0x1b] == after[tables['output18'][0]+0x1b] == 0, '全国図鑑magic0')
    original = json.loads(z.read('verification.json'))
    need(original['rom_owners']['trainer_references'] == [[1,3],[1200,3],[1203,3]] and
         original['rom_owners']['condition_variable'] == 0x4071 and
         original['rom_owners']['completion_value'] == 3 and original['output_save']['sha256'] == OUTPUT_SHA,
         '既存の実map root/完了var原本へ結合。旧owner走査は再実行しない')
    measured = json.loads(z.read('measurement.json'))
    need(measured['run_id'] == RUN and measured['source_head'] == SOURCE and measured['result'] == original,
         '測定source/resultの一致')
    for suffix, count in [('chain',25),('accept',30)]:
        unit = z.read('unit-'+suffix+'.stderr.txt')
        need(not z.read('unit-'+suffix+'.stdout.txt') and unit.count(b' ... ok\n') == count and b'\nOK\n' in unit
             and b'FAILED' not in unit and b'skipped' not in unit, '旧試験は完了原本のみ再利用')
    return dict(status='PASS_AYAME_SAVE18_PERSISTENCE_AUDIT',source_head=SOURCE,run_id=RUN,artifact_id=ARTIFACT,
        input_save=identity(before),output_save=identity(after),verified_manifest_members=170,
        sector_checksum_checks=56,checksum_scope='ROM宣言payloadのみ。S61E/padding/RTCをstock checksumに含めない。',
        bank_reports=reports,trainer_mapping=mapping,trainer_mapping_scope='既存map root ID→現ROM表→保存physical bit。新規call-path実行ではない。',
        saved_state=delta,previous_bank_preserved_bytes=57344,all_save_rtc_equal_after_continue=True,
        prior_tests_reused=55,prior_test_reruns=0,native_processes=0,compile_count=0,host_writes=0,
        evolution_accepted=False,full_story_accepted=False,release_ready=False,active_baseline_changed=False)


if __name__ == '__main__':
    import sys
    need(len(sys.argv) == 2, '既存Actions artifact ZIPを指定')
    raw = Path(sys.argv[1]).read_bytes()
    need(identity(raw) == ARCHIVE, '外側artifact全byte hash')
    with zipfile.ZipFile(sys.argv[1]) as z:
        print(json.dumps(audit(z),ensure_ascii=False,indent=2))
