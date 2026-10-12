#!/usr/bin/env python3
"""状態0/1・実r8 frame・queueを明示RAMで結合。BIOS/通常storyは未受入。"""
from __future__ import annotations
import copy
import functools
import sys
import pr16_ring_message_tile_leaves as prior
import pr16_ring_message_task_contracts as task
import pr16_ring_explicit_text_machine as strict
import pr16_ring_resource_contracts as resource
import pr16_ring_followup_v2 as s
import pr16_ring_text_export_recovery as export

BASE='3918caabe8ad1dd4cf9c45adae60be705649abc7'
SLUG='pr16-ring-message-window-contracts'
TASK='PR-P08-7-RING-MESSAGE-WINDOW-CONTRACTS'
TITLE='状態0の条件付き進行・実r8 frame書込とBIOS停止を結合'
SELF='scripts/pr16_ring_message_window_contracts.py'
TEST='tests/test_pr16_ring_message_window_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-message-window-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_message_window_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,prior.PRIOR,*prior.SOURCES,task.SELF,strict.SELF,resource.SELF)))
NO_REPEAT=('属性0・mode2状態0進行・frame矩形書込・BIOS停止の今回結合原本を再利用。'
    'queue失敗でもstate1に進むことを描画成功へ昇格しない。BIOS0B/0Cの保存prefixも再採取不要。'
    '今回/旧68命令/280命令/29命令/1231条件/391条件/BP/nativeは単独再実行しない。')
need=s.need
b=task.b
GETTER,FRAME,FRAME_CALLBACK,PALETTE=0x0800491d,0x08004839,0x080f8185,0x0806fb91
TABLE,SELECTOR=0x08004938,0x03000fa1
PIXELS,TILEMAP=0x02024000,0x02028000
BIOS_COPY,BIOS_FILL=0x081c7a88,0x081c7a84
PALETTE_BUFFER=0x0203712c
EXPECTED_GROUPS={'attribute-byte':256,'attribute-id':48,'attribute-short':10,'frame-ram':93,
    'frame-short':13,'palette-bios':48,'state0-mode2':128,'state0-palette':20,'state0-short':14,
    'state01-sequence':9,'state1-short':4,'tile-index':32,'tile-leaf-short':19,'tile-value':30}


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    c=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    return dict(c,nodes=[*c['nodes'],*r['analysis']['new_nodes']],tile_leaves=r['analysis'])


def validate_inputs(c):
    by={n['address']:n for n in c['nodes']};a=c['tile_leaves']
    need(len(by)==len(c['nodes'])==8628,'保存8628命令')
    need(a['candidate']==s.CANDIDATE and a['new_node_count']==68 and a['new_window_bytes']==144,'2leaf出自')
    need(not a['pending_direct_callees'] and not a['pending_continuations'],'2leaf閉包')
    for k in prior.FALSE:need(a[k] is False,'未受入境界 '+k)
    need(c['window_frontier']['selector0']['hex']=='58490008','属性0word')
    for at,raw in {0x08004930:'0068',0x08004962:'0878',0x081c7ae8:'4047',
        0x0800280c:'1c40',0x08002810:'0140',0x08002890:'3180',0x08068c6e:'1070',
        0x08068ca6:'2881',0x080f7f5c:'0cf764fa',0x08004462:'c3f10ffb'}.items():
        need(by[at]['hex']==raw,'状態/矩形/BIOS caller byte '+hex(at))
    for key,start,raw in (('bios_prefix',BIOS_FILL,'0cdf7047'),('audio_bios_prefix',BIOS_COPY,'0bdf7047')):
        p=c['analysis'][key];data=bytes.fromhex(raw)
        need(p['start']==start and p['hex']==raw and p['identity']==s.identity(data)
            and p['executed'] is False and p['return_proven'] is False,'保存BIOS境界 '+key)
        need(start not in by,'BIOSを実行nodeにしない')
    need(c['task_contracts']['contract_cases']==1231 and c['task_contracts']['same_ram_state2_sequences']==96,'旧原本保持')
    full=c['task_contracts']['task_full_boundary']
    need(full['busy_after']==2 and full['task_allocated'] is False and full['liveness_proven'] is False
        and full['normal_play_reproduction_observed'] is False,'task満杯境界保持')
    return by


def uint(value,bits):
    need(type(value)is int and 0<=value<1<<bits,'unsigned引数');return value


def palette_request(source,offset,length):
    return [uint(source,32),PALETTE_BUFFER+2*(uint(offset,32)&65535),(uint(length,32)&65535)//2]


def tile_index(x,y,shape):
    uint(x,32);uint(y,32);need(type(shape)is int and 0<=shape<4,'text shape')
    cols=(32,64,32,64)[shape];rows=(32,32,64,64)[shape];x&=cols-1;y&=rows-1
    return ((y//32)*(cols//32)+x//32)*1024+(y%32)*32+x%32


def tile_value(source,destination,palette,offset,palette_offset):
    uint(source,16);uint(destination,16)
    for v in (palette,offset,palette_offset):uint(v,32)
    signed=palette if palette<0x80000000 else palette-0x100000000
    if 0<=signed<16:return (((source+offset)&4095)+((palette+palette_offset)<<12))&65535
    if signed==16:return (((source+offset)&1023)|((destination&0xfc00)+(palette_offset<<12)))&65535
    return (source+offset+(palette_offset<<12))&65535


def rectangles(left,top,width,alternate=False):
    for v in (left,top,width):uint(v,8)
    need(type(alternate)is bool,'frame variant')
    x=[(left-2)&255,(left-1)&255,left,(left+width)&255,(left+width+1)&255]
    rows=[(0x200,0x201,0x202,0x203,0x204),(0x205,0x206,0x208,0x209),
          (0x20a,0x20b,0x20c,0x20d)]
    middle=[(0xa0a,0xa0b,0xa0c,0xa0d),(0xa05,0xa06,0xa08,0xa09)]
    rows+=middle[::-1] if alternate else middle
    rows.append((0xa00,0xa01,0xa02,0xa03,0xa04));out=[]
    for dy,values in enumerate(rows):
        for column,tile in zip(range(5) if len(values)==5 else (0,1,3,4),values):
            out.append((tile,x[column],(top-1+dy)&255,width if column==2 else 1,1,15))
    return out


def kind(bg,display):
    display&=7
    if bg in (0,1):return 0 if display in (0,1)else -1
    if bg==2:return 0 if display==0 else 1 if display in (1,2)else -1
    if bg==3:return 0 if display==0 else 1 if display==2 else -1
    return -1


def fixture(c,*,task_id=0,state=0,bg=0,shape=0,display=0,left=3,top=5,width=27,height=4,
            mode=2,selector=0,window_id=0,flags=1,bank=0,head=0,occupied=(),enabled=0,
            context_base=0,flag_word=0x12345601,pointer=TILEMAP):
    need(type(shape)is int and 0<=shape<4,'fixture shape')
    need(0<=width<=64 and 0<=height<=8,'有界window寸法')
    table=next(t for t in c['inherited_analysis']['tables']if t.get('start')==resource.TABLE)
    raw=bytes.fromhex(table['hex']);need(len(raw)==32,'保存背景属性表')
    f=resource.fixture(raw,channel=bg,flags=bytes([flags|shape<<2,bank]),display=display,slot=window_id,
        dims=(width,height),offset=9,pointer=pointer,source=PIXELS,head=head,occupied=occupied,
        enabled=enabled,context_base=context_base)
    rec=bytes((bg,left,top,width,height,7,9,0))+b.word(PIXELS)
    seg=[(at,rec if at==b.WINDOWS+window_id*12 else data,w)for at,data,w in f['segments']]
    extent=(2048*(1,2,2,4)[shape]if kind(bg,display)==0 else (256*4**shape if kind(bg,display)==1 else 0))
    seg += [(TABLE,bytes.fromhex(c['window_frontier']['selector0']['hex']),False),
        (task.tasks.TASKS,task.task_fixture(task_id,state),True),(task.MODE,bytes([mode]),False),
        (SELECTOR,bytes([selector]),False),(task.WINDOW_FLAGS,b.word(flag_word),True),
        (PIXELS,b'\x77'*(width*height*32),True)]
    if pointer==TILEMAP:seg.append((TILEMAP,b'\xcc'*extent,True))
    return seg


def frame_writes(seg,*,bg=0,shape=0,display=0,left=3,top=5,width=27,mode=2,selector=0,pointer=TILEMAP):
    e=b.Expected(seg);rect=rectangles(left,top,width,selector==1 and mode!=2)
    if kind(bg,display)<0 or pointer==0 or pointer>0x03008000:return e.writes
    for tile,x,y,w,h,palette in rect:
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                if kind(bg,display)==0:e.write(pointer+2*tile_index(xx,yy,shape),2,tile_value(tile,0,palette,0,0))
                else:e.write(pointer+yy*(16<<shape)+xx,1,tile&255)
    return e.writes


def check_frame_calls(m,*,bg=0,left=3,top=5,width=27,mode=2,selector=0):
    rect=rectangles(left,top,width,selector==1 and mode!=2)
    got=[r['args']for r in m.call_arguments if r['target']==0x08002555]
    need(got==[[bg,tile,x,y]for tile,x,y,_,_,_ in rect],'26矩形の実call順序')
    need({0x081c7ae8,0x080f8184,0x080f868c}<=m.executed_sites,'実r8 callbackと帰還')


def getter_cases(cases,c):
    word=(TABLE,bytes.fromhex(c['window_frontier']['selector0']['hex']),False)
    for bg in range(256):
        seg=[word,(b.WINDOWS,b.template(bg),False)]
        cases.run('attribute-bg-'+str(bg),GETTER,seg,(0,0),value=bg,group='attribute-byte')
    for index in (0,1,15,31):
        pool=b''.join(b.template(bg=i)+b.word(PIXELS)for i in range(32))
        for upper in (0,0x100,0x123400,0xffffff00):
            for selector in (0,0x100,0xffffff00):
                cases.run(f'attribute-id-{index}-{upper}-{selector}',GETTER,[word,(b.WINDOWS,pool,False)],
                    (index|upper,selector),value=index,group='attribute-id')
    for size in range(4):
        cases.run('attribute-word-short-'+str(size),GETTER,[(TABLE,word[1][:size],False)],(0,0),
            stop=('未map read',0x08004930),fault=dict(address=TABLE,size=4,site=0x08004930),group='attribute-short')
    for index in (0,31,32,255):
        length=index*12 if index<32 else 384
        cases.run('attribute-record-short-'+str(index),GETTER,[word,(b.WINDOWS,bytes(length),False)],(index,0),
            stop=('未map read',0x08004962),fault=dict(address=b.WINDOWS+12*index,size=1,site=0x08004962),group='attribute-short')
    for selector in (1,7):
        cases.run('attribute-other-selector-'+str(selector),GETTER,[word],(0,selector),
            stop=('未map read',0x08004930),fault=dict(address=TABLE+4*selector,size=4,site=0x08004930),group='attribute-short')


def palette_cases(cases,c):
    for offset in (0,224,511,65535,65536,0xffffffff):
        for length in (0,1,2,20,31,65535,65536,0xffffffff):
            m=cases.run(f'palette-{offset}-{length}',PALETTE,[],(0x083e30ac,offset,length),
                stop=('保存node境界で停止',BIOS_COPY),group='palette-bios')
            need(m.r[:3]==palette_request(0x083e30ac,offset,length),'palette半word数/offset切捨て')
            cases.rows[-1].update(bios_service=11,bios_executed=False,bios_arguments=m.r[:3])
    for mode in (0,1,3,127,255):
        for selector in (0,1,2,255):
            seg=[(task.tasks.TASKS,task.task_fixture(0,0),True),(task.MODE,bytes([mode]),False),(SELECTOR,bytes([selector]),False)]
            m=cases.run(f'state0-palette-{mode}-{selector}',task.CALLBACK,seg,(0,),
                stop=('保存node境界で停止',BIOS_COPY),group='state0-palette')
            need(m.r[:3]==palette_request(0x083e30ac,224,20),'state0 palette供給')
            need(m.data(task.tasks.TASKS+8,2)==b'\0\0','BIOS前state保持')
            need((0x080f8a05 if selector==1 else 0x080f7efd)in [r['target']for r in m.call_arguments],'state0分岐')
            cases.rows[-1].update(task_state_after=0,bios_service=11,bios_executed=False,bios_arguments=m.r[:3])


PATTERNS=(('free',{}),('wrap',dict(head=127,occupied=(127,))),('full',dict(occupied=tuple(range(128)))),
    ('disabled',dict(flags=0)),('bitmap',dict(enabled=1)),('color256',dict(bank=128)),
    ('bank1',dict(bank=1)),('base1023',dict(context_base=1023)))


def state0_cases(cases,c):
    sequences=[]
    for task_id in range(16):
        for label,options in PATTERNS:
            kw=dict(task_id=task_id,bg=task_id%4,flag_word=0x12345600|task_id*17,**options)
            seg=fixture(c,**kw);e=b.Expected(seg);e.write(task.WINDOW_FLAGS,1,(task_id*17)|4)
            reserve=e.tiles(kw['bg'],0x0843f7a4,640,512);e.write(task.tasks.TASKS+40*task_id+8,2,1)
            m=cases.run(f'state0-mode2-{task_id}-{label}',task.CALLBACK,seg,(task_id,),e.writes,b.vm.RETURN,group='state0-mode2')
            need(m.data(task.tasks.TASKS+40*task_id+8,2)==b'\1\0','mode2 state1')
            need(not any(r['target']==PALETTE for r in m.call_arguments),'mode2 palette非依存')
            cases.rows[-1].update(task_state_after=1,queue_index=reserve,queue_reserved=reserve!=65535,
                graphics_success_claimed=False,dma_execution_observed=False)
            if task_id in (0,7,15) and label in ('free','wrap','full'):
                nextseg=task.producer.snapshot(seg,m)
                writes=frame_writes(nextseg,bg=kw['bg'])
                n=cases.run(f'state01-same-ram-{task_id}-{label}',task.CALLBACK,nextseg,(task_id,),writes,
                    stop=('保存node境界で停止',BIOS_FILL),group='state01-sequence')
                check_frame_calls(n,bg=kw['bg'])
                need(n.data(task.tasks.TASKS+40*task_id+8,2)==b'\1\0','fill未完state保持')
                need(n.r[1:3]==[PIXELS,0x01000000|27*4*8] and n.read(n.r[0],4)==0x11111111,'fill ABI')
                sequences.append({'task_id':task_id,'queue_pattern':label,'state0_case':f'state0-mode2-{task_id}-{label}',
                    'state1_case':f'state01-same-ram-{task_id}-{label}','states':[0,1,1],'host_writes_between_calls':0,
                    'queue_reserved':reserve!=65535,'frame_ram_write_count':len(writes),'bios_service':12,
                    'bios_executed':False,'whole_state01_completed':False})
    return sequences


def frame_cases(cases,c):
    vectors=[]
    for bg in range(4):
        for shape in range(4):
            for mode,selector in ((0,0),(0,1),(2,1),(255,255)):
                vectors.append(dict(bg=bg,shape=shape,mode=mode,selector=selector))
    for bg,display in ((2,1),(3,2)):
        for shape in range(4):
            for selector in (0,1):vectors.append(dict(bg=bg,display=display,shape=shape,width=8,mode=0,selector=selector))
    for shape in range(4):
        vectors.append(dict(shape=shape,left=31,top=31,width=2,window_id=31))
        vectors.append(dict(shape=shape,left=0,top=0,width=0,height=0))
    vectors+= [dict(bg=4),dict(pointer=0),dict(display=7),dict(height=0),dict(height=8)]
    for i,kw in enumerate(vectors):
        seg=fixture(c,**kw);params={k:v for k,v in kw.items()if k in ('bg','shape','display','left','top','width','mode','selector','pointer')}
        writes=frame_writes(seg,**params)
        m=cases.run('frame-'+str(i),FRAME,seg,(kw.get('window_id',0),FRAME_CALLBACK),writes,b.vm.RETURN,group='frame-ram')
        check_frame_calls(m,**{k:v for k,v in kw.items()if k in ('bg','left','top','width','mode','selector')})
        cases.rows[-1].update(parameters=kw,frame_callback_execution_proven=True,frame_rectangle_calls=26,
            frame_ram_write_count=len(writes),hardware_frame_observed=False)


def readonly(segments,at):
    need(sum(p==at for p,_,_ in segments)==1,'readonly対象')
    return [(p,data,False if p==at else writable)for p,data,writable in segments]


def protect_byte(segments,address):
    """一byteだけをreadonlyに分離する。map値を追加・消去しない。"""
    out=[];found=0
    for at,data,writable in segments:
        if at<=address<at+len(data):
            i=address-at;found+=1
            out.extend(((at,data[:i],writable),(address,data[i:i+1],False),(address+1,data[i+1:],writable)))
        else:out.append((at,data,writable))
    need(found==1,'保護byteの一意owner');return out


def leaf_cases(cases,c):
    src,dst=0x02001000,0x02001010
    for shape in range(4):
        width=(32,64,32,64)[shape];height=(32,32,64,64)[shape]
        for i,(x,y)in enumerate(((0,0),(31,31),(32,32),(63,63),(64,64),(255,255),(0xffffffff,0xffffffff),(123,456))):
            cases.run(f'tile-index-{shape}-{i}',0x08002805,[(b.vm.SP,b.word(height),False)],
                (x,y,shape,width),value=tile_index(x,y,shape),group='tile-index')
    values=((0,0,0,0),(65535,0xfc00,1,1),(0xabc,65535,1024,15),
        (0x1234,0xabcd,0xffffffff,0xffffffff),(0x3ff,0x1234,0x7fffffff,0x80000000))
    for palette in (0,15,16,17,0x80000000,0xffffffff):
        for i,(source,destination,offset,palette_offset)in enumerate(values):
            seg=[(src,source.to_bytes(2,'little'),False),(dst,destination.to_bytes(2,'little'),True),
                 (b.vm.SP,b.word(palette_offset),False)]
            value=tile_value(source,destination,palette,offset,palette_offset)
            cases.run(f'tile-value-{palette}-{i}',0x0800283d,seg,(src,dst,palette,offset),
                [(dst,2,value)],b.vm.RETURN,group='tile-value')
    for entry,site in ((0x08002805,0x08002808),(0x0800283d,0x08002842)):
        for size in range(4):
            cases.run(f'tile-arg-short-{entry}-{size}',entry,[(b.vm.SP,b.word(32)[:size],False)],
                (0,0,0,32),stop=('未map read',site),fault=dict(address=b.vm.SP,size=4,site=site),group='tile-leaf-short')
    for palette,site in ((0,0x08002850),(16,0x08002870),(17,0x08002884)):
        seg=[(src,b'\x34\x12',False),(dst,b'\xcd\xab',True),(b.vm.SP,b.word(0),False)]
        for size in (0,1):
            cases.run(f'tile-source-short-{palette}-{size}',0x0800283d,task.trim(seg,src,size),(src,dst,palette,0),
                stop=('未map read',site),fault=dict(address=src,size=2,site=site),group='tile-leaf-short')
        cases.run(f'tile-destination-readonly-{palette}',0x0800283d,readonly(seg,dst),(src,dst,palette,0),
            stop=('未許可 write',0x08002890),group='tile-leaf-short')
    for size in (0,1):
        cases.run(f'tile-destination-short-{size}',0x0800283d,task.trim(seg,dst,size),(src,dst,16,0),
            stop=('未map read',0x08002864),fault=dict(address=dst,size=2,site=0x08002864),group='tile-leaf-short')


def state0_short_cases(cases,c):
    base=fixture(c);e=b.Expected(base);e.write(task.WINDOW_FLAGS,1,5)
    e.tiles(0,0x0843f7a4,640,512);e.write(task.tasks.TASKS+8,2,1)
    need(len(e.writes)==9,'予約write独立モデル')
    # prefix長は保存caller/queueの命令順による。実traceから生成しない。
    vectors=[('mode',task.MODE,0,0,0x08068c60,task.MODE,1),
        ('flags',task.WINDOW_FLAGS,0,0,0x08068c68,task.WINDOW_FLAGS,1),
        ('table',TABLE,3,1,0x08004930,TABLE,4),
        ('window',b.WINDOWS,0,1,0x08004962,b.WINDOWS,1),
        ('head',resource.HEAD,0,2,0x08000ecc,resource.HEAD,1),
        ('queue-size',resource.QBASE,9,2,0x08000eda,resource.QBASE+8,2),
        ('mask',resource.MASK,3,7,0x08001854,resource.MASK,4),
        ('enable',resource.ENABLE,3,8,0x0800185c,resource.ENABLE,4)]
    for label,at,size,count,site,fault_at,fault_size in vectors:
        m=cases.run('state0-short-'+label,task.CALLBACK,task.trim(base,at,size),(0,),e.writes[:count],
            stop=('未map read',site),fault=dict(address=fault_at,size=fault_size,site=site),group='state0-short')
        need(m.data(task.tasks.TASKS+8,2)==b'\0\0','不足時state0保持')
        cases.rows[-1].update(task_state_after=0,partial_write_count=count,normal_play_reproduction_observed=False)
    for label,at,count,site in (('window-flags',task.WINDOW_FLAGS,0,0x08068c6e),
        ('lock',resource.LOCK,1,0x08000ec8),('queue',resource.QBASE,2,0x08000ee2),
        ('mask',resource.MASK,7,0x08001858),('task',task.tasks.TASKS,8,0x08068ca6)):
        m=cases.run('state0-readonly-'+label,task.CALLBACK,readonly(base,at),(0,),e.writes[:count],
            stop=('未許可 write',site),group='state0-short')
        need(m.data(task.tasks.TASKS+8,2)==b'\0\0','readonly失敗時state0保持')
        cases.rows[-1].update(task_state_after=0,partial_write_count=count,normal_play_reproduction_observed=False)
    m=cases.run('state0-short-queue-mode',task.CALLBACK,task.trim(base,resource.QBASE,10),(0,),e.writes[:5],
        stop=('未許可 write',0x08000f06),group='state0-short')
    need(m.data(resource.LOCK,1)==b'\1' and m.data(task.tasks.TASKS+8,2)==b'\0\0','部分予約/lock保持')
    cases.rows[-1].update(task_state_after=0,partial_write_count=5,queue_lock_after=1,normal_play_reproduction_observed=False)


def frame_short_cases(cases,c):
    base=fixture(c);writes=frame_writes(base)
    for size in range(8):
        site,at=(0x08004850,b.WINDOWS)if size<4 else(0x08004852,b.WINDOWS+4)
        cases.run('frame-window-short-'+str(size),FRAME,task.trim(base,b.WINDOWS,size),(0,FRAME_CALLBACK),
            stop=('未map read',site),fault=dict(address=at,size=4,site=site),group='frame-short')
    for index in (0,1,28,50,77):
        address=writes[index][0]+1
        need(all(not at<=address<at+size for at,size,_ in writes[:index]),'初回保護byte')
        cases.run('frame-protected-'+str(index),FRAME,protect_byte(base,address),(0,FRAME_CALLBACK),writes[:index],
            stop=('未許可 write',0x08002890),group='frame-short')
        cases.rows[-1].update(partial_frame_writes=index,frame_completion_claimed=False,protected_byte=address)
    # 状態1入口は明示fixture。state0を実行した連続列とは区別する。
    full=fixture(c,state=1);writes=frame_writes(full)
    for size in range(8,12):
        m=cases.run('state1-pixel-pointer-short-'+str(size),task.CALLBACK,task.trim(full,b.WINDOWS,size),(0,),writes,
            stop=('未map read',0x08004456),fault=dict(address=b.WINDOWS+8,size=4,site=0x08004456),group='state1-short')
        check_frame_calls(m);need(m.data(task.tasks.TASKS+8,2)==b'\1\0','frame後state1保持')
        cases.rows[-1].update(initial_task_state=1,state0_execution_claimed=False,task_state_after=1,partial_frame_writes=len(writes))


@functools.lru_cache(maxsize=1)
def evaluated():
    c=saved_inputs();validate_inputs(c);cases=task.Cases(c['nodes'])
    getter_cases(cases,c);palette_cases(cases,c);sequences=state0_cases(cases,c);frame_cases(cases,c)
    leaf_cases(cases,c);state0_short_cases(cases,c);frame_short_cases(cases,c)
    groups={k:sum(r['group']==k for r in cases.rows)for k in sorted({r['group']for r in cases.rows})}
    return {'cases':cases.rows,'groups':groups,'sequences':sequences,'sites':sorted(cases.sites)}


def build_result(c,result):
    validate_inputs(c);rows=result['cases'];returned=sum(r['returned']for r in rows)
    by={r['case']:r for r in rows}
    need(len(by)==len(rows)==724 and returned==587 and len(result['sequences'])==9,'case/連続列')
    groups={k:sum(r['group']==k for r in rows)for k in EXPECTED_GROUPS}
    need(groups==result['groups']==EXPECTED_GROUPS,'case group集合')
    need(all((r['stop'] is None)==r['returned'] and r['return_sp_r4_r11_proven']==r['returned']
        and r['native_observation'] is False and r['successful_callee_stubs']==0 for r in rows),'帰還/停止/非native境界')
    pairs=set()
    for seq in result['sequences']:
        key=(seq['task_id'],seq['queue_pattern']);need(key not in pairs,'連続列重複');pairs.add(key)
        first,second=by.get(seq['state0_case']),by.get(seq['state1_case'])
        need(first is not None and second is not None and first['group']=='state0-mode2'
            and second['group']=='state01-sequence' and first['returned'] and not second['returned']
            and first['task_state_after']==1 and seq['states']==[0,1,1]
            and seq['host_writes_between_calls']==0 and seq['whole_state01_completed'] is False
            and seq['bios_executed'] is False and second['stop']==['保存node境界で停止',BIOS_FILL], '同一RAM列境界')
    need(pairs=={(t,p)for t in (0,7,15)for p in ('free','wrap','full')},'連続列domain')
    for row in rows:
        if row['group']=='state0-mode2':
            need(row['task_state_after']==1 and row['graphics_success_claimed'] is False
                and row['dma_execution_observed'] is False,'state0を描画受入に昇格しない')
            if row['case'].endswith(('-full','-disabled')):need(row['queue_reserved'] is False,'queue失敗境界')
    return {'classification':'WINDOW_STATE0_PROGRESS_FRAME_RAM_AND_BIOS_STOPS_NOT_NATIVE_ACCEPTANCE',
        'candidate':dict(s.CANDIDATE),'saved_node_count':8628,'new_node_count':0,'new_window_bytes':0,
        'contract_cases':len(rows),'conditional_return_cases':returned,'pending_stop_cases':len(rows)-returned,
        'groups':result['groups'],'same_ram_state01_sequences':len(result['sequences']),
        'mode2_state0_to1_conditional_proven':True,'r8_frame_callback_conditional_proven':True,
        'frame_rectangle_count':26,'state0_progress_on_queue_failure':True,
        'missing_readonly_and_partial_write_cases':60,'tile_leaf_return_cases':62,
        'queue_reservation_is_dma_completion':False,'queue_failure_is_graphics_success':False,
        'palette_pre_bios_arguments_proven':True,'palette_copy_effects_proven':False,
        'window_fill_pre_bios_arguments_proven':True,'window_fill_effects_proven':False,
        'task_state01_complete_proven':False,'task_state_transitions_proven':False,
        'task_state1_to2_proven':False,'task_runtime_observed':False,'task_scheduler_execution_observed':False,
        'normal_story_observed':False,'initializer_runtime_observed':False,'actual_callback_table_observed':False,
        'bios_execution_observed':False,'dma_execution_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'task_full_boundary':copy.deepcopy(c['task_contracts']['task_full_boundary']),
        'pending_bios':[{'entry':BIOS_COPY|1,'service':11,'saved_prefix':c['analysis']['audio_bios_prefix'],
            'source_for_state0':0x083e30ac,'destination_for_state0':PALETTE_BUFFER+448,'halfwords_for_state0':10,
            'second_palette_destination':0x0203752c+448,'second_copy_reached':False},
            {'entry':BIOS_FILL|1,'service':12,'saved_prefix':c['analysis']['bios_prefix'],
             'fill_word':0x11111111,'fixture_destination':PIXELS,'fixture_control':0x01000000|27*4*8}],
        'remaining_window_attribute_selectors_unproven':[1,2,3,4,5,6,7],
        'bios_prefix_resampling_needed':False,'successful_callee_stubs':0,'implicit_ram_or_stack_values':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'saved_nodes_redecoded':0,
        'accepted_native_cases_replayed':0,'accepted_standalone_contracts_replayed':0,'full_rom_scans':0,
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in rows),'cases':rows,
        'state01_sequences':result['sequences'],'executed_saved_sites':result['sites'],
        'boundary_ja':'明示RAM条件のstate0進行とframe帰還。state1はframe書込後の既存BIOS0Cで停止。'
            'queue満杯/無効でもstate1に進むため、状態進行を資源供給/描画成功と同一視しない。通常story/Ring/nativeは未受入。'}


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    c=saved_inputs();result=build_result(c,evaluated())
    need(evaluated.cache_info().misses==1,'新規結合の二重実行禁止')
    result['evaluation_cache_misses']=evaluated.cache_info().misses
    files=exporter.source_export((SELF,TEST,*SOURCES,s.SELF,export.SELF))
    compact={k:v for k,v in result.items()if k not in ('cases','state01_sequences','executed_saved_sites')}
    files['saved-context.json']=s.stable(dict(c,window_contracts=compact))
    manifest=export.bundle(files,out/'export');result['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    result['export_logical_files']=len(manifest['files']);(out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return (f'状態0のmode2進行・属性0・26矩形の実r8 frame・BIOS停止を{r["contract_cases"]}条件と9同一RAM列で結合。新byte/native0。',
        '次は保存BIOS0B/0Cのservice境界を、成功stubではない根拠付きメモリ効果/供給元契約として限定する。'
        'palette state0はROM083E30AC→020372ECの10半word(次の020376ECは未到達)、'
        'state1はframe RAM書込後のfill0x11111111/width*height*8 wordで停止。prefix再採取は不要。'
        'queue失敗時state1進行とtask満杯busy2を保持。今回/旧採取/1231条件/BP/nativeを単独再実行せず、通常story/Ring/live初期化は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    sys.modules['pr16_ring_message_window_contracts']=sys.modules[__name__]
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
