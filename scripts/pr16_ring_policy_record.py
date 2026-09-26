#!/usr/bin/env python3
"""通常戦闘Ringの既存Actions原本を検証・記録する。nativeは再実行しない。"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='1d313d9c6ca706251fbdc2debdd5a471241e0c31'
TASK='USER-20260918-RING-POLICY-CLOSEOUT'
SELF='scripts/pr16_ring_policy_record.py'
TEST='tests/test_pr16_ring_policy_record.py'
WORKFLOW='.github/workflows/pr16-ring-policy-record.yml'
SPEC='content/modernization/pr16_ring_policy_record_spec.json'
REPORT='content/modernization/pr16_ring_policy_acceptance.json'
GIFT='content/modernization/pr16_ring_npc_gift_checkpoint_20260918.json'
OUT=ROOT/'.local/pr16-ring-policy-record'
IMPLEMENTATION=('scripts/pr16_ring_policy_successor.py','tests/test_pr16_ring_policy_build.py',
    'scripts/pr16_ring_policy_native.py','tests/test_pr16_ring_policy_native.py',
    'tools/mgba_pr16_ring_policy.c','.github/workflows/pr16-ring-policy.yml')
RING='P05_NATIVE_RING_ACQUISITION_PHYSICAL'
POLICY='P05_ORDINARY_POLICY_SELECTION_PHYSICAL'
BP_SHA='ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b'
CANDIDATE={'size':33554432,'sha256':'4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'}
PROCESS={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}
STOP=('通常戦闘のRing bridgeを受入済みNPC候補から限定実装。NPC正規受取→Bag Give→通常Save/fresh Continue→'
      '自然遭遇→既存メガUI→技使用→戦闘後復帰→Save/fresh Continueの新規5件を検証。'
      '選択/不選択/取消、未所持/別の石の対照を含む。Ring/policyの2つのphysical IDをこのscoped候補で閉じ、'
      'CircusとP08最終候補への移送・releaseは未完。正式BP候補ceddbe91と旧原本は維持する。')
NEXT=('PHYSICAL_CIRCUS_ADMISSIONの実受付/入場ownerから特性抑制までの最小経路を進める。'
      'content/modernization/pr16_p05_supply_owner_findings.jsonの未解決箇所から始め、'
      'map12/7をCircusと仮定せず、flag直接注入で入場を代用しない。'
      'Ring/policyの受入済み5件とNPC3件、BP/P03/P06/P07は変更影響なしに再実行しない。'
      'Circus修復後に変更ROM範囲/owner/runner/fixture/契約を照合してP08最終候補へ移送する。')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def stable(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def unpack(raw,bound):
    need(identity(raw)==bound,'artifact ZIP identity differs')
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(0<len(archive.infolist())<400,'artifact member count outside limit')
        for info in archive.infolist():
            p=PurePosixPath(info.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                 and info.filename not in files and not info.is_dir(),'unsafe/duplicate ZIP member')
            need(info.file_size<2000000 and (info.external_attr>>16)&0o170000!=0o120000,'unsafe ZIP type/size')
            need(p.suffix in {'.json','.txt','.stdout','.stderr','.log','.c','.h','.py','.csv','.png'},'private artifact suffix')
            data=archive.read(info)
            if p.suffix!='.png':
                data.decode('utf-8');need(b'\0' not in data,'non-text evidence member')
            files[info.filename]=data
    manifest=json.loads(files['members.json'])
    need(set(files)==set(manifest)|{'members.json'},'artifact member manifest differs')
    for name,meta in manifest.items():
        need(identity(files[name])=={k:meta[k] for k in ('size','sha256')},'artifact member identity differs: '+name)
    return files,manifest


def verify_process(row):
    need(type(row) is dict and set(row)==set(PROCESS),'process schema differs')
    for key,value in PROCESS.items():
        need(type(row[key]) is type(value) and row[key]==value,'native process failed: '+key)


def verify_sources(bindings,root):
    need(type(bindings) is dict and bindings,'missing source identities')
    for name,meta in bindings.items():
        p=PurePosixPath(name)
        need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,'unsafe source path')
        need(identity((root/name).read_bytes())==meta,'tested source changed: '+name)


def validate_bundle(files,manifest,spec,root=ROOT):
    from scripts import pr16_ring_policy_native as native
    b=json.loads(files['pr16-ring-policy-successor/candidate.json'])
    n=json.loads(files['pr16-ring-policy-native/result.json'])
    need(b['source_head']==spec['tested_head'] and b['run_id']==spec['run_id'],'builder Actions identity differs')
    need(b['candidate']==n['candidate']==CANDIDATE and b['crc32']=='9EFB0E56','new candidate differs')
    need(b['parent']==n['parent']==dict(size=33554432,sha256='72fbca91cd6ee1082198678ccaed76bcb76dfd19ce9f6f3c26309745b2f09ac0'),'NPC parent differs')
    need(b['independent_policy_compiles']==2 and b['original_entry_changed_bytes']==8
         and b['undeclared_changed_bytes']==0 and b['npc_payload_changed'] is False
         and b['save_layout_changes']==0 and b['existing_allocations_rehashed']==[]
         and b['allocation']['summaries']['overlap_count']==0,'bounded ROM impact differs')
    need(b['payload']['size']==172 and b['payload_offset']==33507864
         and b['displaced_prologue_hex']=='f0b545464e46de46','bridge ABI differs')
    need(n['status']=='PASS_RING_ORDINARY_SUFFIX_ONLY' and n['failures']==[],'native result not successful')
    need(n['actual_new_processes']==5 and n['successful_fresh_cores']==15
         and n['accepted_native_cases_replayed']==0 and n['requested_cases']==list(native.CASES),'native case accounting differs')
    for source in (b,n):
        for key in ('ordinary_battle_accepted','ring_full_acceptance','release_ready'):
            need(source[key] is False,'raw result promoted acceptance')
        verify_sources(source['sources'],root)
    need(n['physical_host']==[96,17,4,12,38],'NPC physical owner differs')
    proof=n['oracle']['flag_contract']
    flags=native.flag_contract('\n'.join(proof['definitions'].values()))
    need(flags['master']==proof['master']==4 and flags['link']==proof['link']==2,'pinned flag proof differs')
    cfg=json.loads((root/'config/github_private_environment.json').read_bytes())
    archived=next(a for a in cfg['archives'] if a['name']==proof['archive']['name'])
    need(proof['archive']=={k:archived[k] for k in ('name','size','sha256')},'flag archive binding differs')
    verify_process(json.loads(files['pr16-ring-policy-native/compile.process.json']))
    for name,binding in n['generated'].items():
        need(identity(files['pr16-ring-policy-native/generated/'+name])==binding,'compiled helper differs')
    need(len(n['guard_checks'])==7 and len(set(n['guard_checks']))==7,'seven guard checks missing')
    for name in n['guard_checks']:
        prefix='pr16-ring-policy-native/guard-'+name
        need(files[prefix+'.stdout']==b'' and files[prefix+'.stderr']==b'P03 archive: host write after observation barrier\n','guard did not reject write')
        process=json.loads(files[prefix+'.process.json']);verify_process(dict(process,returncode=0))
        need(type(process['returncode']) is int and process['returncode']==1,'guard exit differs')
    need(len(n['results'])==5 and {r['case'] for r in n['results']}==set(native.CASES),'case set missing/duplicated')
    originals={}
    for case in n['results']:
        name=case['case'];prefix='pr16-ring-policy-native/'+name
        raw=files[prefix+'.stdout'];stderr=files[prefix+'.stderr'];row=json.loads(raw)
        process=json.loads(files[prefix+'.process.json']);verify_process(process)
        need(process==case['process'] and row==case['native_result'],'native original/projection differs')
        native.validate(row,stderr,name,n['oracle'])
        originals[name]={suffix:dict(identity=identity(files[prefix+'.'+suffix]),
            utf8=files[prefix+'.'+suffix].decode('utf-8')) for suffix in ('stdout','stderr','process.json')}
    tests={}
    for name,path,count in (('host','pr16-ring-policy-run/policy.stderr',11),
                            ('builder','pr16-ring-policy-successor/builder-tests.stderr',12),
                            ('oracle','pr16-ring-policy-run/oracle.stderr',17)):
        data=files[path]
        need(re.search(rb'Ran '+str(count).encode()+rb' tests in [^\n]+\n\nOK\n$',data),'focused test count/failure differs')
        tests[name]=dict(count=count,identity=identity(data),raw=data.decode('utf-8'))
    need(type(spec['visual_review']) is dict and len(spec['visual_review'])>=10,'visual review incomplete')
    for name,digest in spec['visual_review'].items():
        need(name.startswith('pr16-ring-policy-native/') and name.endswith('.png')
             and identity(files[name])['sha256']==digest,'reviewed image changed')
    gift=json.loads((root/GIFT).read_bytes())
    need(gift['run_id']==35339382576 and gift['npc_gift_save_scoped_accepted'] is True,'accepted gift checkpoint differs')
    verify_sources(gift['native']['sources'],root)
    report=dict(schema_version=1,task=TASK,classification='SCOPED_RING_ORDINARY_POLICY_ACCEPTANCE',
        tested_head=spec['tested_head'],run_id=spec['run_id'],job_id=spec['job_id'],artifact_id=spec['artifact_id'],
        artifact_identity=spec['artifact_identity'],candidate=dict(CANDIDATE,crc32='9EFB0E56'),builder=b,native=n,
        originals=originals,source_tests=tests,member_manifest=manifest,
        visual_review=dict(completed=True,reviewed_sha256=spec['visual_review'],
            method_ja='ChatGPTが原PNGのうち24画面を2倍nearest-neighbor一覧で目視確認。受取・Give・既存技UI・対照・復帰・保存再開。mega-activeは種族変更直後でsprite更新前、native-turnでメガspriteを確認。OCR不使用。全66画面の目視とは主張しない。'),
        accepted_gift=dict(path=GIFT,identity=identity((root/GIFT).read_bytes()),run_id=35339382576,
            original_native_processes=3,original_fresh_cores=6,new_replays=0),
        ring_acquisition_accepted=True,ordinary_battle_accepted=True,
        closed_physical_ids=[RING,POLICY],new_emulator_processes=0,
        recorded_native_processes=5,recorded_fresh_cores=15,accepted_native_cases_replayed=0,
        full_p05_acceptance=False,final_candidate_transfer_complete=False,release_ready=False)
    return report


def project(state,backlog,checkpoint,report):
    need(report['classification']=='SCOPED_RING_ORDINARY_POLICY_ACCEPTANCE'
         and report['closed_physical_ids']==[RING,POLICY]
         and report['ring_acquisition_accepted'] is True and report['ordinary_battle_accepted'] is True,
         'scoped acceptance absent')
    need(report['release_ready'] is False and report['candidate']==dict(CANDIDATE,crc32='9EFB0E56'),'acceptance boundary differs')
    s,b,c=copy.deepcopy(state),copy.deepcopy(backlog),copy.deepcopy(checkpoint)
    need(s['candidate']['sha256']==BP_SHA and c['candidate']['sha256']==BP_SHA
         and s['latest_native_run']==c['latest_native_run']==34946969126,'BP authority moved')
    rows=[row for row in b['remaining_conditions'] if row['id']=='NATURAL_CAPTURE_GEAR']
    need(len(rows)==1 and set(rows[0]['remaining_supply_gap_ids'])=={RING,POLICY},'already closed or incomplete Ring ledger')
    row=rows[0]
    row.update(complete=True,remaining_supply_gap_ids=[],ordinary_policy_selection_required=False,
        ring_bp_natural_supply_required=False,supply_physical_acceptance_complete=True,
        status='PASS_SCOPED_RING_POLICY_PENDING_P08_TRANSFER',success_evidence=REPORT,
        ring_ordinary_policy_checkpoint=REPORT,accepted_candidate_sha256=CANDIDATE['sha256'],
        successor_transfer_condition_id='FINAL_NATIVE_ACCEPTANCE',resume=NEXT)
    row['reason_ja']+=' 2026-09-18: '+STOP
    row['ordinary_policy_plan_ja']='所有者方針どおり通常戦闘時にRing所持を再判定し、既存技選択UIのSTARTで選択/不選択/取消。独立した戦闘前UIも揮発NEXT注入も不要。成功原本: '+REPORT
    row['selected_supply_entrypoints'][RING]=dict(fixture_only=False,path='overlays/ring_npc/ring_npc.c',scope='VegaRingNpcInteract')
    row['selected_supply_entrypoints'][POLICY]=dict(fixture_only=False,path='overlays/ring_policy/ring_policy.c',scope='VegaRingPolicyBegin')
    b['next_integration_candidate']['latest_successor_candidate']=report['candidate']
    b['next_integration_candidate']['latest_successor_evidence']=REPORT
    b['next_integration_candidate']['scope']='BP_AUTHORITY_PRESERVED_RING_POLICY_SCOPED_SUCCESSOR_CIRCUS_PENDING'
    from scripts import pr16_resume as resume
    physical,gates=resume.pending_ids(b)
    need(physical==['PHYSICAL_CIRCUS_ADMISSION'] and gates==sorted(s['remaining_p08_gate_ids']), 'unrelated physical/P08 gate changed')
    need(c['physical_gap_count']==3,'old global gap count differs');c['physical_gap_count']=1
    s['remaining_physical_gap_ids']=physical
    s['ring_ordinary_policy_implementation']=dict(path=REPORT,status=report['classification'],
        run_id=report['run_id'],tested_head=report['tested_head'],candidate=report['candidate'],
        ring_acquisition_accepted=True,ordinary_battle_accepted=True,final_candidate_transfer_complete=False)
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['id']='PHYSICAL_CIRCUS_ADMISSION'
    s['next_action']['read_paths']=[REPORT,resume.BACKLOG,'content/modernization/pr16_p05_supply_owner_findings.json',
        'scripts/build_battle_core.py','overlays/cfru/integration.c']
    s['next_action']['stop_rule_ja']='次はCircusの最小実受付経路。完了した区切りを記録してから最終統合へ進む。merge/release/active baseline変更は行わない。'
    s['remaining_sequence_ja']='Ring/policyはscoped受入済み。残る順序はCircus実入場→影響台帳によるP08最終候補移送→release判定。'
    s['session_execution_summary']=dict(new_emulator_processes=0,recorded_native_processes=5,
        recorded_fresh_cores=15,accepted_standalone_replays=0,record_scope_rom_changes=0,
        implementation_candidate_changes=1,scope_ja=STOP)
    s['do_not_repeat'].insert(0,'通常戦闘Ring5件は'+REPORT+'の固定候補/原本から継承。旧NPC3件・BP/P03/P06/P07を影響なしに再実行しない。旧cold-policy-resetの不成立を新候補の結果へ読み替えない。')
    for key in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head',
                'last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_p08_gate_ids'):
        need(s[key]==state[key],'protected BP/global authority changed: '+key)
    cp=copy.deepcopy(c);cp['physical_gap_count']=checkpoint['physical_gap_count'];need(cp==checkpoint,'BP result fields changed')
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='NATURAL_CAPTURE_GEAR':need(old==new,'unrelated condition changed')
    return s,b,c


def checked_artifact(spec,ops,success):
    run=ops.api('actions/runs/'+str(spec['run_id']))
    need(run['id']==spec['run_id'] and run['head_sha']==spec['tested_head']
         and run['head_branch']==ops.BRANCH and run['status']=='completed'
         and run['conclusion']==success,'Actions run not verified')
    job=ops.api('actions/jobs/'+str(spec['job_id']))
    need(job['run_id']==run['id'] and job['head_sha']==spec['tested_head']
         and job['status']=='completed' and job['conclusion']==success,'Actions job not verified')
    artifact=ops.api('actions/artifacts/'+str(spec['artifact_id']))
    need(not artifact['expired'] and artifact['workflow_run']['id']==run['id']
         and artifact['workflow_run']['head_sha']==spec['tested_head']
         and artifact['digest']=='sha256:'+spec['artifact_identity']['sha256']
         and artifact['size_in_bytes']==spec['artifact_identity']['size'],'Actions artifact not verified')
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(spec['artifact_id'])+'/zip'],cwd=ROOT)
    files,manifest=unpack(raw,spec['artifact_identity'])
    verified={label:{key:source[key] for key in ('id','head_sha','status','conclusion')}
              for label,source in (('run',run),('job',job))}
    return files,manifest,verified


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'wrong write scope')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout not pinned')
    ops.assert_remote(head)
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,check=True)
    need(not (ROOT/REPORT).exists(),'already recorded; do not repeat completed native cases')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'tracked source is dirty')
    OUT.mkdir(parents=True,exist_ok=True)
    state=resume.validate(ROOT);backlog=resume.load(ROOT,resume.BACKLOG);checkpoint=resume.load(ROOT,resume.CHECKPOINT)
    spec=json.loads((ROOT/SPEC).read_bytes())
    subprocess.run(['git','merge-base','--is-ancestor',spec['tested_head'],head],cwd=ROOT,check=True)
    files,manifest,actions=checked_artifact(spec,ops,'success')
    report=validate_bundle(files,manifest,spec)
    report['verification']=actions
    histories=[]
    for prior in spec['history']:
        old,m,meta=checked_artifact(prior,ops,prior['conclusion'])
        npath='pr16-ring-policy-native/result.json'
        actual=json.loads(old[npath])['actual_new_processes'] if npath in old else 0
        need(actual==prior['new_emulator_processes'],'rejected attempt process count differs')
        texts={name:dict(identity=identity(old[name]),last_line=old[name].decode('utf-8').splitlines()[-1],
                        original_available_in_fixed_artifact=True) for name in prior['original_stderr']}
        histories.append(dict(prior,verification=meta,original_stderr=texts,accepted=False))
    report['attempt_history']=histories
    report['session_native_processes_including_rejected']=5+sum(p['new_emulator_processes'] for p in histories)
    report['record_source_head']=head;report['record_run_id']=int(os.environ['GITHUB_RUN_ID'])
    report['record_new_emulator_processes']=0
    report['acceptance_conditions']=copy.deepcopy(state['next_action']['success_observations'])
    report['impact_ledger']=[
        dict(area='CFRU ordinary begin',changed_bytes=8,new_reserved_tail_bytes=172,
             proof='builder: full parent SHA/620-byte owner/BL callees/prologue/FF allocation; ARM two-build identity',
             evidence='builder'),
        dict(area='Ring gift/map/save',runtime_changed=False,accepted_checkpoint=GIFT,
             proof='same source bindings; no existing allocator payload/object/map/save-layout changes',new_standalone_replays=0),
        dict(area='cold Ring + existing UI',new_cases=list(report['originals']),
             proof='real NPC receipt, Give, two normal Saves and two fresh Continues; no Ring/NEXT injection'),
        dict(area='explicit pending/facility/raid/link/exclusivity',
             proof='11 production host contracts; unchanged original begin/select/usage owners; active usage=1 and negative usage=0',
             new_facility_native_replays=0,all_facility_native_regression_claimed=False),
        dict(area='BP/P03/P06/P07 and Circus',native_replayed=False,
             proof='unaffected accepted evidence preserved; Circus physical ID and P08 transfer/release remain open'),
        dict(area='legacy cold-policy-reset',old_result_relabelled=False,
             proof='previous candidate intentionally did not retain a volatile NEXT; new owned Ring case proves new per-battle behavior'),
    ]
    outputs=(REPORT,resume.STATE,resume.DOC,resume.BACKLOG,resume.CHECKPOINT,*ops.LOGS)
    s,b,c=project(state,backlog,checkpoint,report)
    gear=next(row for row in b['remaining_conditions'] if row['id']=='NATURAL_CAPTURE_GEAR')
    for gap in (RING,POLICY):
        owner=gear['selected_supply_entrypoints'][gap]
        lines=(ROOT/owner['path']).read_text(encoding='utf-8').splitlines()
        matches=[i for i,line in enumerate(lines,1) if re.search(r'\b'+re.escape(owner['scope'])+r'\s*\(',line) and not line.lstrip().startswith('//')]
        need(len(matches)==1,'production definition not unique: '+gap);owner['line']=matches[0]
    s['candidate_scope_ja']='この欄は正式BP親候補ceddbe91のidentityを維持。Ring/policyは別checkpointの新scoped候補4ea33fb8で受入済み。CircusとP08最終候補への移送/回帰・製品SHA固定は未完。'
    s['bp']['after_battle_launch']=state['bp']['after_battle_launch']+' 2026-09-18追記: Ring/policyは別scoped候補で完了。BP数値・原本の意味は変更しない。'
    s['next_action']['success_observations']=[
        '実受付/入場ownerと必要進行条件を確定。データ上のmap名だけでCircusと断定しない',
        'flag直接注入を入場の証拠にせず、受付から対象ルール/特性抑制まで通常入力で確認',
        '退出/保存再開/原partyと報酬の境界を保ち、変更影響台帳を記録してからP08へ移送']
    s['observed_head']=head
    s['observed_head_semantics']='Ring/policyの成功原本を記録するsource HEAD。自己commit SHAはremote ref/記録receiptで確認。正式BP受入欄は維持。'
    s['observed_head_checks']=dict(scope_head=head,native=actions,prior=state['observed_head_checks'],
        reason_ja='このRing/policy Actionsのsuccessのみを確認。履歴failure/action_requiredは保持。記録Actions自体はcommit時in_progressであり外部確認する。全CI greenとは主張しない。')
    s['pending_runs']=[];s['logs_synchronized']=True
    report['bp_checkpoint_change']=dict(only_field='physical_gap_count',before=3,after=1,
        native_result_fields_unchanged=True,before_identity=identity((ROOT/resume.CHECKPOINT).read_bytes()))
    (ROOT/REPORT).write_bytes(stable(report))
    for path in (*IMPLEMENTATION,SELF,TEST,WORKFLOW,SPEC,REPORT,'overlays/ring_policy/ring_policy.c','overlays/ring_policy/ring_policy.h','tests/ring_policy_host.c'):
        s['source_bindings'][path]=identity((ROOT/path).read_bytes())
    (ROOT/resume.BACKLOG).write_bytes(stable(b));(ROOT/resume.CHECKPOINT).write_bytes(stable(c))
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8')
    resume.validate(ROOT)
    results=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w',encoding='utf-8') as stream:
            t=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(t.wasSuccessful() and t.testsRun>0 and not t.skipped,'record/resume tests failed')
        results.append(dict(pattern=pattern,count=t.testsRun,success=True))
    (OUT/'tests.json').write_bytes(stable(results))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / Ring取得からcold通常戦闘までのscoped受入。Circus/P08/releaseは未完。\n'
        '- Version: pr16-ring-ordinary-policy\n- Summary: '+STOP+'\n'
        '- Files changed: '+', '.join((*IMPLEMENTATION,SELF,TEST,WORKFLOW,SPEC,*outputs))+'\n'
        '- Verify: production host11 + builder12 + native oracle17 = 40 tests PASS。ARM独立2build一致、172-byte payload + 8-byte entryのみ、allocator overlap0/宣言外ROM差分0。\n'
        '- Native: 正規受取・Give・cold通常戦闘の新規5件/15fresh cores。Ring所持/対応石/START選択でMega、未所持・別石・不選択・取消では不成立。技PP/使用回数/復帰/石非消費/Bag・個体・BP・Save保持を確認。7host-write barriers。\n'
        '- Record verification: 固定ZIP/全member/Actions/sourceと元stdout/stderr/processを照合。選択した原PNG24画面を目視、記録/固定resume tests、task graph PASS。最終index guardとdiff checkをcommit前gateにする。\n'
        f'- Evidence: {REPORT}; tested={spec["tested_head"]}; run={spec["run_id"]}; job={spec["job_id"]}; artifact={spec["artifact_id"]}; ZIP SHA256={spec["artifact_identity"]["sha256"]}。\n'
        '- History: 予約領域台帳の誤仮定・旧SHA probe・入力待ちmaster bit・未展開headerの失敗は原artifactに保持。成功原本へ読み替えず、既に成功した単独nativeは再実行しない。\n'
        '- Preserved: 旧NPC3件とBP/P03/P06/P07の独立再実行0。正式BP候補/原本/数値は不変。BP checkpointは全体physical_gap_countだけ3→1へ同期し、Ring/policy2件を閉じる。Circus1件/P08 gates2は未完。\n'
        f'- Commit: この記録を含む同branchへの非force commit。record source={head}; record run={os.environ["GITHUB_RUN_ID"]}。自己SHAはremote ref/receiptで確認。\n'
        '- Network: GitHub connector/Actions・固定private環境のみ。ROM/save/private ZIP/elfをtracked/artifactへ追加しない。\n'
        '- Boundary: 既存full private guard違反の前後出力完全一致と追加違反0を要求。全体guard PASS/全CI green/merge/release/baseline変更は主張しない。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        p=ROOT/name;need(TASK not in p.read_text(encoding='utf-8'),'duplicate completion log')
        with p.open('a',encoding='utf-8') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPLEMENTATION,SELF,TEST,WORKFLOW,SPEC,*outputs))
    guard.guard();subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True)
    ops.assert_remote(head)
    for key,value in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):
        subprocess.run(['git','config',key,value],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': 正規Ringとcold通常戦闘5件の受入・固定引継ぎを記録'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True)
    ops.assert_remote(commit,attempts=12)
    for name in outputs:
        need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'tracked post-push source dirty')
    resume.validate(ROOT)
    receipt=dict(status='PASS_RING_POLICY_RECORDED',commit=commit,source_head=head,branch=ops.BRANCH,
        source_native_run=spec['run_id'],record_run_id=int(os.environ['GITHUB_RUN_ID']),new_emulator_processes=0,
        remaining_physical_gap_ids=s['remaining_physical_gap_ids'],remaining_p08_gate_ids=s['remaining_p08_gate_ids'],
        output_identities={p:identity((ROOT/p).read_bytes()) for p in outputs},release_ready=False)
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(entry,encoding='utf-8')
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG,resume.CHECKPOINT):
        dest=OUT/'final'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':run()
