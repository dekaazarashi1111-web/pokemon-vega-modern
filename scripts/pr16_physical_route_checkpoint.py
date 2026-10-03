#!/usr/bin/env python3
"""Retain exact new physical route originals and advance only verified subroutes.

No emulator is executed here. Historical acceptance, active saves/baseline,
owner-approved public visibility and free move memory are not rewritten.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT))
import pr16_completion_checkpoint as prior
import pr16_form_routes as forms
import pr16_happiny_breeding as happiny
need=prior.need
SELF='scripts/pr16_physical_route_checkpoint.py'
RECEIPT='content/modernization/pr16_physical_route_acceptance.json'
DIRECTORY='content/modernization/pr16_physical_route_evidence'
RECORDS={
 'p06_current':(34556825622,10182862548,13564,'3078ef8a535ca5036518ab3bfc1b0fc930b14284acf467ca3113d22a862d5401','7ebc44f83ef2c4e4e49bb6151adc2e144acaff15','pr16-p06-current-reconcile','pr16-p06-current-reconcile',''),
 'forms':(34559437267,10183811918,378861,'7468c5f2004da2272616b0c9871fc0f5b4ca5a5d66c75d87e873666f4a141615','228cce1ce94aa26990c1c977f018785bfe00d391','pr16-form-routes','pr16-form-routes-acceptance','pr16-form-evidence/'),
 'happiny':(34558529636,10183885718,97240,'3754678bd00a095d33cde20201b9b2206d35a076cf127d07cfa9ce2318af556a','25925166a26f50edc5668cd5727b29498963f44e','pr16-happiny-breeding','pr16-happiny-breeding-acceptance','pr16-happiny-evidence/'),
}


def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    def install(path,raw):
        p=root/path;need(not any(q.is_symlink() for q in (p,*p.parents)),'symlink original destination')
        if p.exists():need(p.read_bytes()==raw,'refuse original overwrite: '+str(path))
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    for record in RECORDS.values():
        run,aid,size,sha,head,wf,name,_=record
        r=prior.load(api(f'actions/runs/{run}'));jobs=prior.load(api(f'actions/runs/{run}/jobs?per_page=100'))
        a=prior.load(api(f'actions/artifacts/{aid}'))
        prior.fields(a['workflow_run'],dict(id=run,head_sha=head))
        need(jobs['total_count']==len(jobs['jobs']) and a['digest']=='sha256:'+sha,'incomplete or changed Actions origin')
        meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,
                    jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        prior.metadata(meta,record)
        raw=api(f'actions/artifacts/{aid}/zip');need(prior.identity(raw)==dict(size=size,sha256=sha),'download identity differs')
        prior.archive(raw);directory=Path(DIRECTORY)/str(run)
        install(directory/'original.zip',raw);install(directory/'actions.json',prior.stable(meta))


def original(root,label):
    record=RECORDS[label];run,aid,size,sha,head,wf,name,prefix=record;directory=Path(DIRECTORY)/str(run)
    meta=prior.load(prior.read(root,directory/'actions.json'));prior.metadata(meta,record)
    raw=prior.read(root,directory/'original.zip');need(prior.identity(raw)==dict(size=size,sha256=sha),'retained ZIP changed')
    files=prior.archive(raw);need(files[prefix+'tested-head.txt']==(head+'\n').encode(),'tested HEAD differs')
    return files,dict(run_id=run,tested_head=head,artifact_id=aid,path=str(directory/'original.zip'),size=size,sha256=sha)


def verify_p06(files):
    for name in ('originals.json','refresh.json','check.json','final-generator.json','forgetting-generator.json','post-commit-check.json'):
        value=prior.load(files[name]);prior.fields(value,dict(status='PASS',new_emulator_runs=0,release_ready=False))
    current=prior.load(files['current-view.json'])
    need(current['full_p06_acceptance'] is True and current['p06_adoption']['full_phase_accepted'] is True,'P06 mirror not accepted')
    need(files['published-head.txt']==b'a1ce109338f12f7f3f584a303a387e72c64c0fc5\n','P06 published HEAD differs')
    log=files['unit.log'].decode();need(re.findall(r'Ran (\d+) tests',log)==['6','5','11','12'] and log.count('\nOK\n')==4,'P06 target test completion differs')
    return dict(p06_nested_phase_consistent=True,unit_tests=34,new_emulator_runs=0,rom_changed=False)


def verify_forms(files,root=ROOT):
    prefix='pr16-form-routes/';report=prior.load(files[prefix+'result.json'])
    prior.fields(report,dict(status='PASS',scope=forms.SCOPE,candidate=prior.CANDIDATE,failures=[],
        actual_new_processes=10,successful_fresh_cores=25,physical_rotom_service_accepted=True,
        other_form_and_egg_supply_accepted=False,full_p03_acceptance=False,release_ready=False,old_runs_relabelled=0))
    need(report['guard_checks']==prior.GUARDS and len(report['results'])==len(forms.CASES),'form count/guard list differs')
    rows=[]
    for name,row in zip(forms.CASES,report['results'],strict=True):
        p=prefix+name;process=prior.load(files[p+'.process.json'])
        value=forms.validate(files[p+'.stdout'],name,forms.common.require_exited(process))
        need(prior.same(row,dict(name=name,result=value,process=process)) and b'mGBA[' not in files[p+'.stderr'],'form raw/report mismatch')
        for index,trace in enumerate(value['traces']):
            for suffix in ('root','continued'):
                image=files[p+f'-{index}-{suffix}.ppm']
                need(image.startswith(b'P6\n240 160\n255\n') and len(image)==115215,'rendered form witness missing')
                need(len(set(image[15:]))>16,'blank form witness')
        rows.append(dict(case=name,fresh_cores=value['fresh_cores'],operations=value['rounds'],
                         automatic_saves=value['automatic_saves'],manual_saves=value['manual_saves']))
    prior.guards(files,prefix)
    need(prior.same(report['oracle'],prior.load(files[prefix+'oracle.json'])),'form independent oracle differs')
    prior.fields(report['oracle'],dict(candidate=prior.CANDIDATE,bg_script_address='0x9411ffc',bg_script_prefix='6a160480030023115b4009',
                                      signature_moves=list(forms.SIGNATURES),signature_pp=list(forms.PP),starting_progress_and_individual_fixture=True))
    nested=prior.archive(files['pr16-form-evidence/sources.zip']);bindings=prior.load(files['pr16-form-evidence/source-bindings.json'])
    need(set(nested)==set(bindings),'form original source membership differs')
    for name,binding in bindings.items():need(prior.same(prior.identity(nested[name]),binding),'form archived source digest differs')
    for name,binding in report['sources'].items():need(prior.same(prior.identity(prior.read(root,name)),binding),'form tested source changed: '+name)
    need(forms.SOURCE in bindings and forms.SELF in bindings and forms.TEST in bindings,'form controller/validator not retained')
    need(b'Ran 7 tests' in files['pr16-form-evidence/unit.log'] and files['pr16-form-evidence/unit.log'].endswith(b'OK\n'),'form unit completion differs')
    return dict(physical_rotom_service_accepted=True,new_native_processes=10,fresh_cores=25,
                physical_service_interactions=15,successful_form_changes=11,cases=rows,starting_progress_individual_map_are_fixtures=True,
                other_form_and_egg_supply_accepted=False,full_p03_acceptance=False,release_ready=False)


def verify_happiny(files,root=ROOT):
    prefix='pr16-happiny-breeding/';report=prior.load(files[prefix+'result.json'])
    prior.fields(report,dict(status='PASS',scope=happiny.SCOPE,candidate=prior.CANDIDATE,failures=[],
        actual_new_processes=5,successful_fresh_cores=15,happiny_retained_incense_routes_accepted=True,
        all_breeding_paths_accepted=False,full_p03_acceptance=False,full_p07_acceptance=False,release_ready=False,old_runs_relabelled=0))
    need(report['guard_checks']==prior.GUARDS and len(report['results'])==5,'Happiny count/guard list differs')
    audit=report['oracle'];need(prior.same(audit,prior.load(files[prefix+'oracle.json'])),'Happiny oracle differs')
    pp={0:0,1:35,204:20,343:25,357:10,461:5,464:10,539:20,549:15}
    prior.fields(audit,dict(canonical_pp={str(k):v for k,v in pp.items()},incense_item=862,
                           candidate_child_level_one={'364':[1,539],'365':[1,111,186,204,343,539,549]},
                           old_egg=[69,215,217,716],new_egg=[69,215,217,716,461,464,357],no_incense_child_species=365,no_incense_egg=[281]))
    happiny.source_rows({happiny.repaired.layer.LAYER:audit['source_rows']});api=happiny.configure(pp);rows=[]
    for case,row in zip(happiny.CASES,report['results'],strict=True):
        name=case[0];p=prefix+name;process=prior.load(files[p+'.process.json'])
        value=api.validate_result(files[p+'.stdout'],name,api.common.require_exited(process))
        need(prior.same(row,dict(name=name,result=value,process=process)) and b'mGBA[' not in files[p+'.stderr'],'Happiny raw/report mismatch')
        rows.append(dict(case=name,child_species=value['child_species'],moves=value['moves'],
                         hatch_steps=value['hatch_steps'],fresh_cores=value['fresh_cores']))
    prior.guards(files,prefix)
    need(files[prefix+'executed-controller.c']==happiny.controller_source().encode(),'executed Happiny controller differs')
    need(files[prefix+'executed-validator.py']==happiny.validator_source().encode(),'executed Happiny validator differs')
    nested=prior.archive(files['pr16-happiny-evidence/sources.zip']);bindings=prior.load(files['pr16-happiny-evidence/source-bindings.json'])
    need(set(nested)==set(bindings),'Happiny source membership differs')
    for name,binding in bindings.items():need(prior.same(prior.identity(nested[name]),binding),'Happiny archived source digest differs')
    for name,binding in report['sources'].items():need(prior.same(prior.identity(prior.read(root,name)),binding),'Happiny tested source changed: '+name)
    return dict(happiny_retained_incense_routes_accepted=True,new_native_processes=5,fresh_cores=15,
                historical_preserved_moves=[461,464,357],cases=rows,parent_individuals_and_starting_map_are_fixtures=True,
                all_breeding_paths_accepted=False,full_p03_acceptance=False,full_p07_acceptance=False,release_ready=False)


def build(root=ROOT):
    p06,p06_origin=original(root,'p06_current');form_files,form_origin=original(root,'forms')
    egg_files,egg_origin=original(root,'happiny')
    return dict(schema_version=1,status='PASS_SCOPED_NOT_PRODUCT',candidate=prior.CANDIDATE,
                origins=dict(p06_current=p06_origin,forms=form_origin,happiny=egg_origin),p06=verify_p06(p06),
                forms=verify_forms(form_files,root),happiny=verify_happiny(egg_files,root),
                accepted_new_native_processes=15,accepted_new_native_cores=40,
                old_completion_receipt=prior.RECEIPT,old_native_runs_relabelled=0,
                p03_remaining='Reconcile other adopted form/egg supply consumers; Rotom physical menu is now accepted',
                p07_remaining='Reconcile remaining changed-consumer coverage; preserved Happiny incense routes are now accepted',
                p05_remaining=['natural capture/item acquisition into battle','actual Circus reception/admission into suppression'],
                clean_rom_full_regeneration_verified=False,full_p03_acceptance=False,full_p05_acceptance=False,
                full_p07_acceptance=False,release_ready=False)


def project(previous,root=ROOT):
    receipt=build(root);need(prior.same(prior.load(prior.read(root,RECEIPT)),receipt),'physical receipt differs from original revalidation')
    out=deepcopy(previous)
    out['physical_route_checkpoint']=dict(source_path=RECEIPT,candidate=prior.CANDIDATE,new_native_processes=15,new_native_cores=40,
                                          physical_rotom_service_accepted=True,happiny_retained_incense_routes_accepted=True,
                                          old_runs_preserved_not_relabelled=True,release_ready=False)
    out['final_integration']['additional_verified_native']=RECEIPT
    for row in out['remaining_conditions']:
        if row['id']=='EVOLUTION_FORM_OTHER_EGG':
            row.update(reason_ja='ロトム実サービスの付与・解除・満杯拒否・取消・保存は10件受入済み。その他の採用済み供給経路について既存原本と未確認範囲を照合する',
                       resume=SELF+' verifies 10 accepted Rotom paths; reconcile other adopted consumer classes, do not repeat successful forms',
                       target_function='remaining adopted form/egg supply consumers, excluding accepted Rotom host routes',
                       pass_condition='Map residual adopted consumers to exact existing or new native originals; keep Rotom/evolution/Pichu successes',
                       partial_success_evidence=RECEIPT)
        elif row['id']=='P07_REMAINING_ROUTE_ACCEPTANCE':
            row.update(reason_ja='ピンプクのおこう条件・復元3技・満杯・対照・孵化・保存は5件受入済み。残る変更対象の消費経路と既存原本の対応を照合する',
                       resume=SELF+' verifies Happiny incense routes; inventory remaining changed consumers, do not repeat Pichu/Happiny or recollect V4',
                       target_function='remaining P07 changed-consumer coverage beyond accepted memory/evolution/breeding',
                       partial_success_evidence=RECEIPT)
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');a=p.parse_args()
    if a.fetch:fetch()
    value=build();path=ROOT/RECEIPT
    if a.write:path.write_bytes(prior.stable(value))
    else:need(prior.same(prior.load(path.read_bytes()),value),'stored physical receipt differs')
    print(json.dumps(dict(status='PASS',candidate_sha256=prior.CANDIDATE['sha256'],originals_verified=True,
                         retained_new_native_processes=15,retained_new_native_cores=40,new_emulator_runs=0,release_ready=False)))

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,OSError,KeyError,TypeError,zipfile.BadZipFile) as exc:
        print(str(exc),file=sys.stderr);raise SystemExit(1)
