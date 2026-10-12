"""実special072 producerと登録opcode49からDancer最小6byteへの独立有限意味モデル。"""
import copy, hashlib, json, re
import ast, csv, io
from pathlib import Path
import pr16_dex_hof_callback_party as p
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as live_engine
import pr16_dex_hof_animation_registered_roots as machine_engine
import pr16_dex_hof_critical_move_list_roots as critical
from pr16_dex_hof_extra_roots import encoded, exact
import pr16_dex_hof_donor as d
import pr16_dex_hof_toxic_orb_roots as layout_engine

need, identity, chunk = p.need, p.identity, p.chunk
HIT, MINIMUM, PRODUCER, ENTRY = 0x090E20AB, 0x090E20AA, 0x0910333C, 0x090DF7A0
CIRCUS, FLAGS, BIT_TABLE = 0x0203DFBC, 0x02022AAC, 0x0821AE68
ATTACKER, TARGET, SCRIPTING, CURSOR = 0x02023CCB, 0x02023CCC, 0x02023F24, 0x02023CD4
NEWBS, BSTRUCT, HITMARKER, STATUS3 = 0x0203DFB0, 0x02023F48, 0x02023D30, 0x02023D5C
CONTEXT, BATTLE_CONTEXT, SCRIPT = 0x02010000, 0x02012000, 0x02014000
STOP_PRODUCER = 0xFFFFFFF0
SPECS=[]
def block(a, specs):
 for k,*x in specs:
  if k=='regmem' and type(x[0]) is bool:
   ld,width,rd,rb,ro=x;x=[{(True,'word'):'ldr',(True,'half'):'ldrh',(True,'byte'):'ldrb',(False,'word'):'str',(False,'half'):'strh',(False,'byte'):'strb'}[ld,width],rd,rb,ro]
  if k=='alu' and x[0] in ('tst','sbc','adc','bic','eor'):k='alu_ext'
  SPECS.append((a,k,tuple(x)));a+=4 if k=='call' else 2
 return a

# frontier.c:全32bitの既存flag走査、71以上のstreakに対応するdefault枝。
block(PRODUCER,[('push',240,True),('movhi',7,10),('movhi',14,11),('movhi',6,9),('movhi',5,8),
 ('imm','mov',2,1),('imm','mov',1,128),('push',224,True),('literal',3,0x091034C8),
 ('mem',False,'half',2,3,0),('literal',3,0x091034CC),('imm','mov',4,0),('mem',True,'word',0,3,0),
 ('imm','mov',7,0),('literal',3,0x091034D0),('spadd',-28),('shift','lsl',1,1,24),('jump',0x09103362),
 ('imm','add',7,1),('mem',True,'word',2,3,0),('alu','tst',2,0),('branch',0,0x0910336E),
 ('imm','add',4,1),('shift','lsl',4,4,24),('shift','lsr',4,4,24),('imm','add',3,4),
 ('compare',2,1),('branch',1,0x09103360),('imm','mov',3,0),('spmem',False,3,0),
 ('literal',3,0x091034D4),('imm','mov',0,0),('shift','lsl',2,3,0),('shift','lsl',1,3,0),
 ('call',0x092D0AC8),('imm','cmp',0,70),('branch',8,0x091033B0)])
block(0x091033A2,[('spadd',28),('pop',240,False),('movhi',11,7),('movhi',10,6),('movhi',9,5),('movhi',8,4),('pop',240,True)])
block(0x091033B0,[('imm','mov',3,1),('imm','mov',2,5),('spmem',False,3,20),('spmem',False,3,16),
 ('compare',4,2),('branch',2,0x091033A2),('imm','mov',2,248),('literal',3,0x091034CC),
 ('mem',True,'word',3,3,0),('shift','lsl',2,2,1),('alu','and',2,3),('movhi',9,2),
 ('imm','mov',2,15),('imm','mov',0,4),('alu','and',2,3),('movhi',11,2),('call',0x091269B8),
 ('shift','lsl',0,0,24),('shift','lsr',3,0,24),('movhi',10,3),('imm','cmp',3,1),('branch',0,0x091033EE)])
block(0x091033EE,[('imm','mov',0,3),('call',0x091269B8),('literal',3,0x091034E0),
 ('shift','lsl',4,3,0),('spmem',False,0,12),('imm','add',7,1),('call',0x0910360E),
 ('literal',3,0x091034CC),('shift','lsl',1,7,0),('mem',True,'word',5,3,0),('call',0x09099E04),
 ('imm','mov',3,255),('alu','and',1,3),('literal',3,0x091034D0),('shift','lsl',1,1,2),
 ('add',6,1,3),('mem',True,'word',3,6,0),('shift','lsl',0,3,0),('alu','and',0,5),
 ('alu','tst',3,5),('branch',1,0x091033FC),('movhi',2,9),('imm','cmp',2,0),('branch',0,0x0910342C),
 ('imm','mov',2,248),('shift','lsl',2,2,1),('alu','tst',3,2),('branch',1,0x091033FC),
 ('movhi',2,11),('imm','cmp',2,0),('branch',0,0x09103436),('shift','lsl',2,3,28),('branch',1,0x091033FC),
 ('movhi',2,10),('imm','cmp',2,0),('branch',0,0x09103440),('shift','lsl',2,3,13),('branch',4,0x091033FC),
 ('spmem',True,2,12),('imm','cmp',2,3),('branch',9,0x0910344A),('shift','lsl',2,3,12),('branch',4,0x091033FC),
 ('spmem',True,2,16),('imm','cmp',2,0),('branch',1,0x09103460)])
block(0x09103460,[('imm','mov',2,128),('shift','lsl',2,2,17),('compare',3,2),('branch',3,0x0910346E),
 ('spmem',True,2,20),('shift','lsl',2,2,31),('branch',5,0x091033FC),('imm','mov',2,248),
 ('shift','lsl',2,2,1),('shift','lsl',4,1,0),('alu','tst',3,2),('branch',0,0x091034A0)])
block(0x091034A0,[('alu','orr',5,3),('literal',3,0x091034CC),('mem',False,'word',5,3,0),
 ('literal',3,0x091034E8),('literal',0,0x091034EC),('regmem',True,'word',1,3,4),
 ('literal',3,0x091034F0),('call',0x0910360C),('imm','mov',2,0),('literal',3,0x091034C8),
 ('mem',False,'half',2,3,0),('jump',0x091033A2)])
block(0x0910360C,[('bx',3),('bx',4)])
# unsigned moduloの実中継。r0=剰余をr1へ移すcompiler ABIを実行する。
block(0x09099E04,[('push',0,True),('call',0x09099E0E),('addi',1,0,0),('pop',0,True),
 ('literal',3,0x09099E5C),('bx',3)])

# Stage77/72の独立手書きassembly。source macrosから意味を固定。
block(ENTRY,[('literal',3,0x090DF7A4),('bx',3)])
block(0x095D5A9C,[('literal',3,0x095D5AB4),('mem',True,'word',3,3,0),('shift','lsl',3,3,5),
 ('branch',5,0x095D5AB0),('literal',3,0x095D5AB8),('mem',True,'word',3,3,0),('imm','cmp',3,0),
 ('branch',5,0x095D5AB0),('literal',3,0x095D5ABC),('bx',3),('literal',3,0x095D5AC0),('bx',3)])
block(0x095343A4,[('push',240,True),('movhi',14,11),('movhi',6,9),('movhi',7,10),
 ('push',8,False),('literal',3,0x095343B8),('movhi',12,3),('pop',8,False),('bx',12)])
# cmd49.c:currentMove/arg1/arg2/ITEM_EFFECT、非bounce、HitMarker unableなし、state48。
block(0x090DF7A8,[('movhi',5,8),('push',224,True),('literal',4,0x090DFB18),('mem',True,'byte',3,4,0),
 ('spadd',-100),('spmem',False,3,32),('literal',3,0x090DFB1C),('mem',True,'half',1,3,0),
 ('movhi',12,1),('spmem',False,3,56),('literal',3,0x090DFB20),('addhi',3,12),('subi',2,3,1),
 ('alu','sbc',3,2),('alu','neg',3,3),('alu','and',1,3),('literal',3,0x090DFB24),
 ('spmem',False,3,44),('mem',True,'word',3,3,0),('mem',True,'byte',2,3,1),('mem',True,'byte',3,3,2),
 ('spmem',False,3,24),('literal',3,0x090DFB28),('mem',True,'byte',0,3,0),('movhi',11,3),
 ('spmem',False,2,12),('spmem',False,4,16),('spmem',False,1,60),('call',0x090D3FEC),
 ('literal',3,0x090DFB2C),('mem',True,'word',2,3,0),('movhi',9,3),('imm','mov',3,176),
 ('shift','lsl',3,3,1),('regmem',True,'byte',3,2,3),('spmem',False,0,68),('shift','lsl',3,3,30),
 ('branch',0,0x090DF86E)])
block(0x090DF86E,[('movhi',1,11),('literal',3,0x090DFB30),('mem',True,'byte',1,1,0),
 ('spmem',False,3,52),('imm','add',1,100),('mem',True,'word',3,3,0),('shift','lsl',1,1,1),
 ('add',1,3,1),('spmem',False,1,64),('jump',0x090DF806)])
block(0x090DF806,[('mem',True,'byte',3,3,19),('spmem',False,3,48),('literal',3,0x090DFB34),
 ('spmem',False,3,28),('mem',True,'word',3,3,0),('shift','lsl',3,3,12),('branch',5,0x090DF838)])
block(0x090DF838,[('spmem',True,3,12),('imm','cmp',3,5),('branch',1,0x090DF842)])
block(0x090DF842,[('literal',3,0x090DFB3C),('movhi',10,3),('mem',True,'byte',3,3,20),
 ('imm','cmp',3,0),('branch',1,0x090DF85A)])
block(0x090DF85A,[('movhi',8,9),('movhi',9,11),('imm','cmp',3,50),('branch',9,0x090DF866)])
block(0x090DF866,[('literal',1,0x090DFB40),('shift','lsl',2,3,2),('regmem',True,'word',2,1,2),('movhi',15,2)])
# cmd49.c state48。count不一致、既存DancerInProgress=trueの短絡を実命令で選ぶ。
block(0x090E010A,[('movhi',3,8),('imm','mov',4,167),('mem',True,'word',3,3,0),
 ('literal',5,0x090E01C4),('shift','lsl',4,4,1),('regmem',True,'byte',1,3,4),
 ('mem',True,'byte',2,5,0),('compare',1,2),('branch',1,0x090E0120),('call',0x090E1B02),
 ('imm','mov',7,177),('imm','mov',6,8),('shift','lsl',7,7,1),('regmem',True,'byte',2,3,7),
 ('spmem',True,1,12),('alu','and',2,6),('imm','cmp',1,4),('branch',1,0x090E0134),
 ('call',0x090E1304),('imm','cmp',2,0),('branch',1,0x090E013C),('call',0x090E12E6),
 ('literal',0,0x090E0194),('shift','lsl',5,0,0),('imm','mov',2,167),('imm','mov',4,88),
 ('movhi',12,5),('shift','lsl',2,2,1),('regmem',True,'byte',2,3,2),('add',1,3,2),
 ('imm','add',1,121),('imm','add',1,255),('mem',True,'byte',1,1,0),('spmem',False,0,20),
 ('shift','lsl',0,4,0),('alu','mul',0,1),('addhi',0,12),('mem',True,'half',5,0,56),
 ('imm','cmp',5,217),('branch',1,0x090E0164),('call',0x090E205A)])
# 生存、absent、同turn attacker比較、実gBankAttacker writer。
block(0x090E205A,[('mem',True,'half',0,0,40),('imm','cmp',0,0),('branch',1,0x090E2064),
 ('call',0x090E0164),('literal',5,0x090E225C),('movhi',12,5),('shift','lsl',0,1,2),
 ('literal',5,0x090E2280),('addhi',0,12),('mem',True,'byte',5,5,0),('mem',True,'word',0,0,0),
 ('alu','tst',0,5),('branch',0,0x090E207A),('call',0x090E0164),('imm','mov',5,80),
 ('imm','add',5,255),('regmem',True,'byte',6,3,5),('shift','lsl',6,6,28),('shift','lsr',6,6,28),
 ('compare',6,1),('branch',1,0x090E208C),('call',0x090E0164),('movhi',11,9),('movhi',3,11),
 ('mem',False,'byte',1,3,0),('literal',3,0x090E2270),('spmem',False,3,36),('mem',True,'half',0,3,0),
 ('literal',3,0x090E2284),('mem',True,'word',3,3,0),('movhi',9,8),('shift','lsl',3,3,31),
 ('branch',5,0x090E20AE),('imm','mov',3,2),('alu','eor',3,1),('compare',6,3),
 ('branch',1,0x090E20AE),('call',0x090E2E94),('spmem',True,3,36)])
# 遠方outlined helper。base target API戻り0条件からCurrentTurnTargetの生存を実読取。
block(0x090E2E94,[('call',0x090D5014),('imm','cmp',0,0),('branch',0,0x090E2EA0),
 ('call',0x090E20AE),('movhi',3,8),('mem',True,'word',3,3,0),('regmem',True,'byte',0,3,5),
 ('spmem',True,3,20),('movhi',12,3),('shift','lsr',0,0,4),('alu','mul',4,0),('addhi',4,12),
 ('mem',True,'half',3,4,40),('imm','cmp',3,0),('branch',0,0x090E2EBA),
 ('call',0x090E20B8),('call',0x090E20AE)])
INS={a:p.Ins(a,k,x)for a,k,x in SPECS}
need(len(INS)==len(SPECS),'手書き命令非重複')
MONS,COUNT,ABSENT,CURRENT_MOVE=0x02023B44,0x02023B2C,0x02023CD0,0x02023CAA
WORDS={0x08163230:PRODUCER|1,0x0903F574:ENTRY|1,
 0x091034C8:0x02037004,0x091034CC:CIRCUS,0x091034D0:BIT_TABLE,0x091034D4:0xFFFF,
 0x091034E0:0x0804448D,0x091034E8:0x091673C4,0x091034EC:0x02022BC4,0x091034F0:0x08008901,
 0x09099E5C:0x081C85A5,0x09167440:0x09141A20,
 0x090DF7A4:0x095D5A9D,0x095D5AB4:FLAGS,0x095D5AB8:CIRCUS,0x095D5ABC:0x095343A5,
 0x095D5AC0:0x09533F2D,0x095343B8:0x090DF7A9,
 0x090DFB18:TARGET,0x090DFB1C:0x02023CAC,0x090DFB20:0xFFFF0001,0x090DFB24:CURSOR,
 0x090DFB28:ATTACKER,0x090DFB2C:NEWBS,0x090DFB30:BSTRUCT,0x090DFB34:HITMARKER,
 0x090DFB3C:SCRIPTING,0x090DFB40:0x09163C24,0x09163CE4:0x090E010A,
 0x090E01C4:COUNT,0x090E0194:MONS,0x090E225C:BIT_TABLE,0x090E2270:CURRENT_MOVE,
 0x090E2280:ABSENT,0x090E2284:FLAGS}
EXTERNAL={
 (0x09103380,0x092D0AC8):('current_streak_wrapper_inclusive_opaque_5arg_api',71),
 (0x091033D0,0x091269B8):('VegaFacilityStateGet_tier',1),
 (0x091033F0,0x091269B8):('VegaFacilityStateGet_battle_type',0),
 (0x091033FC,0x0804448C):('Random',31),
 (0x09099E06,0x081C85A4):('__umodsi3',31),
 (0x091034AE,0x08008900):('StringCopy',0x02022BC4),
 (0x090DF7E0,0x090D3FEC):('GetBankItemEffect',0),
 (0x090E2E94,0x090D5014):('GetBaseMoveTarget',0),
}
BRIDGE=(STOP_PRODUCER,ENTRY)
PROFILE=dict(streak=71,initial_circus_flags=0,tier=1,facility_battle_type=0,random_return=31,
 battle_flags=0x04000001,attacker=0,target=1,chosen_move=1,current_move=1,script_arg1=0,script_arg2=0,
 state=48,move_bounce_bits=0,hitmarker=128,dancer_in_progress=True,dancer_bank_count=0,
 battlers_count=4,dancer_turn_order=[2,0,1,3],dancer_ability=217,dancer_hp=1,absent_flags=0,
 current_turn_attacker=0,current_turn_target=1,base_move_target=0,normal_abi_return=True,
 same_circus_flags_epoch=True,same_battle_context_epoch=True,same_stack_epoch=True)

def memory(target_hp):
 need(type(target_hp)is int and target_hp in(0,1),'target生存二profile')
 mem={}
 for a,n,v in[(CIRCUS,4,0),(FLAGS,4,0x04000001),(ATTACKER,1,0),(TARGET,1,1),
  (0x02023CAC,2,1),(CURRENT_MOVE,2,1),(CURSOR,4,SCRIPT),(SCRIPT+1,1,0),(SCRIPT+2,1,0),
  (NEWBS,4,CONTEXT),(CONTEXT+352,1,0),(BSTRUCT,4,BATTLE_CONTEXT),(BATTLE_CONTEXT+19,1,0),
  (HITMARKER,4,128),(SCRIPTING+20,1,48),(COUNT,1,4),(ABSENT,1,0),
  (CONTEXT+334,1,0),(CONTEXT+354,1,8),(CONTEXT+335,1,16),
  (MONS+88*2+56,2,217),(MONS+88*2+40,2,1),(MONS+88+40,2,target_hp)]:rt.setmem(mem,a,n,v)
 for i,value in enumerate(PROFILE['dancer_turn_order']):rt.setmem(mem,CONTEXT+376+i,1,value)
 return mem

def preserve(live,writes=(),events=None):
 need(type(live)is list and all(type(w)is list and len(w)==2 and type(w[0])is int and type(w[1])is int and w[1]>0 and 0<=w[0]<w[0]+w[1]<=1<<32 for w in live),'有限future-live射影')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'circus_flags_epoch_changed','battle_context_epoch_changed','stack_epoch_changed'} and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 need(not any(events.values()),'circus/battle/stack同epoch維持')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live破壊禁止')
 return True

def _compose(raw,target_hp,projections=None,opaque_writes=None,epoch_events=None,profile=None):
 need(type(target_hp)is int and target_hp in(0,1),'限定target HP profile')
 need(profile is None or exact(profile,PROFILE),'有限入力profileの無断拡張禁止')
 trace=[];boundaries=[];groups=[];visited=[];producer_writes=[];bit_reads=[];dancer_reads=[];dancer_writes=[]
 m=machine_engine.Machine(raw,PRODUCER,{},memory(target_hp),instructions=INS,trace=trace)
 phase='producer';seen_producer=False
 def boundary(key,name,result=None):
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'全opaque境界射影')
   live=projections[index];writes=(opaque_writes or {}).get(key,());events=(epoch_events or {}).get(key,{})
   preserve(live,writes,events)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(site=key[0],target=key[1],role=name,required_fields=[dict(address=a,size=n)for a,n in live],
    normal_abi_return_required=True,same_circus_flags_epoch_required=True,same_battle_context_epoch_required=True,
    same_stack_epoch_required=True,callee_effects_proven=False))
  for reg in(0,1,2,3,12):m.reg[reg]=rt.U
  if result is not None:m.reg[0]=result
  m.flags=(rt.U,)*4;m.flag_pc=None
 while True:
  need(m.steps<2000,'有限producer/Dancer step上限')
  if phase=='dancer'and m.pc==(0x090E20B8 if target_hp else 0x090E20B0):break
  if m.pc==STOP_PRODUCER:
   need(phase=='producer'and m.reg[13]==0x03007000,'producer正常復帰とstack回復')
   need(rt.getmem(m.mem,CIRCUS,4)==0x80000000 and producer_writes==[(0x091034A4,CIRCUS,4,0x80000000)],'正のflagは実producer OR/STRのみ')
   boundary(BRIDGE,'same_epoch_registered_opcode49_API_admission')
   m.reg[14]=STOP_PRODUCER|1;m.pc=ENTRY;phase='dancer';seen_producer=True;continue
  if m.pc in INS:
   visited.append(m.pc)
   if m.pc==0x09103362:bit_reads.append(m.reg[3])
   if m.pc==0x091034A4:producer_writes.append((m.pc,m.reg[3],4,m.reg[5]))
   if m.pc==0x090E2090:dancer_writes.append((m.pc,m.reg[3],1,m.reg[1]))
   before=len(trace);pc=m.pc;m.step()
   if 0x090E010A<=pc<=0x090E2EBA:
    dancer_reads.extend(dict(pc=pc,address=a,size=n)for k,a,n in trace[before:]if k=='read')
   continue
  key=((m.reg[14]&~1)-4,m.pc)
  need(key in EXTERNAL,'非登録opaque/branch逸脱 '+str(tuple(hex(x)for x in key)))
  name,result=EXTERNAL[key]
  if key[0]==0x09103380:need(m.reg[:4]==[0,0xFFFF,0xFFFF,0xFFFF]and m.read(m.reg[13],4)==0,'実current-streak五引数')
  elif key[0]==0x091033D0:need(m.reg[0]==4,'source tier field4')
  elif key[0]==0x091033F0:need(m.reg[0]==3,'source battle-type field3')
  elif key[0]==0x09099E06:need(m.reg[:2]==[31,32],'Random31から実modulo32引数')
  elif key[0]==0x091034AE:need(m.reg[:2]==[0x02022BC4,0x09141A20],'実description table[31]とgStringVarC')
  elif key[0]==0x090DF7E0:need(m.reg[0]==0,'実attacker ItemEffect引数')
  elif key[0]==0x090E2E94:need(m.reg[:2]==[1,2],'実GetBaseMoveTarget(currentMove1,newAttacker2)')
  boundary(key,name,result);m.pc=m.reg[14]&~1
 need(seen_producer and bit_reads==[BIT_TABLE+4*i for i in range(32)],'全32flagを実走査')
 need(MINIMUM in visited and (MINIMUM+4 in visited)==(target_hp==0),'BLとLDRの完全fetch')
 need(dancer_writes==[(0x090E2090,ATTACKER,1,2)],'実Dancer bank2 attacker writer')
 need(0x090E12E6 not in visited and 0x090E12F0 not in visited,'既存DancerInProgressでABILITY_ON_FIELD初回起動を短絡')
 if target_hp:need(m.reg[0]==1,'partnerと同じCurrentTurnTargetの実算出')
 else:need(m.reg[3]==CURRENT_MOVE,'実LDR後続命令結果')
 return dict(steps=m.steps,trace=trace,visited=visited,boundaries=boundaries,groups=groups,
  producer_writes=producer_writes,bit_reads=bit_reads,dancer_reads=dancer_reads,dancer_writes=dancer_writes,endpoint=m.pc)

def compose(raw,target_hp,opaque_writes=None,epoch_events=None,profile=None):
 allowed=set(EXTERNAL)|{BRIDGE}
 need(set(opaque_writes or {})<=allowed and set(epoch_events or {})<=allowed,'未知opaque条件拒否')
 first=_compose(raw,target_hp,profile=profile)
 live=live_engine.future_live(first['trace'],len(first['boundaries']))
 second=_compose(raw,target_hp,live,opaque_writes,epoch_events,profile)
 need(first['visited']==second['visited']and first['producer_writes']==second['producer_writes']and first['dancer_writes']==second['dancer_writes'],'全非live RAM消去replay一致')
 return dict(status='PASS_CONDITIONAL_REGISTERED_DANCER_PROFILE',target_hp=target_hp,
  instruction_steps=second['steps'],endpoint=second['endpoint'],visited=second['visited'],
  conditional_call_groups=second['groups'],producer_writes=second['producer_writes'],
  dancer_reads=second['dancer_reads'],dancer_writes=second['dancer_writes'],
  positive_circus_flag_host_seeded=False,dancer_state_host_initial_condition=True,
  first_dancer_initialization_executed=False,ability_on_field_executed=False,
  nonlive_ram_erased_at_every_boundary=True,actual_runtime_execution_observed=False)

def fixed_parts():
 parts={a:encoded(i)for a,i in INS.items()}
 for a,v in WORDS.items():need(a not in parts,'literal命令非重複');parts[a]=v.to_bytes(4,'little')
 parts[BIT_TABLE]=b''.join((1<<i).to_bytes(4,'little')for i in range(32))
 return parts

def bind(raw):
 for a,b in fixed_parts().items():need(chunk(raw,a,len(b))==b,'独立意味/source field不一致 '+hex(a))
 return True

def windows(raw):return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]

CANDIDATE,DIAGNOSTIC=p.CANDIDATE,p.DIAGNOSTIC
KIND='registered_dancer_circus_minimum_thumb'
KINDS=(KIND,)
TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(HIT,)
HELD_HITS=()

SOURCE_IDS = {'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'ability_ids.csv': {'commit': 'b9be8c6c231df0aac1c5eb163b154a4ec8ff5787',
                     'git_blob_sha': '2d76c9cc130460833c3234fc4efe59bc3a6074f7',
                     'local': 'ability_ids.csv',
                     'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                     'sha256': '8ae721ef01feeddb50cb0ef1ce2f59193a87a871133561ae2557ac8a5c9bfbcf',
                     'size': 70348,
                     'source': 'manifests/ability_ids.csv',
                     'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/b9be8c6c231df0aac1c5eb163b154a4ec8ff5787/manifests/ability_ids.csv'},
 'cfru-abilities.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                      'git_blob_sha': '73be02b9f4df796c4ddddb774882dcff36b0e369',
                      'local': 'cfru-abilities.h',
                      'repository': 'kapibarasan000/CFRU-JP',
                      'sha256': 'fa0f9fffe2192c6230e7b89162bfcb0745a4ce49af8f24f0d7de581ac4eb9f9c',
                      'size': 9550,
                      'source': 'include/constants/abilities.h',
                      'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/abilities.h'},
 'cfru-battle-script-commands.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': '10e8cf9821e5be79798b3ab1d02ea3e44ce44f05',
                                   'local': 'cfru-battle-script-commands.s',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': 'ef6615d20d0768e23828b941fcd2a4f04ba06507a7ed498ab51b8db10e71f5f6',
                                   'size': 11083,
                                   'source': 'assembly/data/battle_script_commands_table.s',
                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/battle_script_commands_table.s'},
 'cfru-cmd49.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                  'git_blob_sha': '96e61fd2bdb8f09e4410752f215ae5f27817b954',
                  'local': 'cfru-cmd49.c',
                  'repository': 'kapibarasan000/CFRU-JP',
                  'sha256': '7710708a14d4e57d63153597caa4e72185fa181a03eab0ffea2d4eebcab897b9',
                  'size': 58345,
                  'source': 'src/cmd49.c',
                  'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/cmd49.c'},
 'cfru-frontier.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                     'git_blob_sha': '8c4e07b5e4553cdb23f2ca393e59672f8d671a2a',
                     'local': 'cfru-frontier.h',
                     'repository': 'kapibarasan000/CFRU-JP',
                     'sha256': 'aa62962fe7f2828a89b64fd8355e386c9ce72f16f0cff27db279d3448d971801',
                     'size': 11523,
                     'source': 'include/new/frontier.h',
                     'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/frontier.h'},
 'cfru-include--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '7add3e78535b105d9d08d3d601da4e1d784f526a',
                            'local': 'cfru-include--battle.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': '8c6b332ef73bc545297b4f6c5bedc1ad11fa4470901f39cf386c1be53f4abdc9',
                            'size': 52228,
                            'source': 'include/battle.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle.h'},
 'cfru-include--battle_util.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                 'git_blob_sha': '444a9885fe3f2fe2301802279f4a5e622f678f30',
                                 'local': 'cfru-include--battle_util.h',
                                 'repository': 'kapibarasan000/CFRU-JP',
                                 'sha256': 'd5561a9dfc48b893202a62222fb023844f289b772115c71adccdc32c70d0675e',
                                 'size': 5033,
                                 'source': 'include/battle_util.h',
                                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/battle_util.h'},
 'cfru-include--constants--battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                       'git_blob_sha': '6ebffb06ae7978281cf9bbd6b082182e4e481714',
                                       'local': 'cfru-include--constants--battle.h',
                                       'repository': 'kapibarasan000/CFRU-JP',
                                       'sha256': '88681a4d9e3f34b8608417adf44f828b8c1a19669bba30e00fe22540e2936fb0',
                                       'size': 16608,
                                       'source': 'include/constants/battle.h',
                                       'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/constants/battle.h'},
 'cfru-include--gba--types.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': '601fdf73ab404a2d1e0ccd5a4d0c3f5382ede8e0',
                                'local': 'cfru-include--gba--types.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': '467a0219173bd2f8e20e962a9eaa43eafba298f815dab6655ae1761367d43ae6',
                                'size': 4241,
                                'source': 'include/gba/types.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/gba/types.h'},
 'cfru-include--global.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': '574c09b9b6209f6bee6e1d3a2fb8866221af8900',
                            'local': 'cfru-include--global.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c2973e69e55633ce39c9fe1763c891e5530b4ac1dc15e82a666c1f1ea7201bc0',
                            'size': 19566,
                            'source': 'include/global.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/global.h'},
 'cfru-include--new--ram_locs.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': '79802668664d2d590c416a1f881eb1f0a6bcd03a',
                                   'local': 'cfru-include--new--ram_locs.h',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '8c8d7fd53813fefff997173f203aa0c97e1c14062db933e55303d5c498b2f089',
                                   'size': 9008,
                                   'source': 'include/new/ram_locs.h',
                                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/ram_locs.h'},
 'cfru-include--pokemon.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': 'b18f2ee2a1517efa8aeb742daedac9e778d73d7a',
                             'local': 'cfru-include--pokemon.h',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': 'd75972c66e85835a3fc9c859cb695c033995ba6627ba1d44f577b35136356c78',
                             'size': 29476,
                             'source': 'include/pokemon.h',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/pokemon.h'},
 'cfru-include--sprite.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                            'git_blob_sha': 'da7057376c71e2cbe3543f262a6e360e2eeaaf8a',
                            'local': 'cfru-include--sprite.h',
                            'repository': 'kapibarasan000/CFRU-JP',
                            'sha256': 'c848594606e7889276457e723c5189cbedbe71862a1b001ed9ec39299a8fe511',
                            'size': 11836,
                            'source': 'include/sprite.h',
                            'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/sprite.h'},
 'cfru-routinepointers': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': 'c0722629632ccc337a1710dfa11036fba64181a8',
                          'local': 'cfru-routinepointers',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': 'dcc05504a939cb1876d1b569fb11a33021908bad4d9af7ed66ff74782b88ca24',
                          'size': 7381,
                          'source': 'routinepointers',
                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/routinepointers'},
 'cfru-src--battle_util.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                             'git_blob_sha': '2ad6fd276a535f99a631ae01f38fe3f6bc0d15e5',
                             'local': 'cfru-src--battle_util.c',
                             'repository': 'kapibarasan000/CFRU-JP',
                             'sha256': '558c9a85d067e984c96bf83fb0c652a58df3b0b5fbf63620e4ea694195458ed3',
                             'size': 67724,
                             'source': 'src/battle_util.c',
                             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/battle_util.c'},
 'cfru-src--defines_battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': 'cf9846c0e8d8c289f096bb15dcbc078cb9f75c71',
                                'local': 'cfru-src--defines_battle.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': 'e85a4e7a35321a05972fa3742fe469619869127b545242f640c6c6cf061355de',
                                'size': 7098,
                                'source': 'src/defines_battle.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/defines_battle.h'},
 'cfru-src--frontier.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': '8879204faaf760cf6882acbe1833ad9f0e8055aa',
                          'local': 'cfru-src--frontier.c',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': 'a33395bfaf81eec041a423d44d5620908e587a4f6e5614780b4bde393d7f4e06',
                          'size': 56750,
                          'source': 'src/frontier.c',
                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/frontier.c'},
 'circus_getter_abi.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                          'git_blob_sha': '54d54c6d6a9fa9d01ca22d6eb800496612246268',
                          'local': 'circus_getter_abi.py',
                          'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                          'sha256': '5268f5e18f8a33fb9573843a39bf8a7babf328af0dd86b0d7b76ae7dc6cdfc7e',
                          'size': 8128,
                          'source': 'scripts/pr16_circus_getter_abi.py',
                          'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/pr16_circus_getter_abi.py'},
 'pret-util.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': 'b32799584937a120a03b08897886f08adc033fce',
                 'local': 'pret-util.c',
                 'repository': 'pret/pokefirered',
                 'sha256': 'de0b72b691ec879404be2391a4dfa4d6b5b633d3a919351e1693c88ad671bf09',
                 'size': 7141,
                 'source': 'src/util.c',
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/util.c'},
 'scripts--build_battle_core.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                   'git_blob_sha': '09bde3df2e2d33701141da7cec6eb53a6562f91c',
                                   'local': 'scripts--build_battle_core.py',
                                   'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                   'sha256': 'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
                                   'size': 239192,
                                   'source': 'scripts/build_battle_core.py',
                                   'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_battle_core.py'},
 'scripts--build_id_spaces.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                 'git_blob_sha': '46e0c760c43bcfc407515f89f97b7ac64c822976',
                                 'local': 'scripts--build_id_spaces.py',
                                 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                 'sha256': '2b9cb736fffcf8df21344aa86d8919b997b74e64b882d14e6db9176e515d0fd6',
                                 'size': 86544,
                                 'source': 'scripts/build_id_spaces.py',
                                 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_id_spaces.py'},
 'stage72_hooks.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                     'git_blob_sha': '85ec1fc2bbe8957fbddc9f57b4d3de47d753d234',
                     'local': 'stage72_hooks.S',
                     'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                     'sha256': '5250cf5f64bb16ac743ad7bf31ce8b572fd29f6265d07acacf7f30ca3cd9650a',
                     'size': 9372,
                     'source': 'overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S',
                     'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S'},
 'stage77_suppression.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                           'git_blob_sha': '7d28b40947a86bfde4031f626348c5f28e4bfbfa',
                           'local': 'stage77_suppression.S',
                           'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                           'sha256': '725a876b24385aab13994a89d5701de8e9e77a63358d03ab8ae1e7de8f5152e0',
                           'size': 4840,
                           'source': 'overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S',
                           'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S'}}
EXPECTED_HITS = [{'accepted': False,
  'address': 151920811,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '376a16ec6c91e9ed8590a4f4b9ca598e7ce1b99b9dbfef2bf4895fa403ec10d5',
  'size': 4,
  'target': 167703536}]
ROOT=dict(kind='source_bound_circus_producer_then_registered_Dancer_API',producer_slot=0x08163230,
 producer_entry=PRODUCER,producer_flag_write=0x091034A4,circus_flags=CIRCUS,
 opcode=0x49,dispatch_slot=0x0903F574,registered_handler=ENTRY|1,entry=ENTRY,
 wrapper=0x095D5A9C,suppressed_trampoline=0x095343A4,continuation=0x090DF7A8,
 state=48,state_cell=0x09163CE4,handler=0x090E010A,attacker_writer=0x090E2090,
 target_gate=0x090E2092,hit_call=MINIMUM,hit_target=0x090E2E94,hit_successor=MINIMUM+4,
 base_target_call=0x090E2E94,base_target_api=0x090D5014,target_hp_read=0x090E2EB0)
CLAIMS=dict(conditional_registered_api_entry=True,positive_flag_generated_by_actual_producer=True,
 complete_selected_caller_path=True,minimum_full_fetch_covered=True,
 same_epoch_required=True,current_candidate_measurement_required=True,
 dancer_state_host_initial_condition=True,dancer_initialization_producer_proven=False,
 ability_macro_is_direct_field=True,ability_on_field_success_assumed=False,
 ability_on_field_executed=False,get_bank_ability_substituted=False,
 natural_battle_entry_proven=False,natural_moveend_reachability_proven=False,
 all_state_producers_proven=False,all_opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False,indirect_reference_completeness_proven=False,
 retirement_proven=False,donor_eligible=False,donor_leased=False,owner_transfer_proven=False)
CONTRACT=dict(
 producer_ja='実special072 slot08163230から初期flags0、streak wrapper正常戻り71、tier1/type0、Random31を有限条件にする。全32bit走査と実modulo中継、実OR/STR091034A4がcircus bit31を生成する。正値をhost seedしない。',
 bridge_ja='同circus/battle/context/stack epochの正常API復帰後に実opcode49を呼ぶ。wrapperと完全prologue、GetBankItemEffect戻り0、非bounce/非unable、実state48表を実行する。自然なbattle開始・全script prefix・全state producerではない。',
 dancer_ja='DancerInProgress=true、BankCount0、TurnOrder=[2,0,1,3]、CurrentTurnAttacker0/Target1は有効な有限context入力条件で、producer実行済みとは主張しない。count!=4、arg1=0、実bit3非zeroでABILITY_ON_FIELD/animation/dance table/SortBanks初期化を短絡する。ABILITY(bank)は直接field、CFRU216を公開canonical manifest/aliasで217へ写す。GetBankAbilityへの置換を禁止。',
 gates_ja='bank2の直接ability217、HP1、absent0、CurrentTurnAttacker0!=2を実readしgBankAttacker=2を実writerで生成。BATTLE_TYPE_DOUBLE mask0x1（bit0）とpartner(2)=0が成立しGetBaseMoveTarget(currentMove1,bank2)へ配送。正常戻りMOVE_TARGET_SELECTED=0を条件としてCurrentTurnTarget1の実HPを0/1の2profileで評価する。',
 opaque_ja='streakは実BL先092D0AC8のwrapperを含めopaqueでありgetter本体への実配送は未証明。GetBaseMoveTarget、GetBankItemEffect、tier/type getter、Random、unsigned modulo、StringCopyは実site/target/引数を固定。通常ABIのcallee-saved r4..r11/SP/LRと明示r0戻りを条件とし、caller-saved/NZCVをUnknownへ消去する。全callee副作用を成功扱いしない。',
 epoch_ja='全9opaque/API境界で実future read-before-write RAMだけを保持し非live RAMをUnknownへ消去して同traceを再現。fieldとポインタとstackを同epochに保ち、各live byte破壊・epoch変更・余分な条件を拒否する。普遍IRQ/heap寿命を主張しない。',
 minimum_ja='090E20AAのBL4byteを実fetchしoutlined helperからbase-target APIとTarget1生存を評価。HP0は090E2EBA→090E20AEのLDR2byteを実fetchし090E20B0で停止。HP1は090E20B8のtarget代入直前で停止。6byteの完全命令のみ分類しGetMoveTargetやDancer全効果/復帰を仮定しない。')
ALL_WINDOWS=critical.merge_parts(fixed_parts())
WINDOWS={f'dancer_roots_{i}':(w['address'],w['size'])for i,w in enumerate(ALL_WINDOWS)}

def source_semantics(sources):
 texts={k:layout_engine.without_comments(v.decode())for k,v in sources.items()}
 constants={}
 for name in('MAX_BATTLERS_COUNT','NUM_BATTLE_SIDES','POKEMON_NAME_LENGTH','PARTY_SIZE','BATTLE_STATS_NO','MAX_SPRITES','MAX_NUM_RAID_SHIELDS','MAX_MON_MOVES'):
  values=[]
  for text in texts.values():values+=re.findall(r'^\s*#define\s+'+name+r'\s+(\d+)\s*$',text,re.M)
  need(values and len(set(values))==1,'独立array macro '+name);constants[name]=int(values[0])
 battle=texts['cfru-include--battle.h']
 new,newsize,_=layout_engine.layout(layout_engine.definition(battle,'NewBattleStruct'),constants)
 mon,monsize,_=layout_engine.layout(layout_engine.definition(texts['cfru-include--pokemon.h'],'BattlePokemon'),constants)
 selected={k:new[k]for k in('MoveBounceInProgress','DancerBankCount','DancerInProgress','DancerTurnOrder','CurrentTurnAttacker','CurrentTurnTarget')}
 expected=dict(MoveBounceInProgress=dict(offset=352,bit=0,width_bits=2,type_size=1),
  DancerBankCount=dict(offset=334,size=1),DancerInProgress=dict(offset=354,bit=3,width_bits=1,type_size=1),
  DancerTurnOrder=dict(offset=376,size=4),CurrentTurnAttacker=dict(offset=335,bit=0,width_bits=4,type_size=1),
  CurrentTurnTarget=dict(offset=335,bit=4,width_bits=4,type_size=1))
 need(selected==expected,'独立Dancer struct/bitfields')
 need(monsize==88 and mon['ability']==dict(offset=56,size=2)and mon['hp']==dict(offset=40,size=2),'独立BattlePokemon stride/ability/hp')
 def prefix(struct,lastfield):
  decl=layout_engine.split_declarations(layout_engine.definition(battle,struct));last=next(i for i,x in enumerate(decl)if re.search(r'\b'+lastfield+r'\b',x))
  return layout_engine.layout(';'.join(decl[:last+1])+';',constants)[0][lastfield]
 bs=prefix('BattleStruct','dynamicMoveType');sc=prefix('BattleScripting','atk49_state')
 need(bs==dict(offset=19,size=1)and sc==dict(offset=20,size=1),'独立context/state offsets')
 enum=re.search(r'enum\s*\{\s*ATK49_SET_UP\s*,([^}]+)\}',texts['cfru-cmd49.c']);need(enum is not None,'cmd49 enum')
 names=['ATK49_SET_UP']+[x.strip()for x in enum[1].split(',')if x.strip()]
 need(all(re.fullmatch(r'[A-Za-z_]\w*',x)for x in names)and names.index('ATK49_DANCER')==48,'独立state48')
 macros={k:v.strip()for k,v in re.findall(r'^\s*#define\s+(\w+)\s+([^\n]+)$',texts['cfru-include--constants--battle.h'],re.M)}
 def evaluate(expr,seen=()):
  def visit(n):
   if isinstance(n,ast.Expression):return visit(n.body)
   if isinstance(n,ast.Constant):need(type(n.value)is int,'整数macro');return n.value
   if isinstance(n,ast.Name):need(n.id in macros and n.id not in seen,'閉じたmacro依存');return evaluate(macros[n.id],(*seen,n.id))
   need(isinstance(n,ast.BinOp)and isinstance(n.op,ast.BitOr),'ORだけのmask式');return visit(n.left)|visit(n.right)
  return visit(ast.parse(expr,mode='eval'))
 masks={k:evaluate(k)for k in('BIT_FLANK','BATTLE_TYPE_DOUBLE','HITMARKER_UNABLE_TO_USE_MOVE','BATTLE_TYPE_BATTLE_CIRCUS','BATTLE_CIRCUS_ABILITY_SUPPRESSION')}
 need(list(masks.values())==[2,1,0x80000,0x04000000,0x80000000],'独立battle masks')
 selected_target=re.findall(r'^\s*#define\s+MOVE_TARGET_SELECTED\s+(0x[0-9a-fA-F]+|\d+)\s*$',battle,re.M)
 need(selected_target==['0x0'],'独立MOVE_TARGET_SELECTED')
 rows=list(csv.DictReader(io.StringIO(sources['ability_ids.csv'].decode())));rows=[r for r in rows if r['ability_key']=='ABILITY_KEY_DANCER']
 need(len(rows)==1,'一意Dancer canonical行');row=rows[0]
 need(all(row[k]==v for k,v in dict(id='217',cfru_id='216',cfru_symbol='ABILITY_DANCER',classification='CFRU_APPEND').items()),'canonical217/source216')
 upstream=re.findall(r'^#define\s+ABILITY_DANCER\s+(\d+)\s*$',texts['cfru-abilities.h'],re.M)
 need(upstream==['216'],'公開upstream Dancer216')
 bitbody=re.search(r'const\s+u32\s+gBitTable\[\]\s*=\s*\{([^}]+)\}',texts['pret-util.c']);need(bitbody is not None,'全bit table source')
 need([x.strip()for x in bitbody[1].split(',')if x.strip()]==[f'1 << {i}'for i in range(32)],'全32bit独立serializer')
 desc=re.search(r'const\s+u8\*\s+const\s+sBattleCircusEffectDescriptions\[\]\s*=\s*\{([^}]+)\}',texts['cfru-src--frontier.c']);need(desc is not None,'description source')
 fields=[x.strip()for x in desc[1].split(',')if x.strip()];need(len(fields)==32 and fields[31]=='gText_BattleCircusDescriptionAbilitySuppression','description31')
 table=texts['cfru-battle-script-commands.s'].split('gBattleScriptingCommandsTable:\n');need(len(table)==2,'primary table')
 commands=re.findall(r'^\.word\s+([^\s@]+)',table[1],re.M);need(commands[0x49]=='atk49_moveend','実source opcode49登録')
 return dict(new_battle_struct_size=newsize,dancer_fields=selected,battle_pokemon=dict(size=monsize,ability=mon['ability'],hp=mon['hp']),
  dynamic_move_type=bs,state_field=sc,dancer_state=48,masks=masks,canonical_ability=217,upstream_ability=216,
  move_target_selected=0,bit_table_fields=32,description_index=31,ability_macro='direct_gBattleMons_field',
  ability_on_field='AbilityBattleEffects_CHECK_ON_FIELD_short_circuited',source_comments_used=False)

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'固定source閉集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'独立source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立source Git blob '+name)
 roles={
  'stage77_suppression.S':['.equ STAGE77_G_BATTLE_CIRCUS_FLAGS, 0x0203DFBC','STAGE77_DISPATCH_R3_CLOBBER Stage77_DispatchAtk49MoveEnd, 0x09533F2D, 0x095343A5','lsls r3, r3, #5','cmp r3, #0','ldr r3, =\\suppressed_target','bx r3'],
  'stage72_hooks.S':['STAGE72_FUNCTION Stage72_OriginalAtk49MoveEnd','STAGE72_JUMP_CONTINUATION 0x090DF7A9','mov lr, r11','mov r6, r9','mov r7, r10'],
  'cfru-routinepointers':['sp072_LoadBattleCircusEffects 08163230'],
  'cfru-include--new--ram_locs.h':['#define gBattleCircusFlags (*((u32*) 0x203DFBC))'],
  'cfru-src--frontier.c':['void sp072_LoadBattleCircusEffects(void)','gBattleCircusFlags |= gBitTable[effectNum];','effectNum = Random() % (i + 1);','u16 streak = GetCurrentBattleTowerStreak();','return GetBattleTowerStreak(CURR_STREAK, 0xFFFF, 0xFFFF, 0xFFFF, 0);','StringCopy(gStringVarC, sBattleCircusEffectDescriptions[effectNum]);'],
  'cfru-cmd49.c':['void atk49_moveend(void)','holdEffectAtk = ITEM_EFFECT(gBankAttacker);','case ATK49_DANCER:',
   'if (gNewBS->DancerBankCount == gBattlersCount)','if (!gNewBS->DancerInProgress','&& ABILITY_ON_FIELD(ABILITY_DANCER)',
   '&& gNewBS->attackAnimationPlayed','&& !gNewBS->moveWasBouncedThisTurn','&& CheckTableForMove(gCurrentMove, gDanceMoves)',
   'else if (!gNewBS->DancerInProgress)','u8 bank = gNewBS->DancerTurnOrder[gNewBS->DancerBankCount];',
   'if (ABILITY(bank) == ABILITY_DANCER','&& BATTLER_ALIVE(bank)','&& !(gAbsentBattlerFlags & gBitTable[bank])',
   '&& bank != gNewBS->CurrentTurnAttacker)','gBankAttacker = bank;',
   'if (gBattleTypeFlags & BATTLE_TYPE_DOUBLE','gNewBS->CurrentTurnAttacker == PARTNER(bank)',
   'GetBaseMoveTarget(gCurrentMove, gBankAttacker) == MOVE_TARGET_SELECTED','gBattleMons[gNewBS->CurrentTurnTarget].hp)',
   'gBankTarget = gNewBS->CurrentTurnTarget;','gBankTarget = GetMoveTarget(gCurrentMove, FALSE);'],
  'cfru-src--defines_battle.h':['#define ITEM_EFFECT(bank) GetBankItemEffect(bank)',
   '#define ABILITY(bank) gBattleMons[bank].ability','#define BATTLER_ALIVE(bank) (gBattleMons[bank].hp > 0)',
   '#define PARTNER(bank) (bank ^ BIT_FLANK)'],
  'cfru-include--battle_util.h':['#define ABILITY_ON_FIELD(abilityId)(AbilityBattleEffects(ABILITYEFFECT_CHECK_ON_FIELD, 0, abilityId, 0, 0))'],
  'cfru-src--battle_util.c':['item_effect_t GetBankItemEffect(u8 bank)','u8 GetBaseMoveTarget(u16 move, u8 bankAtk)','return gBattleMoves[move].target;'],
  'scripts--build_id_spaces.py':["lines.append(f\"#define {row['ability_key']} {row['id']}u\")",'redefine_alias(alias["source_symbol"], alias["ability_key"])'],
  'scripts--build_battle_core.py':['VEGA_FACILITY_STATE_BATTLE_TYPE','VEGA_FACILITY_STATE_TIER','get_token = f"VarGet({name})"','text = text.replace(get_token, f"VegaFacilityStateGet({name})")',
   '("include/constants/abilities.h", \'../../integration/ability_aliases.h\')','def _category_alias_header(', 'f"#undef {name}"', 'f"#define {name} {value}u"'],
  'circus_getter_abi.py':['CALL = 0x09103380','def interworking_veneer('],
  'BPRJ.ld':['Random = 0x804448C | 1;','__umodsi3 = 0x81C85A4 | 1;','StringCopy = 0x8008900 | 1;',
   'gBankAttacker = 0x2023CCB;','gBattleScripting = 0x2023F24;','gHitMarker = 0x2023D30;',
   'gBattleMons = 0x2023B44;','gBattlersCount = 0x2023B2C;','gCurrentMove = 0x2023CAA;','gAbsentBattlerFlags = 0x2023CD0;']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'独立source意味 '+name+' '+token)
 return source_semantics(sources)

def bind_semantics(raw,sources):
 bind(raw);d.signed(raw,ALL_WINDOWS);semantics=source_semantics(sources)
 return dict(instructions=len(INS),instruction_bytes=sum(i.size for i in INS.values()),
  source_layout=semantics,bit_table_serialized=True,canonical_ability_alias_bound=True,rom_observed_values_as_source=False)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI/epoch契約')
 bind(raw);cases=[compose(raw,hp,opaque_writes,epoch_events,profile)for hp in(1,0)]
 cover={a+j for case in cases for a in case['visited']for j in range(INS[a].size)}
 need(all(a in cover for a in range(MINIMUM,MINIMUM+6)),'全profile和で最小6byte fetch')
 return dict(schema_version=1,status='DRAFT_CONDITIONAL_DANCER_MINIMUM_NOT_CURRENT_ACCEPTANCE',
  claims=CLAIMS,minimum=dict(address=MINIMUM,**identity(chunk(raw,MINIMUM,6))),
  windows=windows(raw),cases=cases,hit_byte_coverage=4,minimum_byte_coverage=6,
  positive_circus_flag_host_seeded=False,dancer_state_host_initial_condition=True)

def evidence_template(hit):
 need(type(hit)is int and hit==HIT,'Dancer限定hit')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=MINIMUM,size=6),
  complete_instructions=[dict(address=MINIMUM,size=4,kind='call',target=0x090E2E94),
   dict(address=MINIMUM+4,size=2,kind='spmem',load=True,register=3,stack_offset=36)],
  positive_profiles=[dict(target_hp=1,minimum_fetch=[MINIMUM],endpoint=0x090E20B8),
   dict(target_hp=0,minimum_fetch=[MINIMUM,MINIMUM+4],endpoint=0x090E20B0)],
  input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HIT)),'閉じたDancer最小6byte witness');return MINIMUM,6

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'不変source窓');return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親hit全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),
  windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def measure(raw):return windows(raw)

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現候補/旧診断分離')
 for key,val in[('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)]:need(exact(review[key],val),'閉じたreview '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保存')
 protected_windows(review);sources_bind(review,sources);serialization=bind_semantics(raw,sources);d.signed(raw,selected)
 composition=compose_selected(raw);e=evidence_template(HIT);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_DANCER_ROOTS',count=1,hits=list(HITS),
  serialization=serialization,composition=composition,protected_windows=len(ALL_WINDOWS),protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate');return _regions(raw,inherited,review,sources)
validate=_regions
