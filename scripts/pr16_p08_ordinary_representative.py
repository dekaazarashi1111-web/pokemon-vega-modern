#!/usr/bin/env python3
"""P08最後の代表: 真正Circus退出Save30から通常戦闘の自然callee。"""
from __future__ import annotations
import os
from pathlib import Path
import shlex
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_p08_checkpoint as cp
import pr16_p08_ring_recovery as e
import pr16_circus_suppression_contract as contract
import pr16_circus_getter_abi as cache
need=e.need
TASK='USER-20260920-P08-ORDINARY'
BASE='a36dcb9bc287c7dbf43efaf79ceb76a8d82f8858'
SELF='scripts/pr16_p08_ordinary_representative.py'
HEADER='tools/mgba_pr16_p08_ordinary_main.h'
OBSERVER='tools/mgba_pr16_p08_ordinary_observer.h'
TEST='tests/test_pr16_p08_ordinary_representative.py'
WORKFLOW='.github/workflows/pr16-p08-ordinary.yml'
FILES=(SELF,HEADER,OBSERVER,TEST,WORKFLOW,'scripts/pr16_p08_memory_acceptance.py')
REPORT='content/modernization/pr16_p08_ordinary_representative.json'
IMPACT='content/modernization/pr16_p08_candidate_impact.json'
CIRCUS='content/modernization/pr16_circus_acceptance.json'
PRIOR='content/modernization/pr16_circus_suppression_lifecycle.json'
GETTER='content/modernization/pr16_circus_getter_followup.json'
OUT=ROOT/'.local/pr16-p08-ordinary'
CACHE=ROOT/'.local/pr16-circus-suppression/resume'
TARGET=dict(size=33554432,sha256='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
CASE='circus-exit30-ordinary'
RUN=35504302893
JOB=106061386465
HEAD='cc5d6822266a9663b0e368c9cff2c94d2ede3435'
ARTIFACT=10603527226
ARCHIVE=dict(size=299507,sha256='39481869e73b6685b964d58c8a24143f90c6650ee7e2c444f14207c11c8865e0')
COMMON={'kind','frame','flags','types','host_writes','host_calls','pcs'}
PRED={'bank','raw_ability','result','return_pc'}
DISP={'name','root','delegate','expected_normal','preserve_r3','r3_before','r3_after'}
DYNAMIC={'predicate_returns','normal_dispatches','trace_frames','trace_instructions','walking_steps','continued_frame',
         'boundary_frame','encounter_frame','returned_frame','total_frames','species','ability','enemy_species','enemy_level','outcome'}


def expected():
    return dict(schema_version=1,status='PASS_P08_CIRCUS_POST_EXIT_ORDINARY',case=CASE,candidate_sha256=TARGET['sha256'],
        new_emulator_processes=1,fresh_cores=1,manual_saves=0,prefix_wins_reexecuted=0,host_write_barriers=7,
        host_state_injection=False,ordinary_battles=1,owner_bytes_verified=64,factory_bytes_verified=106,
        bp_before=90,bp_after=90,save_counter_before=3,save_counter_after=3,inventory_preserved=True,
        party_identity_preserved=True,warnings_errors=0,release_ready=False)


def calls_proof(values,routes):
    lookup={r['name']:r for r in routes};pred=[];dispatch=[]
    need(len(lookup)==29,'route inventory')
    for row in values:
        is_pred=row.get('kind')=='predicate';need(row.get('kind') in ('predicate','dispatch'),'unknown call kind')
        need(set(row)==COMMON|(PRED if is_pred else DISP),'ordinary call schema')
        integers=COMMON-{'kind','pcs'}|(PRED if is_pred else DISP-{'name','preserve_r3'})
        need(all(type(row[k]) is int for k in integers),'ordinary call integer types')
        need(row['flags']==row['host_writes']==row['host_calls']==0 and row['types']==0,'suppression or injected ordinary call')
        pcs=row['pcs'];need(type(pcs) is list and 2<=len(pcs)<=128
            and all(type(pc) is int and 0x08000000<=pc<0x0a000000 for pc in pcs),'ordinary PC chain')
        if is_pred:
            need(pcs[0]==0x090D7BB0 and pcs[-1]==row['return_pc'] and row['bank'] in (0,1)
                 and 0<row['raw_ability']<=1024 and row['result']==0,'ordinary suppression predicate')
            pred.append(row)
        else:
            need(row['name'] in lookup,'unknown dispatcher');r=lookup[row['name']]
            need(type(row['preserve_r3']) is bool and row['preserve_r3']==bool(r['preserve_r3'])
                 and row['root']==pcs[0]==r['root'] and pcs[-1]==row['delegate']==row['expected_normal']==r['normal'],
                 'not the actual normal dispatcher')
            need(r['target'] in pcs and (not row['preserve_r3'] or row['r3_before']==row['r3_after']),'dispatcher/4th argument')
            dispatch.append(row)
    need(1<=len(pred)<=8 and 1<=len(dispatch)<=40,'missing or excessive ordinary calls')
    return dict(predicate_returns=len(pred),normal_dispatches=len(dispatch),
                hook_names=sorted({x['name'] for x in dispatch}),natural_normal_calls_verified=True)


def adapt(files):
    result=dict(files);name='getter_suppression.h';old='int main(int argc,char **argv){'
    text=result[name].decode();need(text.count(old)==1,'ordinary source main anchor')
    result[name]=text.replace(old,'int p08_unused_circus_lifecycle_main(int argc,char **argv){',1).encode()
    result['controller.c']+=b'\n#include "mgba_pr16_p08_ordinary_main.h"\n'
    return result


def physical(raw,generated):
    need(e.identity(raw)==TARGET,'ordinary candidate')
    import pr16_capture_geometry as geometry
    import pr16_purchased_gear as gear
    from tools.t02.rom_inventory import RomImage
    town=geometry.geometry(raw,96,5);grass=geometry.geometry(raw,96,17)
    paths={'town':gear.path(town,[20,20],[23,0]),'grass':gear.path(grass,[11,39],[14,30])}
    entry=gear.probe.roots.map_entry(RomImage('P08 fixed candidate',raw),96,5)
    at=struct.unpack_from('<I',raw,entry['header']-0x08000000+12)[0]-0x08000000
    count,table=struct.unpack_from('<II',raw,at);need(0<count<=32,'connections bound')
    links=[struct.unpack_from('<IiBB',raw,table-0x08000000+12*i) for i in range(count)]
    need([x for x in links if x[0]==2]==[(2,12,96,17)],'physical north connection')
    need(any(p['start']==[14,30] and p['end']==[15,30] and p['behavior']==2 for p in grass['walkable_pairs']),'physical grass pair')
    # 受入済みdispatcherのliteral/stubを同じ最終candidateで照合。ROMは変更しない。
    cfg=cp.b.load('config/modernization_p05_stage77_suppression.json')
    prior_sha=contract.SHA
    try:
        contract.SHA=TARGET['sha256'];routes=contract.routes(raw,cfg)
    finally:contract.SHA=prior_sha
    need(contract.route_header(routes)==generated['ss_routes.h'],'physical route binding')
    header='/* Current-ROM collision/elevation/event-excluded physical path. */\n'
    for key,rows in paths.items():
        need(1<=len(rows)<=128,'physical path bound')
        header+='static const unsigned po_'+key+'_path[][2]={'+','.join('{%dU,%dU}'%tuple(x) for x in rows)+'};\n'
    return dict(paths=paths,routes=routes,connection=[2,12,96,17],geometry={
        'town':e.identity(e.stable(town)),'grass':e.identity(e.stable(grass))}),header.encode()


def validate(stdout,stderr,proc,oracle,original_event):
    need(type(proc['returncode']) is int and proc['returncode']==0 and proc['timed_out'] is False
         and proc['spawn_error'] is None and b'mGBA[' not in stderr,'ordinary native process')
    row=e.strict(stdout);fixed=expected();need(set(row)==set(fixed)|DYNAMIC,'ordinary result schema')
    for key,want in fixed.items():need(type(row[key]) is type(want) and row[key]==want,'ordinary result: '+key)
    need(all(type(row[k]) is int for k in DYNAMIC),'ordinary integer schema')
    need(0<row['continued_frame']<row['boundary_frame']<row['encounter_frame']<row['returned_frame']==row['total_frames']<=100000,'ordinary frame order')
    need(1<=row['trace_frames']<=600 and 0<row['trace_instructions']<1200000000
         and 1<=row['walking_steps']<=400 and row['species']==4 and 0<row['ability']<=1024
         and 1<=row['enemy_species']<=2048 and 1<=row['enemy_level']<=100 and row['outcome'] in (1,2,4),'ordinary battle bounds')
    calls=contract.rows(stderr,b'P08_ORDINARY_CALL ');proof=calls_proof(calls,oracle['routes'])
    need(proof['predicate_returns']==row['predicate_returns'] and proof['normal_dispatches']==row['normal_dispatches']
         and all(row['boundary_frame']<x['frame']<=row['returned_frame'] for x in calls),'ordinary call projection')
    need(not contract.rows(stderr,b'CIRCUS_SUPPRESSION_DRAW ') and not contract.rows(stderr,b'CIRCUS_GETTER_ABI '),'old facility work repeated')
    events=contract.rows(stderr,b'CIRCUS_CONTINUOUS ')
    need([x['label'] for x in events]==['p08-exit30','p08-town-boundary','p08-normal-action','p08-normal-return'],'ordinary event sequence')
    before=events[0]
    for key in ('party','owner','factory','bp','count','save_counter','pending','snapshot','marker','flags','newbs','types'):
        need(type(before[key]) is type(original_event[key]) and before[key]==original_event[key],'genuine exit state: '+key)
    for event,frame in zip(events,(row['continued_frame'],row['boundary_frame'],row['encounter_frame'],row['returned_frame'])):
        need(event['frame']==frame and event['owner']==before['owner'] and event['factory']==before['factory']
             and event['bp']==90 and event['save_counter']==3 and event['count']==1 and event['battle']==30
             and not any(event[k] for k in ('flags','pending','snapshot','marker')) and not event['types']&0x04000000,'ordinary leaked owner/ledger')
        need(bytes.fromhex(event['party'])[:8]==bytes.fromhex(before['party'])[:8],'original individual lost')
    need(events[2]['types']==0 and events[2]['newbs'] and events[-1]['newbs']==0,'ordinary allocation/return')
    need(events[-1]['outcome']==row['outcome'],'ordinary outcome projection')
    return row,dict(calls=proof,events=events)


def sources(b):
    run=b.api('actions/runs/'+str(RUN));job=b.api('actions/jobs/'+str(JOB));art=b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='success','Circus source run')
    need(job['run_id']==RUN and job['head_sha']==HEAD and job['conclusion']=='success','Circus source job')
    need(not art['expired'] and art['workflow_run']['id']==RUN and art['digest']=='sha256:'+ARCHIVE['sha256'],'Circus source artifact')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'],cwd=ROOT)
    members=e.archive_members(raw,ARCHIVE);v=e.strict(members['native-result.json']);current=b.load(PRIOR)
    need(v['candidate']==TARGET and v['native_verified'] is True and v['failures']==[],'Circus lifecycle evidence')
    for key in ('events','analysis','generated','cache','inherited'):need(v[key]==current[key],'Circus original projection')
    generated={}
    for name,meta in v['generated'].items():
        data=members['execution/generated/'+name];need(e.identity(data)==meta and Path(name).name==name,'fixed generated source')
        generated[name]=data
    need(len(generated)==19,'fixed generated closure')
    folder=OUT/'original';folder.mkdir(parents=True,exist_ok=True)
    for name,data in generated.items():(folder/name).write_bytes(data)
    need(b.load(CIRCUS)['physical_admission_accepted'] is True and b.load(CIRCUS)['suppression_accepted'] is True,'Circus accepted scope')
    return dict(run_id=RUN,job_id=JOB,head_sha=HEAD,artifact_id=ARTIFACT,archive=ARCHIVE,
        generated=v['generated'],cache=v['cache'],exit_event=v['events'][0],
        note_ja='現候補の施設退出cleanupは受入済み原本を継承。新規区間は旧候補由来の真正退出Save30を現候補でContinue後の通常戦闘だけ。')


def checkpoint(value,phase):
    good=value.get('native_verified') is True
    stop=('P08 Circus退出後の通常戦闘で自然predicate=falseと通常dispatcherを検証。真正Save30から1process、施設戦/30勝再実行0。完了Actionsと画面の受入前。' if good else
          '真正Save30から通常歩行/自然calleeだけの最終代表を記録。cache欠落時は30勝bootstrapせず停止。未達は原本failuresを読む。')
    nxt=('完了Actions・原本・画面を照合してP08_CIRCUS_POST_EXIT_ORDINARYを受入。四境界の候補移送と古い所有範囲CIテストを整合し配布ゲートを整理。' if good else
         '最新Actionsとnative-resultの最初の未達だけを修復。cache以外のSave注入/旧30勝/受入済み施設/Ring/BP/memory再実行は禁止。')
    cp.save(REPORT,value,FILES,OUT,phase,stop,'P08_ORDINARY_REVIEW' if good else 'P08_CIRCUS_POST_EXIT_ORDINARY',nxt,[*FILES,IMPACT,CIRCUS])


def prepare():
    b=cp.b;b.OUT=OUT;head=b.scope();b.resume.validate(ROOT);OUT.mkdir(parents=True,exist_ok=True)
    need(not (ROOT/REPORT).exists(),'already attempted')
    need(set(b.command('git','diff','--name-only',BASE,head).splitlines())==set(FILES),'unreviewed source delta')
    import pr16_p08_memory_acceptance as review
    head=review.accept(FILES);b.OUT=OUT;original=sources(b)
    _,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'ordinary-tests')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'ordinary contracts')
    protected=[IMPACT,e.REPORT,CIRCUS,PRIOR,GETTER,'content/modernization/pr16_bp_chooser_checkpoint.json','config/active_play_baseline.json']
    value=dict(schema_version=1,task=TASK,regression_id='P08_CIRCUS_POST_EXIT_ORDINARY',case=CASE,source_head=head,
        workflow_source_head=os.environ['GITHUB_SHA'],candidate=TARGET,original=original,
        source_bindings={p:e.identity((ROOT/p).read_bytes()) for p in FILES},protected_originals={p:e.identity((ROOT/p).read_bytes()) for p in protected},
        native_verified=False,representative_accepted=False,visual_review_completed=False,new_emulator_processes=0,
        host_compiles=0,fresh_cores=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,
        rom_changes=0,release_ready=False,failures=[])
    (OUT/'native-result.json').write_bytes(e.stable(value));checkpoint(value,'START')


def native():
    b=cp.b;b.OUT=OUT;b.scope();value=b.load(REPORT)
    need(value['recording_run']==int(os.environ['GITHUB_RUN_ID']) and value['new_emulator_processes']==0,'duplicate attempt')
    work=OUT/'work';work.mkdir(parents=True,exist_ok=True)
    try:
        save=CACHE/'normal30.srm';need(not save.is_symlink(),'cache symlink');savebytes=save.read_bytes()
        value['cache']=cache.validate_cache(e.strict((CACHE/'provenance.json').read_bytes()),savebytes,b.load(GETTER)['original_failure']['normal_save30'])
        need(value['cache']==value['original']['cache'],'verified cache differs')
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
Path('.local/pr16-p08-ordinary/work/candidate.gba').write_bytes(raw)
"""
        _,_,proc=b.capture([sys.executable,'-c',code],'materialize');need(b.exited(proc)==0,'materialization')
        rom=work/'candidate.gba';raw=rom.read_bytes();generated={}
        for name,meta in value['original']['generated'].items():
            data=(OUT/'original'/name).read_bytes();need(e.identity(data)==meta,'source original');generated[name]=data
        value['oracle'],walk=physical(raw,generated);generated=adapt(generated)
        generated['po_walk.h']=walk;generated['po_routes.h']=generated['ss_routes.h'].replace(b'ss_routes',b'po_routes')
        for name,data in generated.items():(work/name).write_bytes(data)
        value['generated']={n:e.identity(d) for n,d in generated.items()}
        dep=work/'deps.d';exe=work/'runner'
        _,err,proc=b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+str(work),'-MMD','-MF',str(dep),str(work/'controller.c'),'-lmgba','-o',str(exe)],'compile')
        need(b.exited(proc)==0 and not err,'host compile');value['host_compiles']=1;bindings={}
        for item in shlex.split(dep.read_text().replace('\\\n',' ').split(':',1)[1]):
            p=Path(item);p=(p if p.is_absolute() else ROOT/p).resolve()
            if p.parent==work:need(p.name in generated and p.read_bytes()==generated[p.name],'generated dependency')
            else:
                name=p.relative_to(ROOT).as_posix()
                if name not in (HEADER,OBSERVER):need(p.read_bytes()==subprocess.check_output(['git','show',HEAD+':'+name],cwd=ROOT),'transitive source drift: '+name)
                bindings[name]=e.identity(p.read_bytes())
        value['transitive_compiled_sources']=bindings
        scratch=work/'private.srm';scratch.write_bytes(savebytes);shots=OUT/'screens';shots.mkdir(exist_ok=True)
        value['new_emulator_processes']=1;(OUT/'native-result.json').write_bytes(e.stable(value))
        stdout,stderr,proc=b.capture([str(exe),str(rom),str(scratch),TARGET['sha256'],cache.SAVE['sha256'],CASE,str(shots/CASE)],CASE,600)
        value['process']=proc;row,proof=validate(stdout,stderr,proc,value['oracle'],value['original']['exit_event'])
        need(e.identity(rom.read_bytes())==TARGET and save.read_bytes()==savebytes,'protected input changed')
        for path,meta in value['protected_originals'].items():need(e.identity((ROOT/path).read_bytes())==meta,'protected accepted original')
        value.update(native_verified=True,native_result=row,native_proof=proof,fresh_cores=row['fresh_cores'])
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
