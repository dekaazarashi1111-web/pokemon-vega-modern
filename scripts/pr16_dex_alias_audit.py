#!/usr/bin/env python3
"""固定候補の旧番号衝突を読取監査し、低開示metadataだけを出力する。"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import os
import tempfile
from pathlib import Path
import struct
import pr16_dex_namespace as ns
CANDIDATE = dict(size=33554432, sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')
ROOT_LITERAL = 0x080429A0
NATIONAL_ROOT = 0x09575F68

def project(namespace, national):
    ns.need(len(national) == namespace['runtime_slot_count'], 'complete runtime national table')
    groups=defaultdict(set); splits=defaultdict(set); native_mismatch=0; native_official=0
    owner_to_official={o:n for n,o in enumerate(namespace['official_national_to_owner']) if o}
    for row,number in zip(namespace['species'],national):
        ns.need(type(number) is int and 0 <= number <= 2048, 'bounded legacy number')
        owner=row['owner']
        if owner and number:
            groups[number].add(owner);splits[owner].add(number)
        if 0 < row['species_id'] < 412 and owner in owner_to_official:
            native_official+=1;native_mismatch+=int(number != owner_to_official[owner])
    collisions={n:sorted(owners) for n,owners in sorted(groups.items()) if len(owners)>1}
    split={o:sorted(numbers) for o,numbers in sorted(splits.items()) if len(numbers)>1}
    # 全中間表のbyteやROM文字列を公開しない。再照合用digestと集計だけ。
    return dict(runtime_slots=len(national), stable_owners=namespace['owner_count'],
                cross_owner_collision_groups=len(collisions),
                ambiguous_legacy_bits_1_to_386=sum(n<=386 for n in collisions),
                same_owner_split_tokens=len(split), native_official_rows=native_official,
                native_official_mapping_mismatches=native_mismatch,
                collision_projection_sha256=hashlib.sha256(ns.serialized(collisions)).hexdigest(),
                split_projection_sha256=hashlib.sha256(ns.serialized(split)).hexdigest(),
                examples=[dict(species_id=sid, owner=namespace['species'][sid]['owner'],
                               legacy_national=national[sid]) for sid in [129,481,1147,1537]])

def inspect(rom, namespace):
    ns.need(ns.identity(rom)==CANDIDATE,'fixed candidate identity')
    root=struct.unpack_from('<I',rom,ROOT_LITERAL-0x08000000)[0]
    ns.need(root==NATIONAL_ROOT,'fixed current mapping root')
    count=namespace['runtime_slot_count']-1
    raw=rom[root-0x08000000:root-0x08000000+count*2]
    national=[0]+list(struct.unpack('<'+str(count)+'H',raw))
    result=project(namespace,national)
    ns.need(result['cross_owner_collision_groups']==277
            and result['same_owner_split_tokens']==52
            and result['ambiguous_legacy_bits_1_to_386']==276,
            'known complete alias audit')
    return dict(schema_version=1, status='STATIC_ALIAS_AUDIT_NOT_NATIVE_ACCEPTANCE',
                candidate=CANDIDATE, namespace_order_sha256=namespace['owner_order_sha256'],
                table=dict(address=root,**ns.identity(raw)), summary=result,
                rom_changed=False, save_changed=False, native_processes=0,
                rom_fragments_published=False)

def write_report(rom_path, output, result):
    ns.need(output.resolve() != rom_path.resolve(), 'immutable ROM input')
    ns.need(not output.exists() or not output.samefile(rom_path), 'ROM hardlink output')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.dex-report-', delete=False) as file:
            temporary = Path(file.name); file.write(ns.serialized(result))
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists(): temporary.unlink()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    ns.need(args.output.resolve()!=args.rom.resolve(),'immutable ROM input')
    result=inspect(args.rom.read_bytes(),ns.build());write_report(args.rom,args.output,result)
    print('旧番号衝突277群を監査。ROM/save/nativeは変更なし。')
if __name__=='__main__':main()
