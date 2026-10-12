#!/usr/bin/env python3
"""配置16試験を継承し、欠落していた明示owner2件だけfixtureへ追加。"""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_supply_rom_alignment as a
m,f=a.m,a.f
RUN=35747048291
HEAD='29cb7ce3660554b30dff7a8178b10b24c6e863b7'
ARTIFACT={'id':10703635710,'name':'pr16-learnset-supply-rom-proof','size_in_bytes':55047,
          'digest':'sha256:9b5bd7cac2f5219ecc424e5b523e1a9b18dc5aacb3fe9e1fa2d31c543d75b18c'}
CODE={'scripts/pr16_supply_coverage_followup.py','tools/mgba_pr16_supply_coverage.c'}
SAVED=m.WORK/'coverage-failure'
original_previous=a.previous_failure
original_command=m.command
original_samples=f.samples
cached=None


def inherit():
    old=original_previous()
    run=a.fetch('actions/runs/'+str(RUN))
    m.need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure'
           and run['path']=='.github/workflows/pr16-learnset-supply-rom.yml','coverage source run')
    meta=a.fetch('actions/artifacts/'+str(ARTIFACT['id']))
    m.need(all(meta[k]==v for k,v in ARTIFACT.items()) and not meta['expired']
           and meta['workflow_run']['head_sha']==HEAD,'coverage artifact identity')
    raw=a.fetch('actions/artifacts/'+str(ARTIFACT['id'])+'/zip',binary=True)
    m.need(m.identity(raw)=={'size':ARTIFACT['size_in_bytes'],'sha256':ARTIFACT['digest'][7:]},'coverage ZIP digest')
    SAVED.mkdir()
    members={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        m.need(len(z.namelist())==len(set(z.namelist())) and len(z.namelist())<=128,'coverage ZIP set')
        for info in z.infolist():
            n=info.filename
            m.need(Path(n).name==n and not info.is_dir() and info.external_attr>>28!=0xA
                   and info.file_size<2000000,'coverage ZIP path/size')
            data=z.read(n);members[n]=m.identity(data);(SAVED/n).write_bytes(data)
    unit=(SAVED/'placement-unit.stderr.txt').read_bytes()
    m.need(unit.count(b' ... ok\n')==16 and b'Ran 16 tests' in unit and unit.rstrip().endswith(b'OK')
           and not (SAVED/'placement-unit.stdout.txt').read_bytes(),'inherited placement tests')
    for name in ('scripts/pr16_supply_elf_placement.py','tests/test_pr16_supply_elf_placement.py'):
        m.need((ROOT/name).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+name],cwd=ROOT),'placement test source changed')
    fail=m.load(SAVED/'failure.json');trace=(SAVED/'native11.stderr.txt').read_bytes()
    m.need(fail['source_head']==HEAD and fail['run_id']==str(RUN) and fail['status']=='FAIL'
           and 'vacuous coverage or mGBA warning/error' in fail['error']
           and b'sample=25 species=65535' in trace,'coverage failure boundary')
    for name in ('failure.json','native11.stderr.txt','native11.stdout.txt','placement-unit.stderr.txt',
                 'placement-unit.stdout.txt','placement.json','alignment-link.json'):
        (m.PROOF/('coverage-prior-'+name)).write_bytes((SAVED/name).read_bytes())
    m.write(m.PROOF/'inherited-placement.json',{'run_id':RUN,'source_head':HEAD,'artifact':ARTIFACT,'members':members,
        'whole_run_conclusion':'failure','scoped_tests_passed':16,'tests_rerun':0,'prior_native_processes':1,
        'prior_native_accepted':False,'prior_stop':'26 owners complete, final positive coverage missing',
        'reason_ja':'26旧fixtureにbit0/1の特殊Tutor許可ownerがない。原本280/855を追加し、正例条件を緩めず再検証。'})
    return old


def command(args,name,env=None):
    if name=='placement-unit':
        m.need(args[1:]==['-B','-m','unittest','tests.test_pr16_supply_elf_placement','-v'],'placement command exact')
        for suffix in ('stdout.txt','stderr.txt'):
            (m.PROOF/(name+'.'+suffix)).write_bytes((SAVED/(name+'.'+suffix)).read_bytes())
        return b''
    if name=='native-compile':
        m.need(args.count('tools/mgba_pr16_learnset_supply.c')==1,'native compiler source')
        args=[('tools/mgba_pr16_supply_coverage.c' if x=='tools/mgba_pr16_learnset_supply.c' else x) for x in args]
    return original_command(args,name,env)


def replay(candidate,link,elf,raw):
    global cached
    if cached is not None:return cached
    report=m.load(SAVED/'alignment-link.json');mapping=report['placement_repair']
    m.need(m.identity(candidate)==report['repair_parent']==a.OLD and m.identity(elf)==mapping['elf']
           and m.identity(raw)==mapping['objcopy'] and report['hooks']==link['hooks']
           and report['symbols']==link['symbols'],'saved repair inputs')
    start,end=mapping['repair_start'],mapping['repair_end_exclusive']
    image=b'\xff'*mapping['prefix_bytes']+raw
    m.need(mapping['prefix_bytes']==4 and end-start==len(image) and m.identity(image)==mapping['placed_image']
           and candidate[start:start+len(raw)]==raw and candidate[start+len(raw):end]==b'\xff'*4,'saved repair bytes')
    out=candidate[:start]+image+candidate[end:]
    m.need(m.identity(out)==report['candidate'],'saved successor identity')
    cached=(out,report,image)
    return cached


def samples(bindings):
    count=original_samples(bindings)
    old_header=(m.WORK/'pr16_supply_samples.h').read_bytes()
    manifest=m.load(m.PROOF/'fixture-manifest.json')
    cp=m.load(ROOT/(m.BASE+'pr16_learnset_payload_checkpoint.json'))
    folder=m.WORK/'extra-owner-source'
    members=dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
    a.download(cp['payload_artifact'],cp['source_head'],folder,members)
    index={(r['species_id'],r['consumer']):r for r in map(json.loads,(folder/'consumer-index.jsonl').read_text().splitlines())}
    catalogs=m.load(folder/'catalogs.json')['tutor']['slots']
    additions=[];source=[]
    for sid,key,bit,move in ((280,'SPECIES_KEY_MAWILE',1,783),(855,'SPECIES_KEY_DRUDDIGON',0,399)):
        t=index[sid,'tutor'];p=t['payload']
        m.need(t['species_key']==key and t['status']=='PAYLOAD_PREPARED_NOT_INSTALLED'
               and p['file']=='tutor.bin' and p['size']==16,'explicit extra owner')
        span=(folder/p['file']).read_bytes()[p['offset']:p['offset']+p['size']]
        bits=int.from_bytes(span,'little')
        m.need(len(span)==16 and span[8:]==b'\0'*8 and bits>>bit&1
               and any(r['bit_index']==bit and r['move_id']==move for r in catalogs),'positive source tutor bit')
        row={'species':sid,'policy':1,'bits':bits}
        for family in ('machine','tutor'):
            record=index[sid,family];p=record['archive']
            m.need(record['species_key']==key and record['status']=='PAYLOAD_PREPARED_NOT_INSTALLED'
                   and p['file']==family+'_archive.bin','extra archive identity')
            raw=(folder/p['file']).read_bytes()[p['offset']:p['offset']+p['size']]
            m.need(len(raw)==p['size']==p['moves']*2,'extra archive span')
            row[family]=[x[0] for x in struct.iter_unpack('<H',raw)]
            source.append({'species':sid,'consumer':family,'row':record,'archive_span':m.identity(raw)})
        additions.append(row)
    m.need(not {r['species'] for r in additions}&set(manifest['owners']),'duplicate extra owner')
    text=[]
    for r in additions:
        vals=','.join(map(str,(r['species'],r['policy'],len(r['machine']),len(r['tutor']))))
        text.append('{'+vals+',UINT64_C('+hex(r['bits'])+'),{'+(','.join(map(str,r['machine'])) or '0')+'},{'+(','.join(map(str,r['tutor'])) or '0')+'}},')
    m.need(old_header.endswith(b'};\n'),'fixture array suffix')
    header=old_header[:-3]+('\n'.join(text)+'\n};\n').encode()
    (m.WORK/'pr16_supply_samples.h').write_bytes(header)
    manifest.update(samples=count+len(additions),owners=manifest['owners']+[r['species'] for r in additions],
                    cases=manifest['cases']+additions,header=m.identity(header),inherited_26_header=m.identity(old_header))
    m.write(m.PROOF/'fixture-manifest.json',manifest)
    m.write(m.PROOF/'extra-owner-fixture.json',{'source_head':cp['source_head'],'source_run':cp['run_id'],
        'artifact':cp['payload_artifact'],'members':members,'cases':additions,'source_spans':source,
        'original_26_cases_unchanged':True,'new_original_span_fixtures':2,'source_or_payload_regenerations':0})
    return manifest['samples']


def verify():
    a.previous_failure=inherit;a.repair=replay;m.command=command;f.samples=samples
    a.verify()
    p=m.PROOF/'verification.json';v=m.load(p)
    v.update(new_tests=0,inherited_tests=40,placement_reproductions=0,saved_candidate_replays=1,
             new_original_span_fixtures=2,inherited_placement=m.load(m.PROOF/'inherited-placement.json'),
             new_source_scope='original fixture adds explicit special-positive owners 280 and 855; no ROM/code change')
    m.write(p,v)


def record():
    a.record()
    old='run'+os.environ['GITHUB_RUN_ID']+'、新16試験PASS、保存ELFの独立2配置一致'
    new='run'+os.environ['GITHUB_RUN_ID']+'、保存run35747048291の16配置試験/独立2配置一致を継承（今回再実行0）、旧26owner行は不変・正本280/855の2fixture追加'
    for name in ('design/run_log.md','design/version_log.md'):
        p=ROOT/name;text=p.read_text(encoding='utf-8');m.need(text.count(old)==1,'log current segment')
        p.write_text(text.replace(old,new),encoding='utf-8')


if __name__=='__main__':
    a.CODE|=CODE;a.SOURCE|=CODE
    actions={'verify':verify,'record':record,'guard':a.guard,'paths':lambda:print('\n'.join(sorted(a.owned())))}
    if len(sys.argv)!=2 or sys.argv[1] not in actions:raise SystemExit('usage: supply_coverage_followup.py verify|record|guard|paths')
    try:actions[sys.argv[1]]()
    except Exception as exc:
        m.PROOF.mkdir(parents=True,exist_ok=True)
        m.write(m.PROOF/'failure.json',{'status':'FAIL','source_head':os.environ.get('GITHUB_SHA'),
                'run_id':os.environ.get('GITHUB_RUN_ID'),'error':str(exc).replace(str(ROOT),'$REPO')})
        raise
