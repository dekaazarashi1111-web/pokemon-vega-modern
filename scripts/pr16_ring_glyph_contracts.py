#!/usr/bin/env python3
"""保存字形4文字/font2・4・5とspaceを明示RAMの4bpp効果へ結合する。"""
from __future__ import annotations
import copy
import functools
import hashlib
import json
import sys
import pr16_ring_output_leaf_bytes as prior
import pr16_ring_control_contracts as control
import pr16_ring_followup_v2 as s

BASE='70ec4bc30ee0c07fc7ade308047081904afdb177'
SLUG='pr16-ring-glyph-contracts'
TASK='PR-P08-7-RING-GLYPH-CONTRACTS'
TITLE='保存字形とspaceの展開・clipping・透明pixel・通常callbackを明示RAMへ結合'
SELF='scripts/pr16_ring_glyph_contracts.py'
TEST='tests/test_pr16_ring_glyph_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-glyph-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_glyph_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=30
EXTRA_CODE=()
SOURCES=tuple(dict.fromkeys((prior.SELF,*prior.SOURCES)))
NO_REPEAT=('保存字形4文字/font2・4・5とspaceの展開、透明pixel、clipと通常callbackの明示RAM契約は本原本を再利用。'
    '全文字/live allocation/実画面の受入ではない。既読byte・636control/627text・font/BP/nativeを単独再実行しない。')
need=s.need
b=control.b
strict=control.strict
GLYPH=0x03003de0
PIXELS=0x02005000
DECODER=0x08002f5d
DRAW=0x08002fe5
ENTRIES={2:0x08006355,4:0x080064b9,5:0x0800657d}
PALETTES=((1,0,2),(7,8,9),(0,0,0),(15,15,15)) # fg,bg,shadow
POSITIONS=((0,0),(1,1),(7,7),(0,19),(19,0),(23,23),(24,24),(250,255))
GROUPS=('translation','expand','draw','callback','boundaries')


# 既存受入モデルは変更せず、今回到達した9つの保存LDMだけを限定追加する。
TRANSFERS={0x08003076:'08ca',0x0800310c:'01cb',0x080031a0:'01cb',0x08003244:'08c9',
    0x080032dc:'08ca',0x08003380:'01ca',0x08003408:'01cb',0x080034ac:'01cb',0x08003540:'01cb'}


class Machine(strict.Machine):
    def transfer_output(self,pc,error):
        need(pc in TRANSFERS and error==f'未対応保存命令 {pc:08X}','出力転送例外境界')
        n=self.nodes[pc]
        need(n['hex']==TRANSFERS[pc] and n['size']==2 and n['kind']=='ordinary','出力転送allowlist差分')
        h=int.from_bytes(bytes.fromhex(n['hex']),'little');base=(h>>8)&7;regs=[r for r in range(8)if h&(1<<r)]
        need(h&0xf800==0xc800 and regs and base not in regs,'出力LDM形式')
        at=self.r[base];need(at%4==0 and at+4*len(regs)<=0x100000000,'出力LDM範囲')
        for i,reg in enumerate(regs):self.r[reg]=self.read(at+4*i,4)
        self.r[base]=at+4*len(regs);return pc+2

    def run(self,entry,max_steps=100000):
        while True:
            try:return super().run(entry,max_steps)
            except ValueError as exc:
                pc=getattr(self,'last_pc',None)
                if pc not in TRANSFERS or str(exc)!=f'未対応保存命令 {pc:08X}':raise
                entry=self.transfer_output(pc,str(exc))|1


class Cases(strict.Cases):
    def run(self,label,entry,segments,args=(),writes=(),value=None,stop=None,fault=None):
        need(label not in {r['case']for r in self.rows},'契約label重複')
        e=b.Expected(segments)
        for w in writes:e.write(*w)
        m=Machine(self.nodes,segments,args)
        try:m.run(entry)
        except ValueError as exc:
            if stop is None:raise ValueError(f'{label}: {exc}; pc={getattr(m,"last_pc",0):08X}')from exc
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
        self.sites.update(m.executed_sites)
        self.rows.append({'case':label,'returned':stop is None,'return_value':m.r[0]if stop is None else None,
            'stop':None if stop is None else list(stop),'read_fault':m.read_fault,'steps':m.steps,
            'maximum_stack_bytes':b.vm.SP-m.low_sp,'nonstack_write_count':len(writes),
            'write_sha256':hashlib.sha256(json.dumps(list(writes),separators=(',',':')).encode()).hexdigest(),
            'final_object_sha256':e.image(),'return_sp_r4_r11_proven':stop is None,'calls':m.call_arguments})
        return m


def uint(value,bits,label):
    need(type(value)is int and 0<=value<1<<bits,label+' unsigned');return value


def translation_index(byte):
    uint(byte,8,'変換byte')
    return sum((((byte>>(2*i))&3)%3)*3**i for i in range(4))


def palette(colors):
    need(type(colors)in (tuple,list)and len(colors)==3,'3色')
    for c in colors:uint(c,4,'色')
    return colors[1],colors[0],colors[2]


def expanded_halfword(byte,colors):
    values=palette(colors);uint(byte,8,'展開byte')
    return sum(values[((byte>>(2*i))&3)%3]<<(4*(3-i))for i in range(4))


def checked_data(row):
    need(type(row)is dict and type(row.get('start'))is int and type(row.get('length'))is int,'data形式')
    data=bytes.fromhex(row['hex'])
    need(len(data)==row['length']and s.identity(data)==row['identity'],'data hash/長')
    return row['start'],data,False


def validate_inputs(nodes,a):
    need(type(nodes)is list and len(nodes)==len({n['address']for n in nodes})==7091,'保存7091命令')
    need(a['candidate']==s.CANDIDATE and a['saved_node_count']==7091,'候補/保存数')
    for key in('ring_acquisition_accepted','release_ready','actual_callback_table_observed','all_live_slot_bounds_proven'):
        need(a.get(key)is False,'受入境界 '+key)
    need([f['selector']for f in a['selected_fonts']]==[2,4,5],'font集合')
    need(a['selected_glyphs']==list(prior.prior.CHARS),'保存4文字')
    start,table,_=checked_data(a['glyph_translation'])
    need(start==prior.TABLE and len(table)==256,'変換表範囲')
    need(table==bytes(translation_index(i)for i in range(256)),'変換表の独立3進定義')
    rows=a['output_data'];spec=prior.prior.data_ranges()
    need([(r['name'],r['start'],r['length'])for r in rows]==spec,'出力窓集合')
    for row in rows:checked_data(row)
    return table


def lookup_segment(colors):
    palette(colors);data=bytearray(168)
    for at,size,value in control.lookup_writes(*colors):
        offset=at-control.LOOKUP;data[offset:offset+size]=value.to_bytes(size,'little')
    return control.LOOKUP,bytes(data),False


def glyph_model(a,font,char,colors):
    need(type(font)is int and font in ENTRIES,'限定font')
    need(type(char)is int and char in (0,*prior.prior.CHARS),'限定文字')
    palette(colors);writes=[];segments=[]
    if char==0:
        for i in range(128):writes.extend(((GLYPH+i,1,colors[1]*17),(GLYPH+128,1,10),(GLYPH+129,1,12)))
    else:
        rows={r['name']:r for r in a['output_data']}
        top=rows[f'font{font}-char{char}-left'];bottom=rows[f'font{font}-char{char}-right']
        width=rows[f'font{font}-char{char}-width'];segments=[checked_data(r)for r in(top,bottom,width)]
        for q in range(4):
            source=segments[q//2][1][(q%2)*16:(q%2+1)*16]
            for i in range(16):writes.append((GLYPH+q*32+i*2,2,expanded_halfword(source[i^1],colors)))
        writes.extend(((GLYPH+128,1,segments[2][1][0]),(GLYPH+129,1,12)))
    image=bytearray(130)
    for at,size,value in writes:image[at-GLYPH:at-GLYPH+size]=value.to_bytes(size,'little')
    return segments,writes,bytes(image)


def pixel_offset(x,y,tiles_w):
    uint(x,16,'pixel x');uint(y,16,'pixel y');uint(tiles_w,8,'tile幅')
    return ((y//8)*tiles_w+x//8)*32+(y%8)*4+(x%8)//2


def draw_writes(image,cursor,dims,initial):
    need(type(image)is bytes and len(image)==130,'字形130byte')
    need(type(initial)is bytes and len(initial)==dims[0]*dims[1]*32,'pixel buffer長')
    need(len(cursor)==len(dims)==2,'2座標')
    for value in(*cursor,*dims):uint(value,8,'座標')
    width=min(image[128],dims[0]*8-cursor[0]);height=min(image[129],dims[1]*8-cursor[1])
    need(image[128]<=16 and image[129]<=16,'字形16x16範囲')
    data=bytearray(initial);writes=[]
    # 4象限の独立pixel定義。保存命令・実traceから期待値を作らない。
    for q in range(4):
        ox,oy=(q%2)*8,(q//2)*8
        for y in range(oy,min(oy+8,height)):
            for x in range(ox,min(ox+8,width)):
                source=q*32+(y%8)*4+(x%8)//2
                color=(image[source]>>(4*(x%2)))&15
                if color==0:continue
                px,py=cursor[0]+x,cursor[1]+y;offset=pixel_offset(px,py,dims[0]);shift=(px%2)*4
                value=(data[offset]&(0xf0>>shift))|(color<<shift)
                data[offset]=value;writes.append((PIXELS+offset,1,value))
    return writes


def window_segment(slot,dims):
    uint(slot,5,'window slot')
    return b.WINDOWS+12*slot,b.template(dims=dims)+b.word(PIXELS),False


def contracts(nodes,a,context,groups=GROUPS):
    table=validate_inputs(nodes,a);cases=Cases(nodes);counts={}
    for group in groups:
        need(group in GROUPS,'契約group');before=len(cases.rows)
        if group=='translation':
            for colors in PALETTES:
                for start in range(0,256,16):
                    data=bytes(range(start,start+16));writes=[(GLYPH+2*i,2,expanded_halfword(data[i^1],colors))for i in range(16)]
                    cases.run(f'translation-{colors}-{start}',DECODER,[(b.TEMPLATE,data,False),
                        (prior.TABLE,table,False),lookup_segment(colors),(GLYPH,b'\xcc'*32,True)],(b.TEMPLATE,GLYPH),writes)
        elif group in('expand','draw','callback'):
            for font in ENTRIES:
                for char in(0,*prior.prior.CHARS):
                    for colors in PALETTES:
                        source,expanded,image=glyph_model(a,font,char,colors)
                        base=[*source,(prior.TABLE,table,False),lookup_segment(colors),(GLYPH,b'\xcc'*130,True)]
                        if group=='expand':
                            cases.run(f'expand-{font}-{char}-{colors}',ENTRIES[font],base,(char,),expanded)
                            continue
                        for cursor in POSITIONS:
                            dims=(3,3);initial=bytes((i*37+0xab)&255 for i in range(288));slot=31 if cursor==(7,7)else 0
                            drawn=draw_writes(image,cursor,dims,initial)
                            if group=='draw':
                                p=bytearray(32);p[4]=slot;p[8:10]=bytes(cursor)
                                segs=[(b.POOL,bytes(p),False),(GLYPH,image,False),window_segment(slot,dims),(PIXELS,initial,True)]
                                cases.run(f'draw-{font}-{char}-{colors}-{cursor}',DRAW,segs,(b.POOL,),drawn)
                            else:
                                at,p,segs=control.fixture(a,font=font,text=bytes([char]),cursor=cursor,slot=slot)
                                writes=control.prefix(at,p,font,subtype=False)+expanded+drawn+[(at+8,1,(cursor[0]+p[10]+image[128])&255)]
                                entry=next(f['callback']for f in a['selected_fonts']if f['selector']==font)
                                cases.run(f'callback-{font}-{char}-{colors}-{cursor}',entry,
                                    [*segs,*base,window_segment(slot,dims),(PIXELS,initial,True)],(at,),writes,0)
        elif group=='boundaries':
            # 不足入力をゼロ埋めせず、実停止siteと先行writeを原本へ残す。
            for font in ENTRIES:
                for char in(1,7,8):
                    source,expanded,image=glyph_model(a,font,char,PALETTES[0])
                    for q in range(4):
                        # 指定象限先頭byte不足。それ以前の象限は明示提供。
                        shortened=[]
                        for at,data,writable in source:
                            end=source[q//2][0]+(q%2)*16
                            if at<=end<at+len(data):data=data[:end-at]
                            shortened.append((at,data,writable))
                        pc=0x08002f7c;address=source[q//2][0]+(q%2)*16
                        cases.run(f'boundary-{font}-{char}-{q}',ENTRIES[font],
                            [*shortened,(prior.TABLE,table,False),lookup_segment(PALETTES[0]),(GLYPH,b'\xcc'*130,True)],
                            (char,),expanded[:q*16],stop=('未map read',pc),fault={'address':address,'size':2,'site':pc})
            cases.run('boundary-unmapped-translation',DECODER,[(b.TEMPLATE,bytes(16),False),(GLYPH,bytes(32),True)],
                (b.TEMPLATE,GLYPH),stop=('未map read',0x08002f82),fault={'address':prior.TABLE,'size':1,'site':0x08002f82})
            cases.run('boundary-unmapped-lookup',DECODER,[(b.TEMPLATE,bytes(16),False),(prior.TABLE,table,False),(GLYPH,bytes(32),True)],
                (b.TEMPLATE,GLYPH),stop=('未map read',0x08002f88),fault={'address':control.LOOKUP,'size':2,'site':0x08002f88})
        counts[group]=len(cases.rows)-before
    return cases,counts


@functools.lru_cache(maxsize=1)
def saved_inputs():
    import pr16_ring_flagset_continuation as saved
    import pr16_ring_branch_frontier as windows
    import pr16_ring_effective_frontier as f
    nodes,memory,context=prior.saved_inputs();r=s.load(PRIOR);saved.bindings_fresh(s.ROOT,r['source_bindings'])
    windows.add_windows(memory,r['analysis']['new_windows']);nodes=[*nodes,*r['analysis']['new_nodes']]
    f.nodes_to_memory(memory,nodes);validate_inputs(nodes,r['analysis']);return nodes,memory,context


@functools.lru_cache(maxsize=1)
def evaluated():
    nodes,_,context=saved_inputs();a=s.load(PRIOR)['analysis'];return contracts(nodes,a,context)


def analyze(previous,out):
    nodes,_,context=saved_inputs();a=previous['analysis'];validate_inputs(nodes,a);cases,groups=evaluated()
    result={k:copy.deepcopy(a[k])for k in('candidate','state_table','dispatch_tables','tables','selected_fonts','control_table',
        'scroll_table','output_data','selected_glyphs','font_data_bases','glyph_translation','pending_direct_callees','pending_boundaries')}
    result.update({'classification':'SAVED_GLYPH_AND_SPACE_EXPLICIT_RAM_PIXEL_CONTRACTS_NOT_NATIVE_ACCEPTANCE',
        'saved_node_count':len(nodes),'new_node_count':0,'new_window_bytes':0,'contract_cases':len(cases.rows),
        'conditional_return_cases':sum(r['returned']for r in cases.rows),'pending_stop_cases':sum(not r['returned']for r in cases.rows),
        'groups':groups,'cases':cases.rows,'executed_saved_sites':sorted(cases.sites),
        'maximum_stack_bytes':max(r['maximum_stack_bytes']for r in cases.rows),
        'translation_values_checked':256,'selected_characters_including_space':[0,*prior.prior.CHARS],
        'explicit_stack':{'start':strict.STACK_START,'end':strict.STACK_END},
        'actual_callback_table_observed':False,'initializer_runtime_observed':False,'all_live_slot_bounds_proven':False,
        'all_dispatch_returns_proven':False,'ring_acquisition_accepted':False,'release_ready':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'accepted_native_cases_replayed':0,
        'accepted_standalone_contracts_replayed':0,'saved_nodes_redecoded':0,'full_rom_scans':0,
        'boundary_ja':'明示3x3tile RAMだけ。字形4文字とspaceのpixel/clip/透明度・順序write。全字形/live allocation/実画面/DMA/音声/BIOS/Ringは未受入。'})
    (out/'analysis.json').write_bytes(s.stable(result));b.export_development(out)
    path=out/'development-source.json';sources=s.load(str(path.relative_to(s.ROOT)))
    for p in(*SOURCES,SELF,TEST):
        if p.endswith('.py')and(s.ROOT/p).is_file():sources[p]=(s.ROOT/p).read_text(encoding='utf-8')
    path.write_bytes(s.stable(sources));compact={k:v for k,v in result.items()if k not in('cases','executed_saved_sites')}
    (out/'saved-context.json').write_bytes(s.stable({'nodes':nodes,'analysis':compact,'inherited_analysis':context}));return result


def summaries(r):
    return(f'保存字形4文字/font2・4・5とspaceの展開・clipping・透明pixel・通常callbackを{r["contract_cases"]}条件'
        f'（帰還{r["conditional_return_cases"]}/不足停止{r["pending_stop_cases"]}）で明示RAMへ結合。候補復元/新規byte/native0。',
        '次は保存cursor/scrollの明示RAM/pixel効果と出力queueを結合。音声/BIOS・未読辺をstubにせず、'
        '字形契約・既読採取・636control/627text・font/BP/nativeを単独再実行しない。'
        '実画面/DMA・全live owner・Ring通常取得/policy/Circus/P08は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可');s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
