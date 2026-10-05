"""MOVE_LEER実consumerの有限・条件付き根。ROM/セーブを保持しない。"""
import hashlib,json
import pr16_dex_hof_lifetime_root as prior
BASE=prior.BASE
need=prior.need
ident=prior.ident
canonical=prior.canonical
window=prior.window
u32=prior.u32

class UndefinedCallerRegister:
 """ABIが保証しないr12。伝播はできるが演算・比較・メモリアクセスは拒否。"""
 def __init__(self,label='caller-saved r12'):self.label=label
 def __repr__(self):return '<undefined>'
 def reject(self,*args):raise ValueError('未定義値を使用: '+self.label)
 __add__=__radd__=__sub__=__rsub__=__mul__=__rmul__=reject
 __and__=__rand__=__or__=__ror__=__xor__=__rxor__=reject
 __lshift__=__rlshift__=__rshift__=__rrshift__=reject
 __eq__=__ne__=__lt__=__le__=__gt__=__ge__=reject
 __bool__=__int__=__index__=__neg__=__invert__=reject
UNDEFINED_R12=UndefinedCallerRegister()
UNDEFINED_MUL_C=UndefinedCallerRegister('ARMv4T MUL carry')

class Machine(prior.Machine):
 def __init__(self,raw,code_ranges,write_ranges,hooks=None):
  super().__init__(raw,code_ranges,write_ranges)
  self.hooks=hooks or {};self.contract_calls=[];self.allocations={};self.live_alloc=None
 def run(self,entry,stop,limit=4096):
  pc=entry;r=self.r
  for _ in range(limit):
   if pc==stop:return self
   if pc in self.hooks:
    saved=self.r[4:12]+self.r[13:15];memory=dict(self.mem);first=len(self.writes)
    self.hooks[pc](self,pc)
    self.r[12]=UNDEFINED_R12
    need(self.r[4:12]+self.r[13:15]==saved,'外部境界のcallee-saved/SP/LR保存')
    touched=[w for w in self.writes[first:]]
    if pc in (0x08002BB0,0x081C7A90):allowed=((SCRATCH,SCRATCH+4096),)
    elif pc==0x081C7A88:allowed=tuple((lo,hi)for lo,hi in self.write_ranges if lo not in (STACK[0],CURSOR,SPRITES,0x03000AE8,0x03000B68,0x03000DE8,0x030050D0))
    else:allowed=()
    need(all(any(lo<=w['address']and w['address']+w['size']<=hi for lo,hi in allowed)for w in touched),'外部境界の限定write frame')
    changed={a for a in set(memory)|set(self.mem)if memory.get(a)!=self.mem.get(a)}
    written={a for w in touched for a in range(w['address'],w['address']+w['size'])}
    need(changed<=written,'外部境界のseedによる隠れたwrite禁止')
    pc=self.r[14]&~1;continue
   need(pc%2==0 and any(lo<=pc<hi for lo,hi in self.code_ranges),f'未許可code entry {pc:#x}')
   op=self.read(pc,2);n=4 if op&0xf800==0xf000 else 2
   need(any(lo<=pc and pc+n<=hi for lo,hi in self.code_ranges),'完全命令幅が同一code range内')
   self.trace.append({'address':pc,**ident(self.raw[pc-BASE:pc-BASE+n])});nxt=pc+n
   if n==4:
    second=self.read(pc+2,2);need(second&0xf800==0xf800,'完全ARMv4T BL');v=((op&2047)<<12)|((second&2047)<<1);v-=1<<23 if v&(1<<22)else 0;target=pc+4+v;self.calls.append({'address':pc,'target':target});r[14]=(pc+4)|1;nxt=target
   elif op&0xf800==0x4800:r[(op>>8)&7]=self.read(((pc+4)&~3)+(op&255)*4,4)
   elif op&0xf800==0x1800:
    a=r[(op>>3)&7];b=(op>>6)&7 if op&0x400 else r[(op>>6)&7];r[op&7]=self.arithmetic(a,b,bool(op&0x200))
   elif op&0xe000==0:
    k=(op>>11)&3;s=(op>>6)&31;v=r[(op>>3)&7];need(k<3,'限定shift')
    signed=v-(1<<32)if v&(1<<31)else v;out=((v<<s)if k==0 else (v>>(s or 32)if k==1 else signed>>(s or 32)))&0xffffffff;r[op&7]=out;self.nz(out)
    if k==0 and s:self.flags[2]=bool((v>>(32-s))&1)
    elif k:self.flags[2]=bool((v>>((s or 32)-1))&1)
   elif op&0xe000==0x2000:
    k=(op>>11)&3;reg=(op>>8)&7;b=op&255
    if k==0:r[reg]=b;self.nz(b)
    elif k==1:self.arithmetic(r[reg],b,True)
    else:r[reg]=self.arithmetic(r[reg],b,k==3)
   elif op&0xfc00==0x4000:
    k=(op>>6)&15;reg=op&7;s=(op>>3)&7;a,b=r[reg],r[s]
    if k==0:r[reg]=a&b;self.nz(r[reg])
    elif k==1:r[reg]=a^b;self.nz(r[reg])
    elif k in(2,3,4):
     shift=b&255;signed=a-(1<<32)if a&0x80000000 else a
     if shift:
      if k==2:out=(a<<shift)&0xffffffff if shift<32 else 0;self.flags[2]=bool((a>>(32-shift))&1)if shift<=32 else False
      elif k==3:out=a>>shift if shift<32 else 0;self.flags[2]=bool((a>>(shift-1))&1)if shift<=32 else False
      else:out=(signed>>min(shift,32))&0xffffffff;self.flags[2]=bool((a>>(min(shift,32)-1))&1)
     else:out=a
     r[reg]=out;self.nz(out)
    elif k==8:self.nz(a&b)
    elif k==9:r[reg]=self.arithmetic(0,b,True)
    elif k==10:self.arithmetic(a,b,True)
    elif k==12:r[reg]=a|b;self.nz(r[reg])
    elif k==13:r[reg]=(a*b)&0xffffffff;self.nz(r[reg]);self.flags[2]=UNDEFINED_MUL_C
    elif k==14:r[reg]=a&(~b&0xffffffff);self.nz(r[reg])
    elif k==15:r[reg]=~b&0xffffffff;self.nz(r[reg])
    else:need(False,f'未対応ALU {k} at {pc:#x}')
   elif op&0xfc00==0x4400:
    k=(op>>8)&3;reg=(op&7)|((op>>4)&8);s=(op>>3)&15
    need(s!=15,'PC source operandは未対応のため拒否')
    need(not(k==0 and reg==15),'ADD PC制御遷移は未対応のため拒否')
    need(not(k==1 and reg==15),'CMP PC source operandは未対応のため拒否')
    if k==0:r[reg]=(r[reg]+r[s])&0xffffffff
    elif k==1:self.arithmetic(r[reg],r[s],True)
    elif k==2:
     # ARMv4T Thumb MOV PCはstateを変えずbit0を無視する。
     if reg==15:nxt=r[s]&~1
     else:r[reg]=r[s]
    else:
     need(op&0x87==0,'ARMv4T BX');need(r[s]&1==1,'BXのThumb target bit必須');nxt=r[s]&~1
    if nxt!=pc+2:self.edges.append({'address':pc,'target':nxt})
   elif op&0xf000 in(0x6000,0x7000,0x8000):
    z=1 if op&0xf000==0x7000 else 2 if op&0xf000==0x8000 else 4;a=r[(op>>3)&7]+((op>>6)&31)*z;reg=op&7
    if op&0x800:r[reg]=self.read(a,z)
    else:self.write(a,z,r[reg])
   elif op&0xf000==0x5000:
    k=(op>>9)&7;reg=op&7;a=r[(op>>3)&7]+r[(op>>6)&7];z={0:4,1:2,2:1,3:1,4:4,5:2,6:1,7:2}[k]
    if k>=3:
     v=self.read(a,z);r[reg]=(v-(1<<(z*8))if k in(3,7)and v&(1<<(z*8-1))else v)&0xffffffff
    else:self.write(a,z,r[reg])
   elif op&0xf000==0x9000:
    a=r[13]+(op&255)*4;reg=(op>>8)&7
    if op&0x800:r[reg]=self.read(a,4)
    else:self.write(a,4,r[reg])
   elif op&0xf000==0xa000:r[(op>>8)&7]=(r[13]if op&0x800 else(pc+4)&~3)+(op&255)*4
   elif op&0xff00==0xb000:r[13]+=(-(op&127)*4 if op&128 else(op&127)*4)
   elif op&0xfe00==0xb400:
    names=[i for i in range(8)if op&(1<<i)]+([14]if op&0x100 else[]);r[13]-=4*len(names)
    for i,reg in enumerate(names):self.write(r[13]+4*i,4,r[reg])
   elif op&0xfe00==0xbc00:
    names=[i for i in range(8)if op&(1<<i)]+([15]if op&0x100 else[])
    for i,reg in enumerate(names):
     v=self.read(r[13]+4*i,4)
     # ARMv4T POP PCはBXと異なりinterworkせずThumbを保つ。
     if reg==15:nxt=v&~1
     else:r[reg]=v
    r[13]+=4*len(names)
   elif op&0xf000==0xc000:
    base=(op>>8)&7;a=r[base];names=[i for i in range(8)if op&(1<<i)];need(names,'nonempty multiple register list')
    for i,reg in enumerate(names):
     if op&0x800:r[reg]=self.read(a+4*i,4)
     else:self.write(a+4*i,4,r[reg])
    need(base not in names,'writebackbase not transferred');r[base]=a+len(names)*4
   elif op&0xf000==0xd000:
    c=(op>>8)&15;need(c<14,'予約条件拒否');N,Z,C,V=self.flags;take=(lambda:Z,lambda:not Z,lambda:C,lambda:not C,lambda:N,lambda:not N,lambda:V,lambda:not V,lambda:C and not Z,lambda:not C or Z,lambda:N==V,lambda:N!=V,lambda:not Z and N==V,lambda:Z or N!=V)[c]();off=op&255;off-=256 if off&128 else 0
    if take:nxt=pc+4+2*off
   elif op&0xf800==0xe000:
    off=op&2047;off-=2048 if off&1024 else 0;nxt=pc+4+2*off
   else:need(False,f'未対応Thumb at {pc:#x}')
   pc=nxt
  need(False,'有限命令数上限')


CURSOR=prior.CURSOR
SPRITES=prior.SPRITES
STOP=0x01000000
STACK=(0x03007800,0x03007F00)
SCRATCH=0x02010000
ROOT_ENTRY=0x08071D40
CODE=prior.CONSTRUCTOR_CODE+prior.COMMAND_CODE+(
 (0x08071D40,0x08071D48),(0x090C6654,0x090C66E0),(0x090C69D0,0x090C69D2),
 (0x08071D78,0x08071ECC),(0x09097C22,0x09097C8A),
 (0x08071FCC,0x08071FFA),(0x081C7AC8,0x081C7ACA),(0x0807200C,0x08072014),
 (0x090C5D08,0x090C5D54),(0x0800E9E8,0x0800EA2C),(0x0800EA2C,0x0800EA76),
 (0x08008258,0x0800829C),(0x08006FB0,0x080070C4),(0x08008424,0x0800845E),
 (0x080084A4,0x080084F0),(0x0800851C,0x08008532),(0x0806FB90,0x0806FBBE),
 (0x08071F3C,0x08071F6C),(0x08071FA0,0x08071FCC),
 (0x080725EC,0x08072836),(0x08074A44,0x08074A9C),(0x080723D4,0x08072580),(0x08072594,0x080725EC),(0x080749C8,0x08074A34),(0x09097E30,0x09097E50),
 (0x0807396C,0x080739B4),(0x080BD4B8,0x080BD5C4),(0x08000AC4,0x08000AF0),(0x08000A38,0x08000ABA),
 (0x08072D84,0x08072DB6),(0x0807336C,0x0807339E),(0x080731E8,0x080732AA),(0x08071A98,0x08071AE0),
 (0x08076D40,0x08076D78),(0x08076BB4,0x08076C08),(0x08076C08,0x08076CA0),(0x081C9DF8,0x081C9E50),
)
WRITES=(STACK,(CURSOR,0x02037E60),(SPRITES,SPRITES+3*68),(0x03000AE8,0x03000AE8+128),(0x03000B68,0x03000B68+256),
 (0x03000DE8,0x03000E08),(0x02021AC4,0x02021B44),(0x03000000,0x030000C1),
 (0x020228F4,0x02022900),(0x02039930,0x02039932),(0x020228E8,0x020228F8),(0x030050D0,0x03005350),
 (SCRATCH,SCRATCH+4096),(0x06010000,0x06011000),(0x0203732C,0x0203734C),(0x0203772C,0x0203774C),(0x0203724C,0x0203726C),(0x0203764C,0x0203766C),(0x05000120,0x05000140),(0x02013000,0x02014000),(0x02014800,0x02015000))

# 以下はROM命令を実行したことにせず、有限pathの明示的な外部契約として記録する。
# ABI正常return、nonalias scratch、single-thread継続は全プログラムの証明ではない。
def external(m,pc):
 name={0x08075F94:'visible_battler_priorities_return_frame',0x08047814:'healthbox_priorities_return_frame',
       0x0803F354:'valid_mon_field_read_return_frame',0x08000F44:'bounded_bg_dma_request_return_frame',0x080BE1B4:'bounded_battler_graphics_copy_return_frame',
       0x090D5704:'valid_illusion_party_return_frame',0x081C10B0:'song_start_return_audio_frame',0x081C12D0:'audio_resume_return_audio_frame',0x081C2178:'audio_pan_return_audio_frame'}[pc]
 args=m.r[:4];event={'entry':pc,'name':name,'arguments':args,'assumed_abi_return_and_frame':True}
 if pc==0x08075F94:need(not m.contract_calls,'初回setup helperだけ')
 if pc==0x08047814:need(args[0]==0,'healthbox設定0')
 if pc==0x0803F354:
  need(args[1]in(11,57),'今回のspecies/HP fieldだけ')
  need(args[0]in(0x020241E4,0x02023F8C),'先頭player/enemy mon、非alias')
 if pc==0x090D5704:need(args[0]in range(4),'有効battler0..3')
 if pc==0x08000F44:
  need(args in([0,0x06006000,8192,1],[0,0x0600F000,4096,1]),'BG2専用DMA宛先と幅')
  event['required_preserved_regions']=['all_EWRAM_inputs_and_control','all_IWRAM_inputs_except_DMA_queue','sprite_tile_palette_registries','callee_saved_and_stack_return']
 if pc==0x080BE1B4:
  need(args==[2,0,0,0],'単一attacker背景copyのABI')
  extra=[m.read(m.r[13]+i*4,4)for i in range(4)]
  need(extra==[9,0x02013000,0x02014800,768],'非alias背景buffersとtilesOffset')
  event['stack_arguments']=extra
  event['required_preserved_regions']=['animation_cursor_and_callback','sprite_slot2_and_callback','sprite_tile_palette_registries','battle_context_pointers','callee_saved_and_stack_return']
 if pc==0x081C10B0:need(args[0]==185,'Leer前置SEの実ID')
 if pc==0x081C12D0:need(args[0]in(0x03007390,0x030073D0),'実SE1/SE2 player')
 if pc==0x081C2178:need(args[0]in(0x03007390,0x030073D0)and args[1]==65535 and args[2]==0xFFFFFFC0,'実pan ABI')
 m.contract_calls.append(event)
 result=(0x020241E4 if args[0]%2==0 else 0x02023F8C)if pc==0x090D5704 else 1 if pc==0x0803F354 else 0xA0000000
 m.r[:4]=[result,0xA0000001,0xA0000002,0xA0000003]
 m.flags=[True,False,False,True]

def alloc(m,pc):
 size=m.r[0];need(size in(2560,32)and m.live_alloc is None,'二つの有限sizeと同時allocationなし')
 need(not any(lo<=SCRATCH<hi for lo,hi in (STACK,(SPRITES,SPRITES+64*68),(CURSOR,CURSOR+96))),'scratch非alias')
 m.live_alloc=(SCRATCH,size)
 for i in range(size):m.write(SCRATCH+i,1,0)
 m.contract_calls.append({'entry':pc,'name':'AllocZeroed_success_nonalias','size':size,'result':SCRATCH,'assumed_abi_return_and_frame':True})
 m.r[:4]=[SCRATCH,0xA0000001,0xA0000002,0xA0000003];m.flags=[True,False,False,True]

def free(m,pc):
 need(m.live_alloc is not None and m.r[0]==m.live_alloc[0],'同じallocationをFree')
 m.contract_calls.append({'entry':pc,'name':'Free_matching_allocation','size':m.live_alloc[1],'assumed_abi_return_and_frame':True});m.live_alloc=None
 m.r[:4]=[0xA0000000+i for i in range(4)];m.flags=[True,False,False,True]

def lz(m,pc):
 need(m.read(pc,2)==0xDF11 and m.read(pc+2,2)==0x4770,'BIOS WRAM LZ命令境界')
 src,dest=m.r[:2];need(m.live_alloc==(dest,m.read(src,4)>>8),'同じ有限allocationへのBIOS展開')
 off=src-BASE;need(m.raw[off]==0x10,'LZ10 type');size=m.read(src,4)>>8;pos=off+4;out=bytearray()
 while len(out)<size:
  need(pos<len(m.raw),'有限LZ flags');flags=m.raw[pos];pos+=1
  for bit in range(7,-1,-1):
   if len(out)==size:break
   if flags&(1<<bit):
    need(pos+2<=len(m.raw),'有限LZ pair');a,b=m.raw[pos:pos+2];pos+=2;n=(a>>4)+3;dist=((a&15)<<8|b)+1
    need(dist<=len(out)and len(out)+n<=size,'完全LZ backreference')
    for _ in range(n):out.append(out[-dist])
   else:need(pos<len(m.raw),'有限LZ literal');out.append(m.raw[pos]);pos+=1
 m.reads[src,pos-off]=window(m.raw,src,pos-off)
 for i,v in enumerate(out):m.write(dest+i,1,v)
 m.contract_calls.append({'entry':pc,'name':'BIOS_LZ10_bounded_semantics','encoded':window(m.raw,src,pos-off),'decoded':ident(out),'destination':dest,'assumed_abi_return_and_frame':False})
 m.r[:4]=[0xA0000000+i for i in range(4)];m.flags=[True,False,False,True]

def cpuset(m,pc):
 need(m.read(pc,2)==0xDF0B and m.read(pc+2,2)==0x4770,'BIOS CpuSet命令境界')
 src,dst,control=m.r[:3];unit=4 if control&(1<<26)else 2;count=control&0x1FFFFF
 need(control&~(0x1FFFFF|(1<<24)|(1<<26))==0 and 0<count<=2048,'有限CpuSet control')
 fill=bool(control&(1<<24))
 for i in range(count):m.write(dst+i*unit,unit,m.read(src if fill else src+i*unit,unit))
 m.contract_calls.append({'entry':pc,'name':'BIOS_CpuSet_bounded_semantics','source':src,'destination':dst,'size':count*unit,'assumed_abi_return_and_frame':False})
 m.r[:4]=[0xA0000000+i for i in range(4)];m.flags=[True,False,False,True]

HOOKS={a:external for a in (0x08075F94,0x08047814,0x0803F354,0x08000F44,0x080BE1B4,0x090D5704,0x081C10B0,0x081C12D0,0x081C2178)}
HOOKS.update({0x08002BB0:alloc,0x08002BC4:free,0x081C7A90:lz,0x081C7A88:cpuset})

def seed(m):
 # 値は実save観測ではなく、通常の有効single battleインターフェースを具体化した有限例。
 for a,n in ((SPRITES,64*68),(0x030050D0,16*40),(0x02021AC4,128),(0x03000000,0xC1),
             (0x02037E08,96),(0x02023D5C,16),(0x03007800,0x700)):
  for i in range(n):m.seed(a+i,1,0)
 for i in range(2):
  m.seed(SPRITES+i*68+62,1,1);m.seed(SPRITES+i*68+32,2,120);m.seed(SPRITES+i*68+34,2,80)
 for i in range(64):m.seed(0x03000AE8+i*2,2,65535)
 for i in range(16):m.seed(0x03000DE8+i*2,2,65535)
 for i in range(96):m.seed(0x03000060+i,1,255)
 for a,n,v in ((0x03003E98,1,0),(0x02021AC2,2,0),(0x02023CCB,1,0),(0x02023CCC,1,1),
   (0x02022AAC,4,8),(0x02023B36,4,0xFFFF0100),(0x02023E34,4,0x03020100),
   (0x02023F78,4,0x0203D000),(0x0203D000,4,0x0203D100),(0x0203D004,4,0x0203D200),
   (0x0203D100,4,0x00010000),(0x0203D104,4,0x00010000),(0x0203D200,16,0),
   (0x02023CA4,4,0xFFFF0100),(0x02023B36,4,0xFFFF0100),(0x02023B2E,8,0),
   (0x02022B18,4,0x02012000),(0x02022B1C,4,0x02014000),(0x0203732C,32,0),(0x04000006,2,0),(0x04000000,2,0),(0x020228E8,16,0)):
  m.seed(a,n,v)
 m.r[0]=43

LAST=None
def interpret(raw):
 global LAST
 m=Machine(raw,CODE,WRITES,HOOKS);LAST=m;seed(m)
 m.run(ROOT_ENTRY,STOP,limit=10000)
 need(m.read(CURSOR,4)==prior.PREFIX[0][0]and m.read(0x02037E10,4)==0x08071FCD,'実rootのscript/callback登録')
 need(m.read(0x02037E4E,1)==0 and m.read(0x02037E4F,1)==1,'実DoMoveAnim battle入力producer')
 m.r[14]=STOP|1;m.run(m.read(0x02037E10,4)&~1,STOP,limit=25000)
 need(m.read(CURSOR,4)==0x081B4987 and m.read(0x02037E14,1)==1 and m.read(0x02037E10,4)==0x08071FA1,'loadの実wait継続')
 need(m.read(0x03000AE8,2)==10027 and m.read(0x03000B68,2)==0 and m.read(0x03000DE8,2)==10027,'空registryから実sheet/palette登録')
 need(m.live_alloc is None,'両resource loaderのFree済み')
 for expected in(0,0):
  m.r[14]=STOP|1;m.run(m.read(0x02037E10,4)&~1,STOP)
  need(m.read(0x02037E14,1)==expected,'wait callback再入')
 need(m.read(0x02037E10,4)==0x08071FCD,'waitから同じdispatcherへ復帰')
 m.r[14]=STOP|1;m.run(m.read(0x02037E10,4)&~1,0x080DF98E,limit=25000)
 need(any(t['address']==0x08076BCE for t in m.trace)and m.read(0x030050D0,4)==0x08072919 and m.read(0x030050D4,1)==1,'CreateTaskの実producerが必要、満杯の0戻りは成功でない')
 slot=SPRITES+2*68;prior.same_slot_lifetime(m.writes,slot)
 need(m.read(CURSOR,4)==prior.COMMAND+11 and m.r[4]==slot and m.read(slot+28,4)==prior.CALLBACK|1,'同じ連続prefixから実同slot callback/hit')
 need([t['address']for t in m.trace[-2:]]==[0x08074796,0x080DF98C],'完全BLのreturn後LDR')
 return m

CANDIDATE=dict(prior.CANDIDATE)
HIT=prior.HIT
KIND='rooted_thumb_instruction_stream'
PRIOR_MODULE_ID={'size':19545,'sha256':'7d1827e12c7261371778d0fb08b0bbc5dcdd8efd2344017310c617a2ebbd650a'}
CLAIMS={
 'finite_conditional_root_to_instruction_consumer_proven':True,
 'actual_move_table_dispatch_and_template_bound':True,
 'actual_sprite_resource_registry_producers_executed':True,
 'actual_wait_callback_registration_and_two_returns_executed':True,
 'same_slot_synchronous_callback_lifetime_proven':True,
 'abstract_environment_contracts_explicit':True,
 'all_callees_concretely_executed':False,
 'natural_battle_reachability_claimed':False,
 'universal_lifetime_or_irq_safety_claimed':False,
 'whole_animation_or_indirect_reference_completeness_claimed':False,
 'current_acceptance_claimed':False,
 'newly_classified':1,
 'donor_eligible':False,
 'safe_capacity_bytes':0,
}
PRECONDITIONS={
 'theorem':'If MOVE_LEER is passed to the installed DoMoveAnim entry and the named environment contracts hold, this finite execution consumes the hit as a complete BL plus LDR instruction window.',
 'boundary':'A valid synchronous single battle interface, not a proof that a particular save, gamepad input, or all plays reaches the entry.',
 'battlers':{'attacker':0,'target':1,'positions':[0,1,255,255],'sprite_slots':[0,1,255,255],'party_indexes':[0,0,0,0],'species':1,'hp_nonzero':True,'trainer_battle_flags':8},
 'first_free_sprite_slot':2,
 'resources':'empty tile/palette tag registries; first free tile0 and palette0; reserved palette count0; nonalias allocation success for2560 and32 bytes',
 'background_buffers':{'tiles':0x02012000,'tilemap':0x02014000,'minimum_sizes':[8192,4096]},
 'battle_graphics_context':'valid, readable, nonalias battlerData/healthboxData pointers; transformed species1; no Illusion; these are incoming battle-interface conditions',
 'gpu':'VCOUNT0 and DISPCNT0; empty deferred GPU queue; hardware VBlank/DMA does not run during the interpreted intervals',
 'scheduler':'one invocation of the registered animation callback per displayed wait step; no unmodeled interleaving mutates the proof projection; no task runs between monbg allocation and the synchronous createsprite callback',
 'registers':{'pattern_base':0x10001000,'stride':4,'sp':0x03007F00,'lr':STOP|1,'entry_r0':43,'nzcv':[False]*4},
 'undefined_values':'r12 becomes an unusable unknown at every external boundary; MUL carry becomes unknown until a defining instruction; dependent execution is rejected',
 'external_helpers':'ABI return with callee-saved registers/SP/return context preserved; permitted unrelated display/audio/heap effects are abstracted; control, cursor, resource tags, selected slot and the explicitly supplied nonalias battle input projection remain as required by each contract',
 'scope':'one concrete bounded witness under the interface conditions; neither arbitrary RAM nor arbitrary incoming registers',
}
CONTRACTS={
 'AllocZeroed_success_nonalias':{'kind':'assumption','entry':0x08002BB0,'requires':'success,2560 or32 bytes, no concurrent live allocation, nonalias scratch and stack/control/sprite/tag regions','ensures':'returns zeroed SCRATCH, caller-saved registers/flags need not survive'},
 'Free_matching_allocation':{'kind':'assumption','entry':0x08002BC4,'requires':'same live scratch allocation','ensures':'normal return, no writes to control/registry/sprite projection'},
 'valid_illusion_party_return_frame':{'kind':'assumption','entry':0x090D5704,'requires':'battler0..3 and valid single-battle party indexes','ensures':'nonalias player/enemy first-mon pointer with species1'},
 'valid_mon_field_read_return_frame':{'kind':'assumption','entry':0x0803F354,'requires':'valid first-mon pointer; field11 or57','ensures':'species1 or HP1; preserves animation/sprite/resource projection'},
 'visible_battler_priorities_return_frame':{'kind':'assumption','entry':0x08075F94,'requires':'valid initial visible battler records','ensures':'normal return; permitted OAM priority effects do not alias cursor/callback/tags or future free slot2'},
 'healthbox_priorities_return_frame':{'kind':'assumption','entry':0x08047814,'requires':'argument0 and valid healthbox records','ensures':'normal return; permitted healthbox OAM effects do not alias the selected sprite or animation inputs'},
 'bounded_bg_dma_request_return_frame':{'kind':'assumption','entry':0x08000F44,'requires':'fixed BG2 destinations0x06006000/0x0600F000 and sizes8192/4096','ensures':'normal return; queued DMA writes remain in these background VRAM spans; no transfer is executed in the model'},
 'bounded_battler_graphics_copy_return_frame':{'kind':'assumption','entry':0x080BE1B4,'requires':'battler position0, bg2,palette9; nonalias tiles0x02013000/map0x02014800 and tilesOffset768','ensures':'normal return; graphics writes/queued transfers do not alias animation cursor/callback, sprite slot2, resource tags, or battle pointers'},
 'song_start_return_audio_frame':{'kind':'assumption','entry':0x081C10B0,'requires':'actual SE185 from the selected command; valid initialized audio state','ensures':'normal return; audio-only effects disjoint from proof projection; no audio IRQ interpreted'},
 'audio_resume_return_audio_frame':{'kind':'assumption','entry':0x081C12D0,'requires':'actual SE1 or SE2 player pointer','ensures':'normal return with disjoint audio-only effects'},
 'audio_pan_return_audio_frame':{'kind':'assumption','entry':0x081C2178,'requires':'SE1/SE2, tracks65535, pan-64','ensures':'normal return with disjoint audio-only effects'},
 'BIOS_LZ10_bounded_semantics':{'kind':'trusted_primitive_model','entry':0x081C7A90,'requires':'SWI11/BX LR; finite valid LZ10 payload and matching allocated destination','ensures':'exact decoded bytes written only inside matching allocation; full encoded identity retained, no payload published'},
 'BIOS_CpuSet_bounded_semantics':{'kind':'trusted_primitive_model','entry':0x081C7A88,'requires':'SWI0B/BX LR; bounded positive count, valid aligned source/destination and fill/copy mode','ensures':'exact bounded write; destination is checked by the common write allowlist'},
}

def bind_sources(sources):
 need(set(sources)==set(SOURCE_EXPECTED),'新scope固定公開source集合')
 for key,row in SOURCE_EXPECTED.items():
  raw=sources[key]
  need(ident(raw)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob_sha'],'全source identity '+key)
 prior.bind_sources({key:sources[key]for key in prior.SOURCE_EXPECTED})
 t=sources['cfru-battle-anims.c'].decode()
 need('LoadCompressedSpriteSheetUsingHeap(&gBattleAnimPicTable[GET_TRUE_SPRITE_INDEX(index)]);'in t and 'LoadCompressedSpritePaletteUsingHeap(&gBattleAnimPaletteTable[GET_TRUE_SPRITE_INDEX(index)]);'in t,'実installed commandのsource対応')
 need('gBattleAnimAttacker = gBankAttacker;'in t and 'gBattleAnimTarget = gBankTarget;'in t,'sourceのbattle入力producer')
 need('LoadSpriteSheet(&dest);'in sources['pret-decompress.c'].decode()and 'LoadSpritePalette(&dest);'in sources['pret-decompress.c'].decode(),'decompress→実registry producerのsource')
 return True


def public_review(raw,sources):
 bind_sources(sources)
 m=interpret(raw)
 roles={(w['address'],w['size']):w for w in prior.finite_selection(raw)}
 for w in m.trace+list(m.reads.values()):roles[w['address'],w['size']]=w
 # 未実行の外部契約は入口を別roleとして束縛し、実行した命令に数えない。
 for pc in HOOKS:
  w=window(raw,pc,4);roles[pc,4]=w
 all_writes=[w for w in m.writes if not STACK[0]<=w['address']<STACK[1]]
 calls=[{k:e[k]for k in('entry','name','assumed_abi_return_and_frame')}for e in m.contract_calls]
 resources=[{k:e[k]for k in('entry','name','encoded','decoded','destination')}for e in m.contract_calls if e['name']=='BIOS_LZ10_bounded_semantics']
 outputs={'sprite_slot':2,'sprite_address':SPRITES+136,'callback':prior.CALLBACK|1,'cursor_after_command':prior.COMMAND+11,
          'tile_tag':10027,'tile_start':0,'palette_tag':10027,'palette_index':0,'background_task_slot':0,'background_task_callback':m.read(0x030050D0,4),
          'background_task_active':m.read(0x030050D4,1),'same_slot_lifetime':prior.same_slot_lifetime(m.writes,SPRITES+136)}
 need(outputs['background_task_callback']==0x08072919 and outputs['background_task_active']==1,'実空task0の確保とcallback保存。満杯戻り0ではない')
 return {'schema_version':1,'status':'FINITE_CONDITIONAL_LEER_INSTRUCTION_CONSUMER','required_candidate':CANDIDATE,'hit_address':HIT,
         'source_bindings':SOURCE_EXPECTED,'prior_module_identity':PRIOR_MODULE_ID,'prior_frozen_review_identity':prior.REVIEW_ID,
         'protected_windows':[roles[k]for k in sorted(roles)],'model':{'instruction_count':len(m.trace),'direct_call_count':len(m.calls),'indirect_edge_count':len(m.edges),
          'trace_identity':ident(canonical(m.trace)),'writes_identity':ident(canonical(all_writes)),'calls_identity':ident(canonical(m.calls)),'edges_identity':ident(canonical(m.edges)),
          'environment_contract_calls':calls,'resources':resources,'outputs':outputs},'claims':CLAIMS,'preconditions':PRECONDITIONS,'external_contracts':CONTRACTS,
         'classification_window':window(raw,0x080DF988,6),
         'classification_instructions':[{'address':0x080DF988,'size':4,'kind':'BL'},{'address':0x080DF98C,'size':2,'kind':'LDR'}],
         'out_of_scope':['natural_input_reachability','universal_battle_context_producers','full_heap_allocator_correctness','universal_audio_or_graphics_termination','arbitrary_IRQ_DMA_interference','maximum_old_egg_target_read_width','owner_retirement','donor_capacity']}


def protected_windows(review):
 need(ident(canonical(review))==REVIEW_ID,'固定新review identity')
 return review['protected_windows']


def geometry(e):
 need(e['root_verified']is True and e['root']=='installed_MOVE_LEER_conditional_sprite_callback','実consumer根')
 need(e['instruction_window']==CLASSIFICATION_WINDOW and e['instructions']==[{'address':0x080DF988,'size':4},{'address':0x080DF98C,'size':2}],'完全BL/LDRだけを分類')
 need(e['claims']==CLAIMS and e['review_identity']==REVIEW_ID and e['preconditions_identity']==ident(canonical(PRECONDITIONS))and e['contracts_identity']==ident(canonical(CONTRACTS)),'条件付きscopeを強めない')
 need(e['literal_pool_included']is False and e['full_story_reachability_claimed']is False,'literal/自然到達を混同しない')
 return 0x080DF988,6


def _regions(raw,inherited,review,sources):
 from pathlib import Path
 import pr16_dex_hof_donor as d
 need(ident(Path(prior.__file__).read_bytes())==PRIOR_MODULE_ID,'旧VM依存sourceは不変、旧model再実行なし')
 need(ident(canonical(review))==REVIEW_ID,'固定新review全体')
 match=[h for h in inherited.get('hits',[])if h['address']==HIT]
 need(len(match)==1 and match[0]['accepted']is False and not match[0]['owner_candidates']and match[0]['size']==4,'親unknown1件だけ')
 prior.fingerprint(raw,match[0])
 for w in review['protected_windows']:prior.fingerprint(raw,w)
 need(review==public_review(raw,sources),'新しい連続modelだけを完全再計算')
 e={'root':'installed_MOVE_LEER_conditional_sprite_callback','root_verified':True,'instruction_window':review['classification_window'],
    'instructions':[{'address':0x080DF988,'size':4},{'address':0x080DF98C,'size':2}], 'claims':CLAIMS,'review_identity':REVIEW_ID,
    'preconditions_identity':ident(canonical(PRECONDITIONS)),'contracts_identity':ident(canonical(CONTRACTS)),'literal_pool_included':False,'full_story_reachability_claimed':False}
 a,n=geometry(e)
 proof={'status':'PASS_FINITE_CONDITIONAL_LEER_INSTRUCTION_CONSUMER','count':1,'hit':HIT,'instruction_window':CLASSIFICATION_WINDOW,
        'models':1,'instruction_count':review['model']['instruction_count'],'protected_read_window_count':len(review['protected_windows']),
        'protected_read_identity':ident(canonical(review['protected_windows'])),'review_identity':REVIEW_ID,'claims':CLAIMS,
        'preconditions_identity':e['preconditions_identity'],'contracts_identity':e['contracts_identity'],'prior_models_rerun':0}
 return [d.TypedRegion(a,a+n,KIND,e)],proof


def regions(raw,inherited,review,sources,root=None):
 need(ident(raw)==inherited['candidate']==CANDIDATE,'現0641全ROM identity必須。旧診断を受入にしない')
 return _regions(raw,inherited,review,sources)

SOURCE_EXPECTED={'cfru-BPRJ.ld': {'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
                  'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
                  'size': 68505},
 'cfru-anim-defines.s': {'git_blob_sha': 'fc4168cbc9f43ef084afb04ff4ec8c81f9390592',
                         'sha256': '166cbae334e3c45cb0d694fb483b8ac13b9cc84dc4bd64eb8d04ee696c1e84e4',
                         'size': 33164},
 'cfru-battle-anims.c': {'git_blob_sha': '096a8763a4260052566ed029f841bc68e561d269',
                         'sha256': '4893fda793e75356672e8b1be3bca4bd54fe562774fd8b07ed9f8f9ba501aff3',
                         'size': 192535},
 'cfru-include_battle_anim.h': {'git_blob_sha': '68822edced83efcff0dc1893ec5052ba59875750',
                                'sha256': 'fd80eac8342c2452e9cb62f7b86b6db651d8136c25c9a6eb1369c1a92e4afb98',
                                'size': 28504},
 'cfru-moves.h': {'git_blob_sha': '444712bfec68c13fabffd3e167d380b6c23770ba',
                  'sha256': 'bc2ae17e444625fa2e1727d42c50a24f6758da26e44229a6f12a3afa3a275d79',
                  'size': 30601},
 'cfru-particle-table.s': {'git_blob_sha': '814f613a56d1314a462d5a4aebcca8bb3cdf9010',
                           'sha256': 'ee2d106484b531e17c52d9edb2d966ed1a214685c19fbf6d186328e67372d9fa',
                           'size': 39352},
 'pret-battle-anim-script.inc': {'git_blob_sha': '15c48c39f5860efe132e782c22a6cedb0f8d5ac3',
                                 'sha256': 'cb193c567289983c26ed8acaa8dd64501c64c7e088e28995c49439333b52b27c',
                                 'size': 4279},
 'pret-battle-anim.c': {'git_blob_sha': '30f9a7ad2482d1767f5c70ee30a3c85528605bb3',
                        'sha256': '5883d9ee0483120ef67461952f5880499f322fb1c706cc213ca13c0c2b0e88c5',
                        'size': 46944},
 'pret-decompress.c': {'git_blob_sha': 'f4740f917ed9ae7e0fd967107e1e63733bb8c66a',
                       'sha256': 'f190145b3948c1c22213e1a540f261aba89592ed9f30b6d13fa25b78ac417c7f',
                       'size': 11157},
 'pret-sprite.c': {'git_blob_sha': 'd0198d53004775c8664dcccf57833e178833776e',
                   'sha256': '2a804302eb5a89d31c3ec2f33dc645a80a0c645113d4b33b9bd571064c0286ae',
                   'size': 48783},
 'pret-sprite.h': {'git_blob_sha': '6a1b272119ce6e3a8dcf45adf2eef8923a6d5175',
                   'sha256': 'a77aa1c837dfb58cf60b3eac299c7cc29a23ce27735ba710b9e8eeed102bf773',
                   'size': 9368}}


REVIEW_ID={'size': 264694, 'sha256': 'e87845750f0af232e235b89447190a349c351af9c744cab6b3fb95d84c93d864'}
CLASSIFICATION_WINDOW={'address': 135133576, 'size': 6, 'sha256': '49c270268615c3f03be67515993744bdfbce9aad079e92d73f854830f1b3be44'}
