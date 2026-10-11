"""実opcode5DとMultiMoneyCalc hookから最小6byteを結ぶ条件付き型証明。"""
import copy,hashlib,json,re
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_animation_registered_roots as flags_engine
from pr16_dex_hof_extra_roots import exact,encoded
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
KIND='registered_money_reward_minimum_thumb';KINDS=(KIND,);TYPE_CATEGORY='code'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x0911A3C9,);HELD_HITS=()
EXPECTED_HITS=[dict(address=0x0911A3C9,target=167706870,kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS',size=4,sha256='a2638dc704f1c00ff71f178511f393211b5ab78f8e51fef3bca03db4a5b44390',classification='UNCLASSIFIED',accepted=False,reason='no_complete_typed_asset_consumer_witness',owner_candidates=[])]
SLOT,ENTRY,HOOK,WRAPPER,CALC,HIT_CALL,STOP=0x0903F5C4,0x080250A0,0x080250F4,0x09097FDC,0x0911A3B4,0x0911A3C8,0x0911A3CE
OUTCOME,TRAINER,FLAGS=0x02023DEA,0x020385E2,0x02022AAC
ROOT=dict(kind='actual_primary5d_registered_entry_to_multimoney_hook',primary_opcode=0x5D,primary_table=0x0903F450,primary_slot=SLOT,registered_handler=ENTRY|1,entry=ENTRY,patch=HOOK,patch_literal=0x080250F8,patch_destination=WRAPPER|1,wrapper_call=WRAPPER,callee=CALC,minimum_start=HIT_CALL,minimum_size=6,hit_callee=0x091191CC,post_return_literal=0x0911A3FC,endpoint=STOP)
SPECS=[]
def block(a,specs):
 for k,*args in specs:SPECS.append((a,k,tuple(args)));a+=4 if k=='call'else 2
 return a
# 公開stock Cmd_getmoneyrewardの完全入口。勝利/非secret-base入力の選択枝。
block(ENTRY,[('push',240,True),('movhi',7,10),('movhi',6,9),('movhi',5,8),('push',224,False),('imm','mov',5,0),('imm','mov',4,0),('literal',0,0x080250E4),('mem',True,'byte',0,0,0),('imm','cmp',0,1),('branch',0,0x080250B8)])
block(0x080250B8,[('literal',0,0x080250E8),('mem',True,'half',2,0,0),('imm','mov',1,128),('shift','lsl',1,1,3),('movhi',9,0),('compare',2,1),('branch',1,HOOK)])
# 公開hooksのregister2 patchとmulti_hooks.sの先頭BLを全fetch。
block(HOOK,[('literal',2,0x080250F8),('bx',2)])
block(WRAPPER,[('call',CALC)])
# build_battle_core.pyが追加したfacility guardを含む完全MultiMoneyCalc入口。
block(CALC,[('push',16,True),('call',0x091269A4),('imm','mov',4,0),('imm','cmp',0,0),('branch',0,0x0911A3C4)])
block(0x0911A3C4,[('literal',3,0x0911A3F8),('mem',True,'half',0,3,0),('call',0x091191CC),('literal',3,0x0911A3FC)])
INS={a:party.Ins(a,k,args)for a,k,args in SPECS};need(len(INS)==len(SPECS),'手書き意味命令非重複')
WORDS={SLOT:ENTRY|1,0x080250E4:OUTCOME,0x080250E8:TRAINER,0x080250F8:WRAPPER|1,0x0911A3F8:TRAINER,0x0911A3FC:FLAGS}
PROFILE=dict(battle_outcome=1,trainer_id=131,facility_guard_return=0,calc_reward_return='unspecified_u32',synchronous_registered_api_entry=True)
CLAIMS=dict(proof_scope='conditional_registered_money_reward_minimum_thumb',conditional_registered_api_entry=True,actual_primary_registration_bound=True,full_selected_caller_prefix_executed=True,all_minimum_instruction_bytes_fetched=True,hit_callee_normal_return_required=True,hit_callee_effects_proven=False,post_return_literal_executed=True,whole_candidate_identity_checked_by_parent_required=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,natural_battle_entry_reachability_claimed=False,full_script_prefix_executed=False,opaque_callee_effects_proven=False,universal_heap_or_irq_lifetime_proven=False,whole_function_range_classified=False,pointer_interpretation_claimed=False,retirement_proven=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(entry_ja='実primary opcode5D cell0903F5C4が指すJP handler080250A0のAPI入口。gBattleOutcome=1、u16 trainer131は有限入力例であり、通常勝利やtrainer producerを実行したとは主張しない。stock完全prologue→非secret-base枝→実hook080250F4→wrapper BL→現MultiMoneyCalc入口まで合成する。',guard_ja='build_battle_core.pyの固定src/multi.c rewriteが追加するVegaFacilityStateIsActiveの正常ABI戻り0を条件とする。guard本体の全効果や全facility producerは未証明。直後の実LDRHが同epochのtrainer fieldを再読する。',callee_ja='実BL0911A3C8でCalcMultiMoneyForTrainerへtrainer131を渡す。正常ABI復帰だけを条件とし、賞金戻りu32はUnknownのまま。賞金計算の正しさ、AddMoney実行、セーブ更新や勝利後script完了は主張しない。',lifetime_ja='各opaque境界で残るread-before-write RAMだけを保持し、他のRAMをUnknownへ消去して同pathを再合成。最初の境界ではtrainer2byteの同epochが必要。最後の境界では将来RAM読取がなく、全battle/heap/stack内容の保持を条件にしない。r4-r11/SPと実LRへの正常復帰は通常ABI条件。',minimum_ja='0911A3C8のBL4byteと復帰直後0911A3CCのLDR literal2byteを実fetchし、0911A3CEのflags field読取前で止める。分類はこの6byteだけ。callee本体、literal pool、全関数、隣接paddingを型分類へ広げない。')
EXTERNAL={0x0911A3B6:(0x091269A4,'VegaFacilityStateIsActive',0),HIT_CALL:(0x091191CC,'CalcMultiMoneyForTrainer',None)}

class Machine(flags_engine.Machine):
 def __init__(self,*args,**kw):super().__init__(*args,**kw);self.role_reads=[]
 def read(self,a,n):
  value=super().read(a,n);self.role_reads.append((self.pc,a,n,value));return value

def preservation_contract(live,writes=(),events=None):
 need(type(live)is list and all(type(x)is list and len(x)==2 and all(type(y)is int for y in x)and 0<=x[0]<x[0]+x[1]<=1<<32 for x in live),'有限future-live射影')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'trainer_context_epoch_changed'}and all(type(v)is bool for v in events.values()),'閉じたepoch条件')
 if any(a<=TRAINER< a+n or TRAINER<=a<TRAINER+2 for a,n in live):need(not events.get('trainer_context_epoch_changed',False),'必要trainer fieldの同epoch')
 need(type(writes)in(list,tuple),'有限書込列')
 for row in writes:
  need(type(row)in(list,tuple)and len(row)==3,'有限書込row')
  a,n,v=row
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'有限opaque書込')
  need(not any(a<b+s and b<a+n for b,s in live),'future-live byte破壊禁止')
 return True

def _compose(raw,projections=None,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(profile is None or exact(profile,PROFILE),'閉じた有限API profile')
 need(contract is None or exact(contract,CONTRACT),'閉じたAPI契約')
 need(d.u32(raw,SLOT)==ENTRY|1,'実opcode5D登録先')
 mem={};trace=[];visited=[];fetches=[];boundaries=[];groups=[];calls=[]
 for a,n,value in((OUTCOME,1,1),(TRAINER,2,131)):rt.setmem(mem,a,n,value)
 m=Machine(raw,ENTRY,{},mem,instructions=INS,trace=trace)
 while m.pc!=STOP:
  need(m.steps<60,'有限money caller合成')
  if m.pc in INS:
   visited.append(m.pc);fetches.append((m.pc,INS[m.pc].size));m.step();continue
  site=(m.reg[14]&~1)-4
  need(site in EXTERNAL and m.pc==EXTERNAL[site][0],'閉じた実opaque境界 '+hex(site)+' '+hex(m.pc))
  target,name,value=EXTERNAL[site]
  if site==HIT_CALL:need(m.reg[0]==131,'二度目の実trainer読取からcalc引数')
  calls.append(dict(site=site,target=target,source_role=name,arguments=[]if site!=HIT_CALL else[m.reg[0]],return_value=value if value is not None else'unspecified_u32'))
  index=len(boundaries);boundaries.append((site,target));trace.append(('boundary',index,0))
  if projections is not None:
   need(index<len(projections),'全opaque境界射影');live=projections[index]
   preservation_contract(live,(opaque_writes or {}).get(site,()),(epoch_events or {}).get(site,{}))
   for a,n,v in(opaque_writes or {}).get(site,()):rt.setmem(m.mem,a,n,v)
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   groups.append(dict(site=site,target=target,source_role=name,required_fields=[dict(address=a,size=n)for a,n in live],normal_abi_return_required=True,callee_saved_registers=[4,5,6,7,8,9,10,11,13],same_trainer_epoch_required=bool(live),effects_discharged=False,return_value=value if value is not None else'unspecified_u32'))
  for r in(0,1,2,3,12):m.reg[r]=rt.U
  if value is not None:m.reg[0]=value
  m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
 need(len(boundaries)==2 and visited[-2:]==[HIT_CALL,HIT_CALL+4],'実hit BLと復帰後LDRを連続fetch')
 need(m.reg[0]is rt.U and m.reg[3]==FLAGS,'戻り値Unknownのまま独立literal読取')
 need(not any(a<=FLAGS<a+n for _,a,n,_ in m.role_reads),'flags field読取前停止')
 need([(pc,a,n,v)for pc,a,n,v in m.role_reads if a==TRAINER]==[(0x080250BA,TRAINER,2,131),(0x0911A3C6,TRAINER,2,131)],'実trainer二読取の同epoch')
 return dict(steps=m.steps,visited=visited,fetches=fetches,trace=trace,boundaries=boundaries,groups=groups,calls=calls,reads=m.role_reads)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(opaque_writes is None or type(opaque_writes)is dict,'閉じたopaque書込mapping')
 need(epoch_events is None or type(epoch_events)is dict,'閉じたepoch mapping')
 need(set(opaque_writes or {})<=set(EXTERNAL)and set(epoch_events or {})<=set(EXTERNAL),'未知opaque site禁止')
 first=_compose(raw,profile=profile,contract=contract)
 live=engine.future_live(first['trace'],len(first['boundaries']))
 need(live==[[[TRAINER,2]],[]],'最小future RAM射影がtrainer2byteだけ')
 replay=_compose(raw,live,opaque_writes,epoch_events,profile,contract)
 for key in('visited','fetches','boundaries','calls','reads'):need(exact(first[key],replay[key]),'非live消去後同実path '+key)
 coverage={a+j for a,n in first['fetches']for j in range(n)}
 need(set(range(HIT_CALL,HIT_CALL+6))<=coverage,'全最小6byte実fetch')
 return dict(status='PASS_CONDITIONAL_REGISTERED_MONEY_REWARD',instruction_steps=first['steps'],endpoint=STOP,conditional_call_groups=replay['groups'],actual_call_arguments=first['calls'],actual_role_reads=first['reads'],visited_identity=identity(json.dumps(first['visited'],separators=(',',':')).encode()),minimum_executed_bytes=6,nonlive_ram_erased_at_each_boundary=True,internal_call_argument_host_seeded=False,calc_return_value_used=False,actual_runtime_execution_observed=False)

# SOURCE_IDS は取得済み固定公開sourceの完全identityを生成時にliteral化する。
SOURCE_IDS={'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld',
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'battle-assembly--data--battle_script_commands_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                           'git_blob_sha': '10e8cf9821e5be79798b3ab1d02ea3e44ce44f05',
                                                           'local': 'battle-assembly--data--battle_script_commands_table.s',
                                                           'repository': 'kapibarasan000/CFRU-JP',
                                                           'sha256': 'ef6615d20d0768e23828b941fcd2a4f04ba06507a7ed498ab51b8db10e71f5f6',
                                                           'size': 11083,
                                                           'source': 'assembly/data/battle_script_commands_table.s',
                                                           'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/battle_script_commands_table.s'},
 'cfru-assembly--hooks--multi_hooks.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                         'git_blob_sha': '4ac11b5610b01be9d6c227e95f758895e4937245',
                                         'local': 'cfru-assembly--hooks--multi_hooks.s',
                                         'repository': 'kapibarasan000/CFRU-JP',
                                         'sha256': 'cb0fd6f03e7aa7c3808b72b6c8948833fed65bfac13bb715837adf43336e13b9',
                                         'size': 1830,
                                         'source': 'assembly/hooks/multi_hooks.s',
                                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/hooks/multi_hooks.s'},
 'cfru-hooks': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                'git_blob_sha': '51a0f10dd4cccad235b476edd534a0e3e7e612ad',
                'local': 'cfru-hooks',
                'repository': 'kapibarasan000/CFRU-JP',
                'sha256': '19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5',
                'size': 21787,
                'source': 'hooks',
                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/hooks'},
 'cfru-include--gba--types.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                'git_blob_sha': '601fdf73ab404a2d1e0ccd5a4d0c3f5382ede8e0',
                                'local': 'cfru-include--gba--types.h',
                                'repository': 'kapibarasan000/CFRU-JP',
                                'sha256': '467a0219173bd2f8e20e962a9eaa43eafba298f815dab6655ae1761367d43ae6',
                                'size': 4241,
                                'source': 'include/gba/types.h',
                                'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/gba/types.h'},
 'cfru-include--new--ram_locs_battle.h': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                          'git_blob_sha': '76968c464b78b90266412f6ec0578200d0aa8cdc',
                                          'local': 'cfru-include--new--ram_locs_battle.h',
                                          'repository': 'kapibarasan000/CFRU-JP',
                                          'sha256': '9abbddcacb7488c5f1a007165a8756e8c4ccb6fc888a838da3ff763c9f9377cc',
                                          'size': 8293,
                                          'source': 'include/new/ram_locs_battle.h',
                                          'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/include/new/ram_locs_battle.h'},
 'cfru-src--multi.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                       'git_blob_sha': '34abae98bb3826db74e7bac72ec568f876eba514',
                       'local': 'cfru-src--multi.c',
                       'repository': 'kapibarasan000/CFRU-JP',
                       'sha256': 'e2638f50fc769dfd4228c9152e7d580b85098e958b42c7a4e5e001ea1f6f437b',
                       'size': 31141,
                       'source': 'src/multi.c',
                       'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/src/multi.c'},
 'pret-battle_script_commands.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                   'git_blob_sha': '67f90a37044db87091b2174f78fe1e31ad2ef10d',
                                   'local': 'pret-battle_script_commands.c',
                                   'repository': 'pret/pokefirered',
                                   'sha256': '3b7341db8cd58c54fb0b54b47e6eef89c5c05e8a60ab4e9b45bdc907845c19b3',
                                   'size': 355862,
                                   'source': 'src/battle_script_commands.c',
                                   'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/battle_script_commands.c'},
 'scripts--build_battle_core.py': {'commit': 'd68ae32ed8d55e30d342ab8187dda48e6e16eb59',
                                   'git_blob_sha': '09bde3df2e2d33701141da7cec6eb53a6562f91c',
                                   'local': 'scripts--build_battle_core.py',
                                   'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                                   'sha256': 'e83f659b912e4f61f790ef648f30dd7e669f737da84f326c234dc491a6d135c0',
                                   'size': 239192,
                                   'source': 'scripts/build_battle_core.py',
                                   'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/d68ae32ed8d55e30d342ab8187dda48e6e16eb59/scripts/build_battle_core.py'}}

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'閉じた固定source一覧')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')},'独立source全文 '+name)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立Git blob '+name)
 table=sources['battle-assembly--data--battle_script_commands_table.s'].decode()
 body=table.split('gBattleScriptingCommandsTable:',1)[1].split('gBattleScriptingCommandsTable2:',1)[0]
 words=re.findall(r'^\s*\.word\s+([^\s@]+)',body,re.M)
 need(len(words)==256 and words[0x5D]=='0x80250A1','公開opcode5D実JP登録')
 roles={
  'cfru-hooks':['MultiMoneyCalcHook 80250F4 2'],
  'cfru-assembly--hooks--multi_hooks.s':['MultiMoneyCalcHook:\n        bl MultiMoneyCalc','mov r4, r0','ldr r1, =0x080251C8|1'],
  'cfru-src--multi.c':['u32 MultiMoneyCalc(void)','u32 money = CalcMultiMoneyForTrainer(gTrainerBattleOpponent_A);','static u32 CalcMultiMoneyForTrainer(u16 trainerId)'],
  'pret-battle_script_commands.c':['static void Cmd_getmoneyreward(void)','if (gBattleOutcome == B_OUTCOME_WON)','if (gTrainerBattleOpponent_A == TRAINER_SECRET_BASE)'],
  'BPRJ.ld':['gBattleOutcome = 0x2023DEA;','gBattleTypeFlags = 0x2022AAC;'],
  'cfru-include--new--ram_locs_battle.h':['#define gTrainerBattleOpponent_A (*((u16*) 0x20385E2))'],
  'cfru-include--gba--types.h':['typedef uint16_t u16;','typedef uint32_t u32;','typedef u8  bool8;'],
  'scripts--build_battle_core.py':['money_anchor = "u32 MultiMoneyCalc(void)\\n{\\n\\tu32 money = CalcMultiMoneyForTrainer(gTrainerBattleOpponent_A);"','"\\tif (VegaFacilityStateIsActive())\\n\\t\\treturn 0;\\n\\n"','multi_text = multi_text.replace(']}
 for name,tokens in roles.items():
  text=sources[name].decode()
  for token in tokens:need(token in text,'固定source意味 '+name+' '+token)
 return dict(status='PASS_FIXED_SOURCE_REGISTRATION_AND_REWRITE',sources=len(SOURCE_IDS),primary_opcode=0x5D,primary_slot=SLOT,hook_register=2,trainer_scalar='u16',reward_scalar='u32',guard_scalar='bool8',source_layout_reused_as_current_address=False)

def fixed_parts():
 parts={i.address:encoded(i)for i in INS.values()}
 for a,value in WORDS.items():need(a not in parts,'命令/literal非重複');parts[a]=value.to_bytes(4,'little')
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
ALL_WINDOWS=FIXED_WINDOWS=merge_parts(fixed_parts())
WINDOWS={f'money_reward_{j}':(w['address'],w['size'])for j,w in enumerate(ALL_WINDOWS)}
def bind_semantics(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立Thumb意味 '+hex(i.address))
 for a,value in WORDS.items():need(d.u32(raw,a)==value,'実登録/literal '+hex(a))
 d.signed(raw,ALL_WINDOWS)
 return dict(status='PASS_REGISTERED_MONEY_REWARD_ENCODING',instructions=len(INS),instruction_bytes=sum(i.size for i in INS.values()),literal_fields=len(WORDS))
def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'money hitのみ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=HIT_CALL,size=6),complete_instructions=[dict(address=HIT_CALL,size=4,kind='call',target=0x091191CC),dict(address=HIT_CALL+4,size=2,kind='literal',register=3,literal=0x0911A3FC)],hit=dict(address=hit,size=4),input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))
def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HITS[0])),'witness全field一致');return HIT_CALL,6
def protected_windows(review):
 need(exact(review['windows'],ALL_WINDOWS),'immutable新scope保護窓');return copy.deepcopy(ALL_WINDOWS)
def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'親unknown全field一致')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),root=copy.deepcopy(ROOT),windows=copy.deepcopy(ALL_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review
def measure(raw):return [dict(address=w['address'],**identity(chunk(raw,w['address'],w['size'])))for w in ALL_WINDOWS]
def _regions(raw,inherited,review,sources):
 keys={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','finite_profile'}
 need(type(review)is dict and set(review)==keys and type(review['schema_version'])is int and review['schema_version']==1,'閉じたreview schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'current/diagnostic分離')
 for k,v in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)):need(exact(review[k],v),'固定review '+k)
 selected=[h for h in inherited['hits']if h['address']in HITS];need(exact(selected,EXPECTED_HITS)and exact(selected,review['hits']),'親unknown全field保持')
 protected_windows(review);source=sources_bind(review,sources);encoding=bind_semantics(raw);d.signed(raw,selected);composition=compose_selected(raw)
 e=evidence_template(HITS[0]);a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_MONEY_REWARD_MINIMUM_THUMB',count=1,hits=list(HITS),source=source,encoding=encoding,composition=composition,protected_windows=len(ALL_WINDOWS),protected_bytes=sum(w['size']for w in ALL_WINDOWS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current0641全体identity gate');return _regions(raw,inherited,review,sources)
validate=_regions
