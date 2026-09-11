#!/usr/bin/env python3
"""Retain the actual static probe and rejected gear runs without relabelling them."""
import argparse
import io
from pathlib import Path
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_shop_display_checkpoint as display
prior=display.prior;need=prior.need;load=prior.load;stable=prior.stable;identity=prior.identity
DIRECTORY='content/modernization/pr16_gear_evidence'
RECEIPT='content/modernization/pr16_gear_originals.json'
# run, artifact, bytes, SHA256, actual execution HEAD, workflow, conclusion
RECORDS={
 'probe':(34579454070,10191015811,16626310,'12a465f0eb375b6febb8e8eb0c998aaf8425f476c2500080b6a5444b4617688c','665bd5e82c0cf2492c98cc8d9748ee6f160d10e2','pr16-gear-route-probe','success'),
 'compile_rejected':(34583082652,10192446522,132810,'f8c37244fd03bcdf41990b66bf441c7a8a6627216faef55020cf6072b8bc12e6','72f3cdb97382285ce9133540bc09b22d4b847982','pr16-purchased-gear','failure'),
 'field_rejected':(34585139774,10193291472,366866,'3d77102fae7f40f62fce00f3a1900931d6e510178514f17a94e350741843f390','3c199d8e2d0c44a75ef0687b79a5ec6ffbd63b4e','pr16-purchased-gear','failure'),
 'policy_rejected':(34585692527,10193527572,458433,'c7191e560b7f0a50602164c6c9ee2c5e739179eb57bcfc77de0a393409ed1d14','7ee8b23ba72f6d389ed07cd0c5cc4c55a80b7cac','pr16-purchased-gear','failure'),
}

def probe_archive(raw,depth=0,budget=None):
    """Probe contains 3381 UTF-8 repository sources; no ROM/save/binary allowed."""
    need(depth<=1,'probe nesting differs')
    if budget is None:budget=[128*1024*1024]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries=z.infolist();names=[e.filename for e in entries]
        need(len(entries)<=4000 and len(names)==len(set(names)),'probe ZIP members differ')
        budget[0]-=sum(e.file_size for e in entries);need(budget[0]>=0,'probe expansion limit')
        out={}
        for e in entries:
            p=Path(e.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and not e.is_dir(),'unsafe probe member')
            need(((e.external_attr>>16)&0o170000)!=0o120000,'probe symlink')
            need(p.suffix.lower() not in ('.gba','.gb','.sav','.srm','.ss0','.state','.bin','.elf','.so'),'binary probe member')
            value=z.read(e)
            if p.suffix.lower()=='.zip':probe_archive(value,depth+1,budget)
            else:value.decode('utf8');need(b'\0' not in value,'binary disguised as probe source')
            out[e.filename]=value
        return out

def metadata(meta,rec):
    run,aid,size,sha,head,wf,conclusion=rec
    prior.fields(meta,dict(run_id=run,artifact_id=aid,size=size,sha256=sha,head_sha=head,head_branch=prior.BRANCH,run_attempt=1,path='.github/workflows/'+wf+'.yml',artifact_name=wf,status='completed',conclusion=conclusion))
    jobs=meta['jobs'];need(type(jobs) is list and len(jobs)==1,'gear origin job count')
    for job in jobs:
        prior.fields(job,dict(run_id=run,head_sha=head,status='completed',conclusion=conclusion))
        need(job['steps'] and all(s['status']=='completed' for s in job['steps']),'incomplete gear origin steps')
        if conclusion=='success':need(all(s['conclusion']=='success' for s in job['steps']),'non-success probe step')
        else:need(any(s['conclusion']=='failure' for s in job['steps']),'missing rejected-run failure')

def fetch(root=ROOT):
    def api(path):return subprocess.check_output(['gh','api','repos/'+prior.REPO+'/'+path])
    for label,rec in RECORDS.items():
        run,aid,size,sha,head,wf,conclusion=rec
        r=load(api(f'actions/runs/{run}'));a=load(api(f'actions/artifacts/{aid}'));jobs=load(api(f'actions/runs/{run}/jobs?per_page=100'))
        prior.fields(a['workflow_run'],dict(id=run,head_sha=head));need(a['digest']=='sha256:'+sha and jobs['total_count']==len(jobs['jobs']),'gear provenance differs')
        meta={k:r[k] for k in ('head_sha','head_branch','run_attempt','path','status','conclusion')}
        meta.update(run_id=r['id'],artifact_id=a['id'],artifact_name=a['name'],size=a['size_in_bytes'],sha256=sha,jobs=[{k:j[k] for k in ('id','name','run_id','head_sha','status','conclusion','steps')} for j in jobs['jobs']])
        metadata(meta,rec);raw=api(f'actions/artifacts/{aid}/zip');need(identity(raw)==dict(size=size,sha256=sha),'gear original download differs')
        (probe_archive if label=='probe' else display.archive)(raw)
        for name,data in [('original.zip',raw),('actions.json',stable(meta))]:
            p=root/DIRECTORY/str(run)/name;need(not any(q.is_symlink() for q in (p,*p.parents)),'unsafe gear destination')
            if p.exists():need(p.read_bytes()==data,'refuse gear original overwrite')
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)

def verify(label,files):
    rec=RECORDS[label];prefix='' if label=='probe' else 'pr16-purchased-gear-evidence/'
    need(files[prefix+'tested-head.txt']==(rec[4]+'\n').encode(),'original execution HEAD differs')
    if label=='probe':
        graph=load(files['route-graph.json']);prior.fields(graph,dict(status='STATIC_ROUTE_PROBE_NOT_NATIVE_ACCEPTANCE',candidate=display.CANDIDATE,new_emulator_runs=0,gear_to_battle_accepted=False,full_p05_acceptance=False,release_ready=False))
        snapshot=probe_archive(files['sources.zip']);need(len(snapshot)==3381,'probe snapshot source count')
        need(prior.same(load(files['source-bindings.json']),{k:identity(v) for k,v in snapshot.items()}),'probe source bindings differ')
        return dict(status='STATIC_ORIGINAL_RETAINED_NOT_NATIVE_ACCEPTANCE',source_files=3381,new_native_passes=0)
    p='pr16-purchased-gear/'
    if label=='compile_rejected':
        need(b'BATTLE_SIZE' in files[p+'compile.stderr'] and load(files[p+'compile.process.json'])['returncode']!=0,'expected compile rejection absent')
        return dict(status='COMPILE_REJECTION_RETAINED',new_native_passes=0)
    report=load(files[p+'result.json']);prior.fields(report,dict(status='FAIL',schema_version=1,candidate=display.CANDIDATE,purchased_gear_to_battle_accepted=False,full_p05_acceptance=False,release_ready=False))
    if label=='field_rejected':
        need(len(report['failures'])==3 and not report['results'],'field failure scope changed')
        for name in ('eelektross-active','eelektross-no-toggle','eelektross-cancel-toggle'):
            need(b'gear equip menus did not return to field' in files[p+name+'.stderr'],'field rejection absent')
        return dict(status='LIVE_RECORDING_PREDICATE_REJECTION_RETAINED',new_native_passes=0)
    need([x['name'] for x in report['failures']]==['eelektross-active'],'policy failure scope changed')
    need(b'gear native Mega activation/control differs' in files[p+'eelektross-active.stderr'],'policy rejection absent')
    need([x['name'] for x in report['results']]==['eelektross-no-toggle','eelektross-cancel-toggle'],'historical successful subset changed')
    for row in report['results']:
        loc=p+row['name'];value=load(files[loc+'.stdout']);process=load(files[loc+'.process.json'])
        need(prior.same(row,dict(name=row['name'],result=value,process=process)),'historical raw/report mismatch')
        prior.fields(value,dict(status='PASS',schema_version=1,fresh_cores=3,mega_species=411,ability=26,full_p05_acceptance=False,release_ready=False))
        need(type(process['returncode']) is int and process['returncode']==0,'historical subset did not exit zero')
    return dict(status='VOLATILE_POLICY_REJECTION_RETAINED',historical_successful_processes=2,historical_successful_cores=6,accepted_mega_cases=0,new_native_passes=0)

def build(root=ROOT):
    originals={}
    for label,rec in RECORDS.items():
        run,aid,size,sha,head,_,_=rec;directory=Path(DIRECTORY)/str(run)
        metadata(load(prior.read(root,directory/'actions.json')),rec);raw=prior.read(root,directory/'original.zip');need(identity(raw)==dict(size=size,sha256=sha),'retained gear bytes differ')
        files=(probe_archive if label=='probe' else display.archive)(raw)
        originals[label]=dict(run_id=run,artifact_id=aid,tested_head=head,path=str(directory/'original.zip'),size=size,sha256=sha,verification=verify(label,files))
    return dict(schema_version=1,status='STATIC_AND_REJECTED_ORIGINALS_RETAINED',candidate=display.CANDIDATE,originals=originals,new_emulator_runs=0,gear_to_battle_accepted=False,full_p05_acceptance=False,release_ready=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fetch',action='store_true');p.add_argument('--write',action='store_true');args=p.parse_args()
    if args.fetch:fetch()
    result=build()
    if args.write:(ROOT/RECEIPT).write_bytes(stable(result))
    else:need(prior.same(result,load(prior.read(ROOT,RECEIPT))),'gear original receipt differs')
    print(stable(dict(status=result['status'],originals=len(RECORDS),new_emulator_runs=0,release_ready=False)).decode(),end='')
if __name__=='__main__':main()
