#!/usr/bin/env python3
"""PLA1と新規consumerだけを照合。既受入host/ARM/native/原本生成は呼ばない。"""
from __future__ import annotations
import ctypes as c
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from tools import pr16_learnset_supply as m
WORK=ROOT/'.local/pr16-learnset-supply'
TASK='USER-20260922-LEARNSET-SUPPLY'
CP='content/modernization/pr16_learnset_compact_checkpoint.json'
CODE=('tools/pr16_learnset_supply.py','src/modernization/pr16_learnset_supply.h',
      'src/modernization/pr16_learnset_supply.c','src/modernization/pr16_learnset_supply_game.h',
      'src/modernization/pr16_learnset_supply_game.c','tests/fixtures/pr16_learnset_supply_bindings.h',
      'tests/fixtures/pr16_learnset_supply_fixture.c','tests/test_pr16_learnset_supply.py',
      'scripts/pr16_learnset_supply_verify.py','.github/workflows/pr16-learnset-supply.yml',
      'src/modernization/pr16_learnset_runtime.h','src/modernization/pr16_learnset_owner.h')


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')


def load(path):return json.loads(path.read_bytes())


def command(args,path,env=None):
    run=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=240,env=env)
    path.write_bytes(run.stdout+run.stderr)
    m.need(run.returncode==0,'工程失敗: '+str(args[:3]))
    return run.stdout


def restore():
    from pr16_learnset_floette_verify import download
    from pr16_learnset_payload_verify import completed_run,current_pr
    current_pr(os.environ['GITHUB_SHA'])
    compact=load(ROOT/CP)
    completed_run(compact['run_id'],compact['source_head'],'.github/workflows/pr16-learnset-compact-bound.yml','compact-bound')
    for name,binding in compact['verification']['code_bindings'].items():
        m.need(m.identity((ROOT/name).read_bytes())==binding,'受入source変更: '+name)
    for phase,target in (('payload','parent'),('floette','floette')):
        cp=load(ROOT/('content/modernization/pr16_learnset_'+phase+'_checkpoint.json'))
        members=dict(cp['summary']['files'],**{'receipt.json':cp['proof_bindings']['receipt.json']})
        download(cp['payload_artifact'],cp['source_head'],WORK/target,members)
    download(compact['artifacts']['pr16-learnset-compact-native-data'],compact['source_head'],
             WORK/'compact',compact['verification']['data_files'])
    return compact


def compose(destination):
    destination.mkdir()
    rows,policies=m.accepted_rows(WORK/'parent',WORK/'floette')
    image,receipt=m.compose(rows,policies)
    (destination/'archive-image.bin').write_bytes(image)
    write(destination/'archive-receipt.json',receipt)


def audit(image):
    """oracleは元index/spanを直接読む。圧縮器/validateの復号結果は使わない。"""
    spec=importlib.util.spec_from_file_location('new_supply_tests',ROOT/'tests/test_pr16_learnset_supply.py')
    t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
    rows={(r['species_id'],r['consumer']):r for r in map(json.loads,(WORK/'floette/consumer-index.jsonl').read_text().splitlines())}
    policies=(WORK/'floette/owner-policies.bin').read_bytes()
    pools={folder:{p.name:p.read_bytes() for p in (WORK/folder).glob('*.bin')} for folder in ('parent','floette')}
    encoded=(t.U8*len(image)).from_buffer_copy(image)
    queries={'decode':0,'pages':0,'tutor_bits':0}
    with tempfile.TemporaryDirectory(dir=WORK) as temp:
        dll=t.library(temp)
        for sid,policy in enumerate(policies):
            for family,name in enumerate(m.FAMILIES):
                row=rows[sid,name];pool=pools['floette' if sid==1029 else 'parent']
                out=(t.U16*162)(*([0xbeef]*162));count=t.U16(0xcafe)
                code=dll.Pr16SupplyDecode(encoded,len(image),sid,family,out,160,c.byref(count));queries['decode']+=1
                if policy!=1:
                    m.need(code==0 and count.value==0xcafe and list(out)==[0xbeef]*162,'188ownerの漏洩')
                    continue
                a=row['archive'];source=pool[a['file']][a['offset']:a['offset']+a['size']]
                want=tuple(x[0] for x in struct.iter_unpack('<H',source))
                m.need(code==1 and count.value==len(want) and list(out)==list(want)+[0xbeef]*(162-len(want)),
                       'C/source順序/終端不一致')
                for known in ((0,0,0,0),tuple((list(want[:4])+[0]*4)[:4])):
                    k=(t.U16*4)(*known)
                    for mode in ((2,3,4,5,6) if family==0 else (7,)):
                        for gate in (0,1):
                            result=(t.U16*42)(*([0xbeef]*42))
                            n=dll.Pr16SupplyPage(out,len(want),k,mode,gate,result,40);queries['pages']+=1
                            selected=want if mode in (2,7) else want[(mode-3)*40:(mode-2)*40]
                            expected=[v for v in selected if v not in known] if gate else []
                            if mode==2:expected=expected[:1]
                            m.need(n==len(expected) and list(result)==expected+[0xbeef]*(42-len(expected)),
                                   'raw page/known/gate/C canary不一致')
            row=rows[sid,'tutor'];p=row['payload']
            bits=bytes(16) if p is None else pools['floette' if sid==1029 else 'parent'][p['file']][p['offset']:p['offset']+p['size']]
            buffer=(t.U8*16).from_buffer_copy(bits);view=t.View(buffer,64 if policy==1 else 0,sid)
            for slot in range(64):
                expected=(bits[slot//8]>>(slot%8))&1 if policy==1 else 0
                m.need(dll.Pr16SupplyTutorBit(c.byref(view),sid,slot)==expected,'新規Tutor bit consumer不一致')
                queries['tutor_bits']+=1
        m.need(bytes(encoded)==image,'C入力image書換え')
    return {'status':'PASS_NEW_SUPPLY_C_AGAINST_ACCEPTED_ARCHIVE_SPANS','queries':queries,
        'total_queries':sum(queries.values()),'owners':1671,'identity_only_owners':188,
        'source_order_equal':True,'raw_pages_before_known_filter':True,'hall_of_fame_gate_checked':True,
        'input_unchanged':True,'scope':'HOST_CONSUMERS_NOT_REAL_ROM_OR_GAMEPLAY_ACCEPTANCE'}


def verify():
    WORK.mkdir(parents=True);proof=WORK/'proof';proof.mkdir()
    compact=restore()
    paths=[ROOT/n for n in CODE]+[p for folder in ('parent','floette','compact') for p in (WORK/folder).iterdir()]
    before={str(p):(m.identity(p.read_bytes()),p.stat().st_mtime_ns) for p in paths}
    command([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_supply','-v'],proof/'unit.txt')
    m.need((proof/'unit.txt').read_bytes().count(b' ... ok\n')==30,'新規30試験数不一致')
    for seed in (11,29):
        command([sys.executable,'-B',__file__,'compose',str(WORK/('build'+str(seed)))],
                proof/('compose'+str(seed)+'.txt'),dict(os.environ,PYTHONHASHSEED=str(seed)))
    first=WORK/'build11';second=WORK/'build29'
    for name in ('archive-image.bin','archive-receipt.json'):
        m.need((first/name).read_bytes()==(second/name).read_bytes(),'独立PLA1生成不一致')
    image=(first/'archive-image.bin').read_bytes();receipt=load(first/'archive-receipt.json')
    m.need(m.identity(image)=={'size':21383,'sha256':'499714cc04fd43ecb59ac45d8d23dad6badbc0137189c4fbcb8facbe13c46d13'},
           'local/Actions PLA1不一致')
    result=audit(image);write(proof/'host-audit.json',result)
    from tools.pr16_learnset_runtime import free_span
    plan=load(WORK/'compact/link.json')['allocation']
    at,region=free_span(plan,len(image))
    allocation={'planned_data_offset':at,'region':region,'size':len(image),
        'reservation_modified':False,'rom_written':False,'arm_code_size_unverified':True,
        'remaining_allocatable_bytes_before':plan['summaries']['remaining_allocatable_bytes']}
    write(proof/'allocation-plan.json',allocation)
    after={str(p):(m.identity(p.read_bytes()),p.stat().st_mtime_ns) for p in paths}
    m.need(before==after,'固定source/入力byte/mtime変更')
    command([sys.executable,'-B','scripts/pr16_resume.py','check'],proof/'resume.json')
    command([sys.executable,'-B','scripts/validate_task_graph.py'],proof/'task-graph.txt')
    command(['git','diff','--exit-code'],proof/'tracked-diff.txt')
    data=WORK/'data';data.mkdir()
    for name in ('archive-image.bin','archive-receipt.json'):shutil.copyfile(first/name,data/name)
    write(proof/'verification.json',{'task':TASK,'status':'PASS_PLA1_HOST_SUPPLY_CONSUMERS',
        'scope':result['scope'],'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'parent_candidate':compact['candidate'],'parent_run':compact['run_id'],
        'new_tests':30,'new_host_queries':result['total_queries'],'audit':result,'receipt':receipt,
        'allocation_plan':allocation,'independent_new_archive_images_match':True,
        'accepted_tests_rerun':0,'accepted_native_reruns':0,'accepted_source_regenerations':0,
        'accepted_payload_regenerations':0,'old_arm_compiles':0,'new_arm_compiles':0,'new_native_processes':0,
        'input_byte_mtime_unchanged':True,'game_tutor_connected':False,'archive_rebound':False,
        'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
        'active_baseline_changed':False,'release_ready':False,
        'code_bindings':{name:m.identity((ROOT/name).read_bytes()) for name in CODE},
        'data_files':{p.name:m.identity(p.read_bytes()) for p in data.iterdir()},
        'proof_files':{p.name:m.identity(p.read_bytes()) for p in proof.iterdir()}})
    print(json.dumps({'status':'PASS_PLA1_HOST_SUPPLY_CONSUMERS','image':m.identity(image),'queries':result['total_queries']}))


if __name__=='__main__':
    if sys.argv[1:]==['verify']:
        try:verify()
        except Exception as exc:
            (WORK/'proof').mkdir(parents=True,exist_ok=True)
            write(WORK/'proof/failure.json',{'status':'FAIL','error':str(exc).replace(str(ROOT),'$REPO')})
            raise
    elif len(sys.argv)==3 and sys.argv[1]=='compose':compose(Path(sys.argv[2]))
    else:raise SystemExit('usage: pr16_learnset_supply_verify.py verify|compose NEW_DIRECTORY')
