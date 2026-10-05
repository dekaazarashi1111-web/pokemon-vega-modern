"""TakeItemの実登録根からの条件付き最小Thumb型。ROM I/Oと自然到達は扱わない。"""
import copy
import hashlib
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_callback_party_task as task
import pr16_dex_hof_lifetime_setup as setup
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_runtime_party as runtime
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HIT=0x08120CBD
KIND='rooted_party_takeitem_minimum_thumb'
BOUNDARY={'address':0x08120CBC,'size':6,'sha256':'cf02eb2914f9d3fcb81c5188b9da23aaa74b4b95f415c3152067a731e8f0a2bd'}
HEAP,TASKS,PARTY,MONS,MAIN,CURSOR=0x0203B010,0x030050D0,0x0203B014,0x020241E4,0x03003130,0x0203AD5C
SOURCE_IDS={
 'pret-party_menu.c':dict(local='pret-party_menu.c',repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/party_menu.c',size=211085,sha256='8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b',git_blob_sha='7f3a881e6c56773aee03da475c9a1adc50530223',url='https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/party_menu.c'),
}
# Fixed project source identities; imported review bytes are supplied by the caller.
PROJECT_REFS={
 'runtime_review':('runtime_party',7144,'d879a4f2bba39ef84bbd7eb2e26071f7d78a50a41508a83ca6610879c86ced5a','6e1f102112e3fc38d7cbe88bd42547e778fea870'),
 'party_review':('callback_party',30492,'9aab39682b78ac5199357955cd634ef2ce14d0c4f0b60643dba944f5b7a31691','b310e8ba4cc8292087728fa451a237df1641586c'),
 'setup_review':('lifetime_setup',33229,'2a39c2c125df3a0b23d3bb6048deee5fb4a1911028e6153ac513bd45a6a9eba5','c37a93a509418999f1034ffc84ba130604a19978'),
 'menu_review':('lifetime_menu',21519,'47d5a00dce7d7ee200bd4a4fe3cf6b90a280a5514efcbfbc3c5b47bbcc2fa973','ddbbad16fcb55988cef6389e9fa1bf07ba25e627'),
}
for _key,(_name,_size,_sha,_blob) in PROJECT_REFS.items():
 SOURCE_IDS[_key]=dict(local=_key,repository='dekaazarashi1111-web/pokemon-vega-modern',commit='f90898dd122784f555d0a120f788b06ca8152c4a',path='content/modernization/pr16_dex_hof_'+_name+'_review.json',size=_size,sha256=_sha,git_blob_sha=_blob)

# Independently encoded semantic operands. No raw ROM/opcode sequence.
BLOCKS={}
def put(name,address,specs):BLOCKS[name]=tuple(party.block(address,specs))
put('outer_field_prefix',0x081231D8,[
 ('push',240,True),('movhi',7,10),('movhi',6,9),('movhi',5,8),('push',224,False),('spadd',-8),
 ('movhi',9,0),('shift','lsl',1,1,24),('shift','lsr',1,1,24),('movhi',10,1),
 ('literal',2,0x08123254),('mem',True,'word',1,2,0),('imm','mov',0,0),('mem',False,'byte',0,1,23),
 ('mem',True,'word',1,2,0),('addi',0,1,0),('imm','add',0,15),('imm','add',1,23),('imm','mov',2,0),
 ('call',0x0806F66C),('imm','mov',7,0),('literal',0,0x08123258),('mem',True,'half',0,0,0),
 ('spmem',False,0,0),('movhi',0,9),('imm','add',0,100),('spmem',False,0,4),('imm','mov',4,0),
 ('addi',1,7,1),('movhi',8,1),('spmem',True,0,0),('imm','cmp',0,12),('branch',0,0x0812326C)])
put('outer_field_move_compare',0x0812321C,[
 ('imm','mov',0,100),('movhi',6,10),('alu','mul',6,0),('literal',5,0x08123258),
 ('movhi',1,9),('add',0,1,6),('addi',1,7,0),('imm','add',1,13),('call',0x0803F354),
 ('shift','lsl',1,4,1),('add',1,1,5),('mem',True,'half',1,1,0),('compare',0,1),('branch',1,0x0812325C)])
put('outer_field_move_next',0x0812325C,[
 ('addi',0,4,1),('shift','lsl',0,0,24),('shift','lsr',4,0,24),('shift','lsl',0,4,1),
 ('add',0,0,5),('mem',True,'half',0,0,0),('imm','cmp',0,12),('branch',1,0x08123224)])
put('outer_field_loop_and_second_species',0x0812326C,[
 ('movhi',1,8),('shift','lsl',0,1,24),('shift','lsr',7,0,24),('imm','cmp',7,3),('branch',9,0x08123210),
 ('spmem',True,0,4),('imm','mov',1,11),('call',0x0803F354),('imm','cmp',0,0),('branch',0,0x08123292)])
put('outer_nonmail_item_action_append',0x081232C8,[
 ('literal',0,0x081232F8),('mem',True,'word',1,0,0),('addi',0,1,0),('imm','add',0,15),
 ('imm','add',1,23),('imm','mov',2,3),('call',0x0806F66C)])
put('outer_cancel_append_return',0x081232D8,[
 ('literal',0,0x081232F8),('mem',True,'word',1,0,0),('addi',0,1,0),('imm','add',0,15),
 ('imm','add',1,23),('imm','mov',2,2),('call',0x0806F66C),('spadd',8),('pop',56,False),
 ('movhi',8,3),('movhi',9,4),('movhi',10,5),('pop',240,False),('pop',1,False),('bx',0)])
put('choose_mon_return',0x08120388,[('pop',112,False),('pop',1,False),('bx',0)])
put('item_submenu_producer',0x08123E7C,[
 ('push',48,True),('addi',5,0,0),('shift','lsl',5,5,24),('shift','lsr',5,5,24),('imm','mov',0,5),('call',0x08071A70),
 ('literal',4,0x08123ECC),('mem',True,'word',0,4,0),('imm','add',0,12),('call',0x081224B0),
 ('mem',True,'word',0,4,0),('imm','add',0,13),('call',0x081224B0),
 ('literal',0,0x08123ED0),('literal',1,0x08123ED4),('mem',True,'byte',1,1,9),('imm','mov',2,8),('call',0x08123178),
 ('imm','mov',0,1),('call',0x08122628),('imm','mov',0,25),('call',0x081224D8),
 ('literal',1,0x08123ED8),('shift','lsl',0,5,2),('add',0,0,5),('shift','lsl',0,0,3),('add',0,0,1),
 ('imm','mov',1,255),('mem',False,'half',1,0,8),('literal',1,0x08123EDC),('mem',False,'word',1,0,0),
 ('pop',48,False),('pop',1,False),('bx',0)])
put('take_callback_to_success',0x08124414,[
 ('push',240,True),('shift','lsl',0,0,24),('shift','lsr',7,0,24),('literal',0,0x0812446C),
 ('imm','mov',1,9),('signed_load','byte',1,0,1),('imm','mov',0,100),('alu','mul',1,0),
 ('literal',0,0x08124470),('add',5,1,0),('addi',0,5,0),('imm','mov',1,12),('call',0x0803F354),
 ('shift','lsl',0,0,16),('shift','lsr',6,0,16),('imm','mov',0,5),('call',0x08071A70),
 ('literal',4,0x08124474),('mem',True,'word',0,4,0),('imm','add',0,12),('call',0x081224B0),
 ('mem',True,'word',0,4,0),('imm','add',0,13),('call',0x081224B0),('addi',0,5,0),('call',0x08120E00),
 ('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,0),('branch',0,0x08124478),
 ('imm','cmp',0,1),('branch',0,0x0812449C),('addi',0,5,0),('addi',1,6,0),('imm','mov',2,1),
 ('call',0x08120C9C),('jump',0x081244AA)])
put('take_result_producer',0x08120E00,[
 ('push',16,True),('spadd',-4),('addi',4,0,0),('imm','mov',1,12),('call',0x0803F354),
 ('shift','lsl',0,0,16),('shift','lsr',0,0,16),('movhi',1,13),('mem',False,'half',0,1,0),
 ('imm','cmp',0,0),('branch',1,0x08120E1C),('imm','mov',0,0),('jump',0x08120E3E),
 ('imm','mov',1,1),('call',0x08099A8C),('shift','lsl',0,0,24),('imm','cmp',0,0),('branch',0,0x08120E3C),
 ('imm','mov',1,0),('movhi',0,13),('mem',False,'half',1,0,0),('addi',0,4,0),('imm','mov',1,12),('movhi',2,13),
 ('call',0x0803FA70),('imm','mov',0,2),('jump',0x08120E3E),('imm','mov',0,1),('spadd',4),
 ('pop',16,False),('pop',2,False),('bx',1)])
put('took_item_helper_to_hit',0x08120C9C,[
 ('push',112,True),('addi',6,0,0),('addi',4,1,0),('addi',5,2,0),('shift','lsl',4,4,16),('shift','lsr',4,4,16),
 ('shift','lsl',5,5,24),('shift','lsr',5,5,24),('literal',3,0x08120CE8),('imm','mov',0,8),
 ('addi',1,6,0),('addi',2,4,0),('call',0x080A3554),('literal',1,0x08120CEC),('addi',0,6,0),
 ('call',0x08120AD0),('literal',1,0x08120CF0)])
LITERALS={0x08123254:HEAP,0x08123258:0x08419EFE,0x081232F8:HEAP,
 0x08123ECC:HEAP,0x08123ED0:MONS,0x08123ED4:PARTY,0x08123ED8:TASKS,0x08123EDC:0x08123439,
 0x0812446C:PARTY,0x08124470:MONS,0x08124474:HEAP,0x08120CE8:65535,0x08120CEC:0x02021C4C,0x08120CF0:0x02021C60,
 0x08419DC4:0x08123E7D,0x08419DD4:0x08124415,0x08419EDC:0x08419EAC}
FIELDS={'item_count':(0x08419EF8,1,3),'item_give':(0x08419EAC,1,4),'item_take':(0x08419EAD,1,5),'item_cancel':(0x08419EAE,1,9)}
# Named public field-move ID semantics; final FIELD_MOVE_END is 12.
FIELD_MOVE_IDS=(148,15,19,70,57,249,127,100,91,208,135,230,12)
FIELDS.update({f'field_move_id_{j}':(0x08419EFE+2*j,2,value) for j,value in enumerate(FIELD_MOVE_IDS)})
REUSED={
 'party':(party,('actions_producer','selection_input_prefix','selection_input_and_cancel_filter','selection_confirm_consumer','main_callback_setter','interwork_r1')),
 'task':(task,('run_tasks_field0_dispatch','choose_mon_input','choose_mon_confirm','cursor_pointer_choice','cursor_party_slot','selection_hook_entry','selection_hook_trampoline','actual_action_selector_hook')),
 'menu':(menu,('outer_pokemon_callback_fade_gate','outer_pokemon_callback_install','field_party_constructor_call','field_action_default_to_menu','outer_menu_selector_install','outer_action_menu_builder','outer_type_switch','outer_field_non_egg_type','outer_type_return','mail_held_item_check_and_action_append','action_append','menu_no_wrap_input_prefix','menu_no_wrap_input_tail','cursor_read','cursor_clamp_prefix','cursor_clamp_tail')),
 'setup':(setup,('constructor_1','constructor_2','constructor_3','reset_pointers','set_main_callback','setup_selector','setup_0_2','setup_3_7','setup_8_9','setup_10','setup_11_15','setup_16','setup_17_18','setup_19_20','setup_21_22_increment','setup_default','setup_return','init_callback','scheduler','set_vblank','reset_tasks','memset','create_task_1','create_task_2','insert_task_1','insert_task_2','insert_task_3','find_first_task')),
 'runtime':(runtime,('main_callback_consumer','main_interwork'))}
ALL_BLOCKS={name:(party,rows) for name,rows in BLOCKS.items()};ALL_WORDS=dict(LITERALS)
for scope,(mod,names) in REUSED.items():
 for name in names:
  rows=mod.BLOCKS[name];ALL_BLOCKS[scope+'_'+name]=(mod,rows)
  for ins in rows:
   if ins.kind=='literal':
    a=ins.args[1];need(a not in ALL_WORDS or ALL_WORDS[a]==mod.LITERALS[a],'consistent reused literal');ALL_WORDS[a]=mod.LITERALS[a]
ALL_WORDS.update(setup.TABLE);ALL_WORDS.update({0x0836B380:0x0806EC3D,0x08123320:0x0812334C})
INS={}
for mod,rows in ALL_BLOCKS.values():
 for i in rows:
  if i.address in INS:need(menu.encoded(INS[i.address])==mod.encoded(i),'consistent overlap')
  INS[i.address]=i
WINDOWS={name:(rows[0].address,sum(i.size for i in rows)) for name,(mod,rows) in ALL_BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in sorted(ALL_WORDS)})
WINDOWS.update({name:(a,n) for name,(a,n,v) in FIELDS.items()});WINDOWS['minimal_boundary']=(BOUNDARY['address'],6)
ROOT=dict(kind='existing_start_menu_party_root_to_actual_item_take_callbacks',start_menu_slot=0x0836B380,entry=0x0806EC3C,
 field_callback=0x081277E8,constructor=0x0811F24C,allocation_size=568,setup_state20_call=0x0811F5C4,first_task_function=0x08120319,
 party_scheduler=0x0811F3A8,runtasks=0x08076D10,runtasks_indirect_call=0x08076D2A,actual_action_hook=0x09097A80,
 outer_menu_task_store=0x08123428,selector=0x08123438,outer_nonmail_branch=0x081232AE,item_action_append=0x081232D4,item_action=3,
 item_callback_slot=0x08419DC4,item_callback=0x08123E7C,item_submenu_action_type=8,item_submenu_producer_call=0x08123EA4,
 item_submenu_count=3,item_submenu_actions=[4,5,9],take_input=1,take_action=5,take_callback_slot=0x08419DD4,take_callback=0x08124414,
 try_take_call=0x0812444E,try_take=0x08120E00,try_take_success_store=0x08120E38,try_take_success=2,
 display_helper_call=0x08124464,display_helper=0x08120C9C,questlog_call=0x08120CB4,nickname_call=0x08120CBC,
 nickname_callee=0x08120AD0,static_successor=0x08120CC0)
CLAIMS=dict(proof_scope='conditional_finite_same_selected_task_instruction_type',full_story_reachability_claimed=False,runtime_execution_observed=False,
 universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,field12_getter_effects_proven=False,field11_45_proof_reused_for_field12=False,
 irq_noninterference_proven=False,bl_return_observed=False,whole_function_range_classified=False,maximum_target_access_width_proven=False,
 indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
SELECTION_OUTPUT_SPEC=[
 dict(base='cursor',offset=2,size=1,value=0,role='initial cursor'),
 dict(base='cursor',offset=3,size=1,value=0,role='minimum'),
 dict(base='cursor',offset=4,size=1,value=2,role='maximum'),
 dict(base='cursor',offset=11,size=1,value=1,role='selection sound mode'),
 dict(base='object',offset=12,size=1,value=0,role='valid selection window ID in sufficient profile'),
]
CONTRACT={
 'root':'existing registered StartMenuPokemon callback; selected successful finite continuation only',
 'allocation':'same well-formed aligned 568-byte object and live allocation epoch from constructor through last heap read at 0x08124444; fixed source allocator theorem reused, not a new observed allocation',
 'setup':'existing full constructor/23-state setup CFG reused; callsite-specific success returns and live object/global fields preserved; one finite success on each wait stage',
 'admission':'valid linked task list and one free row at actual state20 CreateTask; selected example uses empty list, not a general requirement',
 'example':'one sufficient profile: slot0, field menuType0/action0, non-egg, nonmail nonzero held item, four move slots without a listed field move (fixture returns0), second-party-species0; extra example choices are not universal necessities',
 'task':'same actual CreateTask result i; active=1, current function and RunTasks membership at each selected dispatch; no whole-task-array freeze',
 'input':'actual no-wrap count3; each conditional DisplaySelectionWindow return initializes cursor0/minimum0/maximum2/soundmode1/object.window12=valid ID0 exactly; finite Down then A yields index1; outer [Summary0,Item3,Cancel2], item [Give4,Take5,Cancel9]',
 'selection_window_outputs':copy.deepcopy(SELECTION_OUTPUT_SPEC),
 'main_callback1':'0x03003130 remains word0 throughout root_setup/outer_builder/item_submenu until each main-dispatch read at 0x08000526; otherwise callback1 executes before callback2 and escapes this selected composition',
 'dispatch_gates':'at each selected task dispatch, fade active bit7 at 0x020379F3 is zero and the called link-wait helper returns0; these are finite input conditions, not an eventual fade/link completion proof',
 'abi':'external returns preserve r4-r11, SP, caller saved-stack contents and valid Thumb return; r0-r3/r12/flags are not assumed preserved',
 'fields_before_take':'preserve heap pointer/epoch, object action bytes15..17 and count23, window bytes12..14 when next read, selected task func/active/list, party menuType/action/slot, input cursor/count/key fields at respective dispatch',
 'field12':'GetMonData at 0x0812329E,0x0812442C,0x08120E08 returns the same selected mon held-item uint16; explicitly conditional external boundary, not field11/45 proof',
 'bag':'AddBagItem at 0x08120E1E consumes held item and quantity1 and returns low-byte nonzero; selected mon/retained item/stack preserved until SetMonData',
 'setter':'SetMonData at 0x08120E34 receives selected mon, field12 and pointer to local halfword0; normal ABI return, selected live registers and saved stack preserved; no transitive getter/setter effect claim',
 'windows':'RemoveWindow calls may update only their selected window byte and window resources within this contract; other future-live party/action/task fields preserved',
 'questlog':'0x08120CB4 receives event8, selected mon, retained original item,65535; normal ABI return preserving r6(mon),r4(item),r5(keepOpen),SP/saved caller stack and readable mon through callsite',
 'hit':'stop before executing GetMonNickname BL; entire BL and adjacent complete LDR are statically encoded; no GetMonNickname return or successor execution is observed'}

def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind_semantics(raw):
 for name,(mod,rows) in ALL_BLOCKS.items():
  for i in rows:need(chunk(raw,i.address,i.size)==mod.encoded(i),'semantic instruction '+name+' '+hex(i.address))
 for a,v in ALL_WORDS.items():need(d.u32(raw,a)==v,'typed literal/table '+hex(a))
 for a,n,v in FIELDS.values():need(int.from_bytes(chunk(raw,a,n),'little')==v,'typed action field')
 need(identity(chunk(raw,BOUNDARY['address'],6))=={k:BOUNDARY[k] for k in ('size','sha256')},'whole BL and static LDR')
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS) and exact(review['source_bindings'],SOURCE_IDS),'closed fixed dependencies')
 for key,b in sources.items():
  need(identity(b)=={k:SOURCE_IDS[key][k] for k in ('size','sha256')},'whole fixed dependency: '+key)
  need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==SOURCE_IDS[key]['git_blob_sha'],'fixed Git blob: '+key)
 text=sources['pret-party_menu.c'].decode()
 for token in ('static void CursorCB_Item(u8 taskId)','static void CursorCB_TakeItem(u8 taskId)',
  'SetPartyMonSelectionActions(gPlayerParty, gPartyMenu.slotId, ACTIONS_ITEM);','sCursorOptions[sPartyMenuInternal->actions[input]].func(taskId);',
  'switch (TryTakeMonItem(mon))','DisplayTookHeldItemMessage(mon, item, TRUE);','ItemUse_SetQuestLogEvent(QL_EVENT_TOOK_HELD_ITEM, mon, item, 0xFFFF);'):
  need(token in text,'pinned public structural role')
 old=json.loads(sources['runtime_review']);need(old['inherited_reviews']==runtime.PRIOR_REFS,'exact existing proof chain')
 need(old['read_mail_type']['root_table']['address']==ROOT['start_menu_slot'],'reuse actual StartMenu root, not ReadMail branch')
def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(WINDOWS),'closed window count')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'address/size/SHA only')
 need(exact([(r['label'],r['address'],r['size']) for r in rows],[(k,*v) for k,v in WINDOWS.items()]),'fixed ordered geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']) for r in rows),'SHA format')
 return [{k:r[k] for k in ('address','size','sha256')} for r in rows]
def evidence_template():
 return dict(schema_version=1,root_verified=True,root=copy.deepcopy(ROOT),input_contract=copy.deepcopy(CONTRACT),claims=copy.deepcopy(CLAIMS),
  instruction_window=dict(BOUNDARY),instructions=[dict(address=0x08120CBC,size=4,role='complete_thumb_bl',callee=0x08120AD0),
  dict(address=0x08120CC0,size=2,role='static_thumb_ldr_return_successor',literal=0x08120CF0)],same_selected_task=True,producer_result=2,literal_pool_included=False,type_classification_only=True)
def witness_geometry(e):
 need(exact(e,evidence_template()),'exact conditional rooted BL/static-successor geometry')
 need(BOUNDARY['address']<=HIT and HIT+4<=BOUNDARY['address']+6,'four hit bytes in complete instructions');return BOUNDARY['address'],6
class Machine(runtime.Machine):
 """Finite inherited VM; only used ALU aliases extended. Instructions bound first."""
 def step(self,branch_choice=None):
  i=self.instructions.get(self.pc)
  if i is not None and i.kind=='alu_ext':
   need(i.args[0] in ('and','neg','orr','mul'),'bounded ALU aliases')
   changed=dict(self.instructions);changed[self.pc]=party.Ins(i.address,'alu',i.args);old=self.instructions;self.instructions=changed
   try:return super().step(branch_choice)
   finally:self.instructions=old
  return super().step(branch_choice)
PHASE_FIELDS={
 'root_setup':['gMain.callback1=0 and callback2/state','party menuType/action/slot','object pointer/epoch/fields0,4,8,10','selected task registration when admitted'],
 'outer_builder':['gMain.callback1=0','object pointer/epoch/window13/actions15..22/count23','party menuType/action/slot','selected task func/active/list','r9 playerParty/r10 slot in saved ABI'],
 'item_submenu':['gMain.callback1=0','object pointer/epoch/window12..14/actions15..17/count23','party slot','same selected task func/active/list','menu cursor/count when initialized'],
 'take_before_last_heap_read':['object pointer/epoch/window12..13','selected mon pointer and retained held item','r7 same taskId','saved caller stack'],
 'try_take':['selected mon pointer','original held item retained in caller r6/saved stack','local item halfword','saved caller stack'],
 'helper':['r6 selected mon','r4 original item','r5 keepOpen','readable selected mon','saved caller stack']}
def selected_profile(held_item=1,bag_result=1,normal_returns=True,fields_preserved=True,stack_nonalias=True):
 need(type(held_item)is int and 0<held_item<=65535,'nonzero uint16 held item')
 need(type(bag_result)is int and 0<bag_result<=255,'bag low byte nonzero')
 need(all(x is True for x in (normal_returns,fields_preserved,stack_nonalias)),'conditional boundaries required')
 return dict(held_item=held_item,bag_result=bag_result,party_slot=0,task_id=0,outer_input=1,item_input=1)

def compose_selected(raw,held_item=1,bag_result=1):
 """One conditional phase composition using synthetic RAM; opaque effects stay open.

 The chosen successful allocator result and each external callee projection are input
 assumptions. Caller-clobbered registers are poisoned. This is not emulation evidence
 of natural play or a proof of all writes by those external callees.
 """
 profile=selected_profile(held_item,bag_result);p=runtime.ROOT+runtime.HEADER;mem=runtime.task_fixture([])
 for a,n in ((p,568),(PARTY,20),(MAIN,1100),(CURSOR,12)):
  for j in range(n):mem[a+j]=0
 runtime.setmem(mem,0x020379F3,1,0)
 assumptions=[];events=[];phase='root_setup';selected=None
 setup_success={0x0811F4D4,0x0811F4FC,0x0811F558,0x0811F578}
 setup_calls={i.address for name in REUSED['setup'][1] if name.startswith('setup_') for i in setup.BLOCKS[name] if i.kind=='call'}
 root_external={0x0806EC54,0x0806EC58,0x0806EC5C,0x0811F37E}
 def run(entry,memory,registers=None,stop=None):
  nonlocal selected,phase
  m=Machine(raw,entry,registers,memory,INS)
  if entry==0x08000510:need(m.read(MAIN,4)==0,'callback1 must remain null before selected callback2 dispatch')
  while m.pc!=0xFFFFFFF0 and m.pc!=stop:
   if m.pc in INS:
    if m.pc==0x0811F5C4:
     need(not runtime.task_chain(m.mem),'selected sufficient empty-list example')
     need(m.reg[0]==0x08120319,'constructor field0 actual CreateTask argument')
    if m.pc==0x0811F5C8:
     selected=m.reg[0];need(selected==0 and selected in runtime.task_chain(m.mem),'actual task admission and membership')
     events.append(dict(role='admitted_same_task',address=0x0811F5C4,task_id=selected))
    if m.pc==0x08123428:events.append(dict(role='outer_selector_registration',task_id=selected,address=m.pc))
    if m.pc==0x08123E7C:need(m.reg[0]==selected,'Item receives selected task');phase='item_submenu'
    if m.pc==0x08124414:need(m.reg[0]==selected,'Take receives same task');phase='take_before_last_heap_read'
    if m.pc==0x08120E00:phase='try_take'
    if m.pc==0x08124452:
     need(m.reg[0]==2,'actual TryTake return2, not opaque return');events.append(dict(role='try_take_actual_return',value=2,address=m.pc))
    if m.pc==0x08120C9C:
     phase='helper';need((m.reg[0],m.reg[1],m.reg[2])==(MONS,held_item,1),'same mon and original held item to helper')
    if m.pc==0x08123512:
     need(m.reg[0] in (0x08419DC4,0x08419DD4),'actual Item or Take callback cell')
     events.append(dict(role='selector_callback',callback_cell=m.reg[0],callback=d.u32(raw,m.reg[0]),task_id=selected))
    m.step();continue
   site=(m.reg[14]&~1)-4;target=m.pc;result=runtime.U;allowed=False;conditional_outputs=[]
   if target in (0x080F6168,0x0813C034):result=0;allowed=site in (0x08000512,0x0800051A)
   elif target==0x08002B9C:
    need(site==0x0811F280 and m.reg[0]==568,'actual constructor Alloc call');result=p;allowed=True
   elif site in root_external:allowed=True
   elif target==0x080C0918:result=0;allowed=site in (0x0811F3DA,0x0812032C,0x0812344A)
   elif target==0x080C08D8:result=1 if phase=='root_setup' and site==0x0811F3F2 else 0;allowed=site in (0x0811F3F2,0x0811F4BC)
   elif site in setup_calls:result=1 if site in setup_success else runtime.U;allowed=True
   elif target in (0x080066D8,0x08006724,0x080F7810,0x0806FC74):allowed=True
   elif target==0x081206EC:need(site==0x0812033E,'actual mon input site');result=1;allowed=True
   elif target==0x08071A70:allowed=True
   elif target==0x081103A8:need(site==0x081104B4,'cursor redraw after clamp');allowed=True
   elif target==0x0803F354:
    field=m.reg[1]
    if site==0x08123350:need(m.reg[0]==MONS and field==45,'selected non-egg');result=0
    elif site==0x0812322C:need(m.reg[0]==MONS and field in (13,14,15,16),'bounded field-move comparison');result=0
    elif site==0x0812327A:need(m.reg[0]==MONS+100 and field==11,'second slot absent in selected profile');result=0
    else:
     need(site in (0x0812329E,0x0812442C,0x08120E08) and m.reg[0]==MONS and field==12,'new field12 boundaries only');result=held_item
    allowed=True
   elif target==0x08097AE8:need(site==0x081232A6 and m.reg[0]==held_item,'actual nonmail check');result=0;allowed=True
   elif target==0x08120AD0:need(site==0x081233C6 and m.reg[0]==MONS,'outer nickname only; hit not executed');allowed=True
   elif target==0x081224B0:
    need(m.reg[0] in (p+12,p+13,p+14),'window exact object field');m.write(m.reg[0],1,255);allowed=True
   elif target==0x08122628:
    need(m.reg[0] in (0,1),'actual outer or Item window');need(m.read(p+23,1)==3,'actual count3 before menu setup')
    # These five conditional outputs are required, not proved callee effects.
    conditional_outputs=selection_initialization(p,m.reg[0],m.read(p+23,1),SELECTION_OUTPUT_SPEC)
    for field in conditional_outputs:m.write(field['address'],field['size'],field['value'])
    need(all(m.read(f['address'],f['size'])==f['value'] for f in conditional_outputs),'declared selection outputs agree with actual modeled cells')
    allowed=True
   elif target in (0x081224D8,0x08122904):allowed=True
   elif target==0x08099A8C:
    need(site==0x08120E1E and (m.reg[0],m.reg[1])==(held_item,1),'bag item and quantity1');result=bag_result;allowed=True
   elif target==0x0803FA70:
    need(site==0x08120E34 and (m.reg[0],m.reg[1])==(MONS,12) and m.read(m.reg[2],2)==0,'setter field12 actual local zero');allowed=True
   elif target==0x080A3554:
    need(site==0x08120CB4 and tuple(m.reg[:4])==(8,MONS,held_item,65535),'QuestLog event8 arguments');allowed=True
   need(allowed,'unlisted boundary '+hex(site)+' -> '+hex(target))
   assumptions.append(dict(site=site,target=target,phase=phase,required_fields=PHASE_FIELDS[phase],normal_abi_return_required=True,effects_discharged=False,
    return_value=result if runtime.concrete(result) else 'unspecified',conditional_outputs=conditional_outputs))
   for r in (0,1,2,3,12):m.reg[r]=runtime.U
   m.reg[0]=result;m.flag_pc=None;m.pc=m.reg[14]&~1
  if stop is None:need(m.reg[13]==0x03007000,'phase stack balanced')
  return m
 m=run(d.u32(raw,ROOT['start_menu_slot'])&~1,mem)
 need(m.read(MAIN+4,4)==0x081277E9,'StartMenu callback installs constructor')
 m=run(0x08000510,m.mem)
 need(m.read(MAIN+4,4)==0x0811F3D9 and m.read(p,4)==0x08120319,'constructor installs init and same task field0')
 for stage in range(24):
  need(m.read(MAIN+1080,1)==stage,'actual setup state producer chain');m=run(0x08000510,m.mem)
 need(selected==0 and m.read(MAIN+4,4)==0x0811F3A9,'finite setup to actual party scheduler')
 phase='outer_builder';m=run(0x08000510,m.mem)
 need(m.read(TASKS,4)==0x08123439 and [m.read(p+15+j,1) for j in range(3)]==[0,3,2] and m.read(p+23,1)==3,'actual nonmail producer and same selector task')
 def input_frame(m,down=False):
  runtime.setmem(m.mem,MAIN+46,2,0 if down else 1);runtime.setmem(m.mem,MAIN+48,2,128 if down else 0)
  need(selected in runtime.task_chain(m.mem) and m.read(TASKS,4)==0x08123439,'same selected active/list/function before dispatch')
  return run(0x08000510,m.mem,stop=BOUNDARY['address'] if not down and phase=='item_submenu' else None)
 m=input_frame(m,True);need(m.read(CURSOR+2,1)==1,'Down produces outer cursor1')
 m=input_frame(m)
 need(phase=='item_submenu' and [m.read(p+15+j,1) for j in range(3)]==[4,5,9] and m.read(p+23,1)==3,'Item action8 produces Give/Take/Cancel')
 need(m.read(TASKS,4)==0x08123439,'Item registers same selected row selector')
 m=input_frame(m,True);need(m.read(CURSOR+2,1)==1,'Down produces Item cursor1');m=input_frame(m)
 need(m.pc==BOUNDARY['address'] and (m.reg[0],m.reg[1])==(MONS,0x02021C4C),'same mon at rooted complete BL')
 return dict(status='PASS_CONDITIONAL_ACTUAL_STARTMENU_SETUP_SAME_TASK_ITEM_TAKE',profile=profile,selected_task=selected,
  outer_actions=[0,3,2],item_actions=[4,5,9],try_take_result=2,reached_instruction=BOUNDARY['address'],static_successor=0x08120CC0,
  events=events,conditional_calls=assumptions,phase_fields=PHASE_FIELDS,
  required_live_projections={phase:live_projection(p,phase) for phase in PHASE_FIELDS},synthetic_contract_execution=True,actual_runtime_execution_observed=False,callee_at_hit_executed=False)

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract'},'closed review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'review schema version')
 need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE),'fixed current candidate')
 need(exact(review['diagnostic_input'],DIAGNOSTIC),'diagnostic distinct from current')
 need(exact(review['root'],ROOT) and exact(review['claims'],CLAIMS) and exact(review['input_contract'],CONTRACT),'exact bounded contract')
 originals=[h for h in inherited['hits'] if h['address']==HIT]
 need(len(originals)==1 and exact(originals[0],review['hit']) and originals[0]['accepted'] is False and originals[0]['owner_candidates']==[],'one unchanged owner-external unknown')
 need(type(originals[0]['size'])is int and originals[0]['size']==4 and originals[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','four-byte all-start hit')
 d.signed(raw,originals[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));bind_semantics(raw)
 composition=compose_selected(raw);composition['callback1_counterexample']=callback1_counterexample(raw);evidence=evidence_template();a,n=witness_geometry(evidence)
 return [d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_PARTY_TAKEITEM_MINIMUM_TYPE',count=1,hit=HIT,
  protected_windows=len(WINDOWS),protected_bytes=sum(n for a,n in WINDOWS.values()),composition=composition,source_bindings=SOURCE_IDS,**CLAIMS)
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current required; diagnostic cannot classify current')
 return _regions(raw,inherited,review,sources)
def try_take_result(raw,held_item,bag_result,setter_returns=True):
 """Actual finite result producer and its conditional 0/1/2 branch partition."""
 need(type(held_item)is int and 0<=held_item<=65535,'held-item uint16 domain')
 need(type(bag_result)is int and 0<=bag_result<=255,'bag byte domain')
 rows={i.address:i for i in BLOCKS['take_result_producer']};m=Machine(raw,0x08120E00,{0:MONS},{},rows);calls=[]
 while m.pc!=0xFFFFFFF0:
  if m.pc in rows:m.step();continue
  site=(m.reg[14]&~1)-4;target=m.pc;calls.append(site)
  if (site,target)==(0x08120E08,0x0803F354):need((m.reg[0],m.reg[1])==(MONS,12),'actual getter12');result=held_item
  elif (site,target)==(0x08120E1E,0x08099A8C):need((m.reg[0],m.reg[1])==(held_item,1),'actual bag arguments');result=bag_result
  elif (site,target)==(0x08120E34,0x0803FA70):
   need(setter_returns is True,'explicit normal setter return');need((m.reg[0],m.reg[1])==(MONS,12) and m.read(m.reg[2],2)==0,'actual local zero setter');result=runtime.U
  else:raise ValueError('TryTake escaped its three boundaries')
  for r in (0,1,2,3,12):m.reg[r]=runtime.U
  m.reg[0]=result;m.pc=m.reg[14]&~1;m.flag_pc=None
 need(m.reg[13]==0x03007000,'TryTake stack balanced')
 return dict(result=m.reg[0],calls=calls,setter_called=0x08120E34 in calls,synthetic_contract_execution=True)

def live_projection(pointer,phase,task_id=0,task_admitted=True):
 """Concrete memory roles for finite conditional intervals, separate from callee proof.

 Opaque calls may write their documented outputs. This function describes the other
 live fields they must preserve. ABI registers/saved stack and semantic mon getter
 values are separate obligations, not guessed physical Pokemon field offsets.
 """
 need(type(pointer)is int and pointer%4==0 and runtime.ROOT+16<=pointer<=runtime.ROOT+runtime.LIMIT-568,'allocator-derived geometry')
 need(phase in PHASE_FIELDS,'fixed phase')
 need(type(task_id)is int and 0<=task_id<16 and type(task_admitted)is bool,'selected task domain')
 fields=[]
 def add(a,n,role):fields.append(dict(address=a,size=n,role=role))
 if phase in ('root_setup','outer_builder','item_submenu','take_before_last_heap_read'):
  add(HEAP,4,'same object pointer');add(pointer-16,8,'live allocation used/magic/extent')
 if phase in ('root_setup','outer_builder','item_submenu'):add(MAIN,4,'null callback1 read before callback2')
 if phase=='root_setup':
  add(pointer,12,'constructor task/exit/control fields');add(PARTY+8,4,'menu type/slot/action');add(MAIN+4,4,'registered main callback');add(MAIN+1080,1,'setup state')
 if phase in ('outer_builder','item_submenu'):
  add(pointer+12,12,'window IDs/actions/count');add(PARTY+8,4,'menu type/slot/action');add(MAIN+4,4,'party scheduler callback')
  add(CURSOR+2,3,'cursor/minimum/maximum');add(CURSOR+11,1,'selection sound mode');add(MAIN+46,4,'selected key/new-repeat inputs');add(0x020379F3,1,'finite fade gate')
 if phase=='take_before_last_heap_read':add(pointer+12,2,'next window IDs')
 if task_admitted and phase in ('root_setup','outer_builder','item_submenu'):add(TASKS+40*task_id,7,'same task function/active/previous/next; whole membership separately')
 return fields

def preservation_contract(pointer,phase,writes,task_id=0,task_admitted=True,freed=(),heap_reinitialized=False):
 """Reject a declared write intersecting live projection; not a callee effect analysis."""
 fields=live_projection(pointer,phase,task_id,task_admitted)
 if phase in ('root_setup','outer_builder','item_submenu','take_before_last_heap_read'):
  need(heap_reinitialized is False and pointer not in freed,'live epoch cannot be replaced by an ABA pointer/header')
 for a,n in writes:
  need(type(a)is int and type(n)is int and n>0 and 0<=a<a+n<=1<<32,'bounded declared write')
  need(all(runtime.disjoint(a,n,f['address'],f['size']) for f in fields),'declared write intersects future-live field')
 return True


def selection_initialization(pointer,kind,count,spec):
 """Exact five-output conditional boundary; no DisplaySelectionWindow effect proof."""
 need(type(pointer)is int and pointer%4==0 and runtime.ROOT+16<=pointer<=runtime.ROOT+runtime.LIMIT-568,'selection object geometry')
 need(type(kind)is int and kind in (0,1) and type(count)is int and count==3,'outer/Item count3 initialization boundary')
 need(exact(spec,SELECTION_OUTPUT_SPEC),'all five exact conditional selection outputs required')
 return [dict(address=(CURSOR if f['base']=='cursor' else pointer)+f['offset'],size=f['size'],value=f['value'],role=f['role']) for f in spec]

def callback1_counterexample(raw):
 """Actual Main dispatch, comparing null callback1 against one field overwrite.

 No alternate callback body is executed. The changed cell is the only difference,
 and the actual LDR/CMP/BL/BX sequence diverts before callback2 is read.
 """
 out=[]
 for callback1 in (0,0x08124415):
  mem={};runtime.setmem(mem,MAIN,4,callback1);runtime.setmem(mem,MAIN+4,4,0x0811F3A9)
  m=Machine(raw,0x08000510,memory=mem,instructions=INS)
  while m.pc not in (0x08124414,0x0811F3A8):
   if m.pc in (0x080F6168,0x0813C034):
    for r in (0,1,2,3,12):m.reg[r]=runtime.U
    m.reg[0]=0;m.pc=m.reg[14]&~1;m.flag_pc=None
   else:m.step()
  out.append(dict(callback1=callback1,first_callback_entry=m.pc,indirect_call=m.calls[-1][0]))
 need(out[0]['first_callback_entry']==0x0811F3A8 and out[0]['indirect_call']==0x08000536,'null callback1 permits callback2 first')
 need(out[1]['first_callback_entry']==0x08124414 and out[1]['indirect_call']==0x0800052C,'nonzero callback1 diverts before callback2')
 return dict(status='PASS_ACTUAL_CALLBACK1_FIELD_COUNTEREXAMPLE',cases=out,alternate_body_executed=False,synthetic_contract_execution=True)
