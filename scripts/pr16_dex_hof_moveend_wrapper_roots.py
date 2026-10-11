"""Circus producerとmoveend登録APIの限定意味モデル。実機/自然到達の証明ではない。"""
import copy, hashlib, json, re
import ast
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
HIT, MINIMUM, PRODUCER, ENTRY = 0x090DFBB5, 0x090DFBB4, 0x0910333C, 0x090DF7A0
CIRCUS, FLAGS, BIT_TABLE = 0x0203DFBC, 0x02022AAC, 0x0821AE68
ATTACKER, TARGET, SCRIPTING, CURSOR = 0x02023CCB, 0x02023CCC, 0x02023F24, 0x02023CD4
NEWBS, BSTRUCT, HITMARKER, STATUS3 = 0x0203DFB0, 0x02023F48, 0x02023D30, 0x02023D5C
CONTEXT, BATTLE_CONTEXT, SCRIPT = 0x02010000, 0x02012000, 0x02014000
STOP_PRODUCER = 0xFFFFFFF0
SPECS=[]
def block(a, specs):
 for k,*x in specs:
  if k=='regmem' and type(x[0]) is bool:
   ld,width,rd,rb,ro=x;x=[{(True,'word'):'ldr',(True,'byte'):'ldrb',(False,'byte'):'strb'}[ld,width],rd,rb,ro]
  if k=='alu' and x[0] in ('tst','sbc','adc','bic'):k='alu_ext'
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
# cmd49.c:currentMove/arg1/arg2/ITEM_EFFECT、非bounce、HitMarker unableなし、state12。
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
block(0x090DFB9C,[('movhi',3,9),('mem',True,'byte',2,3,0),('literal',3,0x090DFE34),
 ('shift','lsl',1,2,2),('regmem',True,'word',1,1,3),('literal',3,0x090DFE38),('alu','tst',1,3),
 ('branch',0,0x090DFBB8),('spmem',True,3,28),('mem',True,'word',3,3,0),('shift','lsl',3,3,24),
 ('branch',5,0x090DFBB8),('call',0x090E298A),('imm','mov',3,13)])
INS={a:p.Ins(a,k,x) for a,k,x in SPECS}
need(len(INS)==len(SPECS),'手書き命令非重複')

WORDS={0x08163230:PRODUCER|1,0x0903F574:ENTRY|1,
 0x091034C8:0x02037004,0x091034CC:CIRCUS,0x091034D0:BIT_TABLE,0x091034D4:0xFFFF,
 0x091034E0:0x0804448D,0x091034E8:0x091673C4,0x091034EC:0x02022BC4,0x091034F0:0x08008901,
 0x09099E5C:0x081C85A5,0x09167440:0x09141A20,
 0x090DF7A4:0x095D5A9D,0x095D5AB4:FLAGS,0x095D5AB8:CIRCUS,0x095D5ABC:0x095343A5,
 0x095D5AC0:0x09533F2D,0x095343B8:0x090DF7A9,
 0x090DFB18:TARGET,0x090DFB1C:0x02023CAC,0x090DFB20:0xFFFF0001,0x090DFB24:CURSOR,
 0x090DFB28:ATTACKER,0x090DFB2C:NEWBS,0x090DFB30:BSTRUCT,0x090DFB34:HITMARKER,
 0x090DFB3C:SCRIPTING,0x090DFB40:0x09163C24,0x09163C54:0x090DFB9C,
 0x090DFE34:STATUS3,0x090DFE38:0x130480C0}
EXTERNAL={
 (0x09103380,0x092D0AC8):('current_streak_wrapper_inclusive_opaque_5arg_api',71),
 (0x091033D0,0x091269B8):('VegaFacilityStateGet_tier',1),
 (0x091033F0,0x091269B8):('VegaFacilityStateGet_battle_type',0),
 (0x091033FC,0x0804448C):('Random',31),
 (0x09099E06,0x081C85A4):('__umodsi3',31),
 (0x091034AE,0x08008900):('StringCopy',0x02022BC4),
 (0x090DF7E0,0x090D3FEC):('GetBankItemEffect',0),
}
BRIDGE=(STOP_PRODUCER,ENTRY)
PROFILE=dict(streak=71,initial_circus_flags=0,tier=1,facility_battle_type=0,random_return=31,
 battle_flags=0x04000000,attacker=0,target=1,chosen_move=1,script_arg1=0,script_arg2=0,
 state=12,move_bounce_bits=0,hitmarker=128,normal_abi_return=True,
 same_circus_flags_epoch=True,same_battle_context_epoch=True,same_stack_epoch=True)

def memory(status):
 mem={}
 for a,n,v in [(CIRCUS,4,0),(FLAGS,4,0x04000000),(ATTACKER,1,0),(TARGET,1,1),
  (0x02023CAC,2,1),(CURSOR,4,SCRIPT),(SCRIPT+1,1,0),(SCRIPT+2,1,0),
  (NEWBS,4,CONTEXT),(CONTEXT+352,1,0),(BSTRUCT,4,BATTLE_CONTEXT),(BATTLE_CONTEXT+19,1,0),
  (HITMARKER,4,128),(SCRIPTING+20,1,12),(STATUS3,4,status)]:rt.setmem(mem,a,n,v)
 return mem

def preserve(live,writes=(),events=None):
 need(type(live)is list and all(type(w)is list and len(w)==2 and type(w[0])is int and type(w[1])is int and w[1]>0 and 0<=w[0]<w[0]+w[1]<=1<<32 for w in live),'有限future-live射影')
 events={} if events is None else events
 need(type(events)is dict and set(events)<={'circus_flags_epoch_changed','battle_context_epoch_changed','stack_epoch_changed'} and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 need(not any(events.values()),'circus/battle/stack同epoch維持')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4) and type(v)is int and 0<=v<1<<(8*n) and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live破壊禁止')
 return True

def _compose(raw,status,projections=None,opaque_writes=None,epoch_events=None,profile=None):
 need(type(status)is int and status in (0,0x40),'限定status profile')
 need(profile is None or exact(profile,PROFILE),'有限入力profileの無断拡張禁止')
 trace=[];boundaries=[];groups=[];visited=[];producer_writes=[];bit_reads=[]
 m=machine_engine.Machine(raw,PRODUCER,{},memory(status),instructions=INS,trace=trace)
 phase='producer';seen_producer=False
 def boundary(key,name,result=None):
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if projections is not None:
   live=projections[index];writes=(opaque_writes or {}).get(key,());events=(epoch_events or {}).get(key,{})
   preserve(live,writes,events)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items() if a in kept}
   groups.append(dict(site=key[0],target=key[1],role=name,required_fields=[dict(address=a,size=n)for a,n in live],
    normal_abi_return_required=True,same_circus_flags_epoch_required=True,same_battle_context_epoch_required=True,
    same_stack_epoch_required=True,callee_effects_proven=False))
  for reg in (0,1,2,3,12):m.reg[reg]=rt.U
  if result is not None:m.reg[0]=result
  m.flags=(rt.U,)*4;m.flag_pc=None
 while True:
  need(m.steps<2000,'有限producer/moveend step上限')
  if phase=='moveend' and m.pc==(0x090E298A if status else 0x090DFBBA):break
  if m.pc==STOP_PRODUCER:
   need(phase=='producer' and m.reg[13]==0x03007000,'producer正常復帰とstack回復')
   need(rt.getmem(m.mem,CIRCUS,4)==0x80000000 and producer_writes==[(0x091034A4,CIRCUS,4,0x80000000)],'正のflagは実producer OR/STRのみ')
   boundary(BRIDGE,'same_epoch_registered_opcode49_API_admission')
   m.reg[14]=STOP_PRODUCER|1;m.pc=ENTRY;phase='moveend';seen_producer=True;continue
  if m.pc in INS:
   visited.append(m.pc)
   if m.pc==0x09103362:bit_reads.append(m.reg[3])
   if m.pc==0x091034A4:producer_writes.append((m.pc,m.reg[3],4,m.reg[5]))
   m.step();continue
  key=((m.reg[14]&~1)-4,m.pc)
  need(key in EXTERNAL,'非登録opaque/branch逸脱 '+str(tuple(hex(x)for x in key)))
  name,result=EXTERNAL[key]
  if key[0]==0x09103380:need(m.reg[:4]==[0,0xFFFF,0xFFFF,0xFFFF] and m.read(m.reg[13],4)==0,'実current-streak五引数')
  elif key[0]==0x091033D0:need(m.reg[0]==4,'source tier field4')
  elif key[0]==0x091033F0:need(m.reg[0]==3,'source battle-type field3')
  elif key[0]==0x09099E06:need(m.reg[:2]==[31,32],'Random31から実modulo32引数')
  elif key[0]==0x091034AE:need(m.reg[:2]==[0x02022BC4,0x09141A20],'実description table[31]とgStringVarC')
  elif key[0]==0x090DF7E0:need(m.reg[0]==0,'実attacker ItemEffect引数')
  boundary(key,name,result);m.pc=m.reg[14]&~1
 need(seen_producer and bit_reads==[BIT_TABLE+4*i for i in range(32)],'全32flagを実走査')
 need((MINIMUM in visited)==bool(status) and ((MINIMUM+4)in visited)==(not status),'BLとMOVの相補profileを区別')
 if not status:need(m.reg[3]==13,'実MOV13命令結果')
 return dict(steps=m.steps,trace=trace,visited=visited,boundaries=boundaries,groups=groups,
  producer_writes=producer_writes,bit_reads=bit_reads,endpoint=m.pc)

def compose(raw,status,opaque_writes=None,epoch_events=None,profile=None):
 allowed=set(EXTERNAL)|{BRIDGE}
 need(set(opaque_writes or {})<=allowed and set(epoch_events or {})<=allowed,'未知opaque条件拒否')
 first=_compose(raw,status,profile=profile)
 live=live_engine.future_live(first['trace'],len(first['boundaries']))
 second=_compose(raw,status,live,opaque_writes,epoch_events,profile)
 need(first['visited']==second['visited'] and first['producer_writes']==second['producer_writes'],'全非live RAM消去replay一致')
 return dict(status='PASS_CONDITIONAL_REGISTERED_MOVEEND_PROFILE',input_status=status,
  instruction_steps=second['steps'],endpoint=second['endpoint'],visited=second['visited'],
  conditional_call_groups=second['groups'],producer_writes=second['producer_writes'],
  positive_circus_flag_host_seeded=False,nonlive_ram_erased_at_every_boundary=True,
  actual_runtime_execution_observed=False)

def fixed_parts():
 parts={a:encoded(i)for a,i in INS.items()}
 for a,v in WORDS.items():need(a not in parts,'literal命令非重複');parts[a]=v.to_bytes(4,'little')
 parts[BIT_TABLE]=b''.join((1<<i).to_bytes(4,'little')for i in range(32))
 return parts

def bind(raw):
 for a,b in fixed_parts().items():need(chunk(raw,a,len(b))==b,'独立意味/source field不一致 '+hex(a))
 return True

def windows(raw):
 spans=[]
 for a,b in sorted(fixed_parts().items()):
  if spans and spans[-1][0]+spans[-1][1]==a:spans[-1][1]+=len(b)
  else:spans.append([a,len(b)])
 return [dict(address=a,**identity(chunk(raw,a,n)))for a,n in spans]

CLAIMS=dict(conditional_registered_api_entry=True,positive_flag_generated_by_actual_producer=True,
 same_epoch_required=True,current_candidate_measurement_required=True,
 natural_battle_entry_proven=False,natural_moveend_reachability_proven=False,
 all_state_producers_proven=False,all_opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False,indirect_reference_completeness_proven=False,
 retirement_proven=False,donor_eligible=False,donor_leased=False,dancer_classified=False)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI/epoch契約')
 bind(raw);cases=[compose(raw,s,opaque_writes,epoch_events,profile)for s in(0x40,0)]
 cover={a+j for case in cases for a in case['visited']for j in range(INS[a].size)}
 need(all(a in cover for a in range(MINIMUM,MINIMUM+6)),'2profileで6byte全命令を実行')
 return dict(schema_version=1,status='DRAFT_CONDITIONAL_MINIMUM_THUMB_NOT_CURRENT_ACCEPTANCE',
  claims=CLAIMS,minimum=dict(address=MINIMUM,**identity(chunk(raw,MINIMUM,6))),
  windows=windows(raw),cases=cases,hit_byte_coverage=4,minimum_byte_coverage=6,
  retained_unknown=[0x090E20AB],positive_flag_host_seeded=False)

SOURCE_IDS = {'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
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
 'stage72_hooks.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                     'git_blob_sha': '85ec1fc2bbe8957fbddc9f57b4d3de47d753d234',
                     'local': 'stage72_hooks.S',
                     'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                     'sha256': '5250cf5f64bb16ac743ad7bf31ce8b572fd29f6265d07acacf7f30ca3cd9650a',
                     'size': 9372,
                     'source': 'overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S',
                     'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime_hooks.S'},
 'stage72_runtime.c': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                       'git_blob_sha': '449a454fd0b9da4b9bbce3f90400c2ae314772f7',
                       'local': 'stage72_runtime.c',
                       'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                       'sha256': 'a00e37540d968ecda3c26ab4e7606a7c5efe249621067449921be120ed03a60b',
                       'size': 52635,
                       'source': 'overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c',
                       'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_ability_rom_runtime/modernization_p05_ability_rom_runtime.c'},
 'stage77_suppression.S': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                           'git_blob_sha': '7d28b40947a86bfde4031f626348c5f28e4bfbfa',
                           'local': 'stage77_suppression.S',
                           'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                           'sha256': '725a876b24385aab13994a89d5701de8e9e77a63358d03ab8ae1e7de8f5152e0',
                           'size': 4840,
                           'source': 'overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S',
                           'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/overlays/modernization_p05_stage77_suppression/modernization_p05_stage77_suppression.S'}}

CANDIDATE, DIAGNOSTIC = p.CANDIDATE, p.DIAGNOSTIC
KIND='registered_moveend_circus_minimum_thumb'
KINDS=(KIND,)
TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(HIT,)
HELD_HITS=(0x090E20AB,)
EXPECTED_HITS=[dict(address=HIT,target=167700976,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,
 sha256='e2270e91c2e95be5f7aa428cf94e92b71075e6e1360a60dffa546b0b92f54e71',
 classification='UNCLASSIFIED',accepted=False,reason='no_complete_typed_asset_consumer_witness',owner_candidates=[])]
ROOT=dict(kind='source_bound_producer_then_registered_moveend_API',producer_slot=0x08163230,
 producer_entry=PRODUCER,producer_flag_write=0x091034A4,circus_flags=CIRCUS,
 opcode=0x49,dispatch_slot=0x0903F574,registered_handler=ENTRY|1,entry=ENTRY,
 wrapper=0x095D5A9C,suppressed_trampoline=0x095343A4,continuation=0x090DF7A8,
 state=12,state_cell=0x09163C54,handler=0x090DFB9C,
 hit_call=MINIMUM,hit_target=0x090E298A,hit_successor=MINIMUM+4)
CONTRACT=dict(
 producer_ja='sp072実登録08163230→0910333CをAPI根に、初期circus_flags0・current streak71・facility tier1/battle-type0・Random31を有限前提にする。全32bitを実走査し、剰余31からbit31を選択し091034A4の実OR/STRだけで0203DFBCへ正の値を生成する。抽選確率や実際のstreak到達は証明しない。',
 bridge_ja='producer正常復帰後、同circus flag epochのままopcode49実登録APIを呼ぶ有限合成。active circus bit26・state12・有効script/contextを入口前提とし、自然なbattle開始や全state producerは主張しない。positive bit31をhost seedしない。',
 prologue_ja='全prologueと実LDR/stack、ITEM_EFFECT、非bounce/非unable枝、実state12表、attacker/status/hitmarkerを実行。無関係なC変数の値も実命令に沿ってロードする。',
 opaque_ja='current streak五引数は実BL先092D0AC8のinterworking wrapper入口まで。wrapperとgetter本体を包括するopaque正常復帰を条件とし、本体へ実行済み・五引数配送済みとは主張しない。VegaFacilityStateGet field4/3、Random、__umodsi3、StringCopy、GetBankItemEffectの実call site/target/引数を固定。callee-saved/r4..r11とSP/LRの通常ABI復帰、明示r0戻り値を条件にし、全callee副作用を成功扱いしない。',
 epoch_ja='全8境界でfuture read-before-write RAMだけを保持し他をUnknownへ消去。circus flag・battle/context・stack epoch変更は拒否する。無関係RAM書換は許可。全IRQ/heap寿命を主張しない。',
 minimum_ja='statuses3=0x40のcaseでBL090DFBB4を実行しcallee090E298A入口で停止。statuses3=0のcaseでは090DFBAA→MOV13/090DFBB8を実行して停止。2profile和が6byteを覆い、tail helper復帰を仮定しない。Dancer090E20ABは未分類。')
ALL_WINDOWS=critical.merge_parts(fixed_parts())
WINDOWS={f'moveend_wrapper_{i}':(w['address'],w['size'])for i,w in enumerate(ALL_WINDOWS)}

# source-only derived fields。ROMの観測offsetやCコメントを入力にしない。
def source_semantics(sources):
 texts={k:layout_engine.without_comments(v.decode())for k,v in sources.items()}
 constants={}
 for name in ('MAX_BATTLERS_COUNT','NUM_BATTLE_SIDES','POKEMON_NAME_LENGTH','PARTY_SIZE','BATTLE_STATS_NO','MAX_SPRITES','MAX_NUM_RAID_SHIELDS','MAX_MON_MOVES'):
  values=[]
  for text in texts.values():values+=re.findall(r'^\s*#define\s+'+name+r'\s+(\d+)\s*$',text,re.M)
  need(values and len(set(values))==1,'独立macro '+name);constants[name]=int(values[0])
 battle=texts['cfru-include--battle.h']
 new,_,_=layout_engine.layout(layout_engine.definition(battle,'NewBattleStruct'),constants)
 need(new['MoveBounceInProgress']==dict(offset=352,bit=0,width_bits=2,type_size=1),'source MoveBounceInProgress bitfield')
 bsbody=layout_engine.definition(battle,'BattleStruct')
 decl=layout_engine.split_declarations(bsbody)
 last=next(i for i,x in enumerate(decl)if re.search(r'\bdynamicMoveType\b',x))
 bs,_,_=layout_engine.layout(';'.join(decl[:last+1])+';',constants)
 scbody=layout_engine.definition(battle,'BattleScripting');decl=layout_engine.split_declarations(scbody)
 last=next(i for i,x in enumerate(decl)if re.search(r'\batk49_state\b',x))
 sc,_,_=layout_engine.layout(';'.join(decl[:last+1])+';',constants)
 need(bs['dynamicMoveType']==dict(offset=19,size=1) and sc['atk49_state']==dict(offset=20,size=1),'source dynamicMoveType/atk49_state offsets')
 enum=re.search(r'enum\s*\{\s*ATK49_SET_UP\s*,([^}]+)\}',texts['cfru-cmd49.c'])
 need(enum is not None,'cmd49公開enum')
 names=['ATK49_SET_UP']+[x.strip()for x in enum[1].split(',')if x.strip()]
 need(all(re.fullmatch(r'[A-Za-z_]\w*',x)for x in names)and names.index('ATK49_ATTACKER_INVISIBLE')==12,'source state12')
 # ORだけの閉じたmacro evaluator。名/整数/括弧以外を解釈しない。
 macros={k:v.strip()for k,v in re.findall(r'^\s*#define\s+(\w+)\s+([^\n]+)$',texts['cfru-include--constants--battle.h'],re.M)}
 def evaluate(expr,seen=()):
  def visit(n):
   if isinstance(n,ast.Expression):return visit(n.body)
   if isinstance(n,ast.Constant):need(type(n.value)is int,'整数macro');return n.value
   if isinstance(n,ast.Name):need(n.id in macros and n.id not in seen,'閉じたmacro依存');return evaluate(macros[n.id],(*seen,n.id))
   need(isinstance(n,ast.BinOp)and isinstance(n.op,ast.BitOr),'ORだけのmask式');return visit(n.left)|visit(n.right)
  return visit(ast.parse(expr,mode='eval'))
 masks={k:evaluate(k)for k in ('STATUS3_SEMI_INVULNERABLE','STATUS3_IN_AIR','HITMARKER_NO_ANIMATIONS','BATTLE_TYPE_BATTLE_CIRCUS','BATTLE_CIRCUS_ABILITY_SUPPRESSION')}
 need(list(masks.values())==[0x130480C0,0x40,128,0x04000000,0x80000000],'独立status/flag masks')
 bitbody=re.search(r'const\s+u32\s+gBitTable\[\]\s*=\s*\{([^}]+)\}',texts['pret-util.c'])
 need(bitbody is not None,'source全bit table')
 fields=[x.strip()for x in bitbody[1].split(',')if x.strip()]
 need(fields==[f'1 << {i}'for i in range(32)],'独立全32bit serializer')
 desc=re.search(r'const\s+u8\*\s+const\s+sBattleCircusEffectDescriptions\[\]\s*=\s*\{([^}]+)\}',texts['cfru-src--frontier.c'])
 need(desc is not None,'source全description table')
 fields=[x.strip()for x in desc[1].split(',')if x.strip()]
 need(len(fields)==32 and fields[31]=='gText_BattleCircusDescriptionAbilitySuppression','source選択description31')
 table=texts['cfru-battle-script-commands.s'].split('gBattleScriptingCommandsTable:\n')
 need(len(table)==2,'一意primary command表')
 commands=re.findall(r'^\.word\s+([^\s@]+)',table[1],re.M)
 need(commands[0x49]=='atk49_moveend','source opcode49登録')
 return dict(move_bounce_field=new['MoveBounceInProgress'],dynamic_move_type=bs['dynamicMoveType'],
  state_field=sc['atk49_state'],attacker_invisible_state=12,masks=masks,
  bit_table_fields=32,description_index=31,description_symbol=fields[31],source_comments_used=False)

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
  'cfru-cmd49.c':['void atk49_moveend(void)','holdEffectAtk = ITEM_EFFECT(gBankAttacker);','case ATK49_ATTACKER_INVISIBLE:','gStatuses3[gBankAttacker] & (STATUS3_SEMI_INVULNERABLE)','gHitMarker & HITMARKER_NO_ANIMATIONS','EmitSpriteInvisibility(0, TRUE);'],
  'cfru-src--defines_battle.h':['#define ITEM_EFFECT(bank) GetBankItemEffect(bank)'],
  'cfru-src--battle_util.c':['item_effect_t GetBankItemEffect(u8 bank)'],
  'scripts--build_battle_core.py':['VEGA_FACILITY_STATE_BATTLE_TYPE','VEGA_FACILITY_STATE_TIER','get_token = f"VarGet({name})"','text = text.replace(get_token, f"VegaFacilityStateGet({name})")'],
  'circus_getter_abi.py':['CALL = 0x09103380','def interworking_veneer('],
  'BPRJ.ld':['Random = 0x804448C | 1;','__umodsi3 = 0x81C85A4 | 1;','StringCopy = 0x8008900 | 1;','gBankAttacker = 0x2023CCB;','gBattleScripting = 0x2023F24;','gHitMarker = 0x2023D30;']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'独立source意味 '+name+' '+token)
 return source_semantics(sources)

def bind_semantics(raw,sources):
 bind(raw);d.signed(raw,ALL_WINDOWS)
 semantics=source_semantics(sources)
 return dict(instructions=len(INS),instruction_bytes=sum(i.size for i in INS.values()),
  source_layout=semantics,bit_table_serialized=True,rom_observed_values_as_source=False)

def evidence_template(hit):
 need(type(hit)is int and hit==HIT,'moveend限定hit')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=MINIMUM,size=6),
  complete_instructions=[dict(address=MINIMUM,size=4,kind='call',target=0x090E298A),dict(address=MINIMUM+4,size=2,kind='imm',operation='mov',register=3,value=13)],
  positive_profiles=[dict(status3=0x40,executed=[MINIMUM],endpoint=0x090E298A),dict(status3=0,executed=[MINIMUM+4],endpoint=MINIMUM+6)],
  input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))
def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HIT)),'閉じた最小6byte witness')
 return MINIMUM,6

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'不変source窓')
 return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親hit全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),
  windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def measure(raw):return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現候補/旧診断分離')
 for key,val in [('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)]:need(exact(review[key],val),'閉じたreview '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保存')
 protected_windows(review);sources_bind(review,sources);serialization=bind_semantics(raw,sources);d.signed(raw,selected)
 composition=compose_selected(raw);e=evidence_template(HIT);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_MOVEEND_WRAPPER',count=1,hits=list(HITS),
  serialization=serialization,composition=composition,protected_windows=len(ALL_WINDOWS),protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate')
 return _regions(raw,inherited,review,sources)
validate=_regions
