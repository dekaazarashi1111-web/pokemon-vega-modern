"""Flash一選択の条件付き実producer。callback入口で止め、文字型は発行しない。"""
import copy

import pr16_dex_hof_party_takeitem as take
import pr16_dex_hof_field_move_roots as field

party, task, setup, menu, runtime = take.party, take.task, take.setup, take.menu, take.runtime
need, chunk, exact = take.need, take.chunk, take.exact
HEAP, TASKS, PARTY, MONS, MAIN, CURSOR = take.HEAP, take.TASKS, take.PARTY, take.MONS, take.MAIN, take.CURSOR
CANDIDATE = take.CANDIDATE
CALLBACK_CELL, CALLBACK, ACTION, MOVE = 0x08419E3C, 0x08124F08, 18, 148
SOURCE_IDS = copy.deepcopy(take.SOURCE_IDS)

# 旧TakeItemの正profileは使わず、共通命令と既存source identityだけを参照する。
OWN_REUSED = (
    'outer_field_prefix', 'outer_field_move_compare', 'outer_field_move_next',
    'outer_field_loop_and_second_species', 'outer_nonmail_item_action_append',
    'outer_cancel_append_return', 'choose_mon_return',
)
REUSED = {name: (mod, tuple(names)) for name, (mod, names) in take.REUSED.items()}
REUSED['party'] = (party, REUSED['party'][1] + ('selection_large_input',))
REUSED['menu'] = (menu, tuple(name for name in REUSED['menu'][1]
                              if name not in ('menu_no_wrap_input_prefix', 'menu_no_wrap_input_tail',
                                              'cursor_clamp_prefix', 'cursor_clamp_tail'))
                   + ('menu_wrap_input_prefix', 'menu_wrap_input_tail',
                      'cursor_wrap_prefix', 'cursor_wrap_tail'))
ALL_BLOCKS = {name: (party, take.BLOCKS[name]) for name in OWN_REUSED}
ALL_BLOCKS['field_match_append'] = (menu, field.BLOCKS['field_match_append'])
for scope, (mod, names) in REUSED.items():
    for name in names:
        ALL_BLOCKS[scope + '_' + name] = (mod, mod.BLOCKS[name])
BLOCKS = {name: rows for name, (mod, rows) in ALL_BLOCKS.items()}
ALL_WORDS = {}
for name, (mod, rows) in ALL_BLOCKS.items():
    for ins in rows:
        if ins.kind == 'literal':
            address = ins.args[1]
            if name in OWN_REUSED:
                value = take.LITERALS[address]
            elif name == 'field_match_append':
                value = field.WORDS[address]
            else:
                value = mod.LITERALS[address]
            need(address not in ALL_WORDS or ALL_WORDS[address] == value, '同住所literalの意味一致')
            ALL_WORDS[address] = value
ALL_WORDS.update(setup.TABLE)
ALL_WORDS.update({0x0836B380: 0x0806EC3D, 0x08123320: 0x0812334C, CALLBACK_CELL: CALLBACK | 1})
FIELDS = {f'field_move_id_{j}': (0x08419EFE + 2*j, 2, value)
          for j, value in enumerate(take.FIELD_MOVE_IDS)}
INS = {}
for mod, rows in ALL_BLOCKS.values():
    for ins in rows:
        if ins.address in INS:
            need(menu.encoded(INS[ins.address]) == mod.encoded(ins), '共通命令の意味一致')
        INS[ins.address] = ins
WINDOWS = {name: (rows[0].address, sum(i.size for i in rows))
           for name, (mod, rows) in ALL_BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}': (a, 4) for a in sorted(ALL_WORDS)})
WINDOWS.update({name: (a, n) for name, (a, n, value) in FIELDS.items()})
Machine = take.Machine

PROFILE = dict(held_item=1, party_slot=0, task_id=0, move_slots=[148, 0, 0, 0],
               egg=0, second_species=0, item_is_mail=0, outer_input=1,
               outer_actions=[0, 18, 3, 2], normal_returns=True,
               fields_preserved=True, stack_nonalias=True)
SELECTION_OUTPUT_SPEC = [
    dict(base='cursor', offset=2, size=1, value=0, role='initial cursor'),
    dict(base='cursor', offset=3, size=1, value=0, role='minimum'),
    dict(base='cursor', offset=4, size=1, value=3, role='maximum'),
    dict(base='cursor', offset=11, size=1, value=1, role='selection sound mode'),
    dict(base='object', offset=12, size=1, value=0, role='valid selection window ID in sufficient profile'),
]
PHASE_FIELDS = {phase: copy.deepcopy(take.PHASE_FIELDS[phase])
                for phase in ('root_setup', 'outer_builder')}
PHASE_FIELDS['outer_builder'].append('action18 at object.actions[1] and count4 through callback dispatch')
CLAIMS = dict(complete_before_callback_accepted=True, callback_body_executed=False,
              badge_branch_proven=False, complete_text_reads_proven=False,
              synthetic_contract_execution=True, actual_runtime_execution_observed=False,
              full_story_reachability_claimed=False, universal_allocation_epoch_proven=False,
              all_opaque_effects_proven=False, irq_noninterference_proven=False,
              indirect_reference_completeness_claimed=False, donor_eligible=False,
              newly_classified=0)
ROOT = dict(start_menu_slot=0x0836B380, entry=0x0806EC3C,
            constructor=0x0811F24C, allocation_size=568, setup_state20_call=0x0811F5C4,
            first_task_function=0x08120319, party_scheduler=0x0811F3A8,
            runtasks=0x08076D10, actual_action_hook=0x09097A80,
            field_producer=0x081231D8, match_append=0x0812323A,
            selector=0x08123438, selector_callback_load=0x08123512,
            count4_input_call=0x0812347C, count4_input_function=0x081105B8,
            cursor_wrap=0x08110438,
            callback_cell=CALLBACK_CELL, callback_thumb=CALLBACK | 1,
            stopped_entry=CALLBACK)
CONTRACT = dict(
    source='固定TakeItemのStartMenu/constructor/state20/RunTasks/selector命令とsource identityのみ再利用する。旧field-moveなしprofileの正結果は再利用しない。',
    example='slot0、非egg、held_item1非mail、second species0、技slot[148,0,0,0]。producerが[0,18,3,2]を生成する一十分条件。',
    selection='count4の条件付き初期化5出力を明示。実>3分岐からwrap入力081105B8へ入り、cursor0/min0/max3/soundmode1/window0からDown1+Aでindex1を得る。旧count3 no-wrapは使わない。',
    allocation='constructorの整列568-byte成功結果と同じ生存epochを、callback入口で次にobjectを読む時点まで保持する。新たな実allocator観測ではない。',
    dispatch='各main dispatchでcallback1=0、fade bit7=0、link-wait helper=0。同じCreateTask結果のactive/list/functionを各selected dispatchで保持する。',
    abi='外部calleeは通常Thumb復帰しr4-r11/SP/saved caller stackを保持。r0-r3/r12/LR/flagsは破壊して戻る。',
    getter='GetMonDataの各callsite/mon/fieldを検査し、field13だけ148、14..16は0、field45とsecond field11は0、field12は1とする条件境界。getter本体の効果証明ではない。',
    endpoint='実selectorが08419E3Cをloadして08124F09へ間接dispatchした後、08124F08入口で停止。callback、badge拒否、text readerは未実行。',
)


def selected_profile(profile=None):
    value = copy.deepcopy(PROFILE) if profile is None else profile
    need(type(value) is dict and exact(value, PROFILE), 'Flash一選択の閉じた型厳密profile')
    return copy.deepcopy(value)


def bind_semantics(raw):
    for name, (mod, rows) in ALL_BLOCKS.items():
        for ins in rows:
            need(chunk(raw, ins.address, ins.size) == mod.encoded(ins), '根/producer意味命令 ' + name + ' ' + hex(ins.address))
    for address, value in ALL_WORDS.items():
        need(take.d.u32(raw, address) == value, '根/producer literalとcallback cell ' + hex(address))
    for address, size, value in FIELDS.values():
        need(int.from_bytes(chunk(raw, address, size), 'little') == value, 'stock field-move表の意味')


def sources_bind(sources):
    take.sources_bind({'source_bindings': SOURCE_IDS}, sources)
    body = sources['pret-party_menu.c'].decode()
    for token in ('static void SetPartyMonFieldSelectionActions(struct Pokemon *mons, u8 slotId)',
                  'if (GetMonData(&mons[slotId], i + MON_DATA_MOVE1) == sFieldMoves[j])',
                  'j + CURSOR_OPTION_FIELD_MOVES);', 'static void CursorCB_FieldMove(u8 taskId)'):
        need(token in body, '固定公開producerの語義')


def selection_initialization(pointer, count=4, spec=None):
    need(type(pointer) is int and pointer % 4 == 0
         and runtime.ROOT + 16 <= pointer <= runtime.ROOT + runtime.LIMIT - 568, 'selection objectの有限配置')
    need(type(count) is int and count == 4, '新producerはcount4')
    spec = SELECTION_OUTPUT_SPEC if spec is None else spec
    need(exact(spec, SELECTION_OUTPUT_SPEC), 'count4の正確な5条件出力')
    return [dict(address=(CURSOR if row['base'] == 'cursor' else pointer) + row['offset'],
                 size=row['size'], value=row['value'], role=row['role']) for row in spec]


def live_projection(pointer, phase, task_id=0, task_admitted=True):
    need(phase in PHASE_FIELDS, '新producerの有限phase')
    return take.live_projection(pointer, phase, task_id, task_admitted)


def preservation_contract(pointer, phase, writes, task_id=0, task_admitted=True,
                          freed=(), heap_reinitialized=False):
    need(phase in PHASE_FIELDS, '新producerの有限phase')
    return take.preservation_contract(pointer, phase, writes, task_id, task_admitted,
                                      freed, heap_reinitialized)


def compose_selected(raw, profile=None, return_machine=False):
    """新Flash profileだけを実命令で合成。opaque正常復帰と生存条件は入力仮定。"""
    profile = selected_profile(profile)
    need(type(return_machine) is bool, 'machine返却指定はbool')
    bind_semantics(raw)
    pointer = runtime.ROOT + runtime.HEADER
    memory = runtime.task_fixture([])
    for address, size in ((pointer, 568), (PARTY, 20), (MAIN, 1100), (CURSOR, 12)):
        for offset in range(size):
            memory[address + offset] = 0
    runtime.setmem(memory, 0x020379F3, 1, 0)
    assumptions, events, frames = [], [], []
    phase, selected = 'root_setup', None
    setup_success = {0x0811F4D4, 0x0811F4FC, 0x0811F558, 0x0811F578}
    setup_calls = {ins.address for name in REUSED['setup'][1] if name.startswith('setup_')
                   for ins in setup.BLOCKS[name] if ins.kind == 'call'}
    root_external = {0x0806EC54, 0x0806EC58, 0x0806EC5C, 0x0811F37E}

    def run(entry, mem, stop=None):
        nonlocal selected
        machine = Machine(raw, entry, memory=mem, instructions=INS)
        if entry == 0x08000510:
            need(machine.read(MAIN, 4) == 0, 'selected callback2前のcallback1はnull')
        while machine.pc != 0xFFFFFFF0 and machine.pc != stop:
            if machine.pc in INS:
                if machine.pc == 0x0811F5C4:
                    need(not runtime.task_chain(machine.mem), 'empty-list一十分条件')
                    need(machine.reg[0] == 0x08120319, 'constructor field0の実CreateTask引数')
                if machine.pc == 0x0811F5C8:
                    selected = machine.reg[0]
                    need(selected == 0 and selected in runtime.task_chain(machine.mem), '実task生成結果とlist所属')
                    events.append(dict(role='admitted_same_task', address=0x0811F5C4, task_id=selected))
                if machine.pc == 0x0812324C:
                    need(tuple(machine.reg[:3]) == (pointer+15, pointer+23, ACTION), '一致枝がaction18を実appendへ渡す')
                    events.append(dict(role='field_move_append', address=machine.pc, action=ACTION, move=MOVE))
                if machine.pc == 0x08123428:
                    events.append(dict(role='outer_selector_registration', address=machine.pc, task_id=selected))
                if machine.pc == 0x0812347C:
                    need(machine.read(pointer+23, 1) == 4, 'count4の実>3分岐')
                    events.append(dict(role='count4_wrap_input', address=machine.pc,
                                       input_function=0x081105B8, task_id=selected))
                if machine.pc == 0x08123512:
                    need(machine.reg[0] == CALLBACK_CELL, '実actions[index1]がfield callback cellを選択')
                    events.append(dict(role='selector_callback', callback_cell=machine.reg[0],
                                       callback=take.d.u32(raw, machine.reg[0]), task_id=selected))
                machine.step()
                continue
            site, target = (machine.reg[14] & ~1) - 4, machine.pc
            result, allowed, outputs = runtime.U, False, []
            if target in (0x080F6168, 0x0813C034):
                result, allowed = 0, site in (0x08000512, 0x0800051A)
            elif target == 0x08002B9C:
                need(site == 0x0811F280 and machine.reg[0] == 568, 'constructorの実Alloc引数')
                result, allowed = pointer, True
            elif site in root_external:
                allowed = True
            elif target == 0x080C0918:
                result, allowed = 0, site in (0x0811F3DA, 0x0812032C, 0x0812344A)
            elif target == 0x080C08D8:
                result = 1 if phase == 'root_setup' and site == 0x0811F3F2 else 0
                allowed = site in (0x0811F3F2, 0x0811F4BC)
            elif site in setup_calls:
                result, allowed = (1 if site in setup_success else runtime.U), True
            elif target in (0x080066D8, 0x08006724, 0x080F7810, 0x0806FC74):
                allowed = True
            elif target == 0x081206EC:
                need(site == 0x0812033E, '実mon入力site')
                result, allowed = 1, True
            elif target == 0x08071A70:
                allowed = True
            elif target == 0x081103A8:
                need(site == 0x08110470, 'wrap後のcursor redraw')
                allowed = True
            elif target == 0x0803F354:
                field_id = machine.reg[1]
                if site == 0x08123350:
                    need(machine.reg[0] == MONS and field_id == 45, '選択mon非egg')
                    result = profile['egg']
                elif site == 0x0812322C:
                    need(machine.reg[0] == MONS and type(field_id) is int and field_id in (13,14,15,16), '実field-move比較引数')
                    result = profile['move_slots'][field_id - 13]
                elif site == 0x0812327A:
                    need(machine.reg[0] == MONS+100 and field_id == 11, '第2slotのspecies getter')
                    result = profile['second_species']
                else:
                    need(site == 0x0812329E and machine.reg[0] == MONS and field_id == 12, 'producer held-item getterのみ')
                    result = profile['held_item']
                allowed = True
            elif target == 0x08097AE8:
                need(site == 0x081232A6 and machine.reg[0] == profile['held_item'], '実nonmail検査')
                result, allowed = profile['item_is_mail'], True
            elif target == 0x08120AD0:
                need(site == 0x081233C6 and machine.reg[0] == MONS, 'outer nicknameのみ')
                allowed = True
            elif target == 0x081224B0:
                need(machine.reg[0] in (pointer+12, pointer+13, pointer+14), '対象window byteだけ条件更新')
                machine.write(machine.reg[0], 1, 255)
                allowed = True
            elif target == 0x08122628:
                need(machine.reg[0] == 0 and machine.read(pointer+23, 1) == 4, '新outer count4 selectionだけ')
                outputs = selection_initialization(pointer, 4)
                for output in outputs:
                    machine.write(output['address'], output['size'], output['value'])
                allowed = True
            elif target in (0x081224D8, 0x08122904):
                allowed = True
            need(allowed, '未登録境界 ' + hex(site) + ' -> ' + hex(target))
            assumptions.append(dict(site=site, target=target, phase=phase,
                                    required_fields=PHASE_FIELDS[phase], normal_abi_return_required=True,
                                    effects_discharged=False,
                                    return_value=result if runtime.concrete(result) else 'unspecified',
                                    conditional_outputs=outputs))
            return_pc = machine.reg[14] & ~1
            for register in (0, 1, 2, 3, 12, 14):
                machine.reg[register] = runtime.U
            machine.reg[0], machine.flag_pc, machine.pc = result, None, return_pc
        if stop is None:
            need(machine.reg[13] == 0x03007000, '各完結phaseのstack均衡')
        frames.append(dict(entry=entry, stop=machine.pc, instruction_steps=machine.steps))
        return machine

    machine = run(take.d.u32(raw, ROOT['start_menu_slot']) & ~1, memory)
    need(machine.read(MAIN+4, 4) == 0x081277E9, 'StartMenuがconstructor callbackを登録')
    machine = run(0x08000510, machine.mem)
    need(machine.read(MAIN+4, 4) == 0x0811F3D9 and machine.read(pointer, 4) == 0x08120319, '同objectとinit/task登録')
    for stage in range(24):
        need(machine.read(MAIN+1080, 1) == stage, '実setup状態producer鎖')
        machine = run(0x08000510, machine.mem)
    need(selected == 0 and machine.read(MAIN+4, 4) == 0x0811F3A9, 'finite setupから実scheduler')
    phase = 'outer_builder'
    machine = run(0x08000510, machine.mem)
    actions = [machine.read(pointer+15+j, 1) for j in range(4)]
    need(machine.read(TASKS, 4) == 0x08123439 and actions == [0,18,3,2]
         and machine.read(pointer+23, 1) == 4, '新producerの実count4/actionsと同selector task')
    for down in (True, False):
        runtime.setmem(machine.mem, MAIN+46, 2, 0 if down else 1)
        runtime.setmem(machine.mem, MAIN+48, 2, 128 if down else 0)
        need(selected in runtime.task_chain(machine.mem) and machine.read(TASKS, 4) == 0x08123439,
             '各frameで同task active/list/function')
        machine = run(0x08000510, machine.mem, stop=None if down else CALLBACK)
        need(machine.read(CURSOR+2, 1) == 1, 'Down1から実cursor1を保持')
    need(machine.pc == CALLBACK and machine.reg[0] == selected, '同taskを引数としてcallback入口へ実dispatch')
    need([row for row in events if row['role'] == 'field_move_append'] ==
         [dict(role='field_move_append', address=0x0812324C, action=ACTION, move=MOVE)], 'field move appendは1個だけ')
    need(len([row for row in events if row['role'] == 'count4_wrap_input']) == 2,
         'DownとAの両frameで実count4 wrap入力へ入る')
    proof = dict(status='PASS_CONDITIONAL_STARTMENU_FLASH_PRODUCER_TO_CALLBACK_ENTRY',
                 profile=profile, root=copy.deepcopy(ROOT), input_contract=copy.deepcopy(CONTRACT),
                 selected_task=selected, outer_actions=actions, outer_count=4,
                 selected_input_function=0x081105B8, selection_wrap=True,
                 legacy_no_wrap_result_reused=False,
                 reached_instruction=machine.pc, callback_task_argument=machine.reg[0],
                 events=events, frames=frames, conditional_calls=assumptions,
                 phase_fields=copy.deepcopy(PHASE_FIELDS),
                 required_live_projections={name: live_projection(pointer, name) for name in PHASE_FIELDS},
                 **copy.deepcopy(CLAIMS))
    return (proof, machine) if return_machine else proof
