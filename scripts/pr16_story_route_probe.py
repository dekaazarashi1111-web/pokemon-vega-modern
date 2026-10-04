#!/usr/bin/env python3
"""New-route observation boundary. Unsupported events stop without saving."""
from __future__ import annotations
import json,os,shutil,subprocess,sys
from pathlib import Path
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_probe as retained
import pr16_story_route_session as reader
import pr16_story_route_owners as owners
import pr16_story_clock as clock
import pr16_story_battle_adapter as battle
from pr16_story_after_maori import need,identity,write
from pr16_story_milestones import DiagnosticStop
BASE='635fe8fab84d13f3dc9ad32dc50129436203d0f7'
OUT=ROOT/'.local/pr16-story-route-adapter';ART=OUT/'artifact'
CODE={'tests/test_pr16_story_publication.py','content/modernization/pr16_story_publication_unit.json','scripts/pr16_story_battle_adapter.py','tests/test_pr16_story_battle_adapter.py','content/modernization/pr16_story_battle_unit.json','scripts/pr16_story_clock.py','scripts/pr16_story_route_session.py','scripts/pr16_story_route_owners.py','scripts/pr16_story_route_probe.py',
      'tools/mgba_pr16_story_route_observer.h','tests/test_pr16_story_clock.py','content/modernization/pr16_story_route_owners.json',
      'content/modernization/pr16_story_clock_unit.json','docs/PR16_STORY_ROUTE_ADAPTER_JA.md','.github/workflows/pr16-story-route-adapter.yml'}

def guard():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized new one-attempt route probe')
    p=retained.api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft head')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only declared adapter paths')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
    for p,b in state['source_bindings'].items():need(identity((ROOT/p).read_bytes())==b,'frozen accepted source '+p)
    unit=json.loads((ROOT/'content/modernization/pr16_story_clock_unit.json').read_bytes())
    for path,binding in unit['source_bindings'].items():
        original=subprocess.check_output(['git','show','da0624bc098904c785a346f5531cf9847e6b0aa0:'+path],cwd=ROOT)
        need(identity(original)==binding,'47-test original exact bytes '+path)
    for path in ('scripts/pr16_story_clock.py','scripts/pr16_story_route_session.py','tests/test_pr16_story_clock.py','tools/mgba_pr16_story_route_observer.h'):
        need(identity((ROOT/path).read_bytes())==unit['source_bindings'][path],'unchanged47-test dependency '+path)
    current=json.loads((ROOT/'content/modernization/pr16_story_battle_unit.json').read_bytes())
    need(current['tests']==current['passed']==29 and current['stderr'].count(' ... ok\n')==29 and '\nOK\n'in current['stderr'],'29 new battle host tests')
    for path,binding in current['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'new battle unit exact bytes '+path)
    public=json.loads((ROOT/'content/modernization/pr16_story_publication_unit.json').read_bytes())
    need(public['tests']==public['passed']==4 and public['stderr'].count(' ... ok\n')==4,'four explicit publication tests')
    for path,binding in public['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'publication exact bytes '+path)
    need(unit['tests']==47 and unit['passed']==47 and unit['stderr'].count(' ... ok\n')==47 and '\nOK\n'in unit['stderr'],'new47 host test original no rerun')

def direction(a,b):
    need(a[:2]==b[:2],'connection needs separate live owner')
    return {(1,0):16,(-1,0):32,(0,-1):64,(0,1):128}[(b[2]-a[2],b[3]-a[3])]

def walk(session,route):
    rows=[]
    for index,(before,target)in enumerate(zip(route,route[1:])):
        if before[:2]!=target[:2]:raise DiagnosticStop('connection_adapter_pending',dict(index=index,target=target))
        need(session.last['map']+session.last['xy']==before,'current exact route tile')
        for attempt in range(3):
            prior=session.live;o=session.step((direction(before,target),8),(0,48))
            if o['callback2']!=0x08055E75 or o['lock']!=0:
                if index==39 and target==[3,24,32,10]:
                    evidence=clock.walking_evidence(prior,session.live,target[2:],observed_transition=True)
                    rows.append(dict(index=index,attempt=attempt,observation=o['observe'],**evidence));write(ART/'walking-ledger.json',rows)
                    # Previously observed closed grass transition: no A, B or direction.
                    transition=session.live;entry=session.step((0,600))
                    need(entry['map']==[3,24] and entry['xy']==[32,10] and entry['save_counter']==101 and entry['flash_sha256']==o['flash_sha256'],'bounded entry preserves region/save')
                    entry_owner=battle.entry_evidence(transition,session.live);write(ART/'battle-entry.json',entry_owner)
                    row=battle.play(session);write(ART/'battle-ledger.json',[row])
                    break
                raise DiagnosticStop('new_route_event_observation',dict(index=index,target=target,observation=o,live_ui=session.live['ui'],trainer=session.live['route']['trainer_id'],no_event_input_sent=True))
            evidence=clock.walking_evidence(prior,session.live,target[2:]);rows.append(dict(index=index,attempt=attempt,observation=o['observe'],**evidence))
            write(ART/'walking-ledger.json',rows)
            if o['xy']==target[2:]:break
        else:raise DiagnosticStop('unpassed_route_tile',dict(index=index,target=target))
    raise DiagnosticStop('facility_adapter_pending')

def export_evidence(source,destination):
    """Prevalidate an extension/structure allowlist before copying any public file."""
    source,destination=Path(source),Path(destination);selected=[]
    need(not destination.exists() and source.is_dir() and not source.is_symlink(),'fresh dedicated public directory')
    for path in sorted(source.rglob('*')):
        relative=path.relative_to(source)
        need(not path.is_symlink() and all(not x.startswith('.')for x in relative.parts),'no symlink or hidden evidence')
        if path.is_dir():continue
        need(path.is_file() and path.suffix in{'.json','.txt','.ppm'},'public text/screenshot allowlist')
        raw=path.read_bytes();need(len(raw)<=16000000,'bounded evidence size')
        if path.suffix=='.ppm':need(len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'native screenshot structure')
        else:
            text=raw.decode('utf-8');need('\0'not in text,'text evidence only')
            if path.suffix=='.json':json.loads(text)
        selected.append((relative,raw))
    need(bool(selected),'nonempty public evidence');destination.mkdir()
    for relative,raw in selected:
        out=destination/relative;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw)
        need(identity(out.read_bytes())==identity(raw),'exact public evidence copy')
    return [relative.as_posix()for relative,_ in selected]

def main():
    guard();need(not OUT.exists(),'no implicit retry');ART.mkdir(parents=True);session=None;execution=None
    try:
        retained.OUT=OUT;runtime,private,seed=retained.restore()
        actual=owners.inspect((private/'candidate.gba').read_bytes());need(actual==json.loads((ROOT/'content/modernization/pr16_story_route_owners.json').read_bytes()),'all active owner roots independently recomputed');write(ART/'owners.json',actual)
        generated=reader.generate();source=OUT/'generated.c';source.write_bytes(generated);exe=OUT/'runner'
        cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120);(ART/'compile.stdout.txt').write_bytes(p.stdout);(ART/'compile.stderr.txt').write_bytes(p.stderr)
        need(p.returncode==0 and not p.stdout and not p.stderr,'strict changed reader compile')
        write(ART/'compile.json',dict(returncode=0,generated=identity(generated),executable=identity(exe.read_bytes()),new_compiles=1,rom_changes=0))
        session=reader.RouteSession(runtime,private/'candidate.gba',exe,seed,ART/'route')
        retained.validate_probe(seed,session.live)
        route=json.loads((ROOT/'content/modernization/pr16_story_shiou_route_candidate.json').read_bytes())['route']
        walk(session,route)
    except DiagnosticStop as e:
        report=e.report;report.update(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),native_processes=int(session is not None),host_tests_reused=80,new_compiles=int(session is not None),accepted_case_reruns=0,ordinary_saves=0,native_multi_battle_accepted=False)
        write(ART/'diagnostic.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as e:
        write(ART/'failure.json',dict(status='NOT_ACCEPTED_FAILURE',type=type(e).__name__,message=str(e),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),native_processes=int(session is not None),milestone_reached=False));raise
    finally:
        if session is not None and not session.closed and session.process.poll()is None:execution=session.quit()
        if session is not None:need(identity(session.save.read_bytes())==retained.SEED,'diagnostic all Save101 bytes unchanged')
        if execution is not None:write(ART/'execution.json',execution)
        for p in ART.rglob('*.srm'):
            need(identity(p.read_bytes())==retained.SEED,'no unrequested save publication');p.unlink()
        need(all(p.suffix in{'.ppm','.json','.txt'}for p in ART.rglob('*')if p.is_file()),'text/screen evidence only')
        write(ART/'publication-policy.json',dict(status='TEXT_SCREENSHOT_ALLOWLIST',hidden_files=False,allowed_extensions=['.json','.txt','.ppm'],rom_input_save_runtime_runner_credentials_excluded=True))
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes())for p in sorted(ART.rglob('*'))if p.is_file()and p.name!='manifest.json'})
        published=export_evidence(ART,ROOT/'public-story-route-evidence');print(json.dumps(dict(public_evidence_files=len(published),hidden_files=False)))
if __name__=='__main__':main()
