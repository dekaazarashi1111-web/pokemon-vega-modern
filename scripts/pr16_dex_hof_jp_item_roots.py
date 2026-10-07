"""交換・mailboxの別根を実登録からcallback入口へ結ぶ条件付き有限型。"""
import copy

import pr16_dex_hof_party_takeitem as take
import pr16_dex_hof_menu_text as live

party, task, setup, menu, runtime = take.party, take.task, take.setup, take.menu, take.runtime
need, chunk, exact = take.need, take.chunk, take.exact
HEAP, TASKS, PARTY, MONS, MAIN = take.HEAP, take.TASKS, take.PARTY, take.MONS, take.MAIN
CANDIDATE = copy.deepcopy(take.CANDIDATE)
NEW_ITEM, OLD_ITEM = 2, 1
NEW_ITEM_CELL, OLD_ITEM_CELL = 0x0203ACA8, 0x0203B04C
ENDPOINTS = {'exchange': 0x08120D48, 'mailbox': 0x08127D3C}
SOURCE_IDS = copy.deepcopy(take.SOURCE_IDS)
BLOCKS = {}


def put(name, address, specs):
    BLOCKS[name] = tuple(party.block(address, specs))


put('switch_prompt_registers_same_task', 0x081240D8, [
 ('push',16,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('call',0x08120B60),('shift','lsl',0,0,24),('shift','lsr',0,0,24),
 ('imm','cmp',0,1),('branch',0,0x081240FC),('call',0x081227D8),
 ('literal',0,0x08124104),('shift','lsl',1,4,2),('add',1,1,4),
 ('shift','lsl',1,1,3),('add',1,1,0),('literal',0,0x08124108),
 ('mem',False,'word',0,1,0),('pop',16,False),('pop',1,False),('bx',0)])
put('switch_yes_input', 0x0812410C, [
 ('push',112,True),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('call',0x08110BF8),('shift','lsl',0,0,24),('shift','asr',1,0,24),
 ('imm','cmp',1,0),('branch',0,0x08124132)])
put('switch_bag_success', 0x08124132, [
 ('literal',5,0x08124174),('mem',True,'half',0,5,0),('imm','mov',1,1),
 ('call',0x08099BE0),('literal',6,0x08124178),('mem',True,'half',0,6,0),
 ('imm','mov',1,1),('call',0x08099A8C),('shift','lsl',0,0,24),
 ('imm','cmp',0,0),('branch',1,0x08124188)])
put('switch_nonmail', 0x08124188, [
 ('mem',True,'half',0,5,0),('call',0x08097AE8),('shift','lsl',0,0,24),
 ('imm','cmp',0,0),('branch',0,0x081241C8)])
put('switch_give_and_message', 0x081241C8, [
 ('literal',0,0x081241F8),('imm','mov',1,9),('signed_load','byte',1,0,1),
 ('imm','mov',0,100),('alu','mul',0,1),('literal',1,0x081241FC),('add',0,0,1),
 ('mem',True,'half',1,5,0),('call',0x08120DB8),
 ('mem',True,'half',0,5,0),('mem',True,'half',1,6,0),('imm','mov',2,1),('call',0x08120D48)])
put('mailbox_constructor_root', 0x08127D10, [
 ('push',0,True),('spadd',-12),('imm','mov',0,6),('spmem',False,0,0),
 ('literal',0,0x08127D34),('spmem',False,0,4),('literal',0,0x08127D38),
 ('spmem',False,0,8),('imm','mov',0,0),('imm','mov',1,0),('imm','mov',2,7),
 ('imm','mov',3,0),('call',0x0811F24C),('spadd',12),('pop',1,False),('bx',0)])
put('mailbox_action7_branch', 0x08120496, [
 ('addi',0,5,0),('call',0x0812054C),('shift','lsl',0,0,24),('imm','cmp',0,0),
 ('branch',0,0x08120546),('imm','mov',0,5),('call',0x08071A70),
 ('addi',0,6,0),('call',0x08127D3C)])
LITERALS = {
 0x08124104:TASKS, 0x08124108:0x0812410D,
 0x08124174:NEW_ITEM_CELL, 0x08124178:OLD_ITEM_CELL,
 0x081241F8:PARTY, 0x081241FC:MONS,
 0x08127D34:0x08120319, 0x08127D38:0x080ED451,
 0x08120404:0x08120496,
}
REUSED = {
 'party':(party,('interwork_r1',)),
 'task':(task,('run_tasks_field0_dispatch','choose_mon_input','choose_mon_confirm',
  'cursor_pointer_choice','cursor_party_slot','selection_hook_entry','selection_hook_trampoline',
  'actual_action_selector_hook','actual_action_selector_resume','action9_table_consumer',
  'non_egg_success','non_egg_return')),
 'setup':(setup,take.REUSED['setup'][1]),
 'runtime':(runtime,take.REUSED['runtime'][1]),
}
ALL_BLOCKS = {name:(party,rows) for name,rows in BLOCKS.items()}
ALL_WORDS = dict(LITERALS)
for scope,(mod,names) in REUSED.items():
    for name in names:
        rows=mod.BLOCKS[name]
        ALL_BLOCKS[scope+'_'+name]=(mod,rows)
        for ins in rows:
            if ins.kind=='literal':
                a=ins.args[1]
                need(a not in ALL_WORDS or ALL_WORDS[a]==mod.LITERALS[a], '共通literalの一致')
                ALL_WORDS[a]=mod.LITERALS[a]
ALL_WORDS.update(setup.TABLE)
INS={}
for mod,rows in ALL_BLOCKS.values():
    for ins in rows:
        need(ins.address not in INS or menu.encoded(INS[ins.address])==mod.encoded(ins), '共通命令の一致')
        INS[ins.address]=ins
WINDOWS={name:(rows[0].address,sum(i.size for i in rows)) for name,(mod,rows) in ALL_BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in sorted(ALL_WORDS)})
FIELDS={}
PROFILES={
 'exchange':dict(task_id=0,party_slot=0,new_item=NEW_ITEM,old_item=OLD_ITEM,
                 text_active=0,yes_input=0,bag_success=1,item_is_mail=0,
                 normal_returns=True,fields_preserved=True,stack_nonalias=True),
 'mailbox':dict(task_id=0,party_slot=0,action=7,egg=0,choose_mon_input=1,
                normal_returns=True,fields_preserved=True,stack_nonalias=True),
}
ROOTS={
 'exchange':dict(entry=0x081240D8,existing_task=0,registration_store=0x081240FA,
                  registration_literal=0x08124108,registered_thumb=0x0812410D,
                  runtasks=0x08076D10,input_entry=0x0812410C,message_call=0x081241E2,
                  stopped_entry=ENDPOINTS['exchange']),
 'mailbox':dict(entry=0x08127D10,constructor_call=0x08127D28,constructor=0x0811F24C,
                constructor_register_arguments=[0,0,7,0],constructor_stack_arguments=[6,0x08120319,0x080ED451],
                allocation_size=568,setup_state20_call=0x0811F5C4,runtasks=0x08076D10,
                actual_action_hook=0x09097A80,action=7,action_table_cell=0x08120404,
                action_branch=0x08120496,callback_call=0x081204AA,stopped_entry=ENDPOINTS['mailbox']),
}
CONTRACT={
 'scope':'交換prompt taskとmailbox constructorを別rootとして閉じる。旧TakeItem/Flash成功profileを実行・流用しない。自然操作によるroot到達は未証明。',
 'exchange':'既存task0がactive/head/last、slot0、新item2/旧item1の十分条件。prompt text非active→YesNo正常復帰→同rowに0812410Dを実STR。RunTasksが同rowを再読しYes0/旧itemのAddBagItem低byte1/新item非mailで進む。',
 'mailbox':'実InitPartyMenu引数(0,0,7,0;6,08120319,080ED451)。同568-byte object、23状態+default、state20のCreateTask成功task0、現hookのaction7、非eggの条件からcallbackへ進む。',
 'allocation':'mailboxでは整列した568-byte allocator成功結果と同じepochを必要なobject読取およびcallback受渡しまで保持する。戻りobjectの先行read byte8/10..14が0であることはこの例の明示条件で、Allocがzero化する効果証明ではない。',
 'initial_ram':'required_initial_memoryは最初のwriteに先行する実RAM readの値条件。unspecifiedは未指定byteであり、0を補っていない。object先行readの0条件はallocation_result_memory_conditionsへ分離する。',
 'abi':'各明示siteのopaque calleeは通常Thumb復帰しr4-r11/SP/必要saved stackを保持する。r0-r3/r12/LR/flagsはUnknownへ破棄。getter/input/bag/mail判定の値は個別条件であり本体の証明ではない。',
 'ram':'各opaque siteのrequired_fieldsは新profileの実読取・書込から逆算したfuture-live RAM。関係ないRAMは各境界で消去して再実行する。callback受渡し用のparty slotと同task所属を最後まで保持する。',
 'dispatch':'mailbox各main dispatchのcallback1=0、fade bit7=0、link-wait戻り0。新root専用のsetup wait成功条件を各callsiteに記録。同期非再入は条件でありIRQや全calleeの普遍証明ではない。',
 'endpoint':'交換08120D48で(new2,old1,keepOpen1)、mailbox08127D3Cで(task0)を保持して停止する。callback本文とtext readerはこのmoduleでは実行しない。',
}
CLAIMS=dict(conditional_finite_type_only=True,synthetic_contract_execution=True,
 actual_runtime_execution_observed=False,full_story_reachability_claimed=False,
 universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,
 irq_noninterference_proven=False,indirect_reference_completeness_claimed=False,
 callback_body_executed=False,complete_text_reads_proven=False,donor_eligible=False,newly_classified=0)


def source_manifest():
    return copy.deepcopy(SOURCE_IDS)


def sources_bind(sources):
    take.sources_bind({'source_bindings':SOURCE_IDS}, sources)
    body=sources['pret-party_menu.c'].decode()
    for token in (
      'static void Task_SwitchItemsYesNo(u8 taskId)',
      'gTasks[taskId].func = Task_HandleSwitchItemsYesNoInput;',
      'switch (Menu_ProcessInputNoWrapClearOnChoose())',
      'if (AddBagItem(sPartyMenuItemId, 1) == FALSE)',
      'else if (ItemIsMail(gSpecialVar_ItemId))',
      'DisplaySwitchedHeldItemMessage(gSpecialVar_ItemId, sPartyMenuItemId, TRUE);',
      'void ChooseMonToGiveMailFromMailbox(void)',
      'InitPartyMenu(PARTY_MENU_TYPE_FIELD, PARTY_LAYOUT_SINGLE, PARTY_ACTION_GIVE_MAILBOX_MAIL, FALSE, PARTY_MSG_GIVE_TO_WHICH_MON, Task_HandleChooseMonInput, Mailbox_ReturnToMailListAfterDeposit);',
      'case PARTY_ACTION_GIVE_MAILBOX_MAIL:', 'TryGiveMailToSelectedMon(taskId);'):
        need(token in body, '固定公開sourceの新producer意味')
    return True


def selected_profile(lane, profile=None):
    need(type(lane)is str and lane in PROFILES, '閉じた二rootの選択')
    p=PROFILES[lane] if profile is None else profile
    need(type(p)is dict and exact(p,PROFILES[lane]), '型厳密なroot別十分条件')
    return copy.deepcopy(p)


def bind_semantics(raw):
    for name,(mod,rows) in ALL_BLOCKS.items():
        for ins in rows:
            need(chunk(raw,ins.address,ins.size)==mod.encoded(ins), 'producer意味 '+name+' '+hex(ins.address))
    for a,v in ALL_WORDS.items():
        need(take.d.u32(raw,a)==v, 'producer literal/登録cell '+hex(a))
    return True


class Machine(take.Machine):
    def __init__(self,*args,trace=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.trace=[] if trace is None else trace

    def read(self,a,n):
        value=super().read(a,n)
        if not 0x08000000<=a<0x0A000000:
            self.trace.append(('read',a,n))
        return value

    def write(self,a,n,value):
        super().write(a,n,value)
        self.trace.append(('write',a,n))


SETUP_SUCCESS={0x0811F4D4,0x0811F4FC,0x0811F558,0x0811F578}
SETUP_CALLS={(ins.address,ins.args[0]) for name in REUSED['setup'][1]
             if name.startswith('setup_') for ins in setup.BLOCKS[name] if ins.kind=='call'}
# 実行するopaqueだけを(site,target)で登録する。targetだけの包括許可はしない。
EXTERNAL={
 (0x081240DE,0x08120B60),(0x081240EA,0x081227D8),(0x08124112,0x08110BF8),
 (0x08124138,0x08099BE0),(0x08124142,0x08099A8C),(0x0812418A,0x08097AE8),
 (0x081241D8,0x08120DB8),(0x0811F280,0x08002B9C),(0x0811F37E,0x08040330),
 (0x08000512,0x080F6168),(0x0800051A,0x0813C034),(0x0811F3DA,0x080C0918),
 (0x0811F3F2,0x080C08D8),(0x0812032C,0x080C0918),(0x0812033E,0x081206EC),
 (0x0812055A,0x0803F354),(0x081204A4,0x08071A70),
 (0x0811F3AE,0x080066D8),(0x0811F3B2,0x08006724),
 (0x0811F3B6,0x080F7810),(0x0811F3BA,0x0806FC74),
 (0x0811F5CE,0x081224D8),
} | SETUP_CALLS


def _compose(raw,lane,profile,boundary_live=None,opaque_writes=None,epoch_events=None):
    pointer=runtime.ROOT+runtime.HEADER
    memory=runtime.task_fixture([(0,0)] if lane=='exchange' else [])
    for a,n in ((pointer,568),(PARTY,20),(MAIN,1100)):
        for j in range(n):memory[a+j]=0
    runtime.setmem(memory,0x020379F3,1,0)
    if lane=='exchange':
        runtime.setmem(memory,TASKS,4,0x081240D9)
        runtime.setmem(memory,NEW_ITEM_CELL,2,NEW_ITEM)
        runtime.setmem(memory,OLD_ITEM_CELL,2,OLD_ITEM)
    entry_memory=dict(memory)
    trace=[];boundaries=[];events=[];frames=[];groups=[]
    selected=0 if lane=='exchange' else None
    allocated=False

    def membership(m,expected):
        # 非選択taskはactive bitだけ。task配列全体を不変条件にしない。
        for i in range(16):
            need(m.read(TASKS+40*i+4,1)==int(i==0), '有限profileのactive所属')
        need(m.read(TASKS,4)==expected and m.read(TASKS+5,1)==254
             and m.read(TASKS+6,1)==255 and m.read(TASKS+7,1)==0, '同taskの登録/連結/優先度')

    def run(entry,mem,registers=None,stop=None):
        nonlocal selected,allocated
        m=Machine(raw,entry,registers=registers,memory=mem,instructions=INS,trace=trace)
        if entry==0x08000510:
            need(m.read(MAIN,4)==0, 'main callback1は各selected frameでnull')
        while m.pc not in (0xFFFFFFF0,stop):
            if m.pc in INS:
                if m.pc==0x081240FA:
                    need(m.reg[1]==TASKS and m.reg[0]==0x0812410D, '同task0への実登録STR')
                    events.append(dict(role='same_task_input_registration',address=m.pc,task_id=0,
                                       registered_thumb=m.reg[0],task_cell=m.reg[1]))
                elif m.pc==0x08127D28:
                    need(m.reg[:4]==[0,0,7,0] and [m.read(m.reg[13]+j,4) for j in (0,4,8)]==[6,0x08120319,0x080ED451], 'mailboxの実constructor引数')
                    events.append(dict(role='mailbox_constructor_arguments',address=m.pc,action=7))
                elif m.pc==0x0811F5C4:
                    need(m.reg[:2]==[0x08120319,0], '同constructor field0の実CreateTask引数')
                    need(all(m.read(TASKS+40*i+4,1)==0 for i in range(16)), '選択例は空task list')
                elif m.pc==0x0811F5C8:
                    selected=m.reg[0]
                    need(selected==0, '実CreateTask成功結果0')
                    membership(m,0x08120319)
                    events.append(dict(role='admitted_same_task',address=0x0811F5C4,task_id=selected))
                elif m.pc==0x081203E6:
                    need(m.reg[0]==0x08120404, '現hook action7が実jump-table cellを選択')
                    events.append(dict(role='mailbox_action_cell',address=m.pc,cell=m.reg[0],target=0x08120496))
                elif m.pc==0x081204AA:
                    need(m.reg[0]==selected==0, 'mailbox callbackへ同CreateTask結果')
                m.step()
                continue
            need(runtime.concrete(m.reg[14]) and m.reg[14]&1==1, '未束縛枝をcallee復帰として扱わない')
            site=(m.reg[14]&~1)-4;target=m.pc;key=(site,target)
            need(key in EXTERNAL, '未登録opaque/枝を拒否 '+hex(site)+' -> '+hex(target))
            result=runtime.U;outputs=[]
            if site==0x081240DE:result=profile['text_active']
            elif site==0x08124112:result=profile['yes_input']
            elif site==0x08124138:
                need(m.reg[:2]==[NEW_ITEM,1], 'RemoveBagItemの実new item/quantity')
            elif site==0x08124142:
                need(m.reg[:2]==[OLD_ITEM,1], 'AddBagItemの実old item/quantity')
                result=profile['bag_success']
            elif site==0x0812418A:
                need(m.reg[0]==NEW_ITEM, '新itemのmail判定')
                result=profile['item_is_mail']
            elif site==0x081241D8:
                need(m.reg[:2]==[MONS,NEW_ITEM], 'GiveItemToMonの実slot0/new item')
            elif site==0x0811F280:
                need(m.reg[0]==568, '実Allocサイズ568')
                result=pointer;allocated=True
            elif site in (0x08000512,0x0800051A,0x0811F3DA,0x0812032C):result=0
            elif site==0x0811F3F2:result=1
            elif site==0x0811F4BC:result=0
            elif site in SETUP_SUCCESS:result=1
            elif site==0x0812033E:
                need(m.reg[0]==PARTY+9, '実slot pointerをinput helperへ渡す')
                result=profile['choose_mon_input']
            elif site==0x0812055A:
                need(m.reg[:2]==[MONS,45], 'mailbox選択monのegg getter')
                result=profile['egg']
            elif site==0x081204A4:need(m.reg[0]==5, 'mailbox選択音5')
            index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
            if boundary_live is not None:
                fields=boundary_live[index]
                event=(epoch_events or {}).get(site,{})
                if allocated:
                    need(not event.get('heap_reinitialized',False) and pointer not in event.get('freed',()), '必要な同object epoch')
                if selected is not None:
                    need(not event.get('task_invalidated',False), 'selected taskの所属/epoch条件')
                writes=(opaque_writes or {}).get(site,())
                for a,n,v in writes:
                    need(not any(a<b+z and b<a+n for b,z in fields), 'future-live RAMへのopaque write')
                    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
                kept={a+j for a,n in fields for j in range(n)}
                m.mem={a:v for a,v in m.mem.items() if a in kept}
                groups.append(dict(site=site,target=target,required_fields=[dict(address=a,size=n) for a,n in fields],
                  normal_abi_return_required=True,effects_discharged=False,
                  return_value=result if runtime.concrete(result) else 'unspecified',
                  conditional_outputs=outputs,object_epoch_required=allocated,
                  same_selected_task_required=selected is not None,
                  discarded_registers=['r0','r1','r2','r3','r12','lr'],flags_discarded=True))
            return_pc=m.reg[14]&~1
            for r in (0,1,2,3,12,14):m.reg[r]=runtime.U
            m.reg[0]=result;m.flags=(runtime.U,)*4;m.flag_pc=None;m.pc=return_pc
        if stop is None:need(m.reg[13]==0x03007000, '完結phaseのstack均衡')
        frames.append(dict(entry=entry,stop=m.pc,instruction_steps=m.steps))
        return m

    if lane=='exchange':
        m=run(0x081240D8,memory,{0:0})
        membership(m,0x0812410D)
        m=run(0x08076D10,m.mem,stop=ENDPOINTS[lane])
        need(m.reg[:3]==[NEW_ITEM,OLD_ITEM,1], '交換callbackの実3引数')
    else:
        m=run(0x08127D10,memory)
        need(m.read(MAIN+4,4)==0x0811F3D9 and m.read(pointer,4)==0x08120319
             and m.read(PARTY+11,1)==7, 'mailbox constructorの実action/task登録')
        for state in range(24):
            need(m.read(MAIN+1080,1)==state, '実setup状態の連続')
            m=run(0x08000510,m.mem)
        need(m.read(MAIN+4,4)==0x0811F3A9, '有限setupから実party schedulerへ')
        membership(m,0x08120319)
        m=run(0x08000510,m.mem,stop=ENDPOINTS[lane])
        need(m.reg[0]==selected==0, 'mailbox callbackの実task引数')
    need(m.pc==ENDPOINTS[lane] and m.read(PARTY+9,1)==0, 'callback入口と実slot0を保持')
    membership(m,0x0812410D if lane=='exchange' else 0x08120319)
    written=set();entry_reads=set()
    for kind,a,n in trace:
        if kind=='write':written.update(range(a,a+n))
        elif kind=='read':entry_reads.update(set(range(a,a+n))-written)
    initial=[];allocation=[]
    for a in sorted(entry_reads):
        value=entry_memory.get(a,runtime.U)
        row=dict(address=a,size=1,value=value if runtime.concrete(value) else 'unspecified')
        (allocation if lane=='mailbox' and pointer<=a<pointer+568 else initial).append(row)
    return m,dict(events=events,frames=frames,trace=trace,boundaries=boundaries,groups=groups,
                  required_initial_memory=initial,allocation_result_memory_conditions=allocation)


def compose_selected(raw,lane='exchange',return_machine=False,profile=None,opaque_writes=None,epoch_events=None):
    """二rootの片方だけを新profileで実行し、callback入口の状態を返す。"""
    profile=selected_profile(lane,profile)
    need(type(return_machine)is bool, 'machine返却flagはbool')
    bind_semantics(raw)
    for value in (opaque_writes,epoch_events):need(value is None or type(value)is dict, '境界入力はdictのみ')
    for site,rows in (opaque_writes or {}).items():
        need(type(site)is int and type(rows)in(list,tuple), 'write site/rows型')
        for row in rows:
            need(type(row)in(list,tuple) and len(row)==3 and all(type(x)is int for x in row), 'writeは整数3個')
            a,n,v=row;need(0<n<=4096 and 0<=a<a+n<=1<<32 and 0<=v<1<<(8*n), '有限write幅/値')
    for site,event in (epoch_events or {}).items():
        need(type(site)is int and type(event)is dict and set(event)<={'freed','heap_reinitialized','task_invalidated'}, 'epochの閉schema')
        for key in ('heap_reinitialized','task_invalidated'):
            need(key not in event or type(event[key])is bool, 'epoch flagはbool')
        need('freed' not in event or type(event['freed'])is list and all(type(a)is int and a%4==0 and 0<=a<1<<32 for a in event['freed']), 'Free先は整列住所list')
    first_machine,first=_compose(raw,lane,profile)
    known={site for site,target in first['boundaries']}
    need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known, '非実行siteを黙殺しない')
    fields=live.future_live(first['trace'],len(first['boundaries']))
    m,second=_compose(raw,lane,profile,fields,opaque_writes,epoch_events)
    need(first['events']==second['events'] and first['frames']==second['frames']
         and first['boundaries']==second['boundaries'], 'nonlive RAM消去後も同root/登録/dispatch')
    for row in second['groups']:
        if row['site']==0x0811F280:
            row['conditional_outputs']=copy.deepcopy(second['allocation_result_memory_conditions'])
    proof=dict(status='PASS_CONDITIONAL_ITEM_PRODUCER_TO_CALLBACK_ENTRY',lane=lane,
        profile=profile,root=copy.deepcopy(ROOTS[lane]),input_contract=copy.deepcopy(CONTRACT),
        reached_instruction=m.pc,selected_task=0,callback_arguments=m.reg[:3] if lane=='exchange' else m.reg[:1],
        events=second['events'],frames=second['frames'],conditional_calls=second['groups'],
        required_initial_memory=second['required_initial_memory'],
        allocation_result_memory_conditions=second['allocation_result_memory_conditions'],
        boundary_count=len(second['groups']),instruction_steps=sum(f['instruction_steps'] for f in second['frames']),
        nonlive_ram_erased_at_each_boundary=True,old_positive_profile_reexecuted=False,**copy.deepcopy(CLAIMS))
    return (proof,m) if return_machine else proof
