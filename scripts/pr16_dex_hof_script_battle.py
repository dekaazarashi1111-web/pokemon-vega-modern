"""effect20のbattle-script crossing一件を、実JP handlerの値流れまで閉じる。"""
from __future__ import annotations
import hashlib,re
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
KIND='battle_script_cross_field'
HITS=(0x09003299,)
UNPROVEN=(0x090023B8,0x0900360B,0x090036CD,0x09003C02,0x09005D94,0x090071FF,0x0900723E,0x09007271,0x0900739D,0x09007432)
CURSOR=0x02023CD4
PRIMARY=0x0903F450
SECONDARY=0x0903F850
EFFECTS=0x0903FA48
GRAMMAR={40:('goto',5,(1,)),42:('jumpifhalfword',12,(8,)),46:('setbyte',6,()),0xff09:('jumpifcounter',10,(6,))}
HANDLERS={40:0x08021E50,42:0x08021F10,46:0x08022178}
ROOT=0x09003284

def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')
def literal(raw,a,reg):
 op=half(raw,a);need(op&0xf800==0x4800 and(op>>8)&7==reg,'actual LDR literal register')
 return ((a+4)&~3)+(op&255)*4

def signed16(raw,a,mask,value):need(half(raw,a)&mask==value,'actual bounded opcode/register/offset semantics')

def source_bindings(review,sources):
 expected={'BPRJ.ld','asm_defines.s','battle_script_macros.s','assembly/data/battle_script_commands_table.s','assembly/data/move_effect_table.s','src/new_bs_commands.c','src/general_bs_commands.c'}
 need(set(review['source_bindings'])==expected,'closed seven public semantic sources')
 texts={}
 for name,exp in review['source_bindings'].items():
  raw=sources[exp['local']];need(identity(raw)=={k:exp[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==exp['git_blob_sha'],'complete pinned public source and Git identity');texts[name]=raw.decode()
 bprj=texts['BPRJ.ld'];defs=texts['asm_defines.s']
 need(re.search(r'^BattleScriptPushCursorAndCallback\s*=\s*0x801B434\s*\|\s*1;',bprj,re.M)and re.search(r'^gBattlescriptCurrInstr\s*=\s*0x2023CD4;',bprj,re.M),'exact JP callable callback API and cursor')
 need(re.search(r'^\.equ\s+CURRENT_MOVE,\s*gCurrentMove\s*$',defs,re.M)and re.search(r'^gCurrentMove\s*=\s*0x2023CAA;',bprj,re.M),'CURRENT_MOVE resolves through the exact JP source symbol')
 for name,value in [('STAT_CHANGE_BYTE',0x02023F3E)]:
  m=re.search(r'^\.equ\s+'+name+r',\s*(0x[0-9a-fA-F]+)',defs,re.M);need(m and int(m[1],16)==value,'source-named selected non-cursor operand')
 macro=re.sub(r'@[^\n]*','',texts['battle_script_macros.s'])
 for op,(name,size,ptrs)in GRAMMAR.items():
  bodies=re.findall(r'\.macro\s+'+name+r'(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S);need(len(bodies)==1,'one source serializer');fields=[];off=0
  for line in bodies[0].splitlines():
   line=line.strip()
   if not line:continue
   m=re.fullmatch(r'\.(byte|2byte|4byte|word)\s+(.+)',line);need(m is not None,'only direct finite source serializer fields')
   z={'byte':1,'2byte':2,'4byte':4,'word':4}[m[1]]
   for value in m[2].split(','):fields.append((off,z,value.strip()));off+=z
  prefix=[255,op&255]if op>255 else[op]
  need(off==size and[int(f[2],0)for f in fields[:len(prefix)]]==prefix,'actual source prefix and full size')
  need(tuple(o for o,z,name in fields if z==4 and name=='\\rom_address')==ptrs,'all complete script-control pointer fields')
 table=texts['assembly/data/battle_script_commands_table.s'].split('gBattleScriptingCommandsTable:',1)[1];one,two=table.split('gBattleScriptingCommandsTable2:',1)
 words=lambda s:re.findall(r'^\s*\.word\s+([^\s@]+)',s,re.M)
 first,second=words(one),words(two);need(len(first)==256 and len(second)==57,'finite dispatch counts')
 need([first[i]for i in(40,42,46,99,255)]==['0x8021E51','0x8021F11','0x8022179','atk63_jumptocalledmove','atkFF_callsecondarytable']and second[9]=='atkFF09_jumpifcounter','exact actual opcode consumers')
 effect=texts['assembly/data/move_effect_table.s'].split('gBattleScriptsForMoveEffects:',1)[1].split('gSetStatusMoveEffects:',1)[0]
 need(len(words(effect))==256,'fixed u8 effect table length')
 return True


def instruction_writes(op):
 """値保持確認に必要なARMv4T Thumb register write集合。未知形式は拒否。"""
 if op&0xf800==0x4800:return{(op>>8)&7}
 if op&0xe000==0x0000:return{op&7}
 if op&0xe000==0x2000:return set()if op&0xf800==0x2800 else{(op>>8)&7}
 if op&0xfc00==0x4000:return set()if(op>>6)&15 in(8,10,11)else{op&7}
 if op&0xfc00==0x4400:return set()if(op>>8)&3 in(1,3)else{(op&7)|((op>>4)&8)}
 if op&0xf000 in(0x6000,0x7000,0x8000):return{op&7}if op&0x0800 else set()
 if op&0xf000==0x5000:return{op&7}if(op>>9)&7>=3 else set()
 if op&0xf000==0xd000 or op&0xf800==0xe000:return set()
 if op&0xfe00==0xb400:return set()
 if op&0xfe00==0xbc00:return{i for i in range(8)if op&(1<<i)}
 if op&0xf800==0xf000:return{0,1,2,3}
 need(False,'unreviewed instruction in preserved cursor-register path')


def root_consumers(raw,review):
 d.signed(raw,review['root_windows']);d.signed(raw,review['root_literals']);d.signed(raw,review['handler_slots']);d.signed(raw,review['root_paths'])
 expected={0x0801B468:CURSOR,0x0801B470:0x03004FC4,0x0801B474:0x08015489,0x080154AC:PRIMARY,0x080154B0:CURSOR,0x0911AAA4:CURSOR,0x0911AAA8:SECONDARY,0x09107EBC:CURSOR,0x09107EC8:0x02023CAA,0x09131A6C:0x090421F4,0x09131A70:EFFECTS,0x0911B0E0:CURSOR}
 need({r['address']for r in review['root_literals']}==set(expected),'all and only finite root literals')
 for r in review['root_literals']:need(r['size']==4 and r['value']==d.u32(raw,r['address'])==expected[r['address']],'actual same-cursor/root table value')
 for pc,reg,address in [(0x0801B43C,0,0x0801B468),(0x0801B456,1,0x0801B470),(0x0801B45C,0,0x0801B474),(0x08015492,1,0x080154AC),(0x08015494,0,0x080154B0),(0x0911AA8C,3,0x0911AAA4),(0x0911AA98,3,0x0911AAA8),(0x09107E82,4,0x09107EBC),(0x09107E94,5,0x09107EC8),(0x09131942,1,0x09131A6C),(0x09131948,2,0x09131A70),(0x0911AF6E,6,0x0911B0E0)]:need(literal(raw,pc,reg)==address,'actual selected literal load')
 # Callback registration and actual primary/secondary table consumer data-flow.
 semantic={0x0801B43E:0x6004,0x0801B458:0x6808,0x0801B45A:0x6010,0x0801B45E:0x6008,0x08015496:0x6800,0x08015498:0x7800,0x0801549A:0x0080,0x0801549C:0x1840,0x0801549E:0x6800,0x081C7AC8:0x4700,0x0911AA90:0x681A,0x0911AA92:0x1C51,0x0911AA94:0x6019,0x0911AA96:0x7852,0x0911AA9A:0x0092,0x0911AA9C:0x58D3,0x0911DC4C:0x4718,0x09107EAE:0x8828,0x09107EB8:0x6020,0x0913193E:0x0043,0x09131940:0x181B,0x09131944:0x009B,0x09131946:0x5C5B,0x0913194A:0x009B,0x0913194C:0x5898,0x0913194E:0x4770}
 for a,value in semantic.items():signed16(raw,a,0xffff,value)
 for a,to in [(0x080154A0,0x081C7AC8),(0x0911AA9E,0x0911DC4C),(0x09107EB4,0x09131928)]:need(code.thumb_bl(chunk(raw,a,4),a)==to,'actual bounded dispatch/helper call')
 need(half(raw,0x09131934)&0xff00==0xd800 and 0x09131934+4+2*(half(raw,0x09131934)&255)==0x0913193E,'actual unsigned fallback edge into u8 effect-root consumer')
 entries=[0x0801B434,0x08015488,0x0911AA8C,0x09107E80,0x09131928]
 need([p['entry']for p in review['root_paths']]==entries,'closed callable/dispatch/fallback paths')
 for path in review['root_paths']:gaps.thumb_path(raw,path['instructions'],path['entry'])
 # The selected atk63 code must keep r4 as CURSOR across ABI calls until STR r0,[r4].
 selected=review['root_paths'][3]['instructions'];need(selected[-1]['address']==0x09107EB8,'root effect consumer ends at actual cursor store')
 need(all(4 not in instruction_writes(half(raw,p['address']))for p in selected if 0x09107E82<p['address']<0x09107EB8),'complete cursor base register survives every intermediate instruction')
 slots={(r['table'],r['opcode']):r for r in review['handler_slots']};exp={(0,i):(PRIMARY+4*i,a|1)for i,a in HANDLERS.items()};exp.update({(0,99):(PRIMARY+4*99,0x09107E81),(0,255):(PRIMARY+4*255,0x0911AA8D),(1,9):(SECONDARY+4*9,0x0911AF69)})
 need(set(slots)==set(exp),'closed selected primary/extended handler roles')
 for key,(address,value)in exp.items():r=slots[key];need(r['address']==address and r['size']==4 and r['target']==d.u32(raw,address)==value,'complete exact actual handler slot')
 need(3 not in instruction_writes(half(raw,0x0911AA8E)),'secondary dispatcher cursor base survives its prologue')
 need(half(raw,0x0911AF78)==0x6833 and code.thumb_bl(chunk(raw,0x0911AF74,4),0x0911AF74)==0x090D3D2C,'FF09 reloads cursor through its ABI-preserved r6 after bank resolver')
 need(all(3 not in instruction_writes(half(raw,a))for a in range(0x0911AF7A,0x0911AF86,2)),'FF09 complete pointer-read slice retains its exact cursor base')
 # The final command is not followed; prove FF09's pointer field is all +6..9, separately.
 for a,off,reg in [(0x0911AF7A,6,1),(0x0911AF7C,5,2),(0x0911AF82,7,2),(0x0911AF84,8,4)]:
  op=half(raw,a);need(op&0xf800==0x7800 and(op>>6)&31==off and(op>>3)&7==3 and op&7==reg,'FF09 receives cursor+1 and reads all four pointer operand bytes')
 return True


def thumb_handler(raw,entry,cursor,ram_value=None):
 """短いBLなしJP handlerの限定Thumb値流れ。未対応命令/不明RAM/任意writeはfail-closed。"""
 regs=[None]*16;regs[13]=0x03007F00;regs[14]=0x01000000;pc=entry;stack=[];flags=[False,False,False,False];memory={};writes=[];reads={};trace=[]
 def reg(i):
  need(type(regs[i])is int,'native continuation may not depend on unconstrained incoming registers');return regs[i]
 def nz(value):flags[0]=bool(value&0x80000000);flags[1]=value==0
 def arithmetic(a,b,subtract=False):
  result=(a-b if subtract else a+b)&0xffffffff;nz(result)
  flags[2]=a>=b if subtract else a+b>0xffffffff
  flags[3]=bool(((a^b)&(a^result) if subtract else ~(a^b)&(a^result))&0x80000000)
  return result
 def write_memory(a,z,value,track=True):
  if track:need(a==CURSOR and z==4 or a==0x02023F3E and z==1,'only exact cursor word or source STAT_CHANGE_BYTE destination');writes.append(dict(address=a,size=z,value=value&((1<<(8*z))-1)))
  for i in range(z):memory[a+i]=(value>>(8*i))&255
 def read_memory(a,z):
  if d.BASE<=a and a+z<=d.BASE+len(raw):
   b=chunk(raw,a,z);reads[(a,z)]=dict(address=a,**identity(b));return int.from_bytes(b,'little')
  need(all(a+i in memory for i in range(z)),'no unexplained native RAM input');return sum(memory[a+i]<<(8*i)for i in range(z))
 write_memory(CURSOR,4,cursor,False)
 if ram_value is not None:write_memory(0x02023CAA,2,ram_value,False)
 def compare(a,b):
  arithmetic(a,b,True)
 for _ in range(256):
  need(pc%2==0 and d.BASE<=pc<d.BASE+len(raw),'finite aligned actual native handler control flow')
  op=half(raw,pc);trace.append(dict(address=pc,**identity(chunk(raw,pc,2))));nxt=pc+2
  if op&0xf800==0x4800:regs[(op>>8)&7]=read_memory(((pc+4)&~3)+(op&255)*4,4)
  elif op&0xf800==0x1800:
   a=reg((op>>3)&7);b=(op>>6)&7 if op&0x400 else reg((op>>6)&7);regs[op&7]=arithmetic(a,b,bool(op&0x200))
  elif op&0xe000==0:
   kind=(op>>11)&3;shift=(op>>6)&31;src=reg((op>>3)&7);need(kind<2,'only reviewed unsigned shifts')
   regs[op&7]=((src<<shift)&0xffffffff)if kind==0 else(src>>(shift or 32));nz(regs[op&7])
   if kind==0 and shift:flags[2]=bool((src>>(32-shift))&1)
   elif kind==1:flags[2]=bool((src>>((shift or 32)-1))&1)
  elif op&0xe000==0x2000:
   kind=(op>>11)&3;r=(op>>8)&7;imm=op&255
   if kind==0:regs[r]=imm;nz(imm)
   elif kind==1:compare(reg(r),imm)
   elif kind==2:regs[r]=arithmetic(reg(r),imm)
   else:regs[r]=arithmetic(reg(r),imm,True)
  elif op&0xfc00==0x4000:
   kind=(op>>6)&15;r=op&7;s=(op>>3)&7
   if kind==0:regs[r]=reg(r)&reg(s);nz(regs[r])
   elif kind==10:compare(reg(r),reg(s))
   elif kind==12:regs[r]=reg(r)|reg(s);nz(regs[r])
   else:need(False,'unsupported ALU in short rooted handler')
  elif op&0xfc00==0x4400:
   kind=(op>>8)&3;r=(op&7)|((op>>4)&8);s=(op>>3)&15
   need(kind in(2,3),'only MOV pc or BX return')
   if kind==2:
    if r==15:nxt=reg(s)
    else:regs[r]=reg(s)
   else:
    if reg(s)==0x01000000:break
    nxt=reg(s)&~1
  elif op&0xf000 in(0x6000,0x7000,0x8000):
   z=1 if op&0xf000==0x7000 else 2 if op&0xf000==0x8000 else 4;a=reg((op>>3)&7)+((op>>6)&31)*z;r=op&7
   if op&0x800:regs[r]=read_memory(a,z)
   else:write_memory(a,z,reg(r))
  elif op&0xf000==0x5000:
   kind=(op>>9)&7;r=op&7;a=reg((op>>3)&7)+reg((op>>6)&7);need(kind in(0,1,2,4,5,6),'no signed/unreviewed register memory operation');z={0:4,1:2,2:1,4:4,5:2,6:1}[kind]
   if kind>=4:regs[r]=read_memory(a,z)
   else:write_memory(a,z,reg(r))
  elif op&0xfe00==0xb400:
   names=[r for r in range(8)if op&(1<<r)]+([14]if op&0x100 else[]);stack.append([(r,regs[r])for r in names])
  elif op&0xfe00==0xbc00:
   names=[r for r in range(8)if op&(1<<r)]+([15]if op&0x100 else[])
   flat=[value for frame in reversed(stack) for _,value in frame];need(len(flat)>=len(names),'balanced actual short handler stack')
   values=flat[:len(names)];flat=flat[len(names):];stack=[[(0,value)for value in flat]]if flat else[]
   for r,value in zip(names,values):
    if r==15:need(value==0x01000000,'matched source handler return');return read_memory(CURSOR,4),writes,trace,list(reads.values())
    regs[r]=value
  elif op&0xf000==0xd000:
   cond=(op>>8)&15;need(cond<14,'no reserved conditional instruction');N,Z,C,V=flags
   take=[Z,not Z,C,not C,N,not N,V,not V,C and not Z,not C or Z,N==V,N!=V,not Z and N==V,Z or N!=V][cond]
   off=op&255;off-=256 if off&128 else 0
   if take:nxt=pc+4+2*off
  elif op&0xf800==0xe000:
   off=op&0x7ff;off-=0x800 if off&0x400 else 0;nxt=pc+4+2*off
  else:need(False,'opaque call/unknown instruction cannot authorize script continuation')
  pc=nxt
 else:need(False,'finite native interpreter bound')
 return read_memory(CURSOR,4),writes,trace,list(reads.values())


def command(raw,c):
 a=c['address'];op=chunk(raw,a,1)[0];op=0xff00|chunk(raw,a+1,1)[0]if op==255 else op
 need(op in GRAMMAR and c['opcode']==op and c['size']==GRAMMAR[op][1],'exact whole encoded source command');d.signed(raw,c)
 need(c['control_fields']==[dict(address=a+o,size=4,value=d.u32(raw,a+o))for o in GRAMMAR[op][2]],'every full control pointer field retained')
 if op==46:need(d.u32(raw,a+1)==0x02023F3E,'source STAT_CHANGE_BYTE only, no cursor/dispatch alias')
 if op==42:need(chunk(raw,a+1,1)[0]==0 and d.u32(raw,a+2)==0x02023CAA,'selected EQUALS CURRENT_MOVE predicate and read operand')
 return op


def native_model(raw,c,edge):
 op=command(raw,c);need(op in HANDLERS,'only fully interpreted native continuation handlers')
 a=c['address'];value=None;expected_writes=[]
 if op==42:
  compare=int.from_bytes(chunk(raw,a+6,2),'little');value=compare if edge=='taken'else compare^1;target=d.u32(raw,a+8)if edge=='taken'else a+12
  expected_writes=[dict(address=CURSOR,size=4,value=a+12)]+([dict(address=CURSOR,size=4,value=target)]if edge=='taken'else[])
 elif op==46:
  need(edge=='next','setbyte has no arbitrary control edge');target=a+6;expected_writes=[dict(address=0x02023F3E,size=1,value=chunk(raw,a+5,1)[0]),dict(address=CURSOR,size=4,value=target)]
 else:
  need(edge=='taken','goto has no implicit fallthrough');target=d.u32(raw,a+1);expected_writes=[dict(address=CURSOR,size=4,value=target)]
 result,writes,instructions,reads=thumb_handler(raw,HANDLERS[op],a,value)
 need(result==target and writes==expected_writes,'actual native value-flow, all write destinations/widths, and exact script successor')
 return dict(command=a,opcode=op,edge=edge,entry=HANDLERS[op],next_cursor=target,writes=writes,instructions=instructions,rom_reads=reads)


def geometry(e,hit):
 need(e['hit']==hit and hit['address']==HITS[0]and hit['size']==4,'closed one exact inherited hit')
 left,right=e['crossing_commands'];need((left['address'],left['size'],left['opcode'])==(0x09003296,5,40)and(right['address'],right['size'],right['opcode'])==(0x0900329B,10,0xff09),'minimal complete adjacent goto and FF09 commands')
 need(hit['address']==left['address']+3==right['address']-2,'only full-left-pointer upper2 and FF09 opcode2')
 need(left['control_fields']==[e['whole_left_pointer']]and e['whole_left_pointer']['address']==left['address']+1 and e['whole_left_pointer']['size']==4,'retain complete distinct left pointer field')
 need([(p['address'],p['size'])for p in right['control_fields']]==[(right['address']+6,4)],'retain complete right pointer separately from its opcode')
 need(not d.DONOR_LO<=d.canonical(e['whole_left_pointer']['value'])<d.DONOR_HI,'actual full goto pointer is outside donor')
 need(e['root_verified']is True and e['whole_script_range_classified']is False and e['full_story_reachability_claimed']is False,'no blanket typing or runtime reachability claim')
 return True


def protected_windows(review):
 out={}
 def visit(x):
  if isinstance(x,dict):
   if{'address','size','sha256'}<=x.keys():
    k=x['address'],x['size'];r={name:x[name]for name in('address','size','sha256')};need(k not in out or out[k]==r,'same whole bytes for shared finite role');out[k]=r
   for y in x.values():visit(y)
  elif isinstance(x,list):
   for y in x:visit(y)
 visit(review);return[out[k]for k in sorted(out)]


def measured_regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and len(review['rows'])==1,'closed one-row classifier')
 source_bindings(review,sources);root_consumers(raw,review)
 row=review['rows'][0];hit=row['hit'];need(hit==next(h for h in inherited['hits']if h['address']==HITS[0])and not hit['accepted']and not hit['owner_candidates'],'entire exact inherited unknown row retained');d.signed(raw,hit)
 e=row['evidence'];geometry(e,hit);root=e['root'];slot=root['slot'];d.signed(raw,slot)
 need(root['table']==EFFECTS and root['index']==20 and root['entry']==ROOT and slot['address']==EFFECTS+20*4 and slot['size']==4 and d.u32(raw,slot['address'])==ROOT,'actual finite u8 effect20 root')
 commands=e['commands'];need([c['address']for c in commands]==[ROOT,0x0900328A,0x09003296,0x0900329B],'closed exact native-proven script graph')
 need(e['crossing_commands']==commands[-2:],'same complete minimal crossing nodes')
 for c in commands:command(raw,c)
 models=[native_model(raw,commands[0],'next'),native_model(raw,commands[1],'next'),native_model(raw,commands[1],'taken'),native_model(raw,commands[2],'taken')]
 need(models==e['native_models'],'same independently re-executed finite semantic witnesses')
 need([m['next_cursor']for m in models[:3]]==[commands[1]['address'],commands[2]['address'],commands[3]['address']],'both crossing commands have actual nonopaque native successor roots')
 return[d.TypedRegion(hit['address'],hit['address']+4,KIND,e)],dict(status='PASS_ONE_NATIVE_PROVEN_BATTLE_SCRIPT_CROSS_FIELD',count=1,unproven_hit_addresses=list(UNPROVEN),donor_leased=False,full_story_reachability_claimed=False,indirect_reference_completeness_claimed=False)


def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'complete current0641 required before acceptance')
 return measured_regions(raw,inherited,review,sources)
