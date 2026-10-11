#!/usr/bin/env python3
"""Issue19: 保存候補の未受入EXP境界だけを独立検証・追記する。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_learnset_natural as n
m=n.m
need,identity,load,write=m.need,m.identity,m.load,m.write
TASK='USER-20260925-LEARNSET-BOUNDARIES'
SELF='scripts/pr16_learnset_boundaries.py'
C='tools/mgba_pr16_learnset_boundaries.c'
TEST='tests/test_pr16_learnset_boundaries.py'
WF='.github/workflows/pr16-learnset-boundaries.yml'
CODE={SELF,C,TEST,WF}
CP=m.BASE+'pr16_learnset_boundaries_checkpoint.json'
GUIDE='docs/PR16_LEARNSET_BOUNDARIES_JA.md'
EVIDENCE=m.BASE+'pr16_learnset_boundaries_evidence'
WORK=ROOT/'.local/pr16-learnset-boundaries'
PROOF=WORK/'proof'
CANDIDATE={'size':33554432,'sha256':'b7790902733a638445129c388d65ab3c199bceb92a41338e0069221b556b9f91'}
CASES=(('butterfree-exp-known',43,0,1,1,(53,89,497,0)),
       ('butterfree-exp-multilevel',10,0,1,2,(53,0,0,0)),
       ('butterfree-exp-replace',43,0,1,1,(53,89,33,45)),
       ('butterfree-exp-summary-refuse',43,1,1,1,(53,89,33,45)))
NEXT='Issue19: EXP境界の保存成功caseを再実行せず、失敗caseだけを修復する。全4caseの終端照合後は、最初の質問での拒否、戦闘EXP進化/共有、自然配布/孵化/form、釣り/隠し野生の特殊技順を限定追加。既受入野生初期技/EXP空き枠・アメ11/Bag23/egg8/旧host/ARM/Wiki/原本再採取は変更影響なし。全owner/Issue19/release/baseline切替は未完。'


def vectors(pp):
    result=[]
    for name,level,mode,slot,delta,moves in CASES:
        need(len(moves)==4 and moves[0]==53 and slot!=0,'attack slot must survive')
        points=[pp[x] if i==0 else min(7+i,pp[x]) if x else 0 for i,x in enumerate(moves)]
        result.append(dict(name=name,level=level,mode=mode,slot=slot,min_delta=delta,moves=list(moves),points=points))
    return result


def expected(case,level,pp,spent,rows):
    need(type(level) is int and case['level']+case['min_delta']<=level<100,'level delta')
    need(type(spent) is int and 0<spent<case['points'][0],'spent attack PP')
    points=case['points'][:];points[0]-=spent
    eligible=[mid for mid,lv in rows if case['level']<lv<=level]
    moves,points,trace=n.p.simulate(case['moves'],points,eligible,2 if case['mode'] else 0,case['slot'],pp)
    return moves,points,trace['selections'],eligible


def validate(out,err,case,rows,pp):
    r=json.loads(out,object_pairs_hook=n.p.strict)
    fixed={'schema_version':1,'status':'PASS','case':case['name'],'candidate_sha256':CANDIDATE['sha256'],
           'level_before':case['level'],'guarded_phases':3,'denied_host_write_apis':7,'fresh_cores':2,
           'save_counters':[2,3,3],'party_preserved_bytes':100,'initial_party_exp_stats_progress_are_fixtures':True,
           'all_owners_accepted':False,'issue19_complete':False,'release_ready':False,'warnings_errors':0}
    integers={'enemy_species','enemy_level','xp_before','xp_threshold','xp_after','level_after','boundary','encounter',
              'pp_spent','level_frame','returned','turns','walking_steps','enemy_hp_before','enemy_hp_min','outcome',
              'summaries','selections','summary_frame','selection_frame'}
    need(set(r)==set(fixed)|integers|{'moves_after','pp_after'},'exact result schema')
    for k,v in fixed.items():need(type(r[k]) is type(v) and r[k]==v,'result field '+k)
    need(all(type(r[k]) is int for k in integers),'integer fields')
    for k in ('moves_after','pp_after'):
        need(type(r[k]) is list and len(r[k])==4 and all(type(x) is int for x in r[k]),'four integer slots')
    level=r['level_after'];moves,points,prompts,eligible=expected(case,level,pp,case['points'][0]-r['pp_after'][0],rows)
    need(r['moves_after']==moves and r['pp_after']==points,'original learned move/PP oracle')
    need(r['summaries']==r['selections']==prompts,'summary count')
    need(r['xp_before']==r['xp_threshold']-1==(case['level']+1)**3-1 and level**3<=r['xp_after']<(level+1)**3,'EXP curve')
    need(0<r['boundary']<r['encounter']<r['pp_spent']<=r['level_frame']<r['returned']<100000,'native chronology')
    need(1<=r['turns']<=8 and case['points'][0]-r['pp_after'][0]<=2*r['turns'] and 0<r['walking_steps']<=400,'ordinary input bounds')
    need(0<r['enemy_species']<1671 and 1<=r['enemy_level']<=100 and r['enemy_hp_before']>0 and r['enemy_hp_min']==0 and r['outcome']==1,'ordinary victory')
    if prompts:need(r['level_frame']<r['summary_frame']<=r['selection_frame']<r['returned'],'summary chronology')
    else:need(r['summary_frame']==r['selection_frame']==0,'unexpected summary')
    observed=re.findall(rb'^BOUNDARY_SELECTION frame=(\d+) cursor=(\d+) key=(\d+) mode=(\d+)$',err,re.M)
    need(len(observed)==prompts,'selection raw evidence')
    for frame,cursor,key,mode in observed:
        need(int(mode)==case['mode'] and int(key)==(2 if case['mode'] else 1) and 0<=int(cursor)<5 and (case['mode'] or int(cursor)==case['slot']),'physical selection key/cursor')
    parties=re.findall(rb'^NATURAL_PARTY stage=(fixture|returned|saved|continued) counter=(\d+) hex=([0-9a-f]{200})$',err,re.M)
    need([x[0] for x in parties]==[b'fixture',b'returned',b'saved',b'continued'] and [int(x[1]) for x in parties]==[2,2,3,3],'raw Save/Continue lifecycle')
    data=[bytes.fromhex(x[2].decode()) for x in parties]
    need(data[0][:8]==data[1][:8] and data[0]!=data[1] and data[1]==data[2]==data[3],'individual/native change/persistence')
    need(err.count(b'original core destroyed; new core normal Continue\n')==1 and b'FORBIDDEN' not in err,'fresh core/host barrier')
    return dict(r,eligible_original_moves=eligible,fixture=case,initial_party=identity(data[0]),persisted_party=identity(data[1]))


def pending(cases,accepted):
    by_name={c['name']:c for c in cases}
    need(set(accepted)<=set(by_name),'unknown prior case')
    for name,a in accepted.items():
        need(a['result']['fixture']==by_name[name] and a['result']['candidate_sha256']==CANDIDATE['sha256'],'accepted case inputs changed; impact review required')
    return [c for c in cases if c['name'] not in accepted]


def execute():
    from pr16_learnset_wiki_actions import current,acquire
    import pr16_learnset_battle as b
    import pr16_learnset_entry_repair as e
    import pr16_learnset_wild_repair as w
    head=current();need(not WORK.exists(),'working evidence already exists');PROOF.mkdir(parents=True)
    old=load(ROOT/CP) if (ROOT/CP).exists() else {}
    protected=set(m.PROTECTED)|{n.CP,n.GUIDE,e.CP,e.GUIDE,n.p.CP,n.p.GUIDE,m.BASE+'pr16_learnset_battle_checkpoint.json',m.BASE+'pr16_learnset_egg_gameplay_checkpoint.json'}
    v={'schema_version':1,'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':CANDIDATE,
       'status':'RUNNING','accepted':old.get('accepted',{}),'results':[],'failures':{},'selected_cases':[],
       'new_unit_tests':0,'native_processes':0,'host_compiles':0,'arm_compiles':0,'accepted_case_reruns':0,
       'rom_changes_from_accepted_candidate':0,'wiki_generations':0,'issue19_complete':False,'release_ready':False,
       'active_baseline_changed':False,'actions_completion_confirmed':False,
       'source_bindings':{x:identity((ROOT/x).read_bytes()) for x in CODE},
       'protected_bindings':{x:identity((ROOT/x).read_bytes()) for x in protected}}
    previous=m.PROOF;m.PROOF=PROOF
    try:
        cp=load(ROOT/n.CP);need(cp['actions_completion_confirmed'] and cp['candidate']==CANDIDATE and cp['status'].startswith('PASS'),'accepted wild candidate')
        for name,binding in dict(cp['source_bindings'],**cp['compiled_sources']).items():
            if name!=n.WF:need(identity((ROOT/name).read_bytes())==binding,'accepted source changed '+name)
        for name,a in v['accepted'].items():
            saved=ROOT/EVIDENCE/str(a['run_id']);raw=load(saved/'verification.json')
            for suffix in ('.stdout.txt','.stderr.txt','.process.json'):
                path=saved/(name+suffix);need(identity(path.read_bytes())==raw['proof_bindings'][path.name],'saved accepted proof changed')
            need(load(saved/(name+'.process.json'))=={'returncode':0,'timed_out':False},'prior native process')
        _,err=m.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_boundaries','-v'],'unit')
        count=re.search(rb'Ran (\d+) tests? in ',err);need(count and b'\nOK\n' in err,'focused unit completion');v['new_unit_tests']=int(count[1])
        b.WORK=WORK/'restore-root';b.WORK.mkdir();parent=b.restore();entry,recipe=e.apply(parent);rom=w.replay(entry,cp['wild_repair'])
        need(identity(rom)==CANDIDATE,'saved exact candidate');(WORK/'candidate.gba').write_bytes(rom);write(PROOF/'recipe.json',dict(entry=recipe,wild=cp['wild_repair']))
        pc=load(ROOT/m.BASE/'pr16_learnset_payload_checkpoint.json')
        acquire(pc['payload_artifact'],pc['source_head'],WORK/'payload',dict(pc['summary']['files'],**{'receipt.json':pc['proof_bindings']['receipt.json']}))
        rows,audit=n.sources(WORK/'payload');write(PROOF/'original-source.json',audit)
        geometry=b.physical(rom);write(PROOF/'geometry.json',geometry)
        import struct
        at=struct.unpack_from('<I',rom,0x1cc)[0]-0x08000000;need(at==0x10421f4,'canonical PP root')
        pp=[rom[at+12*i+4] if i else 0 for i in range(1063)];cases=vectors(pp);todo=pending(cases,v['accepted']);need(todo,'all native cases already saved; complete instead')
        v['selected_cases']=[c['name'] for c in todo];write(PROOF/'vectors.json',{'cases':cases,'selected':v['selected_cases']})
        generated={}
        def put(name,text):
            (WORK/name).write_text(text);generated[name]=identity(text.encode())
        for i,(source,target) in enumerate(n.p.EMBEDDED):
            text,count=re.subn(r'\bint\s+main\s*\(','int boundary_old_'+str(i)+'(',(ROOT/source).read_text());need(count==1,'embedded main');put(target,text)
        text=(ROOT/'tools/mgba_pr16_learnset_battle.c').read_text().split('int main(int argc,char **argv)')[0]
        text=text.replace('#include "pr16_gameplay_driver.c"\n','').replace('#include "pr16_learnset_battle_fixture.h"\n','');put('pr16_natural_walking.h',text)
        put('pr16_boundaries_helpers.h',(ROOT/n.C).read_text().split('int main(int argc,char **argv)')[0])
        n.CANDIDATE=CANDIDATE;put('pr16_natural_vectors.h',n.header(rows,pp,geometry))
        arr=lambda x:'{'+','.join(map(str,x))+'}'
        put('pr16_boundaries_vectors.h','static const struct XCase X_CASES[]={'+','.join('{'+json.dumps(c['name'])+','+','.join(str(c[k]) for k in ('level','mode','slot','min_delta'))+','+arr(c['moves'])+','+arr(c['points'])+'}' for c in cases)+'};\n')
        exe=WORK/'runner';dep=WORK/'dependencies.d';v['host_compiles']=1
        _,err=m.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(WORK),'-MMD','-MF',str(dep),C,'-lmgba','-o',str(exe)],'compile')
        need(not err,'compiler warnings');v.update(generated_sources=generated,compiled_sources={})
        for name in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            path=Path(name);path=(path if path.is_absolute() else ROOT/path).resolve()
            if path.parent==WORK:need(identity(path.read_bytes())==generated[path.name],'generated dependency')
            else:v['compiled_sources'][path.relative_to(ROOT).as_posix()]=identity(path.read_bytes())
        seed=(ROOT/m.SEED).read_bytes();stamp=(ROOT/m.SEED).stat().st_mtime_ns;need(identity(seed)==m.SEED_ID,'seed identity')
        for case in todo:
            name=case['name'];fixture=WORK/(name+'.srm');fixture.write_bytes(seed);v['native_processes']+=1
            try:
                out,err=m.run([str(exe),str(WORK/'candidate.gba'),str(fixture),CANDIDATE['sha256'],m.SEED_ID['sha256'],str(cases.index(case))],name,360)
                result=validate(out,err,case,rows[414],pp);v['results'].append(result)
                v['accepted'][name]={'result':result,'source_head':head,'run_id':v['run_id']}
            except Exception as ex:v['failures'][name]={'type':type(ex).__name__,'error':str(ex).replace(str(ROOT),'$REPO')}
        need((ROOT/m.SEED).read_bytes()==seed and (ROOT/m.SEED).stat().st_mtime_ns==stamp and identity((WORK/'candidate.gba').read_bytes())==CANDIDATE,'input mutation')
        need(v['protected_bindings']=={x:identity((ROOT/x).read_bytes()) for x in protected},'unaffected accepted files changed')
        v['status']='PASS_BATTLE_EXP_BOUNDARIES' if len(v['accepted'])==len(CASES) else 'PARTIAL_BATTLE_EXP_BOUNDARIES'
        need(not v['failures'],'native failures retained individually')
    except Exception as ex:
        if v['status']=='RUNNING':v['status']='FAIL'
        v.update(error_type=type(ex).__name__,error=str(ex).replace(str(ROOT),'$REPO'));raise
    finally:
        v['proof_bindings']={x.name:identity(x.read_bytes()) for x in PROOF.iterdir() if x.is_file() and x.name!='verification.json'}
        write(PROOF/'verification.json',v);m.PROOF=previous


def owned():
    dest=ROOT/EVIDENCE/os.environ.get('GITHUB_RUN_ID','')
    return {CP,GUIDE,m.STATE,m.DOC,'design/run_log.md','design/version_log.md'}|{x.relative_to(ROOT).as_posix() for x in dest.rglob('*') if x.is_file()}


def publish(v):
    from pr16_learnset_compact_record import publish_resume
    good=list(v['accepted']);missing=[c[0] for c in CASES if c[0] not in good]
    next_step=('保存native成功は再実行せずcompleteでActions終端だけ照合。' if not missing and not v['actions_completion_confirmed'] else NEXT)
    (ROOT/GUIDE).write_text('# PR16 Issue19: 戦闘EXP境界\n\n'+
        f"状態 `{v['status']}`、入力HEAD `{v['source_head']}`、run `{v['run_id']}`。Actions終端確認 `{v['actions_completion_confirmed']}`。\n\n"+
        f"候補 `{CANDIDATE['sha256']}` は保存済みrecipeの復元のみ。ARM/原本生成/ROM変更/受入済みcase再実行は0。\n\n"+
        '## 保存されたnative成功\n\n'+('\n'.join('- `'+name+'`: run `'+str(v['accepted'][name]['run_id'])+'`、通常Save/fresh Continueまで。' for name in good) or 'まだなし。')+
        '\n\n## 今回の検証\n\n'+f"新unit {v['new_unit_tests']}、host compile {v['host_compiles']}、native process {v['native_processes']}。未成功: {missing}。原本証拠は `{EVIDENCE}/{v['run_id']}`。\n\n"+
        '開始個体・EXP・能力値・進行はfixture。野生生成の既受入testは呼ばず通常歩行遭遇を共通setupとして利用。勝利/EXP/習得/Save/Continue区間は3組の書込barrierを使う。summaryでB取消して中止を確定する拒否と、最初の質問での拒否を区別。\n\n'+
        '## 未完と次\n\n'+next_step+'\n')
    state=load(ROOT/m.STATE)
    state['learnset_exp_boundaries']={'path':CP,'status':v['status'],'source_head':v['source_head'],'run_id':v['run_id'],'accepted_cases':good,'pending_cases':missing,'actions_completion_confirmed':v['actions_completion_confirmed'],'issue19_complete':False}
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='戦闘EXP境界の限定検証。native成功原本とActions終端を区別し、全体受入へ昇格しない。'
    state['observed_head_checks']={'scope_head':v['source_head'],'runs':[{'id':v['run_id'],'status':'completed' if v['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if v['actions_completion_confirmed'] else None}],'reason_ja':'各caseの成功/失敗原本を保持。一般CIと限定nativeを区別。'}
    state['bp']['current_stop']=f"Issue19: EXP境界{len(good)}/{len(CASES)} native成功。{v['status']}。全体未完。";state['bp']['next_step']=next_step
    state['next_action']=dict(state['next_action'],id='LEARNSET_EXP_BOUNDARIES',goal_ja=next_step,read_paths=[GUIDE,CP,SELF])
    for path in CODE|{GUIDE,CP}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    message='EXP境界の保存成功caseは再実行しない。checkpoint acceptedと原本hashを照合し、失敗/未実施だけ選択する。'
    if message not in state['do_not_repeat']:state['do_not_repeat'].append(message)
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    note=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 戦闘EXP境界\n- Version: issue19-exp-boundaries-v1\n- Status: '+('DONE（限定4case、全体未完）' if not missing else 'BLOCKED（成功を保存、残件のみ継続）')+f"\n- Summary: {v['status']}。保存成功{len(good)}/4。候補の復元のみ、3書込barrier/通常Save/fresh Continue。開始個体/EXP/能力/進行はfixture。\n- Files changed: 限定driver/native/tests/workflow、CP/guide/証拠、固定MD/JSON、両ログ。\n- Verify: unit{v['new_unit_tests']} native{v['native_processes']} host compile{v['host_compiles']}。ARM0、ROM変更0、旧受入再実行0。Actions終端確認={v['actions_completion_confirmed']}。終端照合の場合unit/native/host再実行0。\n- Commit: 同branchへの非force push、reflected-head.txtとremoteで照合。\n- Network: GitHub保存artifact/Actionsのみ。原本再採取、Wiki/release/baseline切替なし。\n"
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(note)


def record():
    from pr16_learnset_wiki_actions import current
    from common import redact_user_paths,user_absolute_path_lines
    current();v=load(PROOF/'verification.json');need(v['source_head']==os.environ['GITHUB_SHA'],'record source')
    dest=ROOT/EVIDENCE/str(v['run_id']);need(not dest.exists(),'duplicate evidence');dest.mkdir(parents=True)
    for path in PROOF.iterdir():
        if not path.is_file():continue
        text=path.read_bytes().decode();need('\0' not in text,'binary proof forbidden')
        safe='\n'.join(line.rstrip() for line in redact_user_paths(text).splitlines()).rstrip()+'\n' if text else ''
        need(not user_absolute_path_lines(safe),'private user path');(dest/path.name).write_text(safe)
    old=load(ROOT/CP) if (ROOT/CP).exists() else None
    v['previous_attempts']=(old.get('previous_attempts',[])+[{'run_id':old['run_id'],'status':old['status']}]) if old else []
    v['public_evidence_bindings']={x.name:identity(x.read_bytes()) for x in dest.iterdir()};write(ROOT/CP,v);publish(v)


def complete():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();v=load(ROOT/CP);need(v['status']=='PASS_BATTLE_EXP_BOUNDARIES' and not v['actions_completion_confirmed'],'pending full native success required')
    run=fetch('actions/runs/'+str(v['run_id']));need(run['head_sha']==v['source_head'] and run['path']==WF and run['status']=='completed' and run['conclusion']=='success','Actions terminal success')
    jobs=fetch('actions/runs/'+str(v['run_id'])+'/jobs?per_page=100');need(jobs['total_count']==1,'exact job count');job=jobs['jobs'][0]
    need(job['conclusion']=='success' and all(s['conclusion'] in ('success','skipped') for s in job['steps']),'push/upload not successful')
    meta=fetch('actions/runs/'+str(v['run_id'])+'/artifacts?per_page=100');need(meta['total_count']==1,'exact artifact count');a=meta['artifacts'][0]
    need(a['name']=='pr16-learnset-boundaries-proof' and not a['expired'] and a['workflow_run']['head_sha']==v['source_head'],'artifact binding')
    raw=fetch('actions/artifacts/'+str(a['id'])+'/zip',binary=True);need(identity(raw)=={'size':a['size_in_bytes'],'sha256':a['digest'][7:]},'ZIP binding')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        saved=json.loads(z.read('verification.json'));need(saved['candidate']==v['candidate'] and saved['accepted']==v['accepted'] and saved['status']==v['status'],'raw success differs')
        reflected=z.read('reflected-head.txt').decode().strip();need(re.fullmatch('[0-9a-f]{40}',reflected),'reflected format')
    need(subprocess.run(['git','merge-base','--is-ancestor',reflected,'HEAD'],cwd=ROOT).returncode==0,'reflection ancestor')
    v['actions_completion_confirmed']=True;v['completed_actions']={'run_id':v['run_id'],'job_id':job['id'],'reflected_head':reflected,'artifact':{k:a[k] for k in ('id','name','size_in_bytes','digest')},'steps':job['steps'],'verified_at_head':os.environ['GITHUB_SHA'],'native_reruns':0,'host_reruns':0,'arm_reruns':0}
    write(ROOT/CP,v);publish(v);PROOF.mkdir(parents=True,exist_ok=True);write(PROOF/'completed-actions.json',v['completed_actions'])


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned();g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    actions={'execute':execute,'record':record,'complete':complete,'guard':guard,'paths':lambda:print('\n'.join(sorted(owned())))}
    need(len(sys.argv)==2 and sys.argv[1] in actions,'execute|record|complete|guard|paths');actions[sys.argv[1]]()
