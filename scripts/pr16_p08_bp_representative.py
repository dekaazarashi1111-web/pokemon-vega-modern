#!/usr/bin/env python3
"""同一最終候補でBP敗北帰還・元party・通常Save/fresh Continueを代表1件。"""
from __future__ import annotations
import io
import os
from pathlib import Path
import re
import shlex
import struct
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_ring_recovery as e
need=e.need
TASK='USER-20260920-P08-BP'
BASE='1009359e8511776c6edf94c5cd0514d99baf749a'
SELF='scripts/pr16_p08_bp_representative.py'
HEADER='tools/mgba_pr16_p08_bp_lifecycle.h'
TEST='tests/test_pr16_p08_bp_representative.py'
WORKFLOW='.github/workflows/pr16-p08-bp.yml'
FILES=(SELF,HEADER,TEST,WORKFLOW,'scripts/pr16_p08_checkpoint.py')
REPORT='content/modernization/pr16_p08_bp_representative.json'
IMPACT='content/modernization/pr16_p08_candidate_impact.json'
OUT=ROOT/'.local/pr16-p08-bp'
TARGET=dict(size=33554432,sha256='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
LOSS_ENTRY=0x09FF59BD
CASE='p08-bp-loss-save-continue'
STATUS='PASS_P08_BP_RETURN_PARTY_SAVE_CONTINUE'
SCOPE='P08_BP_RETURN_PARTY'
EXTRA={'p08_saved_frame','p08_reloaded_frame','p08_save_counter_after','p08_loss_entry',
       'p08_party_bytes','p08_factory_bytes','p08_inventory_preserved','automatic_full_saves'}


def replace_once(text,before,after):
    need(text.count(before)==1,'source anchor differs: '+before[:80])
    return text.replace(before,after,1)


def adapt_controller(raw,header):
    text=raw.decode();header.decode()
    need(b'\0' not in header and b'\0' not in raw,'text source required')
    for before,after in [('factory-loss-return',CASE),('PASS_SCOPED_NATIVE_LOSS_RETURN_NOT_BP',STATUS),
                         ('PR16_P05_SCOPED_FACTORY_LOSS_RETURN',SCOPE)]:
        text=replace_once(text,before,after)
    text=replace_once(text,'int main(int argc,char **argv) {',header.decode()+'\nint main(int argc,char **argv) {')
    anchor='    struct mCore original=*c;a_guard(c);bp_open(c);bp_trial(c);sp_observe(c,"chooser-start");'
    text=replace_once(text,anchor,'    uint32_t p08_inventory[G_ITEMS];g_inventory(c,p08_inventory);\n'
        '    p08_bp_dump("original_party",party,sizeof(party));\n'+anchor)
    anchor='    struct BPReturn finish=br_battle_return(c,party,counter);'
    text=replace_once(text,anchor,anchor+'\n    bp_require(c,finish.outcome==2U,"P08 requires native loss representative");\n'
        '    unsigned p08_loss_entry=read32(c,0x0807FC5CU);\n'
        '    struct P08BPLifecycle p08=p08_bp_lifecycle(&c,&original,argv[1],argv[2],party,p08_inventory,counter);')
    text=replace_once(text,'\\"manual_saves\\":0,\\"fresh_cores\\":1,','\\"manual_saves\\":1,\\"fresh_cores\\":2,')
    anchor='    printf("\\"bp_earned\\":0,'
    addition='    printf("\\"p08_saved_frame\\":%u,\\"p08_reloaded_frame\\":%u,\\"p08_save_counter_after\\":%u,\\"p08_loss_entry\\":%u,\\"p08_party_bytes\\":600,\\"p08_factory_bytes\\":106,\\"p08_inventory_preserved\\":true,\\"automatic_full_saves\\":0,",p08.saved,p08.reloaded,p08.counter_after,p08_loss_entry);\n'
    return replace_once(text,anchor,addition+anchor).encode()


def byte_witness(stderr,row):
    values={}
    for line in stderr.splitlines():
        if not line.startswith(b'P08_BP_BYTES '):continue
        m=re.fullmatch(rb'P08_BP_BYTES name=([a-z_]+) frame=(\d+) size=(\d+) hex=([0-9a-f]+)',line)
        need(m is not None,'byte witness syntax')
        name=m[1].decode();need(name not in values,'duplicate byte witness')
        raw=bytes.fromhex(m[4].decode());need(len(raw)==int(m[3]),'byte witness size')
        values[name]=(int(m[2]),raw)
    need(set(values)=={'original_party','returned_party','returned_factory','reloaded_party','reloaded_factory'},'byte witness inventory')
    need(len(values['original_party'][1])==600 and any(values['original_party'][1]),'empty original party')
    need(values['original_party'][1]==values['returned_party'][1]==values['reloaded_party'][1],'party byte drift')
    need(len(values['returned_factory'][1])==106 and values['returned_factory'][1]==values['reloaded_factory'][1],'Factory prefix drift')
    need(values['original_party'][0]<row['selected_frame'] and values['returned_party'][0]==row['facility_return_frame']
         and values['returned_factory'][0]==row['facility_return_frame']
         and values['reloaded_party'][0]==values['reloaded_factory'][0]==row['p08_reloaded_frame'],'byte witness ordering')
    return {k:e.identity(v[1]) for k,v in values.items()}


def validate(raw,stderr,process):
    need(type(process['returncode']) is int and process['returncode']==0 and process['timed_out'] is False
         and process['spawn_error'] is None,'native process not successful')
    row=e.strict(raw)
    need(row['status']==STATUS and row['scope']==SCOPE and row['case']==CASE
         and row['candidate_sha256']==TARGET['sha256'],'representative identity')
    import pr16_bp_battle_progress as first
    import pr16_bp_battle_return as returned
    import pr16_bp_selection_native as launch
    need(EXTRA<=set(row),'lifecycle absent')
    parent={k:v for k,v in row.items() if k not in EXTRA|returned.EXTRA}
    parent.update(status=first.STATUS,scope=first.SCOPE,case=first.CASE,total_frames=row['action_return_frame'],manual_saves=0,fresh_cores=1)
    old_sha=launch.SHA
    try:
        launch.SHA=TARGET['sha256'];first.validate(e.stable(parent),stderr,0)
    finally:launch.SHA=old_sha
    integers=(returned.EXTRA-{'native_afterbattle_observed'}) | (EXTRA-{'p08_inventory_preserved'})
    need(all(type(row[k]) is int for k in integers),'integer schema')
    for k,want in dict(battle_outcome=2,final_party_count=1,final_marker=0,final_snapshot_valid=0,
        final_reward_pending=0,final_streak=0,final_script_pointer=0,final_callback2=0x08055E75,
        original_party_or_snapshot_bytes_verified=600,manual_saves=1,fresh_cores=2,p08_party_bytes=600,
        p08_factory_bytes=106,p08_save_counter_after=3,automatic_full_saves=0,p08_loss_entry=LOSS_ENTRY).items():
        need(type(row[k]) is int and row[k]==want,'result differs: '+k)
    need(row['native_afterbattle_observed'] is True and row['p08_inventory_preserved'] is True,'return/inventory false')
    need(row['return_start_frame']==row['action_return_frame']<row['outcome_frame']<=row['facility_return_frame']
         <row['p08_saved_frame']<row['p08_reloaded_frame']==row['total_frames']<=130000,'return/save frame order')
    need(1<=row['additional_turns']<=48 and 0<=row['forced_switches']<=2
         and 0<=row['additional_pp_events']<=row['additional_turns'],'native input bounds')
    dispatch=re.findall(rb'BP_RETURN label=transition frame=(\d+) cb2=09ff59bd ',stderr)
    need(len(dispatch)==1 and row['outcome_frame']<=int(dispatch[0])<row['facility_return_frame'],'new loss callback not observed')
    need(not re.search(rb'BP_RETURN [^\n]*cb2=08055f65',stderr),'unexpected WhiteOut')
    need(b'original core destroyed; new core boot and normal Continue\n' in stderr,'cold boot witness')
    final=('P08_BP_LIFECYCLE saved='+str(row['p08_saved_frame'])+' reloaded='+str(row['p08_reloaded_frame'])+
           ' counter_before=2 counter_after=3 party_bytes=600 factory_bytes=106\n').encode()
    need(stderr.count(final)==1,'lifecycle trace differs')
    byte_witness(stderr,row)
    return row


def originals(b):
    import pr16_bp_loss_return_evidence as old
    run=b.api('actions/runs/'+str(old.RUN));job=b.api('actions/jobs/'+str(old.JOB));art=b.api('actions/artifacts/'+str(old.ARTIFACT))
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']==old.HEAD,'source run differs')
    need(job['run_id']==old.RUN and job['status']=='completed' and job['conclusion']=='failure','source job differs')
    need(not art['expired'] and art['workflow_run']['id']==old.RUN and art['digest']=='sha256:'+old.ARCHIVE['sha256'],'source artifact differs')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(old.ARTIFACT)+'/zip'],cwd=ROOT)
    need(e.identity(raw)==old.ARCHIVE,'original archive bytes')
    receipt=old.verify_archive(raw,ROOT)
    members=old.zip_members(raw);prefix='pr16-bp-loss-return-native/'
    sources=old.zip_members(members[prefix+'generated-controller.zip'])
    folder=OUT/'original';folder.mkdir(parents=True,exist_ok=True)
    for name,data in sources.items():
        need(Path(name).name==name and Path(name).suffix in ('.c','.h'),'generated filename')
        need(e.identity(data)==receipt['original_generated'][name],'generated identity');(folder/name).write_bytes(data)
    return dict(run_id=old.RUN,job_id=old.JOB,artifact_id=old.ARTIFACT,archive=old.ARCHIVE,head=old.HEAD,
                original_conclusion='failure',sources=receipt['original_sources'],generated=receipt['original_generated'])


def checkpoint(value,phase):
    import pr16_p08_checkpoint as c
    good=value.get('native_verified') is True
    stop=('同一46487d98のBP代表で正規レンタル1敗→共有敗北callback→party600byte復元→通常Save/fresh Continueを検証。原本保存済み、画面と完了Actionsの別照合前。' if good else
          'P08 BP代表の限定runner/保存再開契約を記録。native未完段階は原本のfailuresと実process数から再開し、旧3勝/購入/Ring/30勝は再実行しない。')
    nxt=('このrunの完了Actions・原本・終端画面を照合してP08_BP_RETURN_PARTYだけ受入。次はP03共有Save/load代表へ。' if good else
         'このrunの最新Actionsを先に読む。未実行なら同じrunのnativeへ、失敗なら原本で停止段階だけ修復。旧BP3勝/支出とRing/30勝の独立再実行は禁止。')
    c.save(REPORT,value,FILES,OUT,phase,stop,'P08_BP_REVIEW' if good else 'P08_BP_REPRESENTATIVE',nxt,[*FILES,IMPACT])


def prepare():
    import pr16_p08_checkpoint as c
    b=c.b;b.OUT=OUT;head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted: read result instead')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed source delta')
    prior=b.api('actions/runs/35510095146')
    need(prior['status']=='completed' and prior['conclusion']=='success' and prior['head_sha']=='3a08d5dbed832a869161a7e5c842d96eebd58659','Ring recovery incomplete')
    need(b.load(e.REPORT)['representative_accepted'] is True,'Ring receipt missing')
    original=originals(b)
    _,_,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'bp-context-tests')
    need(b.exited(proc)==0,'new BP contracts failed')
    protected=[e.REPORT,IMPACT,'content/modernization/pr16_bp_chooser_checkpoint.json','content/modernization/pr16_circus_acceptance.json','config/active_play_baseline.json']
    value=dict(schema_version=1,task=TASK,regression_id=SCOPE,case=CASE,source_head=head,workflow_source_head=os.environ['GITHUB_SHA'],
        candidate=TARGET,original=original,source_bindings={p:e.identity((ROOT/p).read_bytes()) for p in FILES},
        protected_originals={p:e.identity((ROOT/p).read_bytes()) for p in protected},native_verified=False,
        representative_accepted=False,visual_review_completed=False,new_emulator_processes=0,host_compiles=0,fresh_cores=0,
        arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,rom_changes=0,release_ready=False,failures=[])
    (OUT/'native-result.json').write_bytes(e.stable(value));checkpoint(value,'START')


def native():
    import pr16_p08_checkpoint as c
    b=c.b;b.OUT=OUT;b.scope();value=b.load(REPORT)
    need(value['new_emulator_processes']==0 and value['recording_run']==int(os.environ['GITHUB_RUN_ID']),'duplicate native attempt')
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
Path('.local/pr16-p08-bp/work/candidate.gba').write_bytes(raw)
"""
        _,_,proc=b.capture([sys.executable,'-c',code],'materialize');need(b.exited(proc)==0,'materialization failed')
        candidate=work/'candidate.gba';raw=candidate.read_bytes()
        need(e.identity(raw)==TARGET and struct.unpack_from('<I',raw,0x7fc5c)[0]==LOSS_ENTRY,'target/loss hook drift')
        value['loss_entry']=LOSS_ENTRY
        generated={}
        for name,expected in value['original']['generated'].items():
            data=(OUT/'original'/name).read_bytes();need(e.identity(data)==expected,'saved source drift')
            if name=='controller.c':data=adapt_controller(data,(ROOT/HEADER).read_bytes())
            if name=='pr16_gear_capture_helpers.c':
                old='fcda15075a586d59f4f9da5f7f55a294765f826ab1453a576e74192df822d879'
                data=replace_once(data.decode(),'#define N_SHA "'+old+'"','#define N_SHA "'+TARGET['sha256']+'"').encode()
            (work/name).write_bytes(data);generated[name]=e.identity(data)
        value['generated']=generated
        exe=work/'runner';dep=work/'deps.d'
        _,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),
            '-MMD','-MF',str(dep),str(work/'controller.c'),'-lmgba','-o',str(exe)],'compile')
        need(b.exited(proc)==0 and not err,'host compile failed');value['host_compiles']=1
        bindings={}
        for text in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(text);p=p if p.is_absolute() else ROOT/p;p=p.resolve()
            if p.parent==work:need(p.name in generated and e.identity(p.read_bytes())==generated[p.name],'unbound generated')
            else:
                name=p.relative_to(ROOT).as_posix();old=subprocess.check_output(['git','show',value['original']['head']+':'+name],cwd=ROOT)
                need(p.read_bytes()==old,'transitive source drift: '+name);bindings[name]=e.identity(old)
        value['transitive_compiled_sources']=bindings
        seed=(ROOT/b.SEED).read_bytes();need(e.identity(seed)['sha256']==b.SEED_SHA,'seed drift')
        scratch=work/'private.srm';scratch.write_bytes(seed);shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1;(OUT/'native-result.json').write_bytes(e.stable(value))
        stdout,stderr,proc=b.capture([str(exe),str(candidate),str(scratch),TARGET['sha256'],b.SEED_SHA,CASE,str(shots/CASE)],CASE,600)
        value['process']=proc;row=validate(stdout,stderr,proc)
        need(e.identity(candidate.read_bytes())==TARGET and (ROOT/b.SEED).read_bytes()==seed,'input changed')
        for path,expected in value['protected_originals'].items():need(e.identity((ROOT/path).read_bytes())==expected,'accepted original changed')
        value.update(native_verified=True,native_result=row,byte_witnesses=byte_witness(stderr,row),fresh_cores=row['fresh_cores'])
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
    elif sys.argv[1]=='pack':
        import pr16_p08_checkpoint as c
        c.pack(OUT,FILES)
    elif sys.argv[1]=='result':sys.exit(0 if e.strict((OUT/'native-result.json').read_bytes())['native_verified'] else 1)
    else:raise ValueError('unknown command')
