#!/usr/bin/env python3
"""Actual-address placement/ABI evidence only. No input Save, boot or game hooks."""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_placement as placement
need,identity=placement.need,placement.identity
BASE='348650ec75d14065742b960b75fb96f03b03104b'
CODE={'scripts/pr16_dex_placement.py','scripts/pr16_dex_placement_actions.py',
    'tests/test_pr16_dex_placement.py','tools/mgba_pr16_dex_placement.c',
    '.github/workflows/pr16-dex-placement.yml','docs/PR16_DEX_PLACEMENT_JA.md'}
OUT=ROOT/'.local/pr16-dex-placement';PUBLIC=ROOT/'public-dex-placement'
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def guard():
    import pr16_story_live_probe as transport
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','single authorized branch and attempt')
    pr=transport.api('pulls/16');need(pr['state']=='open' and pr['draft'] and not pr['merged'] and pr['head']['sha']==os.environ['GITHUB_SHA'],'sole current draft HEAD')
    need(set(git('diff','--name-only',BASE,'HEAD').decode().splitlines())==CODE,'exact new placement scope')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
    need(state['pending_runs']==[],'previous requested runs closed')
    for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'accepted source unchanged '+path)
    need(placement.rebuild_allocation(placement.allocation_source())==placement.allocation_source(),'canonical latest allocator source')
def run():
    import pr16_story_live_probe as transport
    need(not OUT.exists() and not PUBLIC.exists(),'fresh private execution and dedicated public directory');OUT.mkdir(parents=True);PUBLIC.mkdir()
    native_processes=0
    try:
        z,_=transport.archive(transport.SAVE24)
        with z:
            manifest=json.loads(z.read('manifest.json'));need(set(z.namelist())==set(manifest)|{'manifest.json'},'fixed donor archive members')
            for name,b in manifest.items():need(identity(z.read(name))==b,'fixed donor member '+name)
            before=z.read('candidate.gba')
        need(identity(before)==placement.lease.CANDIDATE,'exact current private ROM');private=OUT/'input.gba';private.write_bytes(before);private.chmod(0o444)
        env=dict(os.environ,VEGA_DEX_ROM_PATH=str(private))
        test=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_placement.py','-v'],cwd=ROOT,env=env,capture_output=True)
        need(test.returncode==0 and not test.stdout and test.stderr.count(b' ... ok\n')==26 and b'\nOK\n'in test.stderr,'26 new placement boundary tests')
        (PUBLIC/'host-tests.txt').write_bytes(test.stderr)
        payload,linked=placement.link(OUT/'link');after,placed=placement.place(before,payload,linked['symbols'])
        candidate=OUT/'placed-unwired.gba';candidate.write_bytes(after);candidate.chmod(0o444)
        need(private.read_bytes()==before,'immutable formal input ROM')
        package=subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()
        need(package=='0.10.2+dfsg-1.1build3','same accepted native package')
        need(identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'same accepted mGBA library')
        exe=OUT/'private-runner'
        cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT),str(ROOT/'tools/mgba_pr16_dex_placement.c'),*[str(ROOT/p)for p in placement.SOURCES],'-lmgba','-lm','-o',str(exe)]
        compiled=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        need(compiled.returncode==0 and not compiled.stdout and not compiled.stderr,'strict isolated linked ARM harness compile: '+compiled.stderr[-2000:])
        native_processes=1;tested=subprocess.run([str(exe),str(candidate)],cwd=OUT,capture_output=True,timeout=180)
        need(tested.returncode==0 and not tested.stderr,'linked ARM native ABI failed: '+tested.stderr.decode('utf-8')[-1000:])
        need(len(tested.stdout)<2000 and tested.stdout.count(b'\n')==1,'one bounded native receipt')
        native=json.loads(tested.stdout)
        need(native['status']=='PASS_PLACED_ARM_APIS_AND_VENEERS_ONLY' and native['api_calls']==24 and native['veneer_cases']==24 and native['functional_cases']==24 and native['native_processes']==1 and native['fresh_cores']==1,'all24 actual linked APIs and veneers')
        need(native['ewram_bytes_compared_per_case']==262144 and native['game_boots']==native['ordinary_saves']==0 and native['game_hooks_installed'] is False and native['story_progress_accepted'] is False,'strict isolated native acceptance boundary')
        need(candidate.read_bytes()==after and private.read_bytes()==before,'private ROM copies unchanged by native')
        write(PUBLIC/'native.json',native)
        sources=CODE|set(placement.SOURCES)|{placement.ALLOCATION,'tools/rom_allocator.py',placement.lease.PROOF,'scripts/pr16_dex_lease.py','overlays/dex_owner/dex_owner.h','overlays/dex_owner/dex_adapter.h','overlays/dex_owner/dex_compact_map.h','overlays/dex_owner/dex_compact_tables.h','overlays/dex_owner/dex_save_bridge.h'}
        write(PUBLIC/'placement.json',dict(schema_version=1,status='PASS_ACTUAL_ALLOCATOR_LINK_AND_ISOLATED_NATIVE_ABI_GAME_UNWIRED',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),host_tests=26,link=linked,placement=placed,native=native,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(sources)},candidate=identity(after),formal_candidate=identity(before),game_hooks_installed=False,formal_save_changed=False,input_saves_loaded=0,ordinary_saves=0,story_progress_accepted=False,public_binary_included=False))
        print(json.dumps(dict(status='PASS_ACTUAL_PLACEMENT_ONLY',payload_bytes=len(payload),reserved_suffix=linked['reserved_suffix_bytes'],new_native_processes=1,game_hooks_installed=False)))
    except Exception as e:
        write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=native_processes,formal_save_changed=False,input_saves_loaded=0))
        raise
def export():
    if not PUBLIC.exists():return
    need(PUBLIC.is_dir() and not PUBLIC.is_symlink(),'regular dedicated public directory')
    for path in PUBLIC.iterdir():
        need(path.is_file() and not path.is_symlink() and path.name in {'placement.json','native.json','host-tests.txt','failure.json'},'strict explicit text-only publication')
        raw=path.read_bytes();need(0<len(raw)<500000 and b'\0'not in raw and raw.endswith(b'\n'),'bounded newline-terminated UTF8 text');raw.decode('utf-8')
        if path.suffix=='.json':json.loads(raw)
    if (PUBLIC/'placement.json').exists():need(json.loads((PUBLIC/'placement.json').read_bytes())['public_binary_included'] is False,'no ROM binary in public output')
if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1]in ('guard','run','export'),'bounded execution mode');globals()[sys.argv[1]]()
