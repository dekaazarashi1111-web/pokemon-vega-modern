#!/usr/bin/env python3
"""既測定の保存view修復だけを照合・記録。native/unit/compileは再実行しない。"""
from __future__ import annotations
import ast
import datetime
import io
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_map_view as m
import pr16_research_lifecycle_actions as d
from pr16_research_phase0_load_actions import terminal
from pr16_learnset_compact_record import publish_resume
need,identity=m.need,m.identity
TASK='USER-20260927-PHOTO-VISUAL'
SELF='scripts/pr16_research_map_view_actions.py'
WF='.github/workflows/pr16-research-photo-visual-20260927.yml'
RAW='content/modernization/pr16_research_map_view_local_measurement.json'
CP='content/modernization/pr16_research_map_view_checkpoint.json'
GUIDE='docs/PR16_PHOTO_VISUAL_DIAGNOSIS_JA.md'
BASE='content/modernization/pr16_research_map_view_evidence'
OLD='content/modernization/pr16_research_photo_checkpoint.json'
OLD_WF='.github/workflows/pr16-research-photo-20260927.yml'
TEST='tests/test_pr16_research_map_view.py'
MODEL='scripts/pr16_research_map_view.py'
AUX={'content/modernization/pr16_research_map_view_controls.json','content/modernization/pr16_research_map_view_unit.json'}
SOURCES={SELF,WF,RAW,MODEL,TEST,m.C,m.RECIPE}|AUX
GOAL='次は他5活動の実RP稼得、通常進行によるResearch受付/ショップ接続、残るnative文言。保存view修復後の研究候補26dac23cを専用recipeで復元する。旧候補の写真成功/取消/重複拒否と、新候補の513空判定/clear境界・写真cold表示・54検査は同一入力で再実行しない。自然到達・全活動・全map・releaseは未受入。'


def sources(raw):
    need(raw['inherited_source_binding_ref']==OLD and raw['inherited_source_binding_exclusions']==[OLD_WF],'closed inheritance')
    old=d.read(OLD)
    inherited={p:b for p,b in old['source_bindings'].items() if p!=OLD_WF}
    need(d.bindings(inherited)==inherited,'all prior measured source unchanged (including non-used CSV)')
    need(d.bindings(raw['source_bindings'])==raw['source_bindings'],'local implementation exact bytes')
    need(raw['historical_bindings_not_locally_used']=={'manifests/item_ids.csv':inherited['manifests/item_ids.csv']},'explicit absent local CSV is not a measured dependency')
    return d.bindings(set(inherited)|SOURCES)


def payload(raw,key):
    spec=raw[key];need(spec['path'] in AUX,'known public measurement path')
    data=Path(spec['path']).read_bytes();need(identity(data)==spec['binding'],'immutable '+key+' transcript')
    return m.load(data)


def restore_parent():
    """固定data ZIPだけを読む。既受入ARM/host/nativeは実行しない。"""
    name,number,size,digest,count,total=next(s for s in d.inputs.SPECS if s[0]=='data')
    meta=d.inputs.api('actions/artifacts/'+str(number))
    need(not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==36218655601,'pinned data metadata')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True)
    need(identity(raw)=={'size':size,'sha256':digest},'pinned data archive')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.infolist())==count and set(z.namelist())=={'candidate.gba','seed.srm','identity.json'} and sum(e.file_size for e in z.infolist())==total,'exact safe data members')
        for e in z.infolist():
            p=PurePosixPath(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and e.external_attr>>28!=10 and not e.is_dir(),'regular data member')
        original=z.read('candidate.gba');seed=z.read('seed.srm')
    need(identity(seed)==d.m.old.SEED,'fixed seed')
    parent,sr=d.save.apply(original);parent,br=d.bag.apply(parent)
    import pr16_research_retry as retry
    import pr16_research_v1_corrupt_load as corrupt
    parent,rr=retry.apply(parent,bytes.fromhex(d.read('content/modernization/pr16_research_retry_recipe.json')['after']))
    recipe=d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
    parent,cr=corrupt.apply(parent,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']])
    need(identity(parent)==m.PARENT,'same exact parent without recompilation')
    candidate,mr=m.apply(parent)
    d.put('reconstruction.json',dict(input_artifact={k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')},parent=identity(parent),candidate=identity(candidate),save=sr,bag=br,retry=rr,corrupt=cr,map_view=mr,arm_compiles=0,arm_links=0,host_compiles=0,native_processes=0))
    return seed,candidate


def verify_measurements(raw,seed,candidate):
    need(raw['environment']=='ChatGPT Linux container; not an Actions native run','measurement provenance')
    need(raw['candidate']==identity(candidate) and raw['parent']==m.PARENT,'measured ROM identities')
    fixture,receipt=m.photo.fixture(seed);need(raw['fixture']==receipt,'measured zero-RP fixture')
    code=m.generate(seed,raw['candidate']);c=Path(m.C).read_bytes()
    adj=raw['source_adjudications'];need(len(adj)==1 and adj[0]['case']=='predicate-boundary','one explicit source correction')
    a=adj[0];old,new=a['old_literal'].encode(),a['new_literal'].encode()
    need((old,new)==(b'h=0x02037130U',b'h=0x02036D30U') and c.count(new)==code.count(new)==1,'exact unused observer correction')
    need(identity(c)==a['after_source'] and identity(c.replace(new,old))==a['before_source'],'predicate and all dependencies unchanged')
    generated={'predicate-boundary':code.replace(new,old),'photo-cold-visual':code}
    accepted={}
    need(set(raw['cases'])==set(generated),'two new scoped measurements only')
    for case,result in raw['cases'].items():
        out=result['stdout'].encode();need(not result['stderr'] and identity(out)==result['stdout_identity'],'clean bounded native transcript')
        need(identity(generated[case])==result['generated_source'],'exact native generated source '+case)
        need(result['terminal']=='PASS followed immediately by return 0 in the bound main; numeric shell exit status not separately persisted','exit-status evidence limitation retained')
        accepted[case]=m.validate(out,case,raw['candidate'],fixture,m.SCREENS)
        (d.PUBLIC/(case+'.stdout.txt')).write_bytes(out)
    need(raw['screens']['visual-cold.ppm']['identity']==raw['screens']['visual-earned.ppm']['identity'],'warm/cold image byte identity')
    expected=dict(m.SCREENS,**{'photo-earn-prompt.ppm':m.photo.SCREENS['photo-earn-prompt.ppm'],'photo-earn-outcome.ppm':m.photo.SCREENS['photo-earn-outcome.ppm']})
    need(set(raw['screens'])==set(expected),'exact reviewed image inventory')
    for name,digest in expected.items():
        need(raw['screens'][name]['identity']=={'size':115215,'sha256':digest},'actual PPM identity')
        if name.startswith('visual-'):need(raw['screens'][name]['visually_reviewed'] is True,'new field images reviewed')
    unit=payload(raw,'unit');current=Path(TEST).read_bytes()
    before=b"False if type(value) is bool else 1 if type(value) is int else 'bad'"
    after=b"False if type(value) is bool else value+1 if type(value) is int else 'bad'"
    need(current.count(after)==1 and identity(current)==unit['final_source'] and identity(current.replace(after,before))==unit['initial_source'],'only one failed test harness method changed')
    initial,target=unit['initial_stderr'],unit['targeted_stderr']
    pattern=r'^(test_\w+) \(test_pr16_research_map_view.MapViewTests\.\1\) \.\.\. (ok|FAIL)$'
    rows=re.findall(pattern,initial,re.M);tail=re.findall(pattern,target,re.M)
    tree=ast.parse(current)
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='MapViewTests')
    names={n.name for n in klass.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    mutation=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='MUTATIONS' for t in n.targets))
    need(isinstance(mutation,ast.Dict),'literal mutation names')
    names|={'test_reject_'+ast.literal_eval(k) for k in mutation.keys}
    need(len(names)==len(rows)==54 and {n for n,s in rows}==names and sum(s=='ok' for n,s in rows)==53,'53 unchanged passes and one recorded harness failure')
    need([(n,s) for n,s in rows if s!='ok']==[('test_boundary_mutations','FAIL')] and tail==[('test_boundary_mutations','ok')],'only failed method retried')
    need('Ran 54 tests' in initial and initial.endswith('FAILED (failures=1)\n') and 'Ran 1 test' in target and target.endswith('\nOK\n'),'original initial failure not rewritten')
    need(unit['accepted_tests']==54 and unit['first_passed']==53 and unit['first_failed']==unit['targeted_passed']==1,'unit counting')
    (d.PUBLIC/'unit-initial-sanitized.txt').write_text(initial);(d.PUBLIC/'unit-targeted.txt').write_text(target)
    controls=payload(raw,'controls');need([r['case'] for r in controls]==['manual-save-control','delegate-save-control'],'two distinct old-parent diagnostics')
    base=m.photo.generate(seed).decode().replace('int main(int argc,char**argv){','int accepted_photo_main(int argc,char**argv){').encode()
    for row in controls:
        out=row['stdout'].encode();need(not row['stderr'] and identity(out)==row['stdout_identity'] and identity(base+row['source_suffix'].encode())==row['generated_source'],'old control source/stdout exact')
        states=[r for r in map(m.load,out.splitlines()) if 'stage' in r]
        labels=['warp','saved','cold'] if row['case']=='manual-save-control' else ['direct-before','direct-cold']
        need([s['stage'] for s in states]==labels and [s['counter'] for s in states]==([2,3,3] if len(labels)==3 else [2,3]) and all(s['map']==[96,37] and s['saved_layout_id']==497 and s['ram_headers']==states[0]['ram_headers'] for s in states),'same map/layout/tilesets for control')
        expected_cold='ff4a943e8bf4084af8f5dbf7150c17d2e64b29a6b61dbd8ec30276448e7ff85e' if len(labels)==3 else 'e5dc8b65607ab06b09f9989ec991abb26334555d6833065d412baedd37118098'
        need(states[-1]['screen']==expected_cold,'normal Save passes, delegate-only recreates blue field')
        (d.PUBLIC/(row['case']+'.stdout.txt')).write_bytes(out)
    need(raw['counts']==dict(diagnostic_native_processes=2,diagnostic_fresh_cores=4,diagnostic_host_compiles=2,accepted_native_processes=2,accepted_fresh_cores=3,accepted_host_compiles=2,readonly_disassembler_host_compiles=1,arm_compiles=0,arm_links=0,unit_processes=2,unit_tests_accepted=54,initial_unit_harness_failures=1,accepted_case_impact_regressions=1,unchanged_accepted_case_reruns=0,guard_processes=0,changed_rom_bytes=1),'honest complete execution counts')
    return accepted


def record():
    d.current();need(not Path(CP).exists(),'record exists; do not repeat')
    d.PUBLIC.mkdir(parents=True)
    raw=d.read(RAW);bound=sources(raw);old=d.read(OLD)
    need(old['photo_accepted'] and old['actions_completion_confirmed'] and not old['cold_field_visual_accepted'],'prior photo RP only')
    need(d.bindings(old['protected_bindings'])==old['protected_bindings'],'all old evidence preserved')
    prior=terminal(old['finalize_run_id'],old['finalize_source_head'],OLD_WF)
    tracked=d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')],'nested rules need review')
    protected=d.bindings(set(old['protected_bindings'])|set(old['source_bindings'])|{OLD,'docs/PR16_RESEARCH_PHOTO_JA.md'}|{p for p in tracked if p.startswith('content/modernization/pr16_research_photo_evidence/')})
    # Metadata only for the already-used fixed emulator; no second runtime download/build.
    meta=d.inputs.api('actions/artifacts/'+str(raw['runtime']['artifact_id']))
    need(meta['digest']=='sha256:'+raw['runtime']['artifact_sha256'] and meta['workflow_run']['id']==36218655601,'measured fixed emulator artifact')
    need(raw['runtime']['library']=={'size':1968536,'sha256':'0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'},'measured emulator library')
    seed,candidate=restore_parent();accepted=verify_measurements(raw,seed,candidate)
    d.put('recorder-preflight.json',dict(status='PASS_LOCAL_RECORD_PREFLIGHT',native_runs=0,unit_runs=0,preflight_rejections_before_correction=3,corrections_ja=['ASTの定数評価を辞書キーだけに限定','delegate対照は2段階の原本であり通常Saveの3段階を要求しない','seed定数の参照先を既存lifecycleへ訂正']))
    d.put('measurement-reconciliation.json',dict(status='PASS_LOCAL_MEASUREMENTS_RECONCILED',measurement=RAW,measurement_binding=identity(Path(RAW).read_bytes()),source_bindings=bound,accepted=accepted,counts=raw['counts'],record_native_runs=0,record_unit_runs=0,record_compiles=0,prior_terminal=prior))
    directory=BASE+'/'+os.environ['GITHUB_RUN_ID'];need(not Path(directory).exists(),'append-only record evidence')
    manifest={}
    for p in sorted(d.PUBLIC.iterdir()):
        data=p.read_bytes();data.decode('utf-8');need(p.suffix in ('.json','.txt') and b'\0' not in data and len(data)<2000000,'bounded public text only')
        target=Path(directory)/p.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);manifest[str(target)]=identity(data)
    d.write(Path(directory)/'manifest.json',manifest)
    cp=dict(schema_version=1,task=TASK,status='PASS_MAP_VIEW_REPAIR_PENDING_TERMINAL',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=identity(candidate),parent=m.PARENT,source_bindings=bound,protected_bindings=protected,raw_measurement=RAW,recipe=m.RECIPE,accepted_cases=sorted(accepted),failed_cases=[],counts=raw['counts'],manifest=directory+'/manifest.json',measurement=directory+'/measurement-reconciliation.json',actions_completion_confirmed=False,cold_field_visual_accepted=True,scope='LOCAL_NATIVE_MEASUREMENTS_ACTIONS_SOURCE_AND_EVIDENCE_RECONCILIATION',all_activities_accepted=False,natural_arrival_accepted=False,all_maps_accepted=False,release_ready=False,active_baseline_changed=False,prior_photo=OLD,prior_terminal=prior)
    publish(cp,set(manifest)|{directory+'/manifest.json'},'record')


def publish(cp,owned,mode):
    d.write(CP,cp)
    guide=f'''# PR16 保存view空判定と写真cold表示の修復

{cp['status']}

{GOAL}

## 原因と最小修正

保存viewはSaveBlock2+0x898から512bytes。空判定0x08058A14のliteral0x08058A48が511で、隣接ownerを含む1024bytesを走査していた。空のviewでも隣接データを非空と誤判定し、Continue時にゼロタイルを地形へ復元する。通常Saveのview snapshot(15x14半語)がある対照は正常、保存delegateだけの対照は青背景を再現。map96/37、layout497、72x20、primary/secondaryの同一性を両対照で確認。warp/tileset変更やRP保存処理の変更は不要。

literalの上限511→255（ff010000→ff000000）だけを変更。実差分1byte、全ROM rollback一致、ARM compile/link0、追加allocation0。clear0x08058A54→CpuSetのnative ABIも512bytesと一致し、隣接512bytesは不変。

親 `{cp['parent']['sha256']}` → 後継 `{cp['candidate']['sha256']}`、各33554432bytes。recipe `{m.RECIPE}`。BP/P08候補やactive baselineの切替ではない。固定data artifact10898510128をsave/bag/retry/V1修復まで復元してから `pr16_research_map_view.apply(parent)` を適用する。後続研究検証もこの順序を使う。

## 実測と限定受入

ローカル新規native2process/3fresh cores。空判定はゼロ1・内側256・外側256=513、全1024byte読取不変。clear1回で512byteだけ消去し隣接ownerとFlashを保全。

写真cold表示は変更影響回帰1件。停止warp後は通常キーだけ、写真実稼得0→6RP、日内/生涯6、claim4、保存counter2→4→4。全Bag/party600/ledger2048（自然minuteのみ除外）と独立Continue/確認台詞時の全Flash不変。稼得後とcold地形PPMは完全一致（e6aa09ed93ed4fd42593a0584509e2cc08ec309cf387c8cf836aad724dc4e1bc）。cold確認画面は旧受入のwarm promptと完全一致（b7bed16f0c7216dea297a2c408332b193f26272bd90ded4efc38259516784895）。建物・木・道・池と台詞を目視した。取消/同日重複拒否は再実行しない。

54種類の新規unitは初回53PASS+1harness失敗。zero_case=1を1へ置換していた無変異テストだけvalue+1へ修正し、その1メソッドを再実行してPASS。53成功は再実行0。初回失敗/原source hashと訂正原本を保存。テスト全文の差分はこの1箇所だけ。predicate成功後、未実行photo observerのheader定数だけを最初の写真実行前に訂正して別host compile。predicate本体/依存は不変なので513判定の再実行0。

ローカル診断は別2native/4cores/2host compile、修正受入は2native/3cores/2host compile、読取disassembler用host compile1。ARM0。新規unit実行2process、異なる54検査。変更影響回帰1、無変更受入再実行0、既受入7API拒否原本再利用でguard process0。

nativeは拘束されたmainの末尾PASS直後にreturn0、stderr空。ただしshell数値exit codeを独立ファイルへ保存していないため、保存したという主張はしない。画像はローカル実測でありActionsが新撮影したものではない。

## Actions・原本・残る境界

記録source `{cp['source_head']}` / run `{cp['run_id']}`。`{cp['measurement']}`、`{RAW}`、`{cp['manifest']}`。Actionsでは固定data/全source/生成C/全ROM rollbackと原本oracleを照合し、native/unit/compile再実行0。終端確認: {cp['actions_completion_confirmed']}。旧写真run36253608437の青背景とRP受入原本はそのまま保全し、この後継修復への参照を固定引継ぎに追加する。

自然到達、他5活動、通常進行から受付/ショップ、全map/全会話、releaseは未受入。一般CIの既存P03 source pin failure/承認待ちは今回の限定PASSとは別で、全CI成功を主張しない。引継ぎ/両ログ/限定index guardの完了後に同branchへ非force push。
'''
    Path(GUIDE).write_text(guide)
    state=d.read(d.STATE)
    state['research_map_view']={k:cp[k] for k in ('status','source_head','run_id','candidate','cold_field_visual_accepted','actions_completion_confirmed')}
    state['research_map_view'].update(path=CP,recipe=m.RECIPE,measurement=RAW)
    state['research_current_candidate']=dict(cp['candidate'],recipe=m.RECIPE,checkpoint=CP,baseline_switch=False)
    state['research_photo']['successor_visual_resolution']=dict(path=CP,candidate=cp['candidate'],original_candidate_finding_retained=True)
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=GOAL
    state['next_action']=dict(state['next_action'],id='RESEARCH_OTHER_ACTIVITIES_AND_NATURAL_CONNECTION_NEXT',goal_ja=GOAL,read_paths=[GUIDE,CP,m.RECIPE,MODEL,SELF,m.C,'content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c','docs/PR16_RESEARCH_CATALOG_JA.md','content/modernization/pr16_research_catalog_checkpoint.json','docs/PR16_RESEARCH_NEW_GAME_JA.md'],stop_rule_ja='旧写真/元ROM/seed/原本不変。後継26dac23cの保存view修復scopeを全map/自然到達へ拡張しない。変更影響がない受入再実行、merge/release/baseline変更禁止。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='保存view修復の記録source。native実測はローカルsource hash照合、Actions実測と混同しない。自己SHAはgit log参照。'
    runs=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=12')['workflow_runs']
    state['observed_head_checks']=dict(scope_head=os.environ['GITHUB_SHA'],runs=[d.run_summary(r) for r in runs],reason_ja='保存viewの限定受入と一般CIは別。P03旧source pin failure/承認待ちを全CI成功へ昇格しない。現実行の完了は次のterminal照合/remote refで確認。')
    for path in SOURCES|{CP,GUIDE}:state['source_bindings'][path]=identity(Path(path).read_bytes())
    note='保存view修復26dac23cは513空判定/clear512byteと写真cold地形/台詞を専用checkpointで受入。54unitは初回53成功+訂正1成功。無変更再実行禁止。旧5d1fc9c4の青背景記録は歴史原本で、後継受入と混同しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-map-view-v1\n- Status: '+('DONE' if cp['actions_completion_confirmed'] else 'VERIFIED_PENDING_TERMINAL')+'（写真cold表示の限定scope）\n- Summary: 保存view空判定の隣接owner overreadを上限511→255の1byte修正で解消。'+mode+'。\n- Files changed: 1byte recipe/検証Python・C/54tests/原本/checkpoint/guide/固定引継ぎMD・JSON/両ログ。\n- Verify: 診断2native/4cores/2host、修正受入2native/3cores/2host、読取utility host1。ARM0。unit初回53PASS+1harness失敗、失敗1のみ修正再実行PASS。写真変更影響回帰1、無変更受入再実行0。Actions native/unit/compile0。全ROM rollback/原本hash/生成C/独立oracleを照合。resume/task graph/index guardは後続stepで検査。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force push、自己SHAはgit log参照。\n- Network: 固定GitHub data取得・runtime metadata参照。新規ROM/save tracked0、baseline/merge/release不変。全CI/自然到達/全活動/全map受入ではない。\n'
    for path in sorted(d.LOGS):
        with Path(path).open('a') as f:f.write(log)
    d.write(d.OUT/'map-view-owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))
    d.put('summary.json',{k:cp[k] for k in ('status','source_head','run_id','candidate','accepted_cases','actions_completion_confirmed')})


def finalize():
    d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(CP)
    need(not cp['actions_completion_confirmed'],'already finalized')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'old evidence unchanged')
    for p,b in cp['source_bindings'].items():
        if p!=WF:need(identity(Path(p).read_bytes())==b,'record source unchanged '+p)
    cp['terminal']=terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_MAP_VIEW_REPAIR_SCOPED',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal.json',cp['terminal']);publish(cp,set(),'finalize')


def guard():
    cp=d.read(CP);owned=set(d.read(d.OUT/'map-view-owned.json'))
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'protected files unchanged')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    else:raise SystemExit('record | finalize | guard')
