#!/usr/bin/env python3
"""実BG資源とheap→通常windowの連続RAM、およびsave退避の停止境界を検証する。"""
from __future__ import annotations
import functools
import json
import re
import sys
import pr16_ring_story_resource_suppliers as prior
import pr16_ring_story_resource_machine as vm
import pr16_ring_story_wait_lifecycle as life
import pr16_ring_story_dispatch_contracts as field
import pr16_ring_story_caller_frontier as archive
import pr16_ring_followup_v2 as s

BASE='9012286da73d8ce8950dd191210675fff5cb5fe0'
SLUG='pr16-ring-story-resource-contracts'
TASK='PR-P08-7-RING-STORY-RESOURCE-CONTRACTS'
TITLE='実BG供給から通常windowへの連続RAMとsave退避後の未証明境界を検証'
SELF='scripts/pr16_ring_story_resource_contracts.py'
TEST='tests/test_pr16_ring_story_resource_contracts.py'
WORKFLOW='.github/workflows/pr16-ring-story-resource-contracts.yml'
PRIOR=prior.REPORT
REPORT='content/modernization/pr16_ring_story_resource_contracts.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=40
EXTRA_CODE=(vm.SELF,)
SOURCES=(prior.SELF,vm.SELF,life.SELF,field.SELF,archive.SELF,'scripts/pr16_ring_message_task_frontier.py')
ARTIFACT=10539838603
ZIP_SHA='84178da982c33d4e34741434a85f5d5d3fc49daf9041147c65f85303b7fc6c47'
NETWORK='成功run35329291913のSHA固定exportだけ。候補復元/新規byte採取/ROM変更/native0。旧model/source-lockは不変。'
NO_REPEAT='保存実BG定数・templateからheap初期化→BG reset/config→属性→通常window→fonts setterの連続明示RAMを本原本から再利用。save3block退避後のRandom停止・callocのCpuSet未読を成功stubにしない。今回条件/旧採取/受入済BP/nativeは単独再実行禁止。次は未読save relocation/暗号化・CpuSet/画面転送・InitFieldMessageBoxの実caller供給。'
GROUPS=('memcpy','copy_faults','heap','bg_reset','attributes','pipeline','save_prefix','calloc','resource_faults')
HEAP,HEAP_SIZE=0x02000000,0x1c000
GPU,QUEUE,LOCK,IO=0x03000000,0x03000060,0x030000c0,0x04000000
BG,CTX,BUSY,BITMAP,ENABLE=0x030008d0,0x030008e8,0x03000928,0x03000938,0x03003dcc
HP,HG,WINDOWS,BUFS,RESET,FONTS=0x03000a38,0x02020004,0x02020430,0x03003e80,0x03003e70,0x03003dd0
MAP_NAME=0x0203af98
need=s.need
word=field.word


@functools.lru_cache(maxsize=3)
def payload(name):
    need(name in ('saved-context.json','jp-symbols.json','reference-sources.json'),'export allowlist')
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-resource-contracts-input.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));row=manifest['files'][name];parts=[]
        for index,part in enumerate(row['parts']):
            need(re.fullmatch(r'file-\d{4}-part-\d{4}\.json',part['path']),'chunk path')
            raw=z.read('export/'+part['path']);need(s.identity(raw)==part['identity'],'chunk identity')
            v=json.loads(raw);need(v['file']==name and v['index']==index and v['count']==len(row['parts']),'chunk sequence');parts.append(v['text'])
        raw=''.join(parts).encode();need(s.identity(raw)==row['identity'],'file identity');return json.loads(raw)


def readonly(c):
    tables=c['story_resource_suppliers']['data_tables']+c['story_resources_frontier']['templates']
    rows=[(r['address'],bytes.fromhex(r['hex']),False)for r in tables]
    x=c['inherited_analysis']['attribute_table'];rows.append((x['address'],bytes.fromhex(x['hex']),False))
    x=next(r for r in c['inherited_analysis']['tables']if r['start']==0x08001224)
    rows.extend(((x['start'],bytes.fromhex(x['hex']),False),(0x081ce040,b'\xff'+bytes(7),False)))
    return rows


def binding(c):
    a=c['story_resource_suppliers'];by={n['address']:n for n in c['nodes']}
    need(len(by)==len(c['nodes'])==10246 and a['new_node_count']==190 and a['candidate']==s.CANDIDATE,'保存node/candidate境界')
    need(not a['deferred_by_wave_limit']and not a['pending_continuations'],'前回採取未完')
    need(a['ring_acquisition_accepted']is False and a['heap_io_window_font_supply_proven']is False,'未受入境界')
    for at in vm.LDM:need(by[at]['hex']=='01cb'and by[at]['kind']=='ordinary','保存LDM byte')
    for at in vm.STM:need(by[at]['hex']=='01c1'and by[at]['kind']=='ordinary','保存STM byte')
    need(by[vm.POP]['hex']=='30bd'and by[vm.POP]['kind']=='return','保存POP byte')
    for at,target in ((0x08001070,0x081cde84),(0x080019fc,0x08001a08),(0x08055b84,0x0822d6c8),(0x080f7cc6,0x083e30d0),(0x081139f0,MAP_NAME)):
        need(by[at]['literal_value']==target,'保存resource literal')
    for r in a['data_tables']+c['story_resources_frontier']['templates']:
        need(s.identity(bytes.fromhex(r['hex']))==r['identity'],'resource identity')
    need(a['data_tables'][0]['hex']=='00000000','実BG default')
    return by


def gpu_segments(vcount=161,seed=0):
    io=bytearray(0x60);io[6:8]=vcount.to_bytes(2,'little')
    return [(GPU,bytes([seed])*96+b'\xff'*96+b'\0',True),(IO,bytes(io),True)]


def bg_segments(seed=0):
    return [(BG,bytes([seed])*0x168,True),(ENABLE,word(0),True)]


class Expected(vm.prior.b.Expected):
    """命令モデルとは別の有界構造体/heap/レジスタ期待値。DMA/BIOSを代行しない。"""
    def mask(self,at,size,clear,bits):self.write(at,size,(self.read(at,size)&~clear)|bits)
    def copy(self,dest,source,size):
        need(type(size)is int and 0<=size<=0x10000,'copy予算')
        words=size//4 if size>15 and (dest|source)&3==0 else 0
        for i in range(words):self.write(dest+4*i,4,self.read(source+4*i,4))
        for i in range(4*words,size):self.write(dest+i,1,self.read(source+i,1))
    def header(self,at,prev,nxt,size):
        for w in ((at,2,0),(at+2,2,0xa3a3),(at+4,4,size),(at+8,4,prev),(at+12,4,nxt)):self.write(*w)
    def heap_init(self,at,size):
        self.write(HP,4,at);self.write(HP+4,4,size);self.header(at,at,at,(size-16)&0xffffffff)
    def allocate(self,size):
        root=self.read(HP,4);size=(size+3)&0xfffffffc;at=root
        self.write(HG,4,root);self.write(HG+4,4,root)
        for _ in range(16):
            need(self.read(at+2,2)==0xa3a3,'heap magic')
            available=self.read(at+4,4)
            if self.read(at,2)==0 and available>=size:break
            at=self.read(at+12,4);need(at!=root,'expected heap不足は別契約');self.write(HG+4,4,at)
        else:raise ValueError('expected heap探索上限')
        if available-size>=32:
            new=at+16+size;nxt=self.read(at+12,4)
            self.write(HG+8,4,new);self.write(at,2,1);self.write(at+4,4,size)
            self.header(new,at,nxt,available-size-16);self.write(at+12,4,new)
            if nxt!=root:self.write(nxt+8,4,new)
        else:self.write(at,2,1)
        return at+16
    def gpu(self,offset,value):
        offset&=255;value&=65535
        if offset>95:return
        self.write(GPU+offset,2,value)
        v=self.read(IO+6,2)&255
        if ((v-161)&65535)<=64 or self.read(IO,2)&128:
            if offset==4:
                self.mask(IO+4,2,0x18,0);self.mask(IO+4,2,0,value)
            else:self.write(IO+offset,2,value)
        else:
            self.write(LOCK,1,1)
            for i in range(96):
                current=self.read(QUEUE+i,1)
                if current==255:break
                if current==offset:self.write(LOCK,1,0);return
            else:i=96
            self.write(QUEUE+i,1,offset);self.write(LOCK,1,0)
    def reset_bg(self,mode):
        for i in reversed(range(4)):self.write(BG+4*i,4,0)
        self.write(BG+16,2,0);self.gpu(0,self.read(GPU,2)&0xf0f8)
        for i in reversed(range(4)):self.write(BUSY+4*i,4,0)
        self.write(ENABLE,4,mode)
        for i in reversed(range(256)):self.write(BITMAP+i,1,0)
    def settings(self,bg,values):
        if bg>3:return
        for value,(offset,clear,mask,shift)in zip(values,((1,3,3,0),(1,124,31,2),(0,12,3,2),(1,128,255,7),(0,48,3,4),(0,64,1,6),(0,128,255,7))):
            if value!=255:self.mask(BG+4*bg+offset,1,clear,(value&mask)<<shift)
        self.write(BG+4*bg+2,1,0);self.write(BG+4*bg+3,1,0);self.mask(BG+4*bg,1,0,1)
    def init_bg(self,mode,table,count):
        self.mask(BG+16,2,7,mode&255)
        for i in reversed(range(4)):self.write(BG+4*i,4,0)
        for i in range(count&255):
            v=self.read(table+4*i,4);bg=v&3;char=(v>>2)&3
            self.settings(bg,(char,(v>>4)&31,(v>>9)&3,(v>>11)&1,(v>>12)&3,0,0))
            at=CTX+16*bg;self.mask(at,2,1023,(v>>14)&1023);self.mask(at+1,1,60,0);self.mask(at,4,0xffffc000,0)
            for delta in (4,8,12):self.write(at+delta,4,0)
            self.write(BITMAP+char*64,1,1)
    def attribute(self,bg,selector,value):
        selector&=255;bg&=255;value&=255
        if not 1<=selector<=7:return
        values=[255]*7;values[(0,1,2,3,5,6,4)[selector-1]]=value;self.settings(bg,values)
    def windows_prefix(self):
        for i in range(4):self.write(BUFS+4*i,4,self.read(CTX+16*i+4,4))
        for i in range(32):
            for off,val in ((0,255),(4,0),(8,0)):self.write(WINDOWS+12*i+off,4,val)
    def standard_window(self):
        need(self.read(ENABLE,4)==0,'window bitmap無効の限定条件');self.windows_prefix()
        need(self.read(BUFS,4)==0,'BG0新規buffer条件')
        tiles=self.allocate(2048)
        for i in range(2048):self.write(tiles+i,1,0)
        self.write(BUFS,4,tiles);self.write(CTX+4,4,tiles)
        pixels=self.allocate(26*4*32);self.write(WINDOWS+8,4,pixels)
        for i in (0,4):self.write(WINDOWS+i,4,self.read(0x083e30d0+i,4))
        self.write(RESET,1,0);self.write(0x0203ab58,1,255);self.write(MAP_NAME,1,255)


def fixture(c,seed,vcount):
    return readonly(c)+gpu_segments(vcount,seed)+bg_segments(seed)+[
        (HEAP,bytes([seed])*HEAP_SIZE,True),(HP,bytes([seed])*8,True),(HG,bytes([seed])*12,True),
        (WINDOWS,bytes([seed])*384,True),(BUFS,bytes([seed])*16,True),(RESET,bytes([seed])*4,True),
        (0x0203ab58,bytes([seed]),True),(MAP_NAME,bytes([seed]),True),(FONTS,bytes([seed])*4,True)]


def invoke(cases,label,entry,seg,args,model,value=None,stop=None,fault=None):
    expected=Expected(seg);model(expected)
    m=cases.run(label,entry,seg,args,expected.writes,value,stop,fault)
    return m


def pipeline(c,cases,seed,vcount):
    seg=fixture(c,seed,vcount);previous=None
    sequence=[('heap',0x08002b81,(HEAP,HEAP_SIZE),lambda e:e.heap_init(HEAP,HEAP_SIZE)),
        ('reset',0x08001619,(0,),lambda e:e.reset_bg(0)),('templates',0x08001659,(0,0x0822d6c8,4),lambda e:e.init_bg(0,0x0822d6c8,4))]
    for bg in (1,2,3):sequence.append(('mosaic'+str(bg),0x080019e5,(bg,5,1),lambda e,bg=bg:e.attribute(bg,5,1)))
    sequence.extend((('window',0x080f7cc5,(),lambda e:e.standard_window()),('fonts',0x080f8a29,(),lambda e:e.write(FONTS,4,0x083e30e8))))
    for name,entry,args,model in sequence:
        incoming=Expected(seg).image();need(previous is None or incoming==previous,'連続RAM境界')
        m=invoke(cases,f'pipeline-{seed}-{vcount}-{name}',entry,seg,args,model,value=None)
        row=cases.rows[-1];row.update(incoming_object_sha256=incoming,previous_final_object_sha256=previous,host_memory_writes_between_ticks=0)
        previous=row['final_object_sha256'];seg=life.carry_segments(seg,m)
    return seg


def contracts(c,group):
    need(group in GROUPS,'group境界');binding(c);cases=vm.Cases(c['nodes'])
    if group=='memcpy':
        for sa in range(4):
            for da in range(4):
                for size in (0,1,3,4,15,16,17,31,32,33,63):
                    src=0x02030000+sa;dst=0x02031000+da
                    seg=[(src,bytes((i*29+7)&255 for i in range(size)),False),(dst,b'\xa5'*size,True)]
                    invoke(cases,f'copy-{sa}-{da}-{size}',0x081c9d99,seg,(dst,src,size),lambda e:e.copy(dst,src,size),dst)
    elif group=='copy_faults':
        src,dst=0x02030000,0x02031000
        for label,have,writable,count,pc,reason in (('source-short',16,True,16,0x081c9dcc,'未map read'),('destination-readonly',32,False,0,0x081c9db4,'未許可 write')):
            seg=[(src,bytes(range(have)),False),(dst,b'\xa5'*32,writable)]
            invoke(cases,label,0x081c9d99,seg,(dst,src,20),lambda e:e.copy(dst,src,count),stop=(reason,pc))
    elif group=='heap':
        for size in (0,15,16,48,2048,HEAP_SIZE):
            seg=[(HP,b'\x55'*8,True),(HEAP,b'\x66'*16,True)]
            invoke(cases,'heap-'+str(size),0x08002b81,seg,(HEAP,size),lambda e:e.heap_init(HEAP,size))
    elif group=='bg_reset':
        for seed in (0,85,255):
            for vcount in (0,161):
                for mode in (0,1):
                    seg=readonly(c)+gpu_segments(vcount,seed)+bg_segments(seed)
                    invoke(cases,f'bg-reset-{seed}-{vcount}-{mode}',0x08001619,seg,(mode,),lambda e:e.reset_bg(mode))
    elif group=='attributes':
        for bg in (0,3,4):
            for selector in range(9):
                for value in (0,1,3,255):
                    seg=readonly(c)+bg_segments(0xa5)
                    invoke(cases,f'attr-{bg}-{selector}-{value}',0x080019e5,seg,(bg,selector,value),lambda e:e.attribute(bg,selector,value))
    elif group=='pipeline':
        for seed in (0x55,0xa5):
            for vcount in (0,161):pipeline(c,cases,seed,vcount)
    elif group=='save_prefix':
        for seed in (17,85):
            srcs=(0x020244e8,0x0202548c,0x0202924c);sizes=(0xf24,0x3d40,0x83d0);total=sum(sizes)
            seg=[(0x03003130,bytes([seed])*0x24,True),(0x03005048,word(srcs[1])+word(srcs[0])+word(srcs[2]),False),(HEAP,b'\xcc'*total,True)]
            seg+=[(src,bytes((i*17+seed)&255 for i in range(size)),False)for src,size in zip(srcs,sizes)]
            def expected(e):
                for off in (12,16,32):e.write(0x03003130+off,4,0)
                at=HEAP
                for src,size in zip(srcs,sizes):e.copy(at,src,size);at+=size
            for entry in (0x0804b85d,0x08055b71,0x08056599):
                objects=list(seg);args=()
                if entry==0x08056599:
                    objects += [(field.FIELD_STATE,b'\0',True),(field.FIELD_TABLE,life.field_data(c['story_field_frontier']['field_slots']),False)];args=(field.FIELD_STATE,)
                invoke(cases,f'save-prefix-{seed}-{entry:x}',entry,objects,args,expected,stop=('保存node境界で停止',0x0804448c))
    elif group=='calloc':
        for size in (0,1,3,4,0x800,0x2000):
            seg=[(HP,word(HEAP),False),(HG,b'\x55'*12,True),(HEAP,b'\xa5'*0x4000,True)]
            e=Expected(seg);e.header(HEAP,HEAP,HEAP,0x3ff0)
            seg=[(at,bytes(e.mem[at+i]for i in range(len(data))),w)for at,data,w in seg]
            invoke(cases,'calloc-bios-stop-'+str(size),0x08002bb1,seg,(size,),lambda e:e.allocate(size),stop=('保存node境界で停止',0x081c7a88))
    elif group=='resource_faults':
        seg=[(GPU,b'\x55'*2,True)]
        invoke(cases,'gpu-before-vcount-missing',0x08000a39,seg,(0,0),lambda e:e.write(GPU,2,0),stop=('未map read',0x08000a4e),fault={'address':IO+6,'size':2,'site':0x08000a4e})
        seg=readonly(c)+bg_segments(0x66)+gpu_segments()
        seg=[(at,data,False if at==BG else w)for at,data,w in seg]
        invoke(cases,'bg-readonly-default-denied',0x08001619,seg,(0,),lambda e:None,stop=('未許可 write',0x08001078))
        seg=readonly(c)+bg_segments(0x66);seg=[r for r in seg if r[0]!=0x081cde84]
        invoke(cases,'bg-default-absent',0x08001619,seg,(0,),lambda e:None,stop=('未map read',0x08001072),fault={'address':0x081cde84,'size':4,'site':0x08001072})
    return cases


@functools.lru_cache(maxsize=1)
def verified_groups():
    c=payload('saved-context.json');return {g:contracts(c,g)for g in GROUPS}


def analyze(previous,out):
    import pr16_ring_message_task_frontier as exporter
    c=payload('saved-context.json');a=previous['analysis'];binding(c)
    need(c['story_resource_suppliers']=={k:v for k,v in a.items()if k!='export_manifest'},'保存原本')
    rows=[];sites=set()
    for cases in verified_groups().values():rows+=cases.rows;sites|=cases.sites
    need(len(rows)==351,'限定case数')
    r={'classification':'EXPLICIT_RAM_BG_HEAP_STANDARD_WINDOW_PIPELINE_NOT_NORMAL_STORY_ACCEPTANCE','candidate':dict(s.CANDIDATE),
        'contract_cases':len(rows),'cases':rows,'executed_saved_sites':sorted(sites),
        'saved_node_count':len(c['nodes']),'candidate_reconstructions':0,'new_node_count':0,'new_window_bytes':0,
        'rom_changes':0,'new_emulator_processes':0,'accepted_standalone_contracts_replayed':0,'accepted_native_cases_replayed':0,
        'standard_window_pipeline_conditional':True,'pipeline_host_memory_writes_between_calls':0,
        'bg_resource_address':BG,'standard_window_template':0x083e30d0,'save_prefix_copied_bytes':0xf24+0x3d40+0x83d0,
        'save_prefix_first_unread_callee':0x0804448d,'calloc_first_unread_callee':0x081c7a89,
        'normal_field_callback_registration_proven':False,'heap_io_window_font_supply_proven':False,
        'normal_story_observed':False,'ring_acquisition_accepted':False,'release_ready':False,
        'boundary_ja':'合成明示RAM/固定VCOUNT上の独立callee連続呼出し。BG/heap/window実writeを継承するが、field全体初期化の実順序到達ではない。fonts setterの通常caller、save relocation/暗号化、CpuSet/実画面転送は未証明。'}
    files=exporter.source_export((SELF,TEST,*SOURCES))
    with archive.artifact(ARTIFACT,ZIP_SHA,'story-resource-contracts-input.zip')as z:
        manifest=json.loads(z.read('export/manifest.json'));need(s.identity(z.read('export/manifest.json'))==a['export_manifest'],'manifest原本')
        for p,raw in files.items():
            if p in manifest['files']:need(s.identity(raw)==manifest['files'][p]['identity'],'保存source差分 '+p)
    r['executed_source_bindings']={p:s.identity(raw)for p,raw in files.items()}
    files['saved-context.json']=s.stable(dict(c,story_resource_contracts=r))
    for name in('jp-symbols.json','reference-sources.json'):files[name]=s.stable(payload(name))
    archive.export.bundle(files,out/'export');r['export_manifest']=s.identity((out/'export/manifest.json').read_bytes())
    (out/'analysis.json').write_bytes(s.stable(r));return r


def summaries(r):
    return (f'実BG定数/template・heap→通常window→fonts setterの連続明示RAMとsave3block退避を{r["contract_cases"]}条件で検証。save退避{r["save_prefix_copied_bytes"]}byte後はRandom、callocはCpuSet未読で停止。候補復元/native0。',
        '保存3block退避後のRandom0804448D→save pointer relocation/暗号化、callocのCpuSet081C7A89と画面DMA/InitFieldMessageBox08068C09、通常fonts/callback登録を未読owner別に進める。今回連続RAM・旧byte/条件・BP/nativeを単独再実行しない。Ring通常取得/装備/保存、policy/Circus/P08未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runのみ');sys.modules['pr16_ring_story_resource_contracts']=sys.modules[__name__]
    import pr16_ring_bios_record as record
    record.run(sys.modules[__name__])
