#!/usr/bin/env python3
"""保存ELFの実load配置だけ修復し、未受入4hookを検証・記録する。"""
from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_supply_rom as m
import pr16_learnset_supply_rom_followup as f
from pr16_supply_elf_placement import repair
from pr16_learnset_floette_verify import download
from pr16_wiki_reconcile import fetch
START='f88f6b395afd2cfddcce26abd9903ecc1450fbd2'
LOCK=m.BASE+'pr16_learnset_supply_alignment_inputs.json'
CP=m.BASE+'pr16_learnset_supply_alignment_checkpoint.json'
CODE={LOCK,'scripts/pr16_supply_elf_placement.py','tests/test_pr16_supply_elf_placement.py',
      'scripts/pr16_learnset_supply_rom_alignment.py','.github/workflows/pr16-learnset-supply-rom.yml'}
SOURCE=CODE | m.CODE | f.CODE
OLD=dict(m.CANDIDATE)


def previous_failure():
    lock=m.load(ROOT/LOCK)
    run=fetch('actions/runs/'+str(lock['run_id']))
    m.need(run['status']=='completed' and run['conclusion']=='failure'
           and run['head_sha']==lock['source_head'] and run['path']=='.github/workflows/pr16-learnset-supply-rom.yml',
           'latest failure identity')
    saved=m.WORK/'third-failure'
    download(lock['artifact'],lock['source_head'],saved,lock['members'])
    failure=m.load(saved/'failure.json')
    trace=(saved/'native11.stderr.txt').read_bytes()
    m.need(failure['status']=='FAIL' and failure['source_head']==lock['source_head']
           and failure['run_id']==str(lock['run_id']) and 'supply timeout' in failure['error']
           and b'pc=09fff60a' in trace and b'fn=091141d5' in trace, 'saved failure boundary')
    for name in lock['members']:
        (m.PROOF/('trace-failure-'+name)).write_bytes((saved/name).read_bytes())
    m.write(m.PROOF/'failed-predecessor.json',dict(lock,whole_run_conclusion='failure',rerun=False))
    return lock


def verify():
    from pr16_learnset_payload_verify import current_pr
    from pr16_learnset_supply_rom_inputs import inherited
    current_pr(os.environ['GITHUB_SHA'])
    m.need(not (ROOT/m.CP).exists() and not (ROOT/CP).exists(),'accepted scope must not be rerun')
    m.WORK.mkdir(parents=True);m.PROOF.mkdir()
    before={n:m.identity((ROOT/n).read_bytes()) for n in SOURCE}
    failure=previous_failure()
    inherited14=inherited(m.PROOF)
    f.inherit()
    m.command([sys.executable,'-B','-m','unittest','tests.test_pr16_supply_elf_placement','-v'],'placement-unit')
    candidate,link=m.restore()
    bindings=f.abi(candidate,link);count=f.samples(bindings)
    old_header=(m.WORK/'pr16_supply_samples.h').read_bytes()
    old_manifest=m.load(m.PROOF/'fixture-manifest.json')
    old_abi=m.load(m.PROOF/'abi.json')
    raw=(m.WORK/'link/supply.bin').read_bytes();elf=(m.WORK/'link/supply.elf').read_bytes()
    first=repair(candidate,link,elf,raw)
    second=repair(candidate,link,elf,raw)
    m.need(first==second,'independent placement repair differs')
    out,newlink,image=first
    m.need(newlink['placement_repair']['prefix_bytes']==4 and len(image)==2788
           and m.identity(image)['sha256']=='14b2e916522ce3cda1e624676edf5f73e95e1da045bcaa14ed1a24be78ba95aa',
           'locked ELF padding result')
    m.CANDIDATE=m.identity(out)
    (m.WORK/'candidate.gba').write_bytes(out)
    aligned=m.WORK/'aligned';aligned.mkdir()
    (aligned/'supply.bin').write_bytes(image)
    for name in ('archive-image.bin','supply.elf','disassembly.txt','original_tutor.S','pr16_learnset_supply_bindings.h'):
        (aligned/name).write_bytes((m.WORK/'link'/name).read_bytes())
    m.write(aligned/'link.json',newlink)
    m.write(m.PROOF/'alignment-link.json',newlink)
    m.write(m.PROOF/'placement.json',newlink['placement_repair'])
    # 原本26owner行を再採取しない。受入headerのcode_endだけを延長する。
    before_macro=('#define PR16_CODE_END '+hex(bindings['PR16_CODE_END'])+'U').encode()
    bindings=dict(bindings,PR16_CODE_END=newlink['code_end'])
    after_macro=('#define PR16_CODE_END '+hex(bindings['PR16_CODE_END'])+'U').encode()
    m.need(old_header.count(before_macro)==1,'fixture code-end binding')
    header=old_header.replace(before_macro,after_macro)
    (m.WORK/'pr16_supply_samples.h').write_bytes(header)
    manifest=dict(old_manifest,candidate=m.CANDIDATE,header=m.identity(header),
                  inherited_candidate=OLD,inherited_header=old_manifest['header'],original_owner_rows_unchanged=True)
    m.write(m.PROOF/'fixture-manifest.json',manifest)
    m.write(m.PROOF/'abi.json',dict(old_abi,bindings=bindings,candidate=m.CANDIDATE,inherited_candidate=OLD))
    binary=m.WORK/'native'
    m.command(['cc','-std=c11','-O2','-g','-fsanitize=address,undefined','-Wall','-Wextra','-Werror','-Itools','-I'+str(m.WORK),
               'tools/mgba_pr16_learnset_supply.c','-lmgba','-o',str(binary)],'native-compile')
    results=[]
    for seed,order in ((11,'forward'),(29,'reverse')):
        output=m.command([str(binary),str(m.WORK/'candidate.gba'),m.CANDIDATE['sha256'],order],f'native{seed}',
                         dict(os.environ,ASAN_OPTIONS='detect_leaks=0:abort_on_error=1'))
        value=m.validate_native(json.loads(output),count)
        m.write(m.PROOF/f'native{seed}.json',value);results.append(value)
    m.need(results[0]==results[1],'independent forward/reverse result mismatch')
    m.need(m.identity((m.WORK/'candidate.gba').read_bytes())==m.CANDIDATE
           and before=={n:m.identity((ROOT/n).read_bytes()) for n in SOURCE},'input mutated')
    m.command(['git','diff','--exit-code'],'tracked-diff')
    v={'status':m.STATUS,'scope':m.SCOPE,'task':m.TASK,'source_head':os.environ['GITHUB_SHA'],
       'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'candidate_crc32':newlink['candidate_crc32'],
       'parent_candidate':OLD,'samples':count,'native_processes':2,'native_results':results,'source_bindings':before,
       'inherited_unit':inherited14,'inherited_input_unit':m.load(m.PROOF/'inherited-input-unit.json'),
       'failed_predecessor':failure,'placement_repair':newlink['placement_repair'],
       'new_tests':16,'inherited_tests':24,'new_host_compiles':1,'new_arm_compiles':0,'new_arm_links':0,
       'accepted_tests_rerun':0,'accepted_native_reruns':0,'accepted_payload_regenerations':0,
       'accepted_source_regenerations':0,'original_fixture_regenerations':0,'elf_archives_downloaded':0,
       'placement_reproductions':2,'independent_placement_results_equal':True,
       'tested_candidate_unchanged':True,'independent_process_results_equal':True,
       'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
       'active_baseline_changed':False,'release_ready':False,
       'data_files':{p.name:m.identity(p.read_bytes()) for p in aligned.iterdir()},
       'proof_bindings':{p.name:m.identity(p.read_bytes()) for p in m.PROOF.iterdir()}}
    m.write(m.PROOF/'verification.json',v)
    print(json.dumps({'status':m.STATUS,'candidate':m.CANDIDATE,'run_id':v['run_id'],'samples':count,'native_processes':2}))


def record():
    from pr16_learnset_compact_record import publish_resume
    from pr16_resume import pending_ids
    m.need(not (ROOT/m.CP).exists() and not (ROOT/CP).exists() and not (ROOT/m.EVIDENCE).exists(),'duplicate record')
    v=m.load(m.PROOF/'verification.json');m.CANDIDATE=v['candidate']
    m.need(v['source_head']==os.environ['GITHUB_SHA'] and v['run_id']==int(os.environ['GITHUB_RUN_ID'])
           and v['native_processes']==2 and v['parent_candidate']==OLD,'record source/run')
    m.need(set(v['proof_bindings'])=={p.name for p in m.PROOF.iterdir()}-{'verification.json'},'proof set')
    for name,binding in v['proof_bindings'].items():m.need(m.identity((m.PROOF/name).read_bytes())==binding,'proof hash '+name)
    for name,binding in v['source_bindings'].items():m.need(m.identity((ROOT/name).read_bytes())==binding,'source hash '+name)
    for result in v['native_results']:m.validate_native(result,v['samples'])
    m.need(v['native_results'][0]==v['native_results'][1],'native mismatch')
    state=m.load(ROOT/m.STATE);bp=m.load(ROOT/(m.BASE+'pr16_bp_chooser_checkpoint.json'))
    m.need(pending_ids(m.load(ROOT/(m.BASE+'p08_remaining_work.json')))==(state['remaining_physical_gap_ids'],state['remaining_p08_gate_ids'])
           and bp['accepted_case_count']==3 and not state['pr_merged'] and not state['release_ready'],'BP/P08 boundary')
    (ROOT/m.EVIDENCE).mkdir()
    for p in m.PROOF.iterdir():
        raw=p.read_bytes();raw.decode('utf-8');m.need(b'\0' not in raw,'binary proof forbidden')
        (ROOT/m.EVIDENCE/p.name).write_bytes(raw)
    checkpoint={'status':'ACCEPTED_NEW_SUPPLY_ROM_ABI_GAMEPLAY_PENDING','verification':v,'candidate':v['candidate'],
                'source_head':v['source_head'],'run_id':v['run_id'],'placement_checkpoint':CP,
                'proof_bindings':{p.name:m.identity(p.read_bytes()) for p in m.PROOF.iterdir()},
                'actions_completion':'VERIFY_AND_GUARDS_REQUIRED_BEFORE_NONFORCE_PUSH; inspect completed run separately',
                'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,'release_ready':False}
    m.write(ROOT/m.CP,checkpoint)
    alignment={'status':'ACCEPTED_ELF_PLACEMENT_REPAIR_AND_DIRECT_ROM_ABI','candidate':v['candidate'],
               'candidate_crc32':v['candidate_crc32'],'parent_candidate':OLD,'source_head':v['source_head'],'run_id':v['run_id'],
               'historical_link_checkpoint':m.LINK,'historical_link_runtime_usable':False,
               'historical_link_evidence_unchanged':True,'failed_predecessor':v['failed_predecessor'],
               'link':m.load(m.PROOF/'alignment-link.json'),'data_files':v['data_files'],
               'reconstruction':'Restore historical candidate with locked artifacts, then pr16_supply_elf_placement.repair using saved supply.elf and supply.bin; no compilation.',
               'native_checkpoint':m.CP,'physical_supply_verified':False,'gameplay_e2e_accepted':False,
               'issue19_complete':False,'release_ready':False,'active_baseline_changed':False}
    m.write(ROOT/CP,alignment)
    short=v['candidate']['sha256'][:8];calls=sum(r['calls'] for r in v['native_results'])
    stop=f'ELF実loadとROM配置の4byteずれを保存ELFから修復し後継{short}を独立2配置一致で確定。新供給4hookを{v["samples"]}代表owner×独立2process、合計{calls}callで検証。特殊Tutor/HoF/raw40ページ/既習得除外/タマゴ/選択境界/保存4技PPを確認。直接ROM診断のみで通常操作・新Wiki・物理供給は未完。'
    goal=f'Issue19: 修復後候補{short}の{CP}から保存ELF配置を復元し、別候補Wikiと変更影響の通常操作（Bag入口・殿堂入りgate・40行ページ選択/取消・習得選択・戦闘・Save/Continue）へ進む。旧ec5992aaは配置ずれがあるため現役候補へ戻さない。新4hook直接診断/16配置試験/旧24試験/ARM/PLA1/PLC2を変更影響なしに再実行しない。'
    state['learnset_supply_native']={k:checkpoint[k] for k in ('status','candidate','source_head','run_id','physical_supply_verified','gameplay_e2e_accepted','issue19_complete','release_ready')}
    state['learnset_supply_native'].update(path=m.CP,placement_checkpoint=CP,scope=m.SCOPE,samples=v['samples'],native_processes=2,calls=calls)
    state['learnset_supply_alignment']={k:alignment[k] for k in ('status','candidate','parent_candidate','source_head','run_id','historical_link_runtime_usable')}
    state['learnset_supply_alignment']['path']=CP
    state['next_action']=dict(state['next_action'],id='LEARNSET_SUPPLY_WIKI_AND_GAMEPLAY',goal_ja=goal,
        read_paths=[m.GUIDE,CP,m.CP,'scripts/pr16_supply_elf_placement.py','scripts/pr16_learnset_supply_rom_alignment.py'])
    state['bp']['next_step']=goal;state['bp']['current_stop']=stop
    state['do_not_repeat'].append(f'run{v["run_id"]}: {short}の新4hook/{calls}call/2processと新16配置試験を受入。旧14+10試験は保存原本を継承し再実行0。run35738895606の失敗原本は保持。次は新Wiki/通常操作のみ。')
    state['logs_synchronized']=True
    publish_resume(state)
    prior=(ROOT/m.GUIDE).read_text(encoding='utf-8')
    guide='# Issue19: ELF配置修復と新供給4hookの実ROM ABI受入\n\n'+stop+'\n\n'
    guide+=f'候補 `{v["candidate"]["sha256"]}` / 33554432 bytes / CRC32 `{v["candidate_crc32"]}`。run{v["run_id"]}、入力HEAD `{v["source_head"]}`。\n\n'
    guide+=f'正本 `{CP}` / `{m.CP}`。旧ec5992aaの独立2link結果は履歴として保持するが、実load不整合のため実行可能な現役候補とは扱わない。旧builderは固定証拠復元専用。先頭FF4bytesを補い、元ELF命令/全hook/PLA1/PLC2は不変。ARM再compile/link0。\n\n## 次工程\n\n'+goal+'\n\n## 前段階（履歴・現役候補ではない）\n\n'+prior
    (ROOT/m.GUIDE).write_text(guide,encoding='utf-8')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {m.TASK} / ELF実load配置修復・新供給4hook受入\n- Version: learnset-supply-alignment-v1\n- Status: DONE（配置と直接ROM ABI限定。通常操作/Wikiは未完）\n- Summary: {stop}\n- Files changed: 配置修復器/16拒否試験/限定Actions、失敗入力lock、後継配置/native checkpoint/証拠、固定MD/JSON、guide、両ログ。\n- Verify: run{v["run_id"]}、新16試験PASS、保存ELFの独立2配置一致、ASan/UBSan host compileと前後逆順2process一致。原本26owner行再採取0、旧14+10試験再実行0、ARM/PLA1/PLC2/受入native再実行0。差分は供給ARM配置2788bytes内限定・全hook不変。resume/task graph/final index guard PASS後のみcommit。全履歴guard PASSは主張しない。\n- Commit: 同branch非forceの本記録commit（自己SHAはgit logで照合）。WIP 1f71e563f8ab9c72b1f6a7756ef395e63c09a7a5に続く完了記録。\n- Network: GitHub固定run/artifactとUbuntu libmgba-devのみ。旧失敗を保持。merge/release/baseline切替なし。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream:stream.write(log)
    print(json.dumps({'status':checkpoint['status'],'run_id':v['run_id'],'candidate':v['candidate']}))


def owned():
    return {CP,m.CP,m.STATE,m.DOC,m.GUIDE,'design/run_log.md','design/version_log.md'} | {
        m.EVIDENCE+'/'+p.name for p in (ROOT/m.EVIDENCE).iterdir()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=START,CODE,owned();g.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'verify':verify,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_rom_alignment.py verify|record|guard|paths')
    try:actions[sys.argv[1]]()
    except Exception as exc:
        m.PROOF.mkdir(parents=True,exist_ok=True)
        m.write(m.PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
