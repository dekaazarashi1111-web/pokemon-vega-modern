#!/usr/bin/env python3
"""保存済み限定native原本を照合・記録する。native/旧unit/ARMの再実行0。"""
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_v1_load_actions as old
import pr16_research_v1_load_followup as m
from pr16_learnset_compact_record import publish_resume
d=old.d;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-V1-ROOT'
MODEL='scripts/pr16_research_v1_load_followup.py'
SELF='scripts/pr16_research_v1_load_followup_actions.py'
TEST='tests/test_pr16_research_v1_load_followup.py'
WF='.github/workflows/pr16-research-v1-root-20260926.yml'
RAW='content/modernization/pr16_research_v1_load_root_diagnostic.json'
CP='content/modernization/pr16_research_v1_load_followup_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_V1_LOAD_FOLLOWUP_JA.md'
SOURCES={MODEL,SELF,TEST,WF,RAW}

def record():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'record once only')
    d.PUBLIC.mkdir(parents=True)
    prior=d.read(ROOT/old.CP);raw=d.read(ROOT/RAW)
    need(prior['actions_completion_confirmed'] and prior['failed_cases']==sorted(m.prior.CASES),'old three failures preserved')
    protected=d.bindings(set(prior['protected_bindings'])|{old.CP,old.GUIDE}|set(p for p in d.git('ls-files').decode().splitlines() if p.startswith(old.EVIDENCE+'/')))
    need(raw['generator']==identity((ROOT/MODEL).read_bytes()),'exact measured generator')
    need(d.bindings(raw['source_bindings'])==raw['source_bindings'],'measured dependency source unchanged')
    need(raw['source_head']=='562cd8dab16ed6ca39f11b6539da5d3ad94fcef7','source snapshot identity')
    subprocess.run(['git','merge-base','--is-ancestor',raw['source_head'],'HEAD'],check=True)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_v1_load_followup.py','-v'],capture_output=True,timeout=90)
    unitraw=unit.stdout+unit.stderr;(d.PUBLIC/'unit.txt').write_bytes(unitraw)
    need(unit.returncode==0 and unitraw.count(b' ... ok\n')==20,'20 new root parser tests')
    runtime,data,seed,parent,artifacts=d.restore()
    recipe=d.read(ROOT/old.r.RECIPE);candidate,_=old.r.m.apply(parent,bytes.fromhex(recipe['after']))
    need(identity(candidate)==raw['candidate']==m.prior.CANDIDATE,'no ROM change')
    need(m.caller_bindings(candidate)==raw['caller_bindings'],'two fixed Thumb BL callers')
    need(identity(m.generate(seed))==raw['generated'],'measured generated C byte-for-byte')
    baseline=d.read(ROOT/d.read(ROOT/old.r.CP)['measurement'])['accepted']['retry-zero']['observations'][0]
    accepted={};failed={}
    for case in m.prior.CASES:
        result=raw['cases'][case];out=result['stdout_utf8'].encode();err=result['stderr_utf8'].encode()
        need(identity(out)==result['stdout'] and identity(err)==result['stderr'],'immutable output identities')
        save,_=m.prior.fixture(seed,case)
        try:
            need(result['returncode']==0 and not err,'native failure retained')
            accepted[case]=m.validate(out,case,save,baseline)
        except (ValueError,KeyError,TypeError) as exc:failed[case]={'type':type(exc).__name__,'reason':str(exc)}
    need(sorted(accepted)==['v1-load-valid'] and sorted(failed)==['v1-load-checksum','v1-load-tail'],'one success/two real failures only')
    need(raw['native_processes']==3 and raw['fresh_cores']==5 and raw['successful_host_compiles']==1 and raw['arm_compiles']==raw['arm_links']==raw['rom_changes']==raw['accepted_native_reruns']==0,'measured accounting')
    need(d.bindings(protected)==protected,'history preserved')
    runid=int(os.environ['GITHUB_RUN_ID']);evidence='content/modernization/pr16_research_v1_load_root_evidence/'+str(runid)
    unitpath=evidence+'/unit.txt';(ROOT/unitpath).parent.mkdir(parents=True);(ROOT/unitpath).write_bytes(unitraw)
    cp={'schema_version':1,'task':TASK,'status':'PARTIAL_VALID_V1_ACCEPTED_CORRUPT_LOAD_OPEN','source_head':os.environ['GITHUB_SHA'],
        'record_run_id':runid,'native_source_head':raw['source_head'],'candidate':raw['candidate'],'raw_evidence':RAW,
        'accepted':accepted,'failed':failed,'accepted_cases':sorted(accepted),'failed_cases':sorted(failed),'new_unit_tests':20,
        'native_processes_measured_once':3,'fresh_cores_measured_once':5,'host_compiles_measured_once':1,
        'record_native_runs':0,'record_host_compiles':0,'record_arm_compiles':0,'record_arm_links':0,'accepted_case_reruns':0,
        'preparation_failure':raw['preparation_failure'],'old_checkpoint_unchanged':old.CP,'protected_bindings':protected,
        'source_bindings':d.bindings(SOURCES),'unit_evidence':unitpath,'unit_binding':identity(unitraw),
        'actions_completion_confirmed':False,'v1_valid_load_accepted':True,'corrupt_load_rejection_accepted':False,
        'phase0_load_failure_accepted':False,'normal_new_game_accepted':False,'transaction_ui_accepted':False,
        'physical_flash_fault_accepted':False,'active_baseline_changed':False,'release_ready':False,'issue19_complete':False}
    summary='先行load call誤認を修正。正常V1は保存counter2→3/全ledger移行/2回fresh Continue成功。破損2例は通常load中に有効V2へ初期化される実不具合を保持。'
    goal='QOL restore_durable_ledger/ensure_saveの空・破損混同を修復し、破損2例の実load拒否だけを先に検証。正常V1成功/旧26unit/7retry/ARMを影響なく再実行しない。'
    d.write(ROOT/CP,cp)
    guide='# PR16 V1通常ロードの先行call修復\n\n'+summary+'\n\n'+goal+'\n\n## 観測と受入境界\n\n起動先行callはreturn PC 0x080ED736、result2/counter0/version0。通常Continueはreturn PC 0x080789FE。両callerのThumb BLが既存root0x080DB4E4へ到達するbyteを候補58079dfbで照合。呼出し数2・順序・型・値を閉じたschemaで検証し、初回だけの停止を成功にしない。ROM変更0、ARM compile/link0。\n\n保存済みローカルnative原本3process/5fresh cores・host compile成功1を再利用。正常V1は全ledger/他owner/Bag/party/実Flash/counter保持を受入。checksum/tail破損はresult1/version2/counter2となり、拒否条件で失敗。旧3失敗と今回2失敗は別原本のまま。私有Flash fixtureであり歴史的ユーザーsaveそのものではない。新規native再実行0。\n\n初期のローカル準備で部分sourceのmodule不足と生成前compile失敗があったがnative0。generation用の依存だけで解決し、測定したC hashを再構成照合。新規parser20試験のみ実行。7書込barrier実装は不変、guard専用process再実行0。\n\n## 残件\n\n破損load拒否、load内phase0保存不可/回復、通常new-game/取引UI、物理Flash故障は未受入。Issue19/全catalog/releaseは未完。merge/release/baseline切替なし。\n\n## 記録\n\nnative source `'+raw['source_head']+'`、record run `'+str(runid)+'`。記録run終端・push/uploadは次に照合。原本: `'+RAW+'`。\n'
    (ROOT/GUIDE).write_text(guide)
    state=d.read(ROOT/d.STATE);state['research_v1_load_followup']={k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','record_run_id','v1_valid_load_accepted','corrupt_load_rejection_accepted')};state['research_v1_load_followup']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_V1_CORRUPT_LOAD_REPAIR_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,RAW,MODEL,SELF,'overlays/qol_production/qol_production.c','overlays/research_economy_v1/research_economy_v1.c'],stop_rule_ja='元候補/seed/旧失敗・既受入を保全。破損loadを成功へ昇格しない。merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='V1先行call修復の原本照合record source。native測定sourceはcheckpoint参照。自己SHAはgit log。'
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[{'id':runid,'head_sha':os.environ['GITHUB_SHA'],'status':'in_progress','conclusion':None}],'reason_ja':'限定原本照合run。正常V1のみ受入。全CI成功を主張しない。'}
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / V1先行call修復と破損境界保存\n- Version: research-v1-root-v1\n- Status: DONE（先行call修復の限定scope。破損loadは未完）\n- Summary: '+summary+'\n- Files changed: 専用model/20tests/原本/record/guide/checkpoint、固定引継ぎMD/JSON、両ログ。\n- Verify: 新規parser20 PASS、生成C/2caller byte/入力hash/正常V1原本照合。測定native3/5cores/host成功1、記録native/ARM/host0、旧受入再実行0。破損2例FAILを保持。最終resume/task graph/scoped index guard/diff-check。\n- Commit: 同branch非force、source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log。\n- Network: 固定GitHub入力artifactのhash照合。私有payloadはGitへ追加0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    owned={CP,GUIDE,d.STATE,d.DOC,unitpath}|d.LOGS;d.write(d.OUT/'root-owned.json',sorted(owned));d.put('record-summary.json',{'accepted_cases':sorted(accepted),'failed_cases':sorted(failed),'new_native_runs':0,'new_unit_tests':20})

def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'root-owned.json'))
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'unchanged history')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('record | guard')
