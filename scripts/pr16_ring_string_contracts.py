#!/usr/bin/env python3
"""保存1752命令からFC全21分岐・memset・selector境界を合成検証する。"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import sys
import pr16_ring_string_machine as model
import pr16_ring_string_frontier as frontier
import pr16_ring_remaining_contracts as c
import pr16_ring_saved_contracts as vm
BASE='840e392418aa7bfdc6b02e88c1246e02aa43ed3f'
SLUG='pr16-ring-string-contracts'
TASK='PR-P08-7-RING-STRING-CONTRACTS'
TITLE='FC全21分岐・memset・placeholderとcallee停止契約を保存検証'
SELF='scripts/pr16_ring_string_contracts.py'
TEST='tests/test_pr16_ring_string_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-string-contracts.yml'
PRIOR=frontier.REPORT
REPORT='content/modernization/pr16_ring_string_contracts.json'
KEY='latest_ring_diagnostic'
EXTRA_CODE=(model.SELF,)
SOURCES=(model.SELF,frontier.SELF,*frontier.SOURCES,vm.SELF,model.prior.SELF,c.SELF)
MIN_TESTS=43
STRING,SELECTOR,FILL,NIBBLE,GATE=0x08008b49,0x08008d5d,0x081c9df9,0x0813d469,0x08002cf1
PLACEHOLDERS,FALLBACK,NIBBLES,GATE_WORD=0x081f1364,0x083dd1dc,0x0842d68c,0x03003dd0
ARG_COUNTS={i:(3 if i==4 else 2 if i==11 else 0 if i in (7,9,15,21,22,23,24) else 1) for i in range(4,25)}
PENDING_DATA=(
    {'label':'placeholder_callback_table','start':PLACEHOLDERS,'length':56,'count':14,'stride':4,'site':0x08008d68},
    {'label':'nibble_table','start':NIBBLES,'length':76,'count':76,'stride':1,'site':0x0813d47e},
    {'label':'placeholder_fallback_first_byte','start':FALLBACK,'length':1,'count':1,'stride':1,'site':0x08008b4e})
NO_REPEAT=('FC全21subtype有限契約・memset0/正長/整列・selector範囲/合成nibble表・null gateは今回原本を再利用。'
    '旧94契約/採取/BP/nativeを再実行せず、3callee・1実中継先・未読data133byteへ進む。'
    '合成表の値を候補ROM値に、null gate成功を非null帰還やRing取得に読み替えない。')
need=c.need


def argument_count(subtype):
    need(type(subtype)is int and subtype in ARG_COUNTS,'subtype範囲')
    return ARG_COUNTS[subtype]


def nibble_expected(arg,data):
    need(type(arg)is int and 0<=arg<=0xffffffff,'selector引数')
    need(type(data)is bytes and len(data)==76,'nibble表長')
    value=arg&65535;index=value>>1
    return 3 if index>75 else (data[index]>>((value&1)*4))&15


def fill_writes(dest,value,length):
    need(type(dest)is int and type(value)is int and type(length)is int and length>=0,'fill引数')
    byte=value&255;words=length//4 if dest%4==0 else 0
    return [(dest+i*4,4,byte*0x01010101) for i in range(words)]+[(dest+i,1,byte) for i in range(words*4,length)]


def verify(nodes,analysis):
    need(len(nodes)==1752 and analysis['cached_node_count']==1576 and analysis['new_node_count']==176,'保存命令件数')
    need(analysis['pending_direct_callees']==[0x0806dd5d,0x08076d41,0x081c7ac9] and analysis['pending_continuations']==[],'先行未読集合')
    tables=analysis['tables'];frontier.validate_table(tables[3],nodes,[(t['start'],t['length'])for t in tables[:3]])
    segments=[(t['start'],bytes.fromhex(t['hex']),False)for t in tables]
    rows=[];stops=[]
    def returned(machine,label):
        row=c.effects(machine,label);rows.append(row);return row
    def stopped(machine,entry,label,error,site,fault=None):
        try:machine.run(entry)
        except ValueError as exc:
            need(str(exc)==error and machine.last_pc==site,'停止境界 '+label)
            if fault is not None:need(machine.read_fault==fault,'read停止 '+label)
        else:raise ValueError('未証明境界を通過 '+label)
        row={'case':label,'stopped_at':site,'read_fault':machine.read_fault,
            'stack_bytes_live':vm.SP-machine.r[13],'nonstack_writes':machine.nonstack_writes(),
            'return_proven':False};stops.append(row);return row
    def string(label,data):
        machine=model.Machine(nodes,[(c.CTX,b'\xcc'*512,True),(c.CTX+1024,data,False),*segments],(c.CTX,c.CTX+1024)).run(STRING)
        need(machine.data(c.CTX,len(data))==data and machine.r[0]==c.CTX+len(data)-1,'FC出力')
        need(machine.nonstack_writes()==[(c.CTX+i,1,b) for i,b in enumerate(data)],'FC書込範囲')
        row=returned(machine,label);row['input_sha256']=hashlib.sha256(data).hexdigest()
    combined=bytearray()
    for subtype in range(4,25):
        count=argument_count(subtype)
        for value in (0,127,252,253,255):
            string('FC-'+str(subtype)+'-payload-'+str(value),bytes([252,subtype])+bytes([value])*count+b'\x42\xff')
        combined.extend(bytes([252,subtype])+bytes([255])*count)
        short=bytes([252,subtype])+bytes([0])*max(0,count-1)
        machine=model.Machine(nodes,[(c.CTX,b'\xcc'*512,True),(c.CTX+1024,short,False),*segments],(c.CTX,c.CTX+1024))
        site=0x08008c18 if count else 0x08008b4e
        stopped(machine,STRING,'FC-truncated-'+str(subtype),'未map read',site,
            {'address':c.CTX+1024+len(short),'size':1,'site':site})
    string('FC-all-21-concatenated',bytes(combined)+b'\xff')
    for value in (*range(14,256),0x100,0xffffffff):
        machine=model.Machine(nodes,[],(value,)).run(SELECTOR)
        need(machine.r[0]==FALLBACK and not machine.nonstack_writes(),'selector範囲外')
        returned(machine,'selector-fallback-'+str(value))
    for value in range(14):
        machine=model.Machine(nodes,[],(value,));site=0x08008d68
        stopped(machine,SELECTOR,'selector-unread-table-'+str(value),'未map read',site,
            {'address':PLACEHOLDERS+value*4,'size':4,'site':site})
    for value in (14,255):
        machine=model.Machine(nodes,[(c.CTX,b'\xcc'*512,True),(c.CTX+1024,bytes([253,value,255]),False),*segments],(c.CTX,c.CTX+1024))
        stopped(machine,STRING,'FD-fallback-unread-body-'+str(value),'未map read',0x08008b4e,
            {'address':FALLBACK,'size':1,'site':0x08008b4e})
    for align in range(4):
        for length in (0,1,2,3,4,5,15,16,17,31,32,33,63,64,65,256,2048):
            for value in (0,255,0x12345678):
                dest=c.CTX+align;initial=b'\xaa'*4+b'\xcc'*length+b'\xdd'*4
                machine=model.Machine(nodes,[(dest-4,initial,True)],(dest,value,length)).run(FILL)
                need(machine.r[0]==dest and machine.data(dest-4,len(initial))==b'\xaa'*4+bytes([value&255])*length+b'\xdd'*4,'memset出力/guard')
                need(machine.nonstack_writes()==fill_writes(dest,value,length),'memset正確書込')
                returned(machine,'memset-'+str(align)+'-'+str(length)+'-'+str(value))
    data=bytes((i*73+17)&255 for i in range(76))
    for value in (*range(152),152,153,65535,0x10000,0x10097,0x10098,0xffffffff):
        machine=model.Machine(nodes,[(NIBBLES,data,False)],(value,)).run(NIBBLE)
        need(machine.r[0]==nibble_expected(value,data) and not machine.nonstack_writes(),'nibble計算')
        row=returned(machine,'nibble-synthetic-'+str(value));row['synthetic_table_not_candidate_data']=True
    for value in (0,1,150,151):
        machine=model.Machine(nodes,[],(value,));site=0x0813d47e
        stopped(machine,NIBBLE,'nibble-unread-'+str(value),'未map read',site,
            {'address':NIBBLES+value//2,'size':1,'site':site})
    for args in ((0,0,0),(17,255,9),(0xffffffff,0x12345678,0xffffffff)):
        machine=model.Machine(nodes,[(GATE_WORD,bytes(4),False)],args).run(GATE)
        need(machine.r[0]==0 and not machine.nonstack_writes(),'null gate')
        returned(machine,'null-gate-'+str(args[0]))
    for value in (1,0xffffffff):
        args=(17,0x12345678,9);machine=model.Machine(nodes,[(GATE_WORD,value.to_bytes(4,'little'),False)],args)
        row=stopped(machine,GATE,'nonnull-gate-'+str(value),'保存node境界で停止',0x09378a30)
        need(machine.r[6]==17 and machine.r[5]==0x78 and machine.r[12]==9 and row['stack_bytes_live']==20,'nonnull frame')
        row['effective_target']=0x09378a31
    for entry,target,stack in ((0x0806dd99,0x0806dd5c,4),(0x08076c09,0x08076d40,24)):
        for value in (0,1,255,256,0x12345678,0xffffffff):
            machine=model.Machine(nodes,[],(value,))
            row=stopped(machine,entry,'callee-prefix-'+hex(entry)+'-'+str(value),'保存node境界で停止',target)
            expected=0x4010+(value&255) if entry==0x0806dd99 else (value&255)<<24
            need(machine.r[0]==expected and row['stack_bytes_live']==stack and not machine.nonstack_writes(),'callee引数/frame')
            row['callee_r0']=expected
    need(len(rows)==716 and len(stops)==55,'契約件数差分')
    return {'classification':'FINITE_FC_MEMSET_SELECTOR_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':len(rows),'contracts':rows,'limited_prefix_stops':stops,
        'fc_argument_counts':{str(k):v for k,v in ARG_COUNTS.items()},
        'string252_all_21_dispatch_cases_proven':True,'all_string_inputs_proven':False,
        'memset_zero_length_noop_proven':True,'memset_return_is_destination':True,
        'string253_actual_references_proven':False,'nibble_actual_table_unread':True,
        'pending_direct_callees':copy.deepcopy(analysis['pending_direct_callees']),
        'pending_effective_targets':[0x09378a31],'pending_data_ranges':copy.deepcopy(list(PENDING_DATA)),
        'pending_continuations':copy.deepcopy(analysis['pending_continuations']),
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_byte_samples':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'preconditions':['有限終端入力、非alias合成buffer/stackと保存命令だけ。実到達/実flash/caller frame証明ではない',
            'FC payload内FF/FC/FDは引数としてコピー。未読placeholder表/本文/実nibble表は推測しない',
            'STMIA r1!,{r3}とPOP {r4,r5,pc}の保存6siteだけを拡張。旧モデル/旧契約は変更も単独再実行もしない'],
        'reference_review':{'query':'ARM7TDMI Thumb STMIA PUSH POP instruction writeback',
            'url':'https://problemkaputt.de/gbatek-thumb-opcodes-memory-multiple-load-store-push-pop-and-ldm-stm.htm',
            'scope_ja':'STMIAの昇順store/base更新、POPのSP更新・ARM7のThumb維持・flags不変。公式Armページ本文は取得不可のため使用せず。'}}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*prior['analysis']['new_nodes']]
    result=verify(nodes,prior['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'summary.json').write_bytes(s.stable({k:result[k] for k in ('classification','synthetic_contract_cases',
        'fc_argument_counts','pending_direct_callees','pending_effective_targets','pending_data_ranges','reference_review')}))
    return result


def summaries(result):
    return (f'保存1752命令から{result["synthetic_contract_cases"]}新規有限合成契約。FC全21分岐・memset整列/0長・selector/nibble/null gateと未読境界を検証。ROM/native0。',
        '残る3calleeと非null実中継先0x09378A31、placeholder14要素56byte・nibble76byte・fallback先頭1byteだけを有限採取して保存結合する。'
        '旧採取/FC/memset/旧94契約/BPを単独再実行せず、placeholder実参照と非null/caller frameへ絞る。'
        'Network補足（この工程では共通runnerの外部技術資料なし定型句を適用しない）: GBATEK THUMB.14/15（https://problemkaputt.de/gbatek-thumb-opcodes-memory-multiple-load-store-push-pop-and-ldm-stm.htm）、STMIA writeback/POP Thumb維持。'
        'Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    import pr16_ring_dependency_contracts as contracts
    SOURCES=tuple(dict.fromkeys((*SOURCES,*contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
