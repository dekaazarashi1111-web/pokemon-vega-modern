#!/usr/bin/env python3
"""P08共有Save/load: わざメモリーの満杯時置換1件だけを同一候補で検証する。"""
from __future__ import annotations
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_checkpoint as cp
import pr16_p08_ring_recovery as e
import pr16_integrated_native as old
need=e.need
TASK='USER-20260920-P08-MEMORY'
SELF='scripts/pr16_p08_memory_representative.py'
HEADER='tools/mgba_pr16_p08_memory_observer.h'
TEST='tests/test_pr16_p08_memory_representative.py'
WORKFLOW='.github/workflows/pr16-p08-memory.yml'
VECTOR='content/modernization/pr16_p08_memory_case.json'
FILES=(SELF,HEADER,TEST,WORKFLOW,VECTOR,'scripts/pr16_p08_bp_acceptance.py')
BASE='2c35c4b7f697e53f109b709e1f0085985ab45035'
REPORT='content/modernization/pr16_p08_memory_representative.json'
IMPACT='content/modernization/pr16_p08_candidate_impact.json'
OUT=ROOT/'.local/pr16-p08-memory'
TARGET=dict(size=33554432,sha256='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
CASE='taillow-memory-full'
RUN=34512326368
JOB=102989241995
HEAD='d49c3d721f3eac994a48d190e980dc34346f0942'
ARTIFACT=10166560990
ARCHIVE=dict(size=346718,sha256='33cbb261552483e67d2ade7bdc9846b463170b515a2d22acbe0412a97f8640f9')
PARENT_SHA='635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e'


def case():
    return e.strict((ROOT/VECTOR).read_bytes())


def replace(text,before,after):
    need(text.count(before)==1,'memory source anchor: '+before[:70]);return text.replace(before,after,1)


def adapt(raw,header):
    text=raw.decode();header.decode()
    need(b'\0' not in header and b'\0' not in raw,'text source')
    text=replace(text,'int main(int argc,char**argv) {',header.decode()+'\nint main(int argc,char**argv) {')
    text=replace(text,'    if(argc!=6)return 2;','    if(argc!=7)return 2;\n    p08_memory_prefix=argv[6];')
    text=replace(text,'    /* No provider calls after this point: fixed vectors -> native input -> compare. */',
        '    p08_memory_video=video;p08_memory_shot("fixture");\n'
        '    p08_memory_original_frame=c->runFrame;c->runFrame=p08_memory_frame;\n'
        '    /* Existing three barriers remain unchanged; observer only reads pixels. */')
    text=replace(text,'    unsigned char party[100],restored[100];r_read_party(c,party);',
        '    unsigned char party[100],restored[100];r_read_party(c,party);\n'
        '    p08_memory_bytes(c,"learned",party);p08_memory_shot("learned-field");')
    text=replace(text,'    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"save changed complete party mon");',
        '    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"save changed complete party mon");\n'
        '    p08_memory_bytes(c,"saved",restored);p08_memory_shot("normal-save");')
    text=replace(text,'    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"cold Continue changed complete party mon");',
        '    r_read_party(c,restored);a_require(!memcmp(party,restored,100),"cold Continue changed complete party mon");\n'
        '    p08_memory_bytes(c,"reloaded",restored);p08_memory_shot("fresh-continue");')
    return text.encode()


def validator(sha):
    api=old.validator();api.ROM_SHA=sha;return api


def bytes_proof(stderr):
    rows={}
    for line in stderr.splitlines():
        if not line.startswith(b'P08_MEMORY_BYTES '):continue
        m=re.fullmatch(rb'P08_MEMORY_BYTES label=(learned|saved|reloaded) counter=(\d+) size=100 hex=([0-9a-f]{200})',line)
        need(m is not None and m[1].decode() not in rows,'memory byte witness')
        rows[m[1].decode()]=(int(m[2]),bytes.fromhex(m[3].decode()))
    need(list(rows)==['learned','saved','reloaded'],'memory lifecycle order')
    before,after,last=(rows[n][0] for n in rows)
    need(before==2 and after==last==before+1,'native memory save counters')
    need(any(rows['learned'][1]) and rows['learned'][1]==rows['saved'][1]==rows['reloaded'][1],'party bytes changed')
    need(stderr.count(b'original core destroyed; new core normal Continue\n')==1,'fresh core witness')
    return dict(party=e.identity(rows['learned'][1]),save_counter_before=before,save_counter_after=last,
                identical_before_save_after_save_after_cold_continue=True)


def validate(stdout,stderr,proc):
    need(type(proc['returncode']) is int and proc['returncode']==0 and proc['timed_out'] is False
         and proc['spawn_error'] is None,'native memory process')
    row=validator(TARGET['sha256']).validate_result(stdout,case(),proc,stderr)
    bytes_proof(stderr);return row


def physical_case(raw):
    need(e.identity(raw)==TARGET,'memory candidate')
    tables=old.layer.source.RomTables(raw,old.layer.COUNT,selected_species={10})
    pool=[move for move,level in tables.level[10] if level<=13]
    pool+=old.layer.indexed(raw,old.layer.REMINDER_INDEX,old.layer.REMINDER_MOVES,10)
    table=old.u32(raw,0x1cc)-old.layer.BASE
    need(0<=table<=len(raw)-1063*12,'move table bound')
    actual=old.make_case((CASE,10,13,0,0,1,457),pool,raw[table+457*12+4])
    need(actual==case(),'physical oracle differs from accepted representative')
    return actual


def original(b):
    import pr16_completion_checkpoint as history
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='success','memory source run')
    need(job['run_id']==RUN and job['head_sha']==HEAD and job['status']=='completed' and job['conclusion']=='success'
         and all(s['conclusion']=='success' for s in job['steps']),'memory source job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'memory source artifact')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    need(e.identity(raw)==ARCHIVE,'memory archive bytes');members=history.archive(raw)
    prefix='acceptance/memory/';result=e.strict(members[prefix+'result.json'])
    need(result['status']=='PASS' and result['candidate']['sha256']==PARENT_SHA and result['new_processes']==10,'source scope')
    for path,meta in result['source_bindings'].items():need(e.identity((ROOT/path).read_bytes())==meta,'source drift: '+path)
    vectors=e.strict(members[prefix+'vectors.json'])['cases']
    need([x for x in vectors if x['name']==CASE]==[case()],'case not the accepted original')
    for guard in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        stem=prefix+'guard-'+guard;proc=e.strict(members[stem+'.process.json'])
        need(type(proc['returncode']) is int and proc['returncode']==1 and not proc['timed_out'] and proc['spawn_error'] is None
             and members[stem+'.stdout']==b'' and members[stem+'.stderr']==b'P03 archive: host write after observation barrier\n','original guard differs')
    proc=e.strict(members[prefix+CASE+'.process.json'])
    validator(PARENT_SHA).validate_result(members[prefix+CASE+'.stdout'],case(),proc,members[prefix+CASE+'.stderr'])
    driver=(ROOT/old.PARENT_C).read_text();anchor='c->setVideoBuffer(c,video,240);'
    need(driver.count(anchor)==2,'renderer count')
    driver=driver.replace(anchor,anchor+'c->reset(c);').encode()
    need(driver==members[prefix+'executed-driver.c'] and validator(PARENT_SHA).header(vectors).encode()==members[prefix+'executed-vectors.h'],'executed source derivation')
    (OUT/'original').mkdir(parents=True,exist_ok=True);(OUT/'original/driver.c').write_bytes(driver)
    return dict(run_id=RUN,job_id=JOB,head_sha=HEAD,artifact_id=ARTIFACT,archive=ARCHIVE,
        source_bindings=result['source_bindings'],case=case(),driver=e.identity(driver),
        accepted_case_outputs={k:e.envelope(members[prefix+CASE+'.'+k]) for k in ('stdout','stderr','process.json')},
        seven_guard_receipts_reused_without_processes=True,unchanged_cases_replayed=0)


def checkpoint(value,phase):
    good=value.get('native_verified') is True
    stop=('P08共有Save/load代表1件がnative成功。通常わざメモリー満杯置換→通常Save→fresh Continueと100byte party/PPを原本照合。別画面/Actions受入前。' if good else
          'P08共有Save/loadの代表1件だけを実装。原本と3書込防止区間を維持し、既存10/46ケースを独立再実行しない。')
    nxt=('完了Actionsと原本・画面を照合しP08_SHARED_SAVE_LOADだけ受入。残るCircus退出後通常戦闘へ。' if good else
         '最新Actionsとnative-resultの停止点を先に読む。原本に基づき未完区間だけ修復し、受入済みRing/BP/30勝は再実行しない。')
    cp.save(REPORT,value,FILES,OUT,phase,stop,'P08_MEMORY_REVIEW' if good else 'P08_SHARED_SAVE_LOAD',nxt,[*FILES,IMPACT])


def prepare():
    b=cp.b;b.OUT=OUT;head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed source delta')
    import pr16_p08_bp_acceptance as review
    head=review.accept(FILES);b.OUT=OUT
    sources=original(b)
    _,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'memory-tests')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'memory contracts failed')
    protected=[IMPACT,e.REPORT,'content/modernization/pr16_bp_chooser_checkpoint.json','content/modernization/pr16_circus_acceptance.json','config/active_play_baseline.json']
    value=dict(schema_version=1,task=TASK,regression_id='P08_SHARED_SAVE_LOAD',case=CASE,
        source_head=head,workflow_source_head=os.environ['GITHUB_SHA'],candidate=TARGET,original=sources,
        source_bindings={p:e.identity((ROOT/p).read_bytes()) for p in FILES},
        protected_originals={p:e.identity((ROOT/p).read_bytes()) for p in protected},
        native_verified=False,representative_accepted=False,visual_review_completed=False,
        new_emulator_processes=0,host_compiles=0,fresh_cores=0,arm_compiles=0,arm_links=0,
        accepted_standalone_replays=0,prefix_wins_reexecuted=0,rom_changes=0,release_ready=False,failures=[])
    (OUT/'native-result.json').write_bytes(e.stable(value));checkpoint(value,'START')


def native():
    b=cp.b;b.OUT=OUT;b.scope();value=b.load(REPORT)
    need(value['recording_run']==int(os.environ['GITHUB_RUN_ID']) and value['new_emulator_processes']==0,'duplicate attempt')
    work=OUT/'work';work.mkdir(parents=True,exist_ok=True)
    try:
        code="""from pathlib import Path
import sys
sys.path.insert(0,'scripts')
import pr16_p08_impact as m
sys.addaudithook(m.offline)
raw=m.saved.safe(m.ROOT,m.ANCHOR_PATH).read_bytes()
m.need(m.saved.identity(raw)==m.ANCHOR,'anchor differs')
for recipe in m.load_model(m.ROOT):
 m.need(m.saved.identity(raw)==recipe['parent'],'materialization parent')
 raw=m.saved.patch(raw,recipe['patches'])
 m.need(m.saved.identity(raw)==recipe['candidate'],'materialization candidate')
m.need(m.saved.identity(raw)==m.TARGET,'final input')
Path('.local/pr16-p08-memory/work/candidate.gba').write_bytes(raw)
"""
        _,_,proc=b.capture([sys.executable,'-c',code],'materialize');need(b.exited(proc)==0,'materialization')
        rom=work/'candidate.gba';raw=rom.read_bytes();value['physical_case']=physical_case(raw)
        api=validator(TARGET['sha256']);generated={}
        for path,dest,entry in [('tools/mgba_modernization_p03_fullslots_e2e.c','p03a_fullslots_embedded.c','old_fullslots_main'),
            ('tools/mgba_modernization_p03_learning_e2e.c','p03_learning_embedded.c','old_learning_main'),
            ('tools/mgba_modernization_p02_stage71_acceptance_smoke.c','p03_p02_embedded.c','old_p02_main')]:
            generated[dest]=api.previous.embed((ROOT/path).read_text(),entry).encode()
        archive=(ROOT/'tools/mgba_modernization_p03_archive_ui_e2e.c').read_text()
        generated['p03r_archive_embedded.c']=replace(archive,'int main(int argc,char**argv)','int old_archive_main(int argc,char**argv)').encode()
        generated['p03r_vectors.h']=api.header([case()]).encode()
        generated['runner.c']=adapt((OUT/'original/driver.c').read_bytes(),(ROOT/HEADER).read_bytes())
        for name,data in generated.items():(work/name).write_bytes(data)
        value['generated']={p:e.identity(v) for p,v in generated.items()}
        dep=work/'deps.d';exe=work/'runner'
        _,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),'-MMD','-MF',str(dep),str(work/'runner.c'),'-lmgba','-o',str(exe)],'compile')
        need(b.exited(proc)==0 and not err,'host compile');value['host_compiles']=1
        bindings={}
        for item in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(item);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==work:need(p.name in generated and p.read_bytes()==generated[p.name],'generated include')
            else:
                name=p.relative_to(ROOT).as_posix();raw_old=subprocess.check_output(['git','show',HEAD+':'+name],cwd=ROOT)
                need(raw_old==p.read_bytes(),'transitive compiled source changed: '+name);bindings[name]=e.identity(raw_old)
        value['transitive_compiled_sources']=bindings
        seed=(ROOT/api.SEED).read_bytes();need(e.identity(seed)['sha256']==api.SEED_SHA,'seed')
        save=work/'private.srm';save.write_bytes(seed);shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1;(OUT/'native-result.json').write_bytes(e.stable(value))
        stdout,stderr,proc=b.capture([str(exe),str(rom),str(save),TARGET['sha256'],api.SEED_SHA,'0',str(shots/CASE)],CASE,180)
        value['process']=proc;row=validate(stdout,stderr,proc)
        need(e.identity(rom.read_bytes())==TARGET and (ROOT/api.SEED).read_bytes()==seed,'input changed')
        for path,expected in value['protected_originals'].items():need(e.identity((ROOT/path).read_bytes())==expected,'protected original changed')
        value.update(native_verified=True,native_result=row,byte_witness=bytes_proof(stderr),fresh_cores=row['core_instances'])
    except Exception as error:
        value['failures'].append(dict(type=type(error).__name__,message=str(error)));raise
    finally:
        value['screens']={p.name:e.identity(p.read_bytes()) for p in sorted((OUT/'screens').glob('*.ppm'))}
        (OUT/'native-result.json').write_bytes(e.stable(value))


if __name__=='__main__':
    need(len(sys.argv)==2,'command required')
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='native':native()
    elif sys.argv[1]=='finish':checkpoint(e.strict((OUT/'native-result.json').read_bytes()),'FINISH')
    elif sys.argv[1]=='pack':cp.pack(OUT,FILES)
    elif sys.argv[1]=='result':sys.exit(0 if e.strict((OUT/'native-result.json').read_bytes())['native_verified'] else 1)
    else:raise ValueError('unknown command')
