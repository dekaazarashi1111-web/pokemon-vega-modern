"""無線ミニゲームの実constructorから参加拒否/取消callback入口への条件付き有限型。"""
import copy
import hashlib

import pr16_dex_hof_party_takeitem as take
import pr16_dex_hof_menu_text as live

party, task, setup, menu, runtime = take.party, take.task, take.setup, take.menu, take.runtime
need, chunk = take.need, take.chunk
HEAP, TASKS, PARTY, MONS, MAIN = take.HEAP, take.TASKS, take.PARTY, take.MONS, take.MAIN
CANDIDATE = copy.deepcopy(take.CANDIDATE)
MODE, PARTY_COUNT, BITFLAG = 0x02036FF6, 0x02023F89, 0x0203B022
ENDPOINTS = {'entry':0x081211E4, 'cancel':0x08121248}
SOURCE_IDS = copy.deepcopy(take.SOURCE_IDS)
for key, path, size, sha, blob in (
 ('cfru-general_hooks.s','assembly/hooks/general_hooks.s',27806,
  'd352401ff799e92e6d85b6cc4c68186e409561760364f9bd4d5fc9388b02fe1f',
  '6f05fd6603a31e05d2c5fc3ba3f7bea68a297f30'),
 ('cfru-hooks','hooks',21787,
  '19c730e12bcc8ee614b43745a1a6478429c1876a025fdce23b80a49599d8deb5',
  '51a0f10dd4cccad235b476edd534a0e3e7e612ad')):
    SOURCE_IDS[key]=dict(local=key,repository='kapibarasan000/CFRU-JP',
        commit='e24a16fe39e27ae162faf5b78596d1f3df18489d',path=path,
        size=size,sha256=sha,git_blob_sha=blob)

BLOCKS = {}
def put(name,address,specs):
    BLOCKS[name]=tuple(party.block(address,specs))

# 意味operandのみ。旧手元ROMの設計窓は現候補受入の代用にしない。
put('wireless_minigame_constructor_root',0x081281C0,[
 ('push',0,True),('spadd',-12),('imm','mov',0,1),('spmem',False,0,0),
 ('literal',0,0x081281E4),('spmem',False,0,4),('literal',0,0x081281E8),
 ('spmem',False,0,8),('imm','mov',0,11),('imm','mov',1,0),('imm','mov',2,13),
 ('imm','mov',3,0),('call',0x0811F24C),('spadd',12),('pop',1,False),('bx',0)])
put('minigame_type_and_mode_selector',0x081210D4,[
 ('push',48,True),('literal',2,0x08121124),('mem',True,'byte',1,2,8),
 ('imm','mov',0,15),('alu','and',0,1),('imm','cmp',0,11),('branch',1,0x0812115E),
 ('addi',5,2,0),('imm','add',5,14),('imm','mov',0,0),('mem',False,'half',0,2,14),
 ('literal',0,0x08121128),('mem',True,'half',0,0,0),('imm','cmp',0,0),('branch',1,0x08121134)])
put('minigame_dodrio_loop',0x08121134,[
 ('imm','mov',4,0),('jump',0x08121156),('imm','mov',0,100),('alu','mul',0,4),
 ('literal',1,0x08121164),('add',0,0,1),('call',0x0812119C),
 ('shift','lsl',0,0,16),('shift','lsr',0,0,16),('alu_ext','lsl',0,4),
 ('mem',True,'half',1,5,0),('add',0,0,1),('mem',False,'half',0,5,0),
 ('addi',0,4,1),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('literal',0,0x08121168),('mem',True,'byte',0,0,0),('compare',4,0),('branch',3,0x08121138),
 ('pop',48,False),('pop',1,False),('bx',0)])
put('dodrio_eligibility',0x0812119C,[
 ('push',16,True),('addi',4,0,0),('imm','mov',1,45),('call',0x0803F354),
 ('imm','cmp',0,1),('branch',0,0x081211BA),('addi',0,4,0),('imm','mov',1,11),
 ('call',0x0803F354),('imm','cmp',0,85),('branch',1,0x081211BA),
 ('imm','mov',0,1),('jump',0x081211BC),('imm','mov',0,0),
 ('pop',16,False),('pop',2,False),('bx',1)])
put('action13_to_entry_callback',0x08120524,[
 ('addi',0,5,0),('call',0x0812054C),('shift','lsl',0,0,24),('imm','cmp',0,0),
 ('branch',0,0x08120546),('mem',True,'byte',1,5,0),('addi',0,6,0),('call',0x081211E4)])
put('choose_mon_b_input',0x08120368,[
 ('addi',0,6,0),('addi',1,4,0),('call',0x08120578)])
put('cancel_hook_trampoline',0x08120578,[('literal',2,0x0812057C),('bx',2)])
put('actual_cancel_hook',0x09097AB4,[
 ('push',48,True),('addi',5,1,0),('shift','lsl',0,0,24),('shift','lsr',4,0,24),
 ('literal',0,0x09097ACC),('mem',True,'byte',0,0,11),('imm','cmp',0,15),
 ('branch',0,0x09097AC8),('literal',0,0x09097AD0),('bx',0)])
put('cancel_action_selector',0x08120580,[
 ('literal',0,0x08120594),('mem',True,'byte',0,0,11),('imm','cmp',0,8),
 ('branch',0,0x081205AA),('imm','cmp',0,8),('branch',12,0x08120598)])
put('cancel_action13_selector',0x08120598,[
 ('imm','cmp',0,10),('branch',0,0x081205AA),('imm','cmp',0,13),('branch',0,0x081205B8)])
put('action13_to_cancel_callback',0x081205B8,[
 ('imm','mov',0,5),('call',0x08071A70),('addi',0,4,0),('call',0x08121248)])
LITERALS={
 0x081281E4:0x08120319,0x081281E8:0x080561A1,
 0x08121124:PARTY,0x08121128:MODE,0x08121164:MONS,0x08121168:PARTY_COUNT,
 0x0812041C:0x08120524,0x0812057C:0x09097AB5,0x08120594:PARTY,
 0x09097ACC:PARTY,0x09097AD0:0x08120581,
}
REUSED={
 'party':(party,('interwork_r1',)),
 'task':(task,('run_tasks_field0_dispatch','choose_mon_input','choose_mon_confirm',
  'cursor_pointer_choice','cursor_party_slot','selection_hook_entry','selection_hook_trampoline',
  'actual_action_selector_hook','actual_action_selector_resume','action9_table_consumer',
  'non_egg_success','non_egg_return')),
 'setup':(setup,take.REUSED['setup'][1]),
 'runtime':(runtime,take.REUSED['runtime'][1]),
}
ALL_BLOCKS={name:(menu,rows) for name,rows in BLOCKS.items()}
ALL_WORDS=dict(LITERALS)
for scope,(mod,names) in REUSED.items():
    for name in names:
        rows=mod.BLOCKS[name];ALL_BLOCKS[scope+'_'+name]=(mod,rows)
        for ins in rows:
            if ins.kind=='literal':
                a=ins.args[1]
                need(a not in ALL_WORDS or ALL_WORDS[a]==mod.LITERALS[a],'共通literalの一致')
                ALL_WORDS[a]=mod.LITERALS[a]
ALL_WORDS.update(setup.TABLE)
INS={}
for mod,rows in ALL_BLOCKS.values():
    for ins in rows:
        need(ins.address not in INS or menu.encoded(INS[ins.address])==mod.encoded(ins),'共通命令の一致')
        INS[ins.address]=ins
WINDOWS={name:(rows[0].address,sum(i.size for i in rows)) for name,(mod,rows) in ALL_BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in sorted(ALL_WORDS)})
FIELDS={}
PROFILES={lane:dict(task_id=0,party_slot=0,menu_type=11,action=13,mode=1,party_count=1,
    egg=0,species=1,choose_mon_input=button,normal_returns=True,fields_preserved=True,stack_nonalias=True)
    for lane,button in (('entry',1),('cancel',2))}
ROOTS={lane:dict(entry=0x081281C0,constructor_call=0x081281D8,constructor=0x0811F24C,
    constructor_register_arguments=[11,0,13,0],constructor_stack_arguments=[1,0x08120319,0x080561A1],
    allocation_size=568,setup_state6_call=0x0811F4CE,bitflag_producer=0x081210D4,
    bitflag_initial_store=0x081210E8,bitflag_accumulating_store=0x0812114E,
    bitflag_address=BITFLAG,setup_state20_call=0x0811F5C4,runtasks=0x08076D10,
    stopped_entry=ENDPOINTS[lane]) for lane in PROFILES}
ROOTS['entry'].update(actual_action_hook=0x09097A80,action_table_cell=0x0812041C,
    action_branch=0x08120524,callback_call=0x08120534)
ROOTS['cancel'].update(input_branch=0x08120368,cancel_trampoline=0x08120578,
    actual_cancel_hook=0x09097AB4,cancel_resume=0x08120580,callback_call=0x081205C0)
CONTRACT={
 'scope':'無線ミニゲームconstructorを共通rootとする二つの有限例。自然操作によるroot到達は未証明。既存TakeItem/交換/mailboxの正profileは再実行しない。',
 'constructor':'実引数(11,0,13,0;1,08120319,080561A1)。568-byte objectから23状態+default、state20のCreateTask成功task0、RunTasksの同row再読まで実命令で接続する。',
 'state6':'SetPartyMonsAllowedInMinigameのmenuType11枝を実行。mode1/partyCount1/非egg/species1の明示getter条件から非Dodrio判定0を生成し、STRH初期化と加算STRHでbitflag0203B022=0を実生産する。menuType0の早期returnやhostのbitflag代入で代用しない。',
 'selection':'input helperの戻り1/2はそれぞれA/B相当の明示条件。実button hardware/key読取は証明しない。entryはaction13実hook/cellと非egg検査、cancelは別hookからstock action13枝を経る。',
 'allocation':'整列した568-byte allocator成功戻りと同epochをcallback受渡しまで保持。object先行read byte8/10..14の0は明示条件でありAllocのzero化効果証明ではない。',
 'initial_ram':'required_initial_memoryはwriteに先行した実RAM readの値条件。未指定byteはunspecifiedで0補完しない。bitflagは先行初期条件に含めず実STRHで生成する。',
 'abi':'各明示siteのopaque calleeは通常Thumb復帰しr4-r11/SP/必要saved stackを保持。r0-r3/r12/LR/flagsはUnknownへ破棄。getter/input/waitの返り値は個別条件で本体の証明ではない。',
 'ram':'各opaque境界のrequired_fieldsは実読取とwriteから逆算したfuture-live RAM。非live RAMは毎境界消去して再実行。callback受渡しのmenuType/action/slot/bitflagと同task/object所属を保持する。',
 'dispatch':'各main dispatchのcallback1=0、fade bit7=0、link-wait戻り0。setup wait成功はsite別に条件化する。同期非再入は前提でIRQ/全callee効果の普遍証明ではない。',
 'endpoint':'entry081211E4で(task0,slot0)、cancel08121248で(task0)を保持し停止。callback本文、bitflag consumer、text readerは別moduleの義務。',
 'identity':'設計用旧手元ROMの限定窓と現0641全ROM受入は区別する。本moduleの疎fixture成功だけではcurrent acceptanceを付与しない。',
}
CLAIMS=dict(conditional_finite_type_only=True,synthetic_contract_execution=True,
 actual_runtime_execution_observed=False,full_story_reachability_claimed=False,
 universal_allocation_epoch_proven=False,all_opaque_effects_proven=False,
 irq_noninterference_proven=False,indirect_reference_completeness_claimed=False,
 callback_body_executed=False,complete_text_reads_proven=False,donor_eligible=False,newly_classified=0,
 current_acceptance_claimed=False)


def source_manifest():
    return copy.deepcopy(SOURCE_IDS)


def sources_bind(sources):
    need(type(sources)is dict and set(sources)==set(SOURCE_IDS),'閉じた固定source集合')
    take.sources_bind({'source_bindings':take.SOURCE_IDS},{k:sources[k] for k in take.SOURCE_IDS})
    for key in set(SOURCE_IDS)-set(take.SOURCE_IDS):
        b=sources[key];row=SOURCE_IDS[key]
        need(take.identity(b)=={k:row[k] for k in ('size','sha256')},'固定hook source全文 '+key)
        need(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'固定hook Git blob '+key)
    body=sources['pret-party_menu.c'].decode()
    for token in (
      'void ChooseMonForWirelessMinigame(void)',
      'InitPartyMenu(PARTY_MENU_TYPE_MINIGAME, PARTY_LAYOUT_SINGLE, PARTY_ACTION_MINIGAME, FALSE, PARTY_MSG_CHOOSE_MON_OR_CANCEL, Task_HandleChooseMonInput, CB2_ReturnToFieldContinueScriptPlayMapMusic);',
      'static void SetPartyMonsAllowedInMinigame(void)', 'minigameBitflag = 0;',
      'minigameBitflag += IsMonAllowedInDodrioBerryPicking(&gPlayerParty[i]) << i;',
      'GetMonData(mon, MON_DATA_SPECIES) == SPECIES_DODRIO',
      'TryEnterMonForMinigame(taskId, (u8)*slotPtr);','HandleChooseMonCancel(taskId, slotPtr);',
      'CancelParticipationPrompt(taskId);'):
        need(token in body,'固定公開sourceのminigame producer意味')
    asm=sources['cfru-general_hooks.s'].decode()
    for token in ('ChooseFaintedMonHook:', 'ChooseFaintedMonCancelHook:',
                  'cmp r0, #0xF','ldr r0, =0x8120580 | 1','ldr r1, =0x81203E0 | 1'):
        need(token in asm,'固定公開hookの独立意味')
    routes=sources['cfru-hooks'].decode()
    for token in ('ChooseFaintedMonHook 81203D4 0','ChooseFaintedMonCancelHook 8120578 2'):
        need(token in routes,'固定公開hookの別登録')
    return True


def exact(a,b):
    """JSON互換値を再帰的に型一致で比較し、bool/intとsubclassを混同しない。"""
    if type(a)is not type(b):return False
    if type(a)is dict:
        return (all(type(k)is str for k in a) and all(type(k)is str for k in b)
                and set(a)==set(b) and all(exact(a[k],b[k]) for k in a))
    if type(a)is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return type(a)in(type(None),bool,int,str) and a==b


def selected_profile(lane,profile=None):
    need(type(lane)is str and lane in PROFILES,'閉じた二callback選択')
    p=PROFILES[lane] if profile is None else profile
    need(type(p)is dict and exact(p,PROFILES[lane]),'型厳密なroot別十分条件')
    return copy.deepcopy(p)


def bind_semantics(raw):
    for name,(mod,rows) in ALL_BLOCKS.items():
        for ins in rows:
            need(chunk(raw,ins.address,ins.size)==mod.encoded(ins),'producer意味 '+name+' '+hex(ins.address))
    for a,v in ALL_WORDS.items():need(take.d.u32(raw,a)==v,'producer literal/登録cell '+hex(a))
    return True


class Machine(take.Machine):
    def __init__(self,*args,trace=None,**kwargs):
        super().__init__(*args,**kwargs);self.trace=[] if trace is None else trace

    def read(self,a,n):
        value=super().read(a,n)
        if not 0x08000000<=a<0x0A000000:self.trace.append(('read',a,n))
        return value

    def write(self,a,n,value):
        super().write(a,n,value);self.trace.append(('write',a,n))

    def step(self,*args,**kwargs):
        ins=self.instructions.get(self.pc)
        if ins is not None and ins.kind=='alu_ext' and ins.args[0]=='lsl':
            _,rd,rs=ins.args;value,amount=self.reg[rd],self.reg[rs]
            if runtime.concrete(value) and runtime.concrete(amount):
                amount&=255
                self.reg[rd]=(value<<amount)&runtime.MASK if amount<32 else 0
            else:self.reg[rd]=runtime.U
            self.flags=(runtime.U,)*4;self.flag_pc=None
            self.pc+=2;self.steps+=1;need(self.steps<30000,'有限shift実行');return
        return super().step(*args,**kwargs)


SETUP_SUCCESS={0x0811F4D4,0x0811F4FC,0x0811F558,0x0811F578}
SETUP_CALLS={(ins.address,ins.args[0]) for name in REUSED['setup'][1]
    if name.startswith('setup_') for ins in setup.BLOCKS[name] if ins.kind=='call' and ins.args[0] not in INS}
EXTERNAL={
 (0x0811F280,0x08002B9C),(0x0811F37E,0x08040330),
 (0x08000512,0x080F6168),(0x0800051A,0x0813C034),(0x0811F3DA,0x080C0918),
 (0x0811F3F2,0x080C08D8),(0x0812032C,0x080C0918),(0x0812033E,0x081206EC),
 (0x081211A2,0x0803F354),(0x081211AE,0x0803F354),(0x0812055A,0x0803F354),
 (0x081205BA,0x08071A70),(0x0811F3AE,0x080066D8),(0x0811F3B2,0x08006724),
 (0x0811F3B6,0x080F7810),(0x0811F3BA,0x0806FC74),(0x0811F5CE,0x081224D8),
} | SETUP_CALLS


def _compose(raw,lane,profile,boundary_live=None,opaque_writes=None,epoch_events=None):
    pointer=runtime.ROOT+runtime.HEADER
    memory=runtime.task_fixture([])
    for a,n in ((pointer,568),(PARTY,20),(MAIN,1100)):
        for j in range(n):
            if a+j not in (BITFLAG,BITFLAG+1):memory[a+j]=0
    runtime.setmem(memory,0x020379F3,1,0)
    runtime.setmem(memory,MODE,2,profile['mode'])
    runtime.setmem(memory,PARTY_COUNT,1,profile['party_count'])
    entry_memory=dict(memory)
    trace=[];boundaries=[];events=[];frames=[];groups=[]
    selected=None;allocated=False

    def membership(m,expected):
        for i in range(16):
            need(m.read(TASKS+40*i+4,1)==int(i==0),'有限profileのactive所属')
        need(m.read(TASKS,4)==expected and m.read(TASKS+5,1)==254
             and m.read(TASKS+6,1)==255 and m.read(TASKS+7,1)==0,'同taskの登録/連結/優先度')

    def run(entry,mem,registers=None,stop=None):
        nonlocal selected,allocated
        m=Machine(raw,entry,registers=registers,memory=mem,instructions=INS,trace=trace)
        if entry==0x08000510:need(m.read(MAIN,4)==0,'main callback1は各selected frameでnull')
        while m.pc not in (0xFFFFFFF0,stop):
            if m.pc in INS:
                if m.pc==0x081281D8:
                    need(m.reg[:4]==[11,0,13,0] and [m.read(m.reg[13]+j,4) for j in (0,4,8)]==[1,0x08120319,0x080561A1],'minigame実constructor引数')
                    events.append(dict(role='minigame_constructor_arguments',address=m.pc,menu_type=11,action=13))
                elif m.pc==0x0811F4CE:
                    need(m.read(MAIN+1080,1)==6 and m.read(PARTY+8,1)&15==11,'実state6とmenuType11')
                    events.append(dict(role='state6_real_producer_call',address=m.pc,target=0x081210D4))
                elif m.pc==0x081210E8:
                    need(m.reg[2]+14==BITFLAG and m.reg[0]==0,'bitflag初期化は実STRH')
                    events.append(dict(role='bitflag_initial_store',address=m.pc,target=BITFLAG,value=0))
                elif m.pc==0x0812114E:
                    need(m.reg[5]==BITFLAG and m.reg[4]==0 and m.reg[0]==0,'非Dodrio結果をslot0へ実加算STRH')
                    events.append(dict(role='bitflag_accumulating_store',address=m.pc,target=BITFLAG,value=0,slot=0))
                elif m.pc==0x0811F5C4:
                    need(m.reg[:2]==[0x08120319,0],'同constructor field0の実CreateTask引数')
                    need(all(m.read(TASKS+40*i+4,1)==0 for i in range(16)),'選択例は空task list')
                elif m.pc==0x0811F5C8:
                    selected=m.reg[0];need(selected==0,'実CreateTask成功結果0')
                    membership(m,0x08120319)
                    events.append(dict(role='admitted_same_task',address=0x0811F5C4,task_id=selected))
                elif m.pc==0x081203E6:
                    need(lane=='entry' and m.reg[0]==0x0812041C,'action13が実jump-table cellを選択')
                    events.append(dict(role='minigame_action_cell',address=m.pc,cell=m.reg[0],target=0x08120524))
                elif m.pc==0x09097AB4:
                    need(lane=='cancel' and m.reg[:2]==[0,PARTY+9],'別cancel hookへ同taskとslot pointer')
                    events.append(dict(role='separate_cancel_hook',address=m.pc,task_id=m.reg[0],slot_pointer=m.reg[1]))
                elif m.pc==0x08120580:
                    need(m.reg[4]==selected==0 and m.reg[5]==PARTY+9,'cancel hookのABI保存とstock復帰')
                    events.append(dict(role='cancel_stock_resume',address=m.pc,action=13))
                elif m.pc==ROOTS[lane]['callback_call']:
                    need(m.reg[0]==selected==0,'同CreateTask結果をcallbackへ渡す')
                    if lane=='entry':need(m.reg[1]==0,'実slot0をentry callbackへ渡す')
                m.step();continue
            need(runtime.concrete(m.reg[14]) and m.reg[14]&1==1,'未束縛枝をcallee復帰として扱わない')
            site=(m.reg[14]&~1)-4;target=m.pc;key=(site,target)
            need(key in EXTERNAL,'未登録opaque/枝を拒否 '+hex(site)+' -> '+hex(target))
            result=runtime.U;outputs=[]
            if site==0x0811F280:
                need(m.reg[0]==568,'実Allocサイズ568');result=pointer;allocated=True
            elif site in (0x08000512,0x0800051A,0x0811F3DA,0x0812032C):result=0
            elif site==0x0811F3F2:result=1
            elif site==0x0811F4BC:result=0
            elif site in SETUP_SUCCESS:result=1
            elif site==0x0812033E:
                need(m.reg[0]==PARTY+9,'実slot pointerをinput helperへ渡す')
                result=profile['choose_mon_input']
            elif site in (0x081211A2,0x0812055A):
                need(m.reg[:2]==[MONS,45],'同slot0のegg getter');result=profile['egg']
            elif site==0x081211AE:
                need(m.reg[:2]==[MONS,11],'同slot0のspecies getter');result=profile['species']
            elif site==0x081205BA:need(m.reg[0]==5,'cancel選択音5')
            index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
            if boundary_live is not None:
                need(index<len(boundary_live),'境界数を固定')
                fields=boundary_live[index];event=(epoch_events or {}).get(site,{})
                if allocated:
                    need(not event.get('heap_reinitialized',False) and pointer not in event.get('freed',()),'必要な同object epoch')
                if selected is not None:need(not event.get('task_invalidated',False),'selected taskの所属/epoch条件')
                for a,n,v in (opaque_writes or {}).get(site,()):
                    need(not any(a<b+z and b<a+n for b,z in fields),'future-live RAMへのopaque write')
                    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
                kept={a+j for a,n in fields for j in range(n)}
                m.mem={a:v for a,v in m.mem.items() if a in kept}
                groups.append(dict(site=site,target=target,required_fields=[dict(address=a,size=n) for a,n in fields],
                    normal_abi_return_required=True,effects_discharged=False,
                    return_value=result if runtime.concrete(result) else 'unspecified',conditional_outputs=outputs,
                    object_epoch_required=allocated,same_selected_task_required=selected is not None,
                    discarded_registers=['r0','r1','r2','r3','r12','lr'],flags_discarded=True))
            return_pc=m.reg[14]&~1
            for r in (0,1,2,3,12,14):m.reg[r]=runtime.U
            m.reg[0]=result;m.flags=(runtime.U,)*4;m.flag_pc=None;m.pc=return_pc
        if stop is None:need(m.reg[13]==0x03007000,'完結phaseのstack均衡')
        frames.append(dict(entry=entry,stop=m.pc,instruction_steps=m.steps));return m

    m=run(0x081281C0,memory)
    need(m.read(MAIN+4,4)==0x0811F3D9 and m.read(pointer,4)==0x08120319
         and m.read(PARTY+11,1)==13 and m.read(PARTY+8,1)&15==11,'constructorの実type/action/task登録')
    for state in range(24):
        need(m.read(MAIN+1080,1)==state,'実setup状態の連続')
        m=run(0x08000510,m.mem)
    need(m.read(MAIN+4,4)==0x0811F3A9,'有限setupから実party schedulerへ')
    membership(m,0x08120319)
    m=run(0x08000510,m.mem,stop=ENDPOINTS[lane])
    need(m.pc==ENDPOINTS[lane] and m.reg[0]==selected==0,'callback入口と同task0')
    if lane=='entry':need(m.reg[1]==0,'entry callbackへ実slot0')
    # 後続consumerへ引き渡す実読取をtraceへ残し、opaque境界で先に消えないようにする。
    need(m.read(PARTY+9,1)==0 and m.read(PARTY+8,1)&15==11
         and m.read(PARTY+11,1)==13 and m.read(BITFLAG,2)==0,'callbackへ同slot/type/action/実生成bitflag0')
    need(m.read(HEAP,4)==pointer and m.read(pointer,4)==0x08120319,'callbackへ同objectとtask field0')
    membership(m,0x08120319)
    need(sum(e['role']=='bitflag_initial_store' for e in events)==1
         and sum(e['role']=='bitflag_accumulating_store' for e in events)==1,'state6の二つの実STRHを各1回実行')
    written=set();entry_reads=set()
    for kind,a,n in trace:
        if kind=='write':written.update(range(a,a+n))
        elif kind=='read':entry_reads.update(set(range(a,a+n))-written)
    need(not entry_reads.intersection((BITFLAG,BITFLAG+1)),'bitflagはhost初期条件ではない')
    initial=[];allocation=[]
    for a in sorted(entry_reads):
        value=entry_memory.get(a,runtime.U)
        row=dict(address=a,size=1,value=value if runtime.concrete(value) else 'unspecified')
        (allocation if pointer<=a<pointer+568 else initial).append(row)
    return m,dict(events=events,frames=frames,trace=trace,boundaries=boundaries,groups=groups,
        required_initial_memory=initial,allocation_result_memory_conditions=allocation)


def compose_selected(raw,lane='entry',return_machine=False,profile=None,opaque_writes=None,epoch_events=None):
    """実constructor/state6/task生成を実行し、選んだcallback入口の状態を返す。"""
    profile=selected_profile(lane,profile)
    need(type(return_machine)is bool,'machine返却flagはbool');bind_semantics(raw)
    for value in (opaque_writes,epoch_events):need(value is None or type(value)is dict,'境界入力はdictのみ')
    for site,rows in (opaque_writes or {}).items():
        need(type(site)is int and type(rows)in(list,tuple),'write site/rows型')
        for row in rows:
            need(type(row)in(list,tuple) and len(row)==3 and all(type(x)is int for x in row),'writeは整数3個')
            a,n,v=row;need(0<n<=4096 and 0<=a<a+n<=1<<32 and 0<=v<1<<(8*n),'有限write幅/値')
    for site,event in (epoch_events or {}).items():
        need(type(site)is int and type(event)is dict and set(event)<={'freed','heap_reinitialized','task_invalidated'},'epochの閉schema')
        for key in ('heap_reinitialized','task_invalidated'):
            need(key not in event or type(event[key])is bool,'epoch flagはbool')
        need('freed' not in event or type(event['freed'])is list and all(type(a)is int and a%4==0 and 0<=a<1<<32 for a in event['freed']),'Free先は整列住所list')
    _,first=_compose(raw,lane,profile)
    known={site for site,target in first['boundaries']}
    need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known,'非実行siteを黙殺しない')
    fields=live.future_live(first['trace'],len(first['boundaries']))
    m,second=_compose(raw,lane,profile,fields,opaque_writes,epoch_events)
    need(first['events']==second['events'] and first['frames']==second['frames']
         and first['boundaries']==second['boundaries'],'nonlive RAM消去後も同root/生成/dispatch')
    for row in second['groups']:
        if row['site']==0x0811F280:row['conditional_outputs']=copy.deepcopy(second['allocation_result_memory_conditions'])
    proof=dict(status='PASS_CONDITIONAL_MINIGAME_PRODUCER_TO_CALLBACK_ENTRY',lane=lane,
        profile=profile,root=copy.deepcopy(ROOTS[lane]),input_contract=copy.deepcopy(CONTRACT),
        reached_instruction=m.pc,selected_task=0,callback_arguments=m.reg[:2] if lane=='entry' else m.reg[:1],
        events=second['events'],frames=second['frames'],conditional_calls=second['groups'],
        required_initial_memory=second['required_initial_memory'],
        allocation_result_memory_conditions=second['allocation_result_memory_conditions'],
        boundary_count=len(second['groups']),instruction_steps=sum(f['instruction_steps'] for f in second['frames']),
        bitflag_host_seeded=False,bitflag_value=m.read(BITFLAG,2),state6_body_executed=True,
        nonlive_ram_erased_at_each_boundary=True,old_positive_profile_reexecuted=False,**copy.deepcopy(CLAIMS))
    return (proof,m) if return_machine else proof


def follow(raw,lane='entry',**kwargs):
    """root実行APIの別名。戻り型と厳密profileはcompose_selectedと同じ。"""
    return compose_selected(raw,lane,**kwargs)


raw_bind=bind_semantics
