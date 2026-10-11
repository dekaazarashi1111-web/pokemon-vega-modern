"""Mystery Giftのmask literal / Thumb命令境界。有限の条件付き型証明だけを扱う。

二つのplacement経路は相互排他的。現実行、自然到達、全heap寿命、donor安全性は
主張しない。私有ROMのI/Oは行わず、全入力を呼出し側から受け取る。
"""
import copy
import hashlib
import json

import pr16_dex_hof_donor as d
from pr16_dex_hof_script_engine import ThumbConsumer
from pr16_dex_hof_reference_gaps import CANDIDATE

need, identity, chunk = d.need, d.identity, d.chunk
HIT = 0x08142F5D
KIND = 'rooted_mask_literal_thumb_boundary'
COMMIT = 'c75f352304d529f6ba92d4f74b9cf8b5c3810788'
DIAGNOSTIC = {'size': 33554432, 'sha256': '06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5'}
SOURCE_IDS = {}
for _name, _path, _size, _sha, _blob in (
    ('pret-mystery_gift_menu.c', 'src/mystery_gift_menu.c', 47233, '0bb89d37bbd201f4b5ec59f5cf66582bc467b01df419ddb3593b254a70a5f215', '77c032c1b1d3360ff5fb87070815c4a98019df8c'),
    ('pret-task.c', 'src/task.c', 5029, '8bdd5205ec396be7b66d6e384a82309b3cab59783d46fb8c4c991b2172d4868b', '01503dc7ae78cf2348524bfb5bbb89183640f944'),
    ('pret-main.c', 'src/main.c', 11699, '0bfa6c662b1cbd49bd31020b6c2509208004611e6701ad64badce22eca371139', '542b0f5d16dd93107523d11163bfcb70a42b707a'),
):
    SOURCE_IDS[_name] = dict(local=_name, repository='pret/pokefirered', commit=COMMIT,
        path=_path, url=f'https://github.com/pret/pokefirered/blob/{COMMIT}/{_path}',
        size=_size, sha256=_sha, git_blob_sha=_blob)

# 以下は実命令の意味別operand契約。ROMから生成したopcode列ではない。
# 選択窓の全命令を独立encoderで拘束する。BL以外は各2byte。
BLOCKS = {
 'main_setter': (0x08000544, [
  ('lit',1,0x08000554),('str',0,1,4),('mov',0,135),('lsl',0,0,3),
  ('addreg',1,1,0),('mov',0,0),('strb',0,1,0),('bx',14)]),
 'main_dispatch': (0x08000510, [
  ('push',16,True),('bl',0x080F6168),('cmp',0,0),('bc',1,0x0800053A),
  ('bl',0x0813C034),('lsl',0,0,24),('cmp',0,0),('bc',1,0x0800053A),
  ('lit',4,0x08000540),('ldr',0,4,0),('cmp',0,0),('bc',0,0x08000530),
  ('bl',0x081C7AC8),('ldr',0,4,4),('cmp',0,0),('bc',0,0x0800053A),
  ('bl',0x081C7AC8),('pop',16),('pop',1),('bx',0)]),
 'bx_r0': (0x081C7AC8,[('bx',0)]),
 'bx_r1': (0x081C7ACC,[('bx',1)]),
 'initializer_success_guard_registration_constructor': (0x081429CC,[
  ('push',0,True),('mov',0,0),('bl',0x081427C8),('cmp',0,0),('bc',0,0x081429E8),
  ('lit',0,0x081429EC),('bl',0x08000544),('lit',1,0x081429F0),('mov',0,0),
  ('strb',0,1,0),('bl',0x08143560),('pop',1),('bx',0)]),
 'registered_cb2_calls_runtasks_first': (0x081427B0,[('push',0,True),('bl',0x08076D10),
  ('bl',0x08002DD0),('bl',0x080066D8),('bl',0x08006724),('pop',1),('bx',0)]),
 'create_task_selected_free_row': (0x08076BB4,[
  ('push',240,True),('addi',2,0,0),('lsl',1,1,24),('lsr',1,1,24),
  ('mov',6,0),('lit',7,0x08076BF0),('lsl',0,6,2),('addreg',0,0,6),
  ('lsl',5,0,3),('addreg',4,5,7),('ldrb',0,4,4),('cmp',0,0),('bc',1,0x08076BF4),
  ('str',2,4,0),('strb',1,4,7),('addi',0,6,0),('bl',0x08076C08),
  ('addi',0,7,0),('add',0,8),('addreg',0,5,0),('mov',1,0),('mov',2,32),
  ('bl',0x081C9DF8),('mov',0,1),('strb',0,4,4),('addi',0,6,0),('b',0x08076C00)]),
 'create_task_return': (0x08076C00,[('pop',240),('pop',2),('bx',1)]),
 'insert_selected_task_into_empty_list': (0x08076C08,[
  ('push',240,True),('movhi',7,8),('push',128,False),('lsl',0,0,24),('lsr',4,0,24),
  ('bl',0x08076D40),('lsl',0,0,24),('lsr',1,0,24),('cmp',1,16),('bc',1,0x08076C38),
  ('lit',1,0x08076C34),('lsl',0,4,2),('addreg',0,0,4),('lsl',0,0,3),('addreg',0,0,1),
  ('mov',1,254),('strb',1,0,5),('mov',1,255),('strb',1,0,6),('b',0x08076C94)]),
 'insert_task_return': (0x08076C94,[('pop',8),('movhi',8,3),('pop',240),('pop',1),('bx',0)]),
 'find_first_active_task': (0x08076D40,[
  ('push',0,True),('mov',2,0),('lit',0,0x08076D78),('ldrb',1,0,4),('addi',3,0,0),
  ('cmp',1,1),('bc',1,0x08076D54),('ldrb',0,3,5),('cmp',0,254),('bc',0,0x08076D72),
  ('addi',0,2,1),('lsl',0,0,24),('lsr',2,0,24),('cmp',2,15),('bc',8,0x08076D72),
  ('lsl',0,2,2),('addreg',0,0,2),('lsl',0,0,3),('addreg',1,0,3),('ldrb',0,1,4),
  ('cmp',0,1),('bc',1,0x08076D54),('ldrb',0,1,5),('cmp',0,254),('bc',1,0x08076D54),
  ('addi',0,2,0),('pop',2),('bx',1)]),
 'runtasks_argument_and_indirect_consumer': (0x08076D10,[
  ('push',48,True),('bl',0x08076D40),('lsl',0,0,24),('lsr',0,0,24),('cmp',0,16),
  ('bc',0,0x08076D34),('lit',5,0x08076D3C),('lsl',4,0,2),('addreg',4,4,0),
  ('lsl',4,4,3),('addreg',4,4,5),('ldr',1,4,0),('bl',0x081C7ACC),('ldrb',0,4,6),
  ('cmp',0,255),('bc',1,0x08076D20),('pop',48),('pop',1),('bx',0)]),
 'constructor_taskid_fields': (0x08143560,[
  ('push',16,True),('lit',0,0x081435A0),('mov',1,0),('bl',0x08076BB4),
  ('lsl',0,0,24),('lsr',0,0,24),('lsl',4,0,2),('addreg',4,4,0),('lsl',4,4,3),
  ('lit',0,0x081435A4),('addreg',4,4,0),('mov',0,0),
  ('strb',0,4,8),('strb',0,4,9),('strb',0,4,10),('strb',0,4,11),('strb',0,4,12),
  ('strb',0,4,13),('mov',1,0),('strh',0,4,0),('strh',0,4,2),('strh',0,4,4),
  ('strh',0,4,6),('strb',1,4,14),('mov',0,64),('bl',0x08002BB0),('str',0,4,16),
  ('pop',16),('pop',1),('bx',0)]),
 'task_entry_bounded_dispatch': (0x081435A8,[
  ('push',48,True),('subsp',4),('lsl',0,0,24),('lsr',4,0,24),('lsl',0,4,2),
  ('addreg',0,0,4),('lsl',0,0,3),('lit',1,0x081435CC),('addreg',5,0,1),('ldrb',0,5,8),
  ('cmp',0,37),('bc',9,0x081435C2),('b',0x08143C62),('lsl',0,0,2),('lit',1,0x081435D0),
  ('addreg',0,0,1),('ldr',0,0,0),('movhi',15,0)]),
 'state11_producer_select_return4': (0x081437EC,[
  ('addi',0,5,0),('bl',0x08145190),('sub',0,2),('cmp',0,4),('bc',9,0x081437FA),
  ('b',0x08143C62),('lsl',0,0,2),('lit',1,0x08143804),('addreg',0,0,1),('ldr',0,0,0),('movhi',15,0)]),
 'state11_producer_store': (0x08143846,[
  ('mov',0,11),('strb',0,5,8),('lit',0,0x08143854),('lit',1,0x08143858),('bl',0x08008900),('b',0x08143C62)]),
 'state23_producer_guard': (0x08143A74,[
  ('addi',0,5,0),('add',0,9),('ldrb',2,5,12),('addi',1,5,0),('bl',0x08143204),
  ('addi',1,0,0),('cmp',1,0),('bc',0,0x08143A90),('cmp',1,0),('bc',13,0x08143ABC),
  ('cmp',1,1),('bc',0,0x08143AD0),('b',0x08143C62),('ldrb',0,5,12),('cmp',0,0),
  ('bc',1,0x08143ACC),('bl',0x081447C8),('cmp',0,1),('bc',1,0x08143ACC),('mov',0,23),('b',0x0814366E)]),
 'state_common_store': (0x0814366E,[('strb',0,5,8),('b',0x08143C62)]),
 'state11_call_and_pending_guard': (0x08143898,[
  ('addi',0,5,0),('add',0,9),('lit',3,0x081438C0),('addi',1,5,0),('mov',2,0),('bl',0x08142EA4),
  ('lsl',0,0,24),('asr',1,0,24),('cmp',1,1),('bc',0,0x081438F4),('cmp',1,1),('bc',2,0x081438E2)]),
 'state11_pending_no_store': (0x081438E2,[
  ('mov',0,1),('neg',0,0),('cmpreg',1,0),('bc',0,0x081438F4),('b',0x08143C62)]),
 'state23_call_and_pending_no_store': (0x08143AA2,[
  ('addi',0,5,0),('add',0,9),('lit',3,0x08143AC8),('addi',1,5,0),('mov',2,1),('bl',0x08142EA4),
  ('lsl',0,0,24),('asr',1,0,24),('cmp',1,1),('bc',0,0x08143AD0),('cmp',1,1),('bc',3,0x08143ACC),
  ('mov',0,1),('neg',0,0),('cmpreg',1,0),('bc',0,0x08143AD0),('b',0x08143C62)]),
 'task_pending_return': (0x08143C62,[('addsp',4),('pop',48),('pop',1),('bx',0)]),
 'helper_entry_text_state_dispatch': (0x08142EA4,[
  ('push',112,True),('subsp',28),('addi',5,0,0),('addi',4,1,0),('addi',1,3,0),
  ('lsl',2,2,24),('lsr',6,2,24),('ldrb',0,5,0),('cmp',0,1),('bc',0,0x08142F3C),
  ('cmp',0,1),('bc',12,0x08142EC2),('cmp',0,0),('bc',0,0x08142ECE),('b',0x08142FEE)]),
 'helper_state0_question_select': (0x08142ECE,[
  ('lit',0,0x08142EDC),('bl',0x08008B48),('cmp',6,0),('bc',1,0x08142EE4),('lit',0,0x08142EE0),('b',0x08142EE6)]),
 'helper_state0_alternate_window': (0x08142EE4,[('lit',0,0x08142F30)]),
 'helper_state0_window_calls': (0x08142EE6,[
  ('bl',0x08003CB0),('strh',0,4,0),('ldrb',0,4,0),('mov',1,17),('bl',0x08004428),
  ('ldrb',0,4,0),('mov',1,1),('strsp',1,0),('mov',1,4),('strsp',1,4),('lit',1,0x08142F34),
  ('strsp',1,8),('mov',1,0),('strsp',1,12),('lit',1,0x08142F38),('strsp',1,16),
  ('mov',1,2),('mov',2,2),('mov',3,2),('bl',0x0812EDAC),('ldrb',0,4,0),
  ('mov',1,1),('mov',2,15),('bl',0x0815310C),('ldrb',0,4,0),('mov',1,2),
  ('bl',0x08003EEC),('ldrb',0,4,0),('bl',0x08003F6C),('b',0x08142F86)]),
 'helper_state1_literal_consumer': (0x08142F3C,[
  ('lit',0,0x08142F58),('ldr',1,0,4),('ldr',0,0,0),('strsp',0,20),('strsp',1,24),
  ('cmp',6,0),('bc',1,0x08142F60),('lit',0,0x08142F5C),('ldrsp',1,20),('and',1,0),
  ('mov',0,144),('lsl',0,0,12),('b',0x08142F6A)]),
 'helper_state1_code_consumer': (0x08142F60,[
  ('lit',0,0x08142F90),('ldrsp',1,20),('and',1,0),('mov',0,240),('lsl',0,0,12),
  ('orr',1,0),('strsp',1,20),('mov',0,10),('strsp',0,0),('mov',0,14),('strsp',0,4),
  ('mov',0,0),('strsp',0,8),('addrsp',0,20),('mov',1,2),('mov',2,2),('mov',3,2),('bl',0x08110A94)]),
 'helper_common_increment': (0x08142F86,[('ldrb',0,5,0),('add',0,1),('strb',0,5,0),('b',0x08142FEE)]),
 'helper_pending_return': (0x08142FEE,[('mov',0,2),('neg',0,0),('addsp',28),('pop',112),('pop',2),('bx',1)]),
}
LITERALS = {
 0x08000554:0x03003130, 0x08000540:0x03003130,
 0x08076BF0:0x030050D0, 0x08076C34:0x030050D0,
 0x08076D78:0x030050D0, 0x08076D3C:0x030050D0,
 0x081429EC:0x081427B1, 0x081429F0:0x0203F32C,
 0x081435A0:0x081435A9, 0x081435A4:0x030050D8, 0x081435CC:0x030050D8, 0x081435D0:0x081435D4,
 0x081435F4:0x081437EC, 0x0814362C:0x08143A74,
 0x08143600:0x08143898, 0x08143630:0x08143AA2,
 0x08143804:0x08143808, 0x08143810:0x08143846,
 0x08143854:0x02021C4C, 0x08143858:0x020226B4,
 0x081438C0:0x084303F8, 0x08143AC8:0x08430710,
 0x08142EDC:0x02021C88, 0x08142EE0:0x08430118, 0x08142F30:0x08430120,
 0x08142F34:0x084307B0, 0x08142F38:0x02021C88,
 0x08142F58:0x08430138, 0x08142F5C:0xFF00FFFF, 0x08142F90:0xFF00FFFF,
}
WINDOWS = {name:(a,sum(4 if op[0]=='bl' else 2 for op in ops)) for name,(a,ops) in BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in LITERALS})
WINDOWS['yesno_template_fields'] = (0x08430138,8)
WINDOWS['minimal_boundary'] = (0x08142F5C,6)
CLAIMS = {
 'proof_scope':'conditional_finite_registered_task_mask_and_instruction_roles',
 'full_story_reachability_claimed':False, 'runtime_execution_observed':False,
 'universal_callback_epoch_claimed':False, 'all_task_states_proven':False,
 'irq_noninterference_proven':False, 'client_heap_lifetime_required':False,
 'all_opaque_callees_return_proven':False, 'both_paths_same_execution_claimed':False,
 'literal_interpreted_as_pointer':False, 'whole_function_range_classified':False,
 'indirect_reference_completeness_claimed':False, 'donor_eligible':False, 'donor_leased':False,
}
ROOT = {
 'kind':'conditional_actual_cb2_create_task_dispatch', 'initializer':0x081429CC,
 'setup_call':0x081429D0, 'setup_success_guard':0x081429D4, 'callback_setter_call':0x081429DA,
 'callback_literal':0x081429EC, 'callback_entry':0x081427B0,
 'constructor_call':0x081429E4, 'constructor':0x08143560, 'create_task_call':0x08143566,
 'create_task':0x08076BB4, 'insert_task':0x08076C08, 'find_first':0x08076D40,
 'main_callback_field':0x03003134, 'main_indirect_call':0x08000536,
 'runtasks_call':0x081427B2, 'runtasks':0x08076D10, 'task_indirect_call':0x08076D2A,
 'task_entry':0x081435A8, 'tasks':0x030050D0, 'task_data_base':0x030050D8,
 'task_stride':40, 'selected_admission':'all_16_inactive_then_first_free_row0',
 'state_offset':8, 'text_state_offset':9, 'state_bound':37, 'state_table':0x081435D4,
 'state11_slot':0x08143600, 'state23_slot':0x08143630, 'helper_entry':0x08142EA4,
 'text_state0_to1_store':0x08142F8A, 'pending_return':-2,
}
CONTRACT = {
 'scope':'finite_selected_slices_only_not_observed_RAM',
 'initializer_admission':'entry_0x081429CC_with_valid_nonalias_ABI_stack',
 'setup_success':'0x081427C8_returns_nonzero_with_ABI_preserved',
 'create_admission':'one_sufficient_selected_example_all_16_task_active_bytes_zero; not_a_general_necessity',
 'opaque_calls':'calls_at_explicit_BL_sites_return_with_ABI; preserve_selected_func_active_head_tail_state_textState_and_callback2_except_documented_writes; memset_clears_only_32_task_data_bytes',
 'cb2_return':'RunTextPrinters_AnimateSprites_BuildOamBuffer_calls_return_normally_and_preserve_selected_task_fields',
 'task_epoch':'row0_func_active_head_tail_and_callback2_hold_for_each_selected_dispatch_only',
 'main_dispatch_guards':'calls_at_0x08000512_and_0x0800051A_return0; callback1_is_null; callback2_is_registered_0x081427B1',
 'state11_producer':'state8_dispatch_and_MysteryGiftClient_Run_returns4; textState0_is_preserved',
 'state23_producer':'state22_dispatch; AskDiscardGift_returns0_with_textState0; isWonderNews0; saved_gift_check_returns1',
 'between_producer_and_helper':'selected_state11_or23_and_textState0_retained_until_RunTasks_dispatch',
 'state0_success':'readable_static_message; text_expansion_and_window_calls_return_normally_with_valid_window_resource',
 'between_two_helper_calls':'same_selected_task_state_and_textState1_retained; ABI_stack_disjoint_from_task_data_and_globals',
 'mask_consumption':'eight_readable_template_bytes_and_writable_nonalias_28byte_helper_stack_frame',
 'client_heap':'no_dereference_on_selected_state11_or23_helper_paths; lifetime_not_required',
}


def exact(a, b):
    """閉schemaとJSON型を同時に照合。boolを整数1として受け入れない。"""
    return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(b, sort_keys=True, separators=(',', ':'), allow_nan=False)


def semantic_consumers(raw):
    s = ThumbConsumer(raw)
    for name, (address, ops) in BLOCKS.items():
        a = address
        for op in ops:
            k, *q = op
            if k == 'bl': s.call(a, *q)
            elif k == 'lit': s.pointer(a, *q)
            elif k in ('mov','cmp','add'): s.imm(a, k, *q)
            elif k == 'sub': s.opcode(a, 0x3800 | (q[0] << 8) | q[1], 'SUB immediate')
            elif k in ('lsl','lsr'): s.shift(a, k=='lsr', *q)
            elif k == 'asr': s.opcode(a, 0x1000 | (q[2]<<6) | (q[1]<<3) | q[0], 'ASR signed return')
            elif k == 'addi': s.addi(a, *q)
            elif k == 'addreg': s.add(a, *q)
            elif k in ('ldr','str','ldrb','strb'): s.mem(a,k.startswith('ldr'),k.endswith('b'),*q)
            elif k == 'strh': s.opcode(a, 0x8000 | ((q[2]//2)<<6) | (q[1]<<3) | q[0], 'STRH exact task field')
            elif k == 'push': s.stack(a,False,*q)
            elif k == 'pop': s.stack(a,True,*q)
            elif k == 'bx': s.bx(a,*q)
            elif k == 'b': s.jump(a,*q)
            elif k == 'bc': s.branch(a,*q)
            elif k == 'cmpreg': s.compare(a,*q)
            elif k == 'movhi': s.opcode(a,0x4600 | ((q[0]&8)<<4) | (q[1]<<3) | (q[0]&7),'MOV high exact register')
            elif k in ('and','orr','neg'):
                mode={'and':0,'orr':12,'neg':9}[k]
                s.opcode(a,0x4000 | (mode<<6) | (q[1]<<3) | q[0],'ALU '+k)
            elif k in ('ldrsp','strsp'): s.opcode(a,(0x9800 if k=='ldrsp' else 0x9000) | (q[0]<<8) | (q[1]//4),'stack word field')
            elif k == 'addrsp': s.opcode(a,0xA800 | (q[0]<<8) | (q[1]//4),'stack template address')
            elif k in ('addsp','subsp'): s.opcode(a,(0xB080 if k=='subsp' else 0xB000) | (q[0]//4),'exact ABI stack frame')
            else: need(False,'unknown semantic contract')
            a += 4 if k=='bl' else 2
        need(a == address + WINDOWS[name][1], 'complete semantic instruction window')
    need(all(d.u32(raw,a)==v for a,v in LITERALS.items()),'actual typed globals, slots, function pointers and scalar masks')
    template=chunk(raw,0x08430138,8)
    need(tuple(template[:6])==(0,23,15,6,4,14) and int.from_bytes(template[6:],'little')==341,
         'complete public WindowTemplate fields')
    need(identity(chunk(raw,0x08142F5C,6)) == BOUNDARY, 'independent minimal boundary identity')


BOUNDARY = {'size':6,'sha256':'56e23ac810e438bc340d6fe37ab342c80ff23a9351c32cd09f6abbd6d14c24b6'}
MASK_SHA = '5fc1f3b5dfc3af9f4a3c54c77f448216c82908ce3953813f1e12695bb71271c8'
CODE_SHA = '0d915a3817397d574d32fdf36d15d0172f9273a2e9f7b59be1fedfc2fd1c77eb'


def evidence_template():
    """ROMなしで利用できる固定geometry契約。証明APIの代替ではない。"""
    return {
      'schema_version':1, 'root_verified':True, 'root':copy.deepcopy(ROOT),
      'input_contract':copy.deepcopy(CONTRACT), 'claims':copy.deepcopy(CLAIMS),
      'boundary_window':{'address':0x08142F5C,**BOUNDARY},
      'hit':{'address':HIT,'size':4}, 'partition':'adjacent_complete_literal32_then_instruction16',
      'elements':[
       {'address':0x08142F5C,'size':4,'sha256':MASK_SHA,'role':'scalar_and_mask_literal32',
        'root':{'selector':11,'slot':0x08143600,'entry':0x08143898,'helper_call':0x081438A2,
          'helper_entry':0x08142EA4,'text_state':1,'placement':0,'condition':'placement_eq_zero',
          'branch':0x08142F48,'selected_successor':0x08142F4A,'load':0x08142F4A,'load_width':4,
          'and_consumer':0x08142F4E,'cleared_bit_start':16,'cleared_bit_count':8,
          'template_stack_offset':20,'replacement_tilemap_top':9}},
       {'address':0x08142F60,'size':2,'sha256':CODE_SHA,'role':'complete_thumb_ldr_literal16',
        'root':{'selector':23,'slot':0x08143630,'entry':0x08143AA2,'helper_call':0x08143AAC,
          'helper_entry':0x08142EA4,'text_state':1,'placement':1,'condition':'placement_ne_zero',
          'branch':0x08142F48,'selected_successor':0x08142F60,'instruction':0x08142F60,
          'loaded_literal':0x08142F90,'load_width':4,'and_consumer':0x08142F64,
          'template_stack_offset':20,'replacement_tilemap_top':15}},
      ],
      'exclusive_paths':True,'single_path_covers_both_elements':False,
      'literal_is_pointer':False,'type_classification_only':True,
    }


def witness_geometry(evidence):
    """異種境界の完全性・隣接・個別root・排他経路を閉schemaで検査。"""
    need(exact(evidence,evidence_template()),'exact complete literal/code partition and independent exclusive roots')
    elements=evidence['elements']
    need(elements[0]['address']+elements[0]['size']==elements[1]['address'],'strictly adjacent complete typed elements')
    start=elements[0]['address'];end=elements[1]['address']+elements[1]['size']
    need(start<=HIT and HIT+4<=end,'all four hit bytes partitioned')
    need(start==0x08142F5C and end-start==6,'only minimal six-byte boundary')
    return start,end-start


def selected_task_contract(active_before, task_id, state, text_state, placement,
                           setup_result, state0_calls_returned, selected_fields_preserved,
                           stack_nonalias, valid_window_resource):
    """有限入力のscalar/flag検査。実RAMやcallee成功を観測したと主張しない。"""
    need(type(active_before) is list and len(active_before)==16 and all(type(x)is int and x==0 for x in active_before),'normal empty-list admission only')
    need(type(task_id)is int and task_id==0,'selected first free task row0')
    need(type(state)is int and type(placement)is int and (state,placement) in ((11,0),(23,1)),'two separate selected task paths')
    need(type(text_state)is int and text_state==0,'actual state0 producer required')
    need(type(setup_result)is int and 0<setup_result<=0xFFFFFFFF,'finite setup success branch')
    need(all(x is True for x in (state0_calls_returned,selected_fields_preserved,stack_nonalias,valid_window_resource)), 'bounded success and nonalias conditions required')
    return {'task_id':0,'data_address':0x030050D8,'state_address':0x030050E0,
            'text_state_address':0x030050E1,'next_text_state':1,'state_preserved':state,
            'placement':placement,'pending_result':-2,'slot':0x081435D4+4*state}


def sources_bind(review,sources):
    need(set(sources)==set(SOURCE_IDS) and exact(review['source_bindings'],SOURCE_IDS),'exact fixed public sources')
    for name,expected in SOURCE_IDS.items():
        b=sources[name]
        need(identity(b)=={k:expected[k] for k in ('size','sha256')},'independent whole public source identity')
        need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==expected['git_blob_sha'],'fixed public Git blob')
    src=sources['pret-mystery_gift_menu.c'].decode()
    for text in ('SetMainCallback2(CB2_MysteryGiftEReader);','CreateMysteryGiftTask();',
                 'u8 taskId = CreateTask(Task_MysteryGift, 0);','windowTemplate.tilemapTop = 9;',
                 'windowTemplate.tilemapTop = 15;','(*textState)++;'):
        need(text in src,'public callback, task and template semantic roles')
    need('gTasks[taskId].func(taskId);' in sources['pret-task.c'].decode(),'public task indirect consumer role')


def protected_windows(review):
    rows=review['windows']
    need(type(rows)is list and len(rows)==len(WINDOWS),'exact bounded dependency window count')
    need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'closed dependency record fields')
    need(exact([(r['label'],r['address'],r['size']) for r in rows],[(k,*v) for k,v in WINDOWS.items()]),'closed dependency roles and geometry')
    need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']) for r in rows),'lowercase SHA256 only')
    return [{k:r[k] for k in ('address','size','sha256')} for r in rows]


def _regions(raw,inherited,review,sources):
    need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract'},'closed review schema')
    need(type(review['schema_version'])is int and review['schema_version']==1,'review version')
    need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE),'fixed current target')
    need(exact(review['diagnostic_input'],DIAGNOSTIC),'diagnostic and current identities remain distinct')
    need(exact(review['root'],ROOT) and exact(review['claims'],CLAIMS) and exact(review['input_contract'],CONTRACT),'finite root and no universal claim')
    original=[h for h in inherited['hits'] if h['address']==HIT]
    need(len(original)==1 and exact(original[0],review['hit']) and original[0]['accepted'] is False and original[0]['owner_candidates']==[],'one exact inherited external unknown')
    need(type(original[0]['size'])is int and original[0]['size']==4 and original[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','original four-byte all-start hit')
    d.signed(raw,original[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));semantic_consumers(raw)
    evidence=evidence_template();a,n=witness_geometry(evidence)
    return [d.TypedRegion(a,a+n,KIND,evidence)], dict(status='PASS_ONE_CONDITIONAL_MYSTERY_GIFT_BOUNDARY',count=1,hit=HIT,
        protected_windows=len(WINDOWS),protected_bytes=sum(n for _,n in WINDOWS.values()),source_bindings=SOURCE_IDS,**CLAIMS)


def regions(raw,inherited,review,sources,root=None):
    need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory; diagnostic is not current')
    return _regions(raw,inherited,review,sources)
