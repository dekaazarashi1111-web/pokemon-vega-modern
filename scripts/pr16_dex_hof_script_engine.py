"""実reset/special/task根から7個の最小THUMB命令窓を閉じる。"""
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_remaining_engine as previous
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
HITS=(0x080F3147,0x080FE9B3,0x08101F0D,0x08101F8B,0x0811719F,0x0813C14F,0x0813D0F7)
half,literal=previous.half,previous.literal

class ThumbConsumer:
 """意味別encoderで有限consumerの全命令とregister/control-flowを拘束。"""
 def __init__(self,raw):self.raw=raw
 def opcode(self,a,value,meaning):need(half(self.raw,a)==value,'actual consumer '+meaning)
 def shift(self,a,right,rd,rs,n):self.opcode(a,(0x0800 if right else 0)|(n<<6)|(rs<<3)|rd,'LSR'if right else'LSL')
 def imm(self,a,kind,rd,n):self.opcode(a,{'mov':0x2000,'cmp':0x2800,'add':0x3000}[kind]|(rd<<8)|n,kind+' immediate')
 def add(self,a,rd,rs,rt):self.opcode(a,0x1800|(rt<<6)|(rs<<3)|rd,'ADD registers')
 def addi(self,a,rd,rs,n):self.opcode(a,0x1C00|(n<<6)|(rs<<3)|rd,'ADD small immediate')
 def mem(self,a,load,byte,rd,rb,offset):
  need(offset%(1 if byte else 4)==0,'consumer immediate field alignment')
  self.opcode(a,0x6000|(0x0800 if load else 0)|(0x1000 if byte else 0)|((offset//(1 if byte else 4))<<6)|(rb<<3)|rd,'typed load/store field')
 def compare(self,a,rn,rm):self.opcode(a,0x4280|(rm<<3)|rn,'CMP registers')
 def stack(self,a,pop,mask,extra=False):self.opcode(a,(0xBC00 if pop else 0xB400)|(int(extra)<<8)|mask,'PUSH/POP preserved register set')
 def bx(self,a,reg):self.opcode(a,0x4700|(reg<<3),'BX exact register')
 def branch(self,a,condition,target):
  op=half(self.raw,a);need(op&0xFF00==0xD000|(condition<<8),'actual conditional branch condition')
  offset=op&255;offset=offset-256 if offset&128 else offset;need(a+4+offset*2==target,'exact conditional branch destination')
 def jump(self,a,target):
  op=half(self.raw,a);need(op&0xF800==0xE000,'actual unconditional Thumb branch')
  offset=op&2047;offset=offset-2048 if offset&1024 else offset;need(a+4+offset*2==target,'exact unconditional branch destination')
 def call(self,a,target):need(code.thumb_bl(chunk(self.raw,a,4),a)==target,'actual complete consumer BL')
 def pointer(self,a,reg,slot):need(literal(self.raw,a,reg)==slot,'consumer actual pointer literal load')

def complete_consumer_slices(raw):
 s=ThumbConsumer(raw)
 # Script-context construction, exact opcode slot computation, and r0 context/r1 function ABI.
 s.pointer(0x080693B4,4,0x080693D8);s.pointer(0x080693B6,1,0x080693DC);s.pointer(0x080693B8,2,0x080693E0);s.addi(0x080693BA,0,4,0);s.call(0x080693BC,0x0806906C)
 s.stack(0x0806906C,False,0,True);s.addi(0x0806906E,3,0,0);s.imm(0x08069070,'mov',0,0)
 for a,byte,offset in[(0x08069072,True,1),(0x08069074,False,8),(0x08069076,True,0),(0x08069078,False,4)]:s.mem(a,False,byte,0,3,offset)
 s.mem(0x0806907A,False,False,1,3,92);s.mem(0x0806907C,False,False,2,3,96)
 s.mem(0x08069118,True,True,1,2,0);s.addi(0x0806911A,0,2,1);s.mem(0x0806911C,False,False,0,4,8);s.shift(0x0806911E,False,1,1,2)
 s.mem(0x08069120,True,False,0,4,92);s.add(0x08069122,1,0,1);s.mem(0x08069124,True,False,0,4,96);s.compare(0x08069126,1,0);s.branch(0x08069128,2,0x080690F8)
 s.mem(0x0806912A,True,False,1,1,0);s.addi(0x0806912C,0,4,0);s.call(0x0806912E,0x081C7ACC)
 # The little-endian halfword reader returns the same bounded special selector in r0.
 s.addi(0x080691B8,3,0,0);s.mem(0x080691BA,True,False,2,3,8);s.mem(0x080691BC,True,True,0,2,0);s.imm(0x080691BE,'add',2,1);s.mem(0x080691C0,False,False,2,3,8)
 s.mem(0x080691C2,True,True,1,2,0);s.shift(0x080691C4,False,1,1,8);s.opcode(0x080691C6,0x4300|(1<<3)|0,'OR r0 with upper selector byte');s.imm(0x080691C8,'add',2,1);s.mem(0x080691CA,False,False,2,3,8);s.bx(0x080691CC,14)
 # Complete selector*4 + table, unsigned-end check, loaded target and immediate interwork.
 s.stack(0x080697BC,False,0,True);s.call(0x080697BE,0x080691B8);s.shift(0x080697C2,False,0,0,16);s.shift(0x080697C4,True,0,0,14)
 s.pointer(0x080697C6,1,0x080697D8);s.add(0x080697C8,1,0,1);s.pointer(0x080697CA,0,0x080697DC);s.compare(0x080697CC,1,0);s.branch(0x080697CE,2,0x080697E0)
 s.mem(0x080697D0,True,False,0,1,0);s.call(0x080697D2,0x081C7AC8);s.jump(0x080697D6,0x080697EC)
 # Main callback2 writer: argument value reaches field4 before state reset and return.
 s.pointer(0x08000544,1,0x08000554);s.mem(0x08000546,False,False,0,1,4);s.imm(0x08000548,'mov',0,135);s.shift(0x0800054A,False,0,0,3)
 s.add(0x0800054C,1,1,0);s.imm(0x0800054E,'mov',0,0);s.mem(0x08000550,False,True,0,1,0);s.bx(0x08000552,14)
 # Main callback reader, conditions and indirect calls, no untracked pointer clobber/transfer.
 s.stack(0x08000510,False,1<<4,True);s.call(0x08000512,0x080F6168);s.imm(0x08000516,'cmp',0,0);s.branch(0x08000518,1,0x0800053A)
 s.call(0x0800051A,0x0813C034);s.shift(0x0800051E,False,0,0,24);s.imm(0x08000520,'cmp',0,0);s.branch(0x08000522,1,0x0800053A)
 s.pointer(0x08000524,4,0x08000540);s.mem(0x08000526,True,False,0,4,0);s.imm(0x08000528,'cmp',0,0);s.branch(0x0800052A,0,0x08000530);s.call(0x0800052C,0x081C7AC8)
 s.mem(0x08000530,True,False,0,4,4);s.imm(0x08000532,'cmp',0,0);s.branch(0x08000534,0,0x0800053A);s.call(0x08000536,0x081C7AC8)
 s.stack(0x0800053A,True,1<<4);s.stack(0x0800053C,True,1);s.bx(0x0800053E,0)
 # CreateTask copies callback argument0 to r2, chooses a free row among16, writes func/active and returns that same row index.
 s.stack(0x08076BB4,False,0xF0,True);s.addi(0x08076BB6,2,0,0);s.shift(0x08076BB8,False,1,1,24);s.shift(0x08076BBA,True,1,1,24);s.imm(0x08076BBC,'mov',6,0);s.pointer(0x08076BBE,7,0x08076BF0)
 s.shift(0x08076BC0,False,0,6,2);s.add(0x08076BC2,0,0,6);s.shift(0x08076BC4,False,5,0,3);s.add(0x08076BC6,4,5,7)
 s.mem(0x08076BC8,True,True,0,4,4);s.imm(0x08076BCA,'cmp',0,0);s.branch(0x08076BCC,1,0x08076BF4);s.mem(0x08076BCE,False,False,2,4,0);s.mem(0x08076BD0,False,True,1,4,7)
 s.addi(0x08076BD2,0,6,0);s.call(0x08076BD4,0x08076C08);s.addi(0x08076BD8,0,7,0);s.imm(0x08076BDA,'add',0,8);s.add(0x08076BDC,0,5,0)
 s.imm(0x08076BDE,'mov',1,0);s.imm(0x08076BE0,'mov',2,32);s.call(0x08076BE2,0x081C9DF8);s.imm(0x08076BE6,'mov',0,1);s.mem(0x08076BE8,False,True,0,4,4);s.addi(0x08076BEA,0,6,0);s.jump(0x08076BEC,0x08076C00)
 s.addi(0x08076BF4,0,6,1);s.shift(0x08076BF6,False,0,0,24);s.shift(0x08076BF8,True,6,0,24);s.imm(0x08076BFA,'cmp',6,15);s.branch(0x08076BFC,9,0x08076BC0);s.imm(0x08076BFE,'mov',0,0)
 s.stack(0x08076C00,True,0xF0);s.stack(0x08076C02,True,2);s.bx(0x08076C04,1)
 # FindFirstActiveTask enumerates16 exact-stride rows; head sentinel0xFE produces index r0 or count16.
 s.stack(0x08076D40,False,0,True);s.imm(0x08076D42,'mov',2,0);s.pointer(0x08076D44,0,0x08076D78)
 need(d.u32(raw,0x08076D78)==0x030050D0,'finder same actual gTasks table')
 s.mem(0x08076D46,True,True,1,0,4);s.addi(0x08076D48,3,0,0);s.imm(0x08076D4A,'cmp',1,1);s.branch(0x08076D4C,1,0x08076D54)
 s.mem(0x08076D4E,True,True,0,3,5);s.imm(0x08076D50,'cmp',0,254);s.branch(0x08076D52,0,0x08076D72)
 s.addi(0x08076D54,0,2,1);s.shift(0x08076D56,False,0,0,24);s.shift(0x08076D58,True,2,0,24);s.imm(0x08076D5A,'cmp',2,15);s.branch(0x08076D5C,8,0x08076D72)
 s.shift(0x08076D5E,False,0,2,2);s.add(0x08076D60,0,0,2);s.shift(0x08076D62,False,0,0,3);s.add(0x08076D64,1,0,3)
 s.mem(0x08076D66,True,True,0,1,4);s.imm(0x08076D68,'cmp',0,1);s.branch(0x08076D6A,1,0x08076D54);s.mem(0x08076D6C,True,True,0,1,5);s.imm(0x08076D6E,'cmp',0,254);s.branch(0x08076D70,1,0x08076D54)
 s.addi(0x08076D72,0,2,0);s.stack(0x08076D74,True,2);s.bx(0x08076D76,1)
 # RunTasks preserves finder result in r0 while building r4=gTasks+40*r0, loading func to r1 and calling BX r1.
 s.stack(0x08076D10,False,(1<<4)|(1<<5),True);s.call(0x08076D12,0x08076D40);s.shift(0x08076D16,False,0,0,24);s.shift(0x08076D18,True,0,0,24)
 s.imm(0x08076D1A,'cmp',0,16);s.branch(0x08076D1C,0,0x08076D34);s.pointer(0x08076D1E,5,0x08076D3C)
 s.shift(0x08076D20,False,4,0,2);s.add(0x08076D22,4,4,0);s.shift(0x08076D24,False,4,4,3);s.add(0x08076D26,4,4,5);s.mem(0x08076D28,True,False,1,4,0);s.call(0x08076D2A,0x081C7ACC)
 s.mem(0x08076D2E,True,True,0,4,6);s.imm(0x08076D30,'cmp',0,255);s.branch(0x08076D32,1,0x08076D20);s.stack(0x08076D34,True,(1<<4)|(1<<5));s.stack(0x08076D36,True,1);s.bx(0x08076D38,0)
 s.bx(0x081C7AC8,0);s.bx(0x081C7ACC,1)


def bind_consumers(raw,review,bprj):
 previous.bind_consumers(raw,review,bprj)
 complete_consumer_slices(raw)
 lit={r['label']:r for r in review['consumer_literals']}
 # GBA header actual unconditional ARM B points to the start-up entry.
 op=d.u32(raw,0x08000000);need(op>>24==0xEA,'actual unconditional ARM reset branch')
 offset=op&0xFFFFFF;offset=offset-(1<<24)if offset&(1<<23)else offset
 need(0x08000008+offset*4==0x08000204,'actual reset branch target')
 # Closed ARM entry contains no opaque control transfer before LDR/BX to Thumb AgbMain.
 ops=[d.u32(raw,a)for a in range(0x08000204,0x08000234,4)]
 need(ops[0]==0xE3A00012 and ops[3]==0xE3A0001F,'actual unconditional ARM MOV r0 IRQ/system mode immediate')
 need(ops[1]==ops[4]==0xE129F000,'actual unconditional MSR CPSR_fc,r0 mode switches')
 for index,rd in[(2,13),(5,13),(6,1),(9,1)]:
  q=ops[index];need(q&0xFFFFF000==0xE59F0000|(rd<<12),'positive ARM PC literal load')
 need(ops[7]&0xFFFFF000==0xE28F0000 and ops[8]==0xE5810000,'interrupt pointer setup has no transfer')
 q=ops[9];need(0x08000228+8+(q&4095)==0x08000244,'same actual AgbMain literal')
 need(ops[10]==0xE1A0E00F and ops[11]==0xE12FFF11,'actual MOV lr,pc and BX r1 Thumb interwork')
 need(lit['startup_main_entry']['value']==0x080003A5,'reset reaches actual Thumb AgbMain')
 previous.symbol(bprj,'SetMainCallback2',0x08000544)
 need(literal(raw,0x08000544,1)==0x08000554 and literal(raw,0x08000524,4)==0x08000540,'actual main setter and caller load table')
 need(lit['main_setter_gMain']['value']==lit['main_dispatch_gMain']['value']==0x03003130,'main writer/caller same RAM structure')
 op=half(raw,0x08000546);need(op&0xF800==0x6000 and(op>>6)&31==1 and(op>>3)&7==1 and op&7==0,'setter stores argument0 to callback2 field4')
 op=half(raw,0x08000530);need(op&0xF800==0x6800 and(op>>6)&31==1 and(op>>3)&7==4 and op&7==0,'caller reads callback2 field4')
 need(code.thumb_bl(chunk(raw,0x08000536,4),0x08000536)==0x081C7AC8,'main dispatches loaded callback2 through BX r0')


def task_store(raw,edge,rows,edges):
 """callback taskId由来r8を、実経路上のregister定義・ABI保存込みで追跡。"""
 need((edge['from'],edge['to'],edge['store'],edge['task_entry'],edge['task_register'],edge['index_scale'],edge['stride'],edge['table'])==(0x080F305E,0x080F3074,0x080F305E,0x080F2ED4,8,40,40,0x030050D0),'closed same-task follow-up edge')
 need(any(e['kind']=='callback_edge'and e['callee']==0x08076BB4 and e['to']==edge['task_entry'] for e in edges),'task entry receives actual scheduler task ID')
 for k in('target_literal','table_literal'):d.signed(raw,edge[k])
 need(edge['target_literal']['address']==0x080F3070 and d.u32(raw,0x080F3070)==edge['target_literal']['value']==edge['target']==edge['to']|1,'exact typed followup callback pointer')
 need(edge['table_literal']['address']==0x080F3054 and d.u32(raw,0x080F3054)==edge['table_literal']['value']==0x030050D0,'same actual task storage')
 addresses=[r['address']for r in rows];start=addresses.index(edge['task_entry']);stop=addresses.index(edge['store']);seq=rows[start:stop+1]
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
   mode=(h>>11)&3;v=regs[(h>>3)&7];n=(h>>6)&31
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
 addresses=[p['address']for p in rows]
 if edge['kind']=='callback_edge'and edge['callee']==0x08000544:
  need(edge['from']==edge['call']and edge['load']+2==edge['call']and edge['load']in addresses and edge['to']in addresses,'rooted immediate main callback registration')
  need(code.thumb_bl(chunk(raw,edge['call'],4),edge['call'])==edge['callee']and literal(raw,edge['load'],0)==edge['literal'],'actual LDR r0 and SetMainCallback2 call')
  w=edge['literal_witness'];d.signed(raw,w);need(w['address']==edge['literal']and d.u32(raw,w['address'])==w['value']==edge['target']==edge['to']|1,'odd Thumb target same loaded pointer')
 elif edge['kind']=='task_store_edge':task_store(raw,edge,rows,edges)
 else:previous.indirect(raw,edge,addresses)


def _regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and tuple(r['hit']['address']for r in review['rows'])==HITS,'closed seven new rooted unknown rows')
 need({e['local']for e in review['source_bindings'].values()}=={'BPRJ.ld','gaps-pret-scrcmd.c','pret-task.c','pret-main.c','pret-crt0.s','pret-hall_of_fame.c'},'all six pinned actual-source roles required')
 required_windows={'reset_vector':(0x08000000,4),'reset_startup_arm':(0x08000204,48),'set_main_callback2':(0x08000544,16),'main_call_callbacks':(0x08000510,48),'CreateTask_post_store_setup':(0x08076BD2,20),'CreateTask_bounded_loop_return':(0x08076BF4,18),'FindFirstActiveTask_bounded_index':(0x08076D40,56)}
 by_label={w['label']:w for w in review['consumer_windows']}
 need(len(by_label)==len(review['consumer_windows'])and all(label in by_label and(by_label[label]['address'],by_label[label]['size'])==geometry for label,geometry in required_windows.items()),'closed new whole consumer windows required')
 bprj=previous.sources_bind(review,sources);bind_consumers(raw,review,bprj);regions=[]
 for row in review['rows']:
  hit=row['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original==hit and not original['accepted']and not original['owner_candidates'],'exact unowned inherited unknown only');d.signed(raw,hit)
  root=row['root'];entry=root['entry'];slot=root['slot'];d.signed(raw,slot)
  if root['kind']=='reset_vector':need(slot['address']==0x08000244 and d.u32(raw,slot['address'])==slot['value']==entry|1 and entry==0x080003A4,'actual reset-to-Thumb root only')
  else:
   need(root['kind']=='special_function'and root['opcode']==37,'only typed special root')
   idx=root['special_id'];need(0<=idx<(0x08163758-0x08163068)//4 and slot['address']==0x08163068+4*idx and d.u32(raw,slot['address'])==slot['value']==entry|1,'bounded actual special dispatch slot')
  rows=row['instruction_path'];need(rows and rows[0]['address']==entry and len(rows)<=512,'finite rooted instruction path');d.signed(raw,rows)
  addresses=[p['address']for p in rows];extra=row['typed_indirect_edges'];edges={e['from']:e for e in extra};need(len(edges)==len(extra),'unique typed outgoing edges');start=0
  for i,p in enumerate(rows):
   if p['address']not in edges:continue
   edge=edges[p['address']];need(i+1<len(rows)and rows[i+1]['address']==edge['to'],'exact typed path adjacency')
   if edge['kind']=='switch_edge':
    need(p['size']==2 and i>start,'complete one-halfword rooted switch');gaps.thumb_path(raw,rows[start:i],rows[start]['address']);need(rows[i-1]['address']+rows[i-1]['size']==p['address'],'switch contiguous predecessor')
   else:gaps.thumb_path(raw,rows[start:i+1],rows[start]['address'])
   indirect(raw,edge,rows,extra);start=i+1
  need(start<len(rows),'nonempty final direct suffix');gaps.thumb_path(raw,rows[start:],rows[start]['address'])
  w=row['instruction_window'];d.signed(raw,w);selected=[p for p in rows if w['address']<=p['address']<w['address']+w['size']]
  need(selected and selected[0]['address']==w['address']and all(a['address']+a['size']==b['address']for a,b in zip(selected,selected[1:]))and selected[-1]['address']+selected[-1]['size']==w['address']+w['size']and d.contains(w['address'],w['address']+w['size'],hit['address'],4),'complete minimal crossing instruction window only')
  need(not row['literal_pool_included']and not row['whole_function_range_classified']and not any(w['address']<=p.get('literal_address',0)<w['address']+w['size']for p in rows),'no literal or blanket range classification')
  regions.append(d.TypedRegion(w['address'],w['address']+w['size'],'rooted_thumb_instruction_stream',dict(root=root,instruction_window=w,instructions=[{k:p[k]for k in('address','size')}for p in selected],root_verified=True,literal_pool_included=False,path_instructions=len(rows),typed_indirect_edges=len(edges),full_story_reachability_claimed=False)))
 return regions,dict(status='PASS_SEVEN_FINITE_RESET_SPECIAL_TASK_CODE_WINDOWS',count=len(regions),full_story_reachability_claimed=False)


def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources)
