#!/usr/bin/env python3
"""producer/guard/upload/consumerの閉じた契約。空dirをuploadまで流さない。"""
import json,re
from pathlib import Path

def need(x,m):
 if not x:raise ValueError(m)
def contract(root,workflow,public,artifact,producer):
 root=Path(root);public=Path(public);s=(root/workflow).read_text();needle='uses: actions/upload-artifact@v4';need(s.count(needle)==1,'one explicit upload action');block=s.split(needle,1)[1]
 def scalar(key):
  got=re.findall(r'^          '+re.escape(key)+r': ([^\n]+)$',block,re.M);need(len(got)==1,'one upload '+key);return got[0].strip()
 need(scalar('path')==public.relative_to(root).as_posix(),'producer output directory exactly equals upload path')
 need(scalar('name')==artifact,'consumer artifact name exactly equals upload name')
 need(s.count('run: python3 -B '+producer+' export')==1 and s.count('id: publication_guard')==1,'one matching producer export guard')
 need("if: ${{ always() && steps.publication_guard.outcome == 'success' }}"in block,'upload only after successful producer guard')
 need(scalar('if-no-files-found')=='error','empty upload cannot succeed')
 return dict(producer=producer,directory=public.relative_to(root).as_posix(),artifact=artifact,workflow=workflow)
def output(public,success='measurement.json',failure='failure.json'):
 p=Path(public);need(p.is_dir()and not p.is_symlink(),'producer directory exists before upload')
 files=[f for f in p.rglob('*')if f.is_file()and not f.is_symlink()];need(files and any(f.stat().st_size for f in files),'nonempty produced files before upload')
 reports=[p/n for n in(success,failure)if n and(p/n).is_file()];need(reports,'one success or diagnostic report before upload')
 for f in reports:need(f.stat().st_size>0,'report is not empty');json.loads(f.read_bytes())
 return len(files)
def consumer(metadata,name,run):
 need(metadata['name']==name and metadata['workflow_run']['id']==run and not metadata['expired'],'exact named producer artifact and run')
