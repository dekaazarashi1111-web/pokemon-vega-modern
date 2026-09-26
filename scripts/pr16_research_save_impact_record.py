#!/usr/bin/env python3
"""研究取引18件の原本記録と別runでの終端確定。native/ARMは実行しない。"""
from __future__ import annotations
import datetime, io, json, os
from pathlib import Path
import subprocess, sys, zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_save_impact as m
import pr16_research_public_evidence as public
bag=m.bag;need=m.need;identity=m.identity
TASK='USER-20260926-RESEARCH-SAVE-IMPACT'
SELF='scripts/pr16_research_save_impact_record.py'
TEST='tests/test_pr16_research_save_impact.py'
WF='.github/workflows/pr16-research-save-impact-record-20260926.yml'
CP='content/modernization/pr16_research_save_impact_checkpoint.json'
BASE='content/modernization/pr16_research_save_impact_evidence'
GUIDE='docs/PR16_RESEARCH_SAVE_IMPACT_JA.md'
STATE='content/modernization/pr16_native_supply_resume_20260913.json'
DOC='docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
LOGS={'design/run_log.md','design/version_log.md'}
CODE=m.SOURCES|m.ITEM_SOURCES|{SELF,TEST,WF,'scripts/pr16_research_save_impact.py','.github/workflows/pr16-research-save-impact-20260926.yml'}
PUB='scripts/pr16_research_public_evidence.py'
PUB_TEST='tests/test_pr16_research_public_evidence.py'
CODE|={PUB,PUB_TEST,'scripts/common.py','scripts/guard_private_files.py','scripts/pr16_learnset_runtime_record.py'}
MANDATORY={CP,STATE,DOC,GUIDE}|LOGS
OUT=ROOT/'.local/pr16-research-save-impact-record'
ARTS=[(False,36229142708,m.SOURCE,10902306338,'pr16-research-save-impact-native',26921,'992fca1b848c54977c6301d4f267e3a834b16359e6af8f5bced23c9d339c3105'),
      (True,36229762846,m.ITEM_SOURCE,10901613823,'pr16-research-bag-native',29835,'945e2b9b2dc70479761618a8702f3a1f873fad8d05fe1bd2374fb57e67b879f6')]


def read(name):return m.load((ROOT/name).read_bytes())
def write(name,value):
    p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def ref(name):return {'path':name,'binding':identity((ROOT/name).read_bytes())}
def dest():return BASE+'/'+os.environ['GITHUB_RUN_ID']


def source_bytes(sha,name):
    exists=subprocess.run(['git','cat-file','-e',sha+'^{commit}'],cwd=ROOT,capture_output=True)
    if exists.returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',sha],cwd=ROOT,check=True)
    return git('show',sha+':'+name)


def bound_artifact(fetch,number,name,size,digest,run,source):
    meta=fetch(f'actions/artifacts/{number}')
    need(meta['id']==number and meta['name']==name and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and not meta['expired'],'fixed artifact metadata')
    need(meta['workflow_run']['id']==run and meta['workflow_run']['head_sha']==source,'artifact source/run')
    raw=fetch(f'actions/artifacts/{number}/zip',binary=True)
    need(identity(raw)=={'size':size,'sha256':digest},'artifact exact bytes')
    return raw,{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')}


def run_summary(run):
    return {k:run[k] for k in ('id','head_sha','head_branch','event','path','status','conclusion','run_attempt','created_at','updated_at')}


def remember_originals(files,run):
    from guard_private_files import document_user_path_lines
    projection=public.project(files,4 if run==36229762846 else 3,document_user_path_lines)
    directory=BASE+'/'+str(run);need(not (ROOT/directory).exists(),'native evidence is immutable')
    for name,raw in projection.items():
        p=ROOT/directory/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    return {directory+'/'+name:identity(raw) for name,raw in projection.items()}


def record():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();need(not (ROOT/CP).exists(),'do not redo accepted record')
    need(identity((ROOT/bag.SOURCE).read_bytes())==bag.SOURCE_BEFORE,'unmodified canonical preimage')
    failed=fetch('actions/runs/'+str(public.FAILED_RUN));failed_jobs=fetch('actions/runs/'+str(public.FAILED_RUN)+'/jobs?per_page=100')
    public.verify_failed_run(failed,failed_jobs,WF)
    raw,_=bound_artifact(fetch,public.FAILED_ARTIFACT,'pr16-research-save-impact-record',public.FAILED_BINDING['size'],public.FAILED_BINDING['sha256'],public.FAILED_RUN,public.FAILED_SOURCE)
    protected=(m.SOURCES|m.ITEM_SOURCES|{TEST,'scripts/pr16_research_save_impact.py'})
    def unit_source(name):
        raw=(ROOT/name).read_bytes()
        return bag.correct_source(raw) if name==bag.SOURCE else raw
    reused_unit,reuse=public.reuse_unit(raw,unit_source,protected)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_public_evidence.py','-v'],cwd=ROOT,capture_output=True)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'new-unit.txt').write_bytes(unit.stdout+unit.stderr)
    (OUT/'reused-unit.txt').write_bytes(reused_unit)
    need(unit.returncode==0 and (unit.stdout+unit.stderr).count(b' ... ok\n')==12 and b'\nOK\n' in unit.stderr,'12 publication-only unit tests')
    bundles={};evidence={};runs=[];artifacts=[];originals={}
    for items,number,source,artifact,name,size,digest in ARTS:
        run=fetch(f'actions/runs/{number}');jobs=fetch(f'actions/runs/{number}/jobs?per_page=100')
        if items:m.terminal(run,jobs,source,m.ITEM_WF,'native')
        else:m.historical_terminal(run,jobs)
        raw,meta=bound_artifact(fetch,artifact,name,size,digest,number,source)
        files=m.unpack(raw,items);v=m.validate_bundle(files,source,number,lambda path:source_bytes(source,path),items)
        for path,binding in v['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'unchanged measured source '+path)
        key='items' if items else 'earn';bundles[key]=v;originals[key]=files
        v['original_artifact_member_bindings']=v.pop('public_evidence_bindings')
        v['tracked_publication_manifest']=BASE+'/'+str(number)+'/publication.json'
        v['publication_note']='compile.public.json is a declared path-redacted projection; original compile.json remains in the pinned artifact.'
        runs.append(dict(run=run_summary(run),jobs=jobs['jobs']));artifacts.append(meta)
        evidence.update(remember_originals(files,number))
        path=dest()+'/'+key+'-verification.json';write(path,v);evidence[path]=identity((ROOT/path).read_bytes())
    raw,_=bound_artifact(fetch,10898510128,'pr16-special-wild-gameplay-data',17366330,'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed',36218655601,'8660fe70f4354333cf7647186663cacafa04451b')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist())=={'candidate.gba','seed.srm','identity.json'} and len(z.infolist())==3 and sum(i.file_size for i in z.infolist())==33685811,'fixed candidate archive')
        need(identity(z.read('seed.srm'))==m.SEED,'read-only seed binding')
        parent,sr=m.repair.apply(z.read('candidate.gba'))
    candidate,br=bag.apply(parent);need(sr==m.load(originals['earn']['repair.json'])==m.load(originals['items']['repair.json']) and br==m.load(originals['items']['bag-repair.json']),'exact reconstruction receipts')
    corrected=bag.correct_source((ROOT/bag.SOURCE).read_bytes())
    audit=m.audit(candidate,(ROOT/m.CONFIG).read_bytes(),corrected,bag.CANDIDATE)
    (ROOT/bag.SOURCE).write_bytes(corrected)
    path=dest()+'/scope-audit.json';write(path,audit);evidence[path]=identity((ROOT/path).read_bytes())
    path=dest()+'/new-unit.txt';(ROOT/path).write_bytes(unit.stdout+unit.stderr);evidence[path]=identity((ROOT/path).read_bytes())
    for name,raw in [('reused-unit.txt',reused_unit),('unit-reuse.json',public.encode(reuse))]:
        path=dest()+'/'+name;(ROOT/path).write_bytes(raw);evidence[path]=identity(raw)
    pre=fetch('actions/runs/36228964902');need(pre['status']=='completed' and pre['conclusion']=='failure' and pre['head_sha']=='9866c4ce935927887daedb48ab2462f0ca7aa597','retain pre-native acquisition failure')
    manifest=dest()+'/evidence-manifest.json';write(manifest,evidence)
    need(len(bundles['earn']['results'])==8 and len(bundles['items']['results'])==10,'exact scoped acceptance count')
    cp={'schema_version':1,'task':TASK,'status':'PASS_RESEARCH_SAVE_IMPACT_18_SCOPED','scope':'SCHEDULED_PRODUCTION_TRANSACTION_SERVICES_NOT_NORMAL_TRANSACTION_UI',
        'session_start_head':'be751c120cea6bdaa58a6fa5240ab40a942e1cf6','candidate':bag.CANDIDATE,
        'accepted_case_keys':sorted(set(bundles['earn']['results'])|set(bundles['items']['results'])),'accepted_native_cases':18,'accepted_fresh_cores':54,
        'historical_actions_native_processes':26,'historical_actions_guard_processes':14,'historical_actions_host_compiles':2,'arm_compiles':0,'accepted_case_reruns':0,
        'local_diagnostics_ja':'別途ローカルfixture/IRQ/scheduler/Bag境界診断あり。正式18件やActions26processへ混入せず、タスク全体のnative数0とは主張しない。',
        'earn':{'measured_candidate':m.repair.CANDIDATE,'applies_to':bag.CANDIDATE,'source_head':m.SOURCE,'run_id':36229142708,'cases':sorted(bundles['earn']['results']),'verification':ref(dest()+'/earn-verification.json'),'applicability':'Only the unused Bag-capacity literal differs; CreditActivity/recover_pending/persist_phase bodies and all inputs are unchanged. Not executed again on the new candidate.'},
        'items':{'measured_candidate':bag.CANDIDATE,'source_head':m.ITEM_SOURCE,'run_id':36229762846,'cases':sorted(bundles['items']['results']),'verification':ref(dest()+'/items-verification.json')},
        'repair':br,'scope_audit':ref(dest()+'/scope-audit.json'),'evidence_manifest':ref(manifest),
        'canonical_source':dict(path=bag.SOURCE,binding=identity(corrected)),
        'actions_completion_confirmed':False,'normal_transaction_ui_accepted':False,'issue19_complete':False,'release_ready':False,'active_baseline_changed':False,
        'new_unit_tests':12,'reused_unit_tests':68,'unit_reuse':ref(dest()+'/unit-reuse.json'),'excluded_scopes':['normal transaction UI','all catalog rows','new save / V1 migration','phase0 failure injection','map3/19 excluded130 rows'],
        'preserved_formal_acceptance':['BP/P08','special-wild fishing/hidden UI 2 cases','active play baseline'],
        'record_source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE}}
    receipt={'mode':'record','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'new_native_processes':0,'host_compiles':0,'arm_compiles':0,'accepted_case_reruns':0,
             'new_unit_tests':12,'reused_unit_tests':68,'unit_reuse':reuse,'previous_publication_failure':run_summary(failed),'native_runs':runs,'artifacts':artifacts,'pre_native_failure':run_summary(pre),'evidence_manifest':cp['evidence_manifest'],
             'source_bindings':cp['record_source_bindings'],'private_rom_save_tracked':False}
    publish(cp,receipt,'record')


def finalize():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_wiki_actions import current
    current();cp=read(CP);need(cp['status']=='PASS_RESEARCH_SAVE_IMPACT_18_SCOPED' and cp['accepted_native_cases']==18 and not cp['actions_completion_confirmed'],'recorded, not re-finalized')
    prior=cp['record_receipt'];raw=(ROOT/prior['path']).read_bytes();need(identity(raw)==prior['binding'],'original record receipt binding')
    old=m.load(raw);run=fetch('actions/runs/'+str(prior['run_id']));jobs=fetch('actions/runs/'+str(prior['run_id'])+'/jobs?per_page=100')
    m.terminal(run,jobs,prior['source_head'],WF,'record')
    need(old['new_native_processes']==old['host_compiles']==old['arm_compiles']==0 and old['new_unit_tests']==12 and old['reused_unit_tests']==68,'original record scope')
    head=fetch('git/commits/'+os.environ['GITHUB_SHA']);need(len(head['parents'])==1,'linear finalize head');reflected=head['parents'][0]['sha'];parent=fetch('git/commits/'+reflected)
    need([p['sha'] for p in parent['parents']]==[prior['source_head']],'record commit is the direct nonforce parent')
    before=source_bytes(prior['source_head'],WF);after=(ROOT/WF).read_bytes()
    need(before.count(b'RESEARCH_MODE: record')==1 and after==before.replace(b'RESEARCH_MODE: record',b'RESEARCH_MODE: finalize'),'only explicit workflow phase change')
    for path,binding in cp['record_source_bindings'].items():
        if path!=WF:need(identity((ROOT/path).read_bytes())==binding,'recorded source unchanged '+path)
    manifest=cp['evidence_manifest'];need(identity((ROOT/manifest['path']).read_bytes())==manifest['binding'],'immutable proof manifest')
    for path,binding in read(manifest['path']).items():need(identity((ROOT/path).read_bytes())==binding,'immutable original proof '+path)
    cp['actions_completion_confirmed']=True
    receipt={'mode':'finalize','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'new_native_processes':0,'host_compiles':0,'arm_compiles':0,'new_unit_tests':0,'reused_unit_tests':80,'accepted_case_reruns':0,
             'record_run':run_summary(run),'record_jobs':jobs['jobs'],'reflected_record_commit':reflected,'record_receipt':prior,'evidence_manifest':manifest,
             'source_bindings':{p:identity((ROOT/p).read_bytes()) for p in CODE},'private_rom_save_tracked':False}
    publish(cp,receipt,'finalize')


def publish(cp,receipt,mode):
    from pr16_learnset_compact_record import publish_resume
    from pr16_wiki_reconcile import fetch
    path=dest()+'/receipt.json';need(not (ROOT/path).exists(),'immutable record receipt');write(path,receipt)
    cp['record_receipt' if mode=='record' else 'terminal_receipt']=dict(ref(path),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']))
    write(CP,cp)
    next_step=('共有研究取引の18境界とBag誤接続修正を受入。earn8件は実行候補23d58409を保持し2byte差分証明で限定適用、spend/rank10件は4aee03e8。再実行しない。次は保存新規初期化/V1移行とphase0失敗の未検証影響範囲を限定検証する。通常取引UI/全catalogは未受入。map3/19除外130行も未確定。' if mode=='finalize' else '共有研究18境界・Bag誤接続修正の原本記録済み。次はこの記録Actionsの終端成功とpushを確認し、同workflowのRESEARCH_MODEだけfinalizeへ変更する。native/旧unit/ARMを再実行しない。')
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n## 記録工程 '+mode+'\n\nsource `'+os.environ['GITHUB_SHA']+'` / run `'+os.environ['GITHUB_RUN_ID']+'`。受入18件、新unit='+str(receipt['new_unit_tests'])+'、この記録工程のnative/host compile/ARM/既受入再実行=0。canonical Cは正しい空き確認delegateへ同期。\n\n'+next_step+'\n')
    with (ROOT/GUIDE).open('a',encoding='utf-8') as f:f.write('\n公開記録補足: raw compiler receiptは固定Actions artifact内で原本保持し、Gitには絶対引数3+4個だけを識別子へ置換したcompile.public.jsonを保存する。publication.jsonに全memberの原本hash/公開hash/変換有無を明示し、他の原本memberはbyte同一。初回記録run36230558876はprivate guard failure・push未実行として保持。そこで成功した68試験は依存source hashと7942-byte transcriptを束縛して再利用し、修正後の記録工程は公開変換12試験だけを新規実行した。finalizeでは両方再実行しない。\n')
    s=read(STATE)
    s['research_save_impact']={'path':CP,'status':cp['status'],'candidate':cp['candidate'],'accepted_cases':18,'actions_completion_confirmed':cp['actions_completion_confirmed'],'record_receipt':cp['record_receipt'],'normal_transaction_ui_accepted':False}
    if mode=='finalize':s['research_save_impact']['terminal_receipt']=cp['terminal_receipt']
    s['bp']['current_stop']='共有研究保存の16取引境界と容量拒否2件、Bag容量delegate誤接続2byte修正を受入。'+('記録Actions終端成功を確認済み。' if mode=='finalize' else '記録Actions終端は別runで確認する。')
    s['bp']['next_step']=next_step
    s['next_action']=dict(s['next_action'],id='RESEARCH_SAVE_PHASE0_IMPACT' if mode=='finalize' else 'RESEARCH_SAVE_IMPACT_TERMINAL',goal_ja=next_step,
        read_paths=[GUIDE,CP,SELF,'scripts/pr16_research_save_impact.py','scripts/pr16_research_bag_delegate.py','scripts/pr16_research_save_delegate.py',bag.SOURCE,m.CONFIG],
        stop_rule_ja='固定候補identityと実行候補別の受入範囲を保持。fixture/scheduler実サービス試験を通常取引UI受入に昇格しない。既受入18件と特殊野生2件・BP/P08は影響がなければ再実行しない。新規/V1移行・phase0失敗・map3/19除外130行の未完を隠さず、merge/release/baseline変更をしない。')
    s['observed_head']=os.environ['GITHUB_SHA'];s['observed_head_semantics']='研究保存限定記録工程のsource HEAD。自己commit SHAはgit logで確認する。正式BP/P08の実行HEAD/candidateとは別であり置換しない。'
    runs=fetch('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=30')
    s['observed_head_checks']={'scope_head':m.ITEM_SOURCE,'runs':[{'id':36229762846,'head_sha':m.ITEM_SOURCE,'status':'completed','conclusion':'success'}],
        'previous_failed_runs':[{'id':36228964902,'conclusion':'failure'},{'id':36229142708,'conclusion':'failure','accepted_earn_cases':8,'failed_item_cases_retained':8},{'id':36230558876,'conclusion':'failure','failure_stage':'private guard; push skipped'}],
        'record_head':os.environ['GITHUB_SHA'],'record_head_runs':[{k:r[k] for k in ('id','name','head_sha','status','conclusion','path')} for r in runs['workflow_runs']],
        'reason_ja':'修正後native run36229762846は10件成功。元run36229142708はearn8成功/item8失敗のfailureを維持。記録runの終端は専用receiptで確定する。source-validation/P03等のaction_required・未完了を成功に読み替えず、全CI成功は主張しない。'}
    for name in CODE|{CP,GUIDE}:s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    s['logs_synchronized']=True;publish_resume(s)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-save-impact-{mode}-v1\n- Status: DONE（共有取引18境界の限定記録。新規/V1移行・phase0失敗・通常取引UI・Issue19/release未完）\n- Summary: 研究保存delegate影響を実Flashで検証し、Bag空き確認が所持確認へ誤結合する不具合を2byteとcanonical C 1macroで修正。earn8件の原本を再利用、修正候補spend/rank8件と実容量拒否2件を受入。元failure run36228964902/36229142708/36230558876を保持。compile receiptの絶対引数7個は明示した公開写像のみ除去し原本はartifactに保持。68試験は原本再利用、公開変換12試験を追加。\n- Files changed: 専用C/Python/unit/workflow、canonical research C、18件のUTF8証拠/公開写像/manifest/receipt、checkpoint、固定引継ぎMD/JSON、guide、両ログ。\n- Verify: 測定Actions=16+10 native（元失敗8を含む）、成功18件/54 fresh cores、guard7+7、host compile1+1、ARM0。別途ローカル診断あり。今回記録phase={mode}はnative/host/ARM/既受入再実行0、新unit={receipt["new_unit_tests"]}。resume check/task graph/最終index限定private guard後のみcommit。\n- Commit: 同branch非force push、remote HEAD照合。source={os.environ["GITHUB_SHA"]}、自己SHAはgit log参照。\n- Network: 固定Actions metadata/原本artifactのみ。ROM/save非tracked、正式BP/P08/野生原本/baseline不変、全CI/通常取引UI/全catalog成功は主張しない。\n'
    for name in LOGS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(log)
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'receipt.json').write_bytes((ROOT/path).read_bytes())
    write(str((OUT/'checkpoint.json').relative_to(ROOT)),cp)
    print(f'PASS: {mode}; scoped cases=18; new native/host/ARM/accepted reruns=0')


def allowed():
    cp=read(CP);paths=set(MANDATORY)|{bag.SOURCE}
    manifest=cp['evidence_manifest'];paths.add(manifest['path']);paths.update(read(manifest['path']))
    paths.add(dest()+'/receipt.json')
    return paths


def guard():
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set()
    actual=set(git('diff','--cached','--name-only','-z',g.START).decode().strip('\0').split('\0'))
    mandatory=MANDATORY|({bag.SOURCE} if os.environ['RESEARCH_MODE']=='record' else set())
    g.OWNED=m.guard_scope(allowed(),actual,mandatory);g.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)


if __name__=='__main__':
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['paths']:print('\n'.join(sorted(allowed())))
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('usage: record|finalize|paths|guard')
