#!/usr/bin/env python3
"""保存external1 prefixのみのABI。未読継続・ROM・nativeには触れない。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s
BASE='4ea46b7ba0ca118435b37e708527cd05bc8f41a1'
SLUG='pr16-ring-external1-abi'
TASK='PR-P08-7-RING-EXTERNAL1-ABI'
TITLE='保存外部callee prefixの引数切詰め・条件分岐・stack書込境界を検証'
SELF='scripts/pr16_ring_external1_abi.py'
TEST='tests/test_pr16_ring_external1_abi.py'
WORKFLOW='.github/workflows/pr16-ring-external1-abi.yml'
PRIOR='content/modernization/pr16_ring_external1_bytes.json'
REPORT='content/modernization/pr16_ring_external1_abi.json'
KEY='ring_external1_abi'
SOURCES=()
EXTRA_CODE=()
MIN_TESTS=18
NO_REPEAT='0x08113889の保存prefix ABIは完了。再採取/単独ABI再実行をせず、未読0x081138C9/0x081138F1のみを進める。局所stack書込を全副作用なし/帰還/owner除外に昇格しない。'
START=0x08113888
CONT,EXIT=0x081138C8,0x081138F0
CODE=dict(zip([*range(START,0x081138B2,2),0x081138C4,0x081138C6],
              ('70b5','0006','060e','0904','0d0c','0848','0188','0029','09d0','0748','0088',
               '8142','05d2','064c','0649','2088','0988','8842','0ad3','0020','1ee0','2388','0848')))
LITERALS={0x081138B4:0x0203AF10,0x081138B8:0x03005EDC,0x081138BC:0x0203AF96,
          0x081138C0:0x03002030,0x081138E8:0x0300202C}
MASK=(1<<32)-1
STOP='SAVED_OR_DEFERRED_OR_WINDOW_BOUNDARY_NOT_DECODED'


def expected_nodes():
    nodes=[]
    for at,text in CODE.items():
        h=int.from_bytes(bytes.fromhex(text),'little')
        kind='conditional' if h&0xf000==0xd000 else 'jump' if h&0xf800==0xe000 else 'ordinary'
        n=dict(address=at,size=2,hex=text,kind=kind,memory_write=at==START)
        successors=[at+2] if at+2 in CODE else []
        if kind!='ordinary':
            bits=8 if kind=='conditional' else 11;off=h&((1<<bits)-1)
            if off&(1<<(bits-1)):off-=1<<bits
            target=at+4+2*off;n['target']=target
            successors=([at+2,target] if kind=='conditional' else [target])
            successors=[p for p in successors if p in CODE]
        if h&0xf800==0x4800:
            p=((at+4)&~3)+(h&255)*4;n.update(literal_address=p,literal_value=LITERALS[p])
        n['successors']=successors;nodes.append(n)
    return nodes


def expected_ranges():
    values={p:bytes.fromhex(h) for p,h in CODE.items()}
    values.update({p:v.to_bytes(4,'little') for p,v in LITERALS.items()})
    return [dict(address=p,hex=b.hex(),**s.identity(b)) for p,b in sorted(values.items())]


def program(a):
    g=a['graph']
    s.need(a['candidate']==s.CANDIDATE and a['target']==START|1,'candidate/entry差分')
    s.need(g['entry']==START|1 and g['window']==64 and g['window_identity']==
           {'size':64,'sha256':'e100b51b7f2c73e835baefbe2aa45c0f57ef07031e8fb4f025a856ef7eaa67d4'},'window差分')
    s.need(g['nodes']==expected_nodes() and g['memory_write_sites']==[START],'命令/辺/literal差分')
    edges=[dict(site=0x081138B0,kind='jump',target=EXIT|1,resolved_to_code_address_only=True,stop_reason=STOP),
           dict(site=0x081138C6,kind='window_fallthrough',target=CONT|1,resolved_to_code_address_only=True,stop_reason=STOP)]
    s.need(g['external_edges']==edges and g['saved_instruction_bytes_redecoded']==0
           and g['deferred_roots_decoded']==0,'採取境界差分')
    s.need(a['sampled_ranges']==expected_ranges() and a['sampled_instruction_bytes']==46,'sample identity差分')
    s.need(len(set(a['old_unread_targets']))==18 and {CONT|1,EXIT|1}<=set(a['remaining_unread_targets']),'残件欠落')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False,'過大受入')
    return g['nodes']


def execute(arg0,arg1,reads,initial=None,code=None):
    """各LDRH観測値を独立入力とする。再読の値不変・RAMとstackの非aliasは仮定しない。"""
    code=CODE if code is None else code
    s.need(code==CODE,'保存命令以外を拒否')
    initial={4:0x44444444,5:0x55555555,6:0x66666666,13:0x03007F00,14:0x08000001} if initial is None else initial
    s.need(set(initial)=={4,5,6,13,14},'初期register不足')
    s.need(all(type(v) is int and 0<=v<=MASK for v in [arg0,arg1,*initial.values()]),'register範囲')
    s.need(initial[13]%4==0 and initial[13]>=16,'stack alignment/underflow')
    s.need(all(type(v) is int and 0<=v<=0xffff for v in reads),'LDRH範囲')
    r=[0]*16;r[0]=arg0;r[1]=arg1
    for k,v in initial.items():r[k]=v
    pc=START;seen=[];stores=[];loads=[];flags=None
    while pc in code:
        s.need(pc not in seen,'loop');seen.append(pc)
        h=int.from_bytes(bytes.fromhex(code[pc]),'little');after=pc+2
        if h==0xb570:
            r[13]-=16;stores=[{'address':r[13]+i*4,'value':r[k],'register':k} for i,k in enumerate((4,5,6,14))]
        elif h&0xf800 in (0x0000,0x0800):
            shift=(h>>6)&31;src=r[(h>>3)&7]
            r[h&7]=(src<<shift)&MASK if h&0xf800==0 else src>>(shift or 32)
        elif h&0xf800==0x4800:r[(h>>8)&7]=LITERALS[((pc+4)&~3)+(h&255)*4]
        elif h&0xf800==0x8800:
            s.need(len(loads)<len(reads),'LDRH観測値不足');addr=(r[(h>>3)&7]+((h>>6)&31)*2)&MASK
            value=reads[len(loads)];loads.append({'site':pc,'address':addr,'value':value});r[h&7]=value
        elif h&0xffc0==0x4280:flags=(r[h&7],r[(h>>3)&7])
        elif h&0xf800==0x2800:flags=(r[(h>>8)&7],h&255)
        elif h&0xf000==0xd000:
            s.need(flags is not None,'比較前分岐');x,y=flags;cond=(h>>8)&15
            take={0:x==y,2:x>=y,3:x<y}[cond];off=h&255;off=off-256 if off&128 else off
            if take:after=pc+4+2*off
        elif h&0xf800==0x2000:r[(h>>8)&7]=h&255
        elif h&0xf800==0xe000:
            off=h&2047;off=off-2048 if off&1024 else off;after=pc+4+2*off
        else:raise ValueError('未知命令')
        pc=after
    s.need(pc in (CONT,EXIT) and len(loads)==len(reads),'未読境界/観測値数不一致')
    return {'boundary':pc|1,'registers':r,'loads':loads,'stack_writes':stores,
            'local_sp_delta':r[13]-initial[13],'visited':seen,'nonstack_store_count':0,
            'unread_code_executed':False}


def analyze(prior,out):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL1-BYTES','先行task不一致')
    a=prior['analysis'];program(a)
    scenarios=([0],[1,1],[0xffff,0x8000],[1,2,3,3],[1,2,0xffff,1],
               [1,2,0,1,0],[1,2,0,1,0xffff],[0x8000,0xffff,0x7fff,0x8000,123])
    seen=set();records=[]
    for values in scenarios:
        r=execute(0x123456AB,0x8765FEDC,values);seen.update(r['visited'])
        s.need(r['registers'][6]==0xab and r['registers'][5]==0xfedc and r['local_sp_delta']==-16,'ABI差分')
        records.append({'reads':values,'boundary':r['boundary'],'read_addresses':[x['address'] for x in r['loads']]})
    s.need(seen==set(CODE),'未検査命令')
    for value in range(256):s.need(execute(0xA5000000|value,0,[0])['registers'][6]==value,'u8切詰め')
    for value in range(65536):s.need(execute(0,0xA5000000|value,[0])['registers'][5]==value,'u16切詰め')
    return {'classification':'EXTERNAL1_PREFIX_LOCAL_ABI_NOT_CALLEE_RETURN_OR_SIDE_EFFECT_EXCLUSION',
        'candidate':copy.deepcopy(s.CANDIDATE),'target':START|1,'instructions_verified':23,
        'instruction_bytes_verified':46,'literal_bytes_verified':20,'argument_truncation_cases':256+65536,
        'branch_diagnostics':records,'local_sp_delta':-16,'stack_write_words':4,'saved_register_order':[4,5,6,14],
        'local_nonstack_store_count':0,'local_call_count':0,
        'boundary_contracts':{'early_exit':{'target':EXIT|1,'r0':0,'frame_bytes_live':16},
            'continuation':{'target':CONT|1,'r0':0x0300202C,'r1':'fourth LDRH result',
                'r3':'fifth independent LDRH result','r4':0x0203AF96,'r5':'u16(entry_r1)','r6':'u8(entry_r0)','frame_bytes_live':16}},
        'predicate_ja':'h[0203AF10]!=0 かつ h[0203AF10]<h[03005EDC] かつ初回h[0203AF96]<h[03002030]なら継続。それ以外はr0=0で未読末尾へ。全比較はunsigned。',
        'repeated_ram_read_stability_assumed':False,'ram_stack_non_alias_proven':False,
        'old_unread_targets':a['old_unread_targets'],'remaining_unread_targets':a['remaining_unread_targets'],
        'priority_unread_targets':[CONT|1,EXIT|1,0x0806DD1D,0x081138F9],
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'new_graph_decodes':0,'accepted_native_cases_replayed':0,
        'prior_abi_classifications_replayed':0}


def summaries(a):
    return ('外部callee0x08113889の保存23命令/46byte・literal20byteで局所ABIを検証。'
        'u8/u16切詰め65792件、unsigned分岐8診断、16byte PUSHと2未読境界を固定。'
        'RAM再読の同値/stack非aliasは仮定せず、帰還・callee全副作用・owner除外は未受入。',
        '次は未読継続0x081138C9の1根だけ採取する。保存prefixは再実行せず16byte live-frameを継承。'
        '次いで保存継続ABI、0x081138F1末尾採取/ABIへ。0x0806DD1D/0x081138F9・旧18ownerは保持しRing通常取得は未受入。')

if __name__=='__main__':s.run(sys.modules[__name__])
