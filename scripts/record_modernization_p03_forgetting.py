#!/usr/bin/env python3
"""Accept exact Stage84 forgetting originals; this command never runs an emulator."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile
import run_modernization_remaining_routes as suite

ROOT=Path(__file__).resolve().parents[1]
RUN=34459625383
HEAD='8846cd86de22af35b41eb358b9ed30e4c825750c'
ARTIFACT=10145008020
ZIP_SHA='aa7a122729052c711e27a85658ad96277837b55aa961b8f33799ae2ebf975e04'
CHILD_SHA='55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b'
REPO='dekaazarashi1111-web/pokemon-vega-modern'
BRANCH='codex/modernization-followup-20260908'
WORKFLOW='.github/workflows/p03-p05-remaining-e2e.yml'
DIRECTORY=f'content/modernization/p08_forgetting_evidence/{RUN}'
MANIFEST='content/modernization/p08_p03_forgetting_acceptance.json'
OVERVIEW='content/modernization/p08_remaining_work.json'
SOURCES=frozenset('''
.github/workflows/p03-p05-remaining-e2e.yml
config/active_play_baseline.json
config/modernization_stage79_cumulative_mgba.json
design/active_play_baseline.md
infra/setup_github_actions.sh
infra/toolchain_manifest.json
manifests/move_ids.csv
scripts/run_modernization_p03_fullslots_e2e.py
scripts/run_modernization_remaining_routes.py
tests/test_modernization_remaining_routes.py
tools/mgba_ai_fixture_runner.c
tools/mgba_battle_core_smoke.c
tools/mgba_modernization_p02_stage71_acceptance_smoke.c
tools/mgba_modernization_p03_archive_ui_e2e.c
tools/mgba_modernization_p03_fullslots_e2e.c
tools/mgba_modernization_p03_learning_e2e.c
tools/mgba_modernization_remaining_routes.c
tools/mgba_qol_production_smoke.c
tools/modernization_empty_move_pp_repair.py
tools/modernization_remaining_route_labels.py
'''.split())
need=suite.need
load=suite.base.strict_json

def identity(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def same(a,b):
    if type(a) is not type(b):return False
    if type(a) is dict:return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
    if type(a) is list:return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
    return a==b

def fields(got,expected):
    need(type(got) is dict,'object required')
    for k,v in expected.items():need(same(got.get(k),v),'identity/contract differs: '+k)

def metadata(run,jobs,artifact,data):
    fields(run,dict(id=RUN,head_sha=HEAD,head_branch=BRANCH,event='push',run_attempt=1,path=WORKFLOW,status='completed',conclusion='success'))
    for key in ('repository','head_repository'):fields(run[key],dict(id=1358127462,full_name=REPO))
    fields(artifact,dict(id=ARTIFACT,name='p03-p05-remaining-routes',size_in_bytes=86028,digest='sha256:'+ZIP_SHA))
    fields(artifact['workflow_run'],dict(id=RUN,head_sha=HEAD,head_branch=BRANCH,repository_id=1358127462,head_repository_id=1358127462))
    need(same(identity(data),dict(size=86028,sha256=ZIP_SHA)),'original ZIP identity differs')
    fields(jobs,dict(total_count=1));need(type(jobs['jobs']) is list and len(jobs['jobs'])==1,'one complete job required')
    job=jobs['jobs'][0]
    fields(job,dict(run_id=RUN,head_sha=HEAD,name='remaining-routes',status='completed',conclusion='success'))
    required={'Fixed toolchain','Fail-closed result and input regressions','Reconstruct exact Stage83 without changing accepted baseline','New native forgetting routes, physical write guards and two-core saves','Run actions/upload-artifact@v4'}
    need(required <= {s['name'] for s in job['steps']},'required Actions steps absent')
    need(all(s['status']=='completed' and s['conclusion']=='success' for s in job['steps']),'failed/skipped Actions step')

def members(data):
    need(0<len(data)<=1000000,'archive size bound')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        need(len(infos)==78 and len(set(names))==78 and sum(i.file_size for i in infos)<4000000,'archive count/size/duplicates')
        for i in infos:
            p=PurePosixPath(i.filename)
            need(len(p.parts)==1 and not p.is_absolute() and '\\' not in i.filename and not i.is_dir() and ((i.external_attr>>16)&0o170000)!=0o120000,'unsafe archive member')
        return {i.filename:z.read(i) for i in infos}

def bindings(report,root):
    need(set(report['source_bindings'])==SOURCES,'source closure differs')
    for name,b in report['source_bindings'].items():
        p=root/name
        need(not any(q.is_symlink() for q in (p,*p.parents)),'symlink source')
        need(same(identity(p.read_bytes()),b),'source changed: '+name)

def validate_files(f):
    names={c['name'] for c in suite.cases()} | {'guard-'+a for a in suite.GUARDS} | {'compile','fixed-toolchain','parent-negative'}
    expected={n+s for n in names for s in ('.stdout','.stderr','.process.json')} | {'result.json','candidate.json','matrix-outcomes.json','route-labels.json','tested-head.txt','tests.log','toolchain.log','prepare.log','job.stdout.log','job.stderr.log','circus-source-audit.json','reviewed-source-context.zip'}
    need(set(f)==expected,'original member set differs')
    need(f['tested-head.txt'].decode().strip()==HEAD,'checkout differs')
    report=load(f['result.json'])
    fields(report,dict(schema_version=1,status='PASS',scope=suite.SCOPE,candidate_stage=84,rom=dict(size=33554432,sha256=CHILD_SHA),parent_rom=dict(size=33554432,sha256=suite.ROM_SHA),seed=dict(size=131072,sha256=suite.SEED_SHA),guard_checks=list(suite.GUARDS),fresh_processes=12,core_instances=24,parent_negative_controls=1,cache_reuse=0,validation_class='FIXED_TOOLCHAIN_NATIVE_EXECUTION',full_matrix=True,full_p03_acceptance=False,full_p05_acceptance=False,release_ready=False,active_baseline_changed=False,fixture_scope='Party/position/items configured before Bag input; no natural acquisition claim'))
    recipe=load(f['candidate.json'])
    need(same(recipe,report['recipe']),'recipe differs')
    fields(recipe,dict(schema_version=1,status='BUILT_NOT_ACCEPTED',stage=84,scope='MOVE_NONE_CANONICAL_PP_SENTINEL_ONLY',parent=report['parent_rom'],candidate=report['rom'],patch=dict(offset=17048056,move_id=0,field='pp',before=35,after=0),changed_byte_count=1,real_move_rows_unchanged=True,p06_stage83_species_rows_unchanged=True,save_abi_unchanged=True,active_baseline_changed=False,full_p03_acceptance=False,full_p05_acceptance=False,release_ready=False))
    need(type(report['cases']) is list and len(report['cases'])==12,'twelve cases required')
    need(same(report['cases'],load(f['matrix-outcomes.json'])),'matrix differs')
    for row,c in zip(report['cases'],suite.cases()):
        n=c['name'];fields(row,dict(name=n,validation_error=None))
        process=load(f[n+'.process.json']);need(same(process,row['process']),'process receipt differs')
        actual=suite.validate(f[n+'.stdout'],c,process,f[n+'.stderr'],CHILD_SHA)
        need(same(actual,row['result']),'native result differs')
        for suffix in ('stdout','stderr'):need(same(identity(f[n+'.'+suffix]),row[suffix]),'native output digest differs')
    for api in suite.GUARDS:
        n='guard-'+api
        need(suite.base.require_exited(load(f[n+'.process.json']))==1 and not f[n+'.stdout'] and f[n+'.stderr']==b'P03 archive: host write after observation barrier\n','real write guard failed')
    need(suite.base.require_exited(load(f['parent-negative.process.json']))==1 and not f['parent-negative.stdout'] and b'slot=3 move=0/0 pp=35/0\n' in f['parent-negative.stderr'] and f['parent-negative.stderr'].endswith(b'P03 archive: forget move/PP differs\n'),'Stage83 defect not reproduced')
    for n in ('compile','fixed-toolchain'):
        need(suite.base.require_exited(load(f[n+'.process.json']))==0 and not f[n+'.stderr'],'compile/toolchain check failed')
    need(b'[OK] host_cc: 13.3.0\n' in f['fixed-toolchain.stdout'] and b'[OK] mgba: 0.10.2\n' in f['fixed-toolchain.stdout'],'fixed versions absent')
    need(b'Ran 24 tests' in f['tests.log'] and f['tests.log'].rstrip().endswith(b'OK'),'regression receipt absent')
    need(not f['job.stderr.log'] and same(load(f['job.stdout.log']),{k:v for k,v in report.items() if k not in ('cases','source_bindings')}),'job summary differs')
    return report

def verify(data,run,jobs,artifact,root=ROOT):
    metadata(run,jobs,artifact,data);report=validate_files(members(data));bindings(report,root)
    return dict(schema_version=1,status='PASS',task='USER-MODERNIZATION-P03-P05',scope=suite.SCOPE,source_run_id=RUN,source_head_sha=HEAD,artifact_id=ARTIFACT,original_archive=identity(data),evidence_directory=DIRECTORY,original_member_count=78,source_bindings=report['source_bindings'],candidate_stage=84,candidate_rom=report['rom'],parent_rom=report['parent_rom'],repair=report['recipe']['patch'],accepted_case_names=[c['name'] for c in suite.cases()],accepted_native_processes=12,accepted_core_instances=24,save_continue_cycles=12,host_write_denial_probes=7,parent_defect_controls=1,original_cache_reuse=0,new_emulator_runs_during_integration=0,mgba_version='0.10.2',compiler='13.3.0',fixture_scope=report['fixture_scope'],active_baseline_stage=62,active_baseline_changed=False,full_p03_acceptance=False,full_p05_acceptance=False,release_ready=False,remaining_scope=['other evolution/form learning and additional egg supply paths','archive economy formal adoption','natural acquisition and physical Battle Circus admission','P06/P07 full acceptance and final-candidate convergence'])

def build(root=ROOT):
    directory=root/DIRECTORY;need(not any(p.is_symlink() for p in (directory,*directory.parents)),'unsafe evidence directory')
    names=('original.zip','actions-run.json','actions-jobs.json','actions-artifact.json');raw={}
    for n in names:
        p=directory/n;need(p.is_file() and not p.is_symlink(),'missing/unsafe evidence '+n);raw[n]=p.read_bytes()
    result=verify(raw[names[0]],*(load(raw[n]) for n in names[1:]),root)
    result['metadata_bindings']={n:identity(raw[n]) for n in names[1:]}
    return result

def remaining_work(root,forgetting):
    # Frozen accepted reports remain historical evidence on their own ROMs.
    # Their old "remaining" prose is deliberately not imported as today's tasks.
    pins={
        'p08_p03_breeding_acceptance.json':'65b7a61dee18f26aec29da52c2e275f7b9729a7c788c84aa2675081059a94c16',
        'p08_p03_breeding_capacity_acceptance.json':'9eb1b96e877f2032493fc99d63ba8f7786332a1a45bed9464f598fba4422b986',
        'p08_native_mega_acceptance.json':'981fbaf2d86f10c21e9943a10abf89963c2020d011e94ea53bd80569822528b5',
        'p08_p03_relearner_acceptance.json':'1518d7471fcfcb15d7a03155eccb7e0049b209c1b46cfb74973d3be9dfde287e',
        'p06_decided_adjustments.json':'1934a98f5d60f33a5c65ae294defc03e092a3c9826462e327f41c7ce8d4a24e3',
        'p07_layered_learnset_contract.json':'ca17b3e33989d0ae105e5ac6ecc1c62ed27daae7ddc8d0a16632be64852842c5'}
    documents={};receipts={}
    def read(name):
        p=root/name
        need(not any(q.is_symlink() for q in (p,*p.parents)),'unsafe overview input')
        raw=p.read_bytes();receipts[name]=identity(raw);return raw
    for name,sha in pins.items():
        raw=read('content/modernization/'+name);need(identity(raw)['sha256']==sha,'accepted/adopted source changed: '+name)
        documents[name]=load(raw)
    accepted=[]
    for name,label,count in [('p08_p03_breeding_acceptance.json','daycare birth and hatch',8),('p08_p03_breeding_capacity_acceptance.json','egg queue and party/PC capacity',3),('p08_native_mega_acceptance.json','six Mega lifecycles plus 36 nonactivation controls',42),('p08_p03_relearner_acceptance.json','normal 17 and egg 29 relearner paths',46)]:
        d=documents[name];need(d['release_ready'] is False,'unexpected prior release approval')
        directory=d.get('evidence_root',d.get('evidence_directory'))
        receipt=d.get('original_archive',d.get('files',{}).get('original.zip'))
        p=PurePosixPath(directory)/'original.zip'
        need(not p.is_absolute() and '..' not in p.parts,'unsafe original archive')
        need(same(identity(read(p.as_posix())),receipt),'prior original archive differs')
        accepted.append(dict(label=label,source_path='content/modernization/'+name,source_run_id=d['source_run_id'],cases=count,candidate_rom=d.get('candidate',dict(size=33554432,sha256=d.get('candidate_rom_sha256')))))
    accepted.append(dict(label='native forgetting and cold Save/Continue',source_path=MANIFEST,source_run_id=RUN,cases=12,candidate_rom=forgetting['candidate_rom']))
    receipts[MANIFEST]=identity((json.dumps(forgetting,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
    p06=documents['p06_decided_adjustments.json'];p07=documents['p07_layered_learnset_contract.json']
    fields(p06['adoption'],dict(adopted_delta_count=2,field_change_count=3,runtime_patch_authorized=True,explicit_species_adjustment_spec_received=True))
    for source in p06['sources'].values():need(same(identity(read(source['path'])),{k:source[k] for k in ('size','sha256')}),'P06 decision original differs')
    directions=p07['adopted_delta'];need(directions['normal_species_to_vega_move']==[] and directions['vega_species_to_normal_move']==[],'P07 adoption changed; reconcile explicitly')
    economy=load(read('config/modernization_p03_stage74_supply.json'))['runtime']['economy']
    need(economy['status']=='PROVISIONAL_REPLACEABLE','economy policy changed; reconcile explicitly')
    reasons=[
      ('P03','EVOLUTION_FORM_OTHER_EGG','技忘れ12件は受入済み。進化・フォームに伴う技習得、その他の繁殖・タマゴ技供給経路の受入照合と保存検証が残る'),
      ('P03','ARCHIVE_ECONOMY','追加技供給の殿堂入り後・わざメモリーから無料という暫定仕様の正式確定'),
      ('P05','NATURAL_CAPTURE_GEAR','通常の捕獲・道具取得から戦闘までの通し受入'),
      ('P05','PHYSICAL_CIRCUS_ADMISSION','実際の受付・入場からBattle Circus特性抑制までの通し受入。既存のフラグ設定試験で代替しない'),
      ('P06','PHASE_ACCEPTANCE','採用済み2件を工程全体の受入とP08へ接続し、その他のレビュー資料は採用・保留を整理する'),
      ('P07','SOURCE_RECONCILIATION_ADOPTION','両方向の採用表は空。指示が無かったと断定せず既存資料を照合し、採用表・P06整合・実装・習得画面・保存を確定する'),
      ('P08','SINGLE_CANDIDATE','Stage82/83/84の異なる候補上の成功を一つの最終候補での全工程受入と混同しない。最終候補の統一が必要'),
      ('P08','REPOSITORY_GUARD','既存の追跡ROM/save・過去ログの絶対パスに対するリポジトリ全体guardの是正。差分guard成功と区別する'),
      ('P08','RELEASE_DECISION','配布用成果物・リリース判定・PRマージ・プレイ基準の扱いを全受入後に決定する')]
    return dict(schema_version=1,status='CURRENT_REMAINING_WORK_NOT_RELEASE_ACCEPTANCE',task='USER-MODERNIZATION-P03-P05',historical_snapshot='content/modernization/p08_current_acceptance.json',historical_snapshot_is_current_backlog=False,accepted_scoped_reports=accepted,p06_adoption=dict(adopted_species_count=2,field_change_count=3,source_path='content/modernization/p06_decided_adjustments.json',full_phase_accepted=False),p07_adoption=dict(normal_species_to_vega_move=0,vega_species_to_normal_move=0,prior_instructions_absent_claimed=False),latest_scoped_candidate=forgetting['candidate_rom'],latest_scoped_candidate_stage=84,final_candidate=None,remaining_conditions=[dict(phase=p,id=i,reason_ja=why) for p,i,why in reasons],source_bindings=receipts,new_emulator_runs_during_reconciliation=0,full_p03_acceptance=False,full_p05_acceptance=False,full_p06_acceptance=False,full_p07_acceptance=False,release_ready=False,active_baseline_changed=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');args=p.parse_args()
    try:
        result=build();overview=remaining_work(ROOT,result);target=ROOT/MANIFEST;summary=ROOT/OVERVIEW
        if args.write:
            need(all(not p.exists() and not p.is_symlink() for p in (target,summary)),'refuse existing acceptance overwrite')
            target.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
            summary.write_text(json.dumps(overview,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
        else:
            need(same(load(target.read_bytes()),result),'acceptance snapshot differs')
            need(same(load(summary.read_bytes()),overview),'remaining-work snapshot differs')
        print(json.dumps(dict(status='PASS',source_run_id=RUN,accepted_native_processes=12,save_continue_cycles=12,new_emulator_runs=0,release_ready=False)));return 0
    except (OSError,ValueError,KeyError,TypeError,zipfile.BadZipFile) as e:print('forgetting acceptance: '+str(e),file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
