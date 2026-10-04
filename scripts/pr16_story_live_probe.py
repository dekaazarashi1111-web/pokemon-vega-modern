#!/usr/bin/env python3
"""Save101の未保存read-only観測器を検証。戦闘/施設到達の受入とは分離。"""
from __future__ import annotations
import hashlib,io,json,os,re,struct,subprocess,sys,zipfile,zlib
from pathlib import Path,PurePosixPath
sys.setrecursionlimit(max(sys.getrecursionlimit(),1500))
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_live_observer as m
from pr16_story_live_session import LiveSession
from pr16_story_after_maori import need,identity,write,validate_archive
BASE='1d82a2d9f47350ea8a6dd217e22c897e03a942e6'
OUT=ROOT/'.local/pr16-story-live-probe';ART=OUT/'artifact'
CODE={'scripts/pr16_story_live_observer.py','scripts/pr16_story_live_session.py','scripts/pr16_story_live_probe.py',
      'tools/mgba_pr16_story_live_observer.h','tests/test_pr16_story_live_observer.py',
      '.github/workflows/pr16-story-live-probe.yml','content/modernization/pr16_story_live_observer_unit.json',
      'docs/PR16_STORY_LIVE_OBSERVER_JA.md'}
SEED=dict(size=131088,sha256='814a8e31ce20d720a1f1bddc08caa9cdd3d86b5bbb874738b9cb859653552149')
RUNTIME=(10898620034,36218655601,102586759,'a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d')
SAVE101=(11303305200,37200922210,217263,'5b152b826e6ea90695dce99ba2744e1faa7958b4434da769e5f3a7a79f54e25b')
SAVE24=(11263343138,37093559410,17559812,'6a0cff0cd7a5d4118fd090bd8588c9076f1525d689b7e53802cbea9bbe9d49b0')
LAYOUT=[3876]+[3968]*3+[3776]+[3968]*8+[2000]

def api(path,binary=False):
    # 既存の安全なHTTPS redirect/GitHub認証transportを再利用。秘密の作成なし。
    import pr16_research_bag_actions as retained
    return retained.api(path,binary)

def archive(spec):
    number,run,size,digest=spec;meta=api('actions/artifacts/'+str(number))
    need(meta['id']==number and not meta['expired'] and meta['size_in_bytes']==size and meta['digest']=='sha256:'+digest and meta['workflow_run']['id']==run,'fixed artifact metadata')
    raw=api('actions/artifacts/'+str(number)+'/zip',True);need(identity(raw)==dict(size=size,sha256=digest),'archive identity')
    z=zipfile.ZipFile(io.BytesIO(raw));entries=z.infolist()
    need(0<len(entries)<1000 and len(entries)==len(set(z.namelist())) and sum(e.file_size for e in entries)<300000000,'archive bounds')
    for e in entries:
        p=PurePosixPath(e.filename);need(not p.is_absolute() and '..' not in p.parts and '\\' not in e.filename and e.external_attr>>28!=10 and not e.is_dir(),'safe regular member')
    return z,meta

def restore():
    private=OUT/'private';private.mkdir();runtime=OUT/'runtime';runtime.mkdir()
    z,meta=archive(RUNTIME)
    with z:
        need(len(z.infolist())==333 and sum(e.file_size for e in z.infolist())==240469427,'fixed full runtime/header archive')
        for e in z.infolist():
            p=runtime/e.filename;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(e))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    need(identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed mGBA library')
    z,_=archive(SAVE24)
    with z:
        manifest=json.loads(z.read('manifest.json'))
        need(set(z.namelist())==set(manifest)|{'manifest.json'},'candidate donor manifest')
        for n,b in manifest.items():need(identity(z.read(n))==b,'candidate donor member '+n)
        rom=z.read('candidate.gba')
    need(identity(rom)==dict(size=33554432,sha256=m.CANDIDATE),'unchanged existing ROM')
    z,_=archive(SAVE101)
    with z:
        manifest=json.loads(z.read('manifest.json'));need(len(manifest)==50 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save101 full evidence')
        for n,b in manifest.items():need(identity(z.read(n))==b,'Save101 member '+n)
        seed=z.read('story-fast.srm')
    need(identity(seed)==SEED,'only current accepted Save101');(private/'candidate.gba').write_bytes(rom);(private/'candidate.gba').chmod(0o444)
    return runtime,private,seed

def physical(seed):
    need(identity(seed)==SEED,'Save101 identity');table={}
    for pos in range(0xe000,0x1c000,0x1000):
        sid,check,signature,counter=struct.unpack_from('<HHII',seed,pos+0xff4)
        need(sid<14 and sid not in table and signature==0x08012025 and counter==101,'one complete generation')
        total=sum(struct.unpack_from('<'+'I'*(LAYOUT[sid]//4),seed,pos))&0xffffffff
        need(check==((total>>16)+(total&65535))&65535,'physical sector checksum');table[sid]=pos
    need(set(table)==set(range(14)),'complete sectors')
    party=seed[table[1]+56:table[1]+656]
    s1=b''.join(seed[table[sid]:table[sid]+LAYOUT[sid]] for sid in range(1,5))
    s2=seed[table[0]:table[0]+LAYOUT[0]]
    record=seed[table[13]+0x7d0:table[13]+0xde6];magic,version,size,crc,inverse=struct.unpack_from('<4sHHII',record)
    need((magic,version,size)==(b'S61E',1,0x606) and zlib.crc32(record[16:])==crc and inverse==crc^0xffffffff,'S61E physical checksum')
    return dict(party=party,flags=s1[0xee0:0x1000],variables=s1[0x1000:0x1200],expanded=record[16:],save2=s2)

def validate_probe(seed,observed):
    raw=physical(seed);o=observed['observation']
    need(o['map']==[3,24] and o['xy']==[53,13] and o['facing']==3 and o['callback2']==m.FIELD and o['lock']==0 and o['save_counter']==101 and o['party_count']==4 and o['rp']==0,'exact current location')
    need(observed['party']==raw['party'] and observed['flags']==raw['flags'] and observed['save1'][0x1000:0x1200]==raw['variables'],'live whole party/flags/variables vs physical Save101')
    need(observed['expanded_flags']+observed['expanded_vars']+observed['last_ball']+observed['coins']==raw['expanded'],'live all1536 expanded data plus ball/coins')
    need(m.resources(observed)==dict(hp=277,pp=[3,9,8,2]),'actual lead resources')
    need(observed['party_mons'][1]['hp']==354 and observed['party_mons'][1]['pp']==[10,20,15,10],'actual reserve resources')
    need(observed['party_mons'][0]['moves']==[337,89,280,332] and observed['variables'][0x21]==98 and observed['variables'][0x72]==3,'actual lead moves/walk/story')
    return dict(lead=observed['party_mons'][0],reserve=observed['party_mons'][1],field=o,
                physical_checksums=14,party_verified_bytes=600,legacy_flag_bytes=288,legacy_vars=256,expanded_verified_bytes=1542)

def guard():
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern' and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908' and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized one attempt')
    p=api('pulls/16');need(p['state']=='open' and p['draft'] and not p['merged'] and p['head']['sha']==os.environ['GITHUB_SHA'],'sole live draft head')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only declared new observer paths')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes())
    for path,binding in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'unchanged accepted source '+path)
    unit=json.loads((ROOT/'content/modernization/pr16_story_live_observer_unit.json').read_bytes())
    for path,binding in unit['source_bindings'].items():need(identity((ROOT/path).read_bytes())==binding,'local unit bytes '+path)
    need(unit['tests']==49 and unit['passed']==49 and unit['stderr'].count(' ... ok\n')==49 and '\nOK\n' in unit['stderr'],'49 new host test original, no rerun')

def main():
    guard();need(not OUT.exists(),'one execution only');ART.mkdir(parents=True);session=None
    try:
        runtime,private,seed=restore();generated=m.generate();source=OUT/'generated.c';source.write_bytes(generated)
        exe=OUT/'runner'
        cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        p=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=120);(ART/'compile.stdout.txt').write_bytes(p.stdout);(ART/'compile.stderr.txt').write_bytes(p.stderr)
        need(p.returncode==0 and not p.stdout and not p.stderr,'strict new observer compile')
        write(ART/'compile.json',dict(returncode=0,generated=identity(generated),executable=identity(exe.read_bytes()),new_compiles=1,rom_changes=0))
        session=LiveSession(runtime,private/'candidate.gba',exe,seed,ART/'probe')
        first=validate_probe(seed,session.live);session.step((0,120));second=validate_probe(seed,session.live);execution=session.quit()
        need(session.save.read_bytes()==seed,'all Save101/RTC bytes remain unchanged')
        report=dict(status='PASS_READ_ONLY_LIVE_OBSERVER_SAVE101_ONLY',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
                    first=first,second=second,execution=execution,host_tests_reused=49,new_host_test_reruns=0,native_processes=1,new_host_compiles=1,
                    field_inputs=0,ordinary_saves=0,accepted_case_reruns=0,new_game_replays=0,rom_changes=0,fixture_writes=0,
                    native_postbattle_adapter_accepted=False,native_battle_continuation_accepted=False,milestone_reached=False,full_story_accepted=False,release_ready=False)
        write(ART/'measurement.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as e:
        if session is not None and not session.closed and session.process.poll() is None:
            try:session.quit()
            except Exception:session.process.terminate()
        write(ART/'failure.json',dict(status='DIAGNOSTIC_STOP_NOT_MILESTONE',type=type(e).__name__,message=str(e),native_processes=int(session is not None),source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID'])))
        raise
    finally:
        # 原本Save/ROM/runtime/runnerを公開artifactへ入れない。
        for p in ART.rglob('*.srm'):
            need(identity(p.read_bytes())==SEED,'read-only probe unexpectedly changed save');p.unlink()
        need(all(p.suffix in {'.ppm','.txt','.json'} for p in ART.rglob('*') if p.is_file()),'public evidence text/screenshot only')
        write(ART/'manifest.json',{p.relative_to(ART).as_posix():identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file() and p.name!='manifest.json'})

if __name__=='__main__':main()
