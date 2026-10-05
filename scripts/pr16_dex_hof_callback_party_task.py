"""通常tutor rootからparty taskへの局所機械診断。未証明lifetimeを昇格しない。"""
import pr16_dex_hof_callback_party as shared

Ins, block, encoded = shared.Ins, shared.block, shared.encoded
need, chunk, identity, d = shared.need, shared.chunk, shared.identity, shared.d
HIT = 0x08126B0B
TASKS, HEAP_CELL = 0x030050D0, 0x0203B010
COMMON = (
    'constructor_entry', 'constructor_success_fields', 'constructor_callback_tail',
    'constructor_reset', 'init_callback', 'init_state_selector',
    'state20_task_consumer', 'state_increment', 'state_default_scheduler_registration',
    'party_scheduler', 'main_callback_setter', 'interwork_r1',
)
BLOCKS = {name: tuple(shared.BLOCKS[name]) for name in COMMON}

def put(name, address, specs):
    BLOCKS[name] = tuple(block(address, specs))

# special397の実登録。ScriptReadHalfword後のindex*4と実end境界を束縛。
put('special_dispatch',0x080697BC,[('push',0,True),('call',0x080691B8),
 ('shift','lsl',0,0,16),('shift','lsr',0,0,14),('literal',1,0x080697D8),('add',1,0,1),
 ('literal',0,0x080697DC),('compare',1,0),('branch',2,0x080697E0),('mem',True,'word',0,1,0),
 ('call',0x081C7AC8),('jump',0x080697EC)])
put('interwork_r0',0x081C7AC8,[('bx',0)])
put('tutor_root_normal_constructor',0x08128154,[('push',0,True),('spadd',-12),
 ('literal',0,0x0812817C),('mem',True,'half',0,0,0),('imm','cmp',0,14),('branch',8,0x08128188),
 ('imm','mov',0,4),('spmem',False,0,0),('literal',0,0x08128180),('spmem',False,0,4),
 ('literal',0,0x08128184),('spmem',False,0,8),('imm','mov',0,0),('imm','mov',1,0),
 ('imm','mov',2,12),('imm','mov',3,0),('call',0x0811F24C),('jump',0x081281A8)])

# CreateTaskの空slot成功枝。r0のfuncをr2に退避し同じstride40のfield0へ置く。
put('create_task_success',0x08076BB4,[('push',0xF0,True),('addi',2,0,0),
 ('shift','lsl',1,1,24),('shift','lsr',1,1,24),('imm','mov',6,0),('literal',7,0x08076BF0),
 ('shift','lsl',0,6,2),('add',0,0,6),('shift','lsl',5,0,3),('add',4,5,7),
 ('mem',True,'byte',0,4,4),('imm','cmp',0,0),('branch',1,0x08076BF4),('mem',False,'word',2,4,0),
 ('mem',False,'byte',1,4,7),('addi',0,6,0),('call',0x08076C08),('addi',0,7,0),
 ('imm','add',0,8),('add',0,5,0),('imm','mov',1,0),('imm','mov',2,32),('call',0x081C9DF8),
 ('imm','mov',0,1),('mem',False,'byte',0,4,4),('addi',0,6,0),('jump',0x08076C00)])
put('run_tasks_field0_dispatch',0x08076D10,[('push',0x30,True),('call',0x08076D40),
 ('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,16),('branch',0,0x08076D34),
 ('literal',5,0x08076D3C),('shift','lsl',4,0,2),('add',4,4,0),('shift','lsl',4,4,3),('add',4,4,5),
 ('mem',True,'word',1,4,0),('call',0x081C7ACC),('mem',True,'byte',0,4,6),('imm','cmp',0,255),
 ('branch',1,0x08076D20),('pop',0x30,False),('pop',1,False),('bx',0)])

# fade/link待機解除後、button handlerの戻り1を取る局所経路。
put('choose_mon_input',0x08120318,[('push',0x70,True),('shift','lsl',0,0,24),('shift','lsr',5,0,24),
 ('addi',6,5,0),('literal',0,0x08120354),('mem',True,'byte',1,0,7),('imm','mov',0,128),('alu','and',0,1),
 ('imm','cmp',0,0),('branch',1,0x08120388),('call',0x080C0918),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
 ('imm','cmp',0,1),('branch',0,0x08120388),('call',0x08120394),('addi',4,0,0),('call',0x081206EC),
 ('shift','lsl',0,0,16),('shift','lsr',0,0,16),('imm','cmp',0,2),('branch',0,0x08120368),
 ('imm','cmp',0,2),('branch',12,0x08120358),('imm','cmp',0,1),('branch',0,0x0812035E),('jump',0x08120388)])
put('choose_mon_confirm',0x0812035E,[('addi',0,5,0),('addi',1,4,0),('call',0x081203B4),('jump',0x08120388)])
put('cursor_pointer_choice',0x08120394,[('push',0,True),('literal',0,0x081203A8),('mem',True,'byte',1,0,11),
 ('imm','cmp',1,8),('branch',0,0x081203A2),('imm','cmp',1,10),('branch',1,0x081203AC),('imm','add',0,10),('jump',0x081203AE)])
put('cursor_party_slot',0x081203AC,[('imm','add',0,9),('pop',2,False),('bx',1)])
put('selection_hook_entry',0x081203B4,[('push',0x70,True),('addi',5,1,0),('shift','lsl',0,0,24),('shift','lsr',6,0,24),
 ('imm','mov',0,0),('signed_load','byte',0,5,0),('imm','cmp',0,6),('branch',1,0x081203D4)])
put('selection_hook_trampoline',0x081203D4,[('literal',0,0x081203D8),('bx',0)])
put('actual_action_selector_hook',0x09097A80,[('literal',0,0x09097AA4),('mem',True,'byte',0,0,11),('imm','sub',0,3),
 ('imm','cmp',0,12),('branch',0,0x09097A92),('imm','cmp',0,10),('branch',9,0x09097A9E),('literal',0,0x09097AA8),('bx',0)])
put('actual_action_selector_resume',0x09097A9E,[('literal',1,0x09097AB0),('bx',1)])
put('action9_table_consumer',0x081203E0,[('shift','lsl',0,0,2),('literal',1,0x081203F0),('add',0,0,1),
 ('mem',True,'word',0,0,0),('movhi',15,0)])
put('action9_tutor_call',0x0812047C,[('addi',0,5,0),('call',0x0812054C),('shift','lsl',0,0,24),('imm','cmp',0,0),
 ('branch',0,0x08120546),('imm','mov',0,5),('call',0x08071A70),('addi',0,6,0),('call',0x08127704),('jump',0x08120546)])
put('non_egg_success',0x0812054C,[('push',0,True),('mem',True,'byte',1,0,0),('imm','mov',0,100),('alu','mul',0,1),
 ('literal',1,0x08120568),('add',0,0,1),('imm','mov',1,45),('call',0x0803F354),('imm','cmp',0,1),
 ('branch',0,0x0812056C),('imm','mov',0,1),('jump',0x08120574)])
put('non_egg_return',0x08120574,[('pop',2,False),('bx',1)])

# 通常tutor適合・未習得・4技満杯の分岐。taskIdはr6で保持。
put('tutor_try_eligible_full_moves',0x08127704,[('push',0xF0,True),('movhi',7,8),('push',128,False),
 ('shift','lsl',0,0,24),('shift','lsr',6,0,24),('literal',0,0x08127784),('mem',True,'byte',1,0,7),
 ('imm','mov',0,128),('alu','and',0,1),('imm','cmp',0,0),('branch',1,0x081277D0),
 ('literal',7,0x08127788),('imm','mov',1,9),('signed_load','byte',1,7,1),('imm','mov',0,100),('alu','mul',1,0),
 ('literal',0,0x0812778C),('add',5,1,0),('imm','mov',0,14),('add',0,0,7),('movhi',8,0),
 ('literal',1,0x08127790),('addi',0,5,0),('call',0x08120AD0),('literal',4,0x08127794),('mem',True,'byte',0,4,0),
 ('call',0x08121398),('mem',False,'half',0,7,14),('literal',0,0x08127798),('imm','mov',2,14),('signed_load','half',1,7,2),
 ('shift','lsl',1,1,4),('literal',2,0x0812779C),('add',1,1,2),('call',0x08008900),('imm','mov',0,2),
 ('movhi',1,8),('mem',False,'half',0,1,2),('mem',True,'byte',2,4,0),('addi',0,5,0),('imm','mov',1,0),
 ('call',0x08121310),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',0,0x081277A4),
 ('imm','cmp',0,2),('branch',0,0x081277AC),('mem',True,'half',1,7,14),('addi',0,5,0),('call',0x0803E008),
 ('shift','lsl',0,0,16),('literal',1,0x081277A0),('compare',0,1),('branch',0,0x081277BC)])
put('tutor_install_replace_prompt',0x081277BC,[('literal',0,0x081277DC),('call',0x0812643C),('literal',1,0x081277E0),
 ('shift','lsl',0,6,2),('add',0,0,6),('shift','lsl',0,0,3),('add',0,0,1),('literal',1,0x081277E4),('mem',False,'word',1,0,0),
 ('pop',8,False),('movhi',8,3),('pop',0xF0,False),('pop',1,False),('bx',0)])
put('replace_prompt_to_input',0x081266D0,[('push',16,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('call',0x08120B60),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',0,0x081266F4),
 ('call',0x081227D8),('literal',0,0x081266FC),('shift','lsl',1,4,2),('add',1,1,4),('shift','lsl',1,1,3),
 ('add',1,1,0),('literal',0,0x08126700),('mem',False,'word',0,1,0),('pop',16,False),('pop',1,False),('bx',0)])
put('replace_input_no_branch',0x08126704,[('push',16,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('call',0x08110BF8),('shift','lsl',0,0,24),('shift','asr',1,0,24),('imm','cmp',1,0),('branch',0,0x0812672A),
 ('imm','cmp',1,0),('branch',12,0x08126724),('imm','mov',0,1),('alu','neg',0,0),('compare',1,0),('branch',0,0x08126750),
 ('jump',0x0812675C),('imm','cmp',1,1),('branch',0,0x08126756),('jump',0x0812675C)])
put('replace_input_no_call',0x08126756,[('addi',0,4,0),('call',0x08126A20),('pop',16,False),('pop',1,False),('bx',0)])
put('stop_learning_prompt_writer',0x08126A20,[('push',0x30,True),('addi',5,0,0),('shift','lsl',5,5,24),('shift','lsr',5,5,24),
 ('literal',0,0x08126A68),('literal',1,0x08126A6C),('imm','mov',2,14),('signed_load','half',1,1,2),('shift','lsl',1,1,4),
 ('literal',2,0x08126A70),('add',1,1,2),('call',0x08008900),('literal',4,0x08126A74),('literal',1,0x08126A78),
 ('addi',0,4,0),('call',0x08008B48),('addi',0,4,0),('imm','mov',1,1),('call',0x08120AE8),('imm','mov',0,2),('call',0x080F77FC),
 ('literal',1,0x08126A7C),('shift','lsl',0,5,2),('add',0,0,5),('shift','lsl',0,0,3),('add',0,0,1),
 ('literal',1,0x08126A80),('mem',False,'word',1,0,0),('pop',0x30,False),('pop',1,False),('bx',0)])
put('stop_learning_to_input',0x08126A84,[('push',16,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('call',0x08120B60),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',0,0x08126AA8),
 ('call',0x081227D8),('literal',0,0x08126AB0),('shift','lsl',1,4,2),('add',1,1,4),('shift','lsl',1,1,3),('add',1,1,0),
 ('literal',0,0x08126AB4),('mem',False,'word',0,1,0),('pop',16,False),('pop',1,False),('bx',0)])
put('stop_learning_input_yes',0x08126AB8,[('push',0xF0,True),('shift','lsl',0,0,24),('shift','lsr',6,0,24),
 ('literal',7,0x08126AE8),('imm','mov',1,9),('signed_load','byte',1,7,1),('imm','mov',0,100),('alu','mul',1,0),
 ('literal',0,0x08126AEC),('add',4,1,0),('call',0x08110BF8),('shift','lsl',0,0,24),('shift','asr',5,0,24),
 ('imm','cmp',5,0),('branch',0,0x08126AF6)])
put('hit_complete_stringcopy_and_ldr',0x08126AF6,[('literal',1,0x08126B38),('addi',0,4,0),('call',0x08120AD0),
 ('literal',0,0x08126B3C),('imm','mov',2,14),('signed_load','half',1,7,2),('shift','lsl',1,1,4),('literal',2,0x08126B40),
 ('add',1,1,2),('call',0x08008900),('literal',4,0x08126B44)])

LITERALS = {i.args[1]:shared.LITERALS[i.args[1]] for name in COMMON for i in BLOCKS[name] if i.kind=='literal'}
LITERALS.update({
 0x080697D8:0x08163068,0x080697DC:0x08163758,0x0816369C:0x08128155,
 0x0812817C:0x02036FF6,0x08128180:0x08120319,0x08128184:0x080561A1,
 0x0811F47C:0x0811F5BC,0x08076BF0:TASKS,0x08076D3C:TASKS,
 0x08120354:0x020379EC,0x081203A8:0x0203B014,0x081203D8:0x09097A81,
 0x09097AA4:0x0203B014,0x09097AA8:0x0812053B,0x09097AB0:0x081203E1,
 0x081203F0:0x081203F4,0x08120418:0x0812047C,0x08120568:0x020241E4,
 0x08127784:0x020379EC,0x08127788:0x0203B014,0x0812778C:0x020241E4,0x08127790:0x02021C4C,
 0x08127794:0x02036FF6,0x08127798:0x02021C60,0x0812779C:0x090453C8,0x081277A0:0xFFFF0000,
 0x081277DC:0x083DE0C2,0x081277E0:TASKS,0x081277E4:0x081266D1,
 0x081266FC:TASKS,0x08126700:0x08126705,
 0x08126A68:0x02021C60,0x08126A6C:0x0203B014,0x08126A70:0x090453C8,0x08126A74:0x02021C88,
 0x08126A78:0x083DE113,0x08126A7C:TASKS,0x08126A80:0x08126A85,
 0x08126AB0:TASKS,0x08126AB4:0x08126AB9,0x08126AE8:0x0203B014,0x08126AEC:0x020241E4,
 0x08126B38:0x02021C4C,0x08126B3C:0x02021C60,0x08126B40:0x090453C8,0x08126B44:0x02021C88,
})
BLOCKERS = (
 'constructor_fields_to_callback_tail_complete_cfg_not_bound',
 'all_setup_states_and_success_conditions_not_bound',
 'same_allocation_and_task_lifetime_across_opaque_calls_not_proven',
 'input_and_tutor_helper_return_conditions_not_proven',
 'whole_current_candidate_and_sources_delegated_to_parent_wrapper',
)

def make_review(raw):
    """reviewにはaddress/size/SHAだけを保存。原本byteと私有pathを含めない。"""
    def window(address,size): return dict(address=address,**identity(chunk(raw,address,size)))
    return dict(
        instruction_windows={name:window(rows[0].address,sum(i.size for i in rows)) for name,rows in BLOCKS.items()},
        literal_words={str(a):window(a,4) for a in LITERALS},
        hit=window(HIT,4), minimal_instruction_window=window(HIT-1,6))

def _window(raw,w,address,size):
    need(isinstance(w,dict) and set(w)=={'address','size','sha256'},'address/size/SHA record only')
    need(type(w['address']) is int and type(w['size']) is int,'integer window geometry')
    need((w['address'],w['size'])==(address,size),'fixed semantic window geometry')
    d.signed(raw,w)

def check_local(raw,review):
    """局所の実登録と命令意味を確認。unknown維持、TypedRegionは発行しない。"""
    need(set(review)=={'instruction_windows','literal_words','hit','minimal_instruction_window'},'closed diagnostic review schema')
    need(set(review['instruction_windows'])==set(BLOCKS),'every fixed instruction block')
    for name,rows in BLOCKS.items():
        _window(raw,review['instruction_windows'][name],rows[0].address,sum(i.size for i in rows))
        for ins in rows:
            need(chunk(raw,ins.address,ins.size)==encoded(ins),'semantic constraint: '+name+' '+ins.kind)
    need(set(review['literal_words'])=={str(a) for a in LITERALS},'every fixed pointer role')
    for a,value in LITERALS.items():
        _window(raw,review['literal_words'][str(a)],a,4)
        need(d.u32(raw,a)==value,'exact literal role')
    _window(raw,review['hit'],HIT,4)
    _window(raw,review['minimal_instruction_window'],HIT-1,6)
    need(shared.code.thumb_bl(chunk(raw,HIT-1,4),HIT-1)==0x08008900,'complete StringCopy BL crossing hit')
    return dict(status='PASS_LOCAL_PARTY_TASK_CONSUMERS_NOT_ACCEPTED',role='party_move_tutor_stop_learning',
        hit=HIT,special_id=397,actual_special_registration_bound=True,
        sixth_stack_argument_local_flow_bound=True,local_task_field0_rewrites_bound=True,
        semantic_instruction_count=sum(map(len,BLOCKS.values())),instruction_window_count=len(BLOCKS),
        full_root_to_hit_lifetime_proven=False,newly_classified=0,donor_eligible=False,
        current_acceptance_claimed=False,unresolved_obligations=list(BLOCKERS))

def regions(raw,review,*args,**kwargs):
    check_local(raw,review)
    raise ValueError('party setup and same-allocation/task lifetime remain unproven; unknown retained')
