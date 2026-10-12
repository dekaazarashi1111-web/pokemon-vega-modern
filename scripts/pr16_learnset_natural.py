#!/usr/bin/env python3
"""Issue19: 固定原本・保存候補を使う自然野生生成/戦闘EXPの限定受入。"""
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
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_learnset_progression as p
m = p.m
need, identity, load, write = m.need, m.identity, m.load, m.write
TASK = 'USER-20260925-LEARNSET-NATURAL'
SELF = 'scripts/pr16_learnset_natural.py'
C = 'tools/mgba_pr16_learnset_natural.c'
TEST = 'tests/test_pr16_learnset_natural.py'
WF = '.github/workflows/pr16-learnset-natural.yml'
CODE = {SELF, C, TEST, WF}
CP = m.BASE+'pr16_learnset_natural_checkpoint.json'
GUIDE = 'docs/PR16_LEARNSET_NATURAL_JA.md'
EVIDENCE = m.BASE+'pr16_learnset_natural_evidence'
WORK = ROOT/'.local/pr16-learnset-natural'
PROOF = WORK/'proof'
CASE = 'wild-initial-butterfree-exp-empty'
CANDIDATE = {'size':33554432, 'sha256':'8946438bc37fda468c53e41378a6f82fac8f0b1af7ac6785ef07ca708c2714a1'}
NEXT = 'Issue19: 自然野生初期技/戦闘EXP空き枠の保存成功は再実行しない。未受入の戦闘EXP置換/拒否/既習得/複数level・進化/EXP共有、自然配布/孵化/固定form初期技を変更影響台帳と照合して限定追加する。通常アメ11/Bag23/旧戦闘/egg8/旧host/ARM/Wiki/原本再採取は不要。全owner/Issue19/release/baseline切替は未完。'


def initial(rows, level):
    need(type(level) is int and 1 <= level <= 100, 'initial level bounds')
    need(isinstance(rows, list) and len(rows) <= 128, 'bounded original rows')
    need(all(isinstance(r, (tuple,list)) and len(r)==2 and type(r[0]) is int and type(r[1]) is int
             and 0 < r[0] < 1063 and 1 <= r[1] <= 100 for r in rows), 'original row bounds')
    need(all(a[1] <= b[1] for a,b in zip(rows,rows[1:])), 'original row order')
    # PLR1 takes the last four raw eligible rows; GiveMove drops duplicates AFTER this window.
    window = [mid for mid,lv in rows if lv <= level][-4:]
    unique = list(dict.fromkeys(window))
    return unique+[0]*(4-len(unique))


def sources(folder):
    cp = load(ROOT/m.BASE/'pr16_learnset_payload_checkpoint.json')
    data = {}
    for name in ('consumer-index.jsonl','level_up.bin'):
        raw=(folder/name).read_bytes();need(identity(raw)==cp['summary']['files'][name], 'locked payload '+name);data[name]=raw
    result={}
    for line in data['consumer-index.jsonl'].splitlines():
        row=json.loads(line)
        if row['consumer']!='level_up' or row['status']!='PAYLOAD_PREPARED_NOT_INSTALLED':continue
        sid=row['species_id'];span=row['payload']
        need(type(sid) is int and 0<sid<1671 and sid not in result,'unique selected original owner')
        need(span['file']=='level_up.bin','level source file');at,size=span['offset'],span['size']
        need(type(at) is int and type(size) is int and 0<=at<at+size<=len(data['level_up.bin']),'source span bounds')
        result[sid]=p.decode_span(data['level_up.bin'][at:at+size],'level_up');initial(result[sid],100)
    need(result[414]==p.LEVELS[414] and [mid for mid,lv in result[414] if lv==44]==[497], 'Butterfree original Lv44')
    return result,{'payload_source_head':cp['source_head'],'payload_artifact':cp['payload_artifact'],
                   'files':{n:identity(v) for n,v in data.items()},'prepared_owners_not_native_accepted':len(result)}


def header(rows, pp, geometry):
    arr=lambda values:'{'+','.join(map(str,values))+'}'
    starts=[0]*1671;counts=[0]*1671;flat=[]
    for sid,values in sorted(rows.items()):
        starts[sid]=len(flat);counts[sid]=len(values);flat.extend(values)
    text='#define N_ROM_SHA '+json.dumps(CANDIDATE['sha256'])+'\n#define N_SEED_SHA '+json.dumps(m.SEED_ID['sha256'])+'\n'
    text+='static const unsigned n_rows[][2]={'+','.join(arr(v) for v in flat)+'};\n'
    for name,values in [('start',starts),('count',counts),('pp',pp)]:text+='static const unsigned n_'+name+'[]='+arr(values)+';\n'
    for name,path in geometry['paths'].items():
        need(name in ('town','grass') and 1<=len(path)<=128 and all(len(x)==2 and all(type(v) is int and 0<=v<1024 for v in x) for x in path),'physical path')
        text+='static const unsigned lb_'+name+'_path[][2]={'+','.join(arr(x) for x in path)+'};\n'
    return text


def validate(out, err, rows, pp):
    r=json.loads(out,object_pairs_hook=p.strict)
    fixed={'schema_version':1,'status':'PASS','case':CASE,'candidate_sha256':CANDIDATE['sha256'],
           'level_before':43,'level_after':44,'guarded_phases':3,'denied_host_write_apis':7,'fresh_cores':2,
           'save_counters':[2,3,3],'party_preserved_bytes':100,'initial_party_exp_stats_progress_are_fixtures':True,
           'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    integers={'enemy_species','enemy_level','xp_before','xp_threshold','xp_after','boundary','encounter','pp_spent','level_frame','returned','turns','walking_steps','enemy_hp_before','enemy_hp_min','outcome'}
    arrays={'enemy_moves','enemy_pp','moves_after','pp_after'}
    need(set(r)==set(fixed)|integers|arrays,'native exact schema')
    for key,value in fixed.items():need(type(r[key]) is type(value) and r[key]==value,'native field '+key)
    need(all(type(r[k]) is int for k in integers),'native integer types')
    need(all(isinstance(r[k],list) and len(r[k])==4 and all(type(x) is int for x in r[k]) for k in arrays),'native four slots')
    need(r['enemy_species'] in rows,'natural owner not in locked source')
    wanted=initial(rows[r['enemy_species']],r['enemy_level'])
    need(r['enemy_moves']==wanted and r['enemy_pp']==[pp[x] for x in wanted],'natural initial moves/PP')
    need(r['moves_after']==[53,89,497,0] and r['pp_after'][1:]==[pp[89],pp[497],0],'EXP learned source move/PP')
    need(1<=r['turns']<=8 and 0<=r['pp_after'][0]<pp[53] and pp[53]-r['pp_after'][0]<=2*r['turns'],'native spent PP')
    need(0<r['boundary']<r['encounter']<r['pp_spent']<=r['level_frame']<r['returned']<100000,'frame chronology')
    need(0<r['xp_before']==r['xp_threshold']-1<r['xp_threshold']<=r['xp_after']<2000000,'battle EXP threshold')
    need(0<r['enemy_hp_before'] and r['enemy_hp_min']==0 and r['outcome']==1 and 0<r['walking_steps']<=400,'ordinary victory')
    need(b'mGBA[' not in err and err.count(b'original core destroyed; new core normal Continue\n')==1,'warnings/core lifecycle')
    parties=re.findall(rb'^NATURAL_PARTY stage=(fixture|returned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',err,re.M)
    need([x[0] for x in parties]==[b'fixture',b'returned',b'saved',b'continued'] and [int(x[1]) for x in parties]==[2,2,3,3],'Save/Continue observations')
    values=[bytes.fromhex(x[2].decode()) for x in parties]
    need(values[0][:8]==values[1][:8] and values[0]!=values[1] and values[1]==values[2]==values[3],'individual/native change/persistence')
    slots=re.findall(rb'^NATURAL_INITIAL slot=(\d+) move=(\d+) pp=(\d+) expected=(\d+) expected_pp=(\d+)$',err,re.M)
    need([tuple(map(int,x)) for x in slots]==[(i,wanted[i],pp[wanted[i]],wanted[i],pp[wanted[i]]) for i in range(4)],'independent wild observations')
    return dict(r,initial_party=identity(values[0]),persisted_party=identity(values[1]),original_rows=rows[r['enemy_species']])


def execute():
    from pr16_learnset_wiki_actions import current,acquire
    from pr16_wiki_reconcile import fetch
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as e
    head=current();need(not WORK.exists(),'natural working evidence exists');PROOF.mkdir(parents=True)
    old=load(ROOT/CP) if (ROOT/CP).exists() else None
    need(old is None or old['status']=='FAIL','accepted natural case rerun prohibited')
    protected=set(m.PROTECTED)|{e.CP,e.GUIDE,p.CP,p.GUIDE,m.BASE+'pr16_learnset_battle_checkpoint.json',m.BASE+'pr16_learnset_egg_gameplay_checkpoint.json'}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'status':'RUNNING',
       'candidate':CANDIDATE,'results':[],'new_unit_tests':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,
       'accepted_case_reruns':0,'wiki_generations':0,'rom_changes_from_accepted_candidate':0,'issue19_complete':False,
       'release_ready':False,'active_baseline_changed':False,'actions_completion_confirmed':False,
       'source_bindings':{x:identity((ROOT/x).read_bytes()) for x in CODE},'protected_bindings':{x:identity((ROOT/x).read_bytes()) for x in protected}}
    oldproof=m.PROOF;m.PROOF=PROOF
    try:
        cp=load(ROOT/e.CP);need(cp['status']=='PASS_REPAIRED_CFRU_FIRST_CALL_ENTRY' and cp['actions_completion_confirmed'] and cp['candidate']==CANDIDATE,'accepted entry recipe')
        run=fetch('actions/runs/'+str(cp['run_id']));need(run['status']=='completed' and run['conclusion']=='success' and run['head_sha']==cp['source_head'],'entry completed run')
        recent=fetch('actions/runs?branch='+m.BRANCH+'&per_page=100')['workflow_runs']
        relevant=[r for r in recent if r['path'] in (e.WF,WF)]
        need(not any(r['status'] in ('queued','in_progress') and r['id']!=v['run_id'] for r in relevant),'concurrent relevant run')
        v['prior_actions']=[{k:r[k] for k in ('id','path','head_sha','status','conclusion')} for r in relevant]
        _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_natural','-v'],'unit')
        match=re.search(rb'Ran (\d+) tests? in ',err);need(match and b'\nOK\n' in err,'new unit completion');v['new_unit_tests']=int(match[1])
        b.WORK=WORK/'restore-root';b.WORK.mkdir();parent=b.restore();rom,recipe=e.apply(parent)
        need(identity(rom)==CANDIDATE,'accepted repaired candidate');m.CANDIDATE=CANDIDATE
        (WORK/'candidate.gba').write_bytes(rom);write(PROOF/'recipe.json',recipe)
        pc=load(ROOT/m.BASE/'pr16_learnset_payload_checkpoint.json');members=dict(pc['summary']['files'],**{'receipt.json':pc['proof_bindings']['receipt.json']})
        acquire(pc['payload_artifact'],pc['source_head'],WORK/'payload',members)
        rows,audit=sources(WORK/'payload');geometry=b.physical(rom);write(PROOF/'original-source.json',audit);write(PROOF/'geometry.json',geometry)
        at=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000;need(at==0x10421f4,'canonical PP root')
        pp=[rom[at+12*i+4] if i else 0 for i in range(1063)];need(all(0<pp[x]<=64 for x in (53,89,497)),'fixture/learned PP')
        generated={}
        def put(name,text):
            (WORK/name).write_text(text);generated[name]=identity(text.encode())
        for i,(source,target) in enumerate(p.EMBEDDED):
            text,n=re.subn(r'\bint\s+main\s*\(','int natural_old_'+str(i)+'(',(ROOT/source).read_text());need(n==1,'embedded main');put(target,text)
        text=(ROOT/'tools/mgba_pr16_learnset_battle.c').read_text();need(text.count('int main(int argc,char **argv)')==1,'walking source main')
        text=text.split('int main(int argc,char **argv)')[0]
        text=text.replace('#include "pr16_gameplay_driver.c"\n','').replace('#include "pr16_learnset_battle_fixture.h"\n','')
        put('pr16_natural_walking.h',text);put('pr16_natural_vectors.h',header(rows,pp,geometry))
        exe=WORK/'runner';dep=WORK/'dependencies.d'
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(exe)],'compile')
        need(not err,'host compiler warning');v.update(host_compiles=1,generated_sources=generated,compiled_sources={})
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            path=Path(name);path=(path if path.is_absolute() else ROOT/path).resolve()
            if path.parent==WORK:need(identity(path.read_bytes())==generated[path.name],'generated dependency')
            else:v['compiled_sources'][path.relative_to(ROOT).as_posix()]=identity(path.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed identity')
        fixture=WORK/(CASE+'.srm');fixture.write_bytes(seed);v['native_processes']=1
        out,err=m.run([str(exe),str(WORK/'candidate.gba'),str(fixture),CANDIDATE['sha256'],m.SEED_ID['sha256']],CASE,480)
        v['results']=[validate(out,err,rows,pp)];v['fresh_cores']=2
        need((ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp and identity((WORK/'candidate.gba').read_bytes())==CANDIDATE,'input mutation')
        need(v['protected_bindings']=={x:identity((ROOT/x).read_bytes()) for x in protected},'unaffected accepted files changed')
        v['status']='PASS_WILD_INITIAL_AND_BATTLE_EXP_EMPTY'
    except Exception as ex:
        v.update(status='FAIL',error_type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={x.name:identity(x.read_bytes()) for x in PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=oldproof;m.CANDIDATE=e.PARENT


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return CODE|{CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{x.relative_to(ROOT).as_posix() for x in dest.rglob('*') if x.is_file()}


def publish(v,completion=False):
    from pr16_learnset_compact_record import publish_resume
    good=v['status'].startswith('PASS');next_step=NEXT if good else 'Issue19: '+str(v.get('error_type','FAIL'))+'の保存原本を確認し、未成功の自然生成/戦闘EXP経路だけ修復する。既存アメ11/Bag23/旧戦闘/egg8/ARM/host/Wikiは再実行しない。'
    (ROOT/GUIDE).write_text(f'''# Issue19: 自然野生初期技と戦闘EXP

状態 `{v['status']}` / run{v['run_id']} / source `{v['source_head']}`。
候補 `{CANDIDATE['sha256']}`。受入済みentry repairの保存recipe適用だけで復元。ROM変更0、ARM0。

自然移動で発生した野生の4技/PPを固定原本のraw末尾4行窓→重複除外と独立照合する。
開始手持ちバタフリーLv43、EXPをLv44閾値-1、技53/89、能力値999、開始進行は明示fixture。
観測中は7API host書込禁止で通常移動/技選択/勝利EXP/空き枠497習得/通常Save/fresh Continueを行う。
fixture能力値は最終バランス・自然な手持ち取得・通常進行の受入ではない。
原本の初期技順は生の4行窓を先に取り、GiveMoveの既習得除外を後に適用する。独自sortや先行dedupは禁止。

新unit{v['new_unit_tests']}、native{v['native_processes']}、成功{len(v['results'])}、fresh core{v.get('fresh_cores',0)}。
受入済みアメ11/Bag23/旧戦闘/egg8/旧host/ARM/Wikiの再実行0。
成功しても実観測owner/この空き枠ケースのみ。全owner・配布・孵化・form・EXP共有・置換・拒否・進化へ拡張しない。
Actions終端確認 `{v['actions_completion_confirmed']}`。原本 `{v['public_evidence_path']}`。

## 次

{next_step}
''')
    state=load(ROOT/m.STATE);state['learnset_natural_progression']={k:v[k] for k in ('status','source_head','run_id','candidate','native_processes','issue19_complete','release_ready','actions_completion_confirmed')}
    state['learnset_natural_progression'].update(path=CP,successful_cases=len(v['results']))
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='自然野生生成/戦闘EXPの限定工程。開始手持ち/EXP/能力値はfixtureであり全owner受入ではない。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if completion else 'in_progress','conclusion':v.get('completed_actions',{}).get('conclusion')}],'reason_ja':'native証拠とpush/upload終端を区別。一般CI action_requiredをnative失敗へ読み替えない。'}
    state['bp']['current_stop']=f'Issue19: 自然野生初期技/戦闘EXP空き枠 {v["status"]}、成功{len(v["results"])}。開始手持ち/EXP/能力値fixture。全owner/Issue19は未完。'
    state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='LEARNSET_NATURAL_REMAINING' if good and completion else 'LEARNSET_NATURAL_COMPLETION' if good else 'LEARNSET_NATURAL_FAILURE_ONLY',goal_ja=next_step,read_paths=[GUIDE,CP,SELF])
    for path in CODE|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    message='自然初期技/戦闘EXP run'+str(v['run_id'])+'の成功caseは再実行しない。開始fixtureと自然生成enemyを区別し、元の失敗原本を保持する。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 自然野生初期技・戦闘EXP'+(' Actions終端照合' if completion else '')+f'\n- Version: issue19-natural-v1\n- Status: '+('DONE（限定1case、全体未完）' if good else 'BLOCKED（保存失敗から限定継続）')+f'\n- Summary: 保存修復候補を再buildせず復元。自然野生の原本初期技、通常戦闘EXPの空き枠習得、Save/fresh Continueを限定検証。開始手持ち/EXP/能力値/進行はfixture。\n- Files changed: 新driver/C/tests/限定Actions、証拠/CP/guide、固定MD/JSON、両ログ。\n- Verify: {v["status"]} run{v["run_id"]} unit{v["new_unit_tests"]} native{v["native_processes"]} 成功{len(v["results"])}。既受入再実行0、ARM0、ROM変更0、Wiki0。'+(' この終端照合はnative/host/unit再実行0。' if completion else '')+'\n- Commit: 同branchへ非force pushしreflected-head.txtでremote照合。\n- Network: GitHub既存原本artifact/最新Actionsのみ。原本再採取・release・baseline切替なし。\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'duplicate natural evidence');dest.mkdir(parents=True)
    for path in PROOF.iterdir():
        if not path.is_file():continue
        text=path.read_bytes().decode();need('\0' not in text,'binary proof prohibited')
        safe='\n'.join(line.rstrip() for line in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private user path');(dest/path.name).write_text(safe)
    old=load(ROOT/CP) if (ROOT/CP).exists() else None
    v.update(public_evidence_path=dest.relative_to(ROOT).as_posix(),public_evidence_bindings={x.name:identity(x.read_bytes()) for x in dest.iterdir()},
             previous_attempts=old.get('previous_attempts',[])+[{'run_id':old['run_id'],'status':old['status'],'evidence':old['public_evidence_path']}] if old else [])
    write(ROOT/CP,v);publish(v)


def complete():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();v=load(ROOT/CP);need(v['status'].startswith('PASS') and not v['actions_completion_confirmed'],'not pending success')
    run=fetch('actions/runs/'+str(v['run_id']));need(run['head_sha']==v['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success','natural Actions not completed success')
    jobs=fetch('actions/runs/'+str(v['run_id'])+'/jobs?per_page=100');need(jobs['total_count']==1,'natural jobs');job=jobs['jobs'][0]
    need(job['status']=='completed' and job['conclusion']=='success' and all(s['conclusion'] in ('success','skipped') for s in job['steps']),'push/upload steps incomplete')
    meta=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100');need(meta['total_count']==1,'natural artifact count');a=meta['artifacts'][0]
    need(a['name']=='pr16-learnset-natural-proof' and not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'natural artifact binding')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True);need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'natural ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        saved=json.loads(z.read('verification.json'));need(saved['candidate']==v['candidate'] and saved['results']==v['results'] and saved['status']==v['status'],'raw verification differs')
        reflected=z.read('reflected-head.txt').decode().strip();need(re.fullmatch('[0-9a-f]{40}',reflected),'reflected head format')
    need(subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=ROOT).returncode==0,'reflection ancestor')
    v['actions_completion_confirmed']=True;v['completed_actions']={'run_id':v['run_id'],'source_head':v['source_head'],'conclusion':'success','job_id':job['id'],'reflected_head':reflected,'artifact':{k:a[k] for k in ('id','name','size_in_bytes','digest')},'steps':job['steps'],'verified_at_head':os.environ['GITHUB_SHA'],'native_reruns':0,'host_reruns':0,'arm_reruns':0}
    write(ROOT/CP,v);publish(v,completion=True);PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completed-actions.json',v['completed_actions'])


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned()-CODE;g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'complete':complete,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
