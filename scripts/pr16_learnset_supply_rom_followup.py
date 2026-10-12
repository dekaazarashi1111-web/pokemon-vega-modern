#!/usr/bin/env python3
"""保存14+10試験/ELF ABI/原本fixtureを継承。未完nativeだけを実行する。"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_supply_rom as m
from pr16_wiki_reconcile import fetch
from pr16_learnset_floette_verify import download
LOCK='content/modernization/pr16_learnset_supply_rom_reuse_inputs.json'
CODE={LOCK,'scripts/pr16_learnset_supply_rom_followup.py'}
original_command=m.command
SAVED=m.WORK/'second-failure'


def inherit():
    lock=m.load(ROOT/LOCK)
    run=fetch('actions/runs/'+str(lock['run_id']))
    m.need(run['status']=='completed' and run['conclusion']=='failure'
        and run['head_sha']==lock['source_head'] and run['path']=='.github/workflows/pr16-learnset-supply-rom.yml','second failure source')
    for name in ('scripts/pr16_learnset_supply_rom_inputs.py','tests/test_pr16_learnset_supply_rom_inputs.py'):
        m.need((ROOT/name).read_bytes()==subprocess.check_output(['git','show',lock['source_head']+':'+name],cwd=ROOT),'inherited input test source')
    download(lock['artifact'],lock['source_head'],SAVED,lock['members'])
    unit=(SAVED/'unit-inputs.stderr.txt').read_bytes()
    failure=m.load(SAVED/'failure.json')
    m.need(unit.count(b' ... ok\n')==10 and b'Ran 10 tests' in unit and unit.rstrip().endswith(b'OK')
        and not (SAVED/'unit-inputs.stdout.txt').read_bytes(),'saved input tests')
    m.need(failure['status']=='FAIL' and failure['source_head']==lock['source_head']
        and failure['run_id']==str(lock['run_id']) and 'supply timeout' in failure['error'],'saved failure boundary')
    for name in lock['members']:(m.PROOF/('previous-'+name)).write_bytes((SAVED/name).read_bytes())
    m.write(m.PROOF/'inherited-input-unit.json',{'run_id':lock['run_id'],'source_head':lock['source_head'],
        'whole_run_conclusion':'failure','scoped_tests_passed':10,'tests_rerun':0,
        'prior_host_compiles':1,'prior_native_processes':1,'prior_native_accepted':False,
        'prior_stop':'first archive call timeout; successful ELF/ABI/source fixtures inherited',
        'artifact':lock['artifact'],'members':lock['members']})


def command(args,name,env=None):
    if name=='unit-inputs':
        m.need(args[1:]==['-B','-m','unittest','tests.test_pr16_learnset_supply_rom_inputs','-v'],'inherit command exact')
        inherit()
        for suffix in ('stdout.txt','stderr.txt'):
            (m.PROOF/(name+'.'+suffix)).write_bytes((SAVED/(name+'.'+suffix)).read_bytes())
        return b''
    return original_command(args,name,env)


def abi(candidate,link):
    m.need(m.identity(candidate)==m.CANDIDATE,'reused ABI candidate')
    result=m.load(SAVED/'abi.json');bindings=result['bindings']
    m.need(result['candidate']==m.CANDIDATE and not result['private_originals_modified']
        and bindings['PR16_CODE_START']==link['code_start'] and bindings['PR16_CODE_END']==link['code_end']
        and bindings['PR16_ORIGINAL_TUTOR']==link['symbols']['Pr16_SupplyOriginalTutor']|1,'saved ABI link binding')
    for name in ('abi.json','abi-symbols.json','elf-restore.json'):
        (m.PROOF/name).write_bytes((SAVED/name).read_bytes())
    return bindings


def samples(bindings):
    manifest=m.load(SAVED/'fixture-manifest.json');items=manifest['cases']
    m.need(manifest['source']=='ACCEPTED_ORIGINAL_OWNER_SPANS_NOT_PLA1'
        and manifest['candidate']==m.CANDIDATE and manifest['samples']==len(items)==26
        and manifest['owners']==[r['species'] for r in items],'fixed original fixture')
    text=['/* Generated from accepted original owner spans, never from PLA1 decode. */']
    text.extend('#define '+k+' '+hex(v)+'U' for k,v in sorted(bindings.items()))
    text.append('struct SupplySample {uint16_t species;uint8_t policy;uint16_t machine_count,tutor_count;uint64_t bits;uint16_t machine[160],tutor[40];};')
    text.append('static const uint16_t special_moves[9]={'+','.join(map(str,m.SPECIAL))+'};')
    text.append('static const struct SupplySample supply_samples[]={')
    for r in items:
        vals=','.join(map(str,(r['species'],r['policy'],len(r['machine']),len(r['tutor']))))
        text.append('{'+vals+',UINT64_C('+hex(r['bits'])+'),{'+(','.join(map(str,r['machine'])) or '0')+'},{'+(','.join(map(str,r['tutor'])) or '0')+'}},')
    text.append('};');header=('\n'.join(text)+'\n').encode()
    m.need(m.identity(header)==manifest['header'],'saved fixture header exact bytes')
    (m.WORK/'pr16_supply_samples.h').write_bytes(header)
    (m.PROOF/'fixture-manifest.json').write_bytes((SAVED/'fixture-manifest.json').read_bytes())
    return len(items)


def verify():
    m.command=command;m.abi=abi;m.samples=samples
    m.verify()
    path=m.PROOF/'verification.json';v=m.load(path)
    v['new_tests']=0;v['inherited_input_unit']=m.load(m.PROOF/'inherited-input-unit.json')
    v['elf_archives_downloaded']=0;v['original_fixture_regenerations']=0
    v['new_source_scope']='only native trace/runner; fixed candidate and ARM untouched'
    m.write(path,v)


def record():
    m.record()
    old='新規入力拒否10試験（旧14試験は失敗run35736673504の成功部分を継承）'
    new='14+10試験は保存済み成功部分を継承（今回再実行0、2件の失敗原本を保持）'
    for name in ('design/run_log.md','design/version_log.md'):
        path=ROOT/name;s=path.read_text(encoding='utf-8')
        m.need(s.count(old)==1,'new log description count');path.write_text(s.replace(old,new),encoding='utf-8')


if __name__=='__main__':
    m.CODE|=CODE
    actions={'verify':verify,'record':record,'guard':m.guard,'paths':lambda:print('\n'.join(sorted(m.owned())))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_rom_followup.py verify|record|guard|paths')
    try:actions[sys.argv[1]]()
    except Exception as exc:
        m.PROOF.mkdir(parents=True,exist_ok=True)
        m.write(m.PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
            'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
