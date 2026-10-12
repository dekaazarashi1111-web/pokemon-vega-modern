"""残battle 10件の部分consumer証明。未接続rootを分類へ昇格させない。"""
from __future__ import annotations
import hashlib
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code

need,chunk,identity=d.need,d.chunk,d.identity
CURSOR=0x02023CD4
CALLBACK=0x03004FC4
PRIMARY=0x0903F450
HANDLER=0x091074D4
TARGET=0x02023CCC
ATTACKER=0x02023CCB
MOVE=0x02023CAA
MONS=0x02023B44
STATUS_COMMANDS=(0x090071F7,0x09007236,0x09007392,0x09007401)
UNPROVEN=(0x090023B8,0x0900360B,0x090036CD,0x09003C02,0x09005D94,0x090071FF,0x0900723E,0x09007271,0x0900739D,0x09007432)
# 末尾を先読みしてadvanceと見なさず、この実entryから全命令を解釈する。
CODE_RANGES=((0x091074D4,0x0910754A),(0x090D3D2C,0x090D3D8A),(0x090D6268,0x090D6290))
SOURCE_EXPECTED={
 'src/general_bs_commands.c':{'size':170849,'sha256':'ee23f75ab32b0f453128a9e5f9c7e77aba4a0de646e762a5fe821b61c1b20643'},
 'src/attackcanceler.c':{'size':43335,'sha256':'5344ba9c634786753235ffc6d72cc0c8554930a42991bc81aa04bb1b839f768f'},
 'BPRJ.ld':{'size':68505,'sha256':'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a'},
}

def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')

def interpret_status(raw,cursor,target_bank=1):
 """bank0..3/status2=0に限る実Thumbの有限経路。未知RAM/call/writeは拒否。"""
 need(cursor in STATUS_COMMANDS and target_bank in range(4),'閉じた四command・四bankのみ')
 need(d.u32(raw,PRIMARY+29*4)==HANDLER|1,'実opcode1D dispatch slot')
 need(chunk(raw,cursor,2)==bytes((29,0)),'実opcodeとBANK_TARGET selector')
 need(d.u32(raw,cursor+2)==0x01000000 and d.u32(raw,cursor+6)==0x09008E11,'対象四命令の全mask/全branch operand')
 regs=[f'incoming_r{i}' for i in range(16)];regs[13]=0x03007F00;regs[14]=0x01000001
 initial=regs[:];pc=HANDLER;memory={};stack={};writes=[];stack_writes=[];rom_reads={};trace=[];calls=[];call_returns=[];call_stack=[];flags=[False,False,False,False]
 def seed(a,z,v):
  for i in range(z):memory[a+i]=(v>>(8*i))&255
 seed(CURSOR,4,cursor);seed(CALLBACK,4,0x08015489);seed(TARGET,1,target_bank);seed(ATTACKER,1,0);seed(MOVE,2,1);seed(MONS+target_bank*88+80,4,0)
 def val(i):need(type(regs[i])is int,'未束縛incoming register依存');return regs[i]
 def nz(v):flags[0]=bool(v&0x80000000);flags[1]=v==0
 def arith(a,b,sub=False):
  v=(a-b if sub else a+b)&0xffffffff;nz(v);flags[2]=a>=b if sub else a+b>0xffffffff;flags[3]=bool(((a^b)&(a^v)if sub else~(a^b)&(a^v))&0x80000000);return v
 def read(a,z):
  if d.BASE<=a and a+z<=d.BASE+len(raw):
   b=chunk(raw,a,z);rom_reads[(a,z)]={'address':a,**identity(b)};return int.from_bytes(b,'little')
  if z==4 and a in stack:return stack[a]
  need(all(a+i in memory for i in range(z)),'未束縛RAM読出し: '+hex(a));return sum(memory[a+i]<<(8*i)for i in range(z))
 def write(a,z,v):
  need(a==CURSOR and z==4 and type(v)is int,'cursor以外の実memorywriteは未証明')
  writes.append({'address':a,'size':z,'value':v});seed(a,z,v)
 for _ in range(512):
  need(pc%2==0 and any(lo<=pc<hi for lo,hi in CODE_RANGES),'未知callee/コード境界')
  op=half(raw,pc);size=4 if op&0xf800==0xf000 else 2;trace.append({'address':pc,**identity(chunk(raw,pc,size))});nxt=pc+size
  if op&0xf800==0xf000:
   target=code.thumb_bl(chunk(raw,pc,4),pc);need(target in (0x090D3D2C,0x090D6268),'実calleeはbank resolverとsubstitute判定だけ');calls.append({'address':pc,'target':target});call_stack.append((pc+4,target,regs[4:12],regs[13]));regs[14]=(pc+4)|1;nxt=target
  elif op&0xf800==0x4800:regs[(op>>8)&7]=read(((pc+4)&~3)+(op&255)*4,4)
  elif op&0xf800==0x1800:
   a=val((op>>3)&7);b=(op>>6)&7 if op&0x400 else val((op>>6)&7);regs[op&7]=arith(a,b,bool(op&0x200))
  elif op&0xe000==0:
   kind=(op>>11)&3;s=(op>>6)&31;v=val((op>>3)&7);need(kind in(0,1),'限定unsigned shift')
   out=(v<<s)&0xffffffff if kind==0 else v>>(s or 32);regs[op&7]=out;nz(out)
   if kind==0 and s:flags[2]=bool((v>>(32-s))&1)
   elif kind==1:flags[2]=bool((v>>((s or 32)-1))&1)
  elif op&0xe000==0x2000:
   k=(op>>11)&3;r=(op>>8)&7;b=op&255
   if k==0:regs[r]=b;nz(b)
   elif k==1:arith(val(r),b,True)
   else:regs[r]=arith(val(r),b,k==3)
  elif op&0xfc00==0x4000:
   k=(op>>6)&15;r=op&7;s=(op>>3)&7
   if k==0:regs[r]=val(r)&val(s);nz(regs[r])
   elif k==8:nz(val(r)&val(s))
   elif k==10:arith(val(r),val(s),True)
   elif k==12:regs[r]=val(r)|val(s);nz(regs[r])
   elif k==13:regs[r]=(val(r)*val(s))&0xffffffff;nz(regs[r])
   else:need(False,'未対応ALU')
  elif op&0xfc00==0x4400:
   k=(op>>8)&3;r=(op&7)|((op>>4)&8);s=(op>>3)&15;need(k in(2,3),'MOV/BXのみ')
   if k==2:
    if r==15:nxt=val(s)&~1
    else:regs[r]=regs[s]
   else:nxt=val(s)&~1
  elif op&0xf000 in(0x6000,0x7000,0x8000):
   z=1 if op&0xf000==0x7000 else 2 if op&0xf000==0x8000 else 4;a=val((op>>3)&7)+((op>>6)&31)*z;r=op&7
   if op&0x800:regs[r]=read(a,z)
   else:write(a,z,val(r))
  elif op&0xf000==0x5000:
   k=(op>>9)&7;r=op&7;a=val((op>>3)&7)+val((op>>6)&7);need(k in(0,1,2,4,5,6),'限定register memory');z={0:4,1:2,2:1,4:4,5:2,6:1}[k]
   if k>=4:regs[r]=read(a,z)
   else:write(a,z,val(r))
  elif op&0xfe00==0xb400:
   names=[i for i in range(8)if op&(1<<i)]+([14]if op&0x100 else[]);regs[13]-=4*len(names)
   need(0x03007E00<=regs[13]<0x03007F00,'有限private stackのみ')
   for i,r in enumerate(names):
    a=regs[13]+4*i;stack[a]=regs[r];stack_writes.append({'address':a,'size':4,'value':regs[r]})
  elif op&0xfe00==0xbc00:
   names=[i for i in range(8)if op&(1<<i)]+([15]if op&0x100 else[])
   for i,r in enumerate(names):
    a=val(13)+4*i;need(a in stack,'実pushと対応するpop');v=stack.pop(a)
    if r==15:need(type(v)is int,'未束縛return');nxt=v&~1
    else:regs[r]=v
   regs[13]+=4*len(names)
  elif op&0xf000==0xd000:
   c=(op>>8)&15;need(c<14,'予約条件拒否');N,Z,C,V=flags;take=[Z,not Z,C,not C,N,not N,V,not V,C and not Z,not C or Z,N==V,N!=V,not Z and N==V,Z or N!=V][c];off=op&255;off-=256 if off&128 else 0
   if take:nxt=pc+4+2*off
  elif op&0xf800==0xe000:
   off=op&0x7ff;off-=0x800 if off&0x400 else 0;nxt=pc+4+2*off
  else:need(False,'未対応Thumb命令')
  if call_stack and nxt==call_stack[-1][0]:
   return_pc,entry,saved,sp=call_stack.pop();expected_return=target_bank if entry==0x090D3D2C else 0
   need(regs[4:12]==saved and regs[13]==sp and regs[0]==expected_return,'各callee return値・SP・callee-save保持')
   call_returns.append({'entry':entry,'return_to':return_pc,'result':regs[0]})
  if nxt==0x01000000:break
  pc=nxt
 else:need(False,'有限命令数超過')
 expected=[{'address':CURSOR,'size':4,'value':cursor+10}]
 need(writes==expected and read(CURSOR,4)==cursor+10,'全非stack writeと実後継一致')
 need(read(CALLBACK,4)==0x08015489 and not stack and not call_stack and regs[13]==initial[13] and regs[4:12]==initial[4:12],'callback/SP/callee-save全保持')
 need([x['target']for x in calls]==[0x090D3D2C,0x090D6268],'両実calleeをentryからreturnまで解釈')
 return {'command':cursor,'opcode':29,'entry':HANDLER,'target_bank':target_bank,'status2':0,'next_cursor':cursor+10,'writes':writes,'stack_writes':stack_writes,'calls':calls,'call_returns':call_returns,'instructions':trace,'rom_reads':[rom_reads[k]for k in sorted(rom_reads)],'callback_preserved':True,'callee_saved_registers_preserved':True,'full_root_chain_proven':False}

def partial_review(raw):
 models=[interpret_status(raw,a,b)for a in STATUS_COMMANDS for b in range(4)]
 return {'schema_version':1,'status':'PARTIAL_CONSUMER_ONLY_ZERO_NEW_CLASSIFICATIONS','diagnostic_candidate':identity(raw),'unproven_hit_addresses':list(UNPROVEN),'models':models,'newly_classified':0,'regions':[],'donor_leased':False,'indirect_reference_completeness_claimed':False,'full_story_reachability_claimed':False,'native_processes':0,'rom_writes':0}

def validate_partial_review(raw,review):
 need(review==partial_review(raw),'独立再計算した部分証明だけを受理')
 return []

def regions(*args,**kwargs):
 raise ValueError('残10の実root→全handler鎖は未証明。部分consumer証明から分類は禁止')


def bind_sources(sources):
 need(set(sources)==set(SOURCE_EXPECTED),'閉じた三つの公開source')
 for name,expected in SOURCE_EXPECTED.items():need(identity(sources[name])==expected,'完全source identity')
 text=sources['src/general_bs_commands.c'].decode()
 need('void atk1D_jumpifstatus2(void)' in text and 'MoveBlockedBySubstitute(gCurrentMove, gBankAttacker, bank)' in text,'状態branch consumerの公開source')
 return True


def diagnostic(raw,sources):
 bind_sources(sources)
 return partial_review(raw)


def current_partial_review(raw,sources):
 import pr16_dex_hof_reference_gaps as gaps
 need(identity(raw)==gaps.CANDIDATE,'現0641全体SHA必須。旧診断ROMを受入へ流用しない')
 return diagnostic(raw,sources)


def public_review(raw,sources):
 """最小公開review。命令byteは含めず、全roleのaddress/size/SHAを保持する。"""
 import json
 import pr16_dex_hof_reference_gaps as gaps
 full=diagnostic(raw,sources);windows={}
 def add(row):
  key=row['address'],row['size'];r={k:row[k]for k in('address','size','sha256')}
  need(key not in windows or windows[key]==r,'全有限roleの一意identity');windows[key]=r
 for a,z in [(PRIMARY+29*4,4)]+[(c,10)for c in STATUS_COMMANDS]:add({'address':a,**identity(chunk(raw,a,z))})
 models=[]
 for m in full['models']:
  for row in m['instructions']+m['rom_reads']:add(row)
  encoded=(json.dumps(m,sort_keys=True,separators=(',',':'))+'\n').encode()
  models.append({k:m[k]for k in('command','opcode','entry','target_bank','status2','next_cursor','writes','call_returns','callback_preserved','callee_saved_registers_preserved','full_root_chain_proven')}|{'instruction_count':len(m['instructions']),'stack_write_count':len(m['stack_writes']),'execution_identity':identity(encoded)})
 return {'schema_version':1,'status':full['status'],'required_candidate':gaps.CANDIDATE,'source_bindings':SOURCE_EXPECTED,'models':models,'protected_windows':[windows[k]for k in sorted(windows)],'newly_classified':0,'unproven_hit_addresses':list(UNPROVEN),'root_frontier':{'common_attackcanceler_closed':False,'leech_seed_root_closed':False},'donor_leased':False,'indirect_reference_completeness_claimed':False,'full_story_reachability_claimed':False,'native_processes':0,'rom_writes':0}


def measured_partial(raw,review,sources):
 """親の全candidate gate内、または明示旧診断だけで呼ぶ部分証明API。"""
 expected=public_review(raw,sources)
 need(review==expected,'全source/窓/実callee/値流れを独立再計算した最小reviewとの一致')
 return [],{'status':review['status'],'count':0,'consumer_models':16,'unproven_hit_addresses':list(UNPROVEN),'donor_leased':False,'full_root_chain_proven':False}


def current_partial(raw,review,sources):
 import pr16_dex_hof_reference_gaps as gaps
 need(identity(raw)==gaps.CANDIDATE,'現0641全体identity gate')
 return measured_partial(raw,review,sources)


def protected_windows(review):
 return list(review['protected_windows'])
