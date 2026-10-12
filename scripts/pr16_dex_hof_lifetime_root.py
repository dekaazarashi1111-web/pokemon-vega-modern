"""有限な新callback経路の診断専用Thumb解釈器。未知read/call/writeを拒否する。"""
import hashlib,json,re
from pathlib import Path

BASE=0x08000000

def need(ok,msg):
 if not ok:raise ValueError(msg)

def ident(b):return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}

class Machine:
 def __init__(self,raw,code_ranges,write_ranges):
  self.raw=raw;self.code_ranges=code_ranges;self.write_ranges=write_ranges
  self.r=[0x10001000+i*4 for i in range(16)];self.r[13]=0x03007F00;self.r[14]=0x01000001
  self.mem={};self.flags=[False]*4;self.trace=[];self.reads={};self.writes=[];self.calls=[];self.edges=[]
 def seed(self,a,n,v):
  for i in range(n):self.mem[a+i]=(v>>(8*i))&255
 def read(self,a,n):
  # この有限profileでは非整列LDRのrotate等をモデル化せず拒否する。
  need(type(a)is int and n in(1,2,4)and 0<=a<1<<32 and a%n==0,'aligned byte/half/word readのみ')
  if BASE<=a<=BASE+len(self.raw)-n:
   b=self.raw[a-BASE:a-BASE+n];self.reads[a,n]={'address':a,**ident(b)};return int.from_bytes(b,'little')
  need(all(a+i in self.mem for i in range(n)),f'未束縛RAM read {a:#x}+{n}')
  return sum(self.mem[a+i]<<(8*i)for i in range(n))
 def write(self,a,n,v):
  need(type(a)is int and n in(1,2,4)and 0<=a<1<<32 and a%n==0,'aligned byte/half/word writeのみ')
  need(any(lo<=a and a+n<=hi for lo,hi in self.write_ranges),f'許可域外write {a:#x}+{n}')
  self.seed(a,n,v);self.writes.append({'address':a,'size':n,'value':v&((1<<(n*8))-1)})
 def nz(self,v):self.flags[:2]=[bool(v&0x80000000),v==0]
 def arithmetic(self,a,b,sub=False):
  v=(a-b if sub else a+b)&0xffffffff;self.nz(v);self.flags[2]=a>=b if sub else a+b>0xffffffff;self.flags[3]=bool(((a^b)&(a^v)if sub else ~(a^b)&(a^v))&0x80000000);return v
 def run(self,entry,stop,limit=4096):
  pc=entry;r=self.r
  for _ in range(limit):
   if pc==stop:return self
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
    elif k==8:self.nz(a&b)
    elif k==9:r[reg]=self.arithmetic(0,b,True)
    elif k==10:self.arithmetic(a,b,True)
    elif k==12:r[reg]=a|b;self.nz(r[reg])
    elif k==13:r[reg]=(a*b)&0xffffffff;self.nz(r[reg])
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
    c=(op>>8)&15;need(c<14,'予約条件拒否');N,Z,C,V=self.flags;take=[Z,not Z,C,not C,N,not N,V,not V,C and not Z,not C or Z,N==V,N!=V,not Z and N==V,Z or N!=V][c];off=op&255;off-=256 if off&128 else 0
    if take:nxt=pc+4+2*off
   elif op&0xf800==0xe000:
    off=op&2047;off-=2048 if off&1024 else 0;nxt=pc+4+2*off
   else:need(False,f'未対応Thumb at {pc:#x}')
   pc=nxt
  need(False,'有限命令数上限')


CANDIDATE={'size':33554432,'sha256':'0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583'}
HIT=0x080DF989
CURSOR=0x02037E08
SPRITES=0x020205B8
TEMPLATE=0x083C4DC4
CALLBACK=0x080DF984
COMMAND=0x081B4992
PREFIX=((0x081B4984,0,3),(0x081B4987,10,2),(0x081B4989,40,2),(0x081B498B,12,3),(0x081B498E,25,4),(COMMAND,2,11))
CONSTRUCTOR_CODE=((0x08006D68,0x08006DFC),(0x08006C10,0x08006D68),(0x08006F58,0x08006FAE),(0x081C9D98,0x081C9DF6),(0x08008380,0x080083D8),(0x08008084,0x080080D4),(0x08008564,0x0800859C),(0x081C7ACC,0x081C7ACE))
COMMAND_CODE=((0x080720C0,0x080721A8),(0x08076000,0x08076028),(0x0807497C,0x0807498C),(0x08073C24,0x08073D34),(0x09097E00,0x09097E20),(0x090F1E14,0x090F1EAC),(0x090F3FFC,0x090F3FFE),(0x091263A8,0x091263BA),(CALLBACK,0x080DF98E),(0x08074770,0x08074798),(0x08074968,0x0807497C),(0x08073F50,0x08073FDE),(0x08073D34,0x08073F50),(0x09097BA6,0x09097BEE),(0x090BB3D4,0x090BB3F0))
OBLIGATIONS=(
 'selected_move_engine_to_prefix_entry_not_executed',
 'prefix_opcodes_0_10_40_25_and_wait_callback_continuity_not_proven',
 'battle_context_input_state_producer_not_proven',
 'sprite_tile_palette_input_state_producer_not_proven',
)
PRECONDITIONS={
 'kind':'artificial_finite_single_thread_seed_not_a_save_or_runtime_observation',
 'initial_register_pattern':{'base':0x10001000,'stride':4,'register_count':16,'sp':0x03007F00,'lr':0x01000001},
 'initial_nzcv':[False,False,False,False],
 'execution_mode':'ARMv4T_THUMB_with_no_IRQ_DMA_or_concurrent_memory_writer',
 'constructor_inputs':{'template':TEMPLATE,'x':120,'y':80,'subpriority':28},
 'slot_profiles':'one model per first-free index0..63; preceding slots busy, this and later slots free',
 'resource_profile':'tile tag10027 at slot0 with tile start0; palette tag10027 at slot0 and reserved palette count0',
 'battle_profile':'attacker0,target1; trainer flag8; identity map0,1,2,3; non-Illusion status; artificial readable battler-data pointers with transformed species1',
 'alpha_profile':'artificial VCOUNT0 and DISPCNT0; deferred GPU update queue initially empty',
 'entry_producers_proven':False,
 'arbitrary_entry_states_covered':False,
}
CLAIMS={'proof_scope':'only_exact_seeded_cases_under_PRECONDITIONS','no_asynchronous_interference_assumed':True,'universal_entry_state_claimed':False,'constructor_to_synchronous_callback_lifetime_proven':True,'command_to_hit_conditional_path_proven':True,'prefix_alpha_handler_conditional_path_proven':True,'full_root_to_hit_proven':False,'current_acceptance_claimed':False,'newly_classified':0,'donor_eligible':False,'natural_battle_reachability_claimed':False}


def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()
def window(raw,a,n):return {'address':a,**ident(raw[a-BASE:a-BASE+n])}
def u32(raw,a):return int.from_bytes(raw[a-BASE:a-BASE+4],'little')
def fingerprint(raw,row):
 need(type(row.get('address'))is int and type(row.get('size'))is int and row['size']>0,'有限正幅ROM window')
 need(BASE<=row['address']<=BASE+len(raw)-row['size'],'ROM範囲内window')
 need(window(raw,row['address'],row['size'])=={k:row[k]for k in('address','size','sha256')},'全window identity')


def _seed(raw,index,command):
 need(type(index)is int and 0<=index<64,'有限64slot')
 lo=SPRITES+index*68
 ranges=[(0x03007800,0x03007F00),(lo,lo+68)]
 if command:ranges += [(CURSOR,CURSOR+4),(0x02037E36,0x02037E46)]
 m=Machine(raw,CONSTRUCTOR_CODE+(COMMAND_CODE if command else()),ranges)
 for i in range(64):m.seed(SPRITES+i*68+62,1,int(i<index))
 # 明示された局所入力条件。prefixからの生成を推論しない。
 for a,n,v in ((0x03000AE8,2,10027),(0x03000B68,2,0),(0x03003E98,1,0),(0x03000DE8,2,10027)):
  m.seed(a,n,v)
 if command:
  for a,n,v in((CURSOR,4,COMMAND),(0x02037E4E,1,0),(0x02037E4F,1,1),(0x02022AAC,4,8),(0x02023B36,4,0x03020100),(0x02023F78,4,0x0203D000),(0x0203D000,4,0x0203D100),(0x0203D102,2,1),(0x0203D106,2,1),(0x02023D5C,16,0)):
   m.seed(a,n,v)
 else:m.r[:4]=[TEMPLATE,120,80,28]
 return m


def same_slot_lifetime(writes,slot):
 """実inUse producer以降、一度でもclearされたslotの再利用を拒否する。"""
 flag=slot+62;states=[]
 for w in writes:
  if w['address']<=flag<w['address']+w['size']:
   states.append((w['value']>>(8*(flag-w['address'])))&1)
 need(1 in states,'実inUse producerが必要')
 suffix=states[states.index(1):]
 need(all(suffix),'inUse producer後のclear/reuseは禁止')
 return {'in_use_writes':len(states),'live_suffix_writes':len(suffix),'clear_after_producer':False}


def interpret_constructor(raw,index=0):
 m=_seed(raw,index,False);m.run(0x08006D68,CALLBACK)
 slot=SPRITES+index*68
 same_slot_lifetime(m.writes,slot)
 need(m.r[0]==slot and m.r[1]==CALLBACK|1 and m.read(slot+28,4)==CALLBACK|1,'同じ実作成slot・callback field28・引数r0')
 need(m.read(slot+62,1)&1==1,'実CreateSpriteAtのinUse producer')
 need(m.edges[-1]=={'address':0x081C7ACC,'target':CALLBACK},'constructor内同期BX r1')
 writes=[w for w in m.writes if slot<=w['address']<slot+68]
 callbacks=[w for w in writes if w['address']<=slot+28 and slot+28<w['address']+w['size']]
 need(callbacks[-1]=={'address':slot+28,'size':4,'value':CALLBACK|1},'全callee後まで最後のcallback writer一致')
 return m


def interpret_command(raw,index=0):
 m=_seed(raw,index,True);m.run(0x080720C0,0x080DF98E)
 slot=SPRITES+index*68
 same_slot_lifetime(m.writes,slot)
 need(m.read(CURSOR,4)==COMMAND+11,'実可変長command11byteを消費')
 need(m.read(0x02037E36,2)==24 and m.read(0x02037E38,2)==65524,'実2個のsigned引数')
 need(m.r[4]==slot and m.r[5]==0x02037E36,'callbackは同じslotと実引数配列を保持')
 need(m.read(slot+28,4)==CALLBACK|1,'全座標hook・calleeを経た同slot callback')
 need([t['address']for t in m.trace[-2:]]==[0x08074796,0x080DF98C],'callback BLの実returnと直後LDR')
 need(any(e=={'address':0x081C7ACC,'target':CALLBACK}for e in m.edges),'実同期callback consumer')
 need(any(c=={'address':0x080DF988,'target':0x08074770}for c in m.calls),'hit先頭の完全BL')
 return m


def interpret_alpha(raw):
 """prefix opcode12の実SetGpuReg二callをdeferred-update条件で全解釈する。"""
 a=0x081B498B
 need(u32(raw,0x08371F8C+12*4)==0x08072D85,'実alpha dispatch slot')
 m=Machine(raw,((0x08072D84,0x08072DB6),(0x08000A38,0x08000ABA)),((0x03007800,0x03007F00),(CURSOR,CURSOR+4),(0x03000050,0x03000054),(0x03000060,0x030000C1)))
 m.seed(CURSOR,4,a);m.seed(0x04000006,2,0);m.seed(0x04000000,2,0)
 for i in range(96):m.seed(0x03000060+i,1,255)
 initial=m.r[:];m.run(0x08072D84,0x01000000)
 need(m.read(CURSOR,4)==a+3,'alpha3byteの全cursor advance')
 need(m.read(0x03000050,2)==0x3F40 and m.read(0x03000052,2)==0x0808,'実BLDCNTと8/8 BLDALPHA shadow producer')
 need(m.read(0x03000060,1)==0x50 and m.read(0x03000061,1)==0x52 and m.read(0x030000C0,1)==0,'二つの実deferred queue登録とlock解除')
 need(m.r[4:12]==initial[4:12]and m.r[13]==initial[13],'alpha全returnのABI/SP保持')
 need([c['target']for c in m.calls]==[0x08000A38,0x08000A38],'両実GPU helperを省略しない')
 return m


def finite_selection(raw):
 need(u32(raw,0x0904A6D4+43*4)==PREFIX[0][0],'実MOVE_LEER43 table slot')
 need(u32(raw,0x08371F8C+2*4)==0x080720C1,'実opcode2 dispatch slot')
 need(u32(raw,TEMPLATE+20)==CALLBACK|1,'実template callback field20')
 for a,op,n in PREFIX:
  need(raw[a-BASE]==op,'有限prefix各opcode')
  need(n==({0:3,10:2,40:2,12:3,25:4}.get(op)if op!=2 else 7+2*raw[a-BASE+6]),'固定sourceの全command境界')
 need(u32(raw,COMMAND+1)==TEMPLATE and raw[COMMAND-BASE+5]==2 and raw[COMMAND-BASE+6]==2,'具体createsprite引数producer')
 return [window(raw,a,n)for a,_,n in PREFIX]+[window(raw,0x0904A6D4+43*4,4),window(raw,0x08371F8C+8,4),window(raw,TEMPLATE,24),window(raw,0x080DF988,6)]


def bind_sources(sources):
 need(set(sources)==set(SOURCE_EXPECTED),'固定公開source集合')
 for key,expected in SOURCE_EXPECTED.items():
  b=sources[key];need(ident(b)=={k:expected[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==expected['git_blob_sha'],'固定全source '+key)
 need(re.search(r'#define\s+MOVE_LEER\s+0x2B\b',sources['cfru-moves.h'].decode()),'固定source move43')
 need(re.search(r'\.equ\s+Template_Leer,\s*0x83C4DC4\b',sources['cfru-anim-defines.s'].decode()),'公開sourceの実JPtemplate')
 s=sources['pret-sprite.c'].decode();need('sprite->callback = template->callback;'in s and 'gSprites[i].callback(sprite);'in s,'producerと同期consumerの独立source')
 need('CreateSpriteAndAnimate('in sources['pret-battle-anim.c'].decode(),'実commandの独立source')
 return True


def summarize(m,index,kind):
 nonstack=[w for w in m.writes if not 0x03007800<=w['address']<0x03007F00]
 result={'slot':index,'kind':kind,'instruction_count':len(m.trace),'direct_call_count':len(m.calls),'indirect_edge_count':len(m.edges),'nonstack_write_count':len(nonstack),'trace_identity':ident(canonical(m.trace)),'write_identity':ident(canonical(nonstack)),'call_identity':ident(canonical(m.calls)),'edge_identity':ident(canonical(m.edges))}
 return result


def public_review(raw,sources):
 bind_sources(sources);roles={(w['address'],w['size']):w for w in finite_selection(raw)};models=[]
 for index in range(64):
  for kind,method in(('constructor',interpret_constructor),('command',interpret_command)):
   m=method(raw,index);models.append(summarize(m,index,kind))
   for w in m.trace+list(m.reads.values()):roles[w['address'],w['size']]=w
 alpha=interpret_alpha(raw);models.append(summarize(alpha,-1,'prefix_alpha'))
 for w in alpha.trace+list(alpha.reads.values())+[window(raw,0x08371F8C+12*4,4)]:roles[w['address'],w['size']]=w
 return {'schema_version':1,'status':'FINITE_LEER_CALLBACK_PARTIAL_ZERO_CLASSIFICATIONS','required_candidate':CANDIDATE,'source_bindings':SOURCE_EXPECTED,'hit_address':HIT,'models':models,'protected_windows':[roles[k]for k in sorted(roles)],'claims':CLAIMS,'preconditions':PRECONDITIONS,'unresolved_obligations':list(OBLIGATIONS)}


def _regions(raw,inherited,review,sources):
 need(ident(canonical(review))==REVIEW_ID,'独立固定の新scope review全体identity')
 need(review['required_candidate']==CANDIDATE,'current identityを診断と混同しない')
 rows=inherited.get('hits',[]);match=[h for h in rows if h['address']==HIT]
 need(len(match)==1 and match[0]['accepted']is False and not match[0]['owner_candidates']and match[0]['size']==4,'既存unknown1件だけ')
 fingerprint(raw,match[0])
 for role in review['protected_windows']:fingerprint(raw,role)
 need(review==public_review(raw,sources),'新129局所モデルを完全再計算')
 proof={'status':'PASS_LOCAL_LEER_CALLBACK_LIFETIME_NOT_ACCEPTED','count':0,'hit':HIT,'slot_models':64,'models':len(review['models']),'protected_read_window_count':len(review['protected_windows']),'protected_read_identity':ident(canonical(review['protected_windows'])),'review_identity':REVIEW_ID,'preconditions_identity':ident(canonical(PRECONDITIONS)),'claims':CLAIMS,'unresolved_obligations':list(OBLIGATIONS)}
 return [],proof


def protected_windows(review):
 need(ident(canonical(review))==REVIEW_ID,'独立固定reviewの全保護窓')
 return review['protected_windows']


def regions(raw,inherited,review,sources,root=None):
 need(ident(raw)==inherited['candidate']==CANDIDATE,'current0641全体束縛必須')
 return _regions(raw,inherited,review,sources)

# 生成後、独立review identityを固定する。
REVIEW_ID={'size': 175197, 'sha256': '08b21dc66aa215cbbb8c6680d48007846edb67776feb14e2ad7bec826ccd01a7'}
SOURCE_EXPECTED={'cfru-BPRJ.ld': {'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
                  'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
                  'size': 68505},
 'cfru-anim-defines.s': {'git_blob_sha': 'fc4168cbc9f43ef084afb04ff4ec8c81f9390592',
                         'sha256': '166cbae334e3c45cb0d694fb483b8ac13b9cc84dc4bd64eb8d04ee696c1e84e4',
                         'size': 33164},
 'cfru-moves.h': {'git_blob_sha': '444712bfec68c13fabffd3e167d380b6c23770ba',
                  'sha256': 'bc2ae17e444625fa2e1727d42c50a24f6758da26e44229a6f12a3afa3a275d79',
                  'size': 30601},
 'pret-battle-anim-script.inc': {'git_blob_sha': '15c48c39f5860efe132e782c22a6cedb0f8d5ac3',
                                 'sha256': 'cb193c567289983c26ed8acaa8dd64501c64c7e088e28995c49439333b52b27c',
                                 'size': 4279},
 'pret-battle-anim.c': {'git_blob_sha': '30f9a7ad2482d1767f5c70ee30a3c85528605bb3',
                        'sha256': '5883d9ee0483120ef67461952f5880499f322fb1c706cc213ca13c0c2b0e88c5',
                        'size': 46944},
 'pret-sprite.c': {'git_blob_sha': 'd0198d53004775c8664dcccf57833e178833776e',
                   'sha256': '2a804302eb5a89d31c3ec2f33dc645a80a0c645113d4b33b9bd571064c0286ae',
                   'size': 48783},
 'pret-sprite.h': {'git_blob_sha': '6a1b272119ce6e3a8dcf45adf2eef8923a6d5175',
                   'sha256': 'a77aa1c837dfb58cf60b3eac299c7cc29a23ce27735ba710b9e8eeed102bf773',
                   'size': 9368}}
