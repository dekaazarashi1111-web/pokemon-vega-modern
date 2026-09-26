#!/usr/bin/env python3
"""保存cursor/scrollをpixel・出力queue・state2/3/4へ結合。ROM/nativeは変更しない。"""
from __future__ import annotations
import copy
import functools
import hashlib
import json
import sys
import pr16_ring_glyph_contracts as prior
import pr16_ring_followup_v2 as s

BASE='4990580c0b60e4c0a07c069cdb4fe4b55ea3c951'
SLUG='pr16-ring-cursor-scroll-contracts'
TASK='PR-P08-7-RING-CURSOR-SCROLL-CONTRACTS'
TITLE='保存cursorと上下scrollのpixel・queue・待機stateを明示RAMへ結合'
SELF='scripts/pr16_ring_cursor_scroll_contracts.py'
TEST='tests/test_pr16_ring_cursor_scroll_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-cursor-scroll-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_cursor_scroll_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存cursor/scrollのpixel・queue・state2/3/4は本原本を再利用する。'
    '4byte旧stack残値の明示条件とfillの隣接nibble効果、speed3..7の進捗0を保持。'
    '同じcursor/scroll・1122glyph・636control/627text・font/BP/nativeは単独再実行しない。')
b=prior.b
strict=prior.strict
control=prior.control
text=control.text
need=s.need
PIXELS=prior.PIXELS
SCROLL=0x08004475
CURSOR=0x080054c5
ERASE=0x080055a1
CONFIG_POINTER=0x0300504c
CONFIG=0x02001000
GROUPS=('scroll','scroll_state','cursor','erase','cursor_state','stack_residue','boundaries')
POSITIONS=((0,0),(1,1),(7,7),(23,23),(24,24),(255,255))
# 初期RAM全体のゼロ埋めを許可しない。call pathで再利用されるこの4byteだけが明示入力。
RESIDUE_OFFSETS=(48,72,100)
WORD_PREFIX={0x0800438e:'0e4e',0x08004390:'039d',0x08004392:'3540',0x08004394:'0543',
    0x08004396:'0395',0x08004398:'2479',0x0800439a:'e404',0x0800439c:'0b48',
    0x0800439e:'2840',0x080043a0:'2043',0x080043a2:'0390'}


class Machine(prior.Machine):
    def __init__(self,nodes,segments,args=(),*,residues=()):
        self.dimension_reads=[];self.dimension_writes=[]
        super().__init__(nodes,segments,args)
        need(type(residues)in(tuple,list)and len(residues)<=1,'旧stack明示入力は1word以下')
        for offset,value in residues:
            need(type(offset)is int and offset in RESIDUE_OFFSETS,'旧stack許可offset')
            prior.uint(value,32,'旧stack値');at=b.vm.SP-offset
            need(all(at+i not in self.mem for i in range(4)),'旧stack入力重複')
            for i in range(4):self.mem[at+i]=(value>>(8*i))&255

    def read(self,at,size):
        value=super().read(at,size)
        if getattr(self,'last_pc',None)==0x08004390:self.dimension_reads.append((at,size,value))
        return value

    def write(self,at,size,value):
        super().write(at,size,value)
        if getattr(self,'last_pc',None)==0x080043a2:self.dimension_writes.append((at,size,value&0xffffffff))


class Cases(prior.Cases):
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None,*,residues=()):
        need(label not in {r['case']for r in self.rows},'契約label重複')
        e=b.Expected(segments)
        for w in writes:e.write(*w)
        m=Machine(self.nodes,segments,args,residues=residues)
        try:m.run(entry)
        except ValueError as exc:
            if stop is None:raise ValueError(f'{label}: {exc}; pc={getattr(m,"last_pc",0):08X}; fault={m.read_fault}')from exc
            need((str(exc),m.last_pc)==stop,'停止境界 '+label+': '+str(exc)+' '+hex(m.last_pc))
        else:need(stop is None,'未証明境界を通過 '+label)
        if fault is not None:need(m.read_fault==fault,'read fault差分 '+label)
        need(m.nonstack_writes()==list(writes),'正確順序write差分 '+label)
        need(all(m.mem[p]==v for p,v in e.mem.items()),'最終object差分 '+label)
        allowed=set(range(m.low_sp,b.vm.SP))
        for at,data,writable in segments:
            if writable:allowed.update(range(at,at+len(data)))
        need(all(all(at+i in allowed for i in range(size))for at,size,_ in m.writes),'object/live-frame外write '+label)
        if stop is None and value is not None:need(m.r[0]==value,'戻値差分 '+label)
        if residues:
            offset,residue=residues[0];at=b.vm.SP-offset
            need(m.dimension_reads==[(at,4,residue)],'旧stack明示値消費 '+label)
            need(len(m.dimension_writes)==1 and m.dimension_writes[0][:2]==(at,4),'寸法word確定site '+label)
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'returned':stop is None,'return_value':m.r[0]if stop is None else None,
            'stack_residues':list(residues),'dimension_reads':m.dimension_reads,'dimension_writes':m.dimension_writes,'stop':None if stop is None else list(stop),'read_fault':m.read_fault,'steps':m.steps,
            'maximum_stack_bytes':b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':e.image(),'return_sp_r4_r11_proven':stop is None,'calls':m.call_arguments})
        return m


def validate_inputs(nodes,a,context):
    prior.validate_inputs(nodes,a)
    by={n['address']:n for n in nodes}
    for at,raw in WORD_PREFIX.items():need(by[at]['hex']==raw,'stack word prefix差分')
    need(by[0x0800438e]['literal_value']==0xffff0000 and by[0x0800439c]['literal_value']==65535,'stack word mask差分')
    table=text.checked_table(a['scroll_table'],8)
    need(table[0]==0x081ce54c and table[1]==bytes([1,2,4,0,0,0,0,0]),'scroll速度表')
    row=next(r for r in context['tables']if r['start']==b.engine.TABLE)
    data=bytes.fromhex(row['hex']);need(len(data)==32 and s.identity(data)==row['identity'],'属性表')
    return data


def initialized_dimensions(residue,dims):
    """保存2maskの代数形。全u32旧値は2回目ANDで消え、両halfwordが確定する。"""
    prior.uint(residue,32,'旧値')
    need(type(dims)in(tuple,list)and len(dims)==2,'寸法2個')
    for n in dims:prior.uint(n,8,'寸法')
    partial=(residue&0xffff0000)|(dims[0]*8)
    return (partial&65535)|(dims[1]*8<<16)


def pixel_buffer(dims):
    need(type(dims)in(tuple,list)and len(dims)==2,'2寸法')
    for v in dims:prior.uint(v,8,'寸法')
    return bytes((i*37+0xab)&255 for i in range(dims[0]*dims[1]*32))


def scroll_writes(initial,dims,direction,amount,fill):
    need(type(initial)is bytes and len(initial)==dims[0]*dims[1]*32,'scroll buffer長')
    for v in(*dims,direction,amount,fill):prior.uint(v,8,'scroll値')
    if direction not in(0,1):return []
    width,height=dims;writes=[]
    # 独立幾何モデル: destinationのtile/rowからsourceのy座標を求める。
    indices=range(width*height)if direction==0 else reversed(range(width*height))
    for tile in indices:
        tx,ty=tile%width,tile//width
        for row in(range(8)if direction==0 else reversed(range(8))):
            y=ty*8+row;source_y=y+amount if direction==0 else y-amount
            if 0<=source_y<height*8:
                offset=((source_y//8)*width+tx)*32+(source_y%8)*4
                value=int.from_bytes(initial[offset:offset+4],'little')
            else:value=fill*0x01010101
            writes.append((PIXELS+tile*32+row*4,4,value))
    return writes


def fill_writes(initial,dims,cursor,color):
    need(type(initial)is bytes and len(initial)==dims[0]*dims[1]*32,'fill buffer長')
    for v in(*dims,*cursor,color):prior.uint(v,8,'fill値')
    data=bytearray(initial);writes=[]
    for y in range(cursor[1],min(cursor[1]+12,dims[1]*8)):
        for x in range(cursor[0],min(cursor[0]+10,dims[0]*8)):
            offset=prior.pixel_offset(x,y,dims[0])
            # 実8bit色のORを保持。偶数xの書込は隣接上位nibbleにも影響し得る。
            value=((data[offset]&(15 if x&1 else 240))|(color<<(4 if x&1 else 0)))&255
            data[offset]=value;writes.append((PIXELS+offset,1,value))
    return writes,bytes(data)


def copy_writes(a,initial,dims,cursor,style,frame):
    need(type(style)is int and style in(0,1)and type(frame)is int and 0<=frame<4,'cursor style/frame')
    need(type(initial)is bytes and len(initial)==dims[0]*dims[1]*32,'copy buffer長')
    for v in(*dims,*cursor):prior.uint(v,8,'copy値')
    rows={r['name']:r for r in a['output_data']}
    _,data,_=prior.checked_data(rows['cursor-two-sources-window'])
    _,anim,_=prior.checked_data(rows['cursor-animation']);source_x=anim[frame]
    target=bytearray(initial);writes=[]
    for y in range(min(12,dims[1]*8-cursor[1])):
        for x in range(min(10,dims[0]*8-cursor[0])):
            sx=x+source_x;offset=style*256+prior.pixel_offset(sx,y,16)
            color=(data[offset]>>(4*(sx%2)))&15
            if color==0:continue
            px,py=cursor[0]+x,cursor[1]+y;offset=prior.pixel_offset(px,py,dims[0]);shift=(px%2)*4
            value=(target[offset]&(240>>shift))|(color<<shift)
            target[offset]=value;writes.append((PIXELS+offset,1,value))
    return writes


def output_fixture(a,attr,*,font=2,state=0,frame=0,style=0,cursor=(0,0),slot=0,occupied=(127,),color=13,dims=(3,3)):
    at,p,segs=control.fixture(a,font=font,state=state,blink=128|frame<<5,cursor=cursor,slot=slot,flags=style*2,colors=(0xab,color))
    initial=pixel_buffer(dims)
    segs+=b.engine.fixture(attr,slot=slot,head=127,occupied=occupied,enabled=1,dims=dims,source=PIXELS)['segments']
    segs.append((PIXELS,initial,True))
    segs.extend(prior.checked_data(r)for r in a['output_data']if r['name'].startswith('cursor'))
    return at,p,segs,initial


def cursor_expected(a,segs,at,p,initial,dims,cursor,style,frame,erase=False):
    writes,filled=fill_writes(initial,dims,cursor,(p[13]&15)*17)
    if not erase:writes+=copy_writes(a,filled,dims,cursor,style,frame)
    e=b.Expected(segs)
    for w in writes:e.write(*w)
    e.resource(p[4],2)
    if not erase:
        e.write(at+21,1,p[21]|8);e.write(at+21,1,(p[21]&128)|8|((frame+1)&3)<<5)
    return e


def contracts(nodes,a,context,groups=GROUPS):
    attr=validate_inputs(nodes,a,context);cases=Cases(nodes);counts={}
    for group in groups:
        need(group in GROUPS,'group');before=len(cases.rows)
        if group=='scroll':
            for dims in((1,1),(2,3),(3,2),(0,3),(3,0)):
                for direction in(0,1,2,255):
                    for amount in(0,1,2,4,7,8,9,15,24,255):
                        initial=pixel_buffer(dims)
                        cases.run(str((group,dims,direction,amount)),SCROLL,
                            [prior.window_segment(0,dims),(PIXELS,initial,True)],(0,direction,amount,0xa5),
                            scroll_writes(initial,dims,direction,amount,0xa5))
        elif group=='scroll_state':
            for f in a['selected_fonts']:
                for speed in range(8):
                    for remaining in(1,2,3,4,15,255):
                        dims=(2,3);slot=31 if remaining==255 else 0
                        occupied=tuple(range(128))if remaining==15 else(127,)
                        at,p,segs,initial=output_fixture(a,attr,font=f['selector'],state=4,slot=slot,occupied=occupied,dims=dims)
                        p[31]=remaining;segs[0]=(at,bytes(p),True)
                        segs.extend(((CONFIG_POINTER,b.word(CONFIG),False),(CONFIG+20,bytes([speed]),False),text.checked_table(a['scroll_table'],8)))
                        amount=min(remaining,bytes.fromhex(a['scroll_table']['hex'])[speed]);e=b.Expected(segs)
                        for w in scroll_writes(initial,dims,0,amount,(p[13]&15)*17):e.write(*w)
                        e.write(at+31,1,remaining-amount);e.resource(slot,2)
                        cases.run(str((group,f['selector'],speed,remaining)),f['callback'],segs,(at,),e.writes,3)
        elif group in('cursor','erase','cursor_state','stack_residue'):
            if group=='cursor':specs=[(2,0,style,frame,cursor,13,0xa5a5a5a5)for style in(0,1)for frame in range(4)for cursor in POSITIONS]
            elif group=='erase':specs=[(2,0,0,0,cursor,color,0x5a5a5a5a)for cursor in POSITIONS for color in(0,5,15)]
            elif group=='cursor_state':specs=[(font,state,style,frame,cursor,13,0xa5a5a5a5)for font in(2,4,5)
                for state in(2,3)for style in(0,1)for frame in range(4)for cursor in((0,0),(1,1),(23,23))]
            else:specs=[(2,0,0,0,(1,1),5,value)for value in(0,0xffffffff,*(1<<i for i in range(32)))]
            for index,(font,state,style,frame,cursor,color,residue)in enumerate(specs):
                dims=(3,3);slot=31 if cursor==(23,23)else 0
                occupied=tuple(range(128))if cursor==(24,24)or(group=='cursor_state'and cursor==(23,23))else(127,)
                at,p,segs,initial=output_fixture(a,attr,font=font,state=state,style=style,frame=frame,cursor=cursor,slot=slot,occupied=occupied,color=color)
                erase=group=='erase';e=cursor_expected(a,segs,at,p,initial,dims,cursor,style,frame,erase)
                entry=ERASE if erase else CURSOR;offset=48 if erase else 72;value=None
                if group=='cursor_state':
                    entry=next(f['callback']for f in a['selected_fonts']if f['selector']==font);offset=100;value=3
                cases.run(str((group,index)),entry,segs,(at,),e.writes,value,residues=((offset,residue),))
        elif group=='boundaries':
            for erase,entry,offset in((False,CURSOR,72),(True,ERASE,48)):
                at,p,segs,initial=output_fixture(a,attr)
                pc=0x08004390;address=b.vm.SP-offset
                cases.run('boundary-stack-'+str(erase),entry,segs,(at,),stop=('未map read',pc),
                    fault={'address':address,'size':4,'site':pc})
            # queue/既存color処理への帰還を仮定せず、不足pixelは書込前の実readで停止する。
            at,p,segs,initial=output_fixture(a,attr)
            segs=[row for row in segs if row[0]!=PIXELS]
            pc=0x08004ce6
            cases.run('boundary-pixel',CURSOR,segs,(at,),stop=('未map read',pc),
                fault={'address':PIXELS,'size':1,'site':pc},residues=((72,0),))
        counts[group]=len(cases.rows)-before
    return cases,counts


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR)
    saved.bindings_fresh(s.ROOT,r['source_bindings']);validate_inputs(nodes,r['analysis'],context)
    return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();return contracts(nodes,s.load(PRIOR)['analysis'],context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];cases,groups=evaluated()
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table',
        'scroll_table','output_data','selected_glyphs','font_data_bases','glyph_translation','pending_direct_callees','pending_boundaries')}
    result.update({'classification':'SAVED_CURSOR_SCROLL_PIXEL_QUEUE_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'groups':groups,'cases':cases.rows,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),
        'stack_residue_contract':{'bytes':4,'allowed_offsets_from_entry_sp':list(RESIDUE_OFFSETS),
            'prefix_sites':sorted(WORD_PREFIX),'dimensions_formula':'(width*8) | (height*8 << 16)',
            'symbolic_elimination':'((u32 & 0xffff0000) | width*8) & 0xffff removes all residue bits',
            'zero_unmapped_stack_permitted':False,'initial_live_stack_universal_proven':False},
        'fill_neighbor_nibble_effect_preserved':True,'zero_step_scroll_indices':[3,4,5,6,7],
        'dma_execution_observed':False,'actual_callback_table_observed':False,'initializer_runtime_observed':False,
        'all_live_slot_bounds_proven':False,'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'有限明示RAM/旧stack1word条件でcursor/scroll/queueを結合。queue予約は実DMAではない。音声/BIOS/live caller/Ring通常取得は未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'保存cursor/scrollのpixel・queue・state2/3/4を{r["contract_cases"]}条件'
        f'（帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}）で結合。4byte旧stack条件・塗り隣接効果・零速度を明記。ROM/native0。',
        '次は保存音声calleeとBIOS境界、RunTextPrinters全出力連鎖の未結合区間。'
        '旧stack条件/queue予約と実DMAを混同せず、cursor/scroll・1122glyph・636control/627text・font/BP/nativeを単独再実行しない。'
        '実画面・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
