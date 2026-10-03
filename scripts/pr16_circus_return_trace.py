#!/usr/bin/env python3
"""修復済み6e候補の敗北後1200frameを読み取り専用で限定記録。"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_circus_loss_followup as record
need,identity,stable=record.need,record.identity,record.stable
SELF='scripts/pr16_circus_return_trace.py'
TEST='tests/test_pr16_circus_return_trace.py'
WORKFLOW='.github/workflows/pr16-circus-return-trace.yml'
HEADER='tools/mgba_pr16_circus_return_trace.h'
REPORT='content/modernization/pr16_circus_return_trace.json'
SHA='6e0483d6f7cd7c0da86ca9e90f9a5261c42b3ededa0b04d7e1434c413c86e97a'
OUT=ROOT/'.local/pr16-circus-return-trace'


def parse(raw):
    rows=[json.loads(s[len('CIRCUS_RETURN '):]) for s in raw.decode().splitlines() if s.startswith('CIRCUS_RETURN ')]
    sizes=dict(main=16,field=8,script=124,fade=32,tasks=640,owner=64)
    integers={'frame','elapsed','dispcnt','bldcnt','bldalpha','bldy'}
    need(33<=len(rows)<=64,'return trace row count')
    for i,r in enumerate(rows):
        need(set(r)==set(sizes)|integers,'return trace schema')
        for k in integers:need(type(r[k]) is int and 0<=r[k]<=0xffffffff,'return trace integer')
        for k,size in sizes.items():
            need(type(r[k]) is str and re.fullmatch('[0-9a-f]{'+str(size*2)+'}',r[k]) is not None,'return trace byte string')
        need(r['frame']>0 and r['elapsed']==r['frame']-rows[0]['frame'] and (i==0 or r['frame']>rows[i-1]['frame']),'trace frame order')
    need(rows[0]['elapsed']==0 and rows[-1]['elapsed']==1200,'return trace endpoints')
    return rows


def checkpoint(value,stop,phase,extra):
    import pr16_resume as resume
    state=resume.validate(ROOT);loss=resume.load(ROOT,record.REPORT)
    loss['return_diagnostic']=dict(path=REPORT,classification=value['classification'],native_acceptance=False,
        run_id=int(os.environ['GITHUB_RUN_ID']))
    (ROOT/REPORT).write_bytes(stable(value))
    record.SELF=SELF;record.TEST=TEST;record.WORKFLOW=WORKFLOW
    record.checkpoint(state,loss,stop,'敗北後のfield callback/script/fade/task記録を照合し、正規復帰経路だけを修復する。hostからPC/LR/勝敗/party/連勝/効果を注入しない。受入済み単体/2linkは無変更再実行しない。',
        [REPORT,HEADER,*extra],'RETURN-'+phase,'readonly trace契約PASS。診断のみ、native受入追加なし。')


def prepare():
    import pr16_resume as resume
    record.scope();resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'return trace already started; inspect result instead of replay')
    result=record.tests(['test_pr16_circus_return_trace.py'])
    value=dict(schema_version=1,classification='CIRCUS_RETURN_READONLY_TRACE_PENDING',candidate=dict(size=33554432,sha256=SHA),
        host_tests=result,physical_admission_accepted=False,release_ready=False,accepted_native_cases_replayed=0)
    OUT.mkdir(parents=True,exist_ok=True)
    checkpoint(value,'6e修復候補はWhiteOutを回避するが黒画面で原party復元前に停止。未観測の敗北後1200frameのfield/script/fade/taskだけを入力専用で記録。固定2linkの再実行なし。','START',[SELF,TEST,WORKFLOW])


def native():
    import pr16_streak_native as n
    import pr16_circus_retention as parent
    from pr16_circus_streak import bounded_patch
    r=json.loads((ROOT/record.REPORT).read_bytes())['native']['build_recipe']
    need(r['candidate']==dict(size=33554432,sha256=SHA),'fixed return candidate')
    raw=(parent.OUT/'candidate.gba').read_bytes();need(identity(raw)==r['parent'],'fixed parent')
    new=bounded_patch(raw,r['patches']);need(identity(new)==r['candidate'],'fixed candidate reconstruction')
    for name,bound in r['source_bindings'].items():need(identity((ROOT/name).read_bytes())==bound,'build binding changed: '+name)
    n.INPUT.mkdir(parents=True,exist_ok=True);(n.INPUT/'candidate.gba').write_bytes(new);(n.INPUT/'report.json').write_bytes(stable(r))
    def verify(recipe):need(recipe==r and identity((n.INPUT/'candidate.gba').read_bytes())==r['candidate'],'readonly input changed')
    n.probe.SHA=SHA;n.reconstruct=lambda:verify(r);n.verify_recipe=verify
    n.SELF=SELF;n.TEST=TEST;n.WORKFLOW=WORKFLOW;n.EXTRA=n.EXTRA|{HEADER}
    original=n.policy;n.policy=lambda wx,br:original(wx,br)+'\n'+(ROOT/HEADER).read_text()
    result=n.run()
    stderr=(n.OUT/(n.probe.CASE+'.stderr')).read_bytes();rows=parse(stderr)
    process=json.loads((n.OUT/(n.probe.CASE+'.process.json')).read_bytes())
    need(result['actual_new_processes']==1 and len(result['guard_checks'])==7 and process['returncode']==1
         and b'bounded return context diagnostic complete' in stderr,'bounded diagnostic did not complete')
    # 実際のROMを対象に、既知callbackと観測calleeの小範囲だけを逆アセンブル。
    starts={0x08055e50,0x08055f60,0x08056160,0x0807fc00}
    for row in rows:
        for key in ('main','field'):
            data=bytes.fromhex(row[key])
            for at in range(0,len(data),4):
                address=int.from_bytes(data[at:at+4],'little')&~1
                if 0x08000000<=address<0x0a000000:starts.add(address)
        data=bytes.fromhex(row['tasks'])
        for at in range(0,640,40):
            address=int.from_bytes(data[at:at+4],'little')&~1
            if data[at+4] and 0x08000000<=address<0x0a000000:starts.add(address)
    need(len(starts)<=32,'callback disassembly bound')
    for address in sorted(starts):
        text=subprocess.check_output(['arm-none-eabi-objdump','-D','-b','binary','-m','arm','-M','force-thumb','--adjust-vma=0x08000000',
            '--start-address='+hex(address),'--stop-address='+hex(address+160),str(n.INPUT/'candidate.gba')],text=True,cwd=ROOT)
        (OUT/('callback-'+hex(address)+'.txt')).write_text(text.replace(str(ROOT)+'/',''))
    (OUT/'rows.json').write_bytes(stable(rows))
    (OUT/'diagnostic.json').write_bytes(stable(dict(classification='CIRCUS_RETURN_READONLY_TRACE_COMPLETE_NOT_ACCEPTANCE',
        rows=len(rows),elapsed_frames=1200,process=process,candidate=r['candidate'],callbacks=sorted(starts),new_emulator_processes=1,
        accepted_native_cases_replayed=0,rom_changes=0,independent_arm_links_replayed=0,native_acceptance=False)))


def finish():
    import pr16_streak_native as n
    value=json.loads((ROOT/REPORT).read_bytes());files=[]
    diagnostic=OUT/'diagnostic.json'
    value['classification']='CIRCUS_RETURN_READONLY_TRACE_FAILED'
    if diagnostic.exists():value.update(json.loads(diagnostic.read_bytes()))
    prefix='evidence/pr16_circus_return_trace/'+os.environ['GITHUB_RUN_ID']+'/'
    sources=list(OUT.glob('*.json'))+list(OUT.glob('callback-*.txt'))
    sources += [n.OUT/name for name in ('report.json',n.probe.CASE+'.stderr',n.probe.CASE+'.process.json')]
    bindings={}
    for p in sources:
        if not p.exists():continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext evidence')
        name=prefix+(('native-' if p.parent==n.OUT else '')+p.name)
        dst=ROOT/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
        bindings[name]=identity(raw);files.append(name)
    value['evidence']=bindings;value['recording_run']=int(os.environ['GITHUB_RUN_ID'])
    checkpoint(value,'6e候補の敗北後限定診断を原本保存。旧nativeの失敗は保持し、今回もparty/save受入へ昇格しない。field/script/fade/taskとcallback逆アセンブルの新しい観測から修復へ進む。','RECORDED',files)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'prepare','native','finish'},'command required')
    globals()[sys.argv[1]]()
