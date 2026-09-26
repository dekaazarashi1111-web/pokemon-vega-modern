#!/usr/bin/env python3
"""保存3918命令だけでUI pool/heap/実RunTextPrintersの帰還と部分書込を検証する。

合成RAMの明示範囲だけを使う。未読callee、実gFonts、native取得は補完しない。
既存の命令モデルと受入原本は変更せず、新しいcallerの結合だけを試す。
"""
from __future__ import annotations
import copy
import functools
import hashlib
import itertools
import json
import sys
from pathlib import Path
import pr16_ring_resource_contracts as engine
import pr16_ring_ui_runtime_bytes as previous

BASE='12b2619431206503e9bda3fc03c9597823b5cd0b'
SLUG='pr16-ring-ui-contracts'
TASK='PR-P08-7-RING-UI-CONTRACTS'
TITLE='保存pool・heap・実描画の条件付き帰還と不足時部分書込を結合'
SELF='scripts/pr16_ring_ui_contracts.py'
TEST='tests/test_pr16_ring_ui_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-ui-contracts.yml'
PRIOR=previous.REPORT
REPORT='content/modernization/pr16_ring_ui_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((previous.SELF,*previous.SOURCES,
    'scripts/pr16_ring_resource_contracts.py','scripts/pr16_ring_dispatch_contracts.py',
    'scripts/pr16_ring_gate_contracts.py','scripts/pr16_ring_caller_contracts.py',
    'scripts/pr16_ring_string_machine.py','scripts/pr16_ring_contract_machine.py',
    'scripts/pr16_ring_saved_contracts.py','scripts/pr16_ring_owner_context.py')))
NO_REPEAT=('保存3918命令のUI pool/heap/実RunTextPrinters有界契約は今回原本を再利用。'
    'heap不足/null freeのassert呼出前とsplit初期化前の部分書込を保持する。'
    '未読3callee/実gFontsを成功stubにせず、旧byte採取/旧resource/受入済みBP/nativeを単独再実行しない。')
need=engine.need
vm=engine.vm
Machine=engine.Machine
MASK=0xffffffff
POOL,WINDOWS,BACKGROUNDS=0x02020030,0x02020430,0x03003e80
HEAP,GLOBALS,HEAP_POINTER=0x02010000,0x02020004,0x03000a38
TEMPLATE,BUFFER,RESET=0x02001800,0x0203d000,0x03003e70
DUMMY,SENTINEL=0x081ce040,0x08003aed
ALLOC,FREE,ALLOC2,FREE2=0x0800295d,0x08002a09,0x08002b9d,0x08002bc5
INIT,ADD,REMOVE,FREE_ALL,DEACTIVATE=0x08003af1,0x08003cb1,0x08003e09,0x08003e99,0x08002c29
RUN,IMPL,ASSERT,SPLIT,THUNK=0x08002dd1,0x09378589,0x081c7a38,0x0800292c,0x09378678
GROUPS=('deactivate','full_pool','allocate','allocation_stops','free_heap','free_stops',
        'init_empty','init_stops','add_window','add_stops','remove_window','free_all','run_text')


def word(value):
    need(type(value)is int and 0<=value<=MASK,'u32引数')
    return value.to_bytes(4,'little')


def template(bg=0,dims=(1,1)):
    need(type(bg)is int and 0<=bg<256,'bg u8')
    need(len(dims)==2 and all(type(v)is int and 0<=v<256 for v in dims),'dimensions u8')
    return bytes((bg,3,5,*dims,7,9,0))


def window_pool(free=0,*,bg=0,pointer=0):
    need(free is None or type(free)is int and 0<=free<32,'free slot')
    data=bytearray((template(bg)+word(pointer))*32)
    if free is not None:data[12*free]=255
    return bytes(data)


def header(active,size,prev,nxt,magic=0xa3a3):
    need(type(active)is int and 0<=active<65536 and type(magic)is int and 0<=magic<65536,'header u16')
    return active.to_bytes(2,'little')+magic.to_bytes(2,'little')+word(size)+word(prev)+word(nxt)


def heap_segments(blocks):
    need(type(blocks)in (list,tuple) and 1<=len(blocks)<=8,'heap block数')
    rows=[]
    for i,(active,size,magic)in enumerate(blocks):
        at=HEAP+0x100*i
        rows.append((at,header(active,size,HEAP+0x100*((i-1)%len(blocks)),HEAP+0x100*((i+1)%len(blocks)),magic),True))
    return [(GLOBALS,b'\xcc'*12,True),(HEAP_POINTER,word(HEAP),False),*rows]


class Expected(engine.Expected):
    def image(self):
        h=hashlib.sha256()
        for at,b in sorted(self.mem.items()):h.update(word(at)+bytes([b]))
        return h.hexdigest()
    def free(self,root,pointer):
        at=pointer-16
        need(self.read(at+2,2)==0xa3a3 and self.read(at,2)==1,'expected free条件')
        self.write(at,2,0)
        right=self.read(at+12,4)
        if right!=root and self.read(right,2)==0:
            need(self.read(right+2,2)==0xa3a3,'expected right magic')
            self.write(at+4,4,(self.read(at+4,4)+16+self.read(right+4,4))&MASK)
            self.write(right+2,2,0)
            nxt=self.read(right+12,4);self.write(at+12,4,nxt)
            if nxt!=root:self.write(nxt+8,4,at)
        if at!=root:
            left=self.read(at+8,4)
            if self.read(left,2)==0:
                need(self.read(left+2,2)==0xa3a3,'expected left magic')
                nxt=self.read(at+12,4);self.write(left+12,4,nxt)
                if nxt!=root:self.write(nxt+8,4,left)
                self.write(at+2,2,0)
                self.write(left+4,4,(self.read(left+4,4)+16+self.read(at+4,4))&MASK)


class Cases:
    def __init__(self,nodes):self.nodes=nodes;self.rows=[]
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None):
        expected=Expected(segments)
        for w in writes:expected.write(*w)
        m=Machine(self.nodes,segments,args)
        try:m.run(entry)
        except ValueError as exc:
            if stop is None:raise ValueError(f'{label}: {exc}; pc={getattr(m,"last_pc",0):08X}')from exc
            need((str(exc),m.last_pc)==stop,'停止境界 '+label+': '+str(exc)+' '+hex(m.last_pc))
        else:need(stop is None,'未証明境界を通過 '+label)
        if fault is not None:need(m.read_fault==fault,'read fault差分 '+label)
        need(m.nonstack_writes()==list(writes),'正確順序write差分 '+label)
        need(all(m.mem[p]==b for p,b in expected.mem.items()),'最終object差分 '+label)
        objects=[(at,len(data))for at,data,w in segments if w and data]
        need(not engine.caller.outside_writes(m,objects),'所有object/frame外write '+label)
        if stop is None and value is not None:need(m.r[0]==value,'戻値差分 '+label)
        self.rows.append({'case':label,'returned':stop is None,'stop':None if stop is None else list(stop),
            'steps':m.steps,'maximum_stack_bytes':vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':expected.image(),'return_sp_r4_r11_proven':stop is None,
            'read_fault':m.read_fault,'calls':m.call_arguments})
        return m


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_followup_v2 as s
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,tables=previous.saved_inputs();r=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,r['source_bindings'])
    a=r['analysis']
    for k in ('new_windows','new_data_windows'):windows.add_windows(memory,a[k])
    nodes=[*nodes,*a['new_nodes']];f.nodes_to_memory(memory,nodes)
    need(len(nodes)==3918 and len({n['address']for n in nodes})==3918,'保存3918命令')
    need(a['pending_direct_callees']==[SPLIT|1,ASSERT|1,THUNK|1] and not a['pending_continuations'],'未読3callee境界')
    need(a['dummy_template']['hex']=='ff00000000000000','dummy差分')
    for k in ('actual_callback_table_observed','all_live_slot_bounds_proven','ring_acquisition_accepted','release_ready'):
        need(a[k]is False,'受入境界 '+k)
    return nodes,memory,copy.deepcopy(a)


def base_segments(*,pool=None,backgrounds=None,enabled=0,source=None,flags=None):
    table=next(t for t in saved_inputs()[2]['tables']if t['start']==engine.TABLE)
    need(table['length']==32,'保存属性表32byte')
    rows=[(engine.ENABLE,word(enabled),False),(DUMMY,bytes.fromhex('ff00000000000000'),False),
        (engine.TABLE,bytes.fromhex(table['hex']),False)]
    if pool is not None:rows.append((WINDOWS,pool,True))
    if backgrounds is not None:rows.append((BACKGROUNDS,b''.join(word(x)for x in backgrounds),True))
    if source is not None:rows.append((TEMPLATE,source,False))
    if flags is not None:rows.append((engine.FLAGS,flags,False))
    return rows


def init_writes(backgrounds=(0,0,0,0)):
    writes=[(BACKGROUNDS+4*i,4,x)for i,x in enumerate(backgrounds)]
    for i in range(32):writes.extend(((WINDOWS+12*i,4,255),(WINDOWS+12*i+4,4,0),(WINDOWS+12*i+8,4,0)))
    return writes


@functools.lru_cache(maxsize=None)
def run_group(name):
    need(name in GROUPS,'契約group')
    nodes,_,a=saved_inputs();cases=Cases(nodes)
    if name=='deactivate':
        for seed in (0,1,127,255):
            data=bytes((i*17+seed)&255 for i in range(1024))
            cases.run('deactivate-'+str(seed),DEACTIVATE,[(POOL,data,True)],
                writes=[(POOL+i*32+27,1,0)for i in reversed(range(32))],value=vm.RETURN)
    elif name=='full_pool':
        for bg in (0,3,4,254):
            m=cases.run('full-'+str(bg),ADD,[(WINDOWS,window_pool(None,bg=bg),True)],(0,),value=255)
            need([at for at,n,_ in m.reads if WINDOWS<=at<WINDOWS+384]==[WINDOWS+12*i for i in range(32)],'満杯探索32slot')
    elif name=='allocate':
        for size in (*range(65),65535,0xfffffffc,0xfffffffd,0xfffffffe,0xffffffff):
            aligned=(size+3)&0xfffffffc
            for slack in (0,31):
                if aligned+slack>MASK:continue
                for target in (0,1):
                    blocks=[(1,0,0xa3a3)]*target+[(0,aligned+slack,0xa3a3)]
                    segs=heap_segments(blocks);at=HEAP+target*256
                    writes=[(GLOBALS,4,HEAP),(GLOBALS+4,4,HEAP)]
                    if target:writes.append((GLOBALS+4,4,at))
                    writes.append((at,2,1))
                    cases.run(f'alloc-{size}-{slack}-{target}',ALLOC2,segs,(size,),writes,at+16)
    elif name=='allocation_stops':
        for size in (0,1,31,32,64):
            rounded=(size+3)&~3
            for capacity,active,target in ((rounded+32,0,SPLIT),(max(0,rounded-1),1,ASSERT)):
                segs=heap_segments([(active,capacity,0xa3a3)])
                writes=[(GLOBALS,4,HEAP),(GLOBALS+4,4,HEAP)]
                if target==SPLIT:writes.extend(((GLOBALS+8,4,HEAP+16+rounded),(HEAP,2,1),(HEAP+4,4,rounded)))
                m=cases.run(f'alloc-stop-{size}-{target:x}',ALLOC2,segs,(size,),writes,
                    stop=('保存node境界で停止',target))
                need(m.call_arguments[-1]['target']==target|1,'allocator未読target')
        cases.run('alloc-unmapped-header',ALLOC,[(GLOBALS,bytes(12),True)],(HEAP,8),
            [(GLOBALS,4,HEAP),(GLOBALS+4,4,HEAP)],stop=('未map read',0x0800297c))
    elif name=='free_heap':
        for count in (1,2,3):
            for target in range(count):
                for flags in itertools.product((0,1),repeat=count):
                    if flags[target]!=1:continue
                    segs=heap_segments([(v,32+4*i,0xa3a3)for i,v in enumerate(flags)])
                    e=Expected(segs);e.free(HEAP,HEAP+256*target+16)
                    cases.run(f'free-{count}-{target}-{flags}',FREE2,segs,(HEAP+256*target+16,),e.writes,vm.RETURN)
    elif name=='free_stops':
        for pointer,active,magic in ((0,1,0xa3a3),(HEAP+16,1,0),(HEAP+16,0,0xa3a3)):
            segs=heap_segments([(active,32,magic)])
            cases.run(f'free-invalid-{pointer}-{active}-{magic}',FREE2,segs,(pointer,),stop=('保存node境界で停止',ASSERT))
        for right_magic in (0,0xa3a2):
            segs=heap_segments([(1,32,0xa3a3),(0,32,right_magic)])
            cases.run('free-partial-'+str(right_magic),FREE2,segs,(HEAP+16,),[(HEAP,2,0)],stop=('保存node境界で停止',ASSERT))
    elif name=='init_empty':
        for bits in range(16):
            flags=b''.join(bytes((int(bool(bits&(1<<i))),0,0,0))for i in range(4))+b'\0'
            contexts=bytearray(64)
            for i in range(4):contexts[16*i+4:16*i+8]=word(HEAP if bits&(1<<i)else 0)
            bgs=tuple(SENTINEL if bits&(1<<i)else 0 for i in range(4))
            segs=base_segments(pool=b'\xaa'*384,backgrounds=(HEAP,)*4,source=b'\xff',flags=flags)
            segs.extend(((engine.CONTEXT,bytes(contexts),False),(RESET,b'\x77',True)))
            cases.run('init-empty-'+str(bits),INIT,segs,(TEMPLATE,),[*init_writes(bgs),(RESET,1,0)],1)
    elif name=='init_stops':
        for dims in ((0,0),(1,1),(1,2),(16,16),(255,255)):
            segs=base_segments(pool=b'\xaa'*384,backgrounds=(HEAP,)*4,source=template(0,dims)+b'\xff',enabled=1,flags=bytes(17))
            segs.extend(((engine.CONTEXT,bytes(64),False),(engine.BITS,b'\xff'*256,True)))
            cases.run('init-bitmap-shortage-'+str(dims),INIT,segs,(TEMPLATE,),init_writes(),0)
        segs=base_segments(pool=b'\xaa'*384,backgrounds=(0,)*4,flags=bytes(17))
        segs.append((engine.CONTEXT,bytes(64),False))
        cases.run('init-missing-terminator',INIT,segs,(TEMPLATE,),init_writes(),stop=('未map read',0x08003b4c))
        segs=base_segments(pool=b'\xaa'*(31*12),backgrounds=(0,)*4,source=b'\xff',flags=bytes(17))
        segs.append((engine.CONTEXT,bytes(64),False))
        cases.run('init-short-pool',INIT,segs,(TEMPLATE,),init_writes()[:4+31*3],stop=('未許可 write',0x08003b30))
    elif name=='add_window':
        for slot in range(32):
            for bg,dims in ((0,(1,1)),(3,(2,1)),(0,(0,0)),(3,(64,32)),(0,(255,255))):
                source=template(bg,dims);size=(dims[0]*dims[1]*32)&65535
                segs=base_segments(pool=window_pool(slot),backgrounds=(SENTINEL,)*4,source=source)+heap_segments([(0,size,0xa3a3)])
                at=WINDOWS+slot*12
                writes=[(GLOBALS,4,HEAP),(GLOBALS+4,4,HEAP),(HEAP,2,1),(at+8,4,HEAP+16),
                    (at,4,int.from_bytes(source[:4],'little')),(at+4,4,int.from_bytes(source[4:],'little'))]
                cases.run(f'add-{slot}-{bg}-{dims}',ADD,segs,(TEMPLATE,),writes,slot)
    elif name=='add_stops':
        for slot in (0,31):
            for bg in (0,3):
                segs=base_segments(pool=window_pool(slot),source=template(bg,(1,2)),enabled=1,flags=bytes(17))
                segs.append((engine.BITS,b'\xff'*256,True))
                cases.run(f'add-bitmap-full-{slot}-{bg}',ADD,segs,(TEMPLATE,),value=255)
        for bg in (4,31,255):
            segs=base_segments(pool=window_pool(0),backgrounds=(SENTINEL,)*4,source=template(bg))
            cases.run('add-bg-unmapped-'+str(bg),ADD,segs,(TEMPLATE,),stop=('未map read',0x08003d1a))
        segs=base_segments(pool=window_pool(0),backgrounds=(SENTINEL,)*4,source=template()[:5])+heap_segments([(0,32,0xa3a3)])
        writes=[(GLOBALS,4,HEAP),(GLOBALS+4,4,HEAP),(HEAP,2,1),(WINDOWS+8,4,HEAP+16)]
        cases.run('add-short-template-partial',ADD,segs,(TEMPLATE,),writes,stop=('未map read',0x08003dca))
    elif name=='remove_window':
        for slot in range(32):
            for bg in (0,3):
                pool=bytearray((bytes.fromhex(a['dummy_template']['hex'])+bytes(4))*32)
                pool[slot*12:slot*12+8]=template(bg)
                segs=base_segments(pool=bytes(pool),backgrounds=(SENTINEL,)*4)
                cases.run(f'remove-null-{slot}-{bg}',REMOVE,segs,(slot,),[(WINDOWS+slot*12,4,255),(WINDOWS+slot*12+4,4,0)],vm.RETURN)
        for slot in (32,255):
            segs=base_segments(pool=window_pool(None),backgrounds=(SENTINEL,)*4)
            cases.run('remove-slot-unmapped-'+str(slot),REMOVE,segs,(slot,),stop=('未map read',0x08003e18))
        pool=bytes.fromhex(a['dummy_template']['hex'])+bytes(4)
        pool=template()+bytes(4)+pool*31
        segs=base_segments(pool=pool,backgrounds=(0,)*4)+heap_segments([(1,32,0xa3a3)])
        cases.run('remove-last-null-background',REMOVE,segs,(0,),[(WINDOWS,4,255),(WINDOWS+4,4,0)],stop=('保存node境界で停止',ASSERT))
    elif name=='free_all':
        for bits in range(16):
            bgs=tuple(SENTINEL if bits&(1<<i)else 0 for i in range(4))
            segs=base_segments(pool=window_pool(None),backgrounds=bgs)
            cases.run('free-all-null-'+str(bits),FREE_ALL,segs,value=vm.RETURN)
        for slot in (0,31):
            pool=bytearray(window_pool(None));pool[slot*12+8:slot*12+12]=word(HEAP+16)
            segs=base_segments(pool=bytes(pool),backgrounds=(SENTINEL,)*4)+heap_segments([(1,32,0xa3a3)])
            cases.run('free-all-one-'+str(slot),FREE_ALL,segs,writes=[(HEAP,2,0),(WINDOWS+slot*12+8,4,0)],value=vm.RETURN)
    elif name=='run_text':
        for magic,fast in ((0,0),(0x31534756,0),(0x31534756,1),(0x31534756,255)):
            data=bytearray(29);data[:4]=word(magic);data[28]=fast
            pool=bytearray(b'\xa5'*1024)
            for i in range(32):pool[i*32+27]=0
            for entry in (RUN,IMPL):
                cases.run(f'run-inactive-{entry:x}-{magic}-{fast}',entry,[(BUFFER,bytes(data),False),(POOL,bytes(pool),True)],value=vm.RETURN if entry==RUN else 1)
            for slot in range(32):
                active=bytearray(pool);active[slot*32+27]=1;active[slot*32+28]=0
                m=cases.run(f'run-active-{magic}-{fast}-{slot}',RUN,[(BUFFER,bytes(data),False),(POOL,bytes(active),True)],stop=('保存node境界で停止',THUNK))
                args=m.call_arguments[-1]['args']
                need(args[0]==POOL+slot*32 and args[3]==0x08002e4d,'実render thunk引数')
        cases.run('run-missing-global',RUN,[],stop=('未map read',0x0937858e))
        cases.run('run-short-pool',RUN,[(BUFFER,word(0),False),(POOL,bytes(31*32),True)],stop=('未map read',0x0937859e))
    need(cases.rows,'空の検証group')
    return cases.rows


def analyze(prior,out):
    import pr16_ring_followup_v2 as s
    nodes,_,a=saved_inputs()
    groups={name:copy.deepcopy(run_group(name))for name in GROUPS}
    rows=[row for values in groups.values()for row in values]
    failed=s.api('actions/runs/35223426249')
    need(failed['head_sha']=='b2424e9964f752815df8dbca6a1ef7588c36722a' and failed['status']=='completed'
        and failed['conclusion']=='failure','初回Actions失敗原本')
    result={'classification':'SAVED_UI_POOL_HEAP_AND_ACTUAL_RENDER_CONDITIONAL_CONTRACTS_NOT_NATIVE',
        'candidate':copy.deepcopy(s.CANDIDATE),'saved_node_count':len(nodes),'groups':groups,
        'contract_cases':len(rows),'conditional_return_cases':sum(r['returned']for r in rows),
        'fail_closed_cases':sum(not r['returned']for r in rows),
        'development_failure_preserved':{'run_id':35223426249,'source_head':failed['head_sha'],
            'original_conclusion':'failure','tests_run':28,'errors':2,'artifact_id':10498260487,
            'artifact_sha256':'b035f151bd091d397809b89f24454c77af6e3e0e9e272cf7115710907c6a590e',
            'reason_ja':'合成RAMで保存属性分岐表と背景contextの明示mapが不足。旧engine/ROMは変更せず今回fixtureだけ修正。'},
        'pending_direct_callees':copy.deepcopy(a['pending_direct_callees']),
        'pending_continuations':[],'pending_effective_targets':[],
        'actual_callback_table_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'all_callers_resolved':False,'all_live_frames_proven':False,
        'all_runtime_owners_excluded':False,'caller_pointer_size_limit_proven':False,
        'unbound_runtime_data':copy.deepcopy(a['unbound_runtime_data']),
        'assumptions_ja':['合成RAMと明示的な非alias object/frameだけ。実heap/caller allocationの証明ではない。',
            'nosplit帰還とfree連結条件だけ。split helper/asserter/render thunkは未読地点で停止する。',
            'size切上げu32 wrap・寸法積u16切捨て・slot/bg上限不足は修正せず実byteの条件として保持。',
            '満杯windowはtemplate非参照。初期化/不足/不正freeは部分書込を巻き戻さない。',
            '実hookから全非active帰還と最初のactive thunkまで。描画callback成功/native取得ではない。'],
        'ring_acquisition_accepted':False,'release_ready':False,'rom_changes':0,'new_emulator_processes':0,
        'candidate_reconstructions':0,'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,
        'saved_nodes_redecoded':0,'new_node_count':0,'full_rom_scans':0}
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return (f'保存3918命令のpool/heap/実RunTextPrintersを{r["contract_cases"]}条件で結合。'
        f'条件付き帰還{r["conditional_return_cases"]}、fail-closed {r["fail_closed_cases"]}。'
        'ROM復元/新規byte/既読単独検証/native0。',
        '次は未読0x0800292D(heap split初期化)、0x081C7A39(assert実体)、0x09378679(render thunk)だけを採取し、'
        '保存heap不足・split部分書込とactive描画継続を結合する。実gFonts callback tableは未観測のまま。'
        '今回pool/heap/非active帰還・旧byte/旧resource/BP/nativeを単独再実行しない。'
        'Ring通常取得・装備実戦・保存、policy/Circus/P08は未受入。')


def export_development(out):
    """診断時もexact保存contextと使用sourceだけをtext artifactへ残す。ROMは出力しない。"""
    import pr16_ring_followup_v2 as s
    nodes,_,a=saved_inputs()
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':a}))
    paths={SELF,TEST}
    for module in tuple(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file:
            p=Path(file).resolve()
            if p.parent==s.ROOT/'scripts' and p.name.startswith('pr16_'):paths.add(str(p.relative_to(s.ROOT)))
    (out/'development-source.json').write_bytes(s.stable({p:(s.ROOT/p).read_text(encoding='utf-8')for p in sorted(paths)}))


if __name__=='__main__':
    import pr16_ring_followup_v2 as support
    need(sys.argv[1:]==['run'],'runだけを許可')
    out=support.ROOT/'.local'/SLUG;out.mkdir(parents=True,exist_ok=True)
    export_development(out)
    support.run(sys.modules[__name__])
