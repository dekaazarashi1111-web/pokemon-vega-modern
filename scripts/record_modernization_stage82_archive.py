#!/usr/bin/env python3
"""Record verified Stage82 original Actions artifacts without promoting release."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request
import zipfile
import io

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
import run_modernization_p03_archive_ui_e2e as archive
import run_modernization_p03_fullslots_e2e as old

REPO='dekaazarashi1111-web/pokemon-vega-modern'
RECORD='content/modernization/p08_stage82_archive_acceptance.json'
ORDER=['p02','mega_shop','floette','p03','p04_mega_runtime','battle_policy','p05']
ARTIFACTS=['stage82-plan','stage82-archive-ui']+['stage82-domain-'+d for d in ORDER]


def require(ok,message):
    if not ok: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()


def read(path): return old.strict_json(path.read_bytes())


def get(url,binary=False):
    require(url.startswith('https://api.github.com/repos/'+REPO+'/actions/'),'non-repository Actions URL')
    request=urllib.request.Request(url,headers={
            'Accept':'application/vnd.github+json','User-Agent':'Stage82-evidence-recorder'})
    # The GitHub bearer token authenticates ONLY this request, never the signed
    # Azure redirect. Ordinary Request headers are copied by urllib on 302.
    request.add_unredirected_header('Authorization','Bearer '+os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request,timeout=120) as response:data=response.read()
    return data if binary else old.strict_json(data)


def verify_zip_members(data,directory):
    """Every extracted byte must originate in the digest-checked GitHub ZIP."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist()
        require(len(names)==len(set(names)),'duplicate ZIP member')
        members=set()
        for name in names:
            p=Path(name)
            require(not p.is_absolute() and '..' not in p.parts,'unsafe ZIP member')
            if name.endswith('/'):continue
            require(not (directory/p).is_symlink(),'symlink in extracted artifact')
            require((directory/p).read_bytes()==z.read(name),'original ZIP/extraction mismatch: '+name)
            members.add(p.as_posix())
        require(members=={p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()},'extra or missing extracted file')


def validate_archive(directory):
    report=read(directory/'result.json')
    require(report['status']=='PASS' and report['candidate_sha256']==archive.repair.CANDIDATE_SHA,'archive candidate/status differs')
    for field,expected in [('fresh_successful_mgba_processes',25),('fresh_negative_mgba_processes',2),('cached_passes',0),
                            ('release_ready',False),('full_p03_acceptance',False),('breeding_e2e',False)]:
        require(old.same_typed(report[field],expected),'archive aggregate differs: '+field)
    cases=archive.vectors();require(len(report['cases'])==25,'missing case records')
    for c,row in zip(cases,report['cases']):
        require(row['name']==c['name'],'case identity differs')
        process=read(directory/(c['name']+'.process.json'))
        require(process==row['process'],'process receipt differs')
        result=archive.validate_result((directory/(c['name']+'.stdout')).read_bytes(),c,old.require_exited(process))
        require(result==row['result'],'case JSON differs from original stdout')
        for suffix in ('stdout','stderr'):
            require(old.identity(directory/(c['name']+'.'+suffix))==row[suffix],'case original bytes differ')
    require([r['name'] for r in report['negative_controls']]==['parent-gate','gate-only-list'],'negative set differs')
    for row in report['negative_controls']:
        name=row['name'];process=read(directory/(name+'.process.json'))
        require(process==row['process'],'negative process differs')
        archive.validate_negative((directory/(name+'.stdout')).read_bytes(),(directory/(name+'.stderr')).read_bytes(),old.require_exited(process),name)
        for suffix in ('stdout','stderr'):
            require(old.identity(directory/(name+'.'+suffix))==row[suffix],'negative original bytes differ')
    require([g['api'] for g in report['host_write_guard_checks']]==list(archive.GUARDS),'host-write guard set differs')
    for api in archive.GUARDS:
        p=read(directory/('guard-'+api+'.process.json'))
        require(old.require_exited(p)==1 and not (directory/('guard-'+api+'.stdout')).read_bytes(),'guard did not reject')
        require((directory/('guard-'+api+'.stderr')).read_bytes()==b'P03 archive: host write after observation barrier\n','guard rejection differs')
    for path,identity in report['sources'].items():
        require(old.identity(ROOT/path)==identity,'tested source no longer matches: '+path)
    return report


def check():
    record=read(ROOT/RECORD)
    require(record['status']=='VERIFIED_WITH_DECLARED_LIMITS' and record['release_ready'] is False,'record promoted beyond evidence')
    root=ROOT/record['evidence_root']
    for relative,identity in record['files'].items():
        p=Path(relative);require(not p.is_absolute() and '..' not in p.parts,'unsafe manifest path')
        require(old.identity(root/p)==identity,'recorded original hash differs: '+relative)
    validate_archive(root/'stage82-archive-ui')
    merge=read(root/'merged/merge-summary.json')
    require(merge['status']=='GITHUB_MATRIX_MERGE_PASS' and merge['domain_order']==ORDER and
            type(merge['matrix_mGBA_process_runs']) is int and merge['matrix_mGBA_process_runs']==7 and
            type(merge['merge_mGBA_process_runs']) is int and merge['merge_mGBA_process_runs']==0,'matrix merge receipt differs')
    require(read(root/'merged/check.json')['status']=='CHECK_PASS','merged engine check missing')
    import run_modernization_stage82_github_domain as stage
    stage.prepare()
    for domain in ORDER:
        stage_command=[sys.executable,str(ROOT/'scripts/run_modernization_stage82_github_domain.py'),'validate-domain','--domain',domain,'--record',str(root/('stage82-domain-'+domain)/'result.json')]
        import subprocess
        subprocess.run(stage_command,check=True,capture_output=True)
    for name in ARTIFACTS:
        verify_zip_members((root/'original-zips'/(name+'.zip')).read_bytes(),root/name)
    require(record['fresh_successful_mgba_processes']==32 and record['negative_controls']==2,'total execution count differs')
    return {'status':'CHECK_PASS','candidate_sha256':archive.repair.CANDIDATE_SHA,'release_ready':False}


def record():
    integration_run=int(os.environ['GITHUB_RUN_ID'])
    run=int(os.environ.get('STAGE82_SOURCE_RUN',str(integration_run)))
    tested=os.environ['STAGE82_TESTED_HEAD']
    base='https://api.github.com/repos/'+REPO+'/actions/runs/'+str(run)
    run_info=get(base)
    require(run_info['id']==run and run_info['head_branch']=='codex/modernization-followup-20260908','source run identity differs')
    jobs=get(base+'/jobs?per_page=100')['jobs']
    required=['prepare','archive-ui']+['stage82 domain / '+d for d in ORDER]
    for name in required:
        found=[j for j in jobs if j['name']==name]
        require(len(found)==1 and found[0]['status']=='completed' and found[0]['conclusion']=='success','required job not successful: '+name)
    source=ROOT/'.local/stage82-input'
    validate_archive(source/'stage82-archive-ui')
    target=ROOT/'content/modernization/p08_stage82_evidence'/str(run)
    require(not target.exists(),'evidence directory already exists')
    target.mkdir(parents=True)
    for name in ARTIFACTS:
        shutil.copytree(source/name,target/name)
        require((target/name/'tested-head.txt').read_text().strip()==tested,'mixed tested commit: '+name)
    shutil.copytree(ROOT/'.local/stage82-merged',target/'merged')
    artifacts=get(base+'/artifacts?per_page=100')['artifacts']
    (target/'original-zips').mkdir()
    for name in ARTIFACTS:
        rows=[a for a in artifacts if a['name']==name]
        require(len(rows)==1 and rows[0]['expired'] is False,'artifact not unique/live: '+name)
        item=rows[0];data=get(item['archive_download_url'],True)
        require(item.get('digest')=='sha256:'+sha(data),'GitHub original ZIP digest differs')
        # Bind the extracted records to the original ZIP, not just to an
        # independent checksum of a possibly different local extraction.
        verify_zip_members(data,target/name)
        (target/'original-zips'/(name+'.zip')).write_bytes(data)
    (target/'actions-run.json').write_text(json.dumps(run_info,indent=2)+'\n')
    (target/'actions-jobs.json').write_text(json.dumps(jobs,indent=2)+'\n')
    (target/'actions-artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    files={p.relative_to(target).as_posix():old.identity(p) for p in sorted(target.rglob('*')) if p.is_file()}
    result={'schema_version':1,'status':'VERIFIED_WITH_DECLARED_LIMITS','candidate_sha256':archive.repair.CANDIDATE_SHA,
            'tested_code_commit':tested,'actions_run_id':run,'actions_run_status_at_record':run_info['status'],
            'actions_run_conclusion_at_record':run_info['conclusion'],'integration_run_id':integration_run,
            'integration_code_commit':os.environ['GITHUB_SHA'],
            'evidence_root':target.relative_to(ROOT).as_posix(),'files':files,
            'fresh_successful_mgba_processes':32,'archive_ui_cases':25,'cumulative_domains':7,
            'negative_controls':2,'cached_passes':0,'merge_new_processes':0,
            'closed_conditions':['post-HOF machine/tutor entry','all four replacement slots','all four machine pages',
                'archive refuse/cancel and pre-HOF denial','normal save and fresh-core Continue for 25 archive cases'],
            'remaining_conditions':['breeding/egg routes','other P03 paths and complete archive economy acceptance',
                'full P05 acceptance','P06/P07 adoption and implementation','final release acceptance'],
            'active_stage62_baseline_changed':False,'breeding_e2e':False,'full_p03_acceptance':False,'release_ready':False}
    (ROOT/RECORD).write_text(json.dumps(result,indent=2)+'\n')
    checked=check()
    entry=f'\n## 2026-09-10 — USER-P03-ARCHIVE-UI / Stage82\n\nRun {run}, tested code {tested}: exact Stage82 {archive.repair.CANDIDATE_SHA}; 25 new native archive UI/save/fresh-core cases and seven fresh cumulative domains passed. Two separate pre-repair failure controls were retained (the gate-only control also reproduces the specifically classified illegal opcode before the metadata assertion). Three observation barriers and seven host-write denial probes are enforced. P08 originals are in {target.relative_to(ROOT)}; record checker passes. Stage62, historical Stage79/81 evidence, Draft state and release_ready=false are unchanged. Breeding, other P03/P05 paths, P06/P07 and release remain incomplete.\n'
    for path in ('design/run_log.md','design/version_log.md'):
        with (ROOT/path).open('a') as f:f.write(entry)
    return checked


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record',action='store_true');args=parser.parse_args()
    print(json.dumps(record() if args.record else check(),indent=2))


if __name__=='__main__':main()
