#!/usr/bin/env python3
"""二次診断ログの原本空白を保持。成功native5/unit22+8は再実行しない。"""
from __future__ import annotations
import io, os, sys, zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_research_lifecycle_record as r
SELF='scripts/pr16_research_lifecycle_publication.py'
r.NEW.add(SELF)
_original_member=r.public_member
_original_run=r.subprocess.run
_original_publish=r.publish


def public_member(name,raw):
    mapped,content=_original_member(name,raw)
    if name=='index-guard.txt':
        content=r.m.encode({'encoding':'utf-8','original_name':name,'original_binding':r.identity(raw),'text':raw.decode('utf-8')})
        value=r.m.old.load(content)
        r.need(value['text'].encode('utf-8')==raw and r.identity(value['text'].encode())==value['original_binding'],'secondary diagnostic exact roundtrip')
        r.need(all(line==line.rstrip() for line in content.splitlines()),'secondary diagnostic no trailing spaces')
        return 'index-guard.original.json',content
    return mapped,content


def run(command,*args,**kwargs):
    if command[-1:]!=['test_pr16_research_lifecycle_record.py']:
        return _original_run(command,*args,**kwargs)
    # 原テスト/原モジュールが変わっていないことをgit objectで確認する。
    head='5b022269c72ddac7fbf0c9a8730921deba3b01df'
    for p in (r.SELF,r.TEST):
        raw=r.d.inputs.api('contents/'+p+'?ref='+head)
        import base64
        r.need(base64.b64decode(raw['content'])==(r.ROOT/p).read_bytes(),'reused eight-test dependency '+p)
    raw=r.d.inputs.api('actions/artifacts/10903084249/zip',True)
    r.need(r.identity(raw)=={'size':1102,'sha256':'17c12275060bb889fa508a22a468b39f4e4ccfc78d97dc2851f38920005e7e07'},'eight-test original archive')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        r.need(len(z.infolist())==4 and 'record-unit.txt' in z.namelist(),'eight-test archive members')
        unit=z.read('record-unit.txt')
    r.need(unit.count(b' ... ok\n')==8 and b'\nOK\n' in unit,'eight-test original PASS')
    # 新しく追加した二次診断経路のみ2種類の原本を検査する。
    for original in (b'++      | \n',b'normal\n\t \n'):
        name,data=public_member('index-guard.txt',original)
        r.need(name=='index-guard.original.json' and r.m.old.load(data)['text'].encode()==original,'new secondary mapping check')
    return r.subprocess.CompletedProcess(command,0,unit,b'')


def publish(cp,mode,owned):
    cp['new_unit_tests']=0;cp['reused_unit_tests']=30;cp['new_secondary_mapping_checks']=2
    cp['previous_publication_failure']=36234251833
    _original_publish(cp,mode,owned)
    for path in r.d.LOGS:
        with (r.ROOT/path).open('a',encoding='utf-8') as f:
            f.write('- Publication correction: 上記公開写像8試験はrun36234251833の成功原本を再利用（今回新unit0）。今回追加の二次診断写像2検査のみ実行。元の末尾空白を持つindex-guardもJSON文字列で可逆保存し、既存原本hashは不変。native再実行0。\n')


r.public_member=public_member
r.subprocess.run=run
r.publish=publish
if __name__=='__main__':
    if sys.argv[1:]==['record']:r.record()
    elif sys.argv[1:]==['finalize']:r.finalize()
    elif sys.argv[1:]==['guard']:r.d.guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(r.d.read(r.OUT/'owned.json')))
    else:raise SystemExit('usage: record|finalize|guard|paths')
