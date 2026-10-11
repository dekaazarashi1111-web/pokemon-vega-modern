#!/usr/bin/env python3
"""保存5891命令だけでtext状態/終端/遅延と実RunTextPrintersの出力予約を結合。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_character_frontier as prior
import pr16_ring_explicit_text_machine as strict
import pr16_ring_followup_v2 as s

BASE='908fb12c8d026291b30eb8b2665428f303eeb12e'
SLUG='pr16-ring-text-state-contracts'
TASK='PR-P08-7-RING-TEXT-STATE-CONTRACTS'
TITLE='明示RAMでtext状態・終端・遅延と通常高速描画の出力予約を結合'
SELF='scripts/pr16_ring_text_state_contracts.py'
TEST='tests/test_pr16_ring_text_state_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-text-state-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_text_state_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=36
EXTRA_CODE=(strict.SELF,)
SOURCES=tuple(dict.fromkeys((strict.SELF,prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存text状態/終端/遅延/通常高速描画の明示RAM契約を再利用。音声globalと512byte live stackを分離。'
    '未読control24表・字形callee・cursor/audio/BIOS境界を成功stubにしない。'
    '今回契約/既読byte採取/旧font初期化/BP/nativeは単独再実行しない。')
b=strict.b;need=s.need
GFONTS,KEYS,TEXT_FLAGS,LINK_MODE=0x03003dd0,0x03003130,0x03003e90,0x0203ad72
GROUPS=('state_delay','audio','text_delay','characters','auto_wait','cursor_wait','missing','renderer')


def audio_active(first,second):
    for n in (first,second):need(type(n)is int and 0<=n<=0xffffffff,'audio status u32')
    return not bool(first&second&0x80000000) and bool((first|second)&65535)


def checked_table(row,size):
    need(type(row)is dict and 'address'in row and 'hex'in row and 'identity'in row,'保存表形式')
    data=bytes.fromhex(row['hex']);need(len(data)==size and s.identity(data)==row['identity'],'保存表hash/長')
    return row['address'],data,False


def validate_inputs(nodes,a,context):
    need(len(nodes)==len({n['address']for n in nodes})==5891,'保存5891命令')
    need(a['ring_acquisition_accepted']is False and a['release_ready']is False,'受入境界')
    need([f['selector']for f in a['selected_fonts']]==[2,4,5],'font集合')
    need([r['name']for r in a['dispatch_tables']]==['character','selected_glyph'],'文字/字形表集合')
    tables=[checked_table(a['state_table'],28),checked_table(a['dispatch_tables'][0],32),
        checked_table(a['dispatch_tables'][1],24),checked_table(a['tables'][0],192)]
    need([r[0]for r in tables]==[0x0800577c,0x0800582c,0x08005ae4,0x083e30e8],'表アドレス差分')
    need(a['tables'][0]['initializer_runtime_observed']is False,'実初期化未観測')
    attr=next(r for r in context['tables']if r['start']==b.engine.TABLE)
    need(attr['length']==32 and s.identity(bytes.fromhex(attr['hex']))==attr['identity'],'属性表hash')
    return tables,bytes.fromhex(attr['hex'])


def fixture(a,*,font=2,state=0,speed=0,counter=0,text=b'\xff',flags=0,keys=0,held=0,
            internal=None,blink=128,auto_counter=0,slot=0,fast=0,full=False,initial=(3,5),cursor=(7,9)):
    for name,v in (('font',font),('state',state),('speed',speed),('counter',counter),('flags',flags),
                   ('blink',blink),('auto_counter',auto_counter)):
        need(type(v)is int and 0<=v<256,name+' u8')
    need(font in (2,4,5)and type(slot)is int and 0<=slot<32 and fast in (0,1),'font/slot/fast')
    need(type(text)is bytes and len(text)<=64,'有限text')
    for v in (keys,held):need(type(v)is int and 0<=v<=65535,'key u16')
    need(type(full)is bool and type(fast)is int,'full/fast型')
    need(internal is None or type(internal)is int and 0<=internal<256,'internal u8')
    need(len(initial)==len(cursor)==2 and all(type(v)is int and 0<=v<256 for v in (*initial,*cursor)),'cursor座標')
    pool=bytearray(1024 if full else 32);offset=slot*32 if full else 0;at=b.POOL+offset
    p=bytearray(32);p[:4]=b.word(b.TEMPLATE);p[4]=slot;p[5]=font;p[6:10]=bytes((*initial,*cursor));p[11]=2
    p[20]=font if internal is None else internal;p[21]=blink;p[22]=auto_counter;p[27]=1;p[28]=state;p[29]=speed;p[30]=counter
    pool[offset:offset+32]=p
    segments=[(b.POOL,bytes(pool),True),* [checked_table(row,n)for row,n in
        ((a['state_table'],28),(a['dispatch_tables'][0],32),(a['dispatch_tables'][1],24),(a['tables'][0],192))],
        (GFONTS,b.word(a['tables'][0]['address']),False),(KEYS+44,held.to_bytes(2,'little')+keys.to_bytes(2,'little'),False),
        (TEXT_FLAGS,b.word(flags),False),(b.TEMPLATE,text,False)]
    # 保存RSBS/ADCSはconfig byte==0をfastにする（0/非0の反転を維持）。
    if full:segments.append((b.BUFFER,b.word(0x31534756)+bytes(24)+bytes([0 if fast else 1]),False))
    return at,p,segments


def setup_writes(at,p,font):
    return []if p[21]&128 else [(at+20,1,(p[20]&240)|font),(at+21,1,p[21]|128)]


def ready_writes(at,speed,flags,held,internal):
    writes=[(at+30,1,0)]if held&3 and internal&16 else []
    return writes+[(at+30,1,1 if flags&4 else speed),(at,4,b.TEMPLATE+1)]


def contracts(nodes,a,context,groups=GROUPS):
    validate_inputs(nodes,a,context);cases=strict.Cases(nodes);group_counts={};resource=next(r for r in context['tables']if r['start']==b.engine.TABLE)
    attr=bytes.fromhex(resource['hex'])
    for group in groups:
        need(group in GROUPS,'契約group');before=len(cases.rows)
        for f in a['selected_fonts']:
            font=f['selector'];entry=f['callback']
            def run(label,kwargs,writes,value=3,stop=None,fault=None,extra=()):
                at,p,segs=fixture(a,font=font,**kwargs)
                return cases.run(f'{group}-{font}-{label}',entry,[*segs,*extra],(at,),
                    setup_writes(at,p,font)+writes,value,stop,fault)
            at=b.POOL
            if group=='state_delay':
                for counter in (0,1,2,127,255):
                    writes=[(at+30,1,counter-1)]if counter else [(at+28,1,0)]
                    run(str(counter),{'state':6,'counter':counter},writes)
                run('scroll-complete',{'state':4},[(at+28,1,0)])
            elif group=='audio':
                for first in (0,1,0x80000000,0x80000001):
                    for second in (0,1,0x80000000,0x80000001):
                        writes=[]if audio_active(first,second)else [(at+28,1,0)]
                        run(f'{first}-{second}',{'state':5},writes,extra=[(strict.AUDIO[0],b.word(first),False),(strict.AUDIO[1],b.word(second),False)])
            elif group=='text_delay':
                for counter in (1,2,255):
                    for speed in (1,255):
                        for flags in (0,1,4,5):
                            for keys in (0,1,2,4):
                                writes=[(at+30,1,counter-1)]
                                if flags&1 and keys&3:writes.extend(((at+20,1,font|16),(at+30,1,0)))
                                run(f'{counter}-{speed}-{flags}-{keys}',dict(counter=counter,speed=speed,flags=flags,keys=keys),writes)
            elif group=='characters':
                for speed in (0,1,255):
                    for flags in (0,4):
                        for held in (0,1):
                            internal=font|16;writes=ready_writes(at,speed,flags,held,internal)
                            run(f'end-{speed}-{flags}-{held}',dict(speed=speed,flags=flags,held=held,internal=internal),writes,1)
                for cursor in ((7,9),(255,250)):
                    writes=ready_writes(at,0,0,0,font)+[(at+8,1,3),(at+9,1,(cursor[1]+14)&255)]
                    run(f'newline-{cursor}',dict(text=b'\xfe',cursor=cursor),writes,2)
                run('placeholder-skip',dict(text=b'\xfd\x01'),ready_writes(at,0,0,0,font)+[(at,4,b.TEMPLATE+2)],2)
                for value in (0,1,247):
                    target={2:0x08006354,4:0x080064b8,5:0x0800657c}[font]
                    run(f'glyph-pending-{value}',dict(text=bytes([value])),ready_writes(at,0,0,0,font),stop=('保存node境界で停止',target))
                for subtype in (1,24):
                    writes=ready_writes(at,0,0,0,font)+[(at,4,b.TEMPLATE+2)]
                    run(f'control-table-pending-{subtype}',dict(text=bytes([252,subtype])),writes,
                        stop=('未map read',0x0800588a),fault={'address':0x08005894+(subtype-1)*4,'size':4,'site':0x0800588a})
                for code,state in ((250,3),(251,2)):
                    writes=ready_writes(at,0,0,0,font)+[(at+28,1,state)]
                    run(f'prompt-init-pending-{code}',dict(text=bytes([code])),writes,stop=('保存node境界で停止',0x08005494))
            elif group=='auto_wait':
                for mode in (0,2):
                    threshold=50 if mode==2 else 120
                    for counter in (0,threshold-1,threshold,255):
                        writes=[(at+28,1,0)]if counter==threshold else [(at+22,1,(counter+1)&255)]
                        run(f'{mode}-{counter}',dict(state=1,flags=4,auto_counter=counter),writes,
                            extra=[(LINK_MODE,bytes([mode]),False)])
                    for state in (2,3):
                        for counter in (0,threshold-1,255):
                            run(f'cursor-{state}-{mode}-{counter}',dict(state=state,flags=4,auto_counter=counter),
                                [(at+22,1,(counter+1)&255)],extra=[(LINK_MODE,bytes([mode]),False)])
                run('manual-no-key',dict(state=1),[])
            elif group=='cursor_wait':
                for state in (2,3):
                    for counter in (1,2,31):
                        run(f'{state}-{counter}',dict(state=state,blink=128|counter),[(at+21,1,128|counter-1)])
            elif group=='missing':
                run('audio-absent',dict(state=5),[],stop=('未map read',0x08071b88),
                    fault={'address':strict.AUDIO[0],'size':4,'site':0x08071b88})
                run('audio-second-absent',dict(state=5),[],stop=('未map read',0x08071ba8),
                    fault={'address':strict.AUDIO[1],'size':4,'site':0x08071ba8},extra=[(strict.AUDIO[0],b.word(0),False)])
                run('source-empty',dict(text=b'',speed=7),[(at+30,1,7)],stop=('未map read',0x0800580e),
                    fault={'address':b.TEMPLATE,'size':1,'site':0x0800580e})
                run('control-byte-empty',dict(text=b'\xfc'),ready_writes(at,0,0,0,font),stop=('未map read',0x08005876),
                    fault={'address':b.TEMPLATE+1,'size':1,'site':0x08005876})
            elif group=='renderer':
                for fast in (0,1):
                    for slot in (0,31):
                        for occupied in ((),(127,),tuple(range(128))):
                            for text in (b'\xff',b'\xfe\xff',b'\xfd\x01\xff'):
                                at,p,segs=fixture(a,font=font,slot=slot,fast=fast,full=True,text=text)
                                segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=occupied,enabled=1,dims=(2,2))['segments']
                                e=b.Expected(segs);ptr=b.TEMPLATE
                                for char in text:
                                    if char==1:continue
                                    e.write(at+30,1,0);ptr+=1;e.write(at,4,ptr)
                                    if char==254:e.write(at+8,1,3);e.write(at+9,1,23)
                                    elif char==253:ptr+=1;e.write(at,4,ptr)
                                if fast:e.resource(slot,2)
                                e.write(at+27,1,0)
                                m=cases.run(f'render-{font}-{fast}-{slot}-{len(occupied)}-{text.hex()}',b.RUN,segs,writes=e.writes,value=b.vm.RETURN)
                                actual=[r for r in m.call_arguments if r['target']==(b.THUNK|1)and r['args'][3]==b.engine.RESOURCE]
                                need(len(actual)==fast,'通常/高速終端resource回数')
                for fast in (0,1):
                    at,p,segs=fixture(a,font=font,fast=fast,full=True,state=6,counter=1)
                    cases.run(f'render-delay-{font}-{fast}',b.RUN,segs,writes=[(at+30,1,0)],value=b.vm.RETURN)
        group_counts[group]=len(cases.rows)-before
    return cases,group_counts


def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);validate_inputs(nodes,r['analysis'],context)
    return nodes,memory,context


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=contracts(nodes,a,context)
    result={'classification':'SAVED_TEXT_STATE_TERMINATOR_DELAY_RENDER_QUEUE_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,
        'contract_cases':len(cases.rows),'conditional_return_cases':sum(r['returned']for r in cases.rows),
        'pending_stop_cases':sum(not r['returned']for r in cases.rows),'groups':groups,'cases':cases.rows,
        'executed_saved_sites':sorted(cases.sites),'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),
        'explicit_stack':{'start':strict.STACK_START,'end':strict.STACK_END,'unwritten_reads_rejected':True,
            'implicit_zero_globals':False,'audio_addresses':list(strict.AUDIO),'accepted_predecessor_model_modified':False},
        'state_table':copy.deepcopy(a['state_table']),'dispatch_tables':copy.deepcopy(a['dispatch_tables']),
        'tables':copy.deepcopy(a['tables']),'selected_fonts':copy.deepcopy(a['selected_fonts']),
        'pending_direct_callees':copy.deepcopy(a['pending_direct_callees']),
        'pending_boundaries':copy.deepcopy(a['pending_boundaries']),
        'inherited_pending_boundaries':copy.deepcopy(a['inherited_pending_boundaries']),
        'original_failed_test_run_preserved':{'run_id':35235301725,'source_head':'9843ef78c726f2c89902ba4d91cc272ea58a904c',
            'artifact_id':10502582515,'artifact_sha256':'752c93719e2fecc37baecab4ce0f6ddb6fa8df5f859ff2c696281f7a9849a71f',
            'original_conclusion':'failure','reason':'duplicate-node fixture omitted duplicate; repaired in 672521934bfd29e8c77c5de37e69b47c235af626',
            'candidate_reconstructions':0,'result_relabelled':False},
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'合成RAMの通常/高速終端とqueue予約まで。字形/制御/音声再生/BIOS、DMA実行、実gFonts初期化とRing通常取得は未受入。'}
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in (prior.prior.prior.SELF,prior.prior.SELF,prior.SELF,strict.SELF,SELF,TEST):sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources))
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':result,'inherited_analysis':context}))
    return result


def summaries(r):
    return (f'保存5891命令だけで{r["contract_cases"]}text条件（帰還{r["conditional_return_cases"]}/pending停止{r["pending_stop_cases"]}）を検証。'
        '512byte明示live stack/音声RAM分離、通常高速終端・改行・遅延と出力queue予約を結合。候補復元/native0。',
        '次は保存pendingからcontrol24表、font2/4/5字形callee、prompt初期化・cursor/scroll出力と音声/BIOSを有限結合。'
        '今回state/終端/遅延/queue契約、保存byte採取、受入済みfont/BP/nativeは単独再実行しない。'
        '実文字描画/DMA・全live owner・gFonts初期化・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
