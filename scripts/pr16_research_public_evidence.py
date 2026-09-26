#!/usr/bin/env python3
"""原本を変更せず、機械固有compiler引数だけ公開用写像へ置換する。"""
from __future__ import annotations
import io
import json
import zipfile
from pr16_research_save_impact import need, identity, load

FAILED_SOURCE='e7136f0658309862328871730f6e3ff10962faab'
FAILED_RUN=36230558876
FAILED_ARTIFACT=10902343421
FAILED_BINDING={'size':9179,'sha256':'42145d4436fbd698da0cec44eb83a7770617494de6d446e042545f90dc423058'}
UNIT_BINDING={'size':7942,'sha256':'6043e79deeae4343a4b26cc8fa55f59eec0671aa7f4e5c981ec147d90f101f2e'}
MEMBERS={'checkpoint.json','new-unit.txt','index-guard.txt','paths.txt','receipt.json','resume-check.txt','task-graph.txt'}


def encode(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def project(files, expected_redactions, check_private):
    """Validation consumes raw originals first. This function only publishes them."""
    need('compile.json' in files and 'compile.public.json' not in files and 'publication.json' not in files,'closed publication names')
    need(type(expected_redactions) is int and expected_redactions in (3,4),'known compilation shape')
    comp=load(files['compile.json'])
    need(set(comp)=={'command','compiler','executable','returncode','source_bindings'},'closed compile receipt schema')
    need(type(comp['command']) is list and comp['command'] and all(type(x) is str for x in comp['command']),'compiler argument types')
    original=files['compile.json']; public_comp=dict(comp);command=[];redactions=[]
    for index,arg in enumerate(comp['command']):
        prefix=arg[:2] if arg.startswith(('-I/','-L/')) else ''
        path=arg[len(prefix):]
        if path.startswith('/'):
            token=prefix+'<artifact-absolute-argument-'+str(index)+'>'
            redactions.append({'argument_index':index,'original_utf8':identity(arg.encode()),'replacement':token})
            command.append(token)
        else:command.append(arg)
    need(len(redactions)==expected_redactions,'exact absolute argument count')
    public_comp['command']=command
    projection={'schema_version':1,'kind':'PUBLIC_PROJECTION_NOT_ORIGINAL','original_member':'compile.json',
                'original_binding':identity(original),'redactions':redactions,'projection':public_comp,
                'policy':'Only absolute compiler arguments are replaced; original bytes remain in the pinned Actions artifact.'}
    result={name:raw for name,raw in files.items() if name!='compile.json'}
    result['compile.public.json']=encode(projection)
    manifest={}
    for name,raw in files.items():
        published='compile.public.json' if name=='compile.json' else name
        manifest[name]={'original_binding':identity(raw),'published_name':published,'published_binding':identity(result[published]),'transformation':'absolute-compiler-argument-projection' if name=='compile.json' else 'identity'}
    result['publication.json']=encode({'schema_version':1,'originals_location':'Pinned Actions artifact; not all originals are copied verbatim to Git.','members':manifest})
    for name,raw in result.items():
        raw.decode('utf-8');need(b'\0' not in raw and not check_private(raw),'unsafe public text: '+name)
    return result


def verify_failed_run(run,jobs,workflow):
    need(run['id']==FAILED_RUN and run['head_sha']==FAILED_SOURCE and run['head_branch']=='codex/modernization-followup-20260908','failed publication source')
    need(run['repository']['full_name']=='dekaazarashi1111-web/pokemon-vega-modern' and run['event']=='push' and run['path']==workflow,'failed publication workflow')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['run_attempt']==1,'guard failure remains failure')
    need(jobs['total_count']==len(jobs['jobs'])==1,'one publication job')
    job=jobs['jobs'][0]
    need(job['id']==108372794363 and job['run_id']==FAILED_RUN and job['head_sha']==FAILED_SOURCE and job['name']=='record' and job['status']=='completed' and job['conclusion']=='failure','bound failed publication job')
    steps={s['number']:s for s in job['steps']}
    need(set(steps)=={1,2,3,4,5,6,7,14,15},'exact failed publication steps')
    for number,s in steps.items():need(s['status']=='completed' and s['conclusion']==('failure' if number==5 else 'skipped' if number==6 else 'success'),'only guard failed; commit skipped')
    need(steps[7]['name']=='Run actions/upload-artifact@v4','partial proof uploaded')


def reuse_unit(raw,read_source,protected):
    need(identity(raw)==FAILED_BINDING,'fixed failed publication artifact')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(set(z.namelist())==MEMBERS and len(z.infolist())==len(MEMBERS),'exact partial-proof archive')
        need(all(i.file_size<100000 and not i.is_dir() and i.external_attr>>28!=10 for i in z.infolist()),'bounded partial proof')
        receipt=load(z.read('receipt.json'));unit=z.read('new-unit.txt')
    need(receipt['source_head']==FAILED_SOURCE and receipt['run_id']==FAILED_RUN and receipt['new_unit_tests']==68,'original unit provenance')
    need(receipt['new_native_processes']==receipt['host_compiles']==receipt['arm_compiles']==0,'record-only source proof')
    need(identity(unit)==UNIT_BINDING and unit.count(b' ... ok\n')==68 and unit.endswith(b'\nOK\n'),'exact 68-test success transcript')
    need(protected and protected<=set(receipt['source_bindings']),'closed reuse dependency set')
    for name in protected:need(identity(read_source(name))==receipt['source_bindings'][name],'unchanged unit dependency: '+name)
    return unit,{'source_head':FAILED_SOURCE,'run_id':FAILED_RUN,'artifact_id':FAILED_ARTIFACT,'artifact_binding':FAILED_BINDING,
                 'unit_member':'new-unit.txt','unit_binding':UNIT_BINDING,'accepted_tests':68,'executed_again':False,
                 'unit_source_bindings':{name:receipt['source_bindings'][name] for name in sorted(protected)},
                 'run_conclusion':'failure','failure_stage':'final-index private guard; commit was skipped'}
