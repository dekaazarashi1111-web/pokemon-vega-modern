#!/usr/bin/env python3
"""Save21後の未受入区間を一度だけ測定。宣言hash一致後に開発text原本を復元する。"""
from __future__ import annotations
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_story_save22_accept as m
import pr16_story_after_maori_measure as transport
import pr16_research_story_route_actions as h
import pr16_story_gym_record as log_gate
OUT=ROOT/'.local/pr16-story-save22'
ART=OUT/'artifact'
SPEC=m.DEV+'/spec.json'
WF='.github/workflows/pr16-story-save22.yml'
CODE={SPEC,WF,'scripts/pr16_story_save22_accept.py','scripts/pr16_story_save22_measure.py',
      'tests/test_pr16_story_save22_accept.py','tests/test_pr16_story_save22_transport.py'}
PARENT=dict(size=17794173,sha256='2ed9efdd23374911bcb23e5092147231ba0af5f06f9280e84ee6a091868e2b05')
SPEC_BINDING=dict(size=12233,sha256='ec1ee2fbe6fffab392920cfc009b5e0fac49c31b1bf357aff356551c691f8e86')


def input_commands(spec):
    p=spec['template']
    m.need(p['task']==m.TASK and p['candidate']==m.CANDIDATE and p['input_save']==m.INPUT_SAVE and p['output_save']==m.OUTPUT_SAVE,'固定新区間identity')
    result={}
    for lane in ('progress','continue'):
        v=p[lane];command=m.inflate(v['commands_zlib_b85'],40000);m.commands(command)
        dev=m.inflate(v['development_commands_zlib_b85'],40000);m.commands(dev)
        m.need(m.identity(command)==v['commands'] and m.identity(dev)==v['development_commands'],'宣言済み入力全byte')
        m.need(command==(dev if lane=='progress' else dev[:-5]+m.COLD_SUFFIX),'未受入cold終端だけ追加')
        result[lane]=command
    return result


def restore_plan(spec,progress,cold):
    """未知の出力を期待値にしない。事前固定された全raw/全JSONのhash一致が必須。"""
    p=deepcopy(spec['template']);v=p['continue'];n=v['development_prefix']['size']
    m.need(m.identity(cold[:n])==v['development_prefix'],'cold開発prefix全byte')
    originals={'progress':progress,'continue':cold[:n]+spec['development_cold_end'].encode('utf-8')}
    for lane in ('progress','continue'):
        m.need(m.identity(originals[lane])==p[lane]['development_stdout'],'測定前に固定した開発stdout全byte '+lane)
        row={}
        for key,value in p[lane].items():
            row[key]=value
            if key=='development_stdout':row['development_stdout_zlib_b85']=base64.b85encode(zlib.compress(originals[lane],9)).decode('ascii')
        p[lane]=row
    raw=(json.dumps(p,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    m.need(m.identity(raw)==spec['expected_json'],'開発expected.json全27997bytesを同一hashで復元。未知値から再採番しない')
    m.decode_plan(p)
    return raw,originals


def invoke(runtime,lane,seed,command):
    m.commands(command);folder=ART/lane;folder.mkdir()
    save=folder/'story.srm';save.write_bytes(seed);(folder/'commands.txt').write_bytes(command)
    argv=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(ART/'runner'),
          str(ART/'candidate.gba'),str(save),'continue-story',m.identity(seed)['sha256']]
    with (folder/'stdout.txt').open('wb') as out,(folder/'stderr.txt').open('wb') as err:
        try:p=subprocess.run(argv,input=command,cwd=folder,stdout=out,stderr=err,timeout=300)
        except subprocess.TimeoutExpired:
            h.d.write(folder/'execution.json',dict(status='TIMEOUT_NOT_ACCEPTED',initial_save=m.identity(seed),
                current_save=m.identity(save.read_bytes()),native_processes=1,automatic_retry=False));raise
    h.d.write(folder/'execution.json',dict(returncode=p.returncode,initial_save=m.identity(seed),
        final_save=m.identity(save.read_bytes()),native_processes=1,automatic_retry=False))
    m.need(p.returncode==0 and not (folder/'stderr.txt').read_bytes(),'失敗原本を保全し停止。自動再走なし')
    return save.read_bytes()


def measure():
    os.chdir(ROOT);h.d.current()
    m.need(os.environ['GITHUB_RUN_ATTEMPT']=='1' and not (ROOT/m.CP).exists() and not OUT.exists(),'未受入の初回測定だけ')
    state=h.source_check();protected=h.d.bindings(set(state['source_bindings'])|h.d.PROTECTED)
    raw=(ROOT/SPEC).read_bytes();m.need(m.identity(raw)==SPEC_BINDING,'転送したspec全byte。誤写はnative前に拒否')
    spec=m.load(raw);m.need(h.d.bindings(spec['source_bindings'])==spec['source_bindings'],'ローカル58試験と同じsource')
    m.need(all(type(spec[k]) is int and spec[k]==v for k,v in dict(development_native_processes=2,development_native_failures=0,
        new_tests=58,accepted_case_reruns=0,accepted_test_reruns=0,compiles=0).items()),'開発実行会計')
    cmds=input_commands(spec);bindings=h.d.bindings(CODE)
    parent=h.d.read(ROOT/m.parent.CP)
    m.need(parent['actions_completion_confirmed'] is True and parent['save21_accepted'] is True and
           parent['verification']['output_save']==m.INPUT_SAVE,'完了済みSave21だけを親にする')
    ART.mkdir(parents=True)
    meta,z=transport.archive(11073849807,36662466133,PARENT,'b58a6356c9b100a9180a9af955d25e1c6be48d0c')
    with z:
        manifest=m.load(z.read('manifest.json'))
        m.need(len(manifest)==86 and set(z.namelist())==set(manifest)|{'manifest.json'},'Save21全86member集合')
        for name,binding in manifest.items():m.need(m.identity(z.read(name))==binding,'親全member '+name)
        for name,target,binding in (('story-fast.srm','input.srm',m.INPUT_SAVE),('candidate.gba','candidate.gba',m.CANDIDATE),('runner','runner',m.RUNNER)):
            value=z.read(name);m.need(m.identity(value)==binding,'親固定byte '+name)
            (ART/target).write_bytes(value);(ART/target).chmod(0o555 if name=='runner' else 0o444)
    h.d.write(ART/'parent.json',{k:meta[k] for k in ('id','name','size_in_bytes','digest','workflow_run','expires_at')})
    runtime=OUT/'runtime';runtime.mkdir()
    _,z=transport.archive(10898620034,36218655601,dict(size=102586759,sha256='a6aeccb72fa15411d956b418ca5f030aa5020a466303a25e0f8814ba2eeb5c4d'))
    with z:
        for name in z.namelist():
            if name=='ld.so' or name.startswith('lib/'):
                path=runtime/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    (runtime/'ld.so').chmod(0o755);(runtime/'lib/libmgba.so.0.10').symlink_to('libmgba.so')
    m.need(m.identity((runtime/'lib/libmgba.so').read_bytes())==dict(size=1968536,
        sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA')
    saved=invoke(runtime,'progress',(ART/'input.srm').read_bytes(),cmds['progress'])
    (ART/'story-fast.srm').write_bytes(saved);m.need(m.identity(saved)==m.OUTPUT_SAVE,'Save22完了後だけcoldへ')
    progress=(ART/'progress/stdout.txt').read_bytes()
    m.need(m.identity(progress)==spec['template']['progress']['development_stdout'],'進行全stdoutを固定開発原本と照合')
    cold=invoke(runtime,'continue',saved,cmds['continue']);(ART/'cold.srm').write_bytes(cold)
    reconstructed,originals=restore_plan(spec,progress,(ART/'continue/stdout.txt').read_bytes())
    dest=ROOT/m.DEV/'expected.json';m.need(not dest.exists(),'未採取planを上書きしない');dest.write_bytes(reconstructed)
    (ART/'expected.json').write_bytes(reconstructed)
    for lane,raw in originals.items():
        (ART/(lane+'-development.stdout.txt')).write_bytes(raw)
        (ART/(lane+'-development.commands.txt')).write_bytes(m.inflate(spec['template'][lane]['development_commands_zlib_b85'],40000))
    os.environ['PR16_SAVE22_FIXTURE']=str(ART)
    for pattern,name,count in (('test_pr16_story_save22_accept.py','unit',58),('test_pr16_story_save22_transport.py','transport-unit',10)):
        unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'],capture_output=True,timeout=120)
        (ART/(name+'.stdout.txt')).write_bytes(unit.stdout);(ART/(name+'.stderr.txt')).write_bytes(unit.stderr)
        m.need(unit.returncode==0,'新規source試験終了値 '+name);log_gate.unit_original(unit.stdout,unit.stderr,count)
    result,ledger=m.verify(ART);h.d.write(ART/'verification.json',result);h.d.write(ART/'save-byte-ledger.json',ledger)
    m.need(h.d.bindings(protected)==protected and h.d.bindings(CODE)==bindings,'旧受入/測定source全byte不変')
    for name,binding in (('input.srm',m.INPUT_SAVE),('candidate.gba',m.CANDIDATE),('runner',m.RUNNER)):
        m.need(m.identity((ART/name).read_bytes())==binding,'原本不変 '+name)
    h.d.write(ART/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
        source_bindings=bindings,result=result,new_tests=68,new_acceptance_tests=58,new_transport_tests=10,
        development_native_processes=2,development_native_failures=0,formal_native_processes=2,
        accepted_case_reruns=0,accepted_test_reruns=0,compiles=0,development_cold_card_end_accepted=False,
        development_text_recovered_only_after_exact_predetermined_hash_match=True,expected_json=spec['expected_json']))
    h.d.write(ART/'manifest.json',{p.relative_to(ART).as_posix():m.identity(p.read_bytes()) for p in sorted(ART.rglob('*')) if p.is_file()})
    print('PASS Save22: 503新5勝/6040円/洞窟北入口/397+35入力/保存cold全byte/新58+10試験/旧再走0')


if __name__=='__main__':measure()
