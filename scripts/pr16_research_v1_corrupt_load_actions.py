#!/usr/bin/env python3
"""保存済み3native/20unitを再実行せず、canonical修正と終端を記録。"""
import datetime
import os
from pathlib import Path
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_v1_load_followup_actions as previous
import pr16_research_v1_corrupt_load as m
from pr16_learnset_compact_record import publish_resume
d=previous.d;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-V1-CORRUPT'
SELF='scripts/pr16_research_v1_corrupt_load_actions.py'
MODEL='scripts/pr16_research_v1_corrupt_load.py'
TEST='tests/test_pr16_research_v1_corrupt_load.py'
WF='.github/workflows/pr16-research-v1-corrupt-20260926.yml'
RAW='content/modernization/pr16_research_v1_corrupt_load_native.json'
RECIPE='content/modernization/pr16_research_v1_corrupt_load_recipe.json'
CP='content/modernization/pr16_research_v1_corrupt_load_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_V1_CORRUPT_LOAD_JA.md'
SOURCES={SELF,MODEL,TEST,WF,RAW,RECIPE,m.SOURCE}

def terminal(runid,head,path):
    run=d.inputs.api('actions/runs/'+str(runid));jobs=d.inputs.api('actions/runs/'+str(runid)+'/jobs?per_page=10')
    need(run['head_sha']==head and run['path']==path and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='success','exact successful record terminal')
    need(len(jobs['jobs'])==1,'one scoped job')
    job=jobs['jobs'][0];need(job['status']=='completed' and job['conclusion']=='success','job success')
    need(all(s['conclusion']=='success' for s in job['steps']),'every step including push/upload success')
    listing=d.inputs.api('actions/runs/'+str(runid)+'/artifacts?per_page=100')
    need(listing['total_count']==len(listing['artifacts'])==1,'exact public artifact')
    artifacts=[{k:a[k] for k in ('id','name','size_in_bytes','digest','workflow_run')} for a in listing['artifacts']]
    return {'run':d.run_summary(run),'jobs':jobs['jobs'],'artifacts':artifacts,'native_reruns':0,'unit_reruns':0,'compiles':0}

def record():
    os.chdir(ROOT);d.current();need(not (ROOT/CP).exists(),'do not repeat completed repair')
    d.PUBLIC.mkdir(parents=True)
    old=d.read(ROOT/previous.CP);raw=d.read(ROOT/RAW);recipe=d.read(ROOT/RECIPE)
    prior_terminal=terminal(old['record_run_id'],old['source_head'],previous.WF)
    protected=d.bindings((set(old['protected_bindings'])|{previous.CP,previous.GUIDE,previous.RAW}|set(p for p in d.git('ls-files').decode().splitlines() if p.startswith('content/modernization/pr16_research_v1_load_root_evidence/')))-{m.SOURCE})
    need(d.bindings(raw['source_bindings'])==raw['source_bindings'],'measured source identities')
    need(d.bindings(d.read(ROOT/previous.RAW)['source_bindings'])==d.read(ROOT/previous.RAW)['source_bindings'],'parent dependency identities before correction')
    unit=raw['unit'];unitbytes=unit['raw_utf8'].encode()
    need(identity(unitbytes)==unit['binding'] and unit['returncode']==0 and unit['count']==20 and unit['canonical_status_pairs']==100,'20 new tests and 100 canonical C status pairs')
    need(unitbytes.count(b' ... ok\n')==20 and b'Ran 20 tests' in unitbytes and unitbytes.endswith(b'\nOK\n'),'exact successful unit transcript')
    need(unit['test_source']==identity((ROOT/TEST).read_bytes()) and unit['model_source']==identity((ROOT/MODEL).read_bytes()),'unit source binding')
    runtime,data,seed,parent,_=d.restore()
    r=previous.old.r;parent,_=r.m.apply(parent,bytes.fromhex(d.read(ROOT/r.RECIPE)['after']))
    before=(ROOT/m.SOURCE).read_bytes();fixed=m.correct_source(before)
    need(identity(fixed)==recipe['source_after'] and identity(m.translation_unit())==recipe['translation_unit'],'canonical and compiled source binding')
    code=bytes.fromhex(recipe['after'])[:m.CODE['size']];candidate,rebuilt=m.apply(parent,code)
    need(identity(candidate)==raw['candidate']==m.CANDIDATE and all(recipe[k]==v for k,v in rebuilt.items()),'exact successor recipe and full rollback')
    refs=[]
    for i in range(0,len(parent)-3,2):
        a,b=struct.unpack_from('<HH',parent,i)
        if a&0xF800!=0xF000 or b&0xF800!=0xF800:continue
        delta=((a&2047)<<12)|((b&2047)<<1)
        if delta&0x400000:delta-=0x800000
        caller=0x08000000+i;target=caller+4+delta
        if m.START<=target<m.START+m.SIZE:
            refs.append({'caller':caller,'target':target})
            need(m.START<=caller<m.START+m.SIZE or target==m.START,'no external caller into overwritten veneer/body')
    need(refs==recipe['caller_references'],'all parent Thumb BL references')
    generated=m.root.generate(seed);need(generated.count(m.PARENT['sha256'].encode())==1,'one ROM binding')
    generated=generated.replace(m.PARENT['sha256'].encode(),m.CANDIDATE['sha256'].encode())
    need(identity(generated)==raw['generated'],'measured native source identity')
    baseline=d.read(ROOT/d.read(ROOT/r.CP)['measurement'])['accepted']['retry-zero']['observations'][0]
    accepted={}
    for case in m.root.prior.CASES:
        result=raw['cases'][case]
        if 'stdout_utf8' in result:out=result['stdout_utf8']
        else:
            need(result['stdout_from']==previous.RAW and result['stdout_case']==case=='v1-load-valid','explicit lossless prior output reference')
            out=d.read(ROOT/previous.RAW)['cases'][case]['stdout_utf8']
            for oldtext,newtext in result['stdout_replacements']:
                need(out.count(oldtext)==1,'one exact output delta');out=out.replace(oldtext,newtext)
        out=out.encode();err=result['stderr_utf8'].encode()
        need(identity(out)==result['stdout'] and identity(err)==result['stderr'] and result['returncode']==0 and not err,'actual clean process result')
        save,_=m.root.prior.fixture(seed,case);accepted[case]=m.validate(out,case,save,baseline)
        (d.PUBLIC/(case+'.stdout.txt')).write_bytes(out)
    need(raw['native_processes']==3 and raw['fresh_cores']==5 and raw['affected_accepted_reruns']==1 and raw['unnecessary_accepted_reruns']==0,'impact-limited rerun accounting')
    need(d.bindings(protected)==protected,'all previous evidence unchanged')
    (ROOT/m.SOURCE).write_bytes(fixed)
    cp={'schema_version':1,'task':TASK,'status':'PASS_V1_NORMAL_LOAD_SCOPED_PENDING_TERMINAL','source_head':os.environ['GITHUB_SHA'],
        'record_run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':m.CANDIDATE,'parent':m.PARENT,'recipe':RECIPE,'raw_evidence':RAW,
        'accepted':accepted,'accepted_cases':sorted(accepted),'failed_cases':[],'actions_completion_confirmed':False,
        'prior_record_terminal':prior_terminal,'protected_bindings':protected,'source_bindings':d.bindings(SOURCES),
        'native_processes_measured_once':3,'fresh_cores_measured_once':5,'arm_compiles_measured_once':1,'arm_links_measured_once':1,
        'host_compiles_measured_once':2,'new_unit_tests':20,'canonical_status_pairs':100,'record_native_runs':0,'record_unit_runs':0,'record_compiles':0,
        'affected_accepted_case_reruns':1,'affected_case':'v1-load-valid','unnecessary_accepted_reruns':0,'outside_declared_rom_changes':0,
        'v1_normal_load_accepted':True,'corrupt_load_rejections_accepted':True,'normal_new_game_accepted':False,
        'phase0_load_failure_accepted':False,'transaction_ui_accepted':False,'physical_flash_fault_accepted':False,
        'active_baseline_changed':False,'issue19_complete':False,'release_ready':False}
    publish(cp,{m.SOURCE})

def publish(cp,owned):
    summary='通常V1 loadの3件を受入。起動先行call誤認とQOLの空/破損混同を修復。破損checksum/tailは全入力とFlashを保持して拒否、正常V1は実保存と2回fresh Continue成功。'
    goal='次は通常load内のphase0保存不可境界・回復を限定実装/検証する。その後通常new-game/取引UI。3load/旧26unit/新40unit/7retry/BP/P08/特殊野生は変更影響なく再実行しない。'
    if not cp['actions_completion_confirmed']:goal='まず本record runの終端・push/uploadを照合する。'+goal
    cp['source_bindings']=d.bindings(SOURCES);d.write(ROOT/CP,cp)
    guide='# PR16 V1通常loadの破損拒否修復\n\n'+summary+'\n\n'+goal+'\n\n## 修正\n\nQOL restore_durable_ledgerが検証statusを返し、EMPTY_OR_LEGACY以外の保存原本は全2048byteをRAMへ保持。ensure_saveは空と破損を区別し、破損からSaveInitNewへ進まない。後続Mirage/Researchの既存検証がエラーを伝播する。候補 `'+m.CANDIDATE['sha256']+'`、32MiB。元58079dfbの既存0x09378DAC～0x09378E34の136byte窓のみ、132byteコンパイルcode、差分112byte、外側変更0、完全rollback一致。外部BLは関数入口のみで旧veneer内部への参照なし。新規領域の割当なし。\n\n## 検証\n\nchecksum/tailの通常cold boot/Continueはresult0、version1、last_result7、counter2、保存0。全ledger入力SHAと128KiB Flash不変をnative側で確認。正常V1はcounter2→3、phase0保存1回、全ledger移行、他owner/Bag/party不変、通常fieldおよび2回fresh Continueの完全一致。7host書込barrierを維持、RAM ledger/owner/PC/戻り値注入0。私有Flash fixtureであり歴史的ユーザーsaveそのものではない。\n\n修正候補native3process/5cores、ARM compile1/link1、native用host compile1。新規unit20件の中でcanonical Cをhost compile1/process1、100組のRAM/Flash statusを検証。先行call修復の新規20unitと合わせ計40件。元の26unit/7retry/他既受入は再実行0。正常V1だけは共有QOL変更の影響で1回回帰確認。ローカル測定原本・コンパイラ版・source/生成C/候補hashはJSONに記録し、Actionsでは再実行せず照合。\n\n## 未受入\n\nload内phase0保存不可/回復、通常new-game/取引UI、破損拒否後メニューUI全体、物理Flash故障、全catalog、Issue19、releaseは未完。merge/release/active baseline切替なし。以前の失敗原本は改変せず保持。\n\n## 実行記録\n\nrecord source `'+cp['source_head']+'`、run `'+str(cp['record_run_id'])+'`、終端確認 `'+str(cp['actions_completion_confirmed'])+'`。'+(' finalize run `'+str(cp['finalize_run_id'])+'`。' if 'finalize_run_id' in cp else '')+'\n'
    (ROOT/GUIDE).write_text(guide)
    state=d.read(ROOT/d.STATE);state['research_v1_corrupt_load']={k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','record_run_id','actions_completion_confirmed')};state['research_v1_corrupt_load']['path']=CP
    state['bp']['current_stop']=summary;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_V1_LOAD_PHASE0_FAILURE_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,RECIPE,RAW,MODEL,SELF,previous.MODEL,previous.old.C,previous.old.CP,previous.old.r.CP,m.SOURCE,'overlays/research_economy_v1/research_economy_v1.c'],stop_rule_ja='最新候補5d1fc9c4をrecipeで復元し、旧seed/ROM/原本を保全。未受入境界を昇格せず、merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='通常V1破損拒否の記録source。自己SHAはgit log参照。'
    state['observed_head_checks']={'scope_head':cp['source_head'],'runs':[{'id':cp['record_run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'限定record成功。全CI成功ではない。'}
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity((ROOT/path).read_bytes())
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-v1-corrupt-load-v1\n- Status: DONE（通常V1 load 3境界、その他未受入）\n- Summary: '+summary+'\n- Files changed: QOL canonical Cの2関数、136byte recipe、検証model/20tests/原本/checkpoint/guide、固定引継ぎMD/JSON、両ログ。\n- Verify: 修正候補native3/5cores、ARM compile1/link1、host compile2（runner/新規C分岐試験）。新規unit20/100 status pairs PASS。先行call新規20は再実行0。正常V1のみ変更影響回帰1、旧26unit/7retry/他受入再実行0。記録・終端確認のnative/unit/compile0。終端確認='+str(cp['actions_completion_confirmed'])+'。最終resume/task graph/scoped index guard/diff-check。\n- Commit: 同branch非force、source='+os.environ['GITHUB_SHA']+'、自己SHAはgit log。\n- Network: 固定GitHub artifact再利用、private payload新規tracked0。active baseline/merge/release変更0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f:f.write(log)
    d.write(d.OUT/'corrupt-owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS));d.put('record-summary.json',{k:cp[k] for k in ('status','candidate','accepted_cases','failed_cases','actions_completion_confirmed')})

def finalize():
    os.chdir(ROOT);d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(ROOT/CP)
    need(not cp['actions_completion_confirmed'],'already finalized; no duplicate')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'historical evidence unchanged')
    for path,binding in cp['source_bindings'].items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'unchanged measured source '+path)
    cp['terminal']=terminal(cp['record_run_id'],cp['source_head'],WF)
    cp.update(status='PASS_V1_NORMAL_LOAD_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set())

def guard():
    os.chdir(ROOT);cp=d.read(ROOT/CP);owned=set(d.read(d.OUT/'corrupt-owned.json'))
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected files unchanged')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('record | finalize | guard')
