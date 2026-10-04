#!/usr/bin/env python3
"""Save101のprivate copyで新MDX候補RAMの実UI lifetimeだけを検査。"""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
def need(v,message):
    if not v:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n")
BASE='587736739708b82178f2ada891cc837aea7c653a'
C='tools/mgba_pr16_dex_lifetime.c'
SELF='scripts/pr16_dex_lifetime.py'
WF='.github/workflows/pr16-dex-lifetime.yml'
CODE={C,SELF,WF,"tests/test_pr16_dex_lifetime.py"}
OUT=ROOT/'.local/pr16-dex-lifetime';ART=OUT/'evidence'
CASES=('bag','summary','pokedex','pc','box-name')

def guard():
    import pr16_story_live_probe as retained
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'
         and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'
         and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized single branch and attempt')
    p=retained.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole exact current draft HEAD')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only new fixture and focused test files')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'no prior pending run')
    for path,binding in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'accepted source unchanged '+path)

def validate(stdout,case):
    need(len(stdout)<100000,'bounded metadata output');rows=[json.loads(x)for x in stdout.decode().splitlines()]
    fixtures=[x for x in rows if 'fixture'in x];results=[x for x in rows if 'status'in x]
    need(len(fixtures)==len(results)==1 and fixtures[0]['case']==case,'one fixture and one terminal')
    r=results[0];need(r['status']=='PASS_UNSAVED_MDX_UI_LIFETIME_ONLY'and r['case']==case and r['whole_owner_bytes']==522
        and r['fixture_bytes']==522 and r['host_write_barriers']==7 and r['ordinary_saves']==0
        and r['runtime_wired']is False and r['rom_changed']is False and r['story_progress_accepted']is False,'exact limited lifetime result')
    need(r['fixture_calls']==int(case in ('pc','box-name')),'only declared PC entry fixture')
    screens=[x for x in rows if 'screen'in x];need(screens[0]['stage']=='loaded-field'and screens[-1]['stage']=='returned-field'and screens[-1]['lock']==0,'visible endpoints')
    required={'bag':'bag','summary':'summary-page2','pokedex':'pokedex','pc':'pc-storage','box-name':'box-name'}[case]
    need(any(x['stage']==required for x in screens),'UI target reached')
    for x in screens:
        path=OUT/case/x['screen'];raw=path.read_bytes();need(len(raw)==115215 and raw[:15]==b'P6\n240 160\n255\n'and identity(raw)['sha256']==x['sha256'],'full native renderer image')
        need(any(raw[i:i+3]!=raw[15:18]for i in range(18,len(raw),3)),'nonblank actual screen')
    return r,rows

def main():
    import pr16_story_live_probe as retained
    import pr16_story_route_probe as publication
    guard();need(not OUT.exists(),'one fresh execution');ART.mkdir(parents=True);results=[];processes=0
    try:
        retained.OUT=OUT;runtime,private,seed=retained.restore()
        exe=OUT/'runner';cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-I'+str(runtime/'include'),str(ROOT/C),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120);(ART/'compile.stdout.txt').write_bytes(p.stdout);(ART/'compile.stderr.txt').write_bytes(p.stderr)
        write(ART/'compile.json',dict(returncode=p.returncode,source=identity((ROOT/C).read_bytes()),host_compiles=1,arm_compiles=0))
        need(p.returncode==0 and not p.stdout and not p.stderr,'strict new lifetime C compile')
        for case in CASES:
            folder=OUT/case;folder.mkdir();save=folder/'private.srm';save.write_bytes(seed)
            invocation=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe),str(private/'candidate.gba'),str(save),case]
            processes+=1;p=subprocess.run(invocation,cwd=folder,capture_output=True,timeout=180)
            target=ART/case;target.mkdir();(target/'stdout.txt').write_bytes(p.stdout);(target/'stderr.txt').write_bytes(p.stderr)
            write(target/'execution.json',dict(returncode=p.returncode,save_unchanged=save.read_bytes()==seed,new_native_processes=1,source_head=os.environ['GITHUB_SHA']))
            for screen in folder.glob('screen-*.ppm'):(target/screen.name).write_bytes(screen.read_bytes())
            need(save.read_bytes()==seed,'all Save101 plus RTC bytes unchanged')
            need(p.returncode==0 and not p.stderr,'new lifetime case '+case)
            result,rows=validate(p.stdout,case);write(target/'result.json',result);results.append(result)
        write(ART/'measurement.json',dict(status='PASS_FIVE_UI_UNSAVED_MDX_LIFETIME_ONLY',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),results=results,native_processes=processes,arm_compiles=0,rom_changed=False,formal_save_changed=False,runtime_wired=False,save_abi_accepted=False,consumer_repair_accepted=False,story_milestone_reached=False))
    except Exception as e:
        write(ART/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),completed_new_cases=results,native_processes=processes,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        write(ART/'publication-policy.json',dict(scope='NEW_UI_LIFETIME_ONLY',rom_runtime_inputsave_runner_excluded=True,hidden_symlink_unknown_extensions_rejected=True))
        publication.export_evidence(ART,ROOT/'public-dex-lifetime')
if __name__=='__main__':main()
