#!/usr/bin/env python3
"""保存external3継続20命令だけを検証。4書込と再読取の順序を保持する。"""
from __future__ import annotations
import copy
from functools import lru_cache
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE='cd3070a49b33707b1c15fa42c903a9c669b9967b'
SLUG='pr16-ring-external3-body-abi'
TASK='PR-P08-7-RING-EXTERNAL3-BODY-ABI'
TITLE='external3継続の順序付き4書込・再読取・非alias境界を検証'
SELF='scripts/pr16_ring_external3_body_abi.py'
TEST='tests/test_pr16_ring_external3_body_abi.py'
WORKFLOW='.github/workflows/pr16-ring-external3-body-abi.yml'
PRIOR='content/modernization/pr16_ring_external3_body_bytes.json'
REPORT='content/modernization/pr16_ring_external3_body_abi.json'
PREFIX='content/modernization/pr16_ring_external3_abi.json'
KEY='ring_external3_body_abi'
SOURCES=(PREFIX,)
EXTRA_CODE=()
MIN_TESTS=22
START,TAIL,COUNTER,BASE_PTR,MASK=0x08113938,0x08113961,0x0203AF96,0x0300202C,0xffffffff
CODE=('0843','1080','3188','8900','0919','fb01','4a78','7f20','1040','1843',
      '4870','3088','2968','8000','4018','6146','4180','3088','0130','3080')
WRITE_OFFSETS=(2,20,32,38)
NO_REPEAT='external3継続20命令/40byteのABIは完了。4書込の順序とcounter/baseの再読取を保存契約として再利用し、再採取/単独ABI再実行しない。次は未読末尾0x08113961だけ。record/counter/base/frame非alias・外側帰還・旧18owner・Ring通常取得は未証明。'


def program(prior):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL3-BODY-BYTES','先行task差分');a=prior['analysis'];g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and a['target']==a['next_saved_abi_target']==START|1,'candidate/target差分')
    s.need(g['entry']==START|1 and g['window']==64 and g['window_identity']==
           {'size':64,'sha256':'b53105c5b9d543a9f8d52c90dce233ffa89f2ea18d2d7a9ce211a8cf06cdbfe1'},'window差分')
    nodes=[dict(address=START+2*i,size=2,hex=hx,kind='ordinary',memory_write=(2*i in WRITE_OFFSETS),
                successors=[START+2*i+2] if i<19 else []) for i,hx in enumerate(CODE)]
    edges=[dict(site=START+38,kind='window_fallthrough',target=TAIL,resolved_to_code_address_only=True,
                stop_reason='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED')]
    ranges=[dict(address=START+2*i,hex=hx,**s.identity(bytes.fromhex(hx))) for i,hx in enumerate(CODE)]
    s.need(g['nodes']==nodes and g['external_edges']==edges and g['memory_write_sites']==[START+o for o in WRITE_OFFSETS],'命令/辺/書込差分')
    s.need(a['sampled_ranges']==ranges and a['sampled_instruction_bytes']==40,'保存byte/hash差分')
    s.need(g['saved_instruction_bytes_redecoded']==g['deferred_roots_decoded']==0,'再decode')
    old=set(a['old_unread_targets']);s.need(len(old)==18 and set(a['remaining_unread_targets'])==old|{TAIL},'frontier差分')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False,'過大受入')
    return a


def join(prefix):
    s.need(prefix['candidate']==s.CANDIDATE and prefix['frame_bytes_live']==20 and prefix['local_sp_delta']==-20,'保存prefix frame差分')
    c=prefix['continuation_contract']
    s.need(c=={'target':START|1,'r0':'loaded_record_halfword & 0x8000','r1':'input_r1 & 0x7fff',
        'r2':'(loaded_base_word + 4 * loaded_u16_index) mod 2^32','r3':'loaded_record_halfword',
        'r4':'loaded_base_word','r5':BASE_PTR,'r6':COUNTER,'r7':'input_r0 & 0xff','r12':'input_r2 & 0xffff','frame_bytes_live':20},'保存prefix引数差分')
    s.need(prefix['early_exit_target']==TAIL and prefix['early_exit_is_return_proven'] is False
           and prefix['hypothetical_stack_overwrites_counter']['observed'] is False,'prefix境界差分')
    return copy.deepcopy(c)


def inputs(index=0,key=1,mode=0,value=2,old_record=0x8000,base=0x02010000):
    """保存境界契約から局所診断入力を構成。先行ABIは実行しない。"""
    s.need(all(type(x)is int and 0<=x<=65535 for x in (index,key,value,old_record)),'u16範囲')
    s.need(type(mode)is int and 0<=mode<=255 and type(base)is int and 0<=base<=MASK and base%2==0,'mode/base差分')
    e=(base+4*index)&MASK;r=[0]*16
    r[0:8]=[old_record&0x8000,key&0x7fff,e,old_record,base,BASE_PTR,COUNTER,mode]
    r[12]=value;r[13]=0x03007EEC;r[14]=0x08100001;mem={}
    for at,width,v in ((COUNTER,2,index),(BASE_PTR,4,base),(e,2,old_record)):
        for j,b in enumerate(v.to_bytes(width,'little')):
            s.need(at+j<=MASK and (at+j not in mem or mem[at+j]==b),'snapshot不一致');mem[at+j]=b
    return r,mem


def execute(registers,memory):
    s.need(len(registers)==16 and all(type(x)is int and 0<=x<=MASK for x in registers),'register範囲')
    r=list(registers);mem=dict(memory);reads=[];writes=[]
    s.need(all(type(a)is int and 0<=a<=MASK and type(v)is int and 0<=v<=255 for a,v in mem.items()),'memory範囲')
    for i,hx in enumerate(CODE):
        at=START+2*i;h=int.from_bytes(bytes.fromhex(hx),'little');op=h&0xf800
        if h&0xffc0 in (0x4000,0x4300):
            if h&0xffc0==0x4000:r[h&7]&=r[(h>>3)&7]
            else:r[h&7]|=r[(h>>3)&7]
        elif op==0:
            r[h&7]=(r[(h>>3)&7]<<((h>>6)&31))&MASK
        elif op==0x1800:
            s.need(h&0x600==0,'未対応ADD');r[h&7]=(r[(h>>3)&7]+r[(h>>6)&7])&MASK
        elif op==0x2000:r[(h>>8)&7]=h&255
        elif op==0x3000:r[(h>>8)&7]=(r[(h>>8)&7]+(h&255))&MASK
        elif h&0xff00==0x4600:r[(h&7)|((h>>4)&8)]=r[(h>>3)&15]
        elif op in (0x8000,0x8800,0x7000,0x7800,0x6800):
            width=2 if op in (0x8000,0x8800) else (4 if op==0x6800 else 1)
            addr=(r[(h>>3)&7]+((h>>6)&31)*width)&MASK
            s.need(addr%width==0 and addr+width-1<=MASK,'非整列/範囲外memory')
            if op in (0x8000,0x7000):
                val=r[h&7]&((1<<(8*width))-1)
                mem.update({addr+j:b for j,b in enumerate(val.to_bytes(width,'little'))})
                writes.append(dict(site=at,address=addr,size=width,value=val))
            else:
                s.need(all(addr+j in mem for j in range(width)),'未提供RAM読取')
                val=int.from_bytes(bytes(mem[addr+j] for j in range(width)),'little');r[h&7]=val
                reads.append(dict(site=at,address=addr,size=width,value=val))
        else:raise ValueError('未対応命令')
    s.need(r[4:8]==list(registers[4:8]) and r[8:16]==list(registers[8:16]),'局所保存register差分')
    return {'registers':r,'memory':mem,'reads':reads,'writes':writes,'boundary':TAIL,'boundary_executed':False,'local_sp_delta':0}


def half(mem,address):return int.from_bytes(bytes(mem[address+j] for j in range(2)),'little')


@lru_cache(maxsize=1)
def sweep():
    for v in range(65536):
        args=dict(index=v,key=v,mode=v&255,value=65535-v,old_record=v,base=(0x02010000-4*v)&MASK);regs,mem=inputs(**args);r=execute(regs,mem)
        e=regs[2];expected=(v&0x7fff)|((v&1)<<15)
        s.need(half(r['memory'],e)==expected and half(r['memory'],e+2)==65535-v
               and half(r['memory'],COUNTER)==(v+1)&65535 and r['registers'][0]==v+1,'独立式差分')
        s.need([w['address'] for w in r['writes']]==[e,e+1,e+2,COUNTER]
               and [w['size'] for w in r['writes']]==[2,1,2,2],'順序/幅差分')
    return {'independent_local_boundary_cases':65536,'all_u16_key_value_index_values_covered':True,
            'all_u8_modes_covered':True,'prefix_reachability_not_claimed_for_every_case':True,'non_alias_record_address':0x02010000}


def alias_diagnostics():
    regs,mem=inputs(index=0,key=1,mode=0,value=0xbeef,old_record=0,base=COUNTER)
    mem[COUNTER+5]=0x12;r=execute(regs,mem)
    s.need([w['address'] for w in r['writes']]==[COUNTER,COUNTER+5,COUNTER+6,COUNTER]
           and half(r['memory'],COUNTER)==2,'counter再読取差分')
    counter={'writes':r['writes'],'observed':False,'single_record_address_formula_valid':False}
    regs,mem=inputs(index=0,key=0x2000,mode=0,value=0xbeef,old_record=BASE_PTR&65535,base=BASE_PTR)
    r=execute(regs,mem)
    s.need(r['writes'][2]['address']==0x03002002 and r['writes'][0]['address']==BASE_PTR,'base再読取差分')
    base_case={'writes':r['writes'],'observed':False,'base_reloaded_after_prior_stores':True}
    regs,mem=inputs(index=44005,key=44005,mode=229,value=21530,old_record=44005)
    r=execute(regs,mem)
    s.need(r['writes'][2]['address']==COUNTER and half(r['memory'],COUNTER)==21531,'value/counter再読取差分')
    return {'record_aliases_counter':counter,'record_aliases_base_pointer':base_case,
        'value_aliases_counter':{'writes':r['writes'],'observed':False,'increment_uses_written_value_not_entry_index':True},
        'native_observation':False}


def analyze(prior,out):
    a=program(prior);inherited=join(s.load(PREFIX)['analysis'])
    return {'classification':'EXTERNAL3_ORDERED_RECORD_WRITES_AND_COUNTER_BASE_RELOAD_ABI',
        'candidate':copy.deepcopy(s.CANDIDATE),'instructions_verified':20,'instruction_bytes_verified':40,
        'local_sp_delta':0,'inherited_frame_bytes_live':20,'next_unread_return_target':TAIL,
        'inherited_contract':inherited,'saved_prefix_reused_not_executed':True,
        'diagnostic_cases':copy.deepcopy(sweep()),'ordered_store_widths':[2,1,2,2],
        'ordered_store_sites':[START+o for o in WRITE_OFFSETS],
        'non_alias_formula':{'record_address':'E = (inherited_base + 4 * inherited_index) mod 2^32',
            'record_header':'(inherited_key & 0x7fff) | ((inherited_mode & 1) << 15)',
            'record_value':'inherited_value & 0xffff at E + 2','counter':'(inherited_index + 1) mod 2^16',
            'tail_r0':'inherited_index + 1 (u32; may be 65536 for an independent local input)',
            'valid_without_alias_preconditions':False},
        'reload_order':['STRH inherited_E','LDRH counter','STRB inherited_base+4*reloaded_index+1',
                        'LDRH counter','LDR base_pointer','STRH reloaded_base+4*reloaded_index+2',
                        'LDRH counter','STRH counter+1'],
        'alias_diagnostics':alias_diagnostics(),
        'proof_assumptions_ja':['各読書きアドレスが有効/整列済みの通常memoryである。',
            '単一Eの要約式にはrecord書込がcounter/base_pointerを変更せずframeを破壊しない条件が必要。',
            '順序付きモデルは書込を反映して再読取する。native観測や未読末尾の帰還を証明しない。'],
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[TAIL],'unresolved_indirect_edges':a['unresolved_indirect_edges'],
        'prior_external_indirect_edges_preserved':a['prior_external_indirect_edges_preserved'],
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_graph_decodes':0,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return ('external3継続20命令/40byteのSTRH→STRB→STRH→STRHとcounter/base再読取を65536局所境界入力で検証。'
        'record/counter・record/base pointer・value/counterの3つの仮想alias反例を保存。前半ABI/ROM復元/nativeの再実行0。',
        '次は未読末尾0x08113961の1根だけを限定採取し、保存byteの帰還ABIとprefix/bodyの条件付き合成を検証する。'
        '既読継続は再実行しない。record/counter/base/frame非alias・旧18owner・Ring通常取得・policy/Circus・P08最終判定は未完。')

if __name__=='__main__':
    sys.modules.setdefault('pr16_ring_external3_body_abi',sys.modules[__name__])
    s.run(sys.modules[__name__])
