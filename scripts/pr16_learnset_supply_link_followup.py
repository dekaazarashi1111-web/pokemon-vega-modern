#!/usr/bin/env python3
"""初回14試験を保存原本から継承し、未成功のARMリンクだけを修復する。"""
from __future__ import annotations
import base64
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
import pr16_learnset_supply_link as m
from pr16_wiki_reconcile import fetch
HEAD='1bb993d81ba08e5633e79cd67992a1326b4607da'
RUN=35731723699
MEMORY='src/modernization/pr16_learnset_supply_memory.S'
ARTIFACT={'id':10695524890,'name':'pr16-learnset-supply-link-proof','size_in_bytes':1078,
 'digest':'sha256:d03eb5c1988396606ec931cf772554b03554b1b1d7ac3a8979fd661896d0097b'}
MEMBERS={'failure.json':{'size':671,'sha256':'26f12a3e7610ecc09e6b8f3aabbe64d7e89c4f9dbb17c8a8a28987beea656caf'},
 'unit.txt':{'size':2251,'sha256':'8e65182e5af5e40c922a78f7dbcddc20c1a160eb60cfb0d20233e12d9e892853'}}
original_command=m.command


def command(args,destination=None):
    if args[1:]==['-B','-m','unittest','tests.test_pr16_learnset_supply_native','-v']:
        run=fetch('actions/runs/'+str(RUN))
        m.need(run['head_sha']==HEAD and run['conclusion']=='failure' and run['status']=='completed','失敗原本を成功へ改作しない')
        for name in m.CODE:
            if name.startswith('src/') or name=='tests/test_pr16_learnset_supply_native.py':
                if name==MEMORY:continue
                old=fetch('contents/'+name+'?ref='+HEAD)
                m.need(old['encoding']=='base64' and base64.b64decode(old['content'])==(ROOT/name).read_bytes(),'継承14試験の入力変更: '+name)
        folder=m.WORK/'previous'
        m.saved.download(ARTIFACT,HEAD,folder,MEMBERS)
        unit=(folder/'unit.txt').read_bytes()
        m.need(unit.count(b' ... ok\n')==14 and b'Ran 14 tests' in unit and unit.rstrip().endswith(b'OK'),'保存14試験不一致')
        failure=json.loads((folder/'failure.json').read_bytes())
        m.need(failure['status']=='FAIL' and "undefined reference to `memset'" in failure['error'],'初回停止点不一致')
        destination.write_bytes(unit)
        m.write(m.WORK/'proof/inherited-unit.json',{'run_id':RUN,'source_head':HEAD,'whole_run_conclusion':'failure',
            'scoped_tests_passed':14,'tests_rerun':0,'artifact':ARTIFACT,'members':MEMBERS})
        return unit
    if '-c' in args and any(str(a).endswith('/original_tutor.S') for a in args):
        name=next(a for a in args if str(a).endswith('/original_tutor.S'))
        path=ROOT/name
        body=path.read_bytes()
        m.need(b'Pr16SupplyMemset' not in body,'memset重複追加')
        path.write_bytes(body+b'\n'+(ROOT/MEMORY).read_bytes())
    return original_command(args,destination)


def main():
    m.CODE += (MEMORY,'scripts/pr16_learnset_supply_link_followup.py','.github/workflows/pr16-learnset-supply-link-followup.yml')
    m.command=command
    m.verify()
    path=m.WORK/'proof/verification.json';report=json.loads(path.read_bytes())
    report['new_tests']=0;report['inherited_scoped_tests']=14
    report['failed_predecessor']={'run_id':RUN,'source_head':HEAD,'conclusion':'failure','new_arm_compiles':4,
        'new_arm_link_attempts':1,'new_native_processes':0,'reason':'memset未解決。新規14試験は成功。'}
    report['arm_memory_helper_added']=MEMORY
    m.write(path,report)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        (m.WORK/'proof').mkdir(parents=True,exist_ok=True)
        m.write(m.WORK/'proof/failure.json',{'status':'FAIL','error':str(exc).replace(str(ROOT),'$REPO')})
        raise
