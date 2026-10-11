#!/usr/bin/env python3
"""Revalidate exact native originals, preserve historical receipts, project current work.

No emulator runs here. A scoped phase closure never implies product readiness.
--fetch reads three fixed Actions runs, installing only exact absent originals.
"""
from copy import deepcopy
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_repaired_acceptance as repaired
import pr16_evolution_fullslots as evolution
import pr16_breeding_delta as breeding
need=repaired.need
stable=repaired.stable
identity=repaired.identity
SELF='scripts/pr16_completion_checkpoint.py'
DIRECTORY='content/modernization/pr16_completion_evidence'
RECEIPT='content/modernization/pr16_completion_acceptance.json'
OVERVIEW='content/modernization/p08_remaining_work.json'
BRANCH='codex/modernization-followup-20260908'
REPO='dekaazarashi1111-web/pokemon-vega-modern'
CANDIDATE={'size':33554432,'sha256':repaired.ROM_SHA}
RECORDS={
 'repaired':(34512326368,10166560990,346718,'33cbb261552483e67d2ade7bdc9846b463170b515a2d22acbe0412a97f8640f9','d49c3d721f3eac994a48d190e980dc34346f0942','pr16-evolution-learning-repair','pr16-repaired-candidate-acceptance',''),
 'evolution':(34552826501,10181460518,88421,'7216ccd85b33f16570c18828fea9d7055835c24d8129e6f77cb2b5da5d97a8d4','37ec0121e8170673542adb1e1213d51954bad576','pr16-evolution-fullslots','pr16-evolution-fullslots-acceptance','pr16-evolution-fullslots-evidence/'),
 'breeding':(34553503441,10181812146,104337,'cd46b3273cb1519044100847ea38f65d1a81bea632909d984107781cab657011','64bf90f83cb928b989fea45ff52696f0d3f775e9','pr16-breeding-delta','pr16-breeding-delta-acceptance','pr16-breeding-delta-evidence/'),
}
DOMAINS=['p02','mega_shop','floette','p03','p04_mega_runtime','battle_policy','p05']
GUARDS=['bus8','bus16','bus32','raw8','raw16','raw32','register']


def same(a,b):return type(a) is type(b) and stable(a)==stable(b)

def fields(value,expected):
    need(type(value) is dict,'object required')
    for key,want in expected.items():need(same(value.get(key),want),'record field differs: '+key)


def load(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(ValueError(s)))


def read(root,path):
    p=root/path;need(not any(q.is_symlink() for q in (p,*p.parents)),'symlink input')
    return p.read_bytes()


def archive(raw,depth=0):
    need(depth<=2,'nested archive depth')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();need(len(entries)<2000 and sum(e.file_size for e in entries)<30000000,'ZIP bounds')
        names=[e.filename for e in entries];need(len(names)==len(set(names)),'duplicate ZIP members')
        out={}
        for e in entries:
            p=Path(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and not e.is_dir(),'unsafe ZIP path')
            need(((e.external_attr>>16)&0o170000)!=0o120000,'symlink member')
            need(p.suffix.lower() not in ('.gba','.gb','.sav','.srm','.ss0','.state','.bin'),'ROM/save/binary evidence forbidden')
            out[e.filename]=z.read(e)
            if p.suffix.lower()=='.zip':archive(out[e.filename],depth+1)
        return out


def metadata(value,record):
    run,aid,size,sha,head,wf,name,_=record
    fields(value,dict(run_id=run,head_sha=head,head_branch=BRANCH,run_attempt=1,
                      path='.github/workflows/'+wf+'.yml',status='completed',conclusion='success',
                      artifact_id=aid,artifact_name=name,size=size,sha256=sha))
    jobs=value['jobs'];need(type(jobs) is list and len(jobs)==1,'one complete native job required')
    for j in jobs:
        fields(j,dict(run_id=run,head_sha=head,status='completed',conclusion='success'))
        need(j['steps'] and all(s['status']=='completed' and s['conclusion']=='success' for s in j['steps']),'failed/skipped/pending step')


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+REPO+'/'+path])
    def install(path,raw):
        target=root/path;need(not any(p.is_symlink() for p in (target,*target.parents)),'unsafe install path')
        if target.exists():need(target.read_bytes()==raw,'refuse original overwrite: '+str(path))
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    for record in RECORDS.values():
        run,aid,size,sha,head,wf,name,_=record
        r=load(api(f'actions/runs/{run}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
        a=load(api(f'actions/artifacts/{aid}'));fields(a['workflow_run'],dict(id=run,head_sha=head))
        need(jobs['total_count']==len(jobs['jobs']),'incomplete jobs listing')
        need(a['digest']=='sha256:'+sha,'artifact API digest differs')
        value={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        value.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,
                     jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        metadata(value,record)
        raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'download differs')
        archive(raw);directory=Path(DIRECTORY)/str(run)
        install(directory/'original.zip',raw);install(directory/'actions.json',stable(value))


def process(files,prefix):
    p=load(files[prefix+'.process.json'])
    return repaired.native_module().validator().previous.require_exited(p)


def guards(files,prefix):
    for guard in GUARDS:
        p=prefix+'guard-'+guard
        need(process(files,p)==1 and files[p+'.stdout']==b'' and files[p+'.stderr']==b'P03 archive: host write after observation barrier\n','physical write guard differs')


def learning(files,prefix,module):
    report=load(files[prefix+'result.json'])
    fields(report,dict(status='PASS',candidate=CANDIDATE,failures=[],old_runs_relabelled=0,
                       actual_new_processes=len(module.CASES),successful_fresh_cores=2*len(module.CASES),release_ready=False))
    need(len(report['results'])==len(module.CASES),'learning raw count')
    for case,expected in zip(module.CASES,report['results'],strict=True):
        p=prefix+case[0]
        got=module.validate(files[p+'.stdout'],case,load(files[p+'.process.json']),files[p+'.stderr'])
        need(same(got,expected),'learning report/raw differs')
    guards(files,prefix)
    return [c[0] for c in module.CASES]


def build(root=ROOT):
    sets={};originals={}
    for label,record in RECORDS.items():
        run,aid,size,sha,head,wf,name,inside=record;directory=Path(DIRECTORY)/str(run)
        metadata(load(read(root,directory/'actions.json')),record)
        raw=read(root,directory/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'original differs: '+label)
        f=archive(raw);need(f[inside+'tested-head.txt'].decode().strip()==head,'native HEAD differs')
        snapshot=archive(f[inside+'sources.zip'])
        selected={'repaired':repaired.SELF,'evolution':evolution.SELF,'breeding':breeding.SELF}[label]
        need(read(root,selected)==snapshot[selected],'executed adapter source differs: '+selected)
        sets[label]=f;originals[label]=dict(run_id=run,tested_head=head,artifact_id=aid,path=str(directory/'original.zip'),size=size,sha256=sha)
    f=sets['repaired'];candidate=load(f['candidate.json'])
    fields(candidate,dict(candidate=CANDIDATE,crc32='5B8BFB51',move_table_changes=0,save_layout_changes=0,release_ready=False,active_baseline_changed=False))
    need(f['build-a.stdout']==f['build-b.stdout'],'independent repair builds differ')
    nat=repaired.native_module();learn=repaired.load('pr16_native_learning');learn.native=nat
    levels=learning(f,'acceptance/learning/',learn)
    evolved=learning(sets['evolution'],'pr16-evolution-fullslots/',evolution.module())
    mem=load(f['acceptance/memory/result.json']);api=nat.validator()
    fields(mem,dict(status='PASS',candidate=CANDIDATE,failures=[],successful_processes=10,successful_fresh_cores=20,old_runs_relabelled=0,release_ready=False))
    vectors=load(f['acceptance/memory/vectors.json'])['cases'];need(len(vectors)==len(mem['cases'])==10,'memory cases differ')
    need(identity(f['acceptance/memory/vectors.json'])==mem['vectors'],'memory vector identity')
    for case,row in zip(vectors,mem['cases'],strict=True):
        p='acceptance/memory/'+case['name']
        got=api.validate_result(f[p+'.stdout'],case,load(f[p+'.process.json']),f[p+'.stderr'])
        need(same(got,row['result']),'memory raw differs')
    guards(f,'acceptance/memory/')
    p06=repaired.load('pr16_integrated_p06');p06.new=nat;base=p06.load_base()
    for name,sha in p06.PINS.items():need(identity(read(root,name))['sha256']==sha,'P06 source pin differs')
    phase=types.ModuleType('checkpoint_phase');phase.__file__=str(root/'scripts/run_modernization_p06_phase_e2e.py')
    text=p06.path_adapter(read(root,'scripts/run_modernization_p06_phase_e2e.py').decode());exec(compile(text,phase.__file__,'exec'),phase.__dict__);phase.base=base
    p6=load(f['acceptance/p06/result.json']);ph=load(f['acceptance/p06/phase/result.json'])
    fields(p6,dict(status='PASS',candidate=CANDIDATE,accepted_fields=3,accepted_species=2,fresh_phase_processes=10,
                   phase_candidate_processes=9,unchanged_stage82_attack_controls=1,fresh_slot_processes=8,fresh_slot_cores=24,slot_failures=[],historical_results_relabelled=0))
    need(len(ph['cases'])==10 and len(p6['slot_results'])==8,'P06 raw counts')
    for i,name in enumerate(phase.CASES):
        p='acceptance/p06/phase/'+name
        need(same(phase.validate(f[p+'.stdout'],i,process(f,p)),ph['cases'][i]) and b'mGBA[' not in f[p+'.stderr'],'P06 phase raw differs')
    for case,row in zip(base.CASES,p6['slot_results'],strict=True):
        p='acceptance/p06/slots/'+'-'.join(map(str,case))
        need(same(base.validate(f[p+'.stdout'],case,process(f,p),repaired.ROM_SHA),row) and not f[p+'.stderr'],'P06 slot raw differs')
    for name,sha in p06.REVIEWED.items():
        raw=f['acceptance/p06/phase/'+name];phase.validate_picture(raw)
        need(identity(raw)==dict(size=115215,sha256=sha),'P06 reviewed pixels differ')
    guards(f,'acceptance/p06/phase/');guards(f,'acceptance/p06/slots/')
    gate=load(f['acceptance/domains/aggregate/runtime_gate.json'])
    fields(gate,dict(status='PASS_WITH_DECLARED_LIMITS',domain_order=DOMAINS))
    fields(gate['input']['rom'],dict(**CANDIDATE,path=repaired.ROM))
    recipe=gate['input']['recipe_report'];fields(recipe,dict(candidate=CANDIDATE,release_ready=False))
    reconciliation=recipe['reconciliation']
    fields(reconciliation['vega_to_official_historical_adoption'],dict(rows=1073,present=1073,missing=0,route_counts=dict(level_up=450,egg=254,machine=179,tutor=190)))
    fields(reconciliation['official_to_vega_legacy_preservation'],dict(rows=499,present=499,missing=0,route_counts=dict(level_up=310,egg=189)))
    need(len(gate['domains'])==7,'seven domain originals required')
    for name,merged in zip(DOMAINS,gate['domains'],strict=True):
        p='acceptance/domains/records/'+name+'/'
        row=load(f[p+'result.json']);fields(row,dict(id=name,status='PASS',input_rom=dict(path=repaired.ROM,**CANDIDATE),plan_fingerprint=gate['plan_fingerprint']))
        need(same(row['runner_result'],load(f[p+'runner.stdout.json'])),'domain raw differs')
        need(row['stderr_sha256']==hashlib.sha256(f[p+'runner.stderr.log']).hexdigest(),'domain stderr differs')
        for k in ('id','status','runner','runner_result','compilation','command_argument_count','stderr_sha256'):need(same(row[k],merged[k]),'domain merge differs')
    bf=sets['breeding'];prefix='pr16-breeding-delta/';br=load(bf[prefix+'result.json'])
    fields(br,dict(status='PASS',candidate=CANDIDATE,actual_new_processes=5,successful_fresh_cores=15,failures=[],old_runs_relabelled=0,release_ready=False))
    pp={int(k):v for k,v in br['oracle']['canonical_pp'].items()};need(pp=={0:0,39:30,84:30,175:15,273:10,344:15,440:40},'canonical PP original differs')
    bapi=breeding.configure(pp);need(len(br['results'])==5,'five actual breeding processes required')
    for case,row in zip(breeding.CASES,br['results'],strict=True):
        p=prefix+case[0];got=bapi.validate_result(bf[p+'.stdout'],case[0],process(bf,p))
        need(same(got,row['result']) and b'mGBA[' not in bf[p+'.stderr'],'breeding raw differs')
    guards(bf,prefix)
    return dict(schema_version=1,status='SCOPED_COMPLETION_PROGRESS_NOT_RELEASE',candidate=CANDIDATE,crc32='5B8BFB51',
                candidate_name='Stage84 + exact P07 preservation + native evolution dispatch repair',originals=originals,
                prior_candidate_sha256=repaired.layer.source.ROM_SHA,originals_relabelled=0,emulator_runs_by_this_verifier=0,
                session_new_native_processes=7,session_new_cores=19,
                p06=dict(adopted_phase_complete=True,adopted_species=2,adopted_fields=3,slot_processes=8,slot_cores=24,
                         phase_candidate_processes=9,stage82_attack_control_processes=1,reviewed_summary_pixels=p06.REVIEWED,
                         evidence_run=RECORDS['repaired'][0],acceptance_boundary='fixture before observation; ordinary Summary/battle/input/save thereafter; not natural acquisition'),
                p07=dict(source_reconciliation=reconciliation,prefix_legacy_rows=472,named_alias_legacy_rows=27,new_beyond_v4_rows=0,
                         new_adoption_decision_required=False,physical_memory_cases=[x['name'] for x in mem['cases']],physical_breeding_cases=[x[0] for x in breeding.CASES]),
                p03=dict(level_and_evolution_cases=levels+evolved,form_service_accepted=False,all_egg_supply_routes_accepted=False),
                regression=dict(domains=DOMAINS,evidence_run=RECORDS['repaired'][0],candidate_sha256=repaired.ROM_SHA,status='PASS_WITH_DECLARED_LIMITS'),
                full_p03_acceptance=False,full_p05_acceptance=False,full_p07_acceptance=False,clean_rom_regeneration_verified=False,
                release_ready=False,active_baseline_changed=False)


def project(current,root=ROOT):
    receipt=build(root);need(same(load(read(root,RECEIPT)),receipt),'completion receipt differs')
    out=deepcopy(current);out['status']='SCOPED_COMPLETION_PROGRESS_NOT_RELEASE'
    out['final_candidate']=dict(**CANDIDATE,crc32=receipt['crc32'],name=receipt['candidate_name'],release_approved=False)
    out['latest_scoped_candidate']=CANDIDATE;out['latest_scoped_candidate_stage']='84+P07+EVOLUTION_REPAIR'
    out['completion_checkpoint']=dict(source_path=RECEIPT,session_new_native_processes=7,session_new_cores=19,original_runs_preserved=True)
    out['full_p06_acceptance']=True;out['p06_adoption']['current_candidate_evidence']=RECEIPT
    out['p06_adoption']['accepted_requirements']=['adopted_three_fields_only','existing_and_new_slot_identity','native_stat_recalculation','normal_save_and_cold_continue','adopted_native_passive_effects_and_controls','rendered_summary_names_descriptions_and_attack']
    out['p07_adoption'].update(source_reconciliation=RECEIPT,decision_required=False,legacy_rows=499,prefix_legacy_rows=472,named_alias_legacy_rows=27,historical_additions=1073,new_beyond_v4_rows=0)
    closed=dict(id='P06_ADOPTED_PHASE_ACCEPTANCE',original_id='PHASE_ACCEPTANCE',phase='P06',evidence=RECEIPT,
                pass_condition='Three adopted fields only: slot/stat/save, native abilities/controls and rendered applicable Summary')
    out['closed_conditions']=[r for r in out.get('closed_conditions',[]) if r['id']!=closed['id']]+[closed]
    remaining=[]
    for old in out['remaining_conditions']:
        row=deepcopy(old);key=row['id']
        if key=='PHASE_ACCEPTANCE':continue
        if key=='EVOLUTION_FORM_OTHER_EGG':
            row.update(reason_ja='進化の空き・満杯・取消とPichu復元タマゴ技の実繁殖5件は受入済み。残るフォームサービス操作と他の採用供給経路を特定して確認する。',success_evidence=RECEIPT,
                       resume='overlays/modernization_p03_stage73_consumer_runtime; CollectionSupply_FieldHost -> form party selection -> Stage73_CollectionApplySelectedForm -> ordinary save/cold Continue; preserve current evolution and breeding passes')
        elif key=='SOURCE_RECONCILIATION_ADOPTION':
            row.update(id='P07_REMAINING_ROUTE_ACCEPTANCE',reason_ja='V4照合・1073採用追加・472+27既存保持の実装は済み。新規配布表の判断待ちではない。経路別の未受入差分を特定し、必要な実操作のみ補う。',success_evidence=RECEIPT,
                       resume='scripts/pr16_p07_preserved_layer.py; content/modernization/p07_preserved_layer_spec.json; compare exact Happiny baby/incense and form consumers with accepted memory/breeding evidence; do not re-adopt or double-apply rows')
        elif key=='FINAL_NATIVE_ACCEPTANCE':
            row.update(reason_ja='修復候補635fd890上の7領域・P06・進化・技メモリー・Pichu繁殖は受入済み。残るP03/P07/P05実経路を同一候補へ接続する。',success_evidence=RECEIPT,
                       resume='scripts/pr16_repaired_acceptance.py; scripts/pr16_evolution_fullslots.py; scripts/pr16_breeding_delta.py; only repeat affected evidence when candidate changes')
        remaining.append(row)
    out['remaining_conditions']=remaining;out['source_bindings'][RECEIPT]=identity(read(root,RECEIPT))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.fetch:fetch()
    value=build();path=ROOT/RECEIPT
    if args.write:
        if path.exists():need(same(load(path.read_bytes()),value),'refuse receipt replacement')
        else:path.write_bytes(stable(value))
    else:need(same(load(path.read_bytes()),value),'completion receipt differs')
    print(json.dumps(dict(status='PASS',candidate_sha256=repaired.ROM_SHA,originals_verified=3,new_emulator_runs=0,release_ready=False)))

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,zipfile.BadZipFile,subprocess.CalledProcessError) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
