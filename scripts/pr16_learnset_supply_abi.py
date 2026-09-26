#!/usr/bin/env python3
"""保存PLC2/PLA1を再利用し実ROM ABIを採取する。旧生成/検証は呼ばない。"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'scripts')]
from tools import pr16_learnset_successor as s
from pr16_learnset_floette_verify import download
from pr16_learnset_payload_verify import current_pr, completed_run
import pr16_learnset_conditional_host as h
BASE = 0x08000000
WORK = ROOT/'.local/pr16-learnset-supply-abi'
CP = 'content/modernization/pr16_learnset_compact_checkpoint.json'
SUPPLY = 'content/modernization/pr16_learnset_supply_checkpoint.json'
TASK = 'USER-20260922-LEARNSET-SUPPLY-ABI'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def write(path, value):
    path.write_bytes(s.encode(value))


def replay(parent, folder, checkpoint):
    """保存segment/hookの全preimageとrollbackを検査。compilerは起動しない。"""
    link = s.read_json(folder/'link.json')
    need(identity(parent) == link['parent'], '保存PLC2親不一致')
    out = bytearray(parent)
    spans = []
    for row in link['segments']:
        name = row['file']
        need(Path(name).name == name, 'segment path不正')
        raw = (folder/name).read_bytes()
        need(identity(raw) == {k:row[k] for k in ('size','sha256')}, 'segment hash不一致')
        at = row['start']; end = at+len(raw)
        need(type(at) is int and 0 <= at < end <= len(parent), 'segment範囲不正')
        need(parent[at:end] == b'\xff'*len(raw), 'segment preimage不一致')
        spans.append((at,end)); out[at:end] = raw
    for row in link['hooks']:
        at = row['offset']; before = bytes.fromhex(row['before']); after = bytes.fromhex(row['after'])
        need(before and len(before) == len(after) and 0 <= at <= len(parent)-len(before), 'hook範囲不正')
        need(parent[at:at+len(before)] == before, 'hook preimage不一致')
        spans.append((at,at+len(before))); out[at:at+len(after)] = after
    ordered = sorted(spans)
    need(all(a[1] <= b[0] for a,b in zip(ordered,ordered[1:])), '保存範囲重複')
    rollback = bytearray(out)
    for a,b in spans:
        rollback[a:b] = parent[a:b]
    need(bytes(rollback) == parent and identity(out) == link['candidate'] == checkpoint['candidate'], '保存PLC2候補不一致')
    return bytes(out), link


def restore():
    current_pr(os.environ['GITHUB_SHA'])
    compact = s.read_json(ROOT/CP); supply = s.read_json(ROOT/SUPPLY)
    completed_run(compact['run_id'],compact['source_head'],'.github/workflows/pr16-learnset-compact-bound.yml','compact-bound')
    completed_run(supply['run_id'],supply['source_head'],'.github/workflows/pr16-learnset-supply.yml','supply-host')
    for checkpoint in (compact,supply):
        for name,binding in checkpoint['verification']['code_bindings'].items():
            need(identity((ROOT/name).read_bytes()) == binding, '受入source変更: '+name)
    h.WORK = WORK/'restore'; h.WORK.mkdir(parents=True)
    raw, prior = h.restore_progress()
    download(compact['artifacts']['pr16-learnset-compact-native-data'],compact['source_head'],WORK/'compact',compact['verification']['data_files'])
    raw, link = replay(raw,WORK/'compact',compact)
    download(supply['artifacts']['data'],supply['source_head'],WORK/'supply',supply['data_files'])
    need(identity((WORK/'supply/archive-image.bin').read_bytes()) == supply['image'], '保存PLA1不一致')
    (WORK/'parent.gba').write_bytes(raw)
    return raw, link


def collect():
    WORK.mkdir(parents=True)
    raw, link = restore()
    proof = WORK/'proof'; proof.mkdir()
    symbols_path = ROOT/'generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json'
    stage74 = s.read_json(symbols_path)
    symbols = {name:int(row['address'],0) for name,row in stage74['symbols'].items()}
    entries = {}
    for name,address in {'CanMonLearnTutorMove':0x09110228,'native_relearner':0x080432D0,
                         'conditional_relearner':0x091141D4,**{n:a for n,a in symbols.items() if n in (
        'Stage74_GetMoveRelearnerMoves','Stage74_PrepareMachinePages','Stage74_OpenMachinePageMenu',
        'Stage74_CommitMachinePage','Stage74_SelectedMachinePageHasMoves','Stage74_PageCountForRowCount',
        'Stage74_SetMachineMode','Stage74_SetTutorMode','Stage74_ResetMode')}}.items():
        at = address-BASE
        need(0 <= at <= len(raw)-512, 'ABI入口範囲不正')
        entries[name] = {'address':address,'offset':at,'window_hex':raw[at:at+512].hex()}
    sources = {}
    candidates = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    selected = [n for n in candidates if n.startswith(('overlays/modernization_p03','overlays/modernization_p07','overlays/modernization_rockruff')) and Path(n).suffix in ('.c','.h','.S','.s','.ld')]
    selected += ['generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json',
                 'vendor/upstream/CFRU-JP/src/item.c','vendor/upstream/CFRU-JP/include/constants/items.h',
                 'vendor/upstream/CFRU-JP/include/constants/species.h']
    with zipfile.ZipFile(proof/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(set(selected)):
            path = ROOT/name
            if not path.is_file():
                continue
            need(not path.is_symlink(), 'source symlink禁止')
            body = path.read_bytes(); body.decode('utf-8')
            need(b'\0' not in body and len(body) <= 2000000, 'source text範囲不正')
            z.writestr(name,body); sources[name] = identity(body)
    report = {'task':TASK,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'status':'SAVED_PLC2_PLA1_ABI_CAPTURED','scope':'READ_ONLY_ABI_NOT_NATIVE_ACCEPTANCE',
        'candidate':identity(raw),'archive':identity((WORK/'supply/archive-image.bin').read_bytes()),
        'entries':entries,'stage74_symbols':stage74,'source_files':sources,
        'source_archive':identity((proof/'source.zip').read_bytes()),
        'accepted_tests_rerun':0,'old_arm_compiles':0,'new_native_processes':0,
        'gameplay_e2e_accepted':False,'release_ready':False}
    write(proof/'abi.json',report)
    print(json.dumps({'status':report['status'],'candidate':report['candidate'],'entries':len(entries)}))


if __name__ == '__main__':
    try:
        collect()
    except Exception as exc:
        (WORK/'proof').mkdir(parents=True,exist_ok=True)
        write(WORK/'proof/failure.json',{'status':'FAIL','error':str(exc).replace(str(ROOT),'$REPO')})
        raise
