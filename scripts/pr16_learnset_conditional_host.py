#!/usr/bin/env python3
"""条件consumerの新host監査と保存ABI採取。旧host/ARM/nativeを再実行しない。"""
from __future__ import annotations
import ctypes as c
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from tools import pr16_learnset_conditional as new
from tools import pr16_learnset_successor as s
import pr16_learnset_runtime_link as old
need = new.need
WORK = ROOT/'.local/pr16-learnset-conditional'
CODE = ('src/modernization/pr16_learnset_conditional.h', 'src/modernization/pr16_learnset_conditional.c',
        'tools/pr16_learnset_conditional.py', 'tests/test_pr16_learnset_conditional.py',
        'scripts/pr16_learnset_conditional_host.py', '.github/workflows/pr16-learnset-conditional.yml')


def write(path, data): path.write_bytes(s.encode(data))


def payloads():
    from pr16_learnset_floette_verify import download
    for directory, name in (('parent', new.prior.PARENT), ('floette', new.prior.FLOETTE)):
        cp = s.read_json(ROOT/name)
        members = dict(cp['summary']['files'], **{'receipt.json': cp['proof_bindings']['receipt.json']})
        download(cp['payload_artifact'], cp['source_head'], WORK/directory, members)


def restore_progress():
    """2段の保存binary/hookを適用するだけ。既存候補の再compile/検証はない。"""
    from pr16_learnset_floette_verify import download
    raw = old.materialize()
    reports = {}
    for phase, binary in (('runtime', 'runtime-bundle.bin'), ('progress', 'progress.bin')):
        cp = s.read_json(ROOT/f'content/modernization/pr16_learnset_{phase}_checkpoint.json')
        for name, binding in cp['verification']['code_bindings'].items(): s.bound(ROOT/name, binding)
        directory = WORK/phase
        download(cp['artifacts'][f'pr16-learnset-{phase}-data'], cp['source_head'], directory, cp['verification']['data_files'])
        report = s.read_json(directory/'link.json'); blob = (directory/binary).read_bytes()
        need(old.saved.identity(raw) == report['parent'] and old.saved.identity(blob) == report['bundle'], '保存候補の親/bundle不一致')
        at = report['start']; need(raw[at:at+len(blob)] == b'\xff'*len(blob), '保存候補の空間不一致')
        out = bytearray(raw); out[at:at+len(blob)] = blob
        for patch in report['hooks']:
            pos = patch['offset']; before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            need(raw[pos:pos+len(before)] == before and len(before) == len(after), '保存hook preimage不一致')
            out[pos:pos+len(after)] = after
        raw = bytes(out)
        need(old.saved.identity(raw) == report['candidate'] == cp['candidate'], '保存候補identity不一致')
        reports[phase] = report
    (WORK/'parent.gba').write_bytes(raw)
    return raw, reports


def audit(raw, parent, floette):
    """配置器のindexをoracleにせず、固定元spanと全owner/条件/levelを比較する。"""
    spec = importlib.util.spec_from_file_location('conditional_vectors', ROOT/'tests/test_pr16_learnset_conditional.py')
    t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
    rows = {(r['species_id'],r['consumer']):r for r in s.rows(floette/'consumer-index.jsonl')}
    policies = (floette/'owner-policies.bin').read_bytes()
    pools = {False:{p.name:p.read_bytes() for p in parent.glob('*.bin')}, True:{p.name:p.read_bytes() for p in floette.glob('*.bin')}}
    def span(sid, family):
        p = rows[sid,family]['payload']
        if p is None:return b''
        return pools[sid==1029][p['file']][p['offset']:p['offset']+p['size']]
    image = (c.c_uint8*len(raw)).from_buffer_copy(raw)
    queries = dict(spans=0,tutor=0,list=0,evolution=0,reminder=0)
    max_reminder=0
    with tempfile.TemporaryDirectory(dir=WORK) as temp:
        dll = t.library(temp)
        for sid,policy in enumerate(policies):
            views, expected = {}, {}
            for cid,family in zip(new.IDS,new.FAMILIES):
                v=t.View(); code=dll.Pr16ReadLearnsetConditional(image,len(raw),sid,cid,c.byref(v));queries['spans']+=1
                need(code == (1 if policy==1 else 2 if policy<5 else 3) and v.owner==sid, '実PLC1 owner不一致')
                want = span(sid,family)
                if policy==1 and family=='egg':
                    want=want[2:]
                    if want.endswith(b'\xff\xff'):want=want[:-2]
                expected[family]=want
                if policy==1:
                    count=64 if family=='tutor' else len(want)//2
                    need(v.count==count and c.string_at(v.bytes,len(want))==want, '実PLC1と元span不一致')
                else:need(not v.bytes and not v.count, '188保全ownerへのspan漏洩')
                views[family]=v
                if family!='tutor':
                    out=(c.c_uint16*52)(*([0xbeef]*52))
                    result=dll.Pr16ConditionalList(c.byref(v),None,0,out,50);queries['list']+=1
                    values=list(dict.fromkeys(x[0] for x in struct.iter_unpack('<H',want))) if policy==1 else []
                    need(result==len(values) and list(out)==values+[0xbeef]*(52-len(values)), '候補list/canary不一致')
            bits=int.from_bytes(expected['tutor'],'little') if policy==1 else 0
            for bit in range(64):
                need(dll.Pr16ConditionalTutorAllowed(image,len(raw),sid,bit)==((bits>>bit)&1), '既存tutor slot不一致');queries['tutor']+=1
            if policy!=1:continue
            levels=list(struct.iter_unpack('<HB',span(sid,'level_up')[:-3]));lv=t.view(levels,owner=sid,levels=True)
            evo=[x[0] for x in struct.iter_unpack('<H',expected['evolution'])]
            reminder=[x[0] for x in struct.iter_unpack('<H',expected['reminder'])]
            for level in range(1,101):
                want=evo+[m for m,l in levels if l==level];cursor=c.c_uint8(255)
                actual=[]
                for i in range(len(want)+1):
                    move=dll.Pr16ConditionalEvolutionNext(c.byref(views['evolution']),c.byref(lv),level,i==0,c.byref(cursor));queries['evolution']+=1
                    if move:actual.append(move)
                    else:break
                need(actual==want and move==0, '進化/同level順序・終端不一致')
                merged=list(dict.fromkeys(evo+[m for m,l in levels if l<=level]+reminder));max_reminder=max(max_reminder,len(merged))
                for known in ([0,0,0,0],(merged[:4]+[0]*4)[:4]):
                    k=(c.c_uint16*4)(*known);out=(c.c_uint16*42)(*([0xbeef]*42));expect=[m for m in merged if m not in known]
                    result=dll.Pr16ConditionalReminder(c.byref(views['evolution']),c.byref(lv),c.byref(views['reminder']),level,k,out,40);queries['reminder']+=1
                    need(result==len(expect) and list(out)==expect+[0xbeef]*(42-len(expect)), '思い出し/既習得/canary不一致')
        need(bytes(image)==raw, '入力image書換え')
    return {'status':'PASS_NEW_CONDITIONAL_C_ALL_OWNERS_100_LEVELS','owners':1671,'learning_owners':1483,
            'identity_only_preserved':188,'queries':queries,'total_queries':sum(queries.values()),'max_reminder_moves':max_reminder,
            'input_image_unchanged':True,'accepted_tests_rerun':0,'gameplay_e2e_accepted':False}


def context():
    """後続hook判断用のtracked sourceだけ保存する。ROM/ELF自体は出力しない。"""
    root=WORK/'context';root.mkdir();manifest={}
    names=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    with zipfile.ZipFile(root/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in names:
            if not (name.startswith(('overlays/modernization_p03','overlays/modernization_rockruff','tools/modernization_p03','generated/runtime/modernization_p03','generated/runtime/modernization_rockruff')) or name=='config/github_private_environment.json'):continue
            p=ROOT/name
            if p.suffix not in {'.c','.h','.S','.s','.py','.json'} or not p.is_file() or p.is_symlink():continue
            data=p.read_bytes();data.decode('utf-8');need(b'\0' not in data,'sourceはtextのみ')
            z.writestr(name,data);manifest[name]=s.identity(p)
    write(root/'manifest.json',manifest)
    raw,reports=restore_progress()
    evidence=s.read_json(ROOT/'content/modernization/pr16_candidate_wiki_saved_link_sources.json')
    elf_path=ROOT/evidence['elf']['member']; symbols={}
    if elf_path.is_file():
        need(s.identity(elf_path)=={k:evidence['elf'][k] for k in ('sha256','size')},'保存ELF固定hash不一致')
        from pr16_wiki_elf_symbols import Elf
        elf=Elf(elf_path.read_bytes())
        for name in ('GetEggMoves','GetAllEggMoves','GetMoveRelearnerMoves','CanMonLearnTutorMove','MonTryLearningNewMoveAfterEvolution','BuildEggMoveset'):
            bound=elf.bind(name,raw)
            if 'address' in bound:
                at=bound['address']-0x08000000;bound['candidate_body_hex']=raw[at:at+bound['size']].hex()
            symbols[name]=bound
    generated={}
    for name in manifest:
        if name.endswith('_symbols.json'):
            obj=s.read_json(ROOT/name)
            generated[name]=obj.get('symbols',obj)
    write(root/'abi.json',{'candidate':old.saved.identity(raw),'saved_elf_available':elf_path.is_file(),
        'elf':evidence['elf'],'symbols':symbols,'generated_symbols':generated,
        'fixed_entry_evolution':{'address':0x09114120,'preimage':raw[0x1114120:0x1114140].hex()},
        'new_native_runs':0,'old_arm_compiles':0})


def run():
    from pr16_learnset_payload_verify import current_pr
    current_pr(os.environ['GITHUB_SHA']);WORK.mkdir(parents=True)
    proof=WORK/'proof';proof.mkdir();data=WORK/'data';data.mkdir()
    run=subprocess.run([sys.executable,'-B','-m','unittest','tests.test_pr16_learnset_conditional','-v'],cwd=ROOT,capture_output=True)
    (proof/'unit.txt').write_bytes(run.stdout+run.stderr);need(run.returncode==0,'条件41試験失敗')
    payloads();raw,receipt=new.compose(ROOT,WORK/'parent',WORK/'floette')
    (data/'conditional-image.bin').write_bytes(raw);write(data/'receipt.json',receipt)
    report=audit(raw,WORK/'parent',WORK/'floette');write(proof/'host-audit.json',report)
    write(proof/'host-checkpoint.json',{'status':report['status'],'source_head':os.environ['GITHUB_SHA'],
        'run_id':int(os.environ['GITHUB_RUN_ID']),'focused_tests':41,'host_audit':report,
        'code_bindings':{n:s.identity(ROOT/n) for n in CODE},'data_files':{p.name:s.identity(p) for p in data.iterdir()},
        'new_native_runs':0,'old_arm_compiles':0,'gameplay_e2e_accepted':False})
    print(json.dumps(report))


if __name__=='__main__':
    if sys.argv[1:] == ['context']:
        WORK.mkdir(parents=True, exist_ok=True); context()
    elif sys.argv[1:] == ['host']:
        run()
    else:
        raise SystemExit('usage: pr16_learnset_conditional_host.py host|context')
