#!/usr/bin/env python3
"""保存3955命令でheap分割・window連結・実描画の未map/callback境界を具体化する。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_ui_contracts as base
import pr16_ring_ui_leaf_bytes as prior

BASE='0714fd2c10079547443cedb96c69e643208cd055'
SLUG='pr16-ring-ui-leaf-contracts'
TASK='PR-P08-7-RING-UI-LEAF-CONTRACTS'
TITLE='heap分割完了・window連結・実描画callback境界を有界検証'
SELF='scripts/pr16_ring_ui_leaf_contracts.py'
TEST='tests/test_pr16_ring_ui_leaf_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-ui-leaf-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_ui_leaf_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存3955命令のheap分割・window連結・実renderの有界契約は今回原本を再利用。'
    'heap不足/assertは未読診断callee前、active描画は実gFontsとcallback未結合のまま保持。'
    '旧733条件・今回37命令採取・resource/BP/nativeを単独再実行しない。')
need=base.need
word=base.word
LOG=0x081c78fc
FATAL=0x081c7a28
GFONTS=0x03003dd0
TABLE=0x02002000
UNKNOWN=0x08040001
GROUPS=('split','split_release','split_partial','assert_prefix','window_split','init_window',
        'render_missing','render_table_bounds','render_arm_reject')


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,_=base.saved_inputs();r=s.load(PRIOR);a=r['analysis']
    saved.bindings_fresh(s.ROOT,r['source_bindings'])
    for key in ('new_windows','new_data_windows'):windows.add_windows(memory,a[key])
    nodes=[*nodes,*a['new_nodes']];f.nodes_to_memory(memory,nodes)
    need(len(nodes)==len({n['address']for n in nodes})==3955,'保存3955命令')
    need(a['pending_direct_callees']==[LOG|1,FATAL|1] and a['pending_continuations']==[], 'assert未読2callee')
    need(any(r['site']==0x081c7a5c and r['kind']=='decoder_rejection' and r['encoded']=='ffef'
        for r in a['pending_boundaries']),'assert未知encoding境界')
    need(a['actual_callback_table_observed']is False,'実callback table未観測')
    return nodes,memory,copy.deepcopy(a)


def arena(blocks):
    """合成連続heap。headerだけでなくpayload容量も明示してaliasを避ける。"""
    need(type(blocks)in (list,tuple) and 1<=len(blocks)<=4,'heap block数')
    need(all(type(active)is int and active in (0,1) and type(size)is int and 0<=size<=4096 and size%4==0
        for active,size in blocks),'heap block条件')
    positions=[];at=base.HEAP
    for _,size in blocks:positions.append(at);at+=16+size
    image=bytearray()
    for i,(active,size)in enumerate(blocks):
        image.extend(base.header(active,size,positions[(i-1)%len(blocks)],positions[(i+1)%len(blocks)]))
        image.extend(bytes(((j*13+i+7)&255)for j in range(size)))
    return [(base.GLOBALS,b'\xcc'*12,True),(base.HEAP_POINTER,word(base.HEAP),False),
        (base.HEAP,bytes(image),True)],positions


class Expected(base.Expected):
    def split(self,root,request):
        need(type(request)is int and 0<=request<=0xffffffff,'request u32')
        rounded=(request+3)&0xfffffffc
        self.write(base.GLOBALS,4,root);self.write(base.GLOBALS+4,4,root)
        at=root
        for _ in range(8):
            cap=self.read(at+4,4)
            if self.read(at,2)==0 and cap>=rounded:
                need(cap-rounded>=32,'今回split条件だけ')
                nxt=self.read(at+12,4);new=at+16+rounded
                self.write(base.GLOBALS+8,4,new);self.write(at,2,1);self.write(at+4,4,rounded)
                for offset,width,value in ((0,2,0),(2,2,0xa3a3),(4,4,cap-16-rounded),(8,4,at),(12,4,nxt)):
                    self.write(new+offset,width,value)
                self.write(at+12,4,new)
                if nxt!=root:self.write(nxt+8,4,new)
                return at+16
            nxt=self.read(at+12,4)
            if nxt==root:return None
            at=nxt;self.write(base.GLOBALS+4,4,at)
        raise ValueError('expected heap探索上限')


def images(expected,segments):
    return [(at,bytes(expected.mem[at+i]for i in range(len(data))),w)for at,data,w in segments]


def render_segments(slot,selector,fast=0,*,table=None,pointer=None):
    need(type(slot)is int and 0<=slot<32,'slot条件')
    need(type(selector)is int and 0<=selector<256,'selector条件')
    need(type(fast)is int and fast in (0,1),'fast条件')
    pool=bytearray(1024);pool[slot*32+27]=1;pool[slot*32+5]=selector
    config=bytearray(29);config[:4]=word(0x31534756);config[28]=fast
    rows=[(base.BUFFER,bytes(config),False),(base.POOL,bytes(pool),True)]
    if pointer is not None:rows.append((GFONTS,word(pointer),False))
    if table is not None:
        need(type(table)is bytes and 0<len(table)<=48,'合成table範囲')
        rows.append((TABLE,table,False))
    return rows


@functools.lru_cache(maxsize=None)
def run_group(name):
    need(name in GROUPS,'契約group')
    nodes,_,_=saved_inputs();cases=base.Cases(nodes)
    if name in ('split','split_release'):
        sizes=range(34)if name=='split'else (0,1,31,32,64)
        for size in sizes:
            rounded=(size+3)&~3
            for selected in (0,1,2):
                for slack in (32,36,128):
                    blocks=[(1,16)]*selected+[(0,rounded+slack),(1,16)]
                    segs,positions=arena(blocks);e=Expected(segs);pointer=e.split(base.HEAP,size)
                    label=f'{name}-{size}-{selected}-{slack}'
                    cases.run(label,base.ALLOC2,segs,(size,),e.writes,pointer)
                    if name=='split_release':
                        after=images(e,segs);f=Expected(after);f.free(base.HEAP,pointer)
                        cases.run(label+'-free',base.FREE2,after,(pointer,),f.writes,base.vm.RETURN)
                        need(f.read(pointer-12,4)==rounded+slack,'分割後free容量復元')
    elif name=='split_partial':
        for size in (0,4,32):
            segs,_=arena([(0,size+64)]);e=Expected(segs);e.split(base.HEAP,size)
            new=base.HEAP+16+size
            for count,pc in ((0,0x08002930),(1,0x08002930),(2,0x08002934),(3,0x08002934),
                             (4,0x08002936),(7,0x08002936),(8,0x08002938),(11,0x08002938),
                             (12,0x0800293a),(15,0x0800293a)):
                short=[*segs[:2],(base.HEAP,segs[2][1][:16+size+count],True)]
                expected=[]
                for at,width,value in e.writes:
                    if new<=at<new+16 and at+width>new+count:break
                    expected.append((at,width,value))
                cases.run(f'split-short-{size}-{count}',base.ALLOC2,short,(size,),expected,
                    stop=('未許可 write',pc))
    elif name=='assert_prefix':
        for request in (0,1,32,4096):
            segs,_=arena([(1,32)]);e=Expected(segs);need(e.split(base.HEAP,request)is None,'不足fixture')
            m=cases.run('alloc-assert-'+str(request),base.ALLOC2,segs,(request,),e.writes,stop=('保存node境界で停止',LOG))
            need(m.call_arguments[-1]['args']==[0x086c0ccc,0x081cde88,0xae,0x081cde9c],'不足診断引数')
        for pointer,active,magic in ((0,1,0xa3a3),(base.HEAP+16,0,0xa3a3),(base.HEAP+16,1,0)):
            segs=base.heap_segments([(active,32,magic)])
            cases.run(f'free-assert-{pointer}-{active}-{magic}',base.FREE2,segs,(pointer,),stop=('保存node境界で停止',LOG))
        segs=base.heap_segments([(1,32,0xa3a3),(0,32,0)])
        cases.run('free-assert-partial',base.FREE2,segs,(base.HEAP+16,),[(base.HEAP,2,0)],stop=('保存node境界で停止',LOG))
        for flag,fmt in ((0,0x086c0d00),(1,0x086c0ccc)):
            m=cases.run('assert-mode-'+str(flag),base.ASSERT|1,[],(0x12345678,123,0x23456789,flag),stop=('保存node境界で停止',LOG))
            need(m.call_arguments[-1]['args']==[fmt,0x12345678,123,0x23456789],'assert書式/引数')
    elif name=='window_split':
        for slot in (0,7,31):
            for dims in ((1,1),(2,3),(0,0)):
                source=base.template(3,dims);size=dims[0]*dims[1]*32
                heap,_=arena([(0,size+64)]);segs=base.base_segments(pool=base.window_pool(slot),
                    backgrounds=(base.SENTINEL,)*4,source=source)+heap
                e=Expected(segs);pointer=e.split(base.HEAP,size);at=base.WINDOWS+12*slot
                e.write(at+8,4,pointer);e.write(at,4,int.from_bytes(source[:4],'little'))
                e.write(at+4,4,int.from_bytes(source[4:],'little'))
                cases.run(f'window-split-{slot}-{dims}',base.ADD,segs,(base.TEMPLATE,),e.writes,slot)
    elif name=='init_window':
        for dims in ((1,1),(2,1),(0,0)):
            source=base.template(0,dims);size=dims[0]*dims[1]*32
            heap,_=arena([(0,size+64)])
            segs=base.base_segments(pool=b'\xaa'*384,backgrounds=(base.HEAP,)*4,source=source+b'\xff',flags=bytes(17))+heap
            table=saved_inputs()[2]['attribute_table']
            segs.extend(((base.engine.CONTEXT,bytes(64),True),(base.RESET,b'\x77',True),
                (table['address'],bytes.fromhex(table['hex']),False)))
            e=Expected(segs)
            for w in base.init_writes():e.write(*w)
            background=e.split(base.HEAP,0)
            e.write(base.BACKGROUNDS,4,background);e.write(base.engine.CONTEXT+4,4,background)
            pointer=e.split(base.HEAP,size)
            e.write(base.WINDOWS+8,4,pointer);e.write(base.WINDOWS,4,int.from_bytes(source[:4],'little'))
            e.write(base.WINDOWS+4,4,int.from_bytes(source[4:],'little'));e.write(base.RESET,1,0)
            cases.run('init-window-'+str(dims),base.INIT,segs,(base.TEMPLATE,),e.writes,1)
    elif name=='render_missing':
        for slot in range(32):
            for fast in (0,1):
                segs=render_segments(slot,0,fast)
                m=cases.run(f'render-global-{slot}-{fast}',base.RUN,segs,stop=('未map read',0x08002e54),
                    fault={'address':GFONTS,'size':4,'site':0x08002e54})
                need(base.THUNK in m.executed_sites and 0x08002e4c in m.executed_sites,'実thunk→RenderFont')
                segs=render_segments(slot,0,fast,pointer=0)
                cases.run(f'render-null-{slot}-{fast}',base.RUN,segs,stop=('未map read',0x08002e5e),
                    fault={'address':0,'size':4,'site':0x08002e5e})
    elif name=='render_table_bounds':
        need(UNKNOWN&~1 not in {n['address']for n in nodes},'unknown callbackが保存済み')
        table=(word(UNKNOWN)+b'\x55'*8)*2
        for slot in (0,15,31):
            for fast in (0,1):
                for selector in (0,1,2,3,255):
                    segs=render_segments(slot,selector,fast,table=table,pointer=TABLE)
                    if selector<2:
                        m=cases.run(f'render-unknown-{slot}-{fast}-{selector}',base.RUN,segs,stop=('保存node境界で停止',UNKNOWN&~1))
                        need(m.r[0]==base.POOL+32*slot and m.r[1]==UNKNOWN,'間接callback引数')
                    else:
                        cases.run(f'render-table-short-{slot}-{fast}-{selector}',base.RUN,segs,
                            stop=('未map read',0x08002e5e),fault={'address':TABLE+12*selector,'size':4,'site':0x08002e5e})
    elif name=='render_arm_reject':
        for callback in (0,0x08040000,0x02002000):
            segs=render_segments(31,0,table=word(callback)+bytes(8),pointer=TABLE)
            cases.run('render-arm-'+str(callback),base.RUN,segs,stop=('ARM state未対応',0x081c7acc))
    need(cases.rows,'空case集合')
    return cases.rows


def analyze(previous,out):
    import pr16_ring_followup_v2 as s
    nodes,_,a=saved_inputs();groups={name:copy.deepcopy(run_group(name))for name in GROUPS}
    rows=[row for items in groups.values()for row in items]
    result={'classification':'SAVED_HEAP_SPLIT_WINDOW_AND_ACTUAL_RENDER_BOUNDARIES_NOT_NATIVE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes),'new_node_count':0,
        'groups':groups,'contract_cases':len(rows),'conditional_return_cases':sum(r['returned']for r in rows),
        'fail_closed_cases':sum(not r['returned']for r in rows),'pending_direct_callees':[LOG|1,FATAL|1],
        'pending_effective_targets':[],'pending_continuations':[],
        'pending_decoder_rejections':[r for r in a['pending_boundaries']if r['kind']=='decoder_rejection'],
        'actual_render_frontier':{'global':GFONTS,'read_site':0x08002e54,'record_read_site':0x08002e5e,
            'record_stride':12,'selector_offset':5,'callback_thunk':0x081c7acc,'actual_table_observed':False,
            'synthetic_table_only_fail_closed':True,'success_stubs':0},
        'unbound_runtime_data':copy.deepcopy(a['unbound_runtime_data']),
        'all_assert_returns_proven':False,'actual_callback_table_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'all_callers_resolved':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'full_rom_scans':0,'saved_nodes_redecoded':0,
        'assumptions_ja':['合成連続heapの明示容量・非alias object/frame。実caller allocationを受入しない。',
            '分割完了後のfree連結とwindow生成を今回新規入力だけで検証。旧nosplit/733条件は単独再実行しない。',
            '初期化は背景設定0の合成条件だけ。size0背景pointerが次heap headerと重なる事実を保持し、実設定へ一般化しない。',
            'assertは保存frameと診断引数まで。未読2calleeと0x081C7A5Cの未知encodingを返却stubで埋めない。',
            '実hook→実thunk→RenderFontの実命令だけ。合成callback tableは範囲外/未読/ARM state停止の負例に限る。']}
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'保存3955命令のheap分割・window連結・実render境界を{r["contract_cases"]}条件で検証。'
        f'帰還{r["conditional_return_cases"]}、fail-closed {r["fail_closed_cases"]}。ROM復元/native0。',
        '次は実gFonts(0x03003DD0)初期化と12byte callback表の出自を固定候補の証拠へ結合する。'
        'assert残辺0x081C78FD/0x081C7A29と0x081C7A5C未知encodingは未証明で保持。'
        '今回3955命令契約・旧733条件/採取/resource/BP/nativeを単独再実行しない。'
        'Ring通常取得・装備実戦・保存、policy/Circus/P08は未受入。')


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    out=support.ROOT/'.local'/SLUG;out.mkdir(parents=True,exist_ok=True)
    base.export_development(out)
    sources=support.load(str(out.relative_to(support.ROOT)/'development-source.json'))
    sources[TEST]=(support.ROOT/TEST).read_text(encoding='utf-8')
    (out/'development-source.json').write_bytes(support.stable(sources))
    nodes,_,a=saved_inputs();(out/'saved-context.json').write_bytes(support.stable({'nodes':nodes,'analysis':a}))
    support.assert_remote(support.cmd('git','rev-parse','HEAD'),attempts=12)
    support.run(sys.modules[__name__])
