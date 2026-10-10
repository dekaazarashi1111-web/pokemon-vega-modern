#!/usr/bin/env python3
"""先頭originの有限命令範囲。逆アセンブル形をowner/実行証明へ自動昇格しない。"""
from __future__ import annotations
import hashlib
import re
import subprocess
from pathlib import Path

BASE = 0x08000000
HIT = 0x080A006F
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
SCOPES = {'preceding_public_entry': (0x0809FE98, 96), 'first_origin_envelope': (0x080A002C, 192),
          'following_public_entry': (0x080A1330, 96), 'second_origin_envelope': (0x081C96DC, 52)}
CALLS = ('ClearStdWindowAndFrameToTransparent', 'CopyWindowToVram', 'RemoveWindow')
CLAIMS = dict(donor_safe_bytes=0, donor_eligible=False, donor_leased=False,
              formal_classification_changes=0, actual_runtime_execution_observed=False,
              first_origin_owner_proven=False, first_origin_consumer_proven=False,
              indirect_reference_completeness_claimed=False, native_processes=0,
              accepted_test_reruns=0, accepted_reader_replays=0, old_full_rom_scan_runs=0,
              formal_rom_changed=False, formal_save_changed=False)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    need(type(raw) is bytes, 'bytesのみ')
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def validate_span(address, size):
    need(type(address) is int and type(size) is int and address % 2 == 0 and size % 2 == 0,
         'Thumb halfword整数/整列')
    need(BASE <= address and 0 < size <= 512 and address + size <= BASE + CANDIDATE['size'], '有限ROM範囲')


def parse_disassembly(text, raw, address):
    """GNU ARMv4Tの有限出力を意味fieldだけにする。data/未定義の値とraw bytesを公開しない。"""
    validate_span(address, len(raw))
    need(type(text) is str and len(text) <= 50000, '有限objdump出力')
    rows=[]
    for line in text.splitlines():
        match=re.fullmatch(r'\s*([0-9a-fA-F]+):\s+([^\s]+)(?:\s+(.*))?',line)
        if not match:
            continue
        pc=int(match[1],16); mnemonic=match[2].lower(); operands=(match[3] or '').strip()
        need(address <= pc < address + len(raw) and pc % 2 == 0,'範囲外/奇数命令')
        need(bool(re.fullmatch(r'[a-z.][a-z0-9_.]*',mnemonic)),'raw opcode出力を拒否')
        rows.append((pc,mnemonic,operands))
    need(bool(rows) and rows[0][0]==address and [r[0] for r in rows]==sorted({r[0] for r in rows}),
         '順序/一意/先頭')
    out=[]
    for index,(pc,mnemonic,operands) in enumerate(rows):
        end=rows[index+1][0] if index+1<len(rows) else address+len(raw)
        size=end-pc;need(size in (2,4),'命令gap/extent')
        kind='INSTRUCTION_SHAPE_ONLY'
        if mnemonic.startswith('.') or 'undefined' in operands.lower() or mnemonic in ('undefined','udf'):
            kind='DATA_OR_UNDEFINED_NOT_EXPORTED';operands=None
        else:
            # GNU comments may print literal raw data; they are never copied to public evidence.
            operands=operands.split(';',1)[0].split('@',1)[0].strip()
            operands=re.sub(r'\s*<[^>]*>','',operands).strip()
            need(len(operands)<=200 and bool(re.fullmatch(r'[a-zA-Z0-9_, #{}\[\]!+\-().]*',operands)), '閉じたoperand文字')
        out.append(dict(address=pc,size=size,sha256=identity(raw[pc-address:end-address])['sha256'],
                        mnemonic=mnemonic,operands=operands,kind=kind))
    return out


def disassemble(path, raw, address, size):
    validate_span(address,size)
    span=raw[address-BASE:address-BASE+size];need(len(span)==size,'全span')
    command=['arm-none-eabi-objdump','-D','-z','-b','binary','-m','armv4t','-M','force-thumb',
             '--no-show-raw-insn','--adjust-vma='+str(BASE),'--start-address='+str(address),
             '--stop-address='+str(address+size),str(path)]
    result=subprocess.run(command,capture_output=True,text=True,check=True)
    need(not result.stderr,'objdump診断あり')
    return dict(address=address,**identity(span),instructions=parse_disassembly(result.stdout,span,address),
                interpretation='ARMV4T_THUMB_SHAPES_NOT_CODE_OWNERSHIP',raw_bytes_exported=False)


def direct_target(operand):
    match=re.fullmatch(r'(?:0x)?([0-9a-fA-F]{7,8})',operand or '')
    return int(match[1],16) if match else None


def normal_return_cfg(instructions, entry):
    """同期外部call正常帰還条件下のCFG。unknown/indirectは境界で停止し到達不能を推測しない。"""
    need(type(instructions) is list and 0<len(instructions)<=256,'有限命令list')
    by={r['address']:r for r in instructions};need(len(by)==len(instructions) and entry in by,'entry/重複')
    todo=[entry];visited=set();calls=[];returns=[];boundaries=[];edges=[]
    conditions={'eq','ne','cs','hs','cc','lo','mi','pl','vs','vc','hi','ls','ge','lt','gt','le'}
    while todo:
        pc=todo.pop()
        if pc in visited:continue
        if pc not in by:
            boundaries.append(dict(address=pc,reason='OUTSIDE_FINITE_SCOPE'));continue
        row=by[pc];visited.add(pc);mn=row['mnemonic'].split('.')[0];operand=row['operands'] or ''
        fall=pc+row['size'];targets=[]
        if row['kind']!='INSTRUCTION_SHAPE_ONLY':
            boundaries.append(dict(address=pc,reason='NOT_DECODED_CODE'));continue
        if mn=='bx':
            if operand=='lr':returns.append(pc)
            else:boundaries.append(dict(address=pc,reason='INDIRECT_BRANCH'))
        elif mn=='pop' and re.search(r'\bpc\b',operand):returns.append(pc)
        elif mn=='bl':
            target=direct_target(operand)
            if target is None:boundaries.append(dict(address=pc,reason='UNRESOLVED_CALL'))
            else:calls.append(dict(address=pc,target=target));targets=[fall]
        elif mn=='blx':boundaries.append(dict(address=pc,reason='NOT_ARMV4T_BL'))
        elif mn=='b' or mn.startswith('b') and mn[1:] in conditions:
            target=direct_target(operand)
            if target is None:boundaries.append(dict(address=pc,reason='UNRESOLVED_BRANCH'))
            else:targets=[target]+([] if mn=='b' else [fall])
        elif re.match(r'pc\s*,',operand) or mn in ('svc','swi','bkpt'):
            boundaries.append(dict(address=pc,reason='OPAQUE_CONTROL'))
        elif mn not in {'push','pop','ldr','ldrb','ldrh','ldrsb','ldrsh','str','strb','strh','add','adds',
                         'sub','subs','mov','movs','cmp','cmn','tst','and','ands','eor','eors','orr','orrs',
                         'bic','bics','mvn','mvns','neg','negs','lsl','lsls','lsr','lsrs','asr','asrs',
                         'adc','adcs','sbc','sbcs','ror','rors','mul','muls','stmia','ldmia','nop'}:
            boundaries.append(dict(address=pc,reason='UNSUPPORTED_CONTROL_CLASS'))
        else:targets=[fall]
        for target in targets:
            edges.append(dict(source=pc,target=target));todo.append(target)
    return dict(entry=entry,visited=sorted(visited),edges=sorted(edges,key=lambda r:(r['source'],r['target'])),
                calls=sorted(calls,key=lambda r:r['address']),returns=sorted(returns),boundaries=boundaries,
                assumptions_ja='entryがThumbコードであり、外部BLは同期ABIで正常帰還する条件。実行/native/IRQやdata aliasの証明ではない。',
                hit_bytes_fetched=sorted({a for pc in visited for a in range(pc,pc+by[pc]['size']) if HIT<=a<HIT+4}),
                whole_hit_control_flow_covered=all(any(pc<=a<pc+by[pc]['size'] and by[pc]['kind']=='INSTRUCTION_SHAPE_ONLY' for pc in visited) for a in range(HIT,HIT+4)))


def overlap_owners(hit, owners):
    need(type(hit) is dict and type(hit.get('address')) is int and hit.get('size')==4,'4byte hit')
    need(type(owners) is dict,'owner table')
    result=[]
    for name,row in sorted(owners.items()):
        if row['address'] < hit['address']+4 and hit['address'] < row['address']+row['size']:
            result.append(dict(name=name,address=row['address'],size=row['size'],sha256=row['after_sha256'],
                               whole_hit_inside=row['address']<=hit['address'] and hit['address']+4<=row['address']+row['size']))
    return result


def bind_public(raw, git_blob):
    need(type(raw) is bytes,'公開source bytes')
    actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    need(actual==git_blob,'固定公開source Git blob')
    return dict(git_blob=git_blob,**identity(raw))
