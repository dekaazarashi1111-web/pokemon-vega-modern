#!/usr/bin/env python3
"""Preserve adapter originals and record scoped verification; never rerun native work."""
from __future__ import annotations
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as transport
import pr16_story_live_observer as observer
import pr16_story_route_session as route_reader
import pr16_story_route_probe as measured
import pr16_story_clock as clock
import pr16_story_battle_adapter as battle
from pr16_story_after_maori import need,identity,write
BASE='28261b8982f70b8482cd10af25f6ee32ed0e0c53'
SOURCE=BASE
TASK='USER-20261004-STORY-ROUTE'
OUT=ROOT/'.local/pr16-story-route-record'
EVIDENCE='content/modernization/pr16_story_route_adapter_evidence'
CP='content/modernization/pr16_story_route_adapter_checkpoint.json'
GUIDE='docs/PR16_STORY_ROUTE_ADAPTER_ACCEPTANCE_JA.md'
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_story_route_record.py','.github/workflows/pr16-story-route-record.yml','content/modernization/pr16_story_route_record_inputs.json'}
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    r=transport.api('pulls/16');need(r['state']=='open' and r['draft'] and not r['merged'] and r['head']['sha']==os.environ['GITHUB_SHA'] and r['head']['ref']=='codex/modernization-followup-20260908','same live draft branch')
def terminal(spec):
    r=transport.api('actions/runs/'+str(spec['run']));j=transport.api('actions/jobs/'+str(spec['job']))
    need(r['head_sha']==spec['source'] and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'original terminal source')
    need(j['run_id']==spec['run'] and j['status']=='completed' and j['conclusion']=='success' and len(j['steps'])==8 and all(x['status']=='completed' and x['conclusion']=='success'for x in j['steps']),'original all8 steps')
    return dict(run=r,job=j)
def trace(folder):
    rows=[json.loads(x)for x in(folder/'stdout.txt').read_text().splitlines()]
    need(rows[0]==dict(begin='INDEPENDENT_CONTINUE',candidate_sha256=observer.CANDIDATE,initial_save_sha256=transport.SEED['sha256'],host_write_barriers=7),'original fixed Continue')
    obs=[];live=[];adjunct=[];screens=[];inputs=[];frame=0;next_kind=None
    for row in rows[1:-1]:
        if 'input'in row:
            need(next_kind is None and row['input']==len(inputs) and row['frame']==frame,'input ordering')
            need(type(row['key'])is int and row['key']in(0,1,2,8,16,32,64,128) and type(row['frames'])is int and 0<row['frames']<=600,'bounded normal input')
            inputs.append((row['key'],row['frames']));frame+=row['frames']
        elif 'observe'in row:
            need(next_kind is None and row['observe']==len(obs) and row['frame']==frame,'observation ordering');obs.append(row);next_kind='live'
        elif 'live'in row:
            need(next_kind=='live','same-frame live ordering');live.append(observer.parse(row,obs[-1]));next_kind='route'
        elif 'route_live'in row:
            need(next_kind=='route','same-frame route ordering');adjunct.append(route_reader.parse(row,obs[-1]));live[-1]['route']=adjunct[-1];next_kind='screen'
        elif 'screen'in row:
            need(next_kind=='screen' and row['screen']==len(screens) and row['frame']==frame,'same-frame screenshot')
            raw=(folder/f"screen-{row['screen']:04d}.ppm").read_bytes();need(identity(raw)['sha256']==row['sha256'] and len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'whole screenshot hash');screens.append(row);next_kind=None
        else:raise ValueError('unexpected trace row')
    ending=dict(end='STORY_INPUT_CHECKPOINT',frames=frame,inputs=len(inputs),warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,fixture_calls=0,natural_research_arrival_accepted=False)
    need(next_kind is None and len(obs)==len(live)==len(adjunct)==len(screens) and rows[-1]==ending and not(folder/'stderr.txt').read_bytes(),'clean exact four-way trace')
    need(inputs[:12]==[(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180)],'retained boot sequence')
    commands=(folder/'commands.txt').read_text().splitlines();need(commands[-1]=='quit' and commands.count('quit')==1 and not any(x=='save'for x in commands),'unsaved diagnostic')
    keys=[tuple(map(int,x.split()[1:]))for x in commands if x.startswith('key ')];need(keys==inputs[12:] and all(x[0]!=8 for x in keys),'no field Save menu')
    execution=json.loads((folder/'execution.json').read_bytes());need(execution==dict(returncode=0,initial_save=transport.SEED,final_save=transport.SEED,native_end=ending,observations=len(obs)),'all Save/RTC unchanged')
    return dict(observations=obs,live=live,screens=screens,inputs=inputs,execution=execution)

def record():
    from pr16_learnset_compact_record import publish_resume
    current();need(not OUT.exists() and not(ROOT/CP).exists() and os.environ['GITHUB_RUN_ATTEMPT']=='1','one record only');OUT.mkdir();receipts=OUT/'receipts';receipts.mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=bindings(state['source_bindings']);need(protected==state['source_bindings'],'all accepted sources unchanged')
    for p in measured.CODE:need(git('show',SOURCE+':'+p)==(ROOT/p).read_bytes(),'exact final measurement bytes '+p)
    config=json.loads((ROOT/'content/modernization/pr16_story_route_record_inputs.json').read_bytes());cases=[];evidence=ROOT/EVIDENCE;evidence.mkdir()
    for spec in config['runs']:
        done=terminal(spec);z,meta=transport.archive((spec['artifact'],spec['run'],spec['archive']['size'],spec['archive']['sha256']))
        folder=OUT/str(spec['run']);folder.mkdir()
        with z:
            mf=json.loads(z.read('manifest.json'));need(set(z.namelist())==set(mf)|{'manifest.json'},'all original members')
            for n,b in mf.items():
                raw=z.read(n);need(identity(raw)==b,'original byte identity '+n);p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            (folder/'manifest.json').write_bytes(z.read('manifest.json'))
        need(not(folder/'failure.json').exists(),'native failure must be recorded separately')
        tr=trace(folder/'route');diag=json.loads((folder/'diagnostic.json').read_bytes())
        need(diag['status']=='DIAGNOSTIC_STOP_NOT_MILESTONE' and diag['source_head']==spec['source'] and diag['run_id']==spec['run'] and diag['milestone_reached']is False and diag['ordinary_saves']==0,'original diagnostic remains diagnostic')
        need(diag['reason']==spec['reason'],'exact diagnostic boundary')
        ledger=json.loads((folder/'walking-ledger.json').read_bytes())if(folder/'walking-ledger.json').exists()else[]
        route=json.loads((ROOT/'content/modernization/pr16_story_shiou_route_candidate.json').read_bytes())['route']
        for row in ledger:
            n=row['observation'];expected=clock.walking_evidence(tr['live'][n-1],tr['live'][n],route[row['index']+1][2:],observed_transition=tr['observations'][n]['callback2']==0x08055E69)
            need(all(row[k]==v for k,v in expected.items()),'closed walking owner ledger')
        v=dict(run=spec['run'],source=spec['source'],artifact=meta,reason=diag['reason'],inputs=len(tr['inputs']),screens=len(tr['screens']),steps=sum(x['walking_steps']for x in ledger),turns=sum(not x['walking_steps']for x in ledger),minute_rollovers=sum(x['clock']['minute_rollovers']for x in ledger),friendship_changes=[x for x in ledger if x['friendship']],save_unchanged=True,native_processes=1,compile=1,ordinary_saves=0,milestone_reached=False,battle_victory_accepted=False,victory_outcome_observed=any(x['battle_outcome']==1 for x in tr['observations'][52:]),last_observation=tr['observations'][-1],last_party=tr['live'][-1]['party_mons'])
        if len(tr['live'])>52:v['battle_entry']=battle.entry_evidence(tr['live'][51],tr['live'][52])
        if(folder/'battle-ledger.json').exists():
            bl=json.loads((folder/'battle-ledger.json').read_bytes());candidates=[x for x in tr['live'][53:]if x['observation']['callback2']==observer.FIELD and x['observation']['lock']==0 and x['observation']['battle_outcome']==1]
            need(len(bl)==1 and candidates,'one exact first wild ledger');result=battle.finished(tr['live'][52],candidates[0]);need(all(bl[0][k]==v for k,v in result.items()),'postbattle all-byte revalidation');v['battle_victory_accepted']=True;v['battle_ledger']=bl
        for f in folder.rglob('*'):
            if f.is_file() and f.suffix in{'.txt','.json'}:
                p=evidence/str(spec['run'])/f.relative_to(folder);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.read_bytes())
        write(evidence/str(spec['run'])/'terminal.json',done);write(evidence/str(spec['run'])/'verification.json',v);cases.append(v)
    final=cases[-1];write(evidence/'visual-review.json',config['visual_review']);need(config['visual_review']['reviewed']is True,'explicit visual review')
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()};unit=json.loads((ROOT/'content/modernization/pr16_story_battle_unit.json').read_bytes())
    need(unit['tests']==unit['passed']==29 and unit['prior_host_tests_reused']==47,'host accounting')
    public=json.loads((ROOT/'content/modernization/pr16_story_publication_unit.json').read_bytes());need(public['tests']==public['passed']==4 and public['stderr'].count(' ... ok\n')==4,'public scope tests')
    status='PASS_SCOPED_FIRST_WILD_CONTINUATION_WITH_TRAINER_DIAGNOSTIC' if final['battle_victory_accepted'] else 'PASS_CLOSED_WALK_AND_BATTLE_ENTRY_DIAGNOSTIC_RETAINED'
    cp=dict(schema_version=1,task=TASK,status=status,measurement_source=SOURCE,cases=cases,formal_story_save=101,input_save=transport.SEED,host_tests=80,host_tests_new=33,host_tests_reused=47,native_processes=len(cases),record_native_processes=0,compiles=len(cases),source_bindings=bindings(measured.CODE|CODE),evidence_bindings=bindings(paths),milestone_reached=False,native_postbattle_adapter_accepted=final['battle_victory_accepted'],native_multi_battle_accepted=False,release_ready=False)
    write(ROOT/CP,cp)
    goal=config['next_goal_ja'];write(OUT/'verification.json',cp)
    state['story_route_adapter']=dict(checkpoint=CP,guide=GUIDE,status=status,measurement_source=SOURCE,last_run=final['run'],last_artifact=final['artifact']['id'],formal_story_save=101,native_postbattle_adapter_accepted=final['battle_victory_accepted'],native_multi_battle_accepted=False,milestone_reached=False)
    state['story_milestone_policy'].update(postbattle_adapter_pending=not final['battle_victory_accepted'],observer_adapter_pending=True,native_multi_battle_continuation_accepted=False)
    state['next_action'].update(goal_ja=goal,read_paths=[GUIDE,CP,'scripts/pr16_story_battle_adapter.py','scripts/pr16_story_clock.py','content/modernization/pr16_story_route_owners.json','docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md','content/modernization/pr16_story_shiou_route_candidate.json'])
    state['bp']['current_stop']='正式進行Save101のまま。通常wild1勝の全state/field復帰/保存せず次歩をnative確認。trainer131視線で未保存停止、シオウ回復施設へ継続中。';state['bp']['next_step']=goal
    state['observed_head']=SOURCE;state['observed_head_semantics']='変更箇所だけの未保存route adapter診断source。正式story Save101と区別。';state['observed_head_checks']=dict(scope_head=SOURCE,adapter_runs=[dict(run=x['run'],reason=x['reason'],milestone_reached=False)for x in cases],general_ci_known_source_mismatch_not_resolved=True,reason_ja='新区間専用5runは各8step成功。正式milestone未達、wild1戦の保存なし継続だけ限定受入。一般CIの既知QOL source不一致は未解決。Stage79は7domain cache再利用/native再走0。')
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('route adapter原本5run/80host証拠は保持。正式Save101以前を再走せず、新しい未保存失敗区間だけ変更影響に応じて再開。時計/再暗号化/seen/QOL provenanceを全byte免除にしない。通常戦ごとのSaveを復活させない。')
    (ROOT/GUIDE).write_text('# Route adapterの限定検証\n\n'+config['summary_ja']+'\n\n## 次の1手\n\n'+goal+'\n',encoding='utf-8')
    owned={CP,GUIDE,STATE,DOC,*LOGS}|paths;state['source_bindings'].update(bindings((owned|measured.CODE|CODE)-{STATE,DOC,*LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / route continuation adapter\n- Version: PR16-STORY-ROUTE-ADAPTER-1\n- Status: DONE（閉じたowner/診断原本の記録。シオウ施設未達）\n- Summary: {config["summary_ja"]}\n- Files changed: 新route/battle observer/clock/rekey adapter、owner proof、80host検査、未保存診断原本、checkpoint、固定resumeMD/JSON、両ログ。\n- Verify: 5個の専用run各8step成功。診断をmilestone成功としない。80host原本再利用、記録native0/compile0。最初のdaycare差分は失敗原本のまま保持。\n- Next: {goal}\n- Commit: source={SOURCE}; record source={os.environ["GITHUB_SHA"]}; 同branch非forcepush。\n- Network: 同repoActions/保存artifacts/固定upstream読取のみ。入力ROM/Save/runtime/runner再配布0、host戦闘書込0、flag注入/進化gate回避/newbalance/merge/release/baseline切替0。一般CI既知QOL不一致は未解決。\n'
    for name in LOGS:
        with(ROOT/name).open('a')as f:f.write(entry)
    need(bindings(protected)==protected,'all earlier accepted sources preserved');write(OUT/'owned.json',sorted(owned));write(receipts/'record.json',dict(status=status,formal_story_save=101,latest_run=final['run'],native=0,compile=0,owned=sorted(owned)));git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'exact committed bytes '+p)
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if (OUT/'receipts').is_dir() and any((OUT/'receipts').iterdir()):
        measured.export_evidence(OUT/'receipts',ROOT/'public-story-route-record-receipts')
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot,export=export);need(len(sys.argv)==2 and sys.argv[1]in actions,'closed record action');actions[sys.argv[1]]()
