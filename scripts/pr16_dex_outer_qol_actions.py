#!/usr/bin/env python3
"""外側QOL失敗の新しいisolated/通常UIだけ測定。旧native受入を再走しない。"""
from __future__ import annotations
import json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_outer_qol as f
import pr16_dex_start_failure_actions as prior
import pr16_dex_start_fault_ui as ui
import pr16_dex_gameplay as game
need,identity,write=prior.need,prior.identity,prior.write
BASE='517d45045d6030e22a3615d9bbb095f004b50c20'
HEADER='tools/mgba_pr16_dex_outer_qol_ui.h'
GUIDE='docs/PR16_DEX_OUTER_QOL_JA.md'
CODE={f.SOURCE,f.BINDINGS,'scripts/pr16_dex_outer_qol.py','scripts/pr16_dex_outer_qol_actions.py','tests/test_pr16_dex_outer_qol.py','tests/test_pr16_dex_outer_qol_ui.py','tools/mgba_pr16_dex_outer_qol.h',HEADER,GUIDE,'.github/workflows/pr16-dex-outer-qol.yml'}
OUT=ROOT/'.local/pr16-dex-outer-qol';PUBLIC=ROOT/'public-dex-outer-qol'
def validate_header(source):
    s=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    for bad in ('busWrite','rawWrite','writeRegister','si_call(','si_restore(','si_open(','loadState(','loadTemporarySave('):need(bad not in s,'no CPU/RAM fixture '+bad)
    need(s.count('cpu->memory.store8=oq_store8;')==1 and 'oq_target=31u*4096u+4095u'in s and 'FLASH_COMMAND_PROGRAM'in s and 'at==oq_target'in s and 'v^1u'in s,'one last-byte Flash fault')
    main=s.split('int main(int argc,char**argv)',1)[1];need(main.index('si_guard(c);')<main.index('st_keys(c,'),'barriers before first frame');return identity(s.encode())
def generate(candidate,cold=False):
    old=game.CANDIDATE
    try:game.CANDIDATE=candidate;source=game.generate().decode()
    finally:game.CANDIDATE=old
    header=(ROOT/HEADER).read_text();validate_header(header)
    if not cold:
        token='int main(int argc,char**argv){';need(source.count(token)==1,'one key-only parent main')
        return(source.replace(token,'int accepted_story_main_not_called(int argc,char**argv){')+'\n'+header).encode()
    helper=header[header.index('static void oq_ledger('):header.index('static void oq_view(')]
    marker='static struct mCore *st_open(';need(source.count(marker)==1,'one cold insertion')
    source=source.replace(marker,helper+'\n'+marker)
    marker='dx_observe(c,n,st_frames);st_screen(n);';need(source.count(marker)==1,'one cold ledger observation')
    return source.replace(marker,'dx_observe(c,n,st_frames);oq_ledger(c);st_screen(n);').encode()
def guard():
    import pr16_story_live_probe as t
    need(os.environ['GITHUB_REPOSITORY']=='dekaazarashi1111-web/pokemon-vega-modern'and os.environ['GITHUB_REF_NAME']=='codex/modernization-followup-20260908'and os.environ['GITHUB_RUN_ATTEMPT']=='1','authorized first run')
    p=t.api('pulls/16');need(p['state']=='open'and p['draft']and not p['merged']and p['head']['sha']==os.environ['GITHUB_SHA'],'sole latest draft HEAD')
    changed=set(subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines());need(changed==CODE,'only declared new outer sources')
    state=json.loads((ROOT/'content/modernization/pr16_native_supply_resume_20260913.json').read_bytes());need(state['pending_runs']==[],'prior record terminal')
    for path,b in state['source_bindings'].items():need(identity((ROOT/path).read_bytes())==b,'all accepted source retained '+path)
def reconstruct():
    prior.OUT=OUT/'parent';prior.OUT.mkdir();_,_,before,_,_=prior.reconstruct()
    need(identity(before)==f.checkpoint()['candidate'],'old candidate whole bytes reconstructed without native')
    payload,linked=f.link(OUT/'outer');after,placed=f.apply(before,payload,linked);path=OUT/'candidate.gba';path.write_bytes(after)
    return path,before,after,linked,placed

def validate_ui(raw,folder,candidate):
    rows=[json.loads(x)for x in raw.splitlines()]
    need(rows[0]==dict(begin='OUTER_QOL_LAST_BYTE_FAULT_AND_KEY_RETRY',candidate_sha256=candidate['sha256'],host_write_barriers=7,ram_fixture_writes=0,register_writes=0),'exact begin')
    end=rows[-1]
    need(end['end']=='PASS_OUTER_QOL_LAST_BYTE_FAULT_KEY_RETRY'and end['failed_counter']==102 and end['retry_counter']==103 and end['fault_physical_address']==131071 and 0<end['fault_writes']<=16 and end['ram_fixture_writes']==end['register_writes']==0 and end['all_extension_bytes_retained_after_fault']==20248 and end['sector31_payload_bytes_retained']==4080,'closed tail-fault end')
    need(end['host_write_barriers']==7 and not end['old_save_failed_entered']and end['source_bank_and_sectors28_30_retained']and end['committed_main_bank0_retained']and not end['all_modes_accepted'],'bounded preservation')
    stages=[r for r in rows if 'start_failure_stage'in r];ledgers=[r for r in rows if 'outer_qol_ledger'in r]
    need([r['start_failure_stage']for r in stages]==['before_fault','error_first_page','error_final_page','field_after_failure','field_after_retry'],'five stages')
    need([r['counter']for r in stages]==[101,102,102,102,103]and all(r['attempt']==255 for r in stages[1:4])and stages[-1]['attempt']==1,'already committed main never hidden')
    need(all(r['damaged_mask']==1<<31 for r in stages[1:4])and stages[-1]['damaged_mask']==0,'actual physical driver bit31 and cleared by next save')
    frame=inputs=screen=0;pending=0;saves=[]
    for r in rows[1:-1]:
        if 'input'in r:need(pending==0 and r['input']==inputs and r['frame']==frame and r['key']in(0,1,2,8,16,32,64,128)and 0<r['frames']<=600,'ordered input');frame+=r['frames'];inputs+=1
        elif 'start_failure_stage'in r:need(pending==0 and r['frame']==frame,'stage frame');pending=1
        elif 'outer_qol_ledger'in r:need(pending==1 and r['frame']==frame and r['size']==2048,'ledger frame');pending=2
        elif 'screen'in r:need(pending==2 and r['screen']==screen and r['frame']==frame,'screen frame');screen+=1;pending=0
        elif 'ordinary_save'in r:need(pending==0 and r==dict(ordinary_save=True,before=102,after=103,frame=frame),'one key-only retry');saves.append(r)
        else:raise ValueError('unknown trace row')
    need(pending==0 and len(saves)==1 and len(ledgers)==5 and screen==end['screens']==5 and inputs==end['inputs']and frame==end['frames'],'whole trace consumed')
    need(len({r['sha256']for r in ledgers})==1,'whole finalized QOL ledger retained across failure and retry')
    return dict(end=end,stages=stages,ledgers=ledgers,saves=saves,screens=ui.screens(rows,folder))
def cold(exe,candidate,data,counter,expected):
    name='cold-'+str(counter);folder=OUT/name;folder.mkdir();public=PUBLIC/name;public.mkdir();save=folder/'cold.srm';save.write_bytes(data)
    args=[str(exe),str(candidate),str(save),'continue-story',identity(data)['sha256']]
    result=subprocess.run(args,cwd=folder,input='quit\n',capture_output=True,text=True,timeout=180)
    (public/'stdout.txt').write_text(result.stdout);(public/'stderr.txt').write_text(result.stderr)
    for p in folder.glob('*.ppm'):shutil.copyfile(p,public/p.name)
    need(result.returncode==0 and not result.stderr,'cold rc='+str(result.returncode)+' '+result.stderr[-800:])
    rows=[json.loads(x)for x in result.stdout.splitlines()];end=rows[-1];obs=[r for r in rows if 'observe'in r];mdx=[r for r in rows if 'mdx'in r];ledger=[r for r in rows if 'outer_qol_ledger'in r]
    need(end['end']=='STORY_INPUT_CHECKPOINT'and end['host_write_barriers']==7 and end['guarded_host_writes']==end['fixture_calls']==end['warnings_errors']==0 and save.read_bytes()==data,'cold no writes full FlashRTC retained')
    need(len(obs)==len(mdx)==len(ledger)==1 and not any('ordinary_save'in r for r in rows),'one cold observation')
    o,d,q=obs[0],mdx[0],ledger[0]
    need(o['save_counter']==counter and o['map']==[3,24]and o['xy']==[53,13]and o['party_count']==4 and o['field']and o['lock']==0,'same main generation location')
    need(d['valid']and d['live_sha256']==identity(expected)['sha256']and d['physical_matches_current_generation']==1,'durable MDX')
    need(q['size']==2048 and q['sha256']==identity(data[31*4096+0x64:31*4096+0x864])['sha256'],'cold whole QOL ledger equals physical payload')
    return dict(counter=counter,input=identity(data),output=identity(save.read_bytes()),observation=o,mdx=d,qol=q,end=end,screens=ui.screens(rows,public))

def run():
    import pr16_story_live_probe as t
    need(not OUT.exists()and not PUBLIC.exists(),'fresh outer attempt');OUT.mkdir(parents=True);PUBLIC.mkdir();attempts=[]
    try:
        r=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_dex_outer_qol*.py','-v'],cwd=ROOT,capture_output=True)
        need(r.returncode==0 and not r.stdout and r.stderr.count(b' ... ok\n')==6,'six targeted suites');(PUBLIC/'host-tests.txt').write_bytes(r.stderr)
        candidate,before,after,linked,placed=reconstruct();ci=identity(after)
        write(PUBLIC/'build.json',dict(candidate=ci,parent_candidate=identity(before),link=linked,placement=placed))
        need(subprocess.check_output(['dpkg-query','-W','-f=${Version}','libmgba-dev'],text=True).strip()=='0.10.2+dfsg-1.1build3'and identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'fixed runtime')
        entries=OUT/'entries.h';entries.write_text(''.join('#define '+n+' '+hex(a)+'u\n'for n,a in f.b.lifecycle.checkpoint()['link']['exports'].items()))
        isolated=(ROOT/'tools/mgba_pr16_dex_save_failure.c').read_text().replace('int main(int argc,char**argv)','int accepted_failure_main_not_called(int argc,char**argv)')+'\n'+(ROOT/'tools/mgba_pr16_dex_outer_qol.h').read_text()
        exes={}
        for name,source in [('isolated',isolated.encode()),('fault',generate(ci)),('cold',generate(ci,True))]:
            src=OUT/(name+'.c');src.write_bytes(source);exe=OUT/name
            cmd=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(ROOT/'tools'),'-I'+str(ROOT),'-DSCHEDULER_ENTRIES="'+str(entries)+'"',str(src),str(ROOT/'overlays/dex_owner/dex_owner.c'),'-lmgba','-lm','-o',str(exe)]
            r=subprocess.run(cmd,capture_output=True,text=True);need(r.returncode==0 and not r.stdout and not r.stderr,'strict '+name+' compile '+r.stderr[-1800:]);exes[name]=exe
        def attempt(name):attempts.append(name);write(PUBLIC/'attempts.json',dict(native_processes=len(attempts),cases=attempts))
        attempt('isolated');r=subprocess.run([str(exes['isolated']),str(candidate)],cwd=OUT,capture_output=True,text=True,timeout=300)
        (PUBLIC/'isolated-stdout.txt').write_text(r.stdout);(PUBLIC/'isolated-stderr.txt').write_text(r.stderr)
        need(r.returncode==0 and not r.stderr,'isolated rc='+str(r.returncode)+' '+r.stderr[-1000:]);native=json.loads(r.stdout);need(native['status']=='PASS_ISOLATED_OUTER_QOL_RESULT_TAIL'and native['cases']==7680,'all7680 new result cases')
        z,_=t.archive(t.SAVE101)
        with z:seed=z.read('story-fast.srm')
        need(identity(seed)==t.SEED,'untouched formal101');expected=game.record(game.physical(seed,101)['legacy']);copy=OUT/'copy.srm';copy.write_bytes(seed);failed=OUT/'failed.srm';saved=OUT/'retry.srm';case=PUBLIC/'fault';case.mkdir();attempt('fault')
        with(case/'stdout.txt').open('wb')as out,(case/'stderr.txt').open('wb')as err:r=subprocess.run([str(exes['fault']),str(candidate),str(copy),str(failed),str(saved)],cwd=case,stdout=out,stderr=err,timeout=300)
        need(r.returncode==0 and not(case/'stderr.txt').read_bytes(),'fault rc='+str(r.returncode)+' '+(case/'stderr.txt').read_text()[-1200:]);trace=validate_ui((case/'stdout.txt').read_bytes(),case,ci)
        bad,good=failed.read_bytes(),saved.read_bytes();need(len(bad)==len(good)==131088 and bad[14*4096:31*4096]==seed[14*4096:31*4096]and bad[131072:]==good[131072:]==seed[131072:],'old source bank/aux28..30/RTC retained')
        for data,counter in [(bad,102),(good,103)]:
            p=game.physical(data,counter);need(p['mdx']==expected and p['party']==game.physical(seed,101)['party'],'both actual main generations contain same MDX and party')
        need(bad[31*4096:31*4096+0xFF0]==good[31*4096:31*4096+0xFF0]and good[31*4096+0xFF0:32*4096]==bytes(16),'all4080 payload bytes and recovered16byte padding')
        cs=[]
        for data,counter in [(bad,102),(good,103)]:attempt('cold-'+str(counter));cs.append(cold(exes['cold'],candidate,data,counter,expected))
        for k in ('party_sha256','map','xy','party_count'):need(cs[0]['observation'][k]==cs[1]['observation'][k],'cold retain '+k)
        need(cs[0]['mdx']['bag_sha256']==cs[1]['mdx']['bag_sha256']and cs[0]['qol']['sha256']==cs[1]['qol']['sha256']==trace['ledgers'][-1]['sha256'],'whole normalized Bag and QOL ledger cold retention')
        need(copy.read_bytes()==good and candidate.read_bytes()==after,'whole runtime outputs exact')
        write(PUBLIC/'measurement.json',dict(status='PASS_OUTER_QOL_RESULT_AND_LAST_BYTE_FAULT_RETRY_COLD',source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=ci,parent_candidate=identity(before),link=linked,placement=placed,isolated=native,trace=trace,cold=cs,failed_save=identity(bad),retried_save=identity(good),input_save=identity(seed),native_processes=len(attempts),host_suites=6,old_native_reruns=0,formal_rom_changed=False,formal_save_changed=False,all_save_modes_accepted=False,non_start_notifications_accepted=False,early_sector31_fault_accepted=False,sector31_atomicity_accepted=False,source_bindings={p:identity((ROOT/p).read_bytes())for p in sorted(CODE)}))
    except Exception as e:
        write(PUBLIC/'failure.json',dict(status='DIAGNOSTIC_NOT_ACCEPTED',type=type(e).__name__,message=str(e),native_processes=len(attempts),attempts=attempts));raise

def export():
    if not PUBLIC.exists():return
    need(PUBLIC.is_dir()and not PUBLIC.is_symlink(),'dedicated public directory')
    for p in PUBLIC.rglob('*'):
        rel=p.relative_to(PUBLIC);need(not p.is_symlink()and not any(v.startswith('.')for v in rel.parts),'no hidden/symlink')
        if p.is_dir():need(str(rel)in('fault','cold-102','cold-103'),'only known directories');continue
        need(p.is_file(),'regular files only')
        if len(rel.parts)==1:need(p.name in{'host-tests.txt','build.json','measurement.json','attempts.json','failure.json','isolated-stdout.txt','isolated-stderr.txt'},'known root files')
        else:need(len(rel.parts)==2 and rel.parts[0]in('fault','cold-102','cold-103')and(p.name in('stdout.txt','stderr.txt')or re.fullmatch(r'screen-000[0-4]\.ppm',p.name)),'known screenshots/text')
        raw=p.read_bytes()
        if p.suffix=='.ppm':need(len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'whole screenshot');continue
        need(len(raw)<2000000 and b'\0'not in raw and(not raw or raw.endswith(b'\n')),'bounded complete text');raw.decode('utf8')
        if p.suffix=='.json':json.loads(raw)
if __name__=='__main__':need(len(sys.argv)==2 and sys.argv[1]in('guard','run','export'),'closed actions');globals()[sys.argv[1]]()
