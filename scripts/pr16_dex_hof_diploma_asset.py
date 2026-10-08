#!/usr/bin/env python3
"""独立Diploma assetの実literalからSWI11とmode0 BG consumerへ結ぶ有限型。"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as p
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_credits_frontier as parent_contract

ROOT = Path(__file__).resolve().parents[1]
need, identity, chunk = d.need, d.identity, d.chunk
exact = parent_contract.exact
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
HIT = 0x083DCAED
KIND = 'rooted_diploma_lz10_minimum_asset'
ASSET = dict(address=0x083DBF7C, size=3366, sha256='cef35413656191513ea96f09a2f088f33fac4b579317567e7b4cf8875388490f')
DECODED = dict(size=8192, sha256='1e3d4069b5ab9ebd09f28341597009aba99696b57290b89d3a6620b6914c7dfd')
CELL, OBJECT, BUFFER = 0x0203AAC0, 0x02038000, 0x02010000
COUNT, TABLE, ENTRY, END = 0x0203AAD4, 0x0203AAD8, 0x080F6000, 0xFFFFFFF0
ALLOC, BIOS, BG = 0x08002B9C, 0x081C7A90, 0x080017D0
LITERALS = {0x080F6018:CELL, 0x080F6040:ASSET['address'], 0x080F6078:CELL,
            0x080F787C:COUNT, 0x080F7880:TABLE, 0x080F7930:COUNT, 0x080F7934:TABLE}
CONTRACT = dict(
 entry_ja='独立JP symbolで指定されたDiplomaLoadGfxへ、有効な同sDiploma objectとgfxState0で入る。自然story/task到達は証明しない。',
 producer_ja='実state0が32 temp pointerを消去しcount0を生成、実storeでgfxState1へ。同objectを保ち2回目に実literalからasset pointerを得る。state1やcountを途中host書込みしない。',
 allocation_ja='実header3byteから8192を生成しAllocへ渡す。同期ABI帰還とdisjoint8192byte成功bufferを条件とする。allocator実装/OOM/普遍heapは未証明。',
 bios_ja='実BLが固定SWI11/BX LR stubへ到達。LZ10仕様モデルで最終outputまで全encoded3366byteを消費。BIOS本体のCPU実行ではない。',
 background_ja='mode0の実分岐がLoadBgTiles(1,同buffer,8192,0)を呼ぶ。正常同期ABI帰還と同buffer epochを条件とし、DMA完了や実画面描画は主張しない。',
 boundary_ja='opaque Alloc/LoadBgTilesのcaller-saved/flagsはUnknownへ破棄し、実future-live RAMとstack/callee-savedだけ保持して再実行する。',
 minimum_ja='圧縮assetのheader/paddingを型へ含めず、完全にconsumed payload内の対象4byteだけを分類。旧egg15118保護/donor0を維持。')
CLAIMS = dict(conditional_finite_type_only=True, actual_runtime_execution_observed=False,
 full_story_reachability_claimed=False, opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False, indirect_reference_completeness_claimed=False,
 actual_bios_cpu_executed=False, actual_screen_rendered=False, padding_classified=False,
 donor_eligible=False, donor_leased=False, formal_rom_changed=False, formal_save_changed=False)
SPECS = [(135225344, 'push', (0, True)),
 (135225346, 'spadd', (-4,)),
 (135225348, 'literal', (0, 135225368)),
 (135225350, 'mem', (True, 'word', 0, 0, 0)),
 (135225352, 'mem', (True, 'byte', 0, 0, 1)),
 (135225354, 'imm', ('cmp', 0, 1)),
 (135225356, 'branch', (0, 135225388)),
 (135225358, 'imm', ('cmp', 0, 1)),
 (135225360, 'branch', (12, 135225372)),
 (135225362, 'imm', ('cmp', 0, 0)),
 (135225364, 'branch', (0, 135225382)),
 (135225366, 'jump', (135225436,)),
 (135225372, 'imm', ('cmp', 0, 2)),
 (135225374, 'branch', (0, 135225412)),
 (135225376, 'imm', ('cmp', 0, 3)),
 (135225378, 'branch', (0, 135225426)),
 (135225380, 'jump', (135225436,)),
 (135225382, 'call', (135231584,)),
 (135225386, 'jump', (135225444,)),
 (135225388, 'literal', (1, 135225408)),
 (135225390, 'imm', ('mov', 0, 0)),
 (135225392, 'spmem', (False, 0, 0)),
 (135225394, 'imm', ('mov', 0, 1)),
 (135225396, 'imm', ('mov', 2, 0)),
 (135225398, 'imm', ('mov', 3, 0)),
 (135225400, 'call', (135231696,)),
 (135225404, 'jump', (135225444,)),
 (135225444, 'literal', (0, 135225464)),
 (135225446, 'mem', (True, 'word', 1, 0, 0)),
 (135225448, 'mem', (True, 'byte', 0, 1, 1)),
 (135225450, 'imm', ('add', 0, 1)),
 (135225452, 'mem', (False, 'byte', 0, 1, 1)),
 (135225454, 'imm', ('mov', 0, 0)),
 (135225456, 'spadd', (4,)),
 (135225458, 'pop', (2, False)),
 (135225460, 'bx', (1,)),
 (135231584, 'push', (0, True)),
 (135231586, 'literal', (3, 135231612)),
 (135231588, 'literal', (1, 135231616)),
 (135231590, 'imm', ('mov', 2, 0)),
 (135231592, 'addi', (0, 1, 0)),
 (135231594, 'imm', ('add', 0, 124)),
 (135231596, 'mem', (False, 'word', 2, 0, 0)),
 (135231598, 'imm', ('sub', 0, 4)),
 (135231600, 'compare', (0, 1)),
 (135231602, 'branch', (10, 135231596)),
 (135231604, 'imm', ('mov', 0, 0)),
 (135231606, 'mem', (False, 'half', 0, 3, 0)),
 (135231608, 'pop', (1, False)),
 (135231610, 'bx', (0,)),
 (135231696, 'push', (240, True)),
 (135231698, 'movhi', (7, 9)),
 (135231700, 'movhi', (6, 8)),
 (135231702, 'push', (192, False)),
 (135231704, 'spadd', (-8,)),
 (135231706, 'addi', (4, 1, 0)),
 (135231708, 'addi', (5, 2, 0)),
 (135231710, 'spmem', (True, 1, 36)),
 (135231712, 'shift', ('lsl', 0, 0, 24)),
 (135231714, 'shift', ('lsr', 0, 0, 24)),
 (135231716, 'movhi', (8, 0)),
 (135231718, 'shift', ('lsl', 3, 3, 16)),
 (135231720, 'shift', ('lsr', 3, 3, 16)),
 (135231722, 'movhi', (9, 3)),
 (135231724, 'shift', ('lsl', 1, 1, 24)),
 (135231726, 'shift', ('lsr', 7, 1, 24)),
 (135231728, 'literal', (6, 135231792)),
 (135231730, 'mem', (True, 'half', 0, 6, 0)),
 (135231732, 'imm', ('cmp', 0, 31)),
 (135231734, 'branch', (8, 135231800)),
 (135231736, 'addi', (0, 4, 0)),
 (135231738, 'spaddr', (1, 4)),
 (135231740, 'call', (135232248,)),
 (135231744, 'addi', (4, 0, 0)),
 (135231746, 'imm', ('cmp', 5, 0)),
 (135231748, 'branch', (1, 135231752)),
 (135231750, 'spmem', (True, 5, 4)),
 (135231752, 'imm', ('cmp', 4, 0)),
 (135231754, 'branch', (0, 135231788)),
 (135231756, 'shift', ('lsl', 2, 5, 16)),
 (135231758, 'shift', ('lsr', 2, 2, 16)),
 (135231760, 'spmem', (False, 7, 0)),
 (135231762, 'movhi', (0, 8)),
 (135231764, 'addi', (1, 4, 0)),
 (135231766, 'movhi', (3, 9)),
 (135231768, 'call', (135232296,)),
 (135231772, 'literal', (2, 135231796)),
 (135231774, 'mem', (True, 'half', 0, 6, 0)),
 (135231776, 'addi', (1, 0, 1)),
 (135231778, 'mem', (False, 'half', 1, 6, 0)),
 (135231780, 'shift', ('lsl', 0, 0, 16)),
 (135231782, 'shift', ('lsr', 0, 0, 14)),
 (135231784, 'add', (0, 0, 2)),
 (135231786, 'mem', (False, 'word', 4, 0, 0)),
 (135231788, 'addi', (0, 4, 0)),
 (135231790, 'jump', (135231802,)),
 (135231800, 'imm', ('mov', 0, 0)),
 (135231802, 'spadd', (8,)),
 (135231804, 'pop', (24, False)),
 (135231806, 'movhi', (8, 3)),
 (135231808, 'movhi', (9, 4)),
 (135231810, 'pop', (240, False)),
 (135231812, 'pop', (2, False)),
 (135231814, 'bx', (1,)),
 (135232248, 'push', (48, True)),
 (135232250, 'addi', (5, 0, 0)),
 (135232252, 'mem', (True, 'byte', 0, 5, 1)),
 (135232254, 'mem', (False, 'byte', 0, 1, 0)),
 (135232256, 'mem', (True, 'byte', 0, 5, 2)),
 (135232258, 'mem', (False, 'byte', 0, 1, 1)),
 (135232260, 'mem', (True, 'byte', 0, 5, 3)),
 (135232262, 'mem', (False, 'byte', 0, 1, 2)),
 (135232264, 'imm', ('mov', 0, 0)),
 (135232266, 'mem', (False, 'byte', 0, 1, 3)),
 (135232268, 'mem', (True, 'word', 0, 1, 0)),
 (135232270, 'call', (134228892,)),
 (135232274, 'addi', (4, 0, 0)),
 (135232276, 'imm', ('cmp', 4, 0)),
 (135232278, 'branch', (0, 135232288)),
 (135232280, 'addi', (0, 5, 0)),
 (135232282, 'addi', (1, 4, 0)),
 (135232284, 'call', (136084112,)),
 (135232288, 'addi', (0, 4, 0)),
 (135232290, 'pop', (48, False)),
 (135232292, 'pop', (2, False)),
 (135232294, 'bx', (1,)),
 (135232296, 'push', (16, True)),
 (135232298, 'addi', (4, 1, 0)),
 (135232300, 'spmem', (True, 1, 8)),
 (135232302, 'shift', ('lsl', 0, 0, 24)),
 (135232304, 'shift', ('lsr', 0, 0, 24)),
 (135232306, 'shift', ('lsl', 2, 2, 16)),
 (135232308, 'shift', ('lsr', 2, 2, 16)),
 (135232310, 'shift', ('lsl', 3, 3, 16)),
 (135232312, 'shift', ('lsr', 3, 3, 16)),
 (135232314, 'shift', ('lsl', 1, 1, 24)),
 (135232316, 'shift', ('lsr', 1, 1, 24)),
 (135232318, 'imm', ('cmp', 1, 0)),
 (135232320, 'branch', (0, 135232326)),
 (135232322, 'imm', ('cmp', 1, 1)),
 (135232324, 'branch', (0, 135232334)),
 (135232326, 'addi', (1, 4, 0)),
 (135232328, 'call', (134223824,)),
 (135232332, 'jump', (135232340,)),
 (135232340, 'shift', ('lsl', 0, 0, 16)),
 (135232342, 'shift', ('lsr', 0, 0, 16)),
 (135232344, 'pop', (16, False)),
 (135232346, 'pop', (2, False)),
 (135232348, 'bx', (1,))]

INS = {a:p.Ins(a,k,args) for a,k,args in SPECS}

def encoded(i):
    return text.encoded(i)


def bind_semantics(raw):
    for i in INS.values():
        need(chunk(raw,i.address,i.size) == encoded(i), '実Thumb意味束縛 '+hex(i.address))
    for a,v in LITERALS.items():
        need(d.u32(raw,a) == v, '実literal束縛 '+hex(a))
    need(chunk(raw,BIOS,4) == bytes((17,223,112,71)), 'SWI11とBX LRの固定stub')


def decode_stream(read, address, *, maximum=8192, encoded_limit=16384):
    """LZ10の全読取を記録。最後のtokenで出力境界を越える入力も拒否する。"""
    need(type(address) is int and address%4 == 0 and 0x08000000<=address<0x0A000000,
         '独立整列root')
    need(type(maximum) is int and 0<maximum<=8192 and type(encoded_limit) is int and 4<encoded_limit<=16384,
         '固定最大出力/入力予算')
    reads=[];encoded_data=bytearray();output=bytearray()
    def take(n):
        need(len(encoded_data)+n <= encoded_limit, '圧縮入力上限')
        a=address+len(encoded_data);b=read(a,n)
        need(type(b) is bytes and len(b)==n, '圧縮入力の完全read')
        reads.append((a,n));encoded_data.extend(b);return b
    header=take(4);need(header[0]==16, '独立LZ10 codec')
    wanted=int.from_bytes(header[1:4],'little');need(0<wanted<=maximum, '解凍出力上限')
    while len(output)<wanted:
        flags=take(1)[0]
        for bit in range(7,-1,-1):
            if len(output)==wanted:break
            if flags&(1<<bit):
                a,b=take(2);length=(a>>4)+3;distance=((a&15)<<8|b)+1
                need(distance<=len(output) and len(output)+length<=wanted, 'LZ後方参照/最終長')
                for _ in range(length):output.append(output[-distance])
            else:output.extend(take(1))
    return bytes(encoded_data),bytes(output),reads


def opaque_return(m, value):
    target=m.reg[14]&~1
    for r in (0,1,2,3,12,14):m.reg[r]=rt.U
    m.reg[0]=value;m.pc=target;m.flags=(rt.U,)*4;m.flag_pc=None


def _compose(raw, live=None, writes=None, invalidated=None):
    memory={};rt.setmem(memory,CELL,4,OBJECT);rt.setmem(memory,OBJECT+1,1,0)
    trace=[];boundaries=[];events=[];allcalls=[];steps=[];bios_reads=[];decoded=None;asset=None
    for phase in (0,1):
        m=text.Machine(raw,ENTRY,memory=memory,instructions=INS,trace=trace)
        while m.pc!=END:
            need(m.steps<2000,'有限命令予算')
            if m.pc in INS:
                m.step();continue
            site=(m.reg[14]&~1)-4
            if m.pc==BIOS:
                need(site==0x080F7B1C and m.reg[:2]==[ASSET['address'],BUFFER], '実literalから同BIOS引数')
                asset,decoded,bios_reads=decode_stream(lambda a,n:chunk(raw,a,n),m.reg[0])
                need(len(decoded)==8192,'実headerの8192byte出力')
                for j,b in enumerate(decoded):m.write(BUFFER+j,1,b)
                events.append(dict(kind='bios_lz10',site=site,source=m.reg[0],destination=m.reg[1],
                    encoded=identity(asset),decoded=identity(decoded),read_trace_identity=identity(json.dumps(bios_reads,separators=(',',':')).encode())))
                opaque_return(m,rt.U);continue
            need((site,m.pc) in ((0x080F7B0E,ALLOC),(0x080F7B48,BG)), '未登録callee/枝を拒否')
            index=len(boundaries);boundaries.append((site,m.pc));trace.append(('boundary',index,0))
            if m.pc==ALLOC:
                need(m.reg[0]==8192,'header由来の実8192 Alloc引数');value=BUFFER
                events.append(dict(kind='conditional_allocation',site=site,size=8192,returned_buffer=BUFFER))
            else:
                need(m.reg[:4]==[1,BUFFER,8192,0], 'mode0 BG1/同buffer/8192/offset0')
                need(bytes(m.mem[BUFFER+j] for j in range(8192))==decoded, '同decoder出力をBG consumerへ渡す')
                # Opaque BG readerに必要なbufferはexplicit precondition。CPU読みを装わない。
                trace.append(('read',BUFFER,8192));value=rt.U
                events.append(dict(kind='conditional_bg_copy',site=site,bg=1,buffer=BUFFER,size=8192,offset=0))
            if live is not None:
                need(index<len(live), '全boundary数')
                need(site not in (invalidated or ()), '同allocation/objectのresource epoch維持')
                fields=live[index]
                for a,n,v in (writes or {}).get(site,()):
                    need(not any(a<b+s and b<a+n for b,s in fields),'future-live RAM改変を拒否')
                    rt.setmem(m.mem,a,n,v)
                kept={a+j for a,n in fields for j in range(n)}
                m.mem={a:v for a,v in m.mem.items() if a in kept}
            opaque_return(m,value)
        need(m.reg[13]==0x03007000 and m.reg[0]==0, '各DiplomaLoadGfxはstack復元/return0')
        need(m.read(OBJECT+1,1)==phase+1,'実gfxStateの増分')
        if phase==0:
            need(m.read(COUNT,2)==0 and all(m.read(TABLE+j*4,4)==0 for j in range(32)), '実state0で全32buffer/countを初期化')
        else:
            need(m.read(COUNT,2)==1 and m.read(TABLE,4)==BUFFER,'同decoded bufferを実tableへ登録')
        memory=m.mem;steps.append(m.steps);allcalls.extend(m.calls)
    return dict(events=events,steps=steps,calls=allcalls,trace=trace,boundaries=boundaries,
                encoded=identity(asset),decoded=identity(decoded),bios_reads=bios_reads)


def compose(raw, *, writes=None, invalidated=None, contract=None):
    need(contract is None or exact(contract,CONTRACT),'閉じた条件契約')
    known={0x080F7B0E,0x080F7B48}
    need(writes is None or type(writes) is dict and all(type(s) is int and s in known for s in writes),'書込boundary閉schema')
    for rows in (writes or {}).values():
        need(type(rows) in (list,tuple),'write列')
        for row in rows:
            need(type(row) in (list,tuple) and len(row)==3 and all(type(x) is int for x in row),'write整数3項')
            a,n,v=row;need(0<n<=8192 and 0<=a<a+n<=1<<32 and 0<=v<1<<(8*n),'write範囲')
    need(invalidated is None or type(invalidated) in (list,tuple) and all(type(s) is int and s in known for s in invalidated),'resource境界')
    bind_semantics(raw)
    first=_compose(raw);live=text.future_live(first['trace'],len(first['boundaries']))
    second=_compose(raw,live,writes,invalidated)
    need(first['events']==second['events'] and first['steps']==second['steps'] and first['calls']==second['calls'],
         'nonlive消去後の実caller/decoder/consumer一致')
    windows=[dict(address=i.address,**identity(chunk(raw,i.address,i.size))) for i in INS.values()]
    windows += [dict(address=a,**identity(chunk(raw,a,4))) for a in LITERALS]
    windows += [dict(address=BIOS,**identity(chunk(raw,BIOS,4)))]
    return dict(status='PASS_CONDITIONAL_DIPLOMA_LZ10_CONSUMER',instruction_count=len(INS),
        phase_steps=first['steps'],calls=[list(x) for x in first['calls']],events=first['events'],
        conditional_boundaries=[dict(site=s,target=t,required_ranges=[dict(address=a,size=n) for a,n in fields],
            normal_abi_return_required=True,effects_discharged=False) for (s,t),fields in zip(first['boundaries'],live)],
        encoded=first['encoded'],decoded=first['decoded'],protected_windows=windows,
        text_pointer_host_seeded=False,asset_pointer_host_seeded=False,state1_host_seeded=False,
        nonlive_ram_erased_at_each_boundary=True,old_full_rom_scan_runs=0,native_processes=0,
        donor_safe_bytes=0,**copy.deepcopy(CLAIMS))


def evidence_template():
    return dict(root_verified=True,root_scope='conditional_independently_mapped_DiplomaLoadGfx_state0_then1',
        classified_window=dict(address=HIT,size=4),asset=copy.deepcopy(ASSET),decoded=copy.deepcopy(DECODED),
        asset_literal=0x080F6040,asset_pointer_load=0x080F602C,decompress_call=0x080F6038,
        allocation_call=0x080F7B0E,bios_call=0x080F7B1C,bios_stub=BIOS,bg_copy_call=0x080F7B48,
        encoded_end_exclusive=ASSET['address']+ASSET['size'],classified_payload_only=True,
        independent_png_decoded_match=True,complete_encoded_stream_consumed=True,
        input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))


def witness_geometry(evidence):
    need(exact(evidence,evidence_template()),'独立minimum assetの閉witness')
    need(d.contains(ASSET['address']+4,ASSET['address']+ASSET['size'],HIT,4),'header/padding外の完全4byte')
    return HIT,4


PROOF_PATH = 'content/modernization/pr16_dex_hof_diploma_development_proof.json'
PROOF_ID = {'size': 22184, 'sha256': '59f3b165c8e04c306d974eab0188033fecbd6cf2bc325b713a03bc18435aa65b'}

def validate_scope_proof(proof):
    raw=(ROOT/PROOF_PATH).read_bytes()
    need(identity(raw)==PROOF_ID, '独立source fixtureの全byte identity')
    expected=parent_contract.load(raw)
    need(exact(proof,expected),'独立source fixtureの完全scope proof')
    need(exact(proof['consumer']['encoded'],{k:ASSET[k] for k in ('size','sha256')}) and
         exact(proof['consumer']['decoded'],DECODED), '圧縮/解凍の完全identity')
    need(exact(proof['evidence'],evidence_template()) and proof['newly_classified']==1 and
         type(proof['newly_classified']) is int, '独立型geometryと1件')
    return True


def _regions(raw,parent):
    parent_contract.validate_parent(parent)
    hit=next(h for h in parent['hits'] if h['address']==HIT)
    need(hit['accepted'] is False and hit['size']==4 and hit['owner_candidates']==[], '唯一4byte未知')
    d.signed(raw,hit)
    consumer=compose(raw)
    evidence=evidence_template()
    proof=dict(status='PASS_ONE_CONDITIONAL_DIPLOMA_LZ10_TYPE',hit=HIT,newly_classified=1,
               consumer=consumer,evidence=evidence,donor_safe_bytes=0,native_processes=0,
               old_full_rom_scan_runs=0,**copy.deepcopy(CLAIMS))
    validate_scope_proof(proof)
    return [d.TypedRegion(HIT,HIT+4,KIND,evidence)],proof


def regions(raw,parent):
    need(identity(raw)==CANDIDATE==parent['candidate'],'現0641全ROM identity')
    return _regions(raw,parent)
