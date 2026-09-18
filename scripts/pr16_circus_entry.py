#!/usr/bin/env python3
"""実Codex受付のFactory分岐へ任意Circus経路を追加する限定候補builder。

旧Trialのscriptを複製し、最終選択UI後の5D直前のみpending選択/sp072を接続。
既受入Factory本体とCFRU ownerは変更しない。native受入とは別の工程。
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
BASE, SIZE = 0x08000000, 33554432
PARENT_SHA = '4ea33fb8224b0b84493ccca6e90161da245705eb1eb0a3874691ab39cc3806cc'
TASK = 'USER-20260918-CIRCUS-ENTRY'
SELF = 'scripts/pr16_circus_entry.py'
SOURCE = 'overlays/circus_admission/circus_script.c'
OUT = ROOT/'.local/pr16-circus-entry'
LENGTHS = {2:1, 3:1, 4:5, 5:5, 6:6, 7:6, 9:2, 15:6, 33:5, 35:5, 37:3, 39:1, 90:1, 93:1, 106:1, 108:1}
ALLOCATION = 'pr16_circus_reception_runtime'
RESERVATION = 8192
GATE, FACTORY = 0x093CDA9C, 0x093C9390
RESULT, DESCRIPTION = 0x02037004, 0x02022BC4
DRAW = 0x0910333D


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def ptr(value, *, thumb=False):
    need(type(value) is int and BASE <= value < BASE+SIZE, 'ROM pointer outside bounds')
    need(not thumb or value & 1, 'native pointer must be Thumb')
    return struct.pack('<I', value)


def call(address):
    return b'\x23'+ptr(address, thumb=True)


def goto(address):
    return b'\x05'+ptr(address)


def equal(address):
    return b'\x21\x0d\x80\x01\x00\x06\x01'+ptr(address)


def admission(address, select, draw, failure):
    """無入力区間だけに挿入。拒否は既存Abortへ、効果は正規sp072だけが生成。"""
    ptr(address)
    prefix = call(select)
    draw_at = address+len(prefix)+11+5
    # sp072 returns true only once all effects have been loaded. False -> next draw.
    launch = draw_at+5+11+5
    return prefix+equal(draw_at)+goto(failure)+call(draw)+equal(launch)+goto(draw_at)+b'\x5d'


def fork_graph(nodes, start, select, draw, cancel, old_prompt, new_prompt):
    """既知命令境界のみ複製する。5Dの直接前にだけ新しい経路を挿入する。"""
    need(type(nodes) is list and 0<len(nodes)<=128, 'script node count outside bounds')
    addresses=[n['address'] for n in nodes]
    need(len(addresses)==len(set(addresses)) and cancel in addresses, 'ambiguous graph or missing Abort path')
    labels={};cursor=start;launches=0
    addition=len(admission(start,select,draw,start))-1
    for n in nodes:
        ptr(n['address']);labels[n['address']]=cursor
        need(0<len(n['instructions'])<=128, 'invalid instruction count')
        expected=n['address']
        for row in n['instructions']:
            raw=bytes.fromhex(row['bytes']);op=row['opcode']
            need(row['address']==expected and raw and raw[0]==op, 'instruction boundary differs')
            need(LENGTHS.get(op)==len(raw), 'unsupported or malformed reception command')
            expected+=len(raw)
            if op==0x5d:
                need(raw==b'\x5d', 'invalid battle launch length');launches+=1
            if op in (0x08,0x09):
                need(len(raw)==2 and op==0x09 and raw[1] in (4,5), 'unresolved std entry in reception graph')
            need(op not in (0x0a,0x0b,0x24,0x5c,0x5e,0x5f,0xb9), 'unsupported dynamic reception edge')
            cursor+=len(raw)+(addition if op==0x5d else 0)
    need(launches==3, 'expected exactly three Trial launch sites')
    ptr(cursor-1)
    result=bytearray();sites=[];std=[]
    for n in nodes:
        need(start+len(result)==labels[n['address']], 'relocation layout differs')
        for row in n['instructions']:
            at=start+len(result);raw=bytearray.fromhex(row['bytes']);op=raw[0]
            if op in (4,5,6,7):
                pos=1 if op in (4,5) else 2
                need(len(raw)==pos+4, 'invalid branch length')
                target=struct.unpack_from('<I',raw,pos)[0]
                need(target==row.get('target') and target in labels, 'unclosed script edge')
                struct.pack_into('<I',raw,pos,labels[target])
            if op==0x0f and len(raw)==6 and raw[1]==0:
                if struct.unpack_from('<I',raw,2)[0]==old_prompt:
                    raw[2:6]=ptr(new_prompt)
            if op==0x09:
                std.append(dict(address=at,index=raw[1],role='existing message std'))
            if op==0x5d:
                raw=admission(at,select,draw,labels[cancel])
                sites.append(dict(original=row['address'],new=at,size=len(raw),selector=select,draw=draw))
            result.extend(raw)
    need(start+len(result)==cursor, 'relocation size differs')
    return bytes(result),labels,sites,std


def cancel_address(nodes, metadata):
    """配布metadataはscript名を持たない。CommitSelectionの拒否edgeと実Abortを結ぶ。"""
    owners=metadata['entrypoints']
    selected=[n for n in nodes if any(r.get('native')==owners['FacilityRuntime_CommitSelection'] for r in n['instructions'])]
    need(len(selected)==1, 'ambiguous CommitSelection script')
    rows=selected[0]['instructions']
    need(rows[-1]['opcode']==5 and rows[-1].get('target') is not None, 'missing selection rejection edge')
    target=rows[-1]['target'];cancel=[n for n in nodes if n['address']==target]
    need(len(cancel)==1 and cancel[0]['instructions'][0].get('native')==owners['FacilityRuntime_Abort'], 'selection rejection does not enter Abort')
    return target


def bridge(address, prompt, circus):
    # Codexの「いいえ」で入る地点。既存Factoryは新しい「いいえ」で元と同じ入口へ。
    raw=b'\x0f\x00'+ptr(prompt)+b'\x09\x05'
    return raw+equal(circus)+goto(FACTORY)


def patch(raw, offset, payload, gate_operand, bridge_address):
    need(type(raw) is bytes and identity(raw)==dict(size=SIZE,sha256=PARENT_SHA), 'accepted parent differs')
    need(type(offset) is int and offset%4==0 and 0<len(payload)<=RESERVATION, 'invalid new payload')
    need(0<=offset<=SIZE-len(payload), 'payload outside ROM')
    need(type(gate_operand) is int and GATE-BASE<=gate_operand<GATE-BASE+64, 'gateway operand outside root')
    need(raw[gate_operand:gate_operand+4]==ptr(FACTORY), 'gateway operand preimage differs')
    need(offset<=bridge_address-BASE<offset+len(payload), 'bridge outside payload')
    need(offset>gate_operand+4 and raw[offset:offset+len(payload)]==b'\xff'*len(payload), 'payload allocation not unused')
    out=bytearray(raw);out[gate_operand:gate_operand+4]=ptr(bridge_address);out[offset:offset+len(payload)]=payload
    spans=[(gate_operand,gate_operand+4),(offset,offset+len(payload))];cursor=0
    for begin,end in spans:
        need(out[cursor:begin]==raw[cursor:begin], 'undeclared ROM change');cursor=end
    need(out[cursor:]==raw[cursor:],'undeclared ROM suffix change')
    return bytes(out)


def compile_adapter(folder, address, owners):
    folder.mkdir(parents=True,exist_ok=True)
    ld=folder/'circus.ld';elf=folder/'circus.elf'
    ld.write_text('ENTRY(VegaCircusAdmissionSelectScript)\nSECTIONS { . = '+hex(address)+'; '
        '.text : { KEEP(*(.text.VegaCircusAdmissionSelectScript)) *(.text*) *(.rodata*) } '
        '/DISCARD/ : { *(.ARM.exidx*) *(.ARM.extab*) *(.comment*) *(.note*) } }\n')
    definitions=dict(owners,VegaCircusScriptResult=RESULT)
    cmd=['arm-none-eabi-gcc','-std=c11','-Os','-mthumb','-mcpu=arm7tdmi','-ffreestanding',
         '-fno-builtin','-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
         '-Wall','-Wextra','-Werror','-nostdlib','-Wl,--gc-sections','-Wl,--build-id=none',
         *['-Wl,--defsym,'+k+'='+hex(v) for k,v in sorted(definitions.items())],
         '-T',str(ld),str(ROOT/SOURCE),str(ROOT/'overlays/circus_admission/circus_admission.c'),'-o',str(elf)]
    proc=subprocess.run(cmd,capture_output=True)
    (folder/'compile.stdout').write_bytes(proc.stdout);(folder/'compile.stderr').write_bytes(proc.stderr)
    need(proc.returncode==0,'new Circus script adapter compile failed')
    need(not subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)]).strip(),'undefined adapter symbol')
    listing=subprocess.check_output(['arm-none-eabi-nm','-n',str(elf)],text=True)
    (folder/'symbols.txt').write_text(listing)
    symbols={r.split()[2]:int(r.split()[0],16) for r in listing.splitlines() if len(r.split())==3}
    need(symbols['VegaCircusAdmissionSelectScript']==address,'script adapter entry drift')
    binary=folder/'circus.bin';subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True)
    code=binary.read_bytes();need(280<=len(code)<512,'unexpected adapter size')
    dis=subprocess.check_output(['arm-none-eabi-objdump','-d',str(elf)],text=True)
    (folder/'disassembly.txt').write_text(dis.replace(str(elf),'circus-script.elf'))
    return code,address|1


def run():
    sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
    import pr16_ring_policy_successor as parent
    from scripts.pr16_bp_party_retention_successor import existing_requests
    from tools.rom_allocator import build_allocation_report_from_csv
    from tools.regression.rom_runtime import _charmap,_encode_text
    from scripts.pr16_bp_trial_route import graph
    OUT.mkdir(parents=True,exist_ok=True)
    need(not OUT.is_symlink(), 'unsafe output')
    checkpoint=json.loads((ROOT/'content/modernization/pr16_circus_admission_checkpoint.json').read_bytes())
    link=checkpoint['link_report'];need(link['candidate']==dict(size=SIZE,sha256=PARENT_SHA),'saved parent link differs')
    # 正式7関数/link/root走査は原本を再利用。新しいaddressへのadapter linkだけを行う。
    for name in ('overlays/circus_admission/circus_admission.c','overlays/circus_admission/circus_admission.h'):
        need(identity((ROOT/name).read_bytes())==link['source_bindings'][name],'inherited pending implementation changed')
    owners={k:v|1 for k,v in link['new_runtime']['owners'].items()}
    recipe=parent.run();raw=(parent.OUT/'candidate.gba').read_bytes()
    need(identity(raw)==link['candidate'] and recipe['candidate']==link['candidate'],'parent reconstruction differs')
    magic=b'VEGAF20\0';at=raw.find(magic)
    need(at>=0 and raw.find(magic,at+1)<0,'ambiguous facility header')
    npc=struct.unpack_from('<I',raw,at+44)[0]
    nodes=graph(raw,[npc]);gate_nodes=graph(raw,[GATE])
    (OUT/'parent-graphs.json').write_bytes(stable(dict(npc=npc,nodes=nodes,gateway=gate_nodes)))
    gate=next(n for n in gate_nodes if n['address']==GATE)
    routes=[r for r in gate['instructions'] if r.get('target')==FACTORY and r['opcode']==5]
    need(len(routes)==1,'unresolved Codex-to-Factory gateway')
    operand=routes[0]['operand_address']-BASE
    # 固定metadataの2つのnative ownerだけを用い、未解読native/stdを不存在扱いしない。
    cfg=json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    name='pokemon-vega-private-env-v1-state.zip';bound=next(a for a in cfg['archives'] if a['name']==name)
    archive=ROOT/'.local/pr16-bp-trial-native-inputs'/name
    need(identity(archive.read_bytes())=={k:bound[k] for k in ('size','sha256')},'state archive differs')
    with zipfile.ZipFile(archive) as z:
        meta=json.loads(z.read('generated/runtime/facility_runtime_symbols.json'))
    (OUT/'facility-symbols.json').write_bytes(stable(meta))
    need(meta['scripts']['npc_address']==npc, 'fixed metadata NPC differs from candidate')
    cancel=cancel_address(nodes,meta)
    entry_node=next(n for n in nodes if n['address']==npc)
    prompt_rows=[r for r in entry_node['instructions'] if r['opcode']==15]
    need(len(prompt_rows)==1 and bytes.fromhex(prompt_rows[0]['bytes'])[:2]==b'\x0f\x00', 'ambiguous Trial prompt')
    old_prompt=struct.unpack_from('<I',bytes.fromhex(prompt_rows[0]['bytes']),2)[0]
    need(cancel in {n['address'] for n in nodes},'cancel path not in rooted graph')
    requests=existing_requests(recipe['allocation'])
    # NPC builderの正本allocator設定をそのまま継承する。
    import pr16_ring_npc_successor as gift
    regions=gift.REGIONS
    req=dict(name=ALLOCATION,region='future_tail',size=RESERVATION,alignment=4,owner=TASK,
             purpose='Circus optional real reception and exact pending/draw sequence',content_sha256='0'*64)
    preview=build_allocation_report_from_csv(ROOT/regions,requests+[req])
    offset=next(r['start'] for r in preview['allocations'] if r['name']==ALLOCATION)
    load=BASE+offset+64
    left,entry=compile_adapter(OUT/'compile-1',load,owners)
    right,entry2=compile_adapter(OUT/'compile-2',load,owners)
    need(left==right and entry==entry2,'independent new adapter links differ')
    payload=bytearray(64);payload[:8]=b'VEGAC18E';payload.extend(left)
    while len(payload)%4:payload.append(0xff)
    mapping,tokens=_charmap(ROOT)
    expected_text=_encode_text('バトルファクトリー トライアル！\nレンタルで 3れんせん しますか？',mapping,tokens)
    need(raw[old_prompt-BASE:old_prompt-BASE+len(expected_text)]==expected_text, 'original Trial question differs')
    prompt=BASE+offset+len(payload)
    payload.extend(_encode_text('サーカスに さんかしますか？\nいいえで ファクトリーへ',mapping,tokens))
    trial_prompt=BASE+offset+len(payload)
    payload.extend(_encode_text('バトルサーカス トライアル！\nレンタルで 3れんせん しますか？',mapping,tokens))
    script_at=BASE+offset+len(payload)
    scripts,labels,sites,std=fork_graph(nodes,script_at,entry,DRAW,cancel,old_prompt,trial_prompt)
    payload.extend(scripts);bridge_at=BASE+offset+len(payload)
    payload.extend(bridge(bridge_at,prompt,labels[npc]))
    struct.pack_into('<8I',payload,8,1,len(payload),entry,labels[npc],bridge_at,3,DRAW,0)
    new=patch(raw,offset,bytes(payload),operand,bridge_at)
    new_again=patch(raw,offset,bytes(payload),operand,bridge_at)
    need(new==new_again,'independent scoped patches differ')
    owners_changed=[]
    for row,request in zip(recipe['allocation']['allocations'],requests):
        a,b=row['start'],row['end_exclusive']
        need(identity(raw[a:b])['sha256']==row['content_sha256'],'parent allocation identity differs')
        if raw[a:b]!=new[a:b]:
            need(a<=operand and operand+4<=b,'unapproved parent allocation edit')
            request['content_sha256']=identity(new[a:b])['sha256'];owners_changed.append(row['name'])
    need(len(owners_changed)==1,'expected one gateway allocation owner')
    req.update(start=offset,size=len(payload),content_sha256=identity(payload)['sha256'])
    allocation=build_allocation_report_from_csv(ROOT/regions,requests+[req])
    need(allocation['summaries']['overlap_count']==0,'new allocation overlap')
    for row in allocation['allocations']:
        need(identity(new[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],'new allocation identity differs')
    sources=(SELF,SOURCE,'tests/test_pr16_circus_entry.py','tests/test_pr16_circus_entry_binding.py','.github/workflows/pr16-circus-entry.yml')
    report=dict(schema_version=1,status='BUILT_CIRCUS_RECEPTION_NATIVE_PENDING',task=TASK,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        run_id=int(os.environ.get('GITHUB_RUN_ID','0')),parent=identity(raw),candidate=identity(new),
        crc32=f'{zlib.crc32(new)&0xffffffff:08X}',payload=identity(payload),payload_offset=offset,
        allocation=allocation,gateway=dict(address=GATE,operand=operand,before=ptr(FACTORY).hex(),after=ptr(bridge_at).hex()),
        entries=dict(circus=labels[npc],bridge=bridge_at,selector=entry,sp072=DRAW),launch_sites=sites,
        rooted_std_edges=std,old_trial_script_unchanged=True,old_cfru_owners_unchanged=True,
        existing_allocations_rehashed=owners_changed,independent_new_adapter_links=2,independent_scoped_patches=2,
        inherited_link_run=checkpoint['link_run_id'],inherited_root_scan_repeated=False,
        sources={n:identity((ROOT/n).read_bytes()) for n in sources},new_emulator_processes=0,accepted_native_cases_replayed=0,
        physical_admission_accepted=False,suppression_accepted=False,release_ready=False,
        next='新しい実受付分岐のnative取消/入場/Save/fresh Continue。30連勝入力の来歴と抑制抽選は別受入。')
    (OUT/'candidate.gba').write_bytes(new);(OUT/'report.json').write_bytes(stable(report))
    need((parent.OUT/'candidate.gba').read_bytes()==raw,'parent mutated')
    print(json.dumps({k:v for k,v in report.items() if k not in ('allocation','sources','rooted_std_edges')},ensure_ascii=False))
    return report


if __name__=='__main__':
    run()
