#!/usr/bin/env python3
"""初回compile診断を保存し、変更のない43unit結果をexact artifactから再利用。"""
import io
import zipfile
RUN=36244548352
HEAD='84309cef21e30bc38b6accf5fa3eedc2db7d7cf4'
ARTIFACT=10906463533
ARCHIVE={'size':12053,'sha256':'f79d89bc8596a77d4cd25ee3d10e4375c8d72f6bde48da359a610ac18ea2222f'}
UNIT={'size':4593,'sha256':'63964254a97da797cb8d82997761ba5c74d00c2443893d310f5578478c8ef51a'}
FILES={'bag-recipe.json','compile.json','compile.stderr.txt','compile.stdout.txt','generation.json','inputs.json','invocation.json','save-recipe.json','unit.txt'}


def unit(d,root,test,model,canonical):
    need,identity=d.need,d.identity
    meta=d.inputs.api('actions/artifacts/'+str(ARTIFACT))
    need(meta['workflow_run']['id']==RUN and meta['workflow_run']['head_sha']==HEAD and not meta['expired'] and meta['size_in_bytes']==ARCHIVE['size'] and meta['digest']=='sha256:'+ARCHIVE['sha256'],'fixed initial diagnostic artifact')
    data=d.inputs.api('actions/artifacts/'+str(ARTIFACT)+'/zip',True)
    need(identity(data)==ARCHIVE,'initial artifact SHA and size')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        need(set(z.namelist())==FILES and len(z.infolist())==9 and sum(e.file_size for e in z.infolist())==44507,'bounded exact diagnostic members')
        raw={name:z.read(name) for name in FILES}
    for name,content in raw.items():
        content.decode('utf-8');need(b'\0' not in content,'diagnostic text only');(d.PUBLIC/('initial-'+name)).write_bytes(content)
    initial=d.read(d.PUBLIC/'initial-invocation.json')
    need(initial['source_head']==HEAD and initial['run_id']==RUN,'fixed diagnostic HEAD/run')
    for path in (test,model,canonical):
        need(identity((root/path).read_bytes())==initial['source_bindings'][path],'unchanged accepted unit source '+path)
    text=raw['unit.txt']
    need(identity(text)==UNIT and text.count(b' ... ok\n')==43 and b'Ran 43 tests' in text and text.endswith(b'\nOK\n'),'saved 43 PASS and canonical C test')
    comp=d.read(d.PUBLIC/'initial-compile.json')
    need(comp['returncode']==1 and comp['executable'] is None and b'[-Werror=sign-compare]' in raw['compile.stderr.txt'],'initial compile failed before any native execution')
    (d.PUBLIC/'unit.txt').write_bytes(text)
    d.put('unit-reuse.json',{'run_id':RUN,'source_head':HEAD,'artifact_id':ARTIFACT,'archive':ARCHIVE,'unit':UNIT,'new_unit_tests':43,'unit_processes_this_run':0,'canonical_unit_compiles_this_run':0,'initial_native_processes':0,'initial_host_compiles':2,'initial_runner_compile_failed':True,'source_bindings':{p:initial['source_bindings'][p] for p in (test,model,canonical)}})
    print('PASS_REUSED_43_UNIT_EXACT_SOURCE; native initial processes=0',flush=True)
