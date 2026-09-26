#!/usr/bin/env python3
"""保存参照表/getter、task列、非null中継の有限契約。実caller境界は昇格しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import pr16_ring_reference_frontier as frontier
import pr16_ring_string_contracts as prior_contracts
import pr16_ring_string_machine as model
import pr16_ring_remaining_contracts as c
import pr16_ring_saved_contracts as vm

BASE='83088f7a6959c2419f4f047b9b9577e74df9b642'
SLUG='pr16-ring-reference-contracts'
TASK='PR-P08-7-RING-REFERENCE-CONTRACTS'
TITLE='placeholder14参照・実nibble・task列・非null境界を保存結合'
SELF='scripts/pr16_ring_reference_contracts.py'
TEST='tests/test_pr16_ring_reference_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-reference-contracts.yml'
PRIOR=frontier.REPORT
REPORT='content/modernization/pr16_ring_reference_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=48
EXTRA_CODE=()
SOURCES=(frontier.SELF,prior_contracts.SELF,model.SELF,model.prior.SELF,vm.SELF,c.SELF,*frontier.SOURCES)
STRING,SELECTOR,NIBBLE=prior_contracts.STRING,prior_contracts.SELECTOR,prior_contracts.NIBBLE
TASKS,COUNT,STRIDE=0x030050d0,16,40
HEAD,INSERT,VARGET=0x08076d41,0x08076c09,0x0806dd5d
SB1,SB2=0x02004000,0x02003000
GLOBAL1,GLOBAL2=0x03005048,0x0300504c
GATE_CONTEXT=0x02020010
FIXED={0:0x02022070,2:0x02021c4c,3:0x02021c60,4:0x02021c74,7:0x083dd1ea,
       8:0x083dd1f2,9:0x083dd1ee,10:0x083dd1fb,11:0x083dd1f6,12:0x083dd206,13:0x083dd200}
TEXT_POINTERS=tuple(sorted({0x083dd1dd,0x083dd1e0,0x083dd210,0x083dd20c,*[p for p in FIXED.values() if p>=0x08000000]}))
NO_REPEAT=('placeholder14参照/実nibble/16slot task挿入と非nullprefixは保存原本を再利用。'
    '正常な有限task列と不正slot255のframe外write診断を混同しない。'
    '旧716契約・FC/memset・同じ採取・BP/nativeを単独再実行せず、1callee/1継続と11文字列の限定窓へ進む。')
need=c.need


def text_windows():
    return [{'label':'placeholder_text_'+hex(p),'start':p,'length':min(32,TEXT_POINTERS[i+1]-p) if i+1<len(TEXT_POINTERS)else 32,
        'max_terminator_scan':32}for i,p in enumerate(TEXT_POINTERS)]


def getter_expected(index,gender=0,rival=255,sb1=SB1,sb2=SB2):
    need(type(index)is int and 0<=index<=13,'getter index')
    need(type(gender)is int and 0<=gender<=255 and type(rival)is int and 0<=rival<=255,'getter byte')
    if index in FIXED:return FIXED[index]
    if index==1:return sb2
    if index==5:return 0x083dd1dd if gender==0 else 0x083dd1e0
    return sb1+0x3a4c if rival!=255 else (0x083dd210 if gender==0 else 0x083dd20c)


def expanded_fd_writes(dest,name):
    need(type(dest)is int and type(name)is bytes and name.endswith(b'\xff') and 255 not in name[:-1],'FD name入力')
    # 再帰展開の仮terminatorも実際のwrite履歴に含め、続く文字による上書きを明示する。
    return [(dest,1,80)]+[(dest+1+i,1,v)for i,v in enumerate(name)]+[(dest+len(name),1,96),(dest+len(name)+1,1,255)]


def outside_writes(machine,objects):
    allowed=set(range(machine.low_sp,vm.SP))
    for start,length in objects:
        need(type(start)is int and type(length)is int and 0<=start<start+length<=0x100000000,'object境界')
        span=set(range(start,start+length));need(not span&set(range(vm.STACK_LO,vm.STACK_HI)),'object/stack重複')
        allowed.update(span)
    return [list(w)for w in machine.writes if not all(w[0]+i in allowed for i in range(w[1]))]


def task_input(chain,priorities,target,priority):
    need(type(target)is int and 0<=target<COUNT and target not in chain,'target slot')
    need(len(chain)==len(priorities) and len(set(chain))==len(chain) and all(type(i)is int and 0<=i<COUNT for i in chain),'task列')
    need(all(type(p)is int and 0<=p<=255 for p in [*priorities,priority]) and list(priorities)==sorted(priorities),'priority列')
    data=bytearray(b'\xcc'*(COUNT*STRIDE))
    for i in range(COUNT):data[i*STRIDE+4:i*STRIDE+8]=bytes([0,255,255,0])
    for k,i in enumerate(chain):
        data[i*STRIDE+4:i*STRIDE+8]=bytes([1,chain[k-1]if k else 254,chain[k+1]if k+1<len(chain)else 255,priorities[k]])
    data[target*STRIDE+7]=priority
    return bytes(data)


def task_expected(chain,priorities,target,priority):
    data=bytearray(task_input(chain,priorities,target,priority));at=next((i for i,p in enumerate(priorities)if priority<p),len(chain))
    left=chain[at-1]if at else 254;right=chain[at]if at<len(chain)else 255
    writes=[(TASKS+target*STRIDE+5,1,left),(TASKS+target*STRIDE+6,1,right)]
    if left!=254:writes.append((TASKS+left*STRIDE+6,1,target))
    if right!=255:writes.append((TASKS+right*STRIDE+5,1,target))
    for address,_,value in writes:data[address-TASKS]=value
    return bytes(data),writes,[*chain[:at],target,*chain[at:]]


def head_expected(data):
    need(type(data)is bytes and len(data)==COUNT*STRIDE,'task領域長')
    return next((i for i in range(COUNT)if data[i*STRIDE+4]==1 and data[i*STRIDE+5]==254),COUNT)


def verify(nodes,analysis):
    need(len(nodes)==1859 and analysis['cached_node_count']==1752 and analysis['new_node_count']==107,'保存node件数')
    need(analysis['pending_direct_callees']==[0x0806dc49] and analysis['pending_continuations']==[],'先行未読集合')
    tables=analysis['tables'];frontier.validate_tables(tables[4:],nodes,[(t['start'],t['length'])for t in tables[:4]])
    need(tables[6]['hex']=='ff','fallback空文字原本')
    segments=[(t['start'],bytes.fromhex(t['hex']),False)for t in tables]
    rows=[];stops=[];negative=[]
    def record(machine,label,objects=()):
        need(not outside_writes(machine,objects),'object/frame外write '+label)
        row=c.effects(machine,label);row['object_and_owned_frame_writes_only']=True;rows.append(row);return row
    def stop(machine,entry,label,error,site,fault=None,budget=100000):
        try:machine.run(entry,budget)
        except ValueError as exc:
            need(str(exc)==error and (site is None or machine.last_pc==site),'停止境界 '+label)
            if fault is not None:need(machine.read_fault==fault,'read停止 '+label)
        else:raise ValueError('未証明境界を通過 '+label)
        row={'case':label,'stopped_at':machine.last_pc,'error':error,'read_fault':machine.read_fault,
             'stack_bytes_live':vm.SP-machine.r[13],'nonstack_writes':machine.nonstack_writes(),'return_proven':False}
        stops.append(row);return row
    def globals_(gender=0,rival=255,sb1=SB1,sb2=SB2):
        return [(GLOBAL1,sb1.to_bytes(4,'little'),False),(GLOBAL2,sb2.to_bytes(4,'little'),False),
            (sb2,bytes([32,33,255,0,0,0,0,0,gender]),False),(sb1+0x3a4c,bytes([rival,48,255]),False)]
    cases=[(i,0,255,SB1,SB2)for i in FIXED]
    cases.extend((1,0,255,SB1,p)for p in (SB2,0x02008000,0x02009000))
    cases.extend((5,g,255,SB1,SB2)for g in range(256))
    cases.extend((6,g,r,SB1,SB2)for r in (0,1,42,252,253,254,255)for g in (0,1,255))
    for index,gender,rival,sb1,sb2 in cases:
        machine=model.Machine(nodes,[*segments,*globals_(gender,rival,sb1,sb2)],(index,)).run(SELECTOR)
        need(machine.r[0]==getter_expected(index,gender,rival,sb1,sb2) and not machine.nonstack_writes(),'getter戻り値')
        record(machine,f'getter-{index}-{gender}-{rival}-{sb2}')
    for index,site,address in ((1,0x08008c9e,GLOBAL2),(5,0x08008cc4,GLOBAL2),(6,0x08008ce8,GLOBAL1)):
        machine=model.Machine(nodes,segments,(index,))
        stop(machine,SELECTOR,'getter-unmapped-global-'+str(index),'未map read',site,{'address':address,'size':4,'site':site})
    names={0:bytes([17,18,255]),1:bytes([32,33,255]),2:bytes([65,255]),3:bytes([66,67,255]),4:bytes([68,69,70,255]),6:bytes([49,48,255]),14:b'\xff',255:b'\xff'}
    name_segments=[(FIXED[i],names[i],False)for i in (0,2,3,4)]
    for index,name in names.items():
        data=bytes([80,253,index,96,255]);expected=bytes([80])+name[:-1]+bytes([96,255])
        machine=model.Machine(nodes,[(c.CTX,b'\xcc'*512,True),(c.CTX+1024,data,False),*segments,*globals_(0,49),*name_segments],(c.CTX,c.CTX+1024)).run(STRING)
        need(machine.data(c.CTX,len(expected))==expected and machine.r[0]==c.CTX+len(expected)-1,'FD展開')
        need(machine.nonstack_writes()==expanded_fd_writes(c.CTX,name),'FD書込範囲')
        record(machine,'FD-expanded-'+str(index),[(c.CTX,512)])
    string_cases=[(5,0),(5,1),(6,0),(6,1),*((i,0)for i in range(7,14))]
    for index,gender in string_cases:
        machine=model.Machine(nodes,[(c.CTX,b'\xcc'*512,True),(c.CTX+1024,bytes([253,index,255]),False),*segments,*globals_(gender)],(c.CTX,c.CTX+1024))
        stop(machine,STRING,'FD-unread-text-'+str(index)+'-'+str(gender),'未map read',0x08008b4e,
            {'address':getter_expected(index,gender),'size':1,'site':0x08008b4e})
    actual_nibbles=bytes.fromhex(tables[5]['hex'])
    for value in range(152):
        machine=model.Machine(nodes,segments,(value,)).run(NIBBLE)
        need(machine.r[0]==prior_contracts.nibble_expected(value,actual_nibbles) and not machine.nonstack_writes(),'実nibble値')
        record(machine,'actual-nibble-'+str(value))
    empty=task_input([],[],0,0)
    head_cases=[empty]
    for index in range(COUNT):
        for active in (0,1,2,255):
            for prev in (254,255):
                data=bytearray(empty);data[index*STRIDE+4:index*STRIDE+6]=bytes([active,prev]);head_cases.append(bytes(data))
    data=bytearray(empty)
    for i in (1,4):data[i*STRIDE+4:i*STRIDE+6]=bytes([1,254])
    head_cases.append(bytes(data))
    for index,data in enumerate(head_cases):
        machine=model.Machine(nodes,[(TASKS,data,False)],()).run(HEAD)
        need(machine.r[0]==head_expected(data) and not machine.nonstack_writes(),'head選択')
        record(machine,'task-head-'+str(index))
    inserts=[([],[],target,p,target)for target in range(COUNT)for p in (0,1,127,255)]
    inserts.extend(([1,4,7,11],[10,50,50,200],target,p,target)for target in range(COUNT)if target not in (1,4,7,11)for p in (0,10,30,50,51,200,255))
    inserts.extend(([head],[old],(head+1)%COUNT,new,(head+1)%COUNT)for head in range(COUNT)for old,new in ((0,0),(0,1),(1,0),(255,255)))
    inserts.extend(([1,4],[10,50],0,p,0x12340000)for p in (0,255))
    for index,(chain,priorities,target,p,arg) in enumerate(inserts):
        data=task_input(chain,priorities,target,p);expected,writes,order=task_expected(chain,priorities,target,p)
        if arg>255:
            data=bytearray(data);expected=bytearray(expected);data[target*STRIDE+4]=expected[target*STRIDE+4]=1
            data,expected=bytes(data),bytes(expected)
        machine=model.Machine(nodes,[(TASKS,data,True)],(arg,)).run(INSERT)
        need(machine.data(TASKS,len(data))==expected and machine.nonstack_writes()==writes,'task挿入/全領域不変')
        row=record(machine,'task-insert-'+str(index),[(TASKS,len(data))]);row['order_after']=order;row['return_value_semantically_unspecified']=True
    machine=model.Machine(nodes,[(TASKS,empty,True)],(16,))
    stop(machine,INSERT,'task-invalid-slot-16','未許可 write',0x08076c2a)
    machine=model.Machine(nodes,[(TASKS,empty,True)],(255,)).run(INSERT)
    escaped=outside_writes(machine,[(TASKS,len(empty))])
    need(escaped==[[TASKS+255*STRIDE+5,1,254],[TASKS+255*STRIDE+6,1,255]],'slot255 frame外診断')
    negative.append({'case':'task-invalid-slot-255','classification':'SYNTHETIC_RETURN_WITH_OUT_OF_OBJECT_STACK_WRITES_NOT_ACCEPTED',
        'escaped_writes':escaped,'accepted':False,'live_caller_out_of_range_proven':False})
    cyclic=bytearray(task_input([1,4],[10,20],0,255));cyclic[4*STRIDE+6]=4
    machine=model.Machine(nodes,[(TASKS,bytes(cyclic),True)],(0,))
    stop(machine,INSERT,'task-cyclic-input','step上限到達',None,budget=1000)
    for value in (0,1,126,127,128,255,0x17f):
        machine=model.Machine(nodes,[(prior_contracts.GATE_WORD,(1).to_bytes(4,'little'),False),(GATE_CONTEXT,bytes(32),True)],(17,value,9))
        row=stop(machine,prior_contracts.GATE,'nonnull-gate-'+str(value),'保存node境界で停止',0x08002d14)
        need(machine.r[5]==(1 if value&255==127 else value&255) and machine.r[6]==17 and machine.r[12]==9,'nonnull register')
        need(machine.nonstack_writes()==[(GATE_CONTEXT+27,1,1)] and not outside_writes(machine,[(GATE_CONTEXT,32)]),'nonnull書込')
        row['effective_target']=0x08002d15
    for value in (0,1,0x3fff,0x4000,0x4010,0x410f,0xffff,0x14010):
        machine=model.Machine(nodes,[],(value,));row=stop(machine,VARGET,'var-prefix-'+str(value),'保存node境界で停止',0x0806dc48)
        need(machine.r[0]==value&65535 and machine.r[4]==value&65535 and row['stack_bytes_live']==8 and not machine.nonstack_writes(),'var callee frame')
    need(len(rows)==795 and len(stops)==31 and len(negative)==1,'契約件数差分')
    return {'classification':'PLACEHOLDER_GETTERS_TASK_LIST_AND_ACTUAL_NIBBLES_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'synthetic_contract_cases':len(rows),'contracts':rows,'limited_prefix_stops':stops,'negative_diagnostics':negative,
        'placeholder_table_thunk_and_14_getters_bounded_proven':True,'dynamic_placeholder_fixture_expansions':6,
        'fallback_empty_body_proven':True,'actual_nibble_values_checked':152,'task_insertion_cases':len(inserts),
        'all_runtime_string_inputs_proven':False,'task_live_caller_index_lt16_proven':False,
        'pending_direct_callees':[0x0806dc49],'pending_effective_targets':[0x08002d15],
        'pending_data_ranges':text_windows(),'pending_continuations':[],
        'all_callers_resolved':False,'all_live_frames_proven':False,'all_runtime_owners_excluded':False,
        'caller_pointer_size_limit_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_byte_samples':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'preconditions':['gettersの実ROM tableと保存byteを使うがsave/global/nameは明示合成fixture。native/story到達ではない',
            'task正常契約はtarget<16・既存列に未挿入・整合した非循環priority昇順列が前提。active化/実callerは未証明',
            'slot255は自動mapされたstack内でも実frame外へ書く。SP帰還だけを安全性/受入にせず負診断で保持',
            'ROM文字列11本は推測せず先頭の正確な未map地点で停止。次は合計83byte以下の非重複窓だけを採取']}


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    nodes,_,_=frontier.saved_inputs();nodes=[*nodes,*prior['analysis']['new_nodes']]
    result=verify(nodes,prior['analysis']);result['candidate']=copy.deepcopy(s.CANDIDATE)
    (out/'analysis.json').write_bytes(s.stable(result))
    (out/'summary.json').write_bytes(s.stable({k:result[k]for k in ('classification','synthetic_contract_cases',
        'actual_nibble_values_checked','task_insertion_cases','negative_diagnostics','pending_direct_callees','pending_effective_targets','pending_data_ranges')}))
    return result


def summaries(result):
    return (f'保存1859命令で{result["synthetic_contract_cases"]}新規合成契約、31停止境界とslot255の負診断を結合。'
        'placeholder14参照/実nibble152値/task挿入214件を限定検証。実caller範囲とRing取得は未証明。',
        '残るcallee0x0806DC49と非null継続0x08002D15、11本のROM文字列を保存pendingの非重複窓（合計83byte）だけ有限採取する。'
        '次の契約では実callerのtask index<16/非循環列/文字列buffer境界を別途結合し、slot255診断を実ゲームbugや正常受入に読み替えない。'
        '同じ採取/旧795・716契約/FC/memset/BPを単独再実行しない。Ring正規story取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import pr16_ring_followup_v2 as support
    import pr16_ring_dependency_contracts as old_contracts
    SOURCES=tuple(dict.fromkeys((*SOURCES,*old_contracts.SOURCES)))
    need(sys.argv[1:]==['run'],'runだけを許可');support.run(sys.modules[__name__])
