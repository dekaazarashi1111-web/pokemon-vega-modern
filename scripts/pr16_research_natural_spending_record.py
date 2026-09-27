#!/usr/bin/env python3
"""ローカル原本の出所・新oracle・影響差分をActionsで記録。native再実行0。"""
from __future__ import annotations
import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_lifecycle_actions as d
import pr16_research_natural_spending_oracle as o
import pr16_research_shop_ui as patch
import pr16_research_natural_spending_probe as probe
START='509cea868a4e332edad805181a7b5525e3a2d6e2'
TASK='USER-20260927-RESEARCH-NATURAL-SPENDING'
CP='content/modernization/pr16_research_natural_spending_checkpoint.json'
RECIPE='content/modernization/pr16_research_shop_ui_recipe.json'
GUIDE='docs/PR16_RESEARCH_NATURAL_SPENDING_JA.md'
SELF='scripts/pr16_research_natural_spending_record.py'
WF='.github/workflows/pr16-research-natural-spending-record.yml'
LOADER='scripts/pr16_natural_spending_transfer.py'
OUT=ROOT/'.local/pr16-natural-record'
EVIDENCE=ROOT/o.BASE


def seed_and_parent():
    """固定dataだけ読取り、既存recipeを適用。旧build/native/受入試験を呼ばない。"""
    number,size,digest=10898510128,17366330,'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed'
    meta=d.inputs.api('actions/artifacts/'+str(number))
    o.need(not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==36218655601,'fixed data metadata')
    raw=d.inputs.api('actions/artifacts/'+str(number)+'/zip',True);o.need(o.identity(raw)==dict(size=size,sha256=digest),'fixed data ZIP')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        o.need(set(z.namelist())=={'candidate.gba','seed.srm','identity.json'} and len(z.infolist())==3,'closed data members')
        seed=z.read('seed.srm');parent=z.read('candidate.gba')
    o.need(o.identity(seed)==dict(size=131072,sha256='f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'),'read-only fixed seed')
    import pr16_research_save_delegate as a,pr16_research_bag_delegate as b
    import pr16_research_retry as c,pr16_research_v1_corrupt_load as v
    def recipe(name):return d.read(ROOT/'content/modernization'/name)
    parent,_=a.apply(parent);parent,_=b.apply(parent);parent,_=c.apply(parent,bytes.fromhex(recipe('pr16_research_retry_recipe.json')['after']))
    q=recipe('pr16_research_v1_corrupt_load_recipe.json');parent,_=v.apply(parent,bytes.fromhex(q['after'])[:v.CODE['size']])
    for name in ['pr16_research_map_view_recipe.json','pr16_research_counter_numeric_recipe.json','pr16_research_standard_list_ui_recipe.json']:
        q=recipe(name);o.need(o.identity(parent)==q['parent'],'saved recipe parent')
        parent=patch.edit(parent,q['patches']);o.need(o.identity(parent)==q['candidate'],'saved recipe candidate')
    o.need(o.identity(parent)==patch.PARENT,'accepted standard-list parent restored without rebuild')
    return seed,parent,meta


def source_proof(seed,parent):
    manifest=d.read(EVIDENCE/'manifest.json');o.need(d.bindings(set(manifest))==manifest,'all immutable original text evidence')
    provenance=d.read(EVIDENCE/'provenance.json')
    generated=probe.generate_ui(seed);o.need(generated==(EVIDENCE/'sources/ui.c.txt').read_bytes(),'actual generator reconstructs final measured source exactly')
    candidate,recipe=patch.apply(parent);o.need(recipe==d.read(ROOT/RECIPE),'recorded patch model and whole ROM rollback')
    # Restore saved objdump byte fields; no compiler invocation or invented instruction.
    memory={}
    for line in (EVIDENCE/'build/disassembly.txt').read_text().splitlines():
        match=re.match(r'^\s*([0-9a-f]+):\s*([0-9a-f ]+)\t',line)
        if not match:continue
        at=int(match[1],16);tokens=match[2].split()
        o.need(all(len(x) in (2,4,8) for x in tokens),'objdump bytes')
        raw=b''.join(int(x,16).to_bytes(len(x)//2,'little') for x in tokens)
        for i,b in enumerate(raw):o.need(at+i not in memory,'no duplicate disassembly byte');memory[at+i]=b
    o.need(set(memory)==set(range(patch.BASE,patch.BASE+64)) and bytes(memory[x] for x in sorted(memory))==patch.CODE,'complete saved 64byte assembly')
    # The final visual correction changes only the wide-frame clear delegate, not transactions.
    before=bytearray(candidate);before[0x1f4b030]=0xfd
    o.need(o.identity(bytes(before))==dict(size=33554432,sha256=o.SPEND),'one-byte UI successor of successful monetary candidate')
    o.need(provenance['final_impact']['changed_bytes']==1 and provenance['counts']['earning_prefix_executions']==1,'exact development/impact counts')
    sources={n:(EVIDENCE/'sources'/(n+'.c.txt')).read_bytes() for n in ('initial','logical','monetary','ui')}
    o.need({n:o.identity(b) for n,b in sources.items()}==provenance['raw_sources'],'all historical generated source bindings')
    prefixes=[]
    for raw in sources.values():
        raw=raw.split('/* 新しい稼得'.encode())[0]
        for digest in (o.EARN,'24d290518543c480c52657251a94f413e7eb63d3d33e14b0b8381fbe635dc8e4',o.SPEND,patch.CANDIDATE['sha256']):raw=raw.replace(digest.encode(),b'<CANDIDATE>')
        prefixes.append(raw)
    o.need(all(x==prefixes[0] for x in prefixes) and o.identity(prefixes[0])==provenance['guard_reuse']['common_prefix'],'unchanged original guard/helper prefix, no redundant guard rerun')
    guards=d.read(EVIDENCE/'guards.json');o.need(set(guards)=={'bus8','bus16','bus32','raw8','raw16','raw32','register'},'seven barrier methods')
    for row in guards.values():o.need(o.exact(row,dict(returncode=1,stdout='',stderr='research-save-impact: host write after observation barrier\n')),'original write denial')
    for trial,key in [('earn-1','initial'),('spend-1','initial'),('spend-2','logical'),('spend-3','monetary'),('ui-final','ui')]:
        exe=d.read(EVIDENCE/trial/'execution.json');o.need(exe['generated_source']==provenance['raw_sources'][key],'trial source '+trial)
        for stream in ('stdout','stderr'):o.need(o.identity((EVIDENCE/trial/(stream+'.txt')).read_bytes())==exe[stream],'original failure/success stream '+trial)
    o.need(d.read(EVIDENCE/'spend-1/execution.json')['returncode']==1 and (EVIDENCE/'spend-1/stderr.txt').read_bytes()==b'research-save-impact: bounded separated pixel allocation\n','first observer stop retained')
    for name in ('compile.stderr.txt','compile-v2.stderr.txt','compile-v3.stderr.txt','compile-ui.stderr.txt'):
        o.need((EVIDENCE/name).read_bytes()==b'','strict original host compile diagnostics')
    saved=(EVIDENCE/'patch-unit-v4.stderr.txt').read_bytes()
    o.need(saved.count(b' ... ok\n')==23 and b'\nOK\n' in saved,'final 23 patch tests reused, not rerun')
    return recipe,provenance


def record():
    os.chdir(ROOT);d.current();o.need(not (ROOT/CP).exists(),'no duplicate acceptance');OUT.mkdir(parents=True,exist_ok=True)
    state=d.read(ROOT/d.STATE)
    protected={p:b for p,b in state['source_bindings'].items() if p not in {GUIDE,RECIPE,SELF}}
    o.need(d.bindings(set(protected))==protected,'all previously bound sources remain unchanged')
    seed,parent,data_meta=seed_and_parent();zero,_=probe.fixture(seed);(OUT/'zero.srm').write_bytes(zero)
    recipe,provenance=source_proof(seed,parent)
    result=o.validate(EVIDENCE,zero)
    env=dict(os.environ,PR16_NATURAL_ZERO_INPUT=str(OUT/'zero.srm'))
    test=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_research_natural_spending','-v'],capture_output=True,timeout=90,env=env)
    for stream in ('stdout','stderr'):(OUT/('unit.'+stream+'.txt')).write_bytes(getattr(test,stream))
    o.need(test.returncode==0 and not test.stdout and test.stderr.count(b' ... ok\n')==120 and b'\nOK\n' in test.stderr,'120 new semantic/negative checks')
    prior=d.inputs.api('actions/runs/36314900752');o.need(prior['head_sha']=='c63448fa1ab349556530fe59a82d63946ca9e04f' and prior['status']=='completed' and prior['conclusion']=='success','prior standard-list acceptance terminal')
    prior_pending=[]
    for row in state['pending_runs']:
        run=d.inputs.api('actions/runs/'+str(row['run_id']));o.need(run['status']=='completed','reconcile earlier pending run');prior_pending.append(d.run_summary(run))
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    o.need(runs['total_count']==len(runs['workflow_runs'])<=50,'all recording source checks')
    transfer=d.read(OUT/'transfer.json');paths=set(transfer['files'])|{LOADER,WF,CP,RECIPE,GUIDE,d.STATE,d.DOC}|d.LOGS
    source_paths=set(transfer['files'])|{LOADER,WF,GUIDE,RECIPE}
    cp=dict(schema_version=1,task=TASK,**result,source_head=os.environ['GITHUB_SHA'],recording_run_id=int(os.environ['GITHUB_RUN_ID']),
            measurement_origin=provenance['measurement_environment'],source_base_head=provenance['source_base_head'],
            original_evidence=o.BASE+'/manifest.json',original_provenance=o.BASE+'/provenance.json',visual_review=o.BASE+'/visual-review.json',recipe=RECIPE,
            development_counts=provenance['counts'],retained_saves=provenance['retained_saves'],failures_preserved=provenance['failures_preserved'],
            patch_tests_reused=23,new_oracle_tests=120,oracle_stdout=o.identity(test.stdout),oracle_stderr=o.identity(test.stderr),
            recording_native_processes=0,recording_host_compiles=0,recording_arm_compiles=0,recording_guard_processes=0,
            data_artifact={k:data_meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run')},
            prior_standard_list_terminal=d.run_summary(prior),prior_pending_reconciled=prior_pending,
            actions_completion_confirmed=False,actions_completion_semantics='recording run must be checked by the next external API read; local native has no Actions run',
            source_actions=[d.run_summary(x) for x in runs['workflow_runs']],protected_bindings=protected)
    goal='自然稼得10RP→5個交換→残高0→独立Continueは限定受入。71byte shop UI後処理と最終12画面も受入。次は通常NewGame/ストーリー進行から研究活動・研究所へ到達する未完境界。既存badge/map/party/屋外warp fixtureを自然到達へ昇格しない。成功した稼得/支出save・数値2境界・標準リスト・旧4入口・旧稼得/BP/P08は変更影響なしに再実行しない。'
    guide=(ROOT/GUIDE).read_text()
    guide=guide.replace('## 進行中のsource checkpoint','## 保存済みsource checkpoint（以下は途中経過）',1)
    guide=guide.replace('# PR16 自然稼得RPのショップ支出\n','# PR16 自然稼得RPのショップ支出\n\n## 現在の限定受入\n\n`'+result['status']+'`\n\n'+goal+'\n\n正本checkpoint: `'+CP+'`。原本: `'+o.BASE+'`。\n',1)
    guide+='\n## 検証と記録\n\n固定Actions artifactのruntimeをローカルで使用した実測であり、Actions上のnative実測ではない。GitHubには原本stdout/stderr/実行identity/生成C全bytes/画面hashと直接視認所見を保存。PPM/ROM/save/runnerはtrackedに含めない。稼得1process、支出開発3process（観測前提停止1を含む）、最終UI-only1process。最後の表示修正は成功した支出候補の1byteだけで、保持済み10RP/0RP saveを開き、追加稼得/購入/保存0で12画面を確認。23patch試験原本を再利用し、独立oracle/拒否120件を記録Actionsで検証。Actionsの終端は外部からの次の読取で確定し、一般CI action_requiredをsuccessへ変更しない。\n'
    (ROOT/GUIDE).write_text(guide)
    cp['source_bindings']=d.bindings(source_paths-{GUIDE})
    d.write(ROOT/CP,cp)
    state['research_natural_spending']=dict(path=CP,status=result['status'],candidate=patch.CANDIDATE,source_head=cp['source_head'],run_id=cp['recording_run_id'],naturally_earned_spending_accepted=True,shop_ui_accepted=True,natural_story_progress_accepted=False)
    state['bp']['current_stop']=result['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='NATURAL_STORY_REACHABILITY_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,RECIPE,'docs/PR16_RESEARCH_STANDARD_LIST_JA.md','content/modernization/pr16_research_photo_checkpoint.json'],
        stop_rule_ja='RP稼得と支出は本checkpointの狭い連結で受入。通常進行/自然地理移動は別の未完境界。保存原本を優先し、無変更の受入済み入力・build・matrixを再実行しない。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'自然稼得RP支出は '+CP+'。実稼得入力1回だけを保持し、10RPから5個交換/0RP/Continueを受入。最後の表示1byte変更はUI-only・追加稼得/購入/保存0で受入。最終candidate e1efb100、12画面。旧数値/標準リスト/旧稼得/BP/P08を無変更で再実行しない。')
    state['observed_head']=cp['source_head'];state['observed_head_semantics']='ローカル実測のsource全bytesと原本を照合した記録Actions source。自己記録commit SHAではない。自然地理移動/通常進行は未受入。'
    state['observed_head_checks']=dict(scope_head=cp['source_head'],runs=cp['source_actions'],reason_ja='source HEADの一般CI action_required等も原値で保持。記録run終端は外部APIで別途確認する。')
    state['pending_runs']=[dict(run_id=x['id'],tested_head=x['head_sha'],status=x['status']) for x in runs['workflow_runs'] if x['status'] in ('queued','in_progress')]
    state['logs_synchronized']=True
    for path in source_paths|{CP}:state['source_bindings'][path]=o.identity((ROOT/path).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-natural-spending-shop-ui-v1\n- Status: DONE（自然稼得RP支出とshop UI限定。通常進行/自然移動は未完）\n- Summary: 実Rock Smashで0→10RPのsaveを1回だけ作成・保持。10RPでitem4を5個交換し0RP、lifetime/daily10/claim保持、自動保存2、別core Continueを確認。shopの純粋input/正しいframe/上余白を71byte修復。最後の1byte変更はUI-only・追加稼得/購入/保存0、12実画面を視認。\n- Files changed: 64byte Thumb source/recipe/patch検査、native観測器/独立oracle120件、失敗を含む原本text、専用MD/JSON、固定引継ぎMD/JSON、両ログ。\n- Verify: 最終23patch原本再利用、独立120検証PASS。全owner64/ledger2048/Bag/party600/Flash照合、保持したsaveの完全file一致、原本source再生成一致、全ROM rollback、accepted_case_reruns=0。記録Actionsでnative/host/ARM/guard実行0。全体historical guardや一般CI全成功は主張しない。\n- Development history: 初回pixel前提違い停止、旧2表示候補の残枠を保持。開発native計5（稼得1/支出3/UI-only1）、host compile4、production Thumb assemble/link4、guard7を同一prefixで再利用。\n- Commit: source={cp["source_head"]}; recording run={cp["recording_run_id"]}; task graph/resume/scoped final-index後に同branchへ非force push。自己SHAはremoteで確認。\n- Network: GitHub固定data artifact/APIのみ。ROM/save/画像/private原本tracked変更0、merge/release/baseline変更0。badge/party/map/屋外warpは明示fixture。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a',encoding='utf-8') as f:f.write(entry)
    o.need(d.bindings(set(protected))==protected,'all protected originals unchanged after record')
    d.write(OUT/'owned.json',sorted(paths));d.write(OUT/'summary.json',cp);print(json.dumps(cp,ensure_ascii=False))


def guard():
    import pr16_learnset_runtime_record as g
    import pr16_resume
    d.current();pr16_resume.validate(ROOT)
    g.START=START;g.CODE=set();g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


def snapshot():
    # Small text-only context for external terminal reconciliation, not another native run.
    files=set(d.read(OUT/'owned.json'))|{'CHATGPT_RESUME.md','AGENTS.md','scripts/pr16_resume.py','scripts/pr16_learnset_compact_record.py'}
    manifest=dict(source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),files={})
    with zipfile.ZipFile(OUT/'context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(files):
            b=subprocess.check_output(['git','show','HEAD:'+p],cwd=ROOT);b.decode();o.need(b'\0' not in b,'text only snapshot');z.writestr(p,b);manifest['files'][p]=o.identity(b)
        z.writestr('context-manifest.json',json.dumps(manifest,ensure_ascii=False,sort_keys=True))

if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    elif sys.argv[1:]==['snapshot']:snapshot()
    else:raise SystemExit('record|guard|paths|snapshot')
