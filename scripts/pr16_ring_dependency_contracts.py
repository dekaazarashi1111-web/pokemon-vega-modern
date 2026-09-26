#!/usr/bin/env python3
"""v2規則/owner buffer/copy/stringを保存命令で結合。未読subtype/calleeは未受入。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import pr16_ring_dependency_frontier as dependency
import pr16_ring_remaining_contracts as c
import pr16_ring_contract_machine as model
import pr16_ring_saved_contracts as vm

BASE='7ae1828b1f37c3c7cc437904bd50bfb01e834b9f'
SLUG='pr16-ring-dependency-contracts'
TASK='PR-P08-7-RING-DEPENDENCY-CONTRACTS'
TITLE='v2正常境界・owner buffer差・copy/string部分契約を保存結合'
SELF='scripts/pr16_ring_dependency_contracts.py'
TEST='tests/test_pr16_ring_dependency_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-dependency-contracts.yml'
PRIOR=dependency.REPORT
REPORT='content/modernization/pr16_ring_dependency_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((dependency.SELF,*dependency.SOURCES)))
NO_REPEAT=('v2正常/規則境界・v1 owner copyとv2 copyなし・有限string契約は今回原本を再利用。'
    '旧採取/単独280契約/BP/nativeを再実行せず、残る6calleeとstring subtype21要素表84byteへ進む。'
    '長さ0のcopyは安全なno-opでなく未map停止として保持。native取得とは別の合成契約。')
need=c.need
COPY=0x093bee0b
STRING=0x08008b49
SHADOW=0x0203e400
PENDING_TABLE={'label':'string_extended_subtypes','start':0x08008bb4,'length':84,
    'count':21,'stride':4,'site':0x08008bac,'index':'subtype - 4; unsigned 0..20'}


def parse_limits(rules,counters):
    need(type(rules)is bytes and len(rules)==23*16,'rule表長')
    need(type(counters)is bytes and len(counters)==6*8,'counter表長')
    mask=0;slots={}
    for i in range(23):
        record=rules[i*16:(i+1)*16]
        if record[10]<32:mask|=1<<record[10]
        if record[7]==1:
            slot,limit=record[8:10]
            need(slot<4 and slot not in slots and limit>0,'slot規則')
            slots[slot]=limit
    need(set(slots)==set(range(4)),'slot不足')
    return {'allowed_mask':mask,'slot_limits':[slots[i] for i in range(4)],
        'counter_limits':[int.from_bytes(counters[i*8+2:i*8+4],'little') for i in range(6)]}


def patched(data,offset,value,width):
    need(type(data)is bytes and len(data)==2048,'fixture長')
    need(type(width)is int and width in (1,2,4),'fixture幅')
    need(type(offset)is int and 0<=offset<=2048-width,'fixture範囲')
    need(not set(range(offset,offset+width))&set(range(8,12)),'checksum直接編集禁止')
    need(type(value)is int and 0<=value<1<<(width*8),'fixture値')
    out=bytearray(data);out[offset:offset+width]=value.to_bytes(width,'little');return c.seal(bytes(out))


def verify(nodes,a):
    dependency.validate_tables(a['tables'],nodes)
    table_memory=[(t['start'],bytes.fromhex(t['hex']),False) for t in a['tables']]
    limits=parse_limits(table_memory[1][1],table_memory[2][1]);base=c.initialized_data(0)
    rows=[];prefixes=[]
    def validate(label,data,expected,source=c.CTX):
        owner=source in (vm.BUFFER,vm.BACKUP)
        meta=vm.metadata_expected();shadow=bytes([0xcc])*2048
        extra=[(vm.META,meta,True),(SHADOW,shadow,True)] if owner else []
        machine=model.Machine(nodes,[(source,data,False),*extra,*table_memory],(source,2048)).run(vm.VALIDATE)
        need(machine.r[0]==expected,'validator return '+label)
        writes=machine.nonstack_writes();version=int.from_bytes(data[4:6],'little')
        expected_writes=[]
        if owner:
            expected_writes=[(vm.META+35,1,0)]
            if version==1 and expected==0:
                expected_writes.extend((SHADOW+i,1,value) for i,value in enumerate(data))
                expected_writes.append((vm.META+35,1,1))
            wanted_meta=bytearray(meta);wanted_meta[35]=int(version==1 and expected==0)
            need(machine.data(vm.META,96)==bytes(wanted_meta),'owner metadata差')
            need(machine.data(SHADOW,2048)==(data if version==1 and expected==0 else shadow),'owner copy差')
        need(writes==expected_writes,'validator副作用 '+label)
        row=c.effects(machine,label);row.update(input_sha256=hashlib.sha256(data).hexdigest(),
            input_pointer=source,version=version,expected_r0=expected,shadow_copied=owner and version==1 and expected==0)
        rows.append(row)
    for arg in (0,1):validate('v2-canonical-'+str(arg),c.initialized_data(arg),0)
    for i,limit in enumerate(limits['counter_limits']):
        validate('v2-counter-at-limit-'+str(i),patched(base,0x74d+i*2,limit,2),0)
        if limit<65535:validate('v2-counter-over-limit-'+str(i),patched(base,0x74d+i*2,limit+1,2),15)
    for i,limit in enumerate(limits['slot_limits']):
        validate('v2-slot-at-limit-'+str(i),patched(base,0x75b+i,limit,1),0)
        if limit<255:validate('v2-slot-over-limit-'+str(i),patched(base,0x75b+i,limit+1,1),15)
    for bit in range(32):
        validate('v2-rule-bit-'+str(bit),patched(base,0x75f,1<<bit,4),0 if limits['allowed_mask']&(1<<bit) else 15)
    for source in (vm.BUFFER,vm.BACKUP):
        for has_vacq in (False,True):
            validate('v1-owner-'+hex(source)+'-vacq-'+str(has_vacq),
                c.validator_data(c.acquisition(17) if has_vacq else None),0,source)
        for arg in (0,1):validate('v2-owner-'+hex(source)+'-'+str(arg),c.initialized_data(arg),0,source)
        validate('v2-owner-reject-'+hex(source),patched(base,0x75f,0xffffffff,4),15,source)
    copy_rows=[]
    for length in (1,2,3,4,31,256,2048):
        source=c.CTX+0x4000;dest=c.CTX
        data=bytes((i*37+17)&255 for i in range(length))
        machine=model.Machine(nodes,[(source,data,False),(dest,bytes([0xcc])*length,True)],(dest,source,length)).run(COPY)
        need(machine.data(dest,length)==data and machine.r[0]==vm.RETURN,'copy出力')
        need(machine.nonstack_writes()==[(dest+i,1,b) for i,b in enumerate(data)],'copy範囲')
        copy_rows.append(c.effects(machine,'copy-nonalias-positive-'+str(length)))
    machine=model.Machine(nodes,[(c.CTX+0x4000,b'Z',False),(c.CTX,b'\0',True)],(c.CTX,c.CTX+0x4000,0))
    try:machine.run(COPY)
    except ValueError as exc:
        need(str(exc)=='未map read' and machine.read_fault=={'address':c.CTX+0x4001,'size':1,'site':0x093bee10},'copy0停止')
    else:raise ValueError('copy0をno-op扱い')
    need(machine.nonstack_writes()==[(c.CTX,1,90)],'copy0最初のwrite')
    prefixes.append({'case':'copy-zero-count-not-noop','read_fault':machine.read_fault,
        'nonstack_writes':machine.nonstack_writes(),'return_proven':False,'safe_zero_count':False})
    string_rows=[]
    def string(label,source,expected):
        need(len(expected)<=512,'string fixture上限')
        machine=model.Machine(nodes,[(c.CTX,bytes([0xcc])*512,True),(c.CTX+1024,source,False),*table_memory],(c.CTX,c.CTX+1024)).run(STRING)
        need(machine.r[0]==c.CTX+len(expected)-1 and machine.data(c.CTX,len(expected))==expected,'string出力 '+label)
        need(machine.nonstack_writes()==[(c.CTX+i,1,value) for i,value in enumerate(expected)],'string書込範囲')
        string_rows.append(c.effects(machine,label))
    string('string-empty',b'\xff',b'\xff')
    string('string-ordinary-all-0-to-249',bytes(range(250))+b'\xff',bytes(range(250))+b'\xff')
    for control in (250,251,254):string('string-control-'+str(control),bytes([control,255]),bytes([control,255]))
    for subtype in (0,1,2,3,25,255):
        for value in (0,127,255):
            source=bytes([252,subtype,value,255]);string('string252-bypass-'+str(subtype)+'-'+str(value),source,source)
    for subtype in range(4,25):
        source=bytes([252,subtype,66,255])
        machine=model.Machine(nodes,[(c.CTX,bytes([0xcc])*512,True),(c.CTX+1024,source,False),*table_memory],(c.CTX,c.CTX+1024))
        try:machine.run(STRING)
        except ValueError as exc:
            need(str(exc)=='未map read' and machine.read_fault=={'address':PENDING_TABLE['start']+(subtype-4)*4,'size':4,'site':PENDING_TABLE['site']},'subtype停止差')
        else:raise ValueError('未読subtype表を推測')
        prefixes.append({'case':'string252-unread-subtype-'+str(subtype),'read_fault':machine.read_fault,'return_proven':False})
    for value in (0,1,2,255):
        source=bytes([253,value,255]);machine=model.Machine(nodes,[(c.CTX,bytes([0xcc])*512,True),(c.CTX+1024,source,False),*table_memory],(c.CTX,c.CTX+1024))
        try:machine.run(STRING)
        except ValueError as exc:
            need(str(exc)=='保存node境界で停止' and machine.last_pc==0x08008d5c and machine.r[0]==value,'string253停止差')
        else:raise ValueError('未読string253 calleeを推測')
        prefixes.append({'case':'string253-callee-'+str(value),'stopped_at':machine.last_pc,'r0':value,'return_proven':False})
    need(vm.flow.node_map(nodes)[0x08008ba8]['literal_value']==PENDING_TABLE['start'],'subtype pointer差')
    return {'classification':'V2_AND_OWNER_COPY_STRING_PARTIAL_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'limits':limits,'validator_cases':rows,'copy_cases':copy_rows,'string_cases':string_rows,
        'synthetic_contract_cases':len(rows)+len(copy_rows)+len(string_rows),'limited_prefix_stops':prefixes,
        'saved_node_count':len(nodes),'pending_direct_callees':copy.deepcopy(a['pending_direct_callees']),
        'pending_data_ranges':[copy.deepcopy(PENDING_TABLE)],'pending_continuations':copy.deepcopy(a['pending_continuations']),
        'validator_v2_canonical_return_proven':True,'validator_owner_buffer_return_proven':True,
        'validator_owner_semantics':{'v1_valid':'2048byte shadow copy and metadata byte35=1',
            'v2_valid':'shadow unchanged and metadata byte35=0','scope':'nonalias synthetic mapped buffers only'},
        'copy_requires_positive_length':True,'copy_r0_contains_saved_lr_not_destination':True,'all_string_subtypes_proven':False,'all_live_frames_proven':False,
        'all_callers_resolved':False,'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_byte_samples':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,
        'preconditions':['保存byte/表と明示mapされた合成buffer/stackだけ。native到達証明ではない',
            'copy長は正、source/destination/stack/metadataは非alias、文字列は検証した終端付き有限入力',
            'string253/252subtype4..24・未知callee・ライブcaller frameを推測して通過しない']}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    nodes,_=dependency.saved_inputs();nodes=[*nodes,*prior['analysis']['new_nodes']]
    result=verify(nodes,prior['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'summary.json').write_bytes(s.stable({k:result[k] for k in (
        'classification','limits','saved_node_count','synthetic_contract_cases','pending_direct_callees','pending_data_ranges',
        'validator_owner_semantics','copy_requires_positive_length','ring_acquisition_accepted','release_ready')}))
    return result


def summaries(result):
    return (f'保存{result["saved_node_count"]}命令と440byte表から{result["synthetic_contract_cases"]}新規合成契約。'
        'v2正常/規則境界、v1 shadow copyとv2 copyなし、正length copy、string有限入力を検証。ROM/native0。',
        '残る6calleeとstring252 subtype4..24の21要素表84byteを一度だけ有限採取し保存結合する。'
        'string253の参照先、scheduler/callback/wait等の未読境界とcaller frameを次に絞る。'
        '今回完了したv2/owner copy/規則境界を単独再実行しない。copy長0は安全なno-opではなく、r0はdestinationでなく保存LRとなる。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
