"""失敗前の14試験を継承し、固定release cacheから診断用ELFだけ読む。"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
HEAD='f35047e4ccd2809c5ac0b9bb66a60c47cbb639b7'
RUN=35736673504
ARCHIVE={'name':'pokemon-vega-private-env-v1-build-cache.zip','size':724902234,
    'sha256':'bf1053779eb1301d324c8f192d00ca07a1a830c734e3a05034f0bd90f46f143f'}
ELF={'member':'build/battle-core/9215826454ee6023888d2f53d33b662d21a340af868c92637aae2c5c191c5717/run-1/linked.o',
     'size':5733212,'sha256':'52bbd57a7d2649164c4706ee45dc17ef1f8357862d8dbd79bdcd439c2b0a36fb'}
ARTIFACT={'id':10697942530,'name':'pr16-learnset-supply-rom-proof','size_in_bytes':933,
    'digest':'sha256:4fa72edef2032c9cbb70cf347ffe5e0f2a896b19293c5fb2ca5f95038d54c02a'}
MEMBERS={'unit.stderr.txt':{'size':1719,'sha256':'cb48f706fb12e4c2830fd37093f04af5f9216c25e2bdbf6f4bd5c76b7384ae04'},
    'unit.stdout.txt':{'size':0,'sha256':'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'},
    'failure.json':{'size':268,'sha256':'0079edf06839517cb4815d47764dc1b69704cf836de9b698d89f17b4563e5b30'}}


def need(ok, why):
    if not ok: raise ValueError(why)


def identity(raw): return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def encode(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()


def validate_metadata(snapshot, config):
    need({k:snapshot['elf'][k] for k in ELF}==ELF,'ELF receipt mismatch')
    a=[x for x in snapshot['archives'] if x['name']==ARCHIVE['name']]
    b=[x for x in config['archives'] if x['name']==ARCHIVE['name']]
    need(len(a)==len(b)==1 and all({k:r[k] for k in ARCHIVE}==ARCHIVE for r in a+b),'cache receipt mismatch')
    need(config['release']['tag']=='private-environment-v1','release tag mismatch')


def member(archive, binding):
    name=binding['member'];p=PurePosixPath(name)
    need(not p.is_absolute() and '..' not in p.parts and '\\' not in name,'unsafe member path')
    need(archive.namelist().count(name)==1,'ELF missing/duplicate member')
    info=archive.getinfo(name)
    need(not info.is_dir() and info.external_attr>>28!=0xA and info.file_size==binding['size']<=32000000,'ELF member kind/size')
    raw=archive.read(info)
    need(identity(raw)=={k:binding[k] for k in ('size','sha256')},'ELF member hash')
    return raw


def load_elf(work, proof):
    snapshot=json.loads((ROOT/'content/modernization/pr16_candidate_wiki_saved_link_sources.json').read_bytes())
    config=json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    validate_metadata(snapshot,config)
    folder=work/'saved-elf';folder.mkdir()
    subprocess.run(['gh','release','download',config['release']['tag'],'--repo','dekaazarashi1111-web/pokemon-vega-modern',
        '--pattern',ARCHIVE['name'],'--dir',str(folder)],check=True,cwd=ROOT,
        env=dict(os.environ,GH_TOKEN=os.environ['GITHUB_TOKEN']),timeout=360)
    path=folder/ARCHIVE['name'];hasher=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):hasher.update(block)
    need(path.stat().st_size==ARCHIVE['size'] and hasher.hexdigest()==ARCHIVE['sha256'],'cache archive bytes')
    with zipfile.ZipFile(path) as archive: raw=member(archive,ELF)
    (proof/'elf-restore.json').write_bytes(encode({'status':'PASS_FIXED_CACHE_MEMBER','archive':ARCHIVE,'elf':ELF,
        'new_arm_compiles':0,'new_arm_links':0,'original_paths_written':0}))
    return raw


def inherited(proof):
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_floette_verify import download
    run=fetch('actions/runs/'+str(RUN))
    need(run['head_sha']==HEAD and run['status']=='completed' and run['conclusion']=='failure'
        and run['path']=='.github/workflows/pr16-learnset-supply-rom.yml','failed predecessor mismatch')
    # Only tested functions are inherited; orchestration/ELF acquisition is new and separately tested.
    tested='tests/test_pr16_learnset_supply_rom.py'
    need((ROOT/tested).read_bytes()==subprocess.check_output(['git','show',HEAD+':'+tested],cwd=ROOT),'inherited tests changed')
    source='scripts/pr16_learnset_supply_rom.py'
    def functions(raw):
        tree=ast.parse(raw)
        return {n.name:ast.dump(n,include_attributes=False) for n in tree.body
            if isinstance(n,ast.FunctionDef) and n.name in ('choose','validate_native')}
    need(functions((ROOT/source).read_bytes())==functions(subprocess.check_output(['git','show',HEAD+':'+source],cwd=ROOT)),'inherited tested functions changed')
    dest=proof.parent/'first-failure';download(ARTIFACT,HEAD,dest,MEMBERS)
    err=(dest/'unit.stderr.txt').read_bytes();failure=json.loads((dest/'failure.json').read_bytes())
    need(err.count(b' ... ok\n')==14 and b'Ran 14 tests' in err and err.rstrip().endswith(b'OK')
         and not (dest/'unit.stdout.txt').read_bytes() and failure['source_head']==HEAD
         and failure['run_id']==str(RUN) and failure['status']=='FAIL'
         and 'No such file or directory' in failure['error'] and ELF['member'] in failure['error'],'first proof scope mismatch')
    for name in MEMBERS:(proof/('first-'+name)).write_bytes((dest/name).read_bytes())
    receipt={'run_id':RUN,'source_head':HEAD,'whole_run_conclusion':'failure','scoped_tests_passed':14,
        'tests_rerun':0,'new_native_processes':0,'failure_reason':'saved ELF missing before host compile/native',
        'artifact':ARTIFACT,'members':MEMBERS}
    (proof/'inherited-unit.json').write_bytes(encode(receipt))
    return receipt
