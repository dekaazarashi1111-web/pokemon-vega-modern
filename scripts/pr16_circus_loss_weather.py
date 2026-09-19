#!/usr/bin/env python3
"""Circus敗北時の正規weather/fade待ちを限定復帰。結果/partyはscriptに委譲。"""
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
SELF='scripts/pr16_circus_loss_weather.py'
TEST='tests/test_pr16_circus_loss_weather.py'
WORKFLOW='.github/workflows/pr16-circus-loss-weather.yml'
HEADER='overlays/circus_streak/circus_streak_return.h'
RUNTIME='overlays/circus_streak/circus_streak_runtime.c'
FIXTURE='tests/fixtures/circus_streak_return_fixture.c'
WATCH='tools/mgba_pr16_circus_loss_weather.h'
REPORT='content/modernization/pr16_circus_loss_weather.json'
OUT=ROOT/'.local/pr16-circus-loss-weather'
OLD='6e0483d6f7cd7c0da86ca9e90f9a5261c42b3ededa0b04d7e1434c413c86e97a'
TRACE='evidence/pr16_circus_return_trace/35414451945/'

BODY='''static void resume_loss_fade_if_waiting(void)
{
    const volatile VegaFactoryState *f = &gVegaModernSaveData->factory;
    const volatile uint8_t *tasks = (const volatile uint8_t *)(uintptr_t)0x030050D0u;
    uint8_t weather_waiter = 0u, script_waiter = 0u;
    uint32_t callback = *(volatile uint32_t *)(uintptr_t)0x03003134u;
    uint32_t script = *(volatile uint32_t *)(uintptr_t)0x03000EB8u;
    uint8_t ready = *(volatile uint8_t *)(uintptr_t)0x02038530u;
    unsigned i;
    if (callback != 0x08055E75u || ready != 0u)
        return;
    for (i = 0; i < 16u; ++i) {
        const volatile uint8_t *task = tasks + 40u * i;
        uint32_t function;
        if (task[4] != 1u)
            continue;
        function = *(const volatile uint32_t *)(const volatile void *)task;
        if (function == 0x0807951Du) weather_waiter = 1u;
        if (function == 0x0807D465u) script_waiter = 1u;
    }
    if (CircusStreakReturnFadeAllowed((uint8_t)CircusStreakRuntimeArmed(),
            (uint8_t)((*(volatile uint32_t *)(uintptr_t)0x02022AACu & 0x04000000u) != 0u),
            f->marker, f->snapshot_valid, f->party_count,
            *(volatile uint8_t *)(uintptr_t)0x02023DEAu, script, callback, ready,
            weather_waiter, script_waiter)
        && VegaSaveValidate(gVegaModernSaveData, VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK) {
        /* 両待機taskの実観測に限定。通常のFadeInFromBlackでreadyForInitを立てる。
         * Task_WeatherInit/Task_ContinueScriptが本来の初期化と再開を完了する。
         * readyForInitとtask遷移が再実行を抑止。hostからの状態注入は不要。 */
        ((void (*)(void))(uintptr_t)0x0807D361u)();
    }
}

'''


def repair_runtime(text):
    old='#include "circus_streak_loss.h"'
    need(text.count(old)==1 and 'resume_loss_fade_if_waiting' not in text,'runtime preimage')
    text=text.replace(old,old+'\n#include "circus_streak_return.h"')
    anchor='EXPORT void CircusStreakRuntimeReadKeys(void)'
    need(text.count(anchor)==1,'readkeys entry');text=text.replace(anchor,BODY+anchor)
    old='    ((void (*)(void))(uintptr_t)CIRCUS_PREVIOUS_READ_KEYS)();\n    restore_cache_if_field();'
    need(text.count(old)==1,'readkeys delegate boundary')
    return text.replace(old,old+'\n    resume_loss_fade_if_waiting();')


def install_probe(probe):
    """不変の旧validatorをstrictな1箇所変換で継承し、初期frame0だけを修復。"""
    import inspect
    source=inspect.getsource(probe.parse)
    old="type(row['label']) is str and row['frame']>0 and (i==0 or row['frame']>events[i-1]['frame'])"
    new="type(row['label']) is str and (row['frame']>0 or (i==0 and row['label']=='fixture' and row['frame']==0)) and (i==0 or row['frame']>events[i-1]['frame'])"
    need(source.count(old)==1,'immutable parser frame anchor changed')
    exec(compile(source.replace(old,new),SELF+':frame-zero','exec'),probe.__dict__)


def checkpoint(value,stop,next_step,phase,extra,state=None):
    import pr16_resume as resume
    if state is None:state=resume.validate(ROOT)
    loss=resume.load(ROOT,record.REPORT)
    loss['weather_followup']=dict(path=REPORT,classification=value['classification'],run_id=int(os.environ['GITHUB_RUN_ID']),physical_admission_accepted=False)
    (ROOT/REPORT).write_bytes(stable(value))
    record.SELF=SELF;record.TEST=TEST;record.WORKFLOW=WORKFLOW;record.HEADER=HEADER
    record.checkpoint(state,loss,stop,next_step,[REPORT,HEADER,FIXTURE,WATCH,*extra],phase,value['classification']+'。旧原本保持、受入済みnative再実行0。')


def prepare():
    import pr16_resume as resume
    import pr16_streak_native as n
    record.scope();state=resume.validate(ROOT)
    need(not (ROOT/REPORT).exists(),'weather followup already executed; do not replay')
    diagnostic=resume.load(ROOT,'content/modernization/pr16_circus_return_trace.json')
    need(diagnostic['classification']=='CIRCUS_RETURN_READONLY_TRACE_COMPLETE_NOT_ACCEPTANCE' and diagnostic['rows']==52,'return evidence incomplete')
    value=dict(schema_version=1,classification='CIRCUS_LOSS_NATIVE_FADE_REPAIR_PENDING',diagnostic_run=35414451945,
        diagnostic_sha256=identity((ROOT/'content/modernization/pr16_circus_return_trace.json').read_bytes())['sha256'],
        accepted_native_cases_replayed=0,physical_admission_accepted=False,suppression_accepted=False,release_ready=False)
    p=ROOT/RUNTIME;need(identity(p.read_bytes())==state['source_bindings'][RUNTIME],'runtime source changed')
    p.write_text(repair_runtime(p.read_text()))
    install_probe(n.probe)
    value['host_tests']=record.tests(['test_pr16_circus_loss_weather.py','test_pr16_streak_native.py'])
    OUT.mkdir(parents=True,exist_ok=True)
    checkpoint(value,'敗北後のweather初期化待ちとスクリプト再開待ちが同時に残る原本52点を保存済み。Circus・実敗北・正規3script・有効台帳・両待機taskに限定してnative FadeInFromBlackを再開。判定側も初期frame0だけを正しく扱う。','新候補の独立2linkと実敗北/原party600/固有owner64/通常Save/fresh Continueを検証する。勝敗やpartyをhostから注入しない。','FADE-SOURCE',[RUNTIME,SELF,TEST,WORKFLOW],state=state)


def build():
    import pr16_circus_streak as b
    b.SOURCES=[*b.SOURCES,HEADER];b.SELF=SELF;b.TEST=TEST;b.WORKFLOW=WORKFLOW
    result=b.run()
    need(result['independent_arm_links']==2 and result['whole_rom_rollback_matches_parent'] is True
         and result['original_factory_runtime_unchanged'] is True,'build invariant')


def native():
    import pr16_circus_streak as b
    import pr16_streak_native as n
    r=json.loads((b.OUT/'report.json').read_bytes());raw=(b.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==r['candidate'] and r['candidate']['sha256']!=OLD,'new scoped runtime absent')
    # 元ROMの待機taskを、保存済みの実際の逆アセンブル先頭32byteに照合。
    for address in (0x0807951c,0x0807d464):
        source=(ROOT/TRACE/('callback-'+hex(address)+'.txt')).read_text();expected={}
        for line in source.splitlines():
            match=re.match(r'\s*([0-9a-f]+):\s+([0-9a-f]{4})(?:\s+([0-9a-f]{4}))?\s',line)
            if not match:continue
            at=int(match[1],16)
            for word in (match[2],match[3]):
                if word:
                    data=int(word,16).to_bytes(2,'little')
                    for byte in data:expected[at]=byte;at+=1
        need(bytes(expected[address+i] for i in range(32))==raw[address-0x08000000:address-0x08000000+32],'native waiter preimage changed')
    n.INPUT.mkdir(parents=True,exist_ok=True);(n.INPUT/'candidate.gba').write_bytes(raw);(n.INPUT/'report.json').write_bytes(stable(r))
    def verify(recipe):
        need(recipe==r and identity((n.INPUT/'candidate.gba').read_bytes())==r['candidate'],'native build/input differs')
        for name,bound in r['source_bindings'].items():need(identity((ROOT/name).read_bytes())==bound,'source binding: '+name)
    n.reconstruct=lambda:verify(r);n.verify_recipe=verify;n.probe.SHA=r['candidate']['sha256'];install_probe(n.probe)
    n.SELF=SELF;n.TEST=TEST;n.WORKFLOW=WORKFLOW;n.EXTRA=n.EXTRA|{HEADER,FIXTURE,WATCH}
    policy=n.policy;n.policy=lambda wx,br:policy(wx,br)+'\n'+(ROOT/WATCH).read_text()
    result=n.run();need(result['status']=='PASS_CIRCUS_SCOPED_NATIVE','weather successor not accepted; inspect preserved original')


def finish():
    import pr16_streak_native as n
    import pr16_circus_streak as b
    value=json.loads((ROOT/REPORT).read_bytes());extra=[]
    value['classification']='CIRCUS_LOSS_FADE_NATIVE_DIAGNOSTIC_OPEN'
    report=n.OUT/'report.json'
    if report.exists():
        value['native']=json.loads(report.read_bytes())
        if value['native']['status']=='PASS_CIRCUS_SCOPED_NATIVE':
            value['classification']='CIRCUS_LOSS_FADE_SAVE_CONTINUE_VERIFIED_SCOPED'
            value['scoped_result']=json.loads((n.OUT/'streak.json').read_bytes())
    prefix='evidence/pr16_circus_loss_weather/'+os.environ['GITHUB_RUN_ID']+'/'
    paths=[report,n.OUT/(n.probe.CASE+'.stdout'),n.OUT/(n.probe.CASE+'.stderr'),n.OUT/(n.probe.CASE+'.process.json'),n.OUT/'streak.json',b.OUT/'report.json']
    value['text_evidence']={}
    for p in paths:
        if not p.exists():continue
        raw=p.read_bytes();raw.decode();need(b'\0' not in raw,'nontext native evidence')
        name=prefix+('build-' if p.parent==b.OUT else '')+p.name
        q=ROOT/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        extra.append(name);value['text_evidence'][name]=identity(raw)
    value['recording_run']=int(os.environ['GITHUB_RUN_ID']);value['visual_review_completed']=False
    passed=value['classification']=='CIRCUS_LOSS_FADE_SAVE_CONTINUE_VERIFIED_SCOPED'
    stop=('Circus実敗北の正規フェード/スクリプト復帰・原party600・固有owner64・Factory104不変・通常Save/fresh Continueをnativeで確認。' if passed else 'Circus限定フェード修復候補の原本を保存。native完了条件未達は成功に改作せず、停止箇所を継続修復。')
    nxt=('受入済みの敗北保存原本を再実行せず、未受入の実3勝・第2/第3launch個体保持・9BP完走に進む。続いて中断復帰、真正30連勝と正規特性抑制。' if passed else '新reportの失敗とweather traceを読み、次の実停止を修復。原本再解釈で受入できる場合はnativeを再実行せず検証のみ。')
    checkpoint(value,stop,nxt,'FADE-NATIVE',extra)


SETUP_WORKFLOW='.github/workflows/pr16-circus-loss-followup.yml'
SETUP_STEPS=('固定compilerとStage84親入力を復元','固定private入力とcharmapだけを復元',
             '修復sourceから独立2linkし旧受入は再実行しない','1byte限定証明と未受入の敗北保存native')

def step_shell(text,label):
    anchor='      - name: '+label+'\n'
    need(text.count(anchor)==1,'setup step boundary')
    block=text.split(anchor,1)[1].split('\n      - ',1)[0]
    need(block.count('        run: |\n')==1,'setup literal run boundary')
    lines=block.split('        run: |\n',1)[1].splitlines()
    need(lines and all(not line or line.startswith('          ') for line in lines),'setup shell indentation')
    return '\n'.join(line[10:] for line in lines)+'\n'


def pipeline():
    import pr16_resume as resume
    state=resume.validate(ROOT);raw=(ROOT/SETUP_WORKFLOW).read_bytes()
    need(identity(raw)==state['source_bindings'][SETUP_WORKFLOW],'inherited setup workflow changed')
    for i,label in enumerate(SETUP_STEPS):
        shell=step_shell(raw.decode(),label).replace('.local/pr16-circus-loss-followup','.local/pr16-circus-loss-weather')
        if i==2:
            need(shell.count('python3 scripts/pr16_circus_streak.py')==1,'build command boundary')
            shell=shell.replace('python3 scripts/pr16_circus_streak.py','python3 '+SELF+' build')
        if i==3:
            need(shell.count('python3 scripts/pr16_circus_loss_followup.py native')==1,'native command boundary')
            shell=shell.replace('python3 scripts/pr16_circus_loss_followup.py native','python3 '+SELF+' native')
        (OUT/('step-'+str(i)+'.sh')).write_text(shell)
        subprocess.run(['bash','-euo','pipefail','-c',shell],cwd=ROOT,check=True)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in {'prepare','build','native','finish','pipeline'},'command required')
    globals()[sys.argv[1]]()
