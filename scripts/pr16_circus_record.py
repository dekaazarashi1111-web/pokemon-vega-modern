#!/usr/bin/env python3
"""Circusのpending実装/実ROM linkを原本から記録。実受付受入には昇格しない。"""
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
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
BASE='eaba8396f282f5e6a48c15c47f30422b745984fa'
TASK='USER-20260918-CIRCUS'
SELF='scripts/pr16_circus_record.py'
TEST='tests/test_pr16_circus_record.py'
WORKFLOW='.github/workflows/pr16-circus-record.yml'
SPEC='content/modernization/pr16_circus_record_spec.json'
REPORT='content/modernization/pr16_circus_admission_checkpoint.json'
OUT=ROOT/'.local/pr16-circus-record'
IMPL=('.github/workflows/pr16-source-workspace.yml',
    'overlays/circus_admission/circus_admission.c','overlays/circus_admission/circus_admission.h',
    'tests/test_pr16_circus_admission.py','scripts/pr16_circus_source_probe.py',
    '.github/workflows/pr16-circus-source.yml','scripts/pr16_circus_link_probe.py',
    'tests/test_pr16_circus_link_probe.py','.github/workflows/pr16-circus-link.yml',
    'tests/test_modernization_p08_forgetting_evidence.py')
PARENT={'size':33554432,'sha256':'4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'}
PAYLOAD={'size':280,'sha256':'286b3d136f39b5305f6b65388f68d5b1a4429ce5b944878e97143a673a36ef80'}
STOP=('未消費の正規facility commandを所有APIでCircus番号3へ切替えるC実装を追加。'
      'mockなしhost10件、ELF境界10件、ARM object独立2compile、現ROMの7関数全byte照合と独立2linkを検証。'
      '280-byte runtimeはlink検証までで、製品ROMへの挿入/受付script接続/実入場nativeは未完。'
      'Ring受入後に古い未完状態を要求していたP03 CI条件も修正し20+24件PASS。')
NEXT=('保存した7関数・リンク結果・5335 root走査を再実行せず、未解決の間接native/std受付経路を絞る。'
      '実受付scriptに未消費pending番号3選択→正規sp072抽選→戦闘開始を接続し、'
      '受付取消/party復帰と正常Save/fresh Continueを新規nativeで検証する。'
      'sp072の特性抑制はpersonal effectで連勝30以上の正規進行条件が必要。'
      'map12/7やraw Var403AをCircusの証拠とせず、flag/PC/LR直接注入で入場を代用しない。'
      'Ring/BP/P03/P06/P07の受入済みnativeは変更影響なしに再実行しない。')


def need(ok,message):
    if not ok:raise ValueError(message)


def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def stable(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()

def load(raw):
    def pairs(items):
        out={}
        for k,v in items:
            need(k not in out,'duplicate JSON key');out[k]=v
        return out
    def bad(value):raise ValueError('nonfinite JSON: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)


def exact(value,expected,message):
    need(type(value) is type(expected) and value==expected,message)


def unpack(raw,bound,with_manifest=True):
    need(identity(raw)==bound,'artifact ZIP identity differs')
    files={};total=0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(0<len(z.infolist())<500,'ZIP count bound')
        for info in z.infolist():
            name=info.filename;p=PurePosixPath(name)
            need(name==p.as_posix() and not p.is_absolute() and '..' not in p.parts
                 and '\\' not in name and name not in files and not info.is_dir(),'unsafe/duplicate ZIP path')
            need((info.external_attr>>16)&0o170000!=0o120000 and info.file_size<2000000,'unsafe ZIP type/size')
            need(p.suffix in {'.json','.txt','.stdout','.stderr','.log','.c','.h','.py','.yml','.ld'},'non-text suffix')
            raw_member=z.read(info);raw_member.decode('utf-8-sig')
            need(b'\0' not in raw_member and not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}',raw_member),'unsafe text')
            total+=len(raw_member);need(total<8000000,'expanded ZIP bound')
            files[name]=raw_member
    manifest=load(files['members.json']) if with_manifest else {n:identity(d) for n,d in files.items()}
    need(set(files)==set(manifest)|({'members.json'} if with_manifest else set()),'member manifest differs')
    for n,m in manifest.items():need(identity(files[n])==m,'member identity differs: '+n)
    return files,manifest


def verify_actions(spec,run,job,artifact,repo,branch):
    need(run['id']==spec['run_id'] and run['head_sha']==spec['tested_head']
         and run['head_branch']==branch and run['path']==spec['workflow']
         and run['event']=='push' and run['run_attempt']==1,'run identity differs')
    need(run['repository']['id']==run['head_repository']['id']==1358127462
         and run['repository']['full_name']==run['head_repository']['full_name']==repo,'repository identity differs')
    need(job['id']==spec['job_id'] and job['run_id']==run['id']
         and job['head_sha']==run['head_sha'],'job identity differs')
    for value in (run,job):need(value['status']=='completed' and value['conclusion']==spec['conclusion'],'run/job conclusion differs')
    steps={s['name']:s for s in job['steps']}
    for name in spec['required_success_steps']:
        need(name in steps and steps[name]['status']=='completed' and steps[name]['conclusion']=='success','required step not successful')
    need(artifact['id']==spec['artifact_id'] and artifact['name']==spec['name']
         and artifact['expired'] is False and artifact['digest']=='sha256:'+spec['artifact_identity']['sha256']
         and artifact['size_in_bytes']==spec['artifact_identity']['size'],'artifact identity/lifecycle differs')
    a=artifact['workflow_run']
    need(a['id']==run['id'] and a['head_sha']==run['head_sha'] and a['head_branch']==branch
         and a['repository_id']==a['head_repository_id']==1358127462,'artifact run binding differs')
    return dict(run={k:run[k] for k in ('id','head_sha','path','status','conclusion','run_attempt')},
        job={k:job[k] for k in ('id','run_id','head_sha','status','conclusion')},
        artifact={k:artifact[k] for k in ('id','name','digest','size_in_bytes','expired')},required_steps=spec['required_success_steps'])


def checked(spec,ops):
    run=ops.api('actions/runs/'+str(spec['run_id']))
    job=ops.api('actions/jobs/'+str(spec['job_id']))
    artifact=ops.api('actions/artifacts/'+str(spec['artifact_id']))
    meta=verify_actions(spec,run,job,artifact,ops.REPO,ops.BRANCH)
    raw=subprocess.check_output(['gh','api','repos/'+ops.REPO+'/actions/artifacts/'+str(spec['artifact_id'])+'/zip'],cwd=ROOT)
    files,manifest=unpack(raw,spec['artifact_identity'],spec['with_manifest'])
    return files,manifest,meta


def tests_pass(raw,count):
    need(re.search(rb'Ran '+str(count).encode()+rb' tests in [^\n]+\n\nOK\n$',raw),'focused tests missing/failed/skipped')


def validate_reports(source,link):
    from scripts.pr16_circus_link_probe import REQUIRED_FUNCTIONS
    exact(source['independent_arm_compiles'],2,'ARM object compile count differs')
    need(source['classification']=='CIRCUS_PENDING_IMPLEMENTED_SOURCE_LINK_PENDING','source scope differs')
    need(link['classification']=='CIRCUS_OWNER_LINKED_NOT_PHYSICAL_ACCEPTANCE' and link['candidate']==PARENT,'link scope/parent differs')
    for report in (source,link):
        for k in ('new_emulator_processes','accepted_native_cases_replayed','rom_changes'):exact(report[k],0,'unexpected replay/ROM change')
        for k in ('physical_admission_accepted','release_ready'):exact(report[k],False,'unproved acceptance')
    new=link['new_runtime'];exact(new['independent_links'],2,'link count differs')
    need(new['payload']==PAYLOAD,'linked payload differs')
    for k in ('no_rom_payload_inserted','placement_is_link_test_only'):exact(new[k],True,'test-only placement boundary lost')
    functions=link['fixed_build']['verified_functions']
    need(set(functions)==set(REQUIRED_FUNCTIONS),'seven owner closure differs')
    for name,binding in functions.items():
        row=link['symbols'][name]
        need(type(binding['address']) is int and binding['address']==row['address']
             and binding['size']==row['size'] and row['kind']=='T','owner ABI differs')
        need(row['matches_candidate'] is True and row['elf_bytes']==row['candidate_bytes']
             =={k:binding[k] for k in ('size','sha256')},'whole owner byte match differs')
    for name,at in new['owners'].items():need(at==functions[name]['address'],'link used different owner')
    need(set(new['owners'])=={'cfru_integration_pending_copy','cfru_integration_pending_facility_set'},'pending owner set differs')
    routes=link['routes']
    exact(routes['decoded_roots'],5335,'root scan identity differs')
    need(len(routes['invalid_roots'])==6,'invalid root count differs')
    for k in ('native_indirect_callers_fully_excluded','no_match_proves_absence','physical_entrance_accepted'):exact(routes[k],False,'absence/entrance incorrectly inferred')
    need(not any(r['category']=='native' or (r['category']=='special' and r['value']==0x72)
                 for r in routes['selected_references']),'route conclusion differs')


def verify_sources(root,bindings):
    need(type(bindings) is dict and bindings,'source bindings absent')
    for name,meta in bindings.items():
        p=PurePosixPath(name)
        need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,'unsafe source path')
        f=root/name;need(f.is_file() and not f.is_symlink() and identity(f.read_bytes())==meta,'tested source changed: '+name)


def project(state,backlog,report):
    need(report['physical_admission_accepted'] is False and report['rom_changes']==0
         and report['classification']=='CIRCUS_PENDING_IMPLEMENTATION_LINKED_PHYSICAL_ENTRY_OPEN','unproved promotion')
    s,b=copy.deepcopy(state),copy.deepcopy(backlog)
    rows=[r for r in b['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION']
    need(len(rows)==1 and rows[0].get('complete') is not True and rows[0]['success_evidence'] is None,'Circus already closed or inconsistent')
    rows[0].update(implementation_checkpoint=REPORT,implementation_status=report['classification'],resume=NEXT)
    s['circus_admission_implementation']={'path':REPORT,'status':report['classification'],
        'tested_head':report['tested_head'],'run_id':report['link_run_id'],'product_rom_wired':False,'physical_admission_accepted':False}
    s['bp']['current_stop']=s['source_change_review_ja']=STOP
    s['bp']['next_step']=s['next_action']['goal_ja']=NEXT
    s['next_action']['read_paths']=[REPORT,'overlays/circus_admission/circus_admission.c',
        'content/modernization/pr16_p05_supply_owner_findings.json','content/modernization/p08_remaining_work.json']
    s['next_action']['host_write_policy_ja']='Circus受付の観測開始後に施設番号・効果bit・進行条件・party・PC/LRをhostから設定しない。連勝30以上は正規進行を保持した入力として別途照合し、零連勝fixtureで抑制を要求しない。'
    s['remaining_sequence_ja']='Circus pending C/実owner linkまで完了。実受付・効果抽選への接続→新native→影響台帳によるP08移送→release判定。'
    s['session_execution_summary']=dict(new_emulator_processes=0,accepted_standalone_replays=0,
        record_scope_rom_changes=0,implementation_candidate_changes=0,product_rom_wired=False,scope_ja=STOP)
    s['do_not_repeat'].insert(0,'Circus source run35351832671/actual-owner link run35353620141を再利用。C/契約/7実関数/候補SHAに影響がなければ10+10件/独立link/5335 rootsを再実行しない。保存ELFはlinked.oであり拡張子.elf限定探索を再発させない。')
    for k in ('candidate','status','latest_native_run','latest_native_job','latest_native_tested_head',
              'last_accepted_native_run','last_accepted_native_tested_head','release_ready','remaining_physical_gap_ids','remaining_p08_gate_ids'):
        need(s[k]==state[k],'protected authority changed')
    for old,new in zip(backlog['remaining_conditions'],b['remaining_conditions']):
        if old['id']!='PHYSICAL_CIRCUS_ADMISSION':need(old==new,'other accepted condition changed')
    return s,b


def run():
    import pr16_resume as resume
    import pr16_ring_followup_v2 as ops
    import pr16_ring_compiled_record as guard
    need(os.environ.get('GITHUB_REPOSITORY')==ops.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+ops.BRANCH,'write scope differs')
    head=ops.cmd('git','rev-parse','HEAD');need(head==os.environ['GITHUB_SHA'],'checkout differs');ops.assert_remote(head)
    subprocess.run(['git','merge-base','--is-ancestor',BASE,head],cwd=ROOT,check=True)
    need(not (ROOT/REPORT).exists(),'checkpoint already recorded; do not replay')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'dirty tracked source')
    OUT.mkdir(parents=True,exist_ok=True)
    state=resume.validate(ROOT);backlog=resume.load(ROOT,resume.BACKLOG)
    bp=identity((ROOT/resume.CHECKPOINT).read_bytes())
    spec=load((ROOT/SPEC).read_bytes());bundles={};metadata={}
    for key,item in spec['artifacts'].items():
        subprocess.run(['git','merge-base','--is-ancestor',item['tested_head'],head],cwd=ROOT,check=True)
        files,manifest,verified=checked(item,ops);bundles[key]=files;metadata[key]=dict(spec=item,verified=verified,member_manifest=manifest)
    source=load(bundles['source']['report.json']);link=load(bundles['link']['pr16-circus-link/report.json'])
    validate_reports(source,link)
    for key,report in (('source',source),('link',link)):
        need(report['source_head']==spec['artifacts'][key]['tested_head'] and report['run_id']==spec['artifacts'][key]['run_id'],'report/run binding differs')
    verify_sources(ROOT,{k:v for k,v in source['source_bindings'].items() if not k.startswith('vendor/')})
    verify_sources(ROOT,link['source_bindings']);verify_sources(ROOT,spec['ci_sources'])
    for name,binding in source['source_bindings'].items():need(identity(bundles['source']['source/'+name])==binding,'source original bytes differ')
    tests_pass(bundles['source']['host.stderr'],10);tests_pass(bundles['link']['pr16-circus-link-run/tests.stderr'],10)
    tests_pass(bundles['ci']['original-mutations.log'],20);tests_pass(bundles['ci']['runtime-contracts.log'],24)
    for name in ('source-head.txt','checkout-head.txt'):need(bundles['ci'][name].decode().strip()==spec['artifacts']['ci']['tested_head'],'CI checkout drift')
    check=load(bundles['ci']['check.json']);need(check['status']=='PASS' and check['new_emulator_runs']==0 and check['release_ready'] is False,'CI acceptance boundary differs')
    failed=bundles['failed_link']['pr16-circus-link-run/link.stderr'].decode()
    need('unique fixed CFRU owner ELF not found' in failed and '/linked.o' in failed,'failed-link cause differs')
    report=dict(schema_version=1,task=TASK,classification='CIRCUS_PENDING_IMPLEMENTATION_LINKED_PHYSICAL_ENTRY_OPEN',
        tested_head=spec['artifacts']['link']['tested_head'],link_run_id=spec['artifacts']['link']['run_id'],
        record_source_head=head,record_run_id=int(os.environ['GITHUB_RUN_ID']),physical_admission_accepted=False,
        product_rom_wired=False,rom_changes=0,new_emulator_processes=0,accepted_native_cases_replayed=0,
        release_ready=False,source_report=source,link_report=link,verified_artifacts=metadata,
        ci_repair=dict(status='PASS',tests=44,reason_ja='Ring/policy受入原本に合わせて古いpending要求を修正。P08/Circusは未完を維持。',
            originals={n:d.decode() for n,d in bundles['ci'].items()},sources=spec['ci_sources']),
        failed_link=dict(run_id=35352684227,accepted=False,
            original_stderr_identity=identity(failed.encode()),original_stderr_last_line=failed.splitlines()[-1],
            original_stderr_available_in_fixed_artifact=True,
            reason_ja='固定cacheの実体linked.oを拡張子.elf限定で見落とした。7関数の全byte照合で修復。'),
        implementation_files=list(IMPL),impact_ledger=dict(accepted_ring_policy_changed=False,
            formal_bp_checkpoint_changed=False,existing_cfru_runtime_changed=False,
            source_only_ci_condition_changed=True,physical_entry_remaining=True,p08_transfer_remaining=True),
        next_action_ja=NEXT)
    # 抽選条件は固定上流の関数本文とheaderから再確認する。効果bitを注入しない。
    frontier=bundles['source']['source/vendor/upstream/CFRU-JP/src/frontier.c'].decode('utf-8-sig')
    start=frontier.index('void sp072_LoadBattleCircusEffects(void)');end=frontier.index('\n}\n',start)+3
    fn=frontier[start:end]
    need('case 30 ... 39:' in fn and 'gBattleCircusFlags |= gBitTable[effectNum]' in fn,'fixed draw owner differs')
    report['effect_owner_source']={'path':'vendor/upstream/CFRU-JP/src/frontier.c','function_utf8':fn,
        'whole_source_identity':source['source_bindings']['vendor/upstream/CFRU-JP/src/frontier.c'],
        'interpretation_ja':'特性抑制bit31はpersonal effect。通常抽選では連勝30以上。実進行/保存ownerの証明は別途必要。'}
    s,b=project(state,backlog,report)
    s['observed_head']=head;s['observed_date_jst']='2026-09-18'
    s['observed_head_semantics']='Circus実装/link/CI修復の原本を記録するsource HEAD。完了commitはremote ref/receiptで確認。正式BP受入HEADではない。'
    s['observed_head_checks']=dict(scope_head=head,verified_artifacts={k:v['verified'] for k,v in metadata.items()},
        prior=state['observed_head_checks'],reason_ja='成功したsource/link/P03 CI原本を確認。失敗した旧linkも保持。記録runはcommit時in_progressで、全CI greenとは主張しない。')
    s['pending_runs']=[];s['logs_synchronized']=True
    (ROOT/REPORT).write_bytes(stable(report));(ROOT/resume.BACKLOG).write_bytes(stable(b))
    for name in (*IMPL,SELF,TEST,WORKFLOW,SPEC,REPORT):s['source_bindings'][name]=identity((ROOT/name).read_bytes())
    (ROOT/resume.STATE).write_bytes(stable(s));(ROOT/resume.DOC).write_text(resume.render(s),encoding='utf-8')
    resume.validate(ROOT);need(bp==identity((ROOT/resume.CHECKPOINT).read_bytes()),'formal BP checkpoint changed')
    results=[]
    for pattern in (Path(TEST).name,'test_pr16_resume.py'):
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern)
        with (OUT/(pattern+'.txt')).open('w',encoding='utf-8') as stream:t=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        need(t.wasSuccessful() and t.testsRun>0 and not t.skipped,'record/resume tests failed');results.append(dict(pattern=pattern,count=t.testsRun,success=True))
    (OUT/'tests.json').write_bytes(stable(results))
    subprocess.run([sys.executable,'scripts/validate_task_graph.py'],cwd=ROOT,check=True)
    outputs=(REPORT,resume.STATE,resume.DOC,resume.BACKLOG,*ops.LOGS)
    stamp=datetime.now(timezone.utc).isoformat()
    entry=(f'\n\n## {stamp} — {TASK}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        '- Status: DONE / pending選択実装と実owner linkの区切り。実受付・入場nativeは未完。\n'
        '- Version: pr16-circus-pending-owner\n- Summary: '+STOP+'\n'
        '- Files changed: '+', '.join((*IMPL,SELF,TEST,WORKFLOW,SPEC,*outputs))+'\n'
        '- Verify: 新Cのmockなしhost10件、ELF/実byte境界10件PASS。ARM object2compile一致、実候補7関数全byte一致、新280-byte payload独立2link一致・未解決symbol0。\n'
        '- CI repair: P03状態保持20件＋既存契約24件PASS（保存原本の検査のみ、native再実行0）。Ring/policyを未完へ戻さず、P08/Circusは未完のまま。\n'
        '- Evidence: '+REPORT+'; source run35351832671/artifact10550280062; link run35353620141/artifact10550587542; CI run35353620112/artifact10550417336。固定HEAD/ZIP/全member/source/job結論照合。\n'
        '- History: run35352684227はlinked.oを.elf限定で見落とした失敗。原stderrのhash/原因行と固定artifactを保持し、成功へ読み替えない。記録run35355663661はrunner絶対パス混入をguardで拒否し、未commitのまま停止。原本参照を保って原因行だけ記録する修復を加えた。\n'
        '- Boundary: 受付への新runtime接続・ROM挿入0、実入場native0、accepted standalone native replay0。5335 decoded rootsで直接owner/sp072呼出し未検出でも、間接native/std経路の不存在は主張しない。\n'
        '- Preserved: 正式BP checkpoint byte不変。Ring/BP/P03/P06/P07の受入原本・既存CFRU・release_ready=false・physical1/P08 gates2を維持。\n'
        '- Record: 固定MD/JSON同期、focused記録/再開testsとtask graph検査。最終index guardは既存違反の前後出力完全一致/追加違反0、diff checkをcommit前必須gate。\n'
        f'- Commit: 同branchへ非force push。record source={head}; record run={os.environ["GITHUB_RUN_ID"]}。自己SHAはreceipt/remote refで確認。\n'
        '- Network: GitHub connector/Actions固定入力のみ。新ROM/save/ELF/private ZIPをtracked/artifactへ追加しない。merge/release/active baseline変更なし。\n'
        '- Next: '+NEXT+'\n')
    for name in ops.LOGS:
        p=ROOT/name;need(('Task: '+TASK+'\n') not in p.read_text(),'duplicate completion log')
        with p.open('a',encoding='utf-8') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*outputs],cwd=ROOT,check=True)
    guard.BASE,guard.OUT,guard.ALLOWED=BASE,OUT,set((*IMPL,SELF,TEST,WORKFLOW,SPEC,*outputs))
    guard.guard();subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);ops.assert_remote(head)
    for k,v in (('user.name','github-actions[bot]'),('user.email','41898282+github-actions[bot]@users.noreply.github.com')):subprocess.run(['git','config',k,v],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': Circus pending実装・実owner link・CI修復を検証し固定引継ぎへ記録'],cwd=ROOT,check=True)
    commit=ops.cmd('git','rev-parse','HEAD');subprocess.run(['git','push','origin','HEAD:refs/heads/'+ops.BRANCH],cwd=ROOT,check=True);ops.assert_remote(commit,attempts=12)
    for name in outputs:need(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT)==(ROOT/name).read_bytes(),'committed output differs')
    need(not ops.cmd('git','status','--porcelain','--untracked-files=no'),'post-push source dirty');resume.validate(ROOT)
    receipt=dict(status='PASS_CIRCUS_PENDING_IMPLEMENTATION_RECORDED',commit=commit,source_head=head,
        record_run_id=int(os.environ['GITHUB_RUN_ID']),branch=ops.BRANCH,tests=results,
        remaining_physical_gap_ids=s['remaining_physical_gap_ids'],remaining_p08_gate_ids=s['remaining_p08_gate_ids'],
        physical_admission_accepted=False,product_rom_wired=False,release_ready=False,
        formal_bp_checkpoint_unchanged=bp==identity((ROOT/resume.CHECKPOINT).read_bytes()),
        output_identities={n:identity((ROOT/n).read_bytes()) for n in outputs})
    (OUT/'receipt.json').write_bytes(stable(receipt));(OUT/'completion-log.txt').write_text(entry)
    for name in (REPORT,resume.STATE,resume.DOC,resume.BACKLOG):
        p=OUT/'final'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':run()
