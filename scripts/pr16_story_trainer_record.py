#!/usr/bin/env python3
"""未保存trainer原本・図鑑保存ABI停止境界を記録。native/ROM生成は0。"""
import datetime,json,os,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_story_live_probe as transport
import pr16_story_route_record as old_record
import pr16_story_trainer_trace as trace_reader
import pr16_story_trainer_adapter as trainer
import pr16_story_dex_guard as dex
from pr16_story_rom_metadata import public_metadata,no_raw_rom_hex
import pr16_story_route_probe as publication
from pr16_story_after_maori import need,identity,write
from pr16_story_milestones import DiagnosticStop
BASE='4ddcdc44aabb704f542f4e37bf2f58cbfaca7573'
TASK='USER-20261004-STORY-TRAINER'
STATE='content/modernization/pr16_native_supply_resume_20260913.json';DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
CP='content/modernization/pr16_story_trainer_checkpoint.json';GUIDE='docs/PR16_STORY_TRAINER_ACCEPTANCE_JA.md'
EVIDENCE='content/modernization/pr16_story_trainer_evidence'
LOGS={'design/run_log.md','design/version_log.md'}
CODE={'scripts/pr16_story_rom_metadata.py','tests/test_pr16_story_rom_metadata.py','content/modernization/pr16_story_rom_metadata_unit.json','scripts/pr16_story_trainer_adapter.py','scripts/pr16_story_trainer_probe.py','scripts/pr16_story_dex_guard.py','scripts/pr16_story_trainer_trace.py','tests/test_pr16_story_trainer_adapter.py','tests/test_pr16_story_dex_guard.py','content/modernization/pr16_story_trainer_unit.json','content/modernization/pr16_story_dex_guard_unit.json','content/modernization/pr16_story_dex_seen_audit.json','content/modernization/pr16_story_trainer_owner_diagnosis.json','content/modernization/pr16_story_dex_seen_repair_plan.json','docs/PR16_DEX_SEEN_REPAIR_JA.md','scripts/pr16_story_trainer_record.py','content/modernization/pr16_story_trainer_record_inputs.json','.github/workflows/pr16-story-trainer-record.yml'}
OUT=ROOT/'.local/pr16-story-trainer-record'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def bindings(paths):return {p:identity((ROOT/p).read_bytes())for p in sorted(paths)}
def current():
    r=transport.api('pulls/16');need(r['state']=='open' and r['draft'] and not r['merged'] and r['head']['sha']==os.environ['GITHUB_SHA'] and r['head']['ref']=='codex/modernization-followup-20260908','sole live draft writer')
def terminal(spec):
    r=transport.api('actions/runs/'+str(spec['run']));j=transport.api('actions/jobs/'+str(spec['job']))
    need(r['head_sha']==spec['source'] and r['status']=='completed' and r['conclusion']=='success' and r['run_attempt']==1,'terminal original measurement')
    need(j['run_id']==spec['run'] and j['status']=='completed' and j['conclusion']=='success' and len(j['steps'])==8 and all(x['conclusion']=='success'for x in j['steps']),'all8 original steps')
    return dict(run=r,job=j)
def record():
    from pr16_learnset_compact_record import publish_resume
    current();need(not OUT.exists() and not(ROOT/CP).exists() and os.environ['GITHUB_RUN_ATTEMPT']=='1','one new source-only recording');OUT.mkdir();(OUT/'receipts').mkdir()
    state=json.loads((ROOT/STATE).read_bytes());protected=bindings(state['source_bindings']);need(protected==state['source_bindings'],'frozen accepted sources')
    for name,count in [('trainer',30),('dex_guard',14),('rom_metadata',4)]:
        unit=json.loads((ROOT/f'content/modernization/pr16_story_{name}_unit.json').read_bytes());need(unit['tests']==unit['passed']==count and unit['stderr'].count(' ... ok\n')==count and '\nOK\n'in unit['stderr'],'exact new focused tests')
        need(bindings(unit['source_bindings'])==unit['source_bindings'],'tested final source bytes')
    config=json.loads((ROOT/'content/modernization/pr16_story_trainer_record_inputs.json').read_bytes());evidence=ROOT/EVIDENCE;evidence.mkdir();cases=[]
    owner=json.loads((ROOT/'content/modernization/pr16_story_route_owners.json').read_bytes())['trainers'][0]
    # Reuse unchanged private ROM only for static disassembly bindings. No runtime restore.
    z,_=transport.archive(transport.SAVE24)
    with z:rom=z.read('candidate.gba')
    expected=dex.inspect(rom,json.loads((ROOT/'content/modernization/pr16_story_route_owners.json').read_bytes())['trainers'])
    need(expected==json.loads((ROOT/'content/modernization/pr16_story_dex_seen_audit.json').read_bytes()),'all actual trainer mappings and legacy setter bytes')
    diagnosis=json.loads((ROOT/'content/modernization/pr16_story_trainer_owner_diagnosis.json').read_bytes())
    need(diagnosis['candidate']==dex.CANDIDATE,'same fixed owner diagnosis')
    need(no_raw_rom_hex(diagnosis)and no_raw_rom_hex(expected),'no public ROM byte fragments')
    for row in diagnosis['bindings']:need(identity(rom[row['address']-0x8000000:row['address']-0x8000000+row['size']])==dict(size=row['size'],sha256=row['sha256']),'fixed private ROM owner hash')
    del rom
    for spec in config['runs']:
        done=terminal(spec);z,meta=transport.archive((spec['artifact'],spec['run'],spec['archive']['size'],spec['archive']['sha256']));folder=OUT/str(spec['run']);folder.mkdir()
        with z:
            mf=json.loads(z.read('manifest.json'));need(set(z.namelist())==set(mf)|{'manifest.json'},'all original evidence members')
            for n in z.namelist():
                raw=z.read(n);need(n=='manifest.json' or identity(raw)==mf[n],'whole original member')
                p=folder/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        need(not(folder/'failure.json').exists(),'retain unexpected failure distinctly')
        tr=(trace_reader.trace if spec['trainer_pc'] else old_record.trace)(folder/'route');diag=json.loads((folder/'diagnostic.json').read_bytes())
        need(diag['reason']==spec['reason'] and diag['status']=='DIAGNOSTIC_STOP_NOT_MILESTONE' and diag['source_head']==spec['source'] and diag['run_id']==spec['run'] and not diag['milestone_reached'],'original diagnostic unchanged')
        need(len(tr['live'])==spec['screens'] and len(tr['inputs'])==spec['inputs'],'complete native trace accounting')
        route=json.loads((ROOT/'content/modernization/pr16_story_shiou_route_candidate.json').read_bytes())['route']
        walking=json.loads((folder/'walking-ledger.json').read_bytes())
        for row in walking:
            n=row['observation'];result=old_record.clock.walking_evidence(tr['live'][n-1],tr['live'][n],route[row['index']+1][2:],observed_transition=tr['observations'][n]['callback2']==0x08055E69)
            need(all(row[k]==v for k,v in result.items()),'retained strict walking owner')
        old_record.battle.entry_evidence(tr['live'][51],tr['live'][52]);old_record.battle.finished(tr['live'][52],tr['live'][68])
        sight=trainer.sight(tr['live'][81],tr['live'][82]);approach=trainer.field_preserved(tr['live'][82],tr['live'][83])
        accepted=dict(sight=sight,approach=approach)
        if spec['trainer_pc']:
            accepted['entry']=trainer.entry(tr['live'][83],tr['live'][84],owner)
            try:dex.require_safe_party(tr['live'][84],expected)
            except DiagnosticStop as error:
                need(error.report['reason']=='unsafe_legacy_dex_seen_target','only expected unsafe storage boundary');accepted['post_record_fail_closed_replay']=error.report
            else:raise ValueError('unsafe party was incorrectly accepted')
            need(tr['inputs'][-3:]==[(0,180),(1,2),(0,180)],'only approach and exact field intro A; no battle command')
        v=dict(run=spec['run'],source=spec['source'],artifact=meta,reason=diag['reason'],screens=len(tr['live']),inputs=len(tr['inputs']),frames=tr['live'][-1]['observation']['frame'],formal_story_save=101,save_unchanged=True,ordinary_saves=0,native_processes=1,compiles=1,trainer_victory_accepted=False,milestone_reached=False,scoped_verified=accepted,last_observation=tr['live'][-1]['observation'],last_party=tr['live'][-1]['party_mons'])
        for f in folder.rglob('*'):
            if f.is_file() and f.suffix in{'.txt','.json'} and f.name not in {'owners.json','trainer-owners.json'}:
                p=evidence/str(spec['run'])/f.relative_to(folder);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(f.read_bytes())
        # Full original artifact stays unchanged. Omit ROM-byte owner files from new tracked copies.
        write(evidence/str(spec['run'])/'publication-projection.json',dict(omitted_original_files=['owners.json','trainer-owners.json'],original_artifact_unchanged=True,private_rom_fragments_republished=False))
        write(evidence/str(spec['run'])/'terminal.json',done);write(evidence/str(spec['run'])/'verification.json',v);cases.append(v)
    write(evidence/'visual-review.json',config['visual_review']);need(config['visual_review']['reviewed']is True,'visual review of original screens')
    paths={p.relative_to(ROOT).as_posix()for p in evidence.rglob('*')if p.is_file()};status='PASS_TRAINER131_ENTRY_BLOCKED_UNSAFE_DEX_STORAGE'
    final=cases[-1];cp=dict(schema_version=1,task=TASK,status=status,measurement_source=BASE,cases=cases,formal_story_save=101,input_save=transport.SEED,host_tests=48,new_native_processes=2,new_compiles=2,record_native_processes=0,record_compiles=0,source_bindings=bindings(CODE|{'scripts/pr16_story_trainer_session.py','content/modernization/pr16_story_trainer_owners.json'}),evidence_bindings=bindings(paths),trainer_entry_accepted=True,trainer_victory_accepted=False,reward_accepted=False,milestone_reached=False,unsafe_dex_writes_executed=False,rom_changed=False,release_ready=False)
    write(ROOT/CP,cp)
    goal=config['next_goal_ja'];state['story_trainer_adapter']=dict(checkpoint=CP,guide=GUIDE,status=status,measurement_source=BASE,last_run=final['run'],last_artifact=final['artifact']['id'],formal_story_save=101,trainer_entry_accepted=True,trainer_victory_accepted=False,milestone_reached=False,blocked_by='LEGACY_DEX_SEEN_STORAGE_ALIAS',repair_plan='content/modernization/pr16_story_dex_seen_repair_plan.json')
    state['next_action'].update(id='REPAIR_DEX_STORAGE_BEFORE_TRAINER131',goal_ja=goal,read_paths=[GUIDE,CP,'docs/PR16_DEX_SEEN_REPAIR_JA.md','content/modernization/pr16_story_dex_seen_repair_plan.json','content/modernization/pr16_story_trainer_owner_diagnosis.json','scripts/pr16_story_dex_guard.py','docs/PR16_STORY_ACCELERATED_ACCEPTANCE_PLAN_JA.md'])
    state['bp']['current_stop']='正式Save101保持。trainer131接近・会話・通常battle entryを全stateで検証。高national見た登録の別field破壊を静的特定し、戦闘コマンド前で停止。';state['bp']['next_step']=goal
    state['story_milestone_policy'].update(observer_adapter_pending=True,native_multi_battle_continuation_accepted=False,blocked_by='LEGACY_DEX_SEEN_STORAGE_ALIAS')
    state['observed_head']=BASE;state['observed_head_semantics']='未保存trainer131 entryのnative証拠source。保存ABIガードは同じ原本のsource-only再検査。正式進行はSave101。'
    state['observed_head_checks']=dict(scope_head=BASE,trainer_runs=[dict(run=x['run'],reason=x['reason'],milestone_reached=False)for x in cases],general_ci_known_source_mismatch_not_resolved=True,reason_ja='trainer専用2runは各8step成功。接近/会話/通常entryだけ限定受入。高national図鑑setterの別field書込を静的検出し戦闘入力0で停止。48host、記録native0/compile0。シオウ回復未達。一般CI既知QOL source不一致は未解決。')
    state['pending_runs']=[dict(run_id=int(os.environ['GITHUB_RUN_ID']),tested_head=os.environ['GITHUB_SHA'],status='in_progress')]
    state['do_not_repeat'].append('trainer131原本2run/48hostを保持。正式Save101と未保存entryを区別。seen高nationalをtrainerRematches/FameChecker等の許可差分にしない。固定ROMの保存ABIを修復・限定回帰する前にtrainer戦闘を続けない。DPE/CFRUのBag衝突パッチを直貼りせず、通常戦ごとのSaveも復活させない。')
    (ROOT/GUIDE).write_text('# trainer131接近・会話・entryの限定受入\n\n'+config['summary_ja']+'\n\n## 次の1手\n\n'+goal+'\n',encoding='utf-8')
    owned={CP,GUIDE,STATE,DOC,*LOGS}|paths;state['source_bindings'].update(bindings((owned|CODE|{'scripts/pr16_story_trainer_session.py','content/modernization/pr16_story_trainer_owners.json'})-{STATE,DOC,*LOGS}));publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / trainer131と図鑑保存ABI境界\n- Version: PR16-STORY-TRAINER-1\n- Status: STOPPED（視線/接近/会話/entry限定受入。図鑑保存ABI修復前の安全停止）\n- Summary: {config["summary_ja"]}\n- Files changed: trainer adapter/5way observer/closed entry検査、dex破壊前guard、owner/修復計画、48host、2native原本、checkpoint、固定resumeMD/JSON、両ログ。\n- Verify: 専用2run各8step成功。30trainer+14dex+4publication host最終成功、原本全byte/全SaveRTC照合。記録native0/compile0。初回NPC template owner未対応停止を履歴保持。\n- Next: {goal}\n- Commit: native source={BASE}; record source={os.environ["GITHUB_SHA"]}; 同branch非forcepush。\n- Network: 同repoGitHub/Actions/保存artifactおよび固定upstream一次source読取。ROM/runtime/inputSave再配布0、ROM切替0、host戦闘書込0、高national seen破壊の実行0、trainer勝利/賞金受入0、merge/release/baseline切替0。一般CI既知QOL source不一致は残件。\n'
    for p in LOGS:
        with(ROOT/p).open('a')as f:f.write(entry)
    need(bindings(protected)==protected,'all earlier accepted sources preserved');write(OUT/'owned.json',sorted(owned));write(OUT/'receipts/record.json',dict(status=status,formal_story_save=101,latest_run=final['run'],native=0,compile=0,owned=sorted(owned)));git('add','--',*sorted(owned))
def guard():
    import pr16_resume,pr16_learnset_runtime_record as g
    current();pr16_resume.validate(ROOT);g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=set(json.loads((OUT/'owned.json').read_bytes()));g.guard();git('diff','--cached','--check')
def snapshot():
    for p in json.loads((OUT/'owned.json').read_bytes()):need(git('show','HEAD:'+p)==(ROOT/p).read_bytes(),'exact committed text readback')
    print('RESULT=STOPPED TASK='+TASK+' VERIFY=PASS COMMIT='+git('rev-parse','HEAD').decode().strip())
def export():
    if (OUT/'receipts').is_dir()and any((OUT/'receipts').iterdir()):publication.export_evidence(OUT/'receipts',ROOT/'public-story-trainer-record-receipts')
if __name__=='__main__':
    actions=dict(record=record,guard=guard,snapshot=snapshot,export=export);need(len(sys.argv)==2 and sys.argv[1]in actions,'closed source-only record command');actions[sys.argv[1]]()
