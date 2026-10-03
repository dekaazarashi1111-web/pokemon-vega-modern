#!/usr/bin/env python3
"""先頭DMA taskだけで原因を断定せず、通常frame境界の実PCとweatherを限定観測。"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
SELF='scripts/pr16_circus_win_return_cpu.py'
TEST='tests/test_pr16_circus_win_return_cpu.py'
HEADER='tools/mgba_pr16_circus_win_return_cpu.h'
WORKFLOW='.github/workflows/pr16-circus-win-return-cpu.yml'
REPORT='content/modernization/pr16_circus_win_return_cpu.json'
OWNER='content/modernization/pr16_circus_win_return_owner.json'
TASK='USER-20260919-CIRCUS-WIN-RETURN-CPU'
OUT=ROOT/'.local/pr16-circus-win-return-cpu'
FILES=(SELF,TEST,HEADER,WORKFLOW,OWNER)
NEXT='新しい実PC/LR/weather原本の最初の停止命令だけを修復する。勝利/party/task/PCをhostから注入しない。2独立linkとROM変更影響台帳を作り新候補で継続を検証する。旧17勝診断や受入済み単体は繰り返さない。'
def need(ok,message):
    if not ok:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def stable(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()

def parse(raw):
    rows=[json.loads(l[15:]) for l in raw.splitlines() if l.startswith(b'CIRCUS_WIN_CPU ')]
    need(len(rows)==21 and [r['elapsed'] for r in rows]==[1,*range(30,601,30)],'CPU sample budget/endpoints')
    for i,r in enumerate(rows):
        for k,size in dict(main=16,weather=64,script=124,tasks=640,stack=128).items():
            need(type(r[k]) is str and re.fullmatch('[0-9a-f]{'+str(2*size)+'}',r[k]),'CPU bytes '+k)
        for k in ('frame','elapsed','pc','lr','sp','cpsr','weather_id','weather_init'):need(type(r[k]) is int,'CPU integer '+k)
        need(r['frame']==rows[0]['frame']+r['elapsed']-1 and 0x03000000<=r['sp']<=0x03008000 and 0<=r['weather_id']<32,'CPU sample scope')
        need(int.from_bytes(bytes.fromhex(r['main'])[4:8],'little')==0x08055e75,'field callback changed')
    need(b'bounded win CPU diagnostic complete' in raw,'diagnostic exit missing')
    return rows

def configure():
    import pr16_circus_win_return_trace as t
    t.SELF=SELF;t.TEST=TEST;t.HEADER=HEADER;t.WORKFLOW=WORKFLOW;t.OUT=OUT;t.TASK=TASK
    t.FILES=tuple(dict.fromkeys((*t.FILES,*FILES)))
    return t

def checkpoint(v,phase,stop):
    import pr16_resume as resume
    t=configure();r=t.configure().rec;state=resume.validate(ROOT);loss=resume.load(ROOT,r.REPORT)
    (ROOT/REPORT).write_bytes(stable(v));state['circus_win_return_cpu']=loss['win_return_cpu']=dict(path=REPORT,classification=v['classification'],run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_continuous_followup']=dict(path=REPORT,classification=v['classification'],target_wins=30)
    r.SELF=SELF;r.TEST=TEST;r.WORKFLOW=WORKFLOW;r.HEADER=HEADER
    r.checkpoint(state,loss,stop,NEXT,[REPORT,*t.FILES,*v.get('text_evidence',{})],phase,v['classification']+'。入力不変、readRegister/bus読取のみ。受入単体再実行0/ARM再link0。')

def prepare():
    import pr16_resume as resume
    t=configure();r=t.configure().rec;r.scope();resume.validate(ROOT);need(not (ROOT/REPORT).exists(),'CPU attempt already exists')
    owner=resume.load(ROOT,OWNER);run=r.api('actions/runs/35432926280')
    need(run['status']=='completed' and run['conclusion']=='success' and owner['classification']=='CIRCUS_WIN_RETURN_READY_ONE_OWNER_INSPECTED','owner inspection incomplete')
    for p,bound in owner['text_evidence'].items():need(identity((ROOT/p).read_bytes())==bound,'owner evidence changed')
    v=dict(schema_version=1,classification='CIRCUS_WIN_CPU_READONLY_PREPARED',candidate=owner['candidate'],
        source_run=35432926280,host_tests=r.tests([Path(TEST).name]),accepted_native_cases_replayed=0,independent_arm_links_replayed=0,
        diagnostic_complete=False,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    checkpoint(v,'PREPARED','ready1原本とROM命令を照合。080f7abdはDMA完了を待つ通常free taskで、先頭にあるだけでは停止原因を確定できない。未観測の実PC/LR/weatherを600frame限定で読む。')

def reconstruct():configure().reconstruct()
def native():
    t=configure();t.configure();ns=dict(t.c.__dict__);ns['chained_watch']=t.chained_watch
    exec(compile(t.chained_native_source(),SELF+':readonly-cpu','exec'),ns)
    try:ns['native']()
    except ValueError as e:need(str(e)=='continuous lifecycle failed; inspect original','unexpected diagnostic failure: '+str(e))
    else:raise ValueError('CPU diagnostic did not stop at its boundary')
    raw=(OUT/'native'/(t.probe.CASE+'.stderr')).read_bytes();rows=parse(raw)
    process=json.loads((OUT/'native'/(t.probe.CASE+'.process.json')).read_bytes())
    need(process==dict(schema_version=1,returncode=1,timed_out=False,spawn_error=None),'bounded diagnostic process')
    events=t.probe.parse(raw);t.verify_prefix(events,(ROOT/t.c.PREFIX).read_bytes());need(len(events)==79,'seventeen outcomes only')
    (OUT/'cpu-rows.json').write_bytes(stable(rows))
    import pr16_streak_native as n
    starts={r[k]&~1 for r in rows for k in ('pc','lr','weather_init') if 0x08000020<=r[k]<0x0a000000-160}
    need(len(starts)<=40,'CPU code evidence budget')
    for at in sorted(starts):
        address=max(0x08000000,at-32)
        text=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma=0x08000000',
            '--start-address='+hex(address),'--stop-address='+hex(at+160),str(n.INPUT/'candidate.gba')],text=True,cwd=ROOT)
        (OUT/('cpu-'+hex(at)+'.txt')).write_text(text.replace(str(ROOT)+'/',''))
    print('CPU_DIAGNOSTIC=PASS NATIVE_ACCEPTANCE=false')

def finish():
    t=configure();v=json.loads((ROOT/REPORT).read_bytes());v['classification']='CIRCUS_WIN_CPU_DIAGNOSTIC_OPEN';v['recording_run']=int(os.environ['GITHUB_RUN_ID']);v['text_evidence']={}
    if (OUT/'cpu-rows.json').exists():v['classification']='CIRCUS_WIN_CPU_READONLY_COMPLETE';v['diagnostic_complete']=True
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and (p.name in ('report.json','reconstruction.json','cpu-rows.json',t.probe.CASE+'.stderr',t.probe.CASE+'.stdout',t.probe.CASE+'.process.json') or (p.parent==OUT and p.name.startswith('cpu-') and p.suffix=='.txt')):
            raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'text evidence only');name='evidence/pr16_circus_win_return_cpu/'+os.environ['GITHUB_RUN_ID']+'/'+p.relative_to(OUT).as_posix()
            q=ROOT/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw);v['text_evidence'][name]=identity(raw)
    checkpoint(v,'RECORDED','17勝後のCPU/weather読取原本を保存。正常Save/30勝の受入とは区別し、実際の停止命令からruntime修復へ進む。')

if __name__=='__main__':
    need(len(sys.argv)==2,'command required');action=sys.argv[1]
    if action=='pipeline':configure().configure().pipeline()
    elif action=='pack':t=configure();t.configure();t.c.f.pack()
    elif action in {'prepare','reconstruct','native','finish'}:globals()[action]()
    else:raise SystemExit('unknown command')
