#!/usr/bin/env python3
"""保存external1継続18命令のpointer選択/STRH。prefixと末尾は実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE='b2685c0e9117989177b8ced6314ca6f780730aee'
SLUG='pr16-ring-external1-cont-abi'
TASK='PR-P08-7-RING-EXTERNAL1-CONT-ABI'
TITLE='保存継続の15bit key/1bit mode照合とpointer返却・counter書込を検証'
SELF='scripts/pr16_ring_external1_cont_abi.py'
TEST='tests/test_pr16_ring_external1_cont_abi.py'
WORKFLOW='.github/workflows/pr16-ring-external1-cont-abi.yml'
PRIOR='content/modernization/pr16_ring_external1_cont_bytes.json'
REPORT='content/modernization/pr16_ring_external1_cont_abi.json'
PREFIX='content/modernization/pr16_ring_external1_abi.json'
KEY='ring_external1_cont_abi'
SOURCES=(PREFIX,)
MIN_TESTS=20
EXTRA_CODE=()
NO_REPEAT='external1保存継続18命令のpointer/条件付きcounter STRHは検証済み。再採取・単独ABI再実行をせず末尾0x081138F1へ。counter/返却pointerの保存slot非aliasと格納域サイズは未証明。'
START,EXIT,COUNTER=0x081138C8,0x081138F0,0x0203AF96
MASK=(1<<32)-1
CODE=dict(zip([*range(START,0x081138E8,2),0x081138EC,0x081138EE],
              ('0168','9800','4218','1168','4804','400c','a842','09d1','0804','c00f','b042','05d1','911c','581c','2080','02e0','0021','081c')))


def expected_nodes():
    nodes=[]
    for at,hx in CODE.items():
        h=int.from_bytes(bytes.fromhex(hx),'little')
        n=dict(address=at,size=2,hex=hx,kind='ordinary',memory_write=at==0x081138E4)
        successors=[at+2] if at+2 in CODE else []
        if h&0xff00==0xd100:
            n.update(kind='conditional',target=0x081138EC);successors=[at+2,0x081138EC]
        elif h==0xe002:n.update(kind='jump',target=0x081138EE);successors=[0x081138EE]
        n['successors']=successors;nodes.append(n)
    return nodes


def program(a):
    g=a['graph'];c=a['inherited_prefix_boundary']
    s.need(a['candidate']==s.CANDIDATE and a['target']==START|1,'candidate/target差分')
    s.need(g['entry']==START|1 and g['window']==64 and g['window_identity']==
           {'size':64,'sha256':'4b644247477cc75b70ee272a1685ce71d62d5853951b7b4f53c9496193fb719d'},'window差分')
    s.need(g['nodes']==expected_nodes() and g['memory_write_sites']==[0x081138E4],'命令/CFG/STRH差分')
    s.need(g['external_edges']==[dict(site=0x081138EE,kind='window_fallthrough',target=EXIT|1,
           resolved_to_code_address_only=True,stop_reason='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED')],'末尾境界差分')
    ranges=[dict(address=p,hex=h,**s.identity(bytes.fromhex(h))) for p,h in CODE.items()]
    s.need(a['sampled_ranges']==ranges and a['sampled_instruction_bytes']==36,'sample hash差分')
    s.need(c['target']==START|1 and c['frame_bytes_live']==16 and c['r0']==0x0300202C and c['r4']==COUNTER,'継承契約差分')
    s.need(g['saved_instruction_bytes_redecoded']==0 and g['deferred_roots_decoded']==0,'重複decode')
    s.need(len(set(a['old_unread_targets']))==18 and EXIT|1 in a['remaining_unread_targets'],'残件欠落')
    for k in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
              'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[k] is False,'過大受入')
    return g['nodes']


def execute(mode,key,index,base_word,record_word,code=None):
    """LDRの観測wordを入力に有限解釈。未観測buffer有効性/非aliasは主張しない。"""
    code=CODE if code is None else code;s.need(code==CODE,'保存code以外')
    for value,limit in ((mode,255),(key,65535),(index,65535),(base_word,MASK),(record_word,MASK)):
        s.need(type(value) is int and 0<=value<=limit,'入力範囲')
    r=[0]*16;r[0]=0x0300202C;r[3]=index;r[4]=COUNTER;r[5]=key;r[6]=mode;r[13]=0x03007000
    pc=START;seen=[];loads=[];writes=[];equal=None
    while pc in code:
        s.need(pc not in seen,'loop');seen.append(pc);h=int.from_bytes(bytes.fromhex(code[pc]),'little');after=pc+2
        if h&0xf800==0x6800:
            addr=(r[(h>>3)&7]+((h>>6)&31)*4)&MASK;value=(base_word,record_word)[len(loads)]
            loads.append({'site':pc,'address':addr,'value':value});r[h&7]=value
        elif h&0xf800 in (0x0000,0x0800):
            n=(h>>6)&31;v=r[(h>>3)&7];r[h&7]=(v<<n)&MASK if h&0xf800==0 else v>>(n or 32)
        elif h&0xfe00==0x1800:r[h&7]=(r[(h>>3)&7]+r[(h>>6)&7])&MASK
        elif h&0xfe00==0x1c00:r[h&7]=(r[(h>>3)&7]+((h>>6)&7))&MASK
        elif h&0xffc0==0x4280:equal=r[h&7]==r[(h>>3)&7]
        elif h&0xff00==0xd100:
            s.need(equal is not None,'比較前BNE')
            if not equal:after=pc+4+(h&255)*2
        elif h&0xf800==0x8000:
            writes.append({'site':pc,'address':(r[(h>>3)&7]+((h>>6)&31)*2)&MASK,'size':2,'value':r[h&7]&65535})
        elif h&0xf800==0x2000:r[(h>>8)&7]=h&255
        elif h==0xe002:after=pc+8
        else:raise ValueError('未知命令')
        pc=after
    s.need(pc==EXIT and len(loads)==2,'未読境界逸脱')
    return {'boundary':EXIT|1,'r0':r[0],'r4':r[4],'r5':r[5],'r6':r[6],
            'loads':loads,'writes':writes,'visited':seen,'local_sp_delta':r[13]-0x03007000,
            'unread_code_executed':False}


def analyze(prior,out):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL1-CONT-BYTES','先行task差分');a=prior['analysis'];program(a)
    prefix=s.load(PREFIX)['analysis']
    s.need(prefix['boundary_contracts']['continuation']==a['inherited_prefix_boundary'],'保存prefix結合差分')
    seen=set()
    for key in range(65536):
        r=execute(1,key,7,0x02010000,0xABCD9234);seen.update(r['visited']);match=key==0x1234
        s.need(r['r0']==(0x0201001E if match else 0) and len(r['writes'])==int(match),'15bit照合差分')
    for mode in range(256):
        r=execute(mode,0x1234,7,0x02010000,0xABCD9234);seen.update(r['visited'])
        s.need(r['r0']==(0x0201001E if mode==1 else 0),'1bit照合差分')
    wrap=execute(0,0,0xffff,0x02000000,0)
    s.need(wrap['writes'][0]['value']==0 and wrap['r0']==0x0203FFFE,'counter wrap差分')
    s.need(seen==set(CODE),'未検査命令')
    return {'classification':'EXTERNAL1_CONTINUATION_POINTER_AND_COUNTER_EFFECT_UNDER_READ_OBSERVATIONS',
        'candidate':copy.deepcopy(s.CANDIDATE),'instructions_verified':18,'instruction_bytes_verified':36,
        'key_cases':65536,'mode_cases':256,'local_sp_delta':0,'local_call_count':0,
        'inherited_frame_bytes_live':16,'next_unread_return_target':EXIT|1,
        'pointer_formula':'E = (observed_base_word + 4 * inherited_u16_index) mod 2^32; result = (E + 2) mod 2^32 on match, otherwise 0',
        'match_formula':'(observed_record_word & 0x7fff) == inherited_u16_key and ((observed_record_word >> 15) & 1) == inherited_u8_mode',
        'counter_write':{'site':0x081138E4,'address':COUNTER,'size':2,'value':'(inherited_u16_index + 1) mod 2^16','only_on_match':True},
        'record_payload_high16_ignored_by_match':True,'explicit_store_to_computed_record_address_count':0,
        'counter_record_buffer_non_alias_proven':False,
        'memory_access_safety_proven':False,'buffer_extent_proven':False,'base_alignment_proven':False,
        'word_reads_are_observation_inputs_not_native_execution':True,
        'hypothetical_counter_saved_lr_overlap':{'external1_entry_sp':0x0203AF98,'saved_lr_word_address':0x0203AF94,'strh_address':COUNTER,'observed':False},
        'hypothetical_return_pointer_saved_slot_overlap':{'observed_base_word':0x03006FF0,'index':0,'pointer':0x03006FF2,'saved_word_address':0x03006FF0,'observed':False},
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[EXIT|1,0x0806DD1D,0x081138F9],
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,
        'release_ready':False,'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,
        'new_graph_decodes':0,'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return ('保存継続18命令/36byteの15bit key/1bit mode照合を65792件で検証。一致時だけrecord+2 pointerとcounter STRH、不一致は0。'
        'counter wrapと保存LR/返却pointerの仮想alias反例を保持。bufferの範囲/整列/非aliasと帰還は未証明。prefix/ROM/native実行0。',
        '次は未読帰還末尾0x081138F1の1根だけ採取し、その保存byteの復元/帰還ABIを検証する。'
        'prefix/継続の再実行禁止。0x0806DD1D/0x081138F9・旧18owner・保存slot非aliasを未完で保持しRing通常取得へ昇格しない。')

if __name__=='__main__':s.run(sys.modules[__name__])
