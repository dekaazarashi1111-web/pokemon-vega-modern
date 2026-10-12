#!/usr/bin/env python3
"""Save22から洞窟内部warp→通常Save23→独立Continueを一度だけ計測する。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_story_save23_inspect as plan
import pr16_story_save22_accept as parent
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
from pr16_story_after_maori_session import Session
from pr16_story_after_maori import need, identity, write

BASE = '7061be3216818a424204761676839e7da289e32e'
TASK = plan.TASK
OUT = ROOT/'.local/pr16-story-save23'
ART = OUT/'artifact'
CODE = {'scripts/pr16_story_save23_measure.py', 'tests/test_pr16_story_save23_measure.py',
        '.github/workflows/pr16-story-save23.yml'}
DIRECTIONS = {(0,-1):64, (1,0):16, (0,1):128, (-1,0):32}
ROUTE = [[4,6],[4,5],[5,5],[5,4],[6,4]]


def idle(o, where, xy=None, counter=22):
    need(o['map'] == where and (xy is None or o['xy'] == xy) and o['field'] is True and
         o['lock'] == 0 and o['callback2'] == parent.FIELD and o['save_counter'] == counter and
         o['party_count'] == 4 and o['rp'] == 0 and o['battle_flags'] == o['battle_outcome'] == 0 and
         o['party_sha256'] == parent.PARTY and o['live_xy'] == [x+7 for x in o['xy']],
         '同一party/RP0/無戦闘/操作可能field境界')


def direction(a, b):
    need(type(a) is list and type(b) is list and len(a) == len(b) == 2 and
         all(type(x) is int for x in a+b), 'integer adjacent xy')
    delta = b[0]-a[0], b[1]-a[1]
    need(delta in DIRECTIONS, 'one adjacent tile only')
    return DIRECTIONS[delta]


def enter_cave(session):
    idle(session.last, [1,36], [4,6])
    for index, (before, after) in enumerate(zip(ROUTE, ROUTE[1:])):
        key = direction(before, after)
        for attempt in range(3):
            o = session.step((key,8),(0,300 if index == 3 else 32))
            if index == 3 and o['map'] == [1,73]:
                break
            need(o['map'] == [1,36] and o['xy'] in (before,after), 'unexpected movement: stop without retry')
            if index != 3 or o['xy'] == before:
                idle(o,[1,36],o['xy'])
            if o['xy'] == after:
                break
        else:
            raise ValueError('bounded normal movement did not advance')
        if index < 3:
            idle(o,[1,36],after)
    # 最後の通常歩行で始まったwarpだけを完了まで待つ。方向入力は追加しない。
    for attempt in range(4):
        if o['map'] == [1,73] and o['field'] is True and o['lock'] == 0:
            break
        need(o['map'] in ([1,36],[1,73]) and o['battle_flags'] == o['battle_outcome'] == 0, 'unexpected encounter')
        o = session.step((0,300))
    idle(o,[1,73],[20,3])
    need(o['flash_sha256'] == parent.FLASH, 'warp前後に保存しない')
    return o


def ordinary_save(session):
    idle(session.last,[1,73],[20,3])
    session.step((8,2),(0,60))
    session.step(*([(128,1),(0,5)]*4), (1,2),(0,60))
    session.step((1,2),(0,60))
    session.step((1,2),(0,180))
    for attempt in range(5):
        o = session.step((0,240))
        need(o['map'] == [1,73] and o['xy'] == [20,3] and o['save_counter'] in (22,23), 'bounded Save23 only')
        if o['save_counter'] == 23 and o['field'] is True and o['lock'] == 0:
            break
    idle(o,[1,73],[20,3],23)
    need(o['flash_sha256'] != parent.FLASH, 'new ordinary save required')
    return o


def trace(folder, seed):
    # 旧trace parserは任意hashの131088byte seedを厳密照合する。旧受入caseは呼ばない。
    command = (folder/'commands.txt').read_bytes()
    parsed = parent.parent.trace((folder/'stdout.txt').read_bytes(), command, seed)
    need(not (folder/'stderr.txt').read_bytes(), 'native stderr')
    names = {p.name for p in folder.glob('screen-*.ppm')}
    need(names == {f"screen-{v['screen']:04d}.ppm" for v in parsed['screens']}, 'whole screenshot set')
    for v in parsed['screens']:
        parent.screen_bytes((folder/f"screen-{v['screen']:04d}.ppm").read_bytes(),v,blank_allowed=True)
    for o in parsed['observations']:
        need(o['live_xy'] == [x+7 for x in o['xy']], 'no unaccepted coordinate lag exception')
    return parsed


def save_boundary(before, after, cold):
    import struct
    s = parent.sectors
    need(identity(before) == plan.INPUT_SAVE and len(after) == 131088 and after == cold, 'parent and complete cold Save/RTC')
    old, ra = s.bank(before,0,22,s.LAYOUT)
    new, rb = s.bank(after,0xe000,23,s.LAYOUT)
    _, rc = s.bank(after,0,22,s.LAYOUT)
    need(before[:0xe000] == after[:0xe000], 'Save22 bank immutable')
    party_a = before[old[1]+56:old[1]+656]
    party_b = after[new[1]+56:new[1]+656]
    need(party_a == party_b and identity(party_b)['sha256'] == parent.PARTY, 'all600 party bytes unchanged')
    need(before[old[1]+52:old[1]+56] == after[new[1]+52:new[1]+56] == struct.pack('<I',4), '4 slots')
    bag_a, money_a = parent.shared.bag(before,old)
    bag_b, money_b = parent.shared.bag(after,new)
    need(bag_a == bag_b and money_a == money_b == 12296, 'all Bag/money/HM05 unchanged')
    for sid in range(5,14):
        need(before[old[sid]:old[sid]+0xff4] == after[new[sid]:new[sid]+0xff4], 'PC/S61E payload unchanged')
    fa, va = s.legacy_state(before,old)
    fb, vb = s.legacy_state(after,new)
    need(fa == fb, 'no new flags for this interior warp')
    changes = [(0x4000+i,u,v) for i,(u,v) in enumerate(zip(va,vb)) if u != v]
    need(all(k in (0x4021,0x4022,0x404d) for k,u,v in changes), 'story vars may not be fixture-unlocked')
    need(before[old[0]+0x1b] == after[new[0]+0x1b] == va[0x4e] == vb[0x4e] == 0 and
         not (fa[0x840//8]&1) and va[0x71] == vb[0x71] == 6 and va[0x72] == vb[0x72] == 1,
         'national gate and story owner preserved')
    return dict(party_bytes_preserved=600, bag_unchanged=True, money=money_b, legacy_flags_unchanged=True,
        auxiliary_var_changes=changes, national_dex_magic=0,national_var404e=0,national_flag840=0,
        story_vars={'4071':6,'4072':1},pc_and_s61e_sections_unchanged=list(range(5,14)),
        sector_checksums=len(ra)+len(rb)+len(rc), complete_save_rtc_cold_identical=True)


def restore():
    meta,z = transport.archive(plan.PARENT_ARTIFACT,plan.PARENT_RUN,plan.PARENT_ARCHIVE,plan.PARENT_HEAD)
    with z:
        manifest = json.loads(z.read('manifest.json'))
        need(len(manifest) == 121 and set(z.namelist()) == set(manifest)|{'manifest.json'}, 'exact parent membership')
        for name,binding in manifest.items():need(identity(z.read(name)) == binding,'parent byte '+name)
        for name,target,binding in [('story-fast.srm','input.srm',plan.INPUT_SAVE),
                                   ('candidate.gba','candidate.gba',plan.CANDIDATE),('runner','runner',parent.RUNNER)]:
            raw = z.read(name);need(identity(raw) == binding,'fixed '+name)
            (ART/target).write_bytes(raw);(ART/target).chmod(0o555 if name == 'runner' else 0o444)
    write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime = OUT/'runtime';runtime.mkdir()
    _,z = transport.archive(10898620034,36218655601,dict(size=102586759,
        sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name == 'ld.so' or name.startswith('lib/'):
                p=runtime/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes()) == dict(size=1968536,
        sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA')
    return runtime


def main():
    os.chdir(ROOT);h.d.current()
    need(os.environ['GITHUB_RUN_ATTEMPT'] == '1' and not OUT.exists(), 'first invocation only, no blind retry')
    state = h.source_check(); protected = h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED|CODE|plan.CODE)
    ART.mkdir(parents=True);runtime = restore();seed = (ART/'input.srm').read_bytes()
    sessions = []
    try:
        progress = Session(runtime,ART/'candidate.gba',ART/'runner',seed,ART/'progress');sessions.append(progress)
        arrival = enter_cave(progress)
        final = ordinary_save(progress)
        result_progress = progress.quit();saved = progress.save.read_bytes();(ART/'story-fast.srm').write_bytes(saved)
        cold = Session(runtime,ART/'candidate.gba',ART/'runner',saved,ART/'continue');sessions.append(cold)
        idle(cold.last,[1,73],[20,3],23)
        need(all(cold.last[k] == final[k] for k in ('facing','party_sha256','flash_sha256','ledger_sha256')), 'fresh core same persisted state')
        cold.step((0,120));idle(cold.last,[1,73],[20,3],23)
        result_cold = cold.quit();(ART/'cold.srm').write_bytes(cold.save.read_bytes())
        parsed_a = trace(ART/'progress',plan.INPUT_SAVE);parsed_b = trace(ART/'continue',identity(saved))
        boundary = save_boundary(seed,saved,cold.save.read_bytes())
        need(h.d.bindings(protected) == protected,'all accepted sources and measurement source unchanged')
        report = dict(schema_version=1,task=TASK,status='MEASURED_INTERIOR_WARP_SAVE23_AWAITING_VISUAL_RECORD',
            source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),input_save=plan.INPUT_SAVE,
            candidate=plan.CANDIDATE,output_save=identity(saved),arrival=arrival,final=final,continued=cold.last,
            progress=result_progress,independent_continue=result_cold,boundary=boundary,source_bindings=h.d.bindings(CODE|plan.CODE),
            native_processes=2,compiles=0,rom_changes=0,accepted_case_reruns=0,accepted_test_reruns=0,
            ordinary_saves=1,national_dex_unlocked=False,hm05_taught_or_used=False,full_story_accepted=False,release_ready=False,
            active_baseline_changed=False,visual_review_completed=False)
        write(ART/'measurement.json',report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as exc:
        for session in sessions:
            if not session.closed and session.process.poll() is None:
                try:session.quit()
                except Exception:session.process.terminate()
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_PRESERVE_NO_AUTOMATIC_REPLAY',exception_type=type(exc).__name__,
            native_processes=len(sessions),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes()) for p in sorted(ART.rglob('*'))
                                  if p.is_file() and p.name != 'manifest.json'})


if __name__ == '__main__':main()
