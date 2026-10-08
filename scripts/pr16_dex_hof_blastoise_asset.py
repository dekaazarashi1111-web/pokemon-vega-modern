#!/usr/bin/env python3
"""Blastoise第一画像の有限consumer。圧縮終端後の見かけ参照を分類しない。"""
from __future__ import annotations
import copy
import json
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as p
import pr16_dex_hof_menu_text as text
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_diploma_asset as codec
import pr16_dex_hof_credits_frontier as strict

ROOT = Path(__file__).resolve().parents[1]
need, identity, chunk, exact = d.need, d.identity, d.chunk, strict.exact
CANDIDATE = dict(codec.CANDIDATE)
HIT = 0x083D6B61
KIND = 'rooted_blastoise_lz10_minimum_asset'
ASSET = dict(address=0x083D655C, size=1794, sha256='795833f5dc50f7eeb6bc69b851d2ea3cdebe18ee6c8ec35e3b708ca1113dea01')
DECODED = dict(size=3200, sha256='53555d2564544f36b20a1100c372fd16e6a4eab1e62f58a2a87b02dae97ab068')
ENTRY, STOP = 0x080F5208, 0x080F52D2
WINDOWS, BUFFER, TEMPLATE = 0x02020430, 0x02010000, 0x083D27C8
INIT, FILL, MON, BIOS = 0x08003AF0, 0x08004428, 0x0810CD00, 0x081C7A90
LITERALS = {0x080F52E0:TEMPLATE,0x080F52E4:ASSET['address'],0x08004424:WINDOWS}
# 公開C定義とwindow.hの6u8+u16 ABIから独立生成する。ROM断片を複写しない。
WINDOW_ROWS = ((0,11,6,8,8,10,8),(0,10,5,10,10,10,72),
               (0,10,4,10,12,10,172),(255,0,0,0,0,0,0))
CONTRACT = dict(
 entry_ja='独立JP symbolのLoadCreditsMonPicへCREDITSMON_BLASTOISE=2で入る有限関数prefix。自然story/task到達は証明しない。',
 window_ja='実literalが公開定義一致の4recordをInitWindowsへ渡す。正常同期ABI帰還とwindow1の10x10tile/3200byte容量のdisjoint writable buffer生成を条件とする。InitWindows/Alloc実装は未証明。',
 preservation_ja='FillWindowPixelBuffer(0,0)とLoadMonPicInWindow(9,8,0,1,10,0)の正常同期ABI帰還がwindow1のbuffer epochを保存する条件。全calleeの効果やheap/IRQは未証明。',
 reader_ja='実LDR/BLでwindow1,size0,offset0を選び、実gWindows stride12/offset8からbufferを読んでSWI11へ渡す。LZ10仕様モデルの全入力を消費し宣言3200byteを生成。BIOS本体CPU実行ではない。',
 endpoint_ja='第一CopyToWindowPixelBuffer帰還直後080F52D2で止める。第二画像、VRAM転送、残関数、画面は未検証。',
 minimum_ja='独立公開PNGの完全compressed/decoded一致とhit4byte全体のconsumed payload包含が揃う場合だけ型候補。header/padding/未消費tailは分類しない。')
CLAIMS = dict(conditional_finite_type_only=True, actual_runtime_execution_observed=False,
 full_story_reachability_claimed=False, opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False, indirect_reference_completeness_claimed=False,
 actual_bios_cpu_executed=False, actual_screen_rendered=False, padding_classified=False,
 donor_eligible=False, donor_leased=False, formal_rom_changed=False, formal_save_changed=False)
SPECS = [(135221768, 'push', (16, True)),
 (135221770, 'spadd', (-8,)),
 (135221772, 'shift', ('lsl', 0, 0, 24)),
 (135221774, 'shift', ('lsr', 4, 0, 24)),
 (135221776, 'imm', ('cmp', 4, 1)),
 (135221778, 'branch', (0, 135221860)),
 (135221780, 'imm', ('cmp', 4, 1)),
 (135221782, 'branch', (12, 135221790)),
 (135221784, 'imm', ('cmp', 4, 0)),
 (135221786, 'branch', (0, 135221800)),
 (135221788, 'jump', (135222054,)),
 (135221790, 'imm', ('cmp', 4, 2)),
 (135221792, 'branch', (0, 135221924)),
 (135221794, 'imm', ('cmp', 4, 3)),
 (135221796, 'branch', (0, 135221996)),
 (135221798, 'jump', (135222054,)),
 (135221924, 'literal', (0, 135221984)),
 (135221926, 'call', (134232816,)),
 (135221930, 'imm', ('mov', 0, 0)),
 (135221932, 'imm', ('mov', 1, 0)),
 (135221934, 'call', (134235176,)),
 (135221938, 'imm', ('mov', 0, 10)),
 (135221940, 'spmem', (False, 0, 0)),
 (135221942, 'imm', ('mov', 0, 0)),
 (135221944, 'spmem', (False, 0, 4)),
 (135221946, 'imm', ('mov', 0, 9)),
 (135221948, 'imm', ('mov', 1, 8)),
 (135221950, 'imm', ('mov', 2, 0)),
 (135221952, 'imm', ('mov', 3, 1)),
 (135221954, 'call', (135318784,)),
 (135221958, 'literal', (1, 135221988)),
 (135221960, 'imm', ('mov', 0, 1)),
 (135221962, 'imm', ('mov', 2, 0)),
 (135221964, 'imm', ('mov', 3, 0)),
 (135221966, 'call', (134235088,)),
 (134235088, 'push', (112, True)),
 (134235090, 'addi', (6, 1, 0)),
 (134235092, 'shift', ('lsl', 0, 0, 24)),
 (134235094, 'shift', ('lsr', 4, 0, 24)),
 (134235096, 'shift', ('lsl', 5, 2, 16)),
 (134235098, 'shift', ('lsl', 3, 3, 16)),
 (134235100, 'shift', ('lsr', 2, 3, 16)),
 (134235102, 'imm', ('cmp', 5, 0)),
 (134235104, 'branch', (0, 134235140)),
 (134235140, 'literal', (1, 134235172)),
 (134235142, 'shift', ('lsl', 0, 4, 1)),
 (134235144, 'add', (0, 0, 4)),
 (134235146, 'shift', ('lsl', 0, 0, 2)),
 (134235148, 'imm', ('add', 1, 8)),
 (134235150, 'add', (0, 0, 1)),
 (134235152, 'shift', ('lsl', 2, 2, 5)),
 (134235154, 'mem', (True, 'word', 1, 0, 0)),
 (134235156, 'add', (1, 1, 2)),
 (134235158, 'addi', (0, 6, 0)),
 (134235160, 'call', (136084112,)),
 (134235164, 'pop', (112, False)),
 (134235166, 'pop', (1, False)),
 (134235168, 'bx', (0,))]

INS = {a:p.Ins(a,k,args) for a,k,args in SPECS}
encoded = text.encoded

def template_bytes():
    return b''.join(bytes(row[:6])+row[6].to_bytes(2,'little') for row in WINDOW_ROWS)

def bind_semantics(raw):
    for ins in INS.values():
        need(chunk(raw,ins.address,ins.size)==encoded(ins),'実Thumb意味束縛 '+hex(ins.address))
    for address,value in LITERALS.items():
        need(d.u32(raw,address)==value,'実literal束縛 '+hex(address))
    need(chunk(raw,TEMPLATE,32)==template_bytes(),'公開WindowTemplate全4record')
    need(chunk(raw,BIOS,4)==bytes((17,223,112,71)),'SWI11/BX LR stub')

def _compose(raw,live=None,writes=None,invalidated=None):
    trace=[];boundaries=[];events=[]
    m=text.Machine(raw,ENTRY,registers={0:2},memory={},instructions=INS,trace=trace)
    asset=decoded=None;reads=[]
    while m.pc!=STOP:
        need(m.steps<200,'有限命令予算')
        if m.pc in INS:
            m.step();continue
        site=(m.reg[14]&~1)-4
        if m.pc==BIOS:
            need(site==0x08004418 and m.reg[:2]==[ASSET['address'],BUFFER],'実asset/window1の同引数')
            asset,decoded,reads=codec.decode_stream(lambda a,n:chunk(raw,a,n),m.reg[0],maximum=3200,encoded_limit=4000)
            need(len(decoded)==3200,'window1容量と同header3200')
            for j,b in enumerate(decoded):m.write(BUFFER+j,1,b)
            events.append(dict(kind='bios_lz10',site=site,source=m.reg[0],destination=m.reg[1],
                encoded=identity(asset),decoded=identity(decoded),
                read_trace_identity=identity(json.dumps(reads,separators=(',',':')).encode())))
            codec.opaque_return(m,rt.U);continue
        need((site,m.pc) in ((0x080F52A6,INIT),(0x080F52AE,FILL),(0x080F52C2,MON)),
             '未登録callee/枝を拒否')
        output=[]
        if m.pc==INIT:
            need(m.reg[0]==TEMPLATE,'実登録WindowTemplate引数')
            # 実calleeの実行を装わない条件付きpostcondition。window1だけ。
            output=[(WINDOWS+12,4,int.from_bytes(template_bytes()[8:12],'little')),
                    (WINDOWS+16,4,int.from_bytes(template_bytes()[12:16],'little')),(WINDOWS+20,4,BUFFER)]
            events.append(dict(kind='conditional_init_windows',site=site,template=TEMPLATE,
                window=1,width_tiles=10,height_tiles=10,capacity_bytes=3200,buffer=BUFFER))
        elif m.pc==FILL:
            need(m.reg[:2]==[0,0],'別window0の初期化引数')
            events.append(dict(kind='conditional_fill_window0',site=site,window=0,fill=0))
        else:
            need(m.reg[:4]==[9,8,0,1] and m.read(m.reg[13],4)==10 and m.read(m.reg[13]+4,4)==0,
                 '別window0の種族画像引数')
            events.append(dict(kind='conditional_mon_window0',site=site,species=9,personality=8,
                               front=True,palette=10,window=0))
        index=len(boundaries);boundaries.append((site,m.pc));trace.append(('boundary',index,0))
        if live is not None:
            need(site not in (invalidated or ()), 'window1/同buffer epochを保存')
            required=live[index]
            for a,n,v in (writes or {}).get(site,()):
                need(not any(a<b+s and b<a+n for b,s in required),'future-live RAM改変拒否')
                rt.setmem(m.mem,a,n,v)
            keep={a+j for a,n in required for j in range(n)}
            m.mem={a:v for a,v in m.mem.items() if a in keep}
        for a,n,v in output:m.write(a,n,v)
        codec.opaque_return(m,rt.U)
    need(asset is not None and decoded is not None and m.reg[13]==0x03006FF0,
         '第一reader帰還直後/root prologue frameだけを保持')
    need(bytes(m.mem[BUFFER+j] for j in range(3200))==decoded,'全3200decoder出力')
    return dict(events=events,calls=m.calls,steps=m.steps,boundaries=boundaries,trace=trace,
                encoded=identity(asset),decoded=identity(decoded),read_bytes=sum(n for _,n in reads))

def compose(raw,*,writes=None,invalidated=None,contract=None):
    need(contract is None or exact(contract,CONTRACT),'閉じた条件契約')
    known={0x080F52A6,0x080F52AE,0x080F52C2}
    need(writes is None or type(writes) is dict and all(type(s) is int and s in known for s in writes),'書込boundary閉schema')
    for rows in (writes or {}).values():
        need(type(rows) in (list,tuple),'write列')
        for row in rows:
            need(type(row) in (list,tuple) and len(row)==3 and all(type(x) is int for x in row),'write整数3項')
            a,n,v=row;need(0<n<=3200 and 0<=a<a+n<=1<<32 and 0<=v<1<<(8*n),'write範囲')
    need(invalidated is None or type(invalidated) in (list,tuple) and all(type(s) is int and s in known for s in invalidated),'resource boundary')
    bind_semantics(raw)
    first=_compose(raw);live=text.future_live(first['trace'],len(first['boundaries']))
    second=_compose(raw,live,writes,invalidated)
    need(all(first[k]==second[k] for k in ('events','calls','steps','encoded','decoded','read_bytes')),
         'caller-saved/flags/nonlive消去後に同readerと全入力')
    windows=[dict(address=i.address,**identity(chunk(raw,i.address,i.size))) for i in INS.values()]
    windows += [dict(address=a,**identity(chunk(raw,a,4))) for a in LITERALS]
    windows += [dict(address=TEMPLATE,**identity(chunk(raw,TEMPLATE,32))),dict(address=BIOS,**identity(chunk(raw,BIOS,4)))]
    return dict(status='PASS_CONDITIONAL_BLASTOISE_FIRST_ASSET_READER',instruction_count=len(INS),
        executed_steps=first['steps'],stop_pc=STOP,complete_function_executed=False,
        calls=[list(x) for x in first['calls']],events=first['events'],
        conditional_boundaries=[dict(site=s,target=t,required_ranges=[dict(address=a,size=n) for a,n in fields],
            normal_abi_return_required=True,effects_discharged=False) for (s,t),fields in zip(first['boundaries'],live)],
        encoded=first['encoded'],decoded=first['decoded'],consumed_input_bytes=first['read_bytes'],
        encoded_end_exclusive=ASSET['address']+first['encoded']['size'],protected_windows=windows,
        asset_pointer_host_seeded=False,window_buffer_conditionally_produced=True,
        nonlive_ram_erased_at_each_boundary=True,**copy.deepcopy(CLAIMS))

def assess(consumer):
    """公開画像と現readerは別identity。完全包含を独立に判定し、tailを型にしない。"""
    encoded_match=exact(consumer['encoded'],{k:ASSET[k] for k in ('size','sha256')})
    decoded_match=exact(consumer['decoded'],DECODED)
    end=consumer['encoded_end_exclusive']
    need(type(end) is int and end==ASSET['address']+consumer['encoded']['size'],'実consumed終端整合')
    covered=d.contains(ASSET['address']+4,end,HIT,4)
    return dict(independent_encoded_match=encoded_match,independent_decoded_match=decoded_match,
                hit_fully_consumed=covered,minimum_type_eligible=encoded_match and decoded_match and covered,
                unread_bytes_before_hit=max(0,HIT-end),classified=0,donor_safe_bytes=0)

def evidence_template():
    return dict(root_verified=True,root_scope='conditional_independently_mapped_LoadCreditsMonPic_blastoise_prefix',
        classified_window=dict(address=HIT,size=4),asset=copy.deepcopy(ASSET),decoded=copy.deepcopy(DECODED),
        template=TEMPLATE,window=1,asset_literal=0x080F52E4,asset_pointer_load=0x080F52C6,
        copy_call=0x080F52CE,bios_call=0x08004418,bios_stub=BIOS,
        encoded_end_exclusive=ASSET['address']+ASSET['size'],classified_payload_only=True,
        independent_png_decoded_match=True,complete_encoded_stream_consumed=True,
        input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
    need(exact(evidence,evidence_template()),'独立minimum assetの閉witness')
    need(d.contains(ASSET['address']+4,ASSET['address']+ASSET['size'],HIT,4),'header/padding外の全4byte')
    return HIT,4

# 今回は閉じた診断scope。実測成功だけでpositive受入経路を開けない。
def validate_scope_proof(proof):
    raise ValueError('現scopeは診断のみ。公開PNG完全一致と現在consumerの正式receipt前は1件型を拒否')

def measure(raw,parent):
    import pr16_dex_hof_blastoise_chain as chain
    need(identity(raw)==CANDIDATE==parent['candidate'],'現0641全ROM identity')
    chain.validate_parent_state(parent)
    hit=next(h for h in parent['hits'] if h['address']==HIT)
    need(hit['accepted'] is False and hit['size']==4 and hit['owner_candidates']==[],'唯一4byte未知')
    d.signed(raw,hit)
    consumer=compose(raw)
    return dict(consumer=consumer,assessment=assess(consumer),hit_identity={k:hit[k] for k in ('address','size','sha256')},
                independent_asset=copy.deepcopy(ASSET),independent_decoded=copy.deepcopy(DECODED),
                newly_classified=0,formal_rom_changed=False,formal_save_changed=False,donor_safe_bytes=0)


PROOF_PATH = 'content/modernization/pr16_dex_hof_blastoise_development_proof.json'
PROOF_ID = dict(size=19698,sha256='8368a475c56439eea472cbfdd07f240372979681ac7289dc7123dc997153ef3b')

def development_proofs():
    raw=(ROOT/PROOF_PATH).read_bytes()
    need(identity(raw)==PROOF_ID,'開発2原本の固定全byte identity')
    obj=strict.load(raw)
    need(obj['current_rom_measured'] is False,'別ROM診断を現0641測定にしない')
    return obj

def validate_diagnostic_proof(proof):
    expected=development_proofs()
    need(exact(proof,expected['independent_png_fixture']) or exact(proof,expected['diagnostic_local_fixture']),
         '有限consumer/全window/全条件/独立assetは2固定開発契約のどちらかに厳密一致')
    need(exact(proof['assessment'],assess(proof['consumer'])) and proof['newly_classified']==0,
         '観測包含を再計算し、source一致でも今scopeの型昇格0')
    return True
