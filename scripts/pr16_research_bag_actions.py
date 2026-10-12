#!/usr/bin/env python3
"""固定候補のspend/rankだけを採取。受入済みearn/野生・ARMは実行しない。"""
import hashlib, io, json, os, pathlib, subprocess, time, urllib.request, zipfile
import pr16_research_save_delegate as save
import pr16_research_bag_delegate as bag
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/pr16-research-bag';PUBLIC=OUT/'public'
WF='.github/workflows/pr16-research-bag-native-20260926.yml'
identity,need=bag.identity,bag.need
SPECS=[('runtime',10898620034,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d',333,240469427),('data',10898510128,17366330,'7d3de78d4e852583eb35551076021630c1343aa623e91fe1529d73f4cf1471ed',3,33685811)]
SOURCES={WF,'scripts/pr16_research_bag_actions.py','scripts/pr16_research_bag_delegate.py',bag.HARNESS,bag.SOURCE,
         'scripts/pr16_research_save_delegate.py',save.CONFIG,'overlays/research_economy_v1/research_economy_v1.h',
         'tools/mgba_qol_production_smoke.c','tools/mgba_battle_core_smoke.c','tools/mgba_ai_fixture_runner.c'}


def put(name,v):
    (PUBLIC/name).write_text(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        need(newurl.startswith('https://'),'HTTPS redirect only')
        result=super().redirect_request(req,fp,code,msg,headers,newurl)
        if result is not None:result.remove_header('Authorization')
        return result


def api(path,binary=False):
    req=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/'+path,headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],'Accept':'application/vnd.github+json'})
    with urllib.request.build_opener(SafeRedirect()).open(req,timeout=120) as response:raw=response.read(150000001)
    need(len(raw)<=150000000,'bounded response')
    return raw if binary else json.loads(raw)


def main():
    PUBLIC.mkdir(parents=True)
    put('invocation.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'scope':'item transactions only; no accepted earn/wild reruns'})
    pr=api('pulls/16');need(pr['draft'] and not pr['merged'] and pr['state']=='open' and pr['head']['sha']==os.environ['GITHUB_SHA'],'exact open draft HEAD')
    artifacts=[]
    for name,number,size,digest,count,total in SPECS:
        meta=api('actions/artifacts/'+str(number));need(not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==36218655601,'fixed artifact metadata')
        raw=api('actions/artifacts/'+str(number)+'/zip',True);need(identity(raw)=={'size':size,'sha256':digest},'fixed artifact bytes')
        dest=OUT/name;dest.mkdir()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            need(len(z.infolist())==count and len(set(z.namelist()))==count and sum(i.file_size for i in z.infolist())==total,'exact archive member bounds')
            for entry in z.infolist():
                p=pathlib.PurePosixPath(entry.filename);need(not p.is_absolute() and '..' not in p.parts and '\\' not in entry.filename and entry.external_attr>>28!=10 and not entry.is_dir(),'safe regular archive member')
                f=dest/str(p);f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(z.read(entry))
        artifacts.append({'id':number,'name':meta['name'],'binding':identity(raw),'source_head':meta['workflow_run']['head_sha']})
    runtime=OUT/'runtime';data=OUT/'data'
    parent,r=save.apply((data/'candidate.gba').read_bytes());put('repair.json',r)
    candidate,r=bag.apply(parent);put('bag-repair.json',r);(data/'candidate.gba').write_bytes(candidate)
    generated=bag.item_runner((ROOT/bag.HARNESS).read_bytes());(PUBLIC/'generated-items.c').write_bytes(generated)
    seed=(data/'seed.srm').read_bytes();need(identity(seed)=={'size':131072,'sha256':'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb'},'fixed seed')
    need(identity((runtime/'lib/libmgba.so').read_bytes())=={'size':1968536,'sha256':'0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'},'fixed libmgba')
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    cp=json.loads((ROOT/'content/modernization/pr16_special_wild_ui_checkpoint.json').read_text())
    for path in SOURCES:
        if path.startswith('tools/') and path!=bag.HARNESS:need(identity((ROOT/path).read_bytes())==cp['source_bindings'][path],'unchanged helper '+path)
    bindings={p:identity((ROOT/p).read_bytes()) for p in SOURCES}
    need(identity((ROOT/bag.SOURCE).read_bytes())==bag.SOURCE_BEFORE,'canonical source correction not yet published')
    put('inputs.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'candidate':identity(candidate),'seed':identity(seed),'artifacts':artifacts,'source_bindings':bindings,'generated_harness':identity(generated),'canonical_source_after':identity(bag.correct_source((ROOT/bag.SOURCE).read_bytes()))})
    exe=OUT/'runner';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I'+str(runtime/'include'),str(PUBLIC/'generated-items.c'),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    comp=subprocess.run(cmd,capture_output=True,timeout=120)
    (PUBLIC/'compile.stdout.txt').write_bytes(comp.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(comp.stderr)
    put('compile.json',{'returncode':comp.returncode,'command':cmd,'compiler':subprocess.check_output(['cc','--version']).decode(),'source_bindings':bindings,'executable':identity(exe.read_bytes()) if exe.exists() else None})
    need(comp.returncode==0,'host compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for mode in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        p=subprocess.run(prefix+['--guard-check',mode],capture_output=True,timeout=10)
        (PUBLIC/('guard-'+mode+'.stdout.txt')).write_bytes(p.stdout);(PUBLIC/('guard-'+mode+'.stderr.txt')).write_bytes(p.stderr)
        guards[mode]={'returncode':p.returncode,'stdout':identity(p.stdout),'stderr':identity(p.stderr)}
        need(p.returncode==1 and not p.stdout and p.stderr==b'research-save-impact: host write after observation barrier\n','write barrier '+mode)
    put('guards.json',guards)
    cases={};failures={}
    for op in ('spend','rank'):
        for phase in range(5):
            key=op+'-'+str(phase);target=OUT/(key+'.srm');target.write_bytes(seed);started=time.monotonic()
            try:
                p=subprocess.run(prefix+[str(data/'candidate.gba'),str(target),op,str(phase)],capture_output=True,timeout=150)
                result={'returncode':p.returncode,'timeout':False};stdout,stderr=p.stdout,p.stderr
            except subprocess.TimeoutExpired as exc:
                result={'returncode':None,'timeout':True};stdout,stderr=exc.stdout or b'',exc.stderr or b''
            for suffix,raw in (('stdout.txt',stdout),('stderr.txt',stderr)):(PUBLIC/(key+'.'+suffix)).write_bytes(raw)
            result.update(elapsed_seconds=round(time.monotonic()-started,3),stdout=identity(stdout),stderr=identity(stderr),private_final_save=identity(target.read_bytes()),source_head=os.environ['GITHUB_SHA'],seed=identity(seed))
            cases[key]=result;put(key+'.process.json',result)
            if result['returncode']!=0 or result['timeout']:failures[key]=result
            print(key,json.dumps(result),flush=True)
    put('measurement.json',{'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'cases':cases,'failures':failures,'native_processes':10,'guard_processes':7,'host_compiles':1,'arm_compiles':0,'accepted_case_reruns':0,'normal_transaction_ui_accepted':False,'status':'MEASURED_NOT_YET_ACCEPTED'})
    need(identity((data/'seed.srm').read_bytes())==identity(seed) and identity((data/'candidate.gba').read_bytes())==bag.CANDIDATE,'read-only seed/candidate')
    need(not failures,'item native failures retained')


if __name__=='__main__':main()
