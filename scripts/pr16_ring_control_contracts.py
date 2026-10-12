#!/usr/bin/env python3
"""保存control24表・prompt初期化を明示RAMと独立した順序write期待値で検証。"""
from __future__ import annotations
import copy
import itertools
import sys
import pr16_ring_control_frontier as prior
import pr16_ring_text_state_contracts as text
import pr16_ring_followup_v2 as s

BASE='825499c1a6057b7a05635850ae29c063ccb92d8f'
SLUG='pr16-ring-control-contracts'
TASK='PR-P08-7-RING-CONTROL-CONTRACTS'
TITLE='control24分岐・色81要素展開・prompt初期化と未読出力境界を結合'
SELF='scripts/pr16_ring_control_contracts.py'
TEST='tests/test_pr16_ring_control_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-control-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_control_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=32
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存control24分岐・色81要素展開・prompt初期化とpayload不足の部分write契約を再利用。'
    '字形/音声/BIOS未読境界は成功stubにしない。同じ採取・旧627text契約・font/BP/nativeを単独再実行しない。')
b=text.b;strict=text.strict;need=s.need
LOOKUP=0x03000a40
MUTE=0x02031d0c
CONTROL_TARGETS=(0x080058f4,0x08005916,0x0800593a,0x08005954,0x08005a78,0x080059a0,
    0x0800586a,0x080059b6,0x080059c6,0x080059da,0x080059de,0x08005a26,
    0x08005a30,0x08005a3c,0x08005a4c,0x08005a0c,0x08005a78,0x08005a78,
    0x08005a78,0x08005a78,0x0800586a,0x0800586a,0x08005a5e,0x08005a6c)
PENDING=(0x08002f5d,0x08002f9d,0x08004a71,0x08071a45,0x081c1229,0x081c1815,0x081c18f9)
GROUPS=('colors','simple','prompt','audio','glyph','truncated','bios','renderer')


def validate_inputs(nodes,a):
    need(type(nodes)is list and len(nodes)==len({n['address']for n in nodes})==6534,'保存6534命令')
    for key in ('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
        need(a.get(key)is False,'受入境界 '+key)
    table=text.checked_table(a['control_table'],96)
    need(table[0]==prior.TABLE and tuple(int.from_bytes(table[1][i:i+4],'little')for i in range(0,96,4))==CONTROL_TARGETS,'control表target差分')
    need(a['control_table']['targets']==list(CONTROL_TARGETS),'control表metadata差分')
    need([f['selector']for f in a['selected_fonts']]==[2,4,5],'font集合')
    need(a['pending_direct_callees']==list(PENDING),'未読callee集合')
    return table


def fixture(a,*,colors=(0xab,0xcd),auto_counter=91,**kwargs):
    need(type(colors)in (tuple,list)and len(colors)==2 and all(type(v)is int and 0<=v<256 for v in colors),'色field u8')
    at,p,segs=text.fixture(a,auto_counter=auto_counter,**kwargs)
    p[12:14]=bytes(colors)
    pool=bytearray(segs[0][1]);offset=at-b.POOL;pool[offset:offset+32]=p
    segs[0]=(b.POOL,bytes(pool),True);segs.append(text.checked_table(a['control_table'],96))
    return at,p,segs


def lookup_writes(fg,bg,shadow):
    """実装のloopや実traceを読まず、3色から81個の4nibble組合せを定義する。"""
    need(all(type(v)is int and 0<=v<16 for v in (fg,bg,shadow)),'色nibble')
    colors=(bg,fg,shadow)
    writes=[(LOOKUP+162,2,bg),(LOOKUP+164,2,fg),(LOOKUP+166,2,shadow)]
    for index,indices in enumerate(itertools.product(range(3),repeat=4)):
        writes.append((LOOKUP+2*index,2,sum(colors[v]<<(4*i)for i,v in enumerate(indices))))
    return writes


def color_writes(at,p,sub,payload,*,pointer=b.TEMPLATE+2,expand=True):
    need(type(sub)is int and 1<=sub<=4 and type(payload)is bytes,'色control形式')
    need(type(expand)is bool,'展開flag')
    fields=list(p[12:14]);writes=[]
    count=3 if sub==4 else 1
    need(len(payload)<=count,'色payload過長')
    for i,value in enumerate(payload):
        kind=i+1 if sub==4 else sub
        if kind==1:fields[0]=(fields[0]&15)|((value&15)<<4);offset=12
        elif kind==2:fields[1]=(fields[1]&240)|(value&15);offset=13
        else:fields[1]=(fields[1]&15)|((value&15)<<4);offset=13
        writes.extend(((at+offset,1,fields[offset-12]),(at,4,pointer+i+1)))
    if expand:
        need(len(payload)==count,'色payload不足')
        writes+=lookup_writes(fields[0]>>4,fields[1]&15,fields[1]>>4)
    return writes


def prefix(at,p,font,flags=0,subtype=True,pointer=b.TEMPLATE):
    need(type(subtype)is bool,'subtype flag')
    writes=text.setup_writes(at,p,font)+[(at+30,1,1 if flags&4 else 0),(at,4,pointer+1)]
    if subtype:writes.append((at,4,pointer+2))
    return writes


def contracts(nodes,a,context,groups=GROUPS):
    validate_inputs(nodes,a);cases=strict.Cases(nodes);counts={}
    for group in groups:
        need(group in GROUPS,'契約group');before=len(cases.rows)
        for fontrow in a['selected_fonts']:
            font=fontrow['selector'];entry=fontrow['callback']
            def run(label,raw,tail=(),value=2,stop=None,fault=None,extra=(),flags=0,**kwargs):
                at,p,segs=fixture(a,font=font,text=raw,flags=flags,**kwargs)
                writes=prefix(at,p,font,flags,raw[0]==252)+list(tail(at,p)if callable(tail)else tail)
                return cases.run(f'{group}-{font}-{label}',entry,[*segs,*extra],(at,),writes,value,stop,fault)
            if group=='colors':
                for sub in range(1,5):
                    for val in (*range(16),16,127,128,255):
                        payload=bytes([val,(val+7)&255,(val+13)&255])if sub==4 else bytes([val])
                        run(f'{sub}-{val}',bytes([252,sub])+payload,lambda at,p:color_writes(at,p,sub,payload),
                            extra=[(LOOKUP,bytes(168),True)])
            elif group=='simple':
                for sub in (5,17,18,19,20):
                    for payload in (b'',b'\xff'):
                        run(f'skip-{sub}-{len(payload)}',bytes([252,sub])+payload,lambda at,p:[(at,4,b.TEMPLATE+3)])
                for sub in (7,21,22):run(f'noop-{sub}',bytes([252,sub]))
                for sub in (6,8,13,14):
                    for val in (0,1,15,16,127,255):
                        for flags in (0,4):
                            def tail(at,p):
                                if sub==6:return [(at+20,1,(p[20]&240)|(val&15)),(at,4,b.TEMPLATE+3)]
                                if sub==8:return [(at+30,1,val),(at,4,b.TEMPLATE+3),(at+28,1,6)]
                                offset=8 if sub==13 else 9
                                return [(at+offset,1,(val+p[offset-2])&255),(at,4,b.TEMPLATE+3)]
                            run(f'{sub}-{val}-{flags}',bytes([252,sub,val]),tail,flags=flags,internal=font|0xa0,initial=(250,255))
                for sub,state in ((9,1),(10,5)):
                    for flags in(0,4):
                        run(f'wait-{sub}-{flags}',bytes([252,sub]),lambda at,p:[(at+28,1,state)]+([(at+22,1,0)]if sub==9 and flags&4 else []),
                            value=3,flags=flags)
            elif group=='prompt':
                for code,state in((250,3),(251,2)):
                    for flags in(0,4):
                        for blink in(0,31,127,128,255):
                            run(f'{code}-{flags}-{blink}',bytes([code]),lambda at,p:[(at+28,1,state),
                                (at+22,1,0)if flags&4 else(at+21,1,128)],value=3,flags=flags,blink=blink,internal=font|0xa0)
            elif group=='audio':
                for sub in (11,16):
                    for mode in (0,2,3):
                        for mute in (0,1):
                            skip=mode in(2,3)if sub==11 else mute!=0 or mode==2
                            target=0x08071a44 if sub==11 else 0x081c10bc
                            stop=None if skip else ('保存node境界で停止',target)if sub==11 else ('未map read',target)
                            sid=0x123;fault=None if skip or sub==11 else {'address':0x08467f0c+8*sid+4,'size':2,'site':target}
                            run(f'{sub}-{mode}-{mute}',bytes([252,sub,0x23,1]),lambda at,p:[(at,4,b.TEMPLATE+3),(at,4,b.TEMPLATE+4)],
                                stop=stop,fault=fault,extra=[(text.LINK_MODE,bytes([mode]),False),(MUTE,bytes([mute]),False)])
                for sub,target in((23,0x081c18f8),(24,0x081c1228)):
                    m=run(str(sub),bytes([252,sub]),stop=('保存node境界で停止',target))
                    need(m.r[0]==0x03007350,'音声callee引数')
                # 明示合成tableのindex/address計算を未読音声player直前まで結合。実音声tableとは区別する。
                for index in(0,3):
                    sid=0x123;player=0x02004000;song=0x08008000
                    desc=b.word(song)+index.to_bytes(2,'little')+bytes(2)
                    m=run(f'synthetic-table-{index}',bytes([252,16,0x23,1]),lambda at,p:[(at,4,b.TEMPLATE+3),(at,4,b.TEMPLATE+4)],
                        stop=('保存node境界で停止',0x081c1814),extra=[(text.LINK_MODE,b'\0',False),(MUTE,b'\0',False),
                            (0x08467f0c+sid*8,desc,False),(0x08467edc+index*12,b.word(player),False)])
                    need(m.r[0:2]==[player,song],'合成音声table引数')
            elif group=='glyph':
                for value in (0,1,247):
                    target=0x08002f9c if value==0 else 0x08002f5c
                    m=run(f'ordinary-{value}',bytes([value]),stop=('保存node境界で停止',target))
                    if value:need(m.r[1]==0x03003de0,'字形出力pointer')
                for sub in(0,25,255):
                    m=run(f'outside-control-{sub}',bytes([252,sub]),stop=('保存node境界で停止',0x08002f9c if sub==0 else 0x08002f5c))
                    if sub:need(m.r[1]==0x03003de0,'範囲外controlの字形境界')
                for val in(0,1,247):
                    target=0x08002f9c if val==0 else 0x08002f5c
                    run(f'extended-{val}',bytes([252,12,0xa7,val]),lambda at,p:[(at,4,b.TEMPLATE+3)],stop=('保存node境界で停止',target))
                for length in(0,1):
                    pc=0x08005a2c
                    run(f'extended-short-{length}',bytes([252,12])+bytes(length),lambda at,p:[(at,4,b.TEMPLATE+3)],
                        stop=('未map read',pc),fault={'address':b.TEMPLATE+3,'size':1,'site':pc})
            elif group=='truncated':
                specs={1:(0x080058f6,),2:(0x08005918,),3:(0x0800593c,),4:(0x08005956,0x0800596a,0x08005980),
                    6:(0x080059a2,),8:(0x080059b8,),11:(0x080059e0,0x080059e6),13:(0x08005a32,),
                    14:(0x08005a3e,),16:(0x08005a0e,0x08005a14)}
                for sub,sites in specs.items():
                    for length,pc in enumerate(sites):
                        payload=bytes([7,8][:length])
                        def tail(at,p):
                            if sub==4:return color_writes(at,p,4,payload,expand=False)
                            if sub in(11,16):return [(at,4,b.TEMPLATE+3)]if length else []
                            return []
                        run(f'{sub}-{length}',bytes([252,sub])+payload,tail,stop=('未map read',pc),
                            fault={'address':b.TEMPLATE+2+length,'size':1,'site':pc})
            elif group=='bios':
                for slot,dims in((0,(1,1)),(31,(2,3))):
                    pool=bytearray(b.window_pool(None,pointer=b.BUFFER));pool[slot*12:slot*12+8]=b.template(dims=dims)
                    m=run(f'fill-{slot}',bytes([252,15]),stop=('保存node境界で停止',0x081c7a84),slot=slot,
                        extra=[(b.WINDOWS,bytes(pool),False)])
                    need(m.r[1]==b.BUFFER and m.r[2]==0x1000000|dims[0]*dims[1]*8,'BIOS transfer引数')
                    need(m.read(m.r[0],4)==0xdddddddd,'BIOS fill source')
            elif group=='renderer':
                # 未読controlの新規縦結合。終端/queue単独の再実行ではない。
                resource=next(r for r in context['tables']if r['start']==b.engine.TABLE);attr=bytes.fromhex(resource['hex'])
                for fast in(0,1):
                    for slot in(0,31):
                        raw=bytes([252,4,7,8,9,252,13,250,252,14,251,255])
                        at,p,segs=fixture(a,font=font,slot=slot,full=True,fast=fast,text=raw)
                        segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=(127,),enabled=1,dims=(2,2))['segments']
                        segs.append((LOOKUP,bytes(168),True));e=b.Expected(segs)
                        ptr=b.TEMPLATE
                        for sub,payload in ((4,bytes([7,8,9])),(13,bytes([250])),(14,bytes([251]))):
                            for w in prefix(at,p,font,pointer=ptr):e.write(*w)
                            if sub==4:writes=color_writes(at,p,sub,payload,pointer=ptr+2)
                            else:
                                offset=8 if sub==13 else 9;writes=[(at+offset,1,(payload[0]+p[offset-2])&255),(at,4,ptr+3)]
                            for w in writes:e.write(*w)
                            ptr+=2+len(payload)
                        e.write(at+30,1,0);e.write(at,4,ptr+1)
                        if fast:e.resource(slot,2)
                        e.write(at+27,1,0)
                        cases.run(f'renderer-{font}-{fast}-{slot}',b.RUN,segs,writes=e.writes,value=b.vm.RETURN)
        counts[group]=len(cases.rows)-before
    return cases,counts


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);validate_inputs(nodes,r['analysis']);return nodes,memory,context


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=contracts(nodes,a,context)
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table','scroll_table','pending_direct_callees')}
    result.update({'classification':'SAVED_CONTROL_COLOR_PROMPT_AND_PENDING_OUTPUT_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'groups':groups,'cases':cases.rows,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),'explicit_stack':{'start':strict.STACK_START,'end':strict.STACK_END},
        'control_selector_coverage':list(range(1,25)),'pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'pending_data_ja':['font2/4/5 bitmap/width','symbol/icon table','実音声song/player table','cursor画像とscroll実buffer'],
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'保存control表の有限効果とprompt初期化だけ。合成音声表は実値でなく、未読字形/音声/BIOSは停止。DMA/描画/実caller/Ring通常取得は未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in (text.prior.prior.prior.SELF,text.prior.prior.SELF,text.prior.SELF,strict.SELF,text.SELF,prior.SELF,SELF,TEST):
        sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources))
    # case原本はanalysis.jsonへ保存。後続のbyte継承用contextに同じ巨大列を複製しない。
    compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'保存6534命令でcontrol24表・色81要素展開・prompt初期化と通常高速出力を{r["contract_cases"]}条件'
        f'（帰還{r["conditional_return_cases"]}/pending{r["pending_stop_cases"]}）検証。候補復元/新規byte/native0。',
        '次は未読7calleeとfont bitmap/width・cursor/symbol・音声の必要dataを限定結合し、字形/cursor/scroll出力とBIOS境界へ進む。'
        '今回control/prompt・旧627text/font/BP/nativeは単独再実行しない。実描画/DMA・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
