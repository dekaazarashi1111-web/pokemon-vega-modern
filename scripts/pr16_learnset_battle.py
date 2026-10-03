#!/usr/bin/env python3
"""保存済みBag23ケースを閉じ、習得個体fixtureの自然戦闘だけを追加検証する。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import zipfile
import zlib
import pr16_learnset_gameplay as m
from pr16_learnset_wiki_actions import current,acquire
from pr16_wiki_reconcile import fetch
ROOT=m.ROOT
WORK=ROOT/'.local/pr16-learnset-battle'
PROOF=WORK/'proof'
TASK='USER-20260923-LEARNSET-BATTLE'
RUN=35831256129
JOB=107084145752
HEAD='059826fec559df3c543dd20cc549b470418ad5dd'
REFLECTED='574975b3ea189ae37c4258c583ba5d1efb1c5d82'
ARTIFACT={'id':10736439669,'name':'pr16-learnset-gameplay-proof','size_in_bytes':599038,
          'digest':'sha256:2fb104c444440ec47a11c9d2194a512c6aeb1079036ec66ee849d2a00f19722b'}
CASE='floette-learned-420-natural-battle'
SOURCE_CASE='floette-replace-420'
CP=m.BASE+'pr16_learnset_battle_checkpoint.json'
COMPLETE=m.BASE+'pr16_learnset_gameplay_completed_actions.json'
EVIDENCE=m.BASE+'pr16_learnset_battle_evidence'
SELF='scripts/pr16_learnset_battle.py'
C='tools/mgba_pr16_learnset_battle.c'
TEST='tests/test_pr16_learnset_battle.py'
CODE=m.CODE|{'scripts/pr16_learnset_gameplay_followup.py','tests/test_pr16_learnset_gameplay_followup.py',SELF,C,TEST}
SCOPE='LEARNED_PARTY_FIXTURE_NATURAL_BATTLE_SAVE_CONTINUE'
NEXT='Issue19: Bag23ケース/32境界試験と習得技420の通常戦闘checkpointを継承し、未受入の条件付きタマゴ等の変更影響へ進む。一覧/summary画面は撮影タイミングの限定修復が必要で見た目未受入。旧Wiki/4hook/ARM/PLA1/PLC2/Bag23ケースを影響なく再実行しない。'


def write(p,v):
    Path(p).parent.mkdir(parents=True,exist_ok=True);m.write(p,v)


def zip_members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        m.need(len(names)==len(set(names)) and len(names)<400 and sum(i.file_size for i in z.infolist())<30000000,'proof ZIP bounds')
        result={}
        for i in z.infolist():
            p=Path(i.filename)
            m.need(not i.is_dir() and not p.is_absolute() and '..' not in p.parts and i.external_attr>>28!=0xa,'proof ZIP path/type')
            result[i.filename]=z.read(i)
        return result


def accepted(data):
    v=json.loads(data['verification.json']);vectors=json.loads(data['vectors.json'])['cases']
    m.need(v['status']=='PASS_SCOPED' and v['source_head']==HEAD and v['run_id']==RUN and v['candidate']==m.CANDIDATE
           and v['new_native_processes']==23 and v['fresh_cores']==46 and v['new_unit_tests']==12
           and v['inherited_unit_tests']==20 and len(v['cases'])==len(vectors)==23,'accepted Bag outcome')
    for name,expected in v['proof_bindings'].items():m.need(m.identity(data[name])==expected,'accepted member '+name)
    m.need(data['reflected-head.txt'].decode().strip()==REFLECTED,'accepted reflected commit')
    for expected,case in zip(v['cases'],vectors):
        name=case['name'];process=json.loads(data[name+'.process.json'])
        m.need(process=={'returncode':0,'timed_out':False},'accepted native process')
        m.need(m.validate_result(data[name+'.stdout.txt'],data[name+'.stderr.txt'],case)==expected,'accepted native proof projection')
    idx=next(i for i,c in enumerate(vectors) if c['name']==SOURCE_CASE)
    case=vectors[idx];m.need(idx==11 and case['species']==1029 and case['expected']==420 and case['slot']==1,'explicit learned owner/move')
    rows=re.findall(rb'^GAMEPLAY_PARTY label=continued counter=3 hex=([0-9a-f]{200})$',data[SOURCE_CASE+'.stderr.txt'],re.M)
    m.need(len(rows)==1,'accepted continued party absent')
    party=bytes.fromhex(rows[0].decode());m.need(m.identity(party)==v['cases'][idx]['party_identity'],'accepted party identity')
    return v,vectors,idx,party


def restore():
    import pr16_learnset_supply_rom as old
    old.WORK=WORK/'restore';old.WORK.mkdir()
    raw,oldlink=old.restore()
    cp=m.load(ROOT/(m.BASE+'pr16_learnset_supply_alignment_checkpoint.json'))
    m.need(cp['actions_completion_confirmed'] and cp['candidate']==m.CANDIDATE,'accepted aligned candidate')
    acquire(cp['artifacts']['aligned_data'],cp['source_head'],WORK/'aligned',cp['data_files'])
    link=m.load(WORK/'aligned/link.json');p=link['placement_repair'];image=(WORK/'aligned/supply.bin').read_bytes()
    original=(old.WORK/'link/supply.bin').read_bytes();start,end=p['repair_start'],p['repair_end_exclusive']
    m.need(m.identity(raw)==link['repair_parent'] and link['hooks']==oldlink['hooks'] and link['symbols']==oldlink['symbols'],'saved hook/parent/symbol')
    m.need(p['prefix_bytes']==4 and image==b'\xff'*4+original and end-start==len(image) and m.identity(image)==p['placed_image']
           and raw[start:start+len(original)]==original and raw[start+len(original):end]==b'\xff'*4,'saved preimage')
    rom=raw[:start]+image+raw[end:]
    m.need(m.identity(rom)==m.CANDIDATE and f'{zlib.crc32(rom):08X}'=='00F31AF7','battle exact candidate')
    (WORK/'candidate.gba').write_bytes(rom)
    return rom


def physical(rom):
    import pr16_capture_geometry as geometry
    from pr16_purchased_gear import path
    from tools.t02.rom_inventory import RomImage
    from pr16_purchased_gear import probe
    town=geometry.geometry(rom,96,5);grass=geometry.geometry(rom,96,17)
    paths={'town':path(town,[20,20],[23,0]),'grass':path(grass,[11,39],[14,30])}
    entry=probe.roots.map_entry(RomImage('fixed learnset candidate',rom),96,5)
    at=struct.unpack_from('<I',rom,entry['header']-0x08000000+12)[0]-0x08000000
    count,table=struct.unpack_from('<II',rom,at);m.need(0<count<=32,'connection count')
    links=[struct.unpack_from('<IiBB',rom,table-0x08000000+12*i) for i in range(count)]
    m.need([r for r in links if r[0]==2]==[(2,12,96,17)],'north map connection')
    m.need(any(p['start']==[14,30] and p['end']==[15,30] and p['behavior']==2 for p in grass['walkable_pairs']),'natural grass pair')
    m.need(all(1<=len(p)<=128 for p in paths.values()),'physical path bounds')
    return {'paths':paths,'connection':[2,12,96,17], 'geometry':{'town':m.identity(m.encode(town)),'grass':m.identity(m.encode(grass))}}


def fixture_header(party,index,audit):
    m.need(len(party)==100 and any(party) and index==11 and set(audit['paths'])=={'town','grass'},'fixture boundary')
    text='/* Bytes of accepted ordinary-learning Continue, initial fixture ONLY. */\n'
    text+='#define LB_ROM_SHA '+json.dumps(m.CANDIDATE['sha256'])+'\n#define LB_SEED_SHA '+json.dumps(m.SEED_ID['sha256'])+'\n#define LB_SOURCE_CASE 11\n'
    text+='static const unsigned char lb_fixture_party[100]={'+','.join(str(n) for n in party)+'};\n'
    for name,rows in audit['paths'].items():
        m.need(name in ('town','grass') and rows and all(len(p)==2 and all(type(x) is int and 0<=x<1024 for x in p) for p in rows),'fixture path shape')
        text+='static const unsigned lb_'+name+'_path[][2]={'+','.join('{%d,%d}'%tuple(p) for p in rows)+'};\n'
    return text.encode()


def validate(stdout,stderr):
    r=json.loads(stdout)
    fixed={'status':'PASS','scope':SCOPE,'candidate_sha256':m.CANDIDATE['sha256'],'species':1029,'move':420,'slot':1,
           'initial_party_fixture':True,'bag_reruns':0,'host_write_barriers':3,'fresh_cores':2,'manual_saves':1,
           'party_preserved_bytes':100,'warnings_errors':0,'story_acquisition_verified':False,'issue19_complete':False,'release_ready':False}
    for k,v in fixed.items():m.need(type(r[k]) is type(v) and r[k]==v,'battle scope/result '+k)
    ints={'enemy_species','walking_steps','boundary','encounter','selection','chosen','pp_spent','damage','returned','pp_before','pp_after','enemy_hp_before','enemy_hp_min','outcome'}
    m.need(set(r)==set(fixed)|ints and all(type(r[k]) is int for k in ints),'battle schema/counters')
    m.need(0<r['boundary']<r['encounter']<r['selection']<r['chosen']<=r['pp_spent']<r['returned']<=100000,'battle frame sequence')
    m.need(r['selection']<r['damage']<=r['returned'] and 0<r['walking_steps']<=400 and 0<r['enemy_species']<2048,'natural encounter/damage')
    m.need(0<=r['pp_after']<r['pp_before']<=64 and r['pp_before']-r['pp_after']<=2 and 0<=r['enemy_hp_min']<r['enemy_hp_before'] and r['outcome'] in (1,4),'native effect/return')
    rows=re.findall(rb'^GAMEPLAY_PARTY label=(battle_fixture|battle_returned|battle_saved|battle_continued) counter=(\d+) hex=([0-9a-f]{200})$',stderr,re.M)
    m.need([x[0] for x in rows]==[b'battle_fixture',b'battle_returned',b'battle_saved',b'battle_continued']
        and [int(x[1]) for x in rows]==[2,2,3,3],'battle Save lifecycle')
    values=[bytes.fromhex(x[2].decode()) for x in rows]
    m.need(values[0][:8]==values[1][:8] and values[1]==values[2]==values[3] and values[0]!=values[1],'individual/native change/persistence')
    return dict(r,initial_party=m.identity(values[0]),persisted_party=m.identity(values[1]))


def execute():
    current();PROOF.mkdir(parents=True,exist_ok=True)
    m.need(not (ROOT/CP).exists() or m.load(ROOT/CP)['status']=='FAIL','accepted battle rerun refused')
    report={'schema_version':1,'task':TASK,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
            'status':'RUNNING','candidate':m.CANDIDATE,'native_processes':0,'bag_reruns':0,'accepted_test_reruns':0,
            'arm_compiles':0,'wiki_generations':0,'rom_changes':0,'issue19_complete':False,'release_ready':False,
            'source_bindings':{p:m.identity((ROOT/p).read_bytes()) for p in sorted(CODE)},
            'protected_bindings':{p:m.identity((ROOT/p).read_bytes()) for p in m.PROTECTED},'next_step_ja':NEXT}
    oldproof=m.PROOF;m.PROOF=PROOF
    try:
        run=fetch('actions/runs/'+str(RUN));job=fetch('actions/jobs/'+str(JOB));meta=fetch('actions/artifacts/'+str(ARTIFACT['id']))
        m.need(run['head_sha']==HEAD and run['head_branch']==m.BRANCH and run['status']=='completed' and run['conclusion']=='success','Bag completed run')
        m.need(job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='success'
               and all(s['conclusion']=='success' for s in job['steps'] if s['number'] in (5,6,7,8)), 'Bag completed job/push/upload')
        m.need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired'] and meta['workflow_run']['head_sha']==HEAD,'Bag fixed artifact')
        raw=fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
        m.need(m.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'Bag proof archive')
        data=zip_members(raw);bag,vectors,index,party=accepted(data)
        completion={'status':'PASS_COMPLETED_ACTIONS_SCOPED_BAG_SAVE_CONTINUE','run_id':RUN,'job_id':JOB,'source_head':HEAD,'reflected_head':REFLECTED,
            'artifact':ARTIFACT,'verified_cases':23,'fresh_cores':46,'new_unit_tests':12,'inherited_unit_tests':20,'native_reruns':0,
            'candidate':m.CANDIDATE,'actions_completion_confirmed':True,'job_steps':[{k:s[k] for k in ('name','number','status','conclusion')} for s in job['steps']],
            'raw_verification':m.identity(data['verification.json']), 'fixture_party_source':{'case':SOURCE_CASE,'phase':'continued','identity':m.identity(party)},
            'screen_review':{'field_and_continue_sample':'visible normal field','summary':'16 transition frames are black; not accepted as layout evidence',
                             'list':'no state6 capture in positive cases; state4/input/list/slot evidence accepted, layout review remains pending'},
            'issue19_complete':False,'release_ready':False}
        write(PROOF/'bag-completed-actions.json',completion);report['bag_completion']=completion
        out,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_battle','-v'],'unit')
        found=re.findall(rb'Ran (\d+) tests?',err);m.need(len(found)==1 and err.rstrip().endswith(b'OK'),'new battle tests')
        report['new_unit_tests']=int(found[0]);rom=restore();audit=physical(rom);write(PROOF/'geometry.json',audit)
        generated={}
        for name,ident in bag['generated_sources'].items():
            raw=data['executed-'+name];m.need(m.identity(raw)==ident,'saved compiled helper '+name)
            (WORK/name).write_bytes(raw);generated[name]=ident
        text=(ROOT/'tools/mgba_pr16_learnset_gameplay.c').read_text();anchor='int main(int argc,char **argv)'
        m.need(text.count(anchor)==1,'unused driver main anchor')
        raw=text.replace(anchor,'int gameplay_bag_unused_main(int argc,char **argv)').encode()
        (WORK/'pr16_gameplay_driver.c').write_bytes(raw);generated['pr16_gameplay_driver.c']=m.identity(raw)
        raw=fixture_header(party,index,audit);(WORK/'pr16_learnset_battle_fixture.h').write_bytes(raw)
        generated['pr16_learnset_battle_fixture.h']=m.identity(raw)
        report['generated_sources']=generated
        exe=WORK/'runner';dep=WORK/'dependencies.d'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(exe)],'compile')
        m.need(not err,'battle compiler warnings');report['host_compiles']=1
        deps={}
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(name);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==WORK:m.need(m.identity(p.read_bytes())==generated[p.name],'generated compile dependency')
            else:deps[p.relative_to(ROOT).as_posix()]=m.identity(p.read_bytes())
        report['compiled_sources']=deps
        seed=(ROOT/m.SEED).read_bytes();m.need(m.identity(seed)==m.SEED_ID,'battle seed identity');(WORK/'fixture.srm').write_bytes(seed)
        screens=PROOF/'screens';screens.mkdir();report['native_processes']=1;write(PROOF/'verification.json',report)
        stdout,stderr=m.run([str(exe),str(WORK/'candidate.gba'),str(WORK/'fixture.srm'),m.CANDIDATE['sha256'],m.SEED_ID['sha256'],CASE,str(screens/CASE)],'battle',300)
        result=validate(stdout,stderr);m.need(result['initial_party']==m.identity(party),'native accepted fixture bytes')
        m.need(m.identity((WORK/'candidate.gba').read_bytes())==m.CANDIDATE and (ROOT/m.SEED).read_bytes()==seed,'battle inputs modified')
        m.need(report['protected_bindings']=={p:m.identity((ROOT/p).read_bytes()) for p in m.PROTECTED},'unrelated accepted source changed')
        report.update(status='PASS_SCOPED',result=result,battle_verified=True)
    except Exception as e:
        report.update(status='FAIL',error_type=type(e).__name__,error=str(e).replace(str(ROOT),'$REPO'))
        raise
    finally:
        report['proof_bindings']={p.relative_to(PROOF).as_posix():m.identity(p.read_bytes()) for p in PROOF.rglob('*') if p.is_file() and p.name!='verification.json'}
        write(PROOF/'verification.json',report);m.PROOF=oldproof


def record():
    current()
    from common import redact_user_paths,user_absolute_path_lines
    from pr16_learnset_compact_record import publish_resume
    v=m.load(PROOF/'verification.json');m.need(v['source_head']==os.environ['GITHUB_SHA'],'battle recording source')
    dest=ROOT/EVIDENCE/str(v['run_id']);m.need(not dest.exists(),'duplicate battle evidence');dest.mkdir(parents=True)
    for p in PROOF.iterdir():
        if not p.is_file():continue
        text=p.read_bytes().decode();m.need('\0' not in text,'public evidence text')
        text=re.sub(r'(GAMEPLAY_PARTY label=\w+ counter=\d+) hex=[0-9a-f]{200}',r'\1 bytes=100 [fixture bytes hashed in checkpoint]',text)
        safe='\n'.join(x.rstrip() for x in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        m.need(not user_absolute_path_lines(safe),'public user path');(dest/p.name).write_text(safe)
    v['public_evidence_path']=dest.relative_to(ROOT).as_posix();v['public_evidence_bindings']={p.name:m.identity(p.read_bytes()) for p in dest.iterdir()}
    v['actions_completion_confirmed']=False;write(ROOT/CP,v)
    if 'bag_completion' in v:
        completion=v['bag_completion'];write(ROOT/COMPLETE,completion)
        cp=m.load(ROOT/m.CP);m.need(cp['source_head']==HEAD and cp['run_id']==RUN and cp['status']=='PASS_SCOPED','Bag checkpoint mismatch')
        cp.update(actions_completion_confirmed=True,completed_actions_path=COMPLETE,completed_job_id=JOB,artifact=ARTIFACT,reflected_head=REFLECTED)
        write(ROOT/m.CP,cp)
    good=v['status']=='PASS_SCOPED'
    guide=f'# Issue19: 通常Bag・習得技戦闘・保存再開\n\n候補 `{m.CANDIDATE["sha256"]}` / CRC32 `00F31AF7`。ROM変更0。\n\n## 完了: Bag/習得/Save/Continue\n\nrun{RUN}/job{JOB} completed/success、反映 `{REFLECTED}`。23ケース・46fresh core。Floette追加12技、殿堂入り前後、raw40ページ/選択/取消、既習得除外、通常思い出し、4技/PP、100byte party、通常Save counter2→3とfresh Continueを受入。20境界試験を継承し追加12試験成功。元失敗run35830398856は履歴として保持。Task初期化前のDOWN送信を60frame待ちで修復しmode6/11技を確認。\n\n正本 `{m.CP}` / `{COMPLETE}`。初期party/進行/道具はfixtureであり、通常ストーリー取得の受入ではない。\n\n## 今回: 保存済み習得個体からの通常戦闘\n\nrun{v["run_id"]}、source `{v["source_head"]}`、状態 `{v["status"]}`。追加unit {v.get("new_unit_tests",0)}件、native {v["native_processes"]} process。正本 `{CP}`。Bag再実行0。成功時は習得済みFloette420の100byteを初期fixtureとして継承し、歩行遭遇→通常の技選択→PP消費/敵HP低下→帰還→通常Save/fresh Continueを確認。タマゴ/全owner/全技戦闘の受入ではない。Actions終端は後続の記録限定照合で確定。\n\n## 見た目の証拠の限界\n\n保存/再開のfield画像は確認。旧Bag runのsummary16画像はフェード中の黒画面で、一覧もstate4から直接進むためstate6撮影がない。実入力/nativeメニュー/文字列/100byteの証拠と、見た目の受入を混同しない。全23ケースを撮影のために再実行しない。\n\n## 次の未完\n\n{NEXT if good else "最新battle checkpointのerrorと原本を先に読み、未受入の戦闘だけ修復する。Bag23/32unit/Wiki/旧hookは再実行しない。"}\n'
    (ROOT/m.GUIDE).write_text(guide)
    state=m.load(ROOT/m.STATE)
    state['learnset_gameplay']['actions_completion_confirmed']='bag_completion' in v
    state['learnset_battle']={k:v[k] for k in ('status','source_head','run_id','candidate','native_processes','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_battle']['path']=CP
    state['observed_head']=v['source_head'];state['observed_head_semantics']='習得済み個体の自然戦闘追加検証source HEAD。反映commit/Actions終端は後続の固定照合。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[], 'reason_ja':f'Bag run{RUN} completed/success固定。新battle run{v["run_id"]}の終端未照合。'}
    state['bp']['current_stop']='Issue19候補6e88a021: Bag23/46core・32unit完了Actions照合済み。新しい通常戦闘は'+v['status']+'。'
    nextstep=NEXT if good else '最新battle checkpointのerror/原本から未完の戦闘だけ修復。Bag23/32unit/Wiki/旧4hook/ARMは再実行しない。'
    state['bp']['next_step']=nextstep
    state['next_action']=dict(state['next_action'],id='LEARNSET_BATTLE_REVIEW' if good else 'LEARNSET_BATTLE_PENDING',goal_ja=nextstep,read_paths=[m.GUIDE,CP,COMPLETE])
    state['do_not_repeat'].append(f'Bag run{RUN} completed/success固定、23ケース/46core/32unitを継承。battle run{v["run_id"]}の状態{v["status"]}と原本から次工程を判断し、無関係な受入を再実行しない。')
    for name in CODE|{CP,COMPLETE,m.CP,m.GUIDE}:
        if (ROOT/name).is_file():state['source_bindings'][name]=m.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / Bag完了Actions固定と習得技の通常戦闘\n- Version: issue19-learned-battle-6e88a021-v1\n- Status: '+('DONE（代表戦闘の区切り、全体未完）' if good else 'BLOCKED（失敗原本を保存、Bag受入は不変）')+f'\n- Summary: Bag23/46core、20+12unitをrun{RUN}/job{JOB}/artifact{ARTIFACT["id"]}へ固定し再実行0。習得個体420の初期fixtureから自然歩行遭遇・技選択・PP/ダメージ・通常Save/fresh Continueを新規実装。\n- Files changed: 新battle runner/C/試験、Actions、Bag完了JSON、battle checkpointとtext原本view、固定引継ぎMD/JSON、両ログ。\n- Verify: run{v["run_id"]}、unit {v.get("new_unit_tests",0)}件、native {v["native_processes"]}process、status {v["status"]}。旧native/Bag/Wiki/ARM再実行0、ROM変更0。summary黒画面は見た目の受入にしない。\n- Commit: 本記録commitを同branchへ非force pushしremote refを照合。自己SHAはActions reflected-head/git log参照。\n- Network: 固定GitHub run/job/artifactのみ。原本ROM/saveの新規追跡なし。全履歴private guard/Issue19全体/releaseの完了を主張しない。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as f:f.write(log)


def owned():
    return m.owned()|{CP,COMPLETE}|{p.relative_to(ROOT).as_posix() for p in (ROOT/EVIDENCE).rglob('*') if p.is_file()}


def guard():
    import pr16_learnset_runtime_record as g
    g.START,g.CODE,g.OWNED=m.START,CODE,owned();g.guard()
    subprocess.run(['git','diff','--cached','--check',m.START],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned()|CODE)))}
    m.need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|guard|paths required');actions[sys.argv[1]]()
