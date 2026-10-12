"""急所move-list境界の登録API条件付き有限消費。raw ROMを出力しない。"""
import copy, hashlib, json, re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_animation_registered_roots as flags_engine
from pr16_dex_hof_extra_roots import exact, encoded
need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
KIND = 'registered_critical_move_list_boundary'
KINDS = (KIND,)
TYPE_CATEGORY = 'data'
HITS = CLASSIFIED_HITS = TARGET_HITS = (0x090405A9,)
HELD_HITS = ()
EXPECTED_HITS = [dict(address=0x090405A9, target=167706116,
 kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS', size=4,
 sha256='2ceb85104eacfeecfddf213304ff0bda629f3c7ee73a15440c36b5ca9844305c',
 classification='UNCLASSIFIED', accepted=False,
 reason='no_complete_typed_asset_consumer_witness', owner_candidates=[])]
ENTRY, STOP, READER = 0x090E4418, 0x090E45DC, 0x09130F38
SLOT = 0x0903F460
HIGH, ALWAYS, TERMINATOR = 0x09040578, 0x090405AC, 0xFEFE
ATTACKER, TARGET, COUNT = 0x02023CCB, 0x02023CCC, 0x02023B2C
MOVE, FLAGS, MONS, NEWBS = 0x02023CAA, 0x02022AAC, 0x02023B44, 0x0203DFB0
# APIの明示例。実RAM/saveの観測値と主張しない。必要fieldだけ初期化する。
CONTEXT = 0x02010000
ROOT = dict(kind='primary_battle_command_registered_api_entry', opcode=4,
 dispatch_slot=SLOT, registered_handler=ENTRY | 1, entry=ENTRY,
 calls=[0x090E45A8,0x090E45D8], reader=READER, stop=STOP)
TABLE_LAYOUT = [('gHighCriticalChanceMoves', HIGH, 26), ('gAlwaysCriticalMoves', ALWAYS, 6)]
TABLE_SYMBOLS = {
 'gHighCriticalChanceMoves': ('KARATECHOP RAZORWIND RAZORLEAF SKYATTACK CRABHAMMER SLASH AEROBLAST CROSSCHOP BLAZEKICK AIRCUTTER POISONTAIL LEAFBLADE NIGHTSLASH SHADOWCLAW PSYCHOCUT CROSSPOISON STONEEDGE ATTACKORDER SPACIALREND DRILLRUN SNIPESHOT ESPERWING TRIPLEARROWS AQUACUTTER IVYCUDGEL TABLES_TERMIN').split(),
 'gAlwaysCriticalMoves': 'STORMTHROW FROSTBREATH SURGINGSTRIKES WICKEDBLOW FLOWERTRICK TABLES_TERMIN'.split(),
}
TABLE_SYMBOLS = {k:tuple('MOVE_'+s for s in v) for k,v in TABLE_SYMBOLS.items()}

# source atk04_critcalcのsingle-target branchだけを手書きで記述する。
# 観測decoder出力はこのモデルの入力にしない。双方の完全命令encodeを別途照合する。
# 登録入口: attacker ability、item、currentMove、target kindを実loader/stackへ束縛。
SPECS = []
def block(address, specs):
 for spec in specs:
  kind, *args = spec
  SPECS.append((address,kind,tuple(args)))
  address += 4 if kind == 'call' else 2
 return address
block(ENTRY, [
 ('push',0xF0,True),('movhi',14,11),('movhi',7,10),('movhi',6,9),('movhi',5,8),
 ('imm','mov',3,88),('push',0xE0,True),('literal',4,0x090E46D0),
 ('mem',True,'byte',0,4,0),('alu','mul',3,0),('literal',7,0x090E46D4),
 ('add',3,7,3),('mem',True,'half',3,3,56),('spadd',-60),
 ('spmem',False,3,20),('spmem',False,4,4),('call',0x090D3FEC),
 ('literal',3,0x090E46D8),('spmem',False,0,28),('mem',True,'byte',1,4,0),
 ('mem',True,'half',0,3,0),('spmem',False,3,24),('call',0x090D5014),
 ('literal',3,0x090E46DC),('spmem',False,3,8),('mem',True,'word',3,3,0),
 ('spmem',False,0,12),('shift','lsl',3,3,31),('branch',4,0x090E4458),
 ('jump',0x090E459C)])
# 非double battleではcalcSpreadMove=FALSE。double側コードは証明範囲に含めない。
block(0x090E459C,[('imm','mov',3,0),('movhi',11,3),('jump',0x090E4464)])
# 有効count→single target、armor/lucky chant/tutorial gate。
block(0x090E4464,[
 ('spmem',True,2,4),('literal',3,0x090E46E0),('mem',True,'byte',2,2,0),
 ('mem',False,'byte',2,3,0),('literal',3,0x090E46E4),('movhi',9,3),
 ('mem',True,'byte',3,3,0),('imm','cmp',3,0),('branch',1,0x090E4478),
 ('jump',0x090E4678),('movhi',3,11),('imm','cmp',3,0),
 ('branch',0,0x090E4480),('jump',0x090E466A),('literal',3,0x090E46E8),
 ('movhi',10,3),('mem',True,'byte',4,3,0),('literal',3,0x090E46EC),
 ('movhi',8,3),('literal',6,0x090E46F0),('imm','mov',5,88),
 ('alu','mul',5,4),('add',5,7,5),('mem',True,'half',3,5,56),
 ('imm','cmp',3,4),('branch',0,0x090E44B4),('imm','cmp',3,75),
 ('branch',0,0x090E44B4),('imm','mov',0,0),('call',0x090D7BDC),
 ('imm','cmp',0,0),('branch',1,0x090E44B4),('mem',True,'word',3,6,0),
 ('spmem',False,3,16),('spmem',True,3,8),('mem',True,'word',2,3,0),
 ('literal',3,0x090E46F4),('alu_ext','tst',2,3),('branch',0,0x090E4568)])
block(0x090E4568,[
 ('shift','lsl',0,4,24),('literal',3,0x090E46FC),('shift','lsr',0,0,24),
 ('call',0x090EA78A),('spmem',True,3,16),('movhi',12,3),('addhi',0,12),
 ('mem',True,'byte',3,0,17),('imm','cmp',3,0),('branch',1,0x090E44B4),
 ('spmem',True,3,20),('imm','cmp',3,197),('branch',1,0x090E458C)])
# attacker ability0なのでMerciless status load枝を要求しない。
block(0x090E458C,[('spmem',True,3,4),('mem',True,'byte',0,3,0),
 ('call',0x090D7B80),('imm','cmp',0,0),('branch',0,0x090E45A2)])
# 実currentMoveポインタをstackから取り戻して両listへ渡す。
block(0x090E45A2,[
 ('spmem',True,3,24),('literal',1,0x090E4700),('mem',True,'half',0,3,0),
 ('call',READER),('imm','cmp',0,0),('branch',1,0x090E4598),
 ('imm','mov',5,88),('spmem',True,3,4),('mem',True,'byte',0,3,0),
 ('shift','lsl',3,5,0),('alu','mul',3,0),('add',3,7,3),
 ('mem',True,'word',1,3,80),('call',0x090D7C64),('spmem',True,2,4),
 ('mem',True,'word',3,6,0),('mem',True,'byte',2,2,0),('add',3,3,2),
 ('imm','add',3,168),('mem',True,'byte',3,3,0),('spmem',False,3,16),
 ('spmem',True,3,24),('literal',1,0x090E4704),('spmem',False,0,40),
 ('mem',True,'half',0,3,0),('call',READER)])
# source util.cの順序: FEFEを先に比較→一致memberでTRUE→2byte進行。
block(READER,[
 ('mem',True,'half',3,1,0),('literal',2,0x09130F5C),('compare',3,2),
 ('branch',0,0x09130F56),('imm','add',1,2),('jump',0x09130F4E),
 ('imm','add',1,2),('subi',3,1,2),('mem',True,'half',3,3,0),
 ('compare',3,2),('branch',0,0x09130F56),('compare',0,3),
 ('branch',1,0x09130F44),('imm','mov',0,1),('jump',0x09130F58),
 ('imm','mov',0,0),('bx',14)])
INS = {a:party.Ins(a,k,args) for a,k,args in SPECS}
need(len(INS)==len(SPECS),'命令spec非重複')
WORDS={SLOT:ENTRY|1,0x090E46D0:ATTACKER,0x090E46D4:MONS,
 0x090E46D8:MOVE,0x090E46DC:FLAGS,0x090E46E0:0x02023CCF,
 0x090E46E4:COUNT,0x090E46E8:TARGET,0x090E46EC:0x02023CD1,
 0x090E46F0:NEWBS,0x090E46F4:0x10210,0x090E46FC:0x08074969,
 0x090E4700:ALWAYS,0x090E4704:HIGH,0x09130F5C:TERMINATOR}
EXTERNAL={0x090E4438:(0x090D3FEC,'GetBattlerItemEffect',0),
 0x090E4446:(0x090D5014,'GetBaseMoveTarget',0),
 0x090E449E:(0x090D7BDC,'CantScoreACrit',0),
 0x090E456E:(0x090EA78A,'SIDE_GetBattlerSide_veneer',1),
 0x090E4590:(0x090D7B80,'IsLaserFocused',0),
 0x090E45BE:(0x090D7C64,'GetCriticalRank',0)}
PROFILE=dict(battle_flags=0,attacker=0,target=1,battlers_count=2,
 current_move=1,attacker_ability=0,target_ability=0,lucky_chant=0,
 attacker_status2=0,chi_strike_boost=0,newbs_context=CONTEXT,
 normal_abi_returns=True,same_battle_context_epoch=True,same_stack_epoch=True)
CLAIMS=dict(proof_scope='conditional_registered_critical_move_lists',
 conditional_registered_api_entry=True,actual_opcode_dispatch_executed=False,
 whole_candidate_identity_checked_by_parent_required=True,
 actual_runtime_execution_observed=False,full_story_reachability_claimed=False,
 full_battle_script_prefix_executed=False,opaque_callee_effects_proven=False,
 universal_heap_or_irq_lifetime_proven=False,whole_table_classified=False,
 pointer_interpretation_claimed=False,retirement_proven=False,
 indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(
 entry_ja='primary opcode4の実登録cellを検証したhandler API入口。自然battle/effect0 prefix/dispatcher全体の到達は未証明。',
 profile_ja='single battle、attacker0/target1/count2、move1、ability0、LuckyChant0、status2とchiStrike0の十分条件。内部reader引数をhost追加せずhandler実LDRHとstack保存から生成する。',
 calls_ja='6個の外部callは明示戻り値と通常ABI復帰のみ条件。callee本体の成功や副作用を証明しない。SIDEは実r3=GetBattlerSide|1を受けたveneerの結果1。',
 memory_ja='全opaque境界で実future read-before-write RAMのみ維持し、非live RAMをUnknownへ消去。gNewBSの同battle context epochとlive stack epochを条件にする。全RAM保持は要求しない。',
 extent_ja='固定公開table sourceの全.hword順序と独立current Move ID resolverから52/12byteをserialize。末尾だけFEFE。move1非memberにより両表を最後まで読む。',
 minimum_ja='分類は090405A9から4byteだけ。high最終member上位byte、FEFE全2byte、always先頭member下位byte。半word全3fieldと全表は根拠であり追加分類しない。')

class Machine(flags_engine.Machine):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.table_reads=[];self.current_move_loads=[]
 def read(self,a,n):
  value=super().read(a,n)
  if self.pc in (READER,0x09130F48):self.table_reads.append((self.pc,a,n,value))
  if self.pc in (0x090E4442,0x090E45A6,0x090E45D6):
   self.current_move_loads.append((self.pc,a,n,value))
  return value

def preservation_contract(live,writes=(),events=None):
 events={} if events is None else events
 need(type(events)is dict and set(events)<={'battle_context_epoch_changed','stack_epoch_changed'} and all(type(v)is bool for v in events.values()),'閉じたsame-epoch条件')
 need(not any(events.values()),'同battle context/stack epochを維持')
 for a,n,value in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4) and type(value)is int and 0<=value<1<<(8*n) and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live RAM破壊禁止')
 return True

def _compose(raw,projections=None,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(profile is None or exact(profile,PROFILE),'閉じた有限入力profile')
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI条件')
 need(d.u32(raw,SLOT)==ENTRY|1,'実opcode4登録')
 mem={};trace=[];visited=[];boundaries=[];groups=[];reader_calls=[]
 for a,n,v in ((ATTACKER,1,0),(TARGET,1,1),(COUNT,1,2),(MOVE,2,1),
  (FLAGS,4,0),(MONS+56,2,0),(MONS+88+56,2,0),(MONS+80,4,0),
  (NEWBS,4,CONTEXT),(CONTEXT+18,1,0),(CONTEXT+168,1,0)):
  rt.setmem(mem,a,n,v)
 m=Machine(raw,ENTRY,{},mem,instructions=INS,trace=trace)
 while m.pc!=STOP:
  need(m.steps<1000,'有限critical reader合成')
  if m.pc in INS:
   visited.append(m.pc)
   if m.pc==READER:
    site=(m.reg[14]&~1)-4
    need((site,m.reg[0],m.reg[1]) in ((0x090E45A8,1,ALWAYS),(0x090E45D8,1,HIGH)),'実currentMove loader→実BL→実list引数')
    reader_calls.append((site,m.reg[0],m.reg[1]))
   m.step();continue
  site=(m.reg[14]&~1)-4
  need(site in EXTERNAL and m.pc==EXTERNAL[site][0],'閉じた実opaque境界 '+hex(site)+' '+hex(m.pc))
  target,name,value=EXTERNAL[site]
  if site==0x090E4446:need(m.reg[:2]==[1,0],'実gCurrentMove/attacker引数')
  elif site==0x090E456E:need(m.reg[0]==1 and m.reg[3]==0x08074969,'SIDEの実targetと登録leaf')
  elif site==0x090E45BE:need(m.reg[:2]==[0,0],'実attacker status2からGetCriticalRank')
  else:need(m.reg[0]==0,'選択opaqueの実attacker/NULL引数')
  index=len(boundaries);boundaries.append((site,target));trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'全opaque境界の射影')
   live=projections[index]
   writes=(opaque_writes or {}).get(site,());events=(epoch_events or {}).get(site,{})
   preservation_contract(live,writes,events)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in live for j in range(n)}
   m.mem={a:v for a,v in m.mem.items() if a in kept}
   groups.append(dict(site=site,target=target,source_role=name,return_value=value,
    required_fields=[dict(address=a,size=n) for a,n in live],
    normal_abi_return_required=True,same_battle_context_epoch_required=True,
    same_stack_epoch_required=True,effects_discharged=False))
  for r in (0,1,2,3,12):m.reg[r]=rt.U
  m.reg[0]=value;m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
 need(reader_calls==[(0x090E45A8,1,ALWAYS),(0x090E45D8,1,HIGH)],'二つの実BLを順に通過')
 need([(a,n) for _,a,n,_ in m.table_reads]==[(ALWAYS+2*j,2)for j in range(6)]+[(HIGH+2*j,2)for j in range(26)],'両表の全32halfword/EOSを実LDRH消費')
 need(m.current_move_loads==[(0x090E4442,MOVE,2,1),(0x090E45A6,MOVE,2,1),(0x090E45D6,MOVE,2,1)],'currentMoveの全実loader')
 need(m.reg[0]==0,'high reader正常FALSE復帰')
 return dict(steps=m.steps,trace=trace,visited=visited,boundaries=boundaries,groups=groups,
  reads=m.table_reads,current_move_loads=m.current_move_loads,reader_calls=reader_calls)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(set(opaque_writes or {})<=set(EXTERNAL) and set(epoch_events or {})<=set(EXTERNAL),'未知opaque境界を黙殺しない')
 first=_compose(raw,profile=profile,contract=contract)
 live=engine.future_live(first['trace'],len(first['boundaries']))
 replay=_compose(raw,live,opaque_writes,epoch_events,profile,contract)
 need(first['visited']==replay['visited'] and first['reads']==replay['reads'] and first['boundaries']==replay['boundaries'],'非live RAM全消去後も同じ有限path')
 return dict(status='PASS_CONDITIONAL_CRITICAL_LIST_CONSUMER',instruction_steps=first['steps'],
  endpoint=STOP,reader_calls=first['reader_calls'],conditional_call_groups=replay['groups'],
  current_move_loads=first['current_move_loads'],complete_halfword_reads=32,
  consumed_bytes=64,includes_both_final_terminators=True,
  reader_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),
  nonlive_ram_erased_at_each_boundary=True,internal_reader_arguments_host_seeded=False,
  actual_runtime_execution_observed=False)

import pr16_dex_hof_critical_move_ids as move_ids
CALLER_SOURCE_IDS = {'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'cfru-battle_script_commands_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                         'git_blob_sha': '10e8cf9821e5be79798b3ab1d02ea3e44ce44f05',
                                         'local': 'cfru-battle_script_commands_table.s',
                                         'repository': 'kapibarasan000/CFRU-JP',
                                         'sha256': 'ef6615d20d0768e23828b941fcd2a4f04ba06507a7ed498ab51b8db10e71f5f6',
                                         'size': 11083,
                                         'source': 'assembly/data/battle_script_commands_table.s',
                                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/battle_script_commands_table.s'},
 'cfru-damage_calc.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                        'git_blob_sha': 'b51484b5b6d0071a39fded2dbcedbcd5850f7389',
                        'local': 'cfru-damage_calc.c',
                        'repository': 'kapibarasan000/CFRU-JP',
                        'sha256': '21aff6f8dd64161786b5b6d8b1f31d094e86643fd2bbc3752d447f9e6019cf04',
                        'size': 143093,
                        'source': 'src/damage_calc.c',
                        'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/damage_calc.c'},
 'cfru-util.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                 'git_blob_sha': '75c2e599e700ebf19ebfeb820c02c1363862110a',
                 'local': 'cfru-util.c',
                 'repository': 'kapibarasan000/CFRU-JP',
                 'sha256': 'bc47039408357c384d88dbbce4a9b3420f231c618c6e3a90395c9d7a5800d6cc',
                 'size': 12448,
                 'source': 'src/util.c',
                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/util.c'}}
SOURCE_IDS = {**copy.deepcopy(move_ids.SOURCE_IDS),**CALLER_SOURCE_IDS}

def source_tables(sources):
 """公開symbol宣言と独立現ID mapのみ。ROM測定値を入力しない。"""
 tables=move_ids.resolve_critical_tables(sources)
 out={};rows=[]
 for name,a,count in TABLE_LAYOUT:
  table=tables[name];fields=table['fields']
  need(tuple(f['symbol'] for f in fields)==TABLE_SYMBOLS[name],'固定source宣言順序')
  need(table['halfword_count']==count and table['only_final_terminator'] and table['move1_not_member'],'source独立完全extent/終端/非member')
  values=[f['canonical_id'] for f in fields]
  need(all(type(v)is int and 0<=v<=0xFFFF for v in values),'u16 source値')
  need(values[-1]==TERMINATOR and TERMINATOR not in values[:-1] and 1 not in values[:-1],'完全終端の独立条件')
  b=b''.join(v.to_bytes(2,'little')for v in values)
  out[a]=b
  rows.append(dict(label=name,address=a,**identity(b),halfword_count=count,
   final_terminator_address=a+2*(count-1),source_symbols=list(TABLE_SYMBOLS[name]),
   independent_current_ids=True,only_final_terminator=True,move1_not_member=True))
 return out,rows

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS) and exact(review['source_bindings'],SOURCE_IDS),'固定source閉集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name]
  need(type(b)is bytes and identity(b)=={k:row[k]for k in ('size','sha256')},'独立source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立Git blob '+name)
 roles={
  'cfru-damage_calc.c':['void atk04_critcalc(void)','u16 atkAbility = ABILITY(gBankAttacker);',
   'u8 atkEffect = ITEM_EFFECT(gBankAttacker);','u8 moveTarget = GetBaseMoveTarget(gCurrentMove, gBankAttacker);',
   'defAbility == ABILITY_BATTLEARMOR','defAbility == ABILITY_SHELLARMOR','CantScoreACrit(NULL)',
   'gNewBS->LuckyChantTimers[SIDE(bankDef)]','IsLaserFocused(gBankAttacker)',
   'CheckTableForMove(gCurrentMove, gAlwaysCriticalMoves)',
   'GetCriticalRank(gBankAttacker, gBattleMons[gBankAttacker].status2)',
   'gNewBS->chiStrikeCritBoosts[gBankAttacker]',
   'CheckTableForMove(gCurrentMove, gHighCriticalChanceMoves)'],
  'cfru-util.c':['bool8 CheckTableForMove(u16 move, const u16 table[])',
   'for (u32 i = 0; table[i] != MOVE_TABLES_TERMIN; ++i)',
   'if (move == table[i])','return TRUE;','return FALSE;'],
  'BPRJ.ld':['gNewBS = 0x203DFB0;','gBattleMons = 0x2023B44;',
   'gCurrentMove = 0x2023CAA;','gBankAttacker = 0x2023CCB;',
   'GetBattlerSide = 0x8074968 | 1;']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'source意味 '+token)
 text=sources['cfru-battle_script_commands_table.s'].decode()
 suffix=text.split('gBattleScriptingCommandsTable:\n')
 need(len(suffix)==2,'一意primary command table')
 commands=re.findall(r'^\.word\s+([^\s@]+)',suffix[1],re.M)
 need(len(commands)>4 and commands[4]=='atk04_critcalc','公開opcode4の型登録')
 return True

def fixed_parts():
 parts={i.address:encoded(i)for i in INS.values()}
 for a,v in WORDS.items():
  need(a not in parts,'命令/literal非重複');parts[a]=v.to_bytes(4,'little')
 return parts

def merge_parts(parts):
 rows=[];start=end=None;data=b''
 for a,b in sorted(parts.items()):
  need(end is None or a>=end,'保護窓非重複')
  if a!=end:
   if start is not None:rows.append(dict(address=start,**identity(data)))
   start=a;data=b''
  data+=b;end=a+len(b)
 if start is not None:rows.append(dict(address=start,**identity(data)))
 return rows
FIXED_WINDOWS=merge_parts(fixed_parts())
# ID workerでsource-only derivation済みの公開期待identity。observed tableから採らない。
TABLE_WINDOWS=[dict(address=HIGH,size=52,sha256='082c43d940efef0ca2fc346f1eafd6f038e1f0e34057ced738aead600b89211a'),
 dict(address=ALWAYS,size=12,sha256='cd67506878b499dd68829033f4870bc18e4520c0767f93a86fbaab7d4266b137')]
ALL_WINDOWS=sorted(FIXED_WINDOWS+TABLE_WINDOWS,key=lambda w:w['address'])
WINDOWS={f'critical_reader_{i}':(r['address'],r['size'])for i,r in enumerate(ALL_WINDOWS)}

def bind_semantics(raw,sources):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'完全独立命令 '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'完全実literal/登録 '+hex(a))
 tables,rows=source_tables(sources)
 need([{k:r[k]for k in('address','size','sha256')}for r in rows]==TABLE_WINDOWS,'独立current-ID serializer identity')
 for a,b in tables.items():need(chunk(raw,a,len(b))==b,'全独立table halfword '+hex(a))
 d.signed(raw,ALL_WINDOWS)
 return dict(status='PASS_SOURCE_CURRENT_ID_SERIALIZATION',tables=rows,
  instruction_count=len(INS),instruction_bytes=sum(i.size for i in INS.values()),
  table_bytes=64,public_upstream_id_substitution=False,observed_value_input=False,
  uniform_id_offset_used=False)

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'critical4byteだけ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,
  classified_window=dict(address=hit,size=4),
  complete_halfword_fields=[
   dict(address=HIGH+48,size=2,symbol='MOVE_IVYCUDGEL',table='gHighCriticalChanceMoves',hit_offset=1,covered_bytes=1),
   dict(address=HIGH+50,size=2,symbol='MOVE_TABLES_TERMIN',table='gHighCriticalChanceMoves',hit_offset=0,covered_bytes=2),
   dict(address=ALWAYS,size=2,symbol='MOVE_STORMTHROW',table='gAlwaysCriticalMoves',hit_offset=0,covered_bytes=1)],
  table_layout=[dict(label=n,address=a,halfword_count=c,size=c*2)for n,a,c in TABLE_LAYOUT],
  source_current_ids_required=True,input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))

def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HITS[0])),'全witness field一致')
 return HITS[0],4

def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'immutable新scope保護窓')
 return copy.deepcopy(ALL_WINDOWS)

def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS),'親unknown全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),
  diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),
  hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),windows=copy.deepcopy(ALL_WINDOWS),
  claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def measure(raw):
 """呼出元が選んだ新scope窓だけ。raw bytesは返さない。"""
 return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]

def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE) and exact(review['diagnostic_input'],DIAGNOSTIC),'current/diagnostic分離')
 for key,value in (('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)):
  need(exact(review[key],value),'review固定field '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,EXPECTED_HITS) and exact(selected,review['hits']),'親unknown全fieldを保存')
 protected_windows(review);sources_bind(review,sources)
 serialization=bind_semantics(raw,sources);d.signed(raw,selected)
 composition=compose_selected(raw)
 e=evidence_template(HITS[0]);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_CRITICAL_MOVE_LIST',
  count=1,hits=list(HITS),serialization=serialization,composition=composition,
  protected_windows=len(ALL_WINDOWS),protected_bytes=sum(r['size']for r in ALL_WINDOWS),
  **copy.deepcopy(CLAIMS))

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate')
 return _regions(raw,inherited,review,sources)
validate=_regions
