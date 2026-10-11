#!/usr/bin/env python3
"""17勝後ready=1の新原本を再実行せず、task/fieldの実ROM命令を限定照合。"""
from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_win_return_owner.py'
TEST='tests/test_pr16_circus_win_return_owner.py'
WORKFLOW='.github/workflows/pr16-circus-win-return-owner.yml'
REPORT='content/modernization/pr16_circus_win_return_owner.json'
TRACE='content/modernization/pr16_circus_win_return_trace.json'
RAW='evidence/pr16_circus_win_return_trace/35432359547/native/circus-continuous-30-save.stderr'
OLD='evidence/pr16_circus_taunt/35430246002/native/circus-continuous-30-save.stderr'
TASK='USER-20260919-CIRCUS-WIN-RETURN-OWNER'
OUT=ROOT/'.local/pr16-circus-win-return-owner'
FILES=(SELF,TEST,WORKFLOW,TRACE,RAW,OLD)
NEXT='ready=1の実17戦目WIN停止を、先頭taskとfield loopの実ROM命令から修復する。ready=0限定FadeInの単純拡張はしない。独立2link/全ROM差分証明の後、新候補だけで継続と保存を検証し、旧17戦診断は再実行しない。'


def need(ok,message):
    if not ok:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def witness(raw,old):
    def events(data):return [json.loads(l[18:]) for l in data.splitlines() if l.startswith(b'CIRCUS_CONTINUOUS ')]
    current,prior=events(raw),events(old)
    need(len(current)==80 and current==prior,'eighty original native events differ')
    need(sum(e['label']=='outcome' and e['outcome']==1 for e in current)==17,'real win count')
    need(current[-1]['label']=='timeout' and current[-1]['battle']==16 and current[-1]['bp']==45,'terminal boundary')
    rows=[json.loads(l[18:]) for l in raw.splitlines() if l.startswith(b'CIRCUS_WIN_RETURN ')]
    need(len(rows)==13,'observed readonly rows differ')
    last=rows[-1]
    for k,v in dict(frame=284892,callback2=0x08055e75,script=0x09ff4d77,ready=1,palette_state=1,
        phase=2,newbs=0,marker=2,snapshot=1,waiting=0,count=3,outcome=1,current=16,best=16).items():
        need(type(last.get(k)) is int and last[k]==v,'observed ready-one boundary: '+k)
    data=bytes.fromhex(last['tasks']);need(len(data)==640,'task ABI')
    active=[dict(slot=i,function=int.from_bytes(data[i*40:i*40+4],'little'),previous=data[i*40+5],
        next=data[i*40+6],priority=data[i*40+7],data=data[i*40+8:(i+1)*40].hex()) for i in range(16) if data[i*40+4]==1]
    need([r['function'] for r in active]==[0x0807951d,0x0806e005,0x0806e031,0x080f7abd,0x080f7abd,0x0807d465],'active task owners differ')
    starts=[r for r in active if r['previous']==254];need(len(starts)==1 and starts[0]['slot']==3,'task chain root')
    byslot={r['slot']:r for r in active};order=[];slot=3
    while slot!=255:
        need(slot in byslot and slot not in order,'invalid active task chain');order.append(slot);slot=byslot[slot]['next']
    need(order==[3,4,5,0,1,2],'task order differs')
    return dict(observed_rows=13,original_events_identical=80,real_wins=17,settled_wins=16,bp=45,
        last_observed_frame=last['frame'],timeout_frame=current[-1]['frame'],ready=1,palette_state=1,
        tasks=active,task_order=order,source_observation_complete=True,
        old_ready_zero_hypothesis_rejected=True,persistent_180_frame_ready_zero_claimed=False,
        native_acceptance=False,save_continue_verified=False,genuine_30_wins_verified=False)


def configure():
    import pr16_circus_three_win as b
    b.SELF=SELF;b.TEST=TEST;b.WORKFLOW=WORKFLOW;b.rec.TASK=TASK
    b.OUT.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True)
    return b


def checkpoint(value,phase,stop):
    import pr16_resume as resume
    b=configure();r=b.rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(value))
    state['circus_win_return_owner']=loss['win_return_owner']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_continuous_followup']=dict(path=REPORT,classification=value['classification'],target_wins=30)
    note='run35432359547/job105869102983: host9と修正wrapper5はPASS、実17戦目WINまで80events完全一致。新readonly13点はready1/palette1/両waiter/先頭080f7abdを観測しready0仮説を反証。native受入/Save/30勝ではなくActions failureを保持。同候補の同じ診断は再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=SELF
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*FILES,*value.get('text_evidence',{})],phase,
        value['classification']+'。保存原本の再照合と限定ROM逆アセンブルのみ。新規native0/ARM link0/受入単体再実行0。')


def prepare():
    import pr16_resume as resume
    b=configure();r=b.rec;r.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'owner analysis already recorded')
    old=resume.load(ROOT,TRACE);run=r.api('actions/runs/35432359547')
    need(run['status']=='completed' and run['conclusion']=='failure' and run['head_sha']=='7370e9222019ff8de5431c2bec71946999ca3bc9','latest trace Actions')
    need(old['recording_run']==35432359547 and old['diagnostic_complete'] is False,'old ready-zero result changed')
    for p,bound in old['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'raw trace changed: '+p)
    value=dict(schema_version=1,classification='CIRCUS_WIN_RETURN_READY_ONE_OWNER_PREPARED',candidate=old['candidate'],
        diagnosis=witness((ROOT/RAW).read_bytes(),(ROOT/OLD).read_bytes()),
        host_tests=r.tests([Path(TEST).name]),source_run=35432359547,source_job=105869102983,
        original_conclusion='failure',actual_new_native_processes=0,independent_arm_links=0,
        accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    checkpoint(value,'PREPARED','実17勝後のreadonly13点はready1。旧80events完全一致を確認し、ready0修復仮説を撤回。先頭task2件とfield loopの未読命令を固定候補から読む。')


def reconstruct():
    import pr16_circus_finish as f
    configure();f.reconstruct()


def native():
    """workflowの既存step名だけを継承する。ここではemulatorを一切起動しない。"""
    import pr16_streak_native as n
    value=json.loads((ROOT/REPORT).read_bytes());raw=(n.INPUT/'candidate.gba').read_bytes()
    need(identity(raw)==value['candidate'],'fixed candidate changed')
    spans=[(0x08055e38,64),(0x080f7abc,224),(0x0807951c,80),(0x0807d464,32),(0x0807d360,128),(0x0807db48,64)]
    for address,size in spans:
        text=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb',
            '--adjust-vma=0x08000000','--start-address='+hex(address),'--stop-address='+hex(address+size),str(n.INPUT/'candidate.gba')],text=True,cwd=ROOT)
        (OUT/('callback-'+hex(address)+'.txt')).write_text(text.replace(str(ROOT)+'/',''))
    (OUT/'inspection.json').write_bytes(stable(dict(candidate=identity(raw),spans=[dict(address=a,size=s,
        identity=identity(raw[a-0x08000000:a-0x08000000+s])) for a,s in spans],native_processes=0,arm_links=0,rom_changes=0)))
    print('SOURCE_INSPECTION=PASS NATIVE_PROCESSES=0 ROM_CHANGES=0')


def finish():
    value=json.loads((ROOT/REPORT).read_bytes());value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['text_evidence']={}
    if (OUT/'inspection.json').exists():value['classification']='CIRCUS_WIN_RETURN_READY_ONE_OWNER_INSPECTED'
    for p in sorted(OUT.iterdir()):
        if p.suffix not in {'.txt','.json'} or p.name.endswith('-receipt.json'):continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'text only')
        path='evidence/pr16_circus_win_return_owner/'+os.environ['GITHUB_RUN_ID']+'/'+p.name
        q=ROOT/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);value['text_evidence'][path]=identity(raw)
    checkpoint(value,'RECORDED','ready1で停止する実17勝後のtask順3→4→5→0→1→2を原本から確定。先頭080f7abdとfield/weather/scriptの固定ROM命令を保存。新規native0。')


if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().pipeline()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
