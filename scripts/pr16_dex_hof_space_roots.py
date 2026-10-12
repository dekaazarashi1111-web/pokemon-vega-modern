"""新148のうち実special263を根とするHall of Fame PC命令窓1件の検証。"""
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_remaining_engine as old
import pr16_dex_hof_script_engine as previous
need,identity,chunk=d.need,d.identity,d.chunk
half,literal=old.half,old.literal
CANDIDATE=gaps.CANDIDATE
HITS=(0x080F3C3F,)
NEW_WINDOWS={'hof_pc_constructor_callback_tail':(0x080F39DA,24),'hof_pc_idle_scheduler':(0x080F2D20,26)}


def pc_scheduler(raw,review):
 s=previous.ThumbConsumer(raw)
 # CreateTask continuation initializes the buffer then installs the exact scheduler callback.
 s.pointer(0x080F39DA,4,0x080F39FC);s.imm(0x080F39DC,'mov',0,128);s.shift(0x080F39DE,False,0,0,6)
 s.call(0x080F39E0,0x08002BB0);s.mem(0x080F39E4,False,False,0,4,0);s.pointer(0x080F39E6,0,0x080F3A00);s.call(0x080F39E8,0x08000544)
 s.stack(0x080F39EC,True,16);s.stack(0x080F39EE,True,1);s.bx(0x080F39F0,0)
 s.stack(0x080F2D20,False,0,True)
 for a,t in [(0x080F2D22,0x08076D10),(0x080F2D26,0x08002DD0),(0x080F2D2A,0x080066D8),(0x080F2D2E,0x08006724),(0x080F2D32,0x0806FC74)]:s.call(a,t)
 s.stack(0x080F2D36,True,1);s.bx(0x080F2D38,0)
 w=next(w for w in review['consumer_literals']if w['label']=='hof_pc_constructor_idle_target');d.signed(raw,w)
 need(w['address']==0x080F3A00 and w['value']==d.u32(raw,0x080F3A00)==0x080F2D21,'same constructor callback and actual idle scheduler')


def task_store(raw,edge,rows,edges):
 """callback taskId由来r6を、実経路上のregister定義・ABI保存込みで追跡。"""
 need((edge['from'],edge['to'],edge['store'],edge['task_entry'],edge['task_register'],edge['index_scale'],edge['stride'],edge['table'])==(0x080F3ABA,0x080F3ACC,0x080F3ABA,0x080F3A04,6,40,40,0x030050D0),'closed same-task follow-up edge')
 need(any(e['kind']=='callback_edge'and e['callee']==0x08076BB4 and e['to']==edge['task_entry'] for e in edges),'task entry receives actual scheduler task ID')
 for k in('target_literal','table_literal'):d.signed(raw,edge[k])
 need(edge['target_literal']['address']==0x080F3AC8 and d.u32(raw,0x080F3AC8)==edge['target_literal']['value']==edge['target']==edge['to']|1,'exact typed followup callback pointer')
 need(edge['table_literal']['address']==0x080F3AC4 and d.u32(raw,0x080F3AC4)==edge['table_literal']['value']==0x030050D0,'same actual task storage')
 addresses=[r['address']for r in rows];start=addresses.index(edge['task_entry']);stop=addresses.index(edge['store']);seq=rows[start:stop+1]
 s=previous.ThumbConsumer(raw);s.shift(0x080F3A08,False,0,0,24);s.shift(0x080F3A0A,True,6,0,24)
 # Values are affine (constant, taskId coefficient), or unknown. The dispatcher supplies a valid u8 task index.
 regs=[None]*16;regs[0]=(0,1)
 def add(a,b,subtract=False):return None if a is None or b is None else(a[0]+(-b[0]if subtract else b[0]),a[1]+(-b[1]if subtract else b[1]))
 def shift(v,n,right=False):
  if v is None:return None
  if right:return(v[0]>>n,v[1]>>n)if v[0]%(1<<n)==0 and v[1]%(1<<n)==0 else None
  return(v[0]<<n,v[1]<<n)
 for p in seq:
  a=p['address'];h=half(raw,a)
  if a==edge['store']:
   need(h&0xF800==0x6000 and(h>>6)&31==0 and(h>>3)&7==1 and h&7==0,'STR r0,[r1] function field0')
   need(regs[0]==(edge['target'],0)and regs[1]==(0x030050D0,40),'same active task index times40 and literal callback value reach store')
   break
  if h&0xF800==0xF000:
   for reg in (0,1,2,3,14):regs[reg]=None
  elif h&0xF800==0x4800:regs[(h>>8)&7]=(d.u32(raw,((a+4)&~3)+(h&255)*4),0)
  elif h&0xF800 in (0,0x0800,0x1000):
   mode=(h>>11)&3;need(mode in(0,1),'arithmetic shifts are not modeled as logical shifts');v=regs[(h>>3)&7];n=(h>>6)&31
   regs[h&7]=shift(v,n or (32 if mode else 0),mode!=0)
  elif h&0xF800==0x1800:
   x=regs[(h>>3)&7];y=((h>>6)&7,0)if h&0x400 else regs[(h>>6)&7];regs[h&7]=add(x,y,bool(h&0x200))
  elif h&0xE000==0x2000:
   mode=(h>>11)&3;rd=(h>>8)&7;n=(h&255,0)
   if mode==0:regs[rd]=n
   elif mode in(2,3):regs[rd]=add(regs[rd],n,mode==3)
  elif h&0xFC00==0x4400:
   mode=(h>>8)&3;rd=(h&7)|((h>>4)&8);rs=(h>>3)&15
   if mode==0:regs[rd]=add(regs[rd],regs[rs])
   elif mode==2:regs[rd]=regs[rs]
   elif mode==3:need(False,'opaque branch forbidden in same-task value flow')
  elif h&0xFC00==0x4000:
   mode=(h>>6)&15
   if mode not in(8,10,11):regs[h&7]=None
  elif h&0xF000==0x5000:
   if(h>>9)&7>=3:regs[h&7]=None
  elif h&0xE000==0x6000 or h&0xF000==0x8000:
   if h&0x0800:regs[h&7]=None
  elif h&0xF000==0x9000:
   if h&0x0800:regs[(h>>8)&7]=None
  elif h&0xF000==0xA000:regs[(h>>8)&7]=None
  elif h&0xFE00==0xBC00:
   for r in range(8):
    if h&(1<<r):regs[r]=None
  elif h&0xF000==0xC000:
   regs[(h>>8)&7]=None
   if h&0x0800:
    for r in range(8):
     if h&(1<<r):regs[r]=None
  elif h&0xF000 in(0xD000,0xE000)or h&0xFE00==0xB400 or h&0xFF00==0xB000:pass
  else:need(False,'unhandled instruction in same-task value flow')


def indirect(raw,edge,rows,edges):
 if edge['kind']=='task_store_edge':task_store(raw,edge,rows,edges)
 else:previous.indirect(raw,edge,rows,edges)


def _regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and tuple(r['hit']['address']for r in review['rows'])==HITS,'closed one newly unknown Hall PC code window')
 need({e['local']for e in review['source_bindings'].values()}=={'BPRJ.ld','gaps-pret-scrcmd.c','pret-task.c','pret-main.c','pret-crt0.s','pret-hall_of_fame.c'},'all six pinned actual-source roles')
 by_label={w['label']:w for w in review['consumer_windows']}
 need(len(by_label)==len(review['consumer_windows'])and all(label in by_label and(by_label[label]['address'],by_label[label]['size'])==geom for label,geom in NEW_WINDOWS.items()),'complete new constructor and idle scheduler windows')
 bprj=old.sources_bind(review,sources);previous.bind_consumers(raw,review,bprj);pc_scheduler(raw,review)
 regions=[]
 for row in review['rows']:
  hit=row['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original==hit and not original['accepted']and not original['owner_candidates'],'exact inherited owner-external unknown only');d.signed(raw,hit)
  root=row['root'];entry=root['entry'];slot=root['slot'];d.signed(raw,slot)
  need(root['kind']=='special_function'and root['opcode']==37 and root['special_id']==263 and entry==0x080CB740,'exact bounded special263 root')
  need(slot['address']==0x08163068+4*263 and d.u32(raw,slot['address'])==slot['value']==entry|1,'actual special dispatch slot')
  rows=row['instruction_path'];need(rows and rows[0]['address']==entry and len(rows)<=512,'finite rooted instruction path');d.signed(raw,rows)
  addresses=[p['address']for p in rows];extra=row['typed_indirect_edges'];edges={e['from']:e for e in extra};need(len(edges)==len(extra),'unique typed outgoing edges')
  need([(e['kind'],e['from'],e['to'])for e in extra]==[('callback_edge',0x080CB75C,0x080CB708),('callback_edge',0x080CB72C,0x080F38D8),('switch_edge',0x080F38F0,0x080F39B8),('callback_edge',0x080F39D6,0x080F3A04),('task_store_edge',0x080F3ABA,0x080F3ACC)],'complete explicit Hall PC root and rewrite chain')
  need(all(a in addresses for a in [0x080F3A04,0x080F3A08,0x080F3A0A,0x080F3A28,0x080F3A44,0x080F3AB8]),'success branch reaches shared callback store with independently loaded target')
  start=0
  for i,p in enumerate(rows):
   if p['address']not in edges:continue
   edge=edges[p['address']];need(i+1<len(rows)and rows[i+1]['address']==edge['to'],'typed path adjacency')
   if edge['kind']=='switch_edge':
    need(p['size']==2 and i>start,'single complete switch Thumb instruction');gaps.thumb_path(raw,rows[start:i],rows[start]['address']);need(rows[i-1]['address']+rows[i-1]['size']==p['address'],'contiguous switch predecessor')
   else:gaps.thumb_path(raw,rows[start:i+1],rows[start]['address'])
   indirect(raw,edge,rows,extra);start=i+1
  need(start<len(rows),'nonempty code suffix');gaps.thumb_path(raw,rows[start:],rows[start]['address'])
  w=row['instruction_window'];d.signed(raw,w);selected=[p for p in rows if w['address']<=p['address']<w['address']+w['size']]
  need((w['address'],w['size'])==(0x080F3C3E,6),'only complete minimal BL and LDR crossing')
  need([(p['address'],p['size'])for p in selected]==[(0x080F3C3E,4),(0x080F3C42,2)]and d.contains(w['address'],w['address']+w['size'],hit['address'],4),'actual whole instruction window')
  need(not row['literal_pool_included']and not row['whole_function_range_classified']and not any(w['address']<=p.get('literal_address',0)<w['address']+w['size']for p in rows),'no literal or whole-function exclusion')
  regions.append(d.TypedRegion(w['address'],w['address']+w['size'],'rooted_thumb_instruction_stream',dict(root=root,instruction_window=w,instructions=[{k:p[k]for k in('address','size')}for p in selected],root_verified=True,literal_pool_included=False,path_instructions=len(rows),typed_indirect_edges=len(edges),full_story_reachability_claimed=False,full_hof_pc_lifetime_claimed=False)))
 return regions,dict(status='PASS_ONE_FINITE_HOF_PC_TASK_CODE_WINDOW',count=1,full_story_reachability_claimed=False,full_hof_pc_lifetime_claimed=False)


def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources)
