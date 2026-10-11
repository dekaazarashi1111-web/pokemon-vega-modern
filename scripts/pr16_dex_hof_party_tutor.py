"""special397の通常Tutor有限continuationから6byteだけを型付けする。

ReadMail phaseの証明は使わない。既存の独立Thumb encoder/VM機構と固定根を
再利用し、Tutor固有のproducer、同taskの再登録、入力と外部境界を結合する。
私有入力I/Oなし。外部calleeの正常復帰条件は実行観測・無opaque証明ではない。
"""
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
HIT=0x08126B0B
KIND='rooted_party_tutor_minimal_thumb'
TASKS,PARTY,HEAP_CELL=party.TASKS,0x0203B014,party.HEAP_CELL
MOVES_CELL,MOVES=0x081213D4,0x0944BC80
SOURCE_IDS={'pret-party_menu.c':dict(local='pret-party_menu.c',repository='pret/pokefirered',
 commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/party_menu.c',source='src/party_menu.c',
 url='https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/party_menu.c',
 size=211085,sha256='8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b',
 git_blob_sha='7f3a881e6c56773aee03da475c9a1adc50530223')}
PRIOR_REFS={'party_review': {'path': 'content/modernization/pr16_dex_hof_callback_party_review.json',
                  'size': 30492,
                  'sha256': '9aab39682b78ac5199357955cd634ef2ce14d0c4f0b60643dba944f5b7a31691'},
 'setup_review': {'path': 'content/modernization/pr16_dex_hof_lifetime_setup_review.json',
                  'size': 33229,
                  'sha256': '2a39c2c125df3a0b23d3bb6048deee5fb4a1911028e6153ac513bd45a6a9eba5'},
 'menu_review': {'path': 'content/modernization/pr16_dex_hof_lifetime_menu_review.json',
                 'size': 21519,
                 'sha256': '47d5a00dce7d7ee200bd4a4fe3cf6b90a280a5514efcbfbc3c5b47bbcc2fa973'},
 'runtime_review': {'path': 'content/modernization/pr16_dex_hof_runtime_party_review.json',
                    'size': 7144,
                    'sha256': 'd879a4f2bba39ef84bbd7eb2e26071f7d78a50a41508a83ca6610879c86ced5a'}}
SOURCE_IDS.update({'party_review': {'local': 'party_review',
                  'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                  'commit': 'f90898dd122784f555d0a120f788b06ca8152c4a',
                  'path': 'content/modernization/pr16_dex_hof_callback_party_review.json',
                  'source': 'content/modernization/pr16_dex_hof_callback_party_review.json',
                  'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/f90898dd122784f555d0a120f788b06ca8152c4a/content/modernization/pr16_dex_hof_callback_party_review.json',
                  'size': 30492,
                  'sha256': '9aab39682b78ac5199357955cd634ef2ce14d0c4f0b60643dba944f5b7a31691',
                  'git_blob_sha': 'b310e8ba4cc8292087728fa451a237df1641586c'},
 'setup_review': {'local': 'setup_review',
                  'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                  'commit': 'f90898dd122784f555d0a120f788b06ca8152c4a',
                  'path': 'content/modernization/pr16_dex_hof_lifetime_setup_review.json',
                  'source': 'content/modernization/pr16_dex_hof_lifetime_setup_review.json',
                  'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/f90898dd122784f555d0a120f788b06ca8152c4a/content/modernization/pr16_dex_hof_lifetime_setup_review.json',
                  'size': 33229,
                  'sha256': '2a39c2c125df3a0b23d3bb6048deee5fb4a1911028e6153ac513bd45a6a9eba5',
                  'git_blob_sha': 'c37a93a509418999f1034ffc84ba130604a19978'},
 'menu_review': {'local': 'menu_review',
                 'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                 'commit': 'f90898dd122784f555d0a120f788b06ca8152c4a',
                 'path': 'content/modernization/pr16_dex_hof_lifetime_menu_review.json',
                 'source': 'content/modernization/pr16_dex_hof_lifetime_menu_review.json',
                 'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/f90898dd122784f555d0a120f788b06ca8152c4a/content/modernization/pr16_dex_hof_lifetime_menu_review.json',
                 'size': 21519,
                 'sha256': '47d5a00dce7d7ee200bd4a4fe3cf6b90a280a5514efcbfbc3c5b47bbcc2fa973',
                 'git_blob_sha': 'ddbbad16fcb55988cef6389e9fa1bf07ba25e627'},
 'runtime_review': {'local': 'runtime_review',
                    'repository': 'dekaazarashi1111-web/pokemon-vega-modern',
                    'commit': 'f90898dd122784f555d0a120f788b06ca8152c4a',
                    'path': 'content/modernization/pr16_dex_hof_runtime_party_review.json',
                    'source': 'content/modernization/pr16_dex_hof_runtime_party_review.json',
                    'url': 'https://github.com/dekaazarashi1111-web/pokemon-vega-modern/blob/f90898dd122784f555d0a120f788b06ca8152c4a/content/modernization/pr16_dex_hof_runtime_party_review.json',
                    'size': 7144,
                    'sha256': 'd879a4f2bba39ef84bbd7eb2e26071f7d78a50a41508a83ca6610879c86ced5a',
                    'git_blob_sha': '6e1f102112e3fc38d7cbe88bd42547e778fea870'}})

SELECTED={
 'task':tuple(task.BLOCKS),
 'setup':tuple(k for k in setup.BLOCKS if k.startswith(('constructor_','setup_')) or k in (
  'init_callback','scheduler','reset_pointers','set_main_callback','set_vblank','set_hblank',
  'null_callbacks','clear_bg_schedule','memset','reset_tasks','create_task_1','create_task_2',
  'insert_task_1','insert_task_2','insert_task_3','find_first_task')),
 'menu':('installed_tutor_predicate_hook','installed_tutor_move_hook','installed_tutor_helper',
  'installed_tutor_move_helper','installed_tutor_compatibility_hook'),
 'runtime':tuple(k for k in runtime.BLOCKS if not k.startswith(('free_','heap_init'))),
}
MODULES=dict(task=task,setup=setup,menu=menu,runtime=runtime)
BLOCKS={scope+'/'+name:tuple(MODULES[scope].BLOCKS[name]) for scope,names in SELECTED.items() for name in names}
NEW_BLOCKS={
 'special_return':tuple(party.block(0x081281A8,[('spadd',12),('pop',1,False),('bx',0)])),
 'script_special_return':tuple(party.block(0x080697EC,[('imm','mov',0,0),('pop',2,False),('bx',1)])),
 'choose_mon_return':tuple(party.block(0x08120388,[('pop',112,False),('pop',1,False),('bx',0)])),
 'selection_return':tuple(party.block(0x08120546,[('pop',112,False),('pop',1,False),('bx',0)])),
 'helper_bx_r3':tuple(party.block(0x09111C72,[('bx',3)])),
}
BLOCKS.update(NEW_BLOCKS)

def encoded(ins):
 return setup.encoded(ins) if ins.kind=='multiple' else menu.encoded(ins)

INS={}
for rows in BLOCKS.values():
 for i in rows:
  if i.address in INS:need(encoded(INS[i.address])==encoded(i),'consistent reused instruction semantics')
  INS[i.address]=i
LITERALS={}
for scope,names in SELECTED.items():
 mod=MODULES[scope]
 for name in names:
  for i in mod.BLOCKS[name]:
   if i.kind=='literal':LITERALS[i.args[1]]=mod.LITERALS[i.args[1]]
LITERALS.update({0x0816369C:0x08128155,0x08120418:0x0812047C,MOVES_CELL:MOVES})
LITERALS.update(setup.TABLE)
WINDOWS={k:(r[0].address,sum(i.size for i in r)) for k,r in BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in LITERALS})
WINDOWS['ordinary_tutor_move_fields']=(MOVES,30)
WINDOWS['minimal_instruction_window']=(HIT-1,6)
BOUNDARY={'size':6,'sha256':'946b7804e4b19dc3dd2fc3595eba750c3f14216e5d3c99c1c26eb7bfdf3b0898'}
CLAIMS=dict(proof_scope='conditional_finite_special397_same_task_tutor_continuation',
 full_story_reachability_claimed=False,runtime_execution_observed=False,
 all_heap_lifetimes_proven=False,irq_noninterference_proven=False,
 all_opaque_callee_effects_proven=False,ordinary_adapter_proof_promoted_to_entire_helper=False,
 whole_function_range_classified=False,maximum_target_access_width_proven=False,
 indirect_reference_complete=False,donor_eligible=False,bl_return_observed=False)
CONTRACT={
 'root':'actual special397 dispatch; ScriptReadHalfword returns397; normal gSpecialVar8005 is an integer0..14',
 'allocation':'well-formed heap with a fit for568 bytes; same epoch through last selected object read; selected incoming object+8..11 bytes zero is one sufficient fixture, not Alloc zero-fill',
 'setup':'actual complete23-state CFG, successful finite selected continuation, callsite return conditions and current live projection preserved; no universal termination claim',
 'task':'valid list plus one free slot at state20; actual CreateTask admission; same active row/list membership and registered func at each RunTasks dispatch; chosen empty-list example is sufficient, not necessary',
 'selection':'constructor menuType0/action12/keepCursor0; slot0 valid/non-egg; no movement required; A-confirm helper returns1',
 'tutor':'tutor0..14; installed move table produces same move in gPartyMenu+14; ordinary compatibility returns nonzero, ItemId_GetType(0)!=4, known-move predicate returns0; GiveMoveToMon returns0xffff for full four moves',
 'inputs':'fade inactive, link wait returns0, text printer returns0, replacement questionNo=1 then stop-learningYes=0',
 'callee_frame':'each explicitly recorded external call returns normally with ABI, valid nonalias stack/resources and readable/writable arguments; may change dead/disjoint memory while preserving phase-specific live projection',
 'phase_fields':'before state20: allocation epoch/pointer/object+0..11, gPartyMenu+0..11, gMain callback/state; after state20 including remaining setup: selected task func/active/list, gPartyMenu slot/action/move/method, special tutor id, main callback; rendering/text resources valid when used',
 'main_callback1':'gMain.callback1 at0x03003130 is zero initially and remains zero across every recorded external call and finite phase; actual main consumer re-reads it before callback2',
 'interruptions':'only preservation of currently live projection is required; whole-heap freeze, all IRQ exclusion and all other task immutability are not asserted',
 'stop':'stop before StringCopy at0x08126B0A; 0x08126B0E is its static return successor only',
}
ROOT=dict(kind='actual_special397_to_same_party_task',special=397,cell=0x0816369C,
 entry=0x08128154,constructor=0x0811F24C,task_admission=0x0811F5C4,
 callback=0x08120319,action=12,installed_hook=0x09097A80,tutor_entry=0x08127704,
 registered_callbacks=[0x08120319,0x081266D1,0x08126705,0x08126A85,0x08126AB9],
 hit_call=HIT-1,static_successor=HIT+3)

def exact(a,b):
 return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)

def sources_bind(sources):
 need(set(sources)==set(SOURCE_IDS)|set(PRIOR_REFS),'fixed public source and inherited review inputs')
 for name,ref in SOURCE_IDS.items():
  data=sources[name]
  need(identity(data)=={k:ref[k] for k in ('size','sha256')},'immutable source/review identity: '+name)
  need(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==ref['git_blob_sha'],'pinned public Git blob')
 text=sources['pret-party_menu.c'].decode()
 for role in ('void ChooseMonForMoveTutor(void)','Task_HandleReplaceMoveYesNoInput',
  'StopLearningMovePrompt(taskId);','Task_HandleStopLearningMoveYesNoInput',
  'StringCopy(gStringVar2, gMoveNames[gPartyMenu.learnMoveId]);'):
  need(role in text,'public semantic role: '+role)
 old=json.loads(sources['party_review'])
 need(old['task_evidence']['minimal_instruction_window']==dict(address=HIT-1,**BOUNDARY),'existing exact task boundary dependency')

def protected_windows(review):
 rows=review['windows']
 need(type(rows)is list and len(rows)==len(WINDOWS),'all finite windows required')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'address/size/SHA records only')
 need(exact([(r['label'],r['address'],r['size']) for r in rows],[(k,*v) for k,v in WINDOWS.items()]),'fixed ordered semantic window geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']) for r in rows),'lowercase SHA256')
 return [{k:r[k] for k in ('address','size','sha256')} for r in rows]

def semantic_bind(raw):
 for k,rows in BLOCKS.items():
  for i in rows:need(chunk(raw,i.address,i.size)==encoded(i),'independent semantic encoder: '+k+' '+hex(i.address))
 for a,v in LITERALS.items():need(d.u32(raw,a)==v,'exact function, global or state-table role')
 need(identity(chunk(raw,HIT-1,6))==BOUNDARY,'independent minimal6byte identity')
 setup.cfg_proof()  # 定義の全setup CFGだけ。旧effect/suiteを再実行しない。

def projection(pointer,phase,task_id=0,task_live=None):
 """生存が必要なfieldだけ。全heapや全task dataの凍結ではない。"""
 need(phase in ('constructor','setup','choose','replace_text','replace_input','stop_text','stop_input'),'named Tutor phase')
 if task_live is None:task_live=phase not in ('constructor','setup')
 need(type(task_live)is bool,'explicit admission phase flag')
 rows=[(PARTY,12,'party controls'),(0x02036FF6,2,'normal tutor id'),(0x03003130,4,'main callback1 remains zero')]
 if task_live:rows.append((TASKS+40*task_id,8,'same task callback active list priority'))
 if phase in ('constructor','setup'):
  rows += [(HEAP_CELL,4,'object pointer'),(pointer-runtime.HEADER,8,'allocation epoch header'),(pointer,12,'live object control fields'),(0x03003134,4,'callback2'),(setup.STATE,1,'setup state')]
 else:
  rows += [(PARTY+14,4,'move and learning method'),(0x03003134,4,'party scheduler'),(0x020379F3,1,'selected inactive fade guard')]
 return [dict(address=a,size=n,role=r) for a,n,r in rows]

def projection_preserved(pointer,phase,writes,task_id=0,freed=(),heap_reinitialized=False,task_live=None):
 if phase in ('constructor','setup'):need(not heap_reinitialized and pointer not in freed,'live allocation epoch cannot be restored after Free/reset')
 for a,n in writes:
  need(type(a)is int and type(n)is int and n>0 and a>=0 and a+n<=1<<32,'bounded explicit writes')
  need(all(runtime.disjoint(a,n,r['address'],r['size']) for r in projection(pointer,phase,task_id,task_live)),'intersects current live Tutor projection')
 return True

class TutorMachine(runtime.Machine):
 """Tutor追加opcodeだけ。ReadMailのphase実行関数には依存しない。"""
 def step(self,branch_choice=None):
  i=self.instructions[self.pc];k,x=i.kind,i.args
  if k=='regmem':
   op,rd,rb,ro=x;need(op=='ldrh','selected ordinary Tutor halfword read only')
   self.reg[rd]=self.read(self.reg[rb]+self.reg[ro],2);self.pc+=2;self.steps+=1;return
  if k=='subi':
   a,b=self.reg[x[1]],x[2];need(runtime.concrete(a),'concrete SBC carry producer');self.subtract_carry=a>=b
  if k=='alu_ext':
   op,rd,rs=x;need(op=='sbc' and hasattr(self,'subtract_carry'),'ordinary known-move bool conversion needs actual SUB carry')
   self.reg[rd]=(self.reg[rd]-self.reg[rs]-(not self.subtract_carry))&runtime.MASK
   self.pc+=2;self.steps+=1;return
  super().step(branch_choice)

SETUP_SUCCESS_RETURNS={0x0811F4BC:0,0x0811F4D4:1,0x0811F4FC:1,0x0811F558:1,0x0811F578:1}
EXTERNAL_TARGETS={0x080691B8,0x08040330,0x080C0918,0x080C08D8,0x080F6168,0x0813C034,
 0x081206EC,0x0803F354,0x08071A70,0x08120AD0,0x08008900,0x09FFF6D0,
 0x0809A3E8,0x0812640C,0x0803E008,0x0812643C,0x08120B60,0x081227D8,
 0x08110BF8,0x08008B48,0x08120AE8,0x080F77FC}
SETUP_CALLS={i.address:i.args[0] for scope,names in SELECTED.items() if scope=='setup'
 for name in names if name.startswith(('constructor_','setup_')) or name in ('init_callback','scheduler')
 for i in setup.BLOCKS[name] if i.kind=='call'}

def finite_case(raw,tutor_id=0,inputs=(1,0),fade=0,compatible=1,known=0,full=0xffff,
                text=0,link=0,fields_preserved=True):
 need(type(tutor_id)is int and 0<=tutor_id<=14,'ordinary normal special Tutor0..14 only')
 need(exact(inputs,(1,0)),'replaceNo then stopYes selected path')
 need(type(fade)is int and fade==0 and type(compatible)is int and compatible==1 and type(known)is int and known==0,'nonfade compatible unlearned selected conditions')
 need(type(full)is int and full==0xffff and type(text)is int and text==0 and type(link)is int and link==0,'four moves full and finite text/link success')
 need(fields_preserved is True,'explicit live projection preservation')
 mem,size=runtime.heap_fixture([(0,runtime.REQUEST+32)])
 pointer=runtime.ROOT+runtime.HEADER
 for a,n,v in [(pointer+8,4,0),(PARTY+8,4,0),(0x02036FF6,2,tutor_id),(0x03003130,4,0),(0x020379F3,1,fade)]:runtime.setmem(mem,a,n,v)
 assumptions=[];trace=[];task_id=None;phase='constructor';question=0
 def run(entry,memory,stop=0xFFFFFFF0):
  nonlocal task_id,question
  m=TutorMachine(raw,entry,memory=memory,instructions=INS)
  need(m.read(0x03003130,4)==0,'main callback1 zero at every finite phase entry')
  while m.pc!=stop:
   target=m.pc
   if target==0x08076BB4:
    need(phase=='setup' and m.calls[-1][0]==0x0811F5C4,'task admission has actual state20 caller')
    before=runtime.task_chain(m.mem)
    need(not before and any(runtime.getmem(m.mem,TASKS+40*i+4,1)==0 for i in range(16)),'selected valid empty-list plus free-slot admission')
   if target==0x0811F5C8:
    task_id=m.reg[0]
    need(type(task_id)is int and task_id==0 and runtime.task_chain(m.mem)==[0],'actual first free task admission')
    need(m.read(TASKS,4)==0x08120319 and m.read(TASKS+4,1)==1,'real task producer copied callback and active')
    trace.append(dict(role='actual_state20_task_admission',task_id=task_id,field0=m.read(TASKS,4)))
   external=(target in EXTERNAL_TARGETS or target not in INS)
   if external:
    need(bool(m.calls),'external boundary must have actual BL caller');site=m.calls[-1][0]
    need((site in SETUP_CALLS and SETUP_CALLS[site]==target) or target in EXTERNAL_TARGETS,'unlisted external callee rejected')
    ret=runtime.U;role='normal_ABI_return'
    if target==0x080691B8:ret=397;role='script_read_actual_special397'
    elif target==0x08040330:ret=1;role='valid_party_slot0_count_at_least1'
    elif target in (0x080C0918,0x080C08D8):ret=link;role='finite_link_success'
    elif target in (0x080F6168,0x0813C034):ret=0;role='main_dispatch_gate_zero'
    elif target==0x081206EC:ret=1;role='A_confirm_current_slot0'
    elif target==0x0803F354:
     need(m.reg[0]==0x020241E4 and m.reg[1]==45,'only selected slot0 egg45 boundary');ret=0;role='selected_non_egg45'
    elif target==0x09FFF6D0:
     need(m.reg[0]==0x020241E4 and m.reg[1]==tutor_id,'ordinary adapter actual selected arguments');ret=compatible;role='ordinary_compatibility_nonzero_conditional'
    elif target==0x0809A3E8:need(m.reg[0]==0,'actual item argument0');ret=0;role='ItemId_GetType0_not4'
    elif target==0x0812640C:
     need(m.reg[0]==0x020241E4 and m.reg[1]==m.read(MOVES+2*tutor_id,2),'actual known-move query args');ret=known;role='selected_move_not_known'
    elif target==0x0803E008:
     need(m.reg[0]==0x020241E4 and m.reg[1]==m.read(PARTY+14,2),'actual GiveMoveToMon tuple');ret=full;role='four_move_slots_full'
    elif target==0x08120B60:ret=text;role='selected_text_complete'
    elif target==0x08110BF8:
     need(question<2,'exactly two questions');ret=inputs[question];question+=1;role='replaceNo' if question==1 else 'stopYes'
    elif site in SETUP_SUCCESS_RETURNS:ret=SETUP_SUCCESS_RETURNS[site];role='selected_setup_success'
    assumptions.append(dict(phase=phase,callsite=site,callee=target,role=role,
     return_condition=ret if runtime.concrete(ret) else 'normal_ABI_return_only',
     protected_fields=projection(pointer,phase,task_id or 0,task_live=task_id is not None),
     task_membership_required=task_id is not None,
     actual_effect_discharged=False,normal_return_assumed=True))
    m.reg[0]=ret;m.reg[1:4]=[runtime.U]*3;m.pc=m.reg[14]&~1
   else:
    try:m.step()
    except (ValueError,KeyError) as exc:raise ValueError(phase+' '+hex(m.pc)+': '+str(exc)) from exc
   need(m.steps<30000 and len(assumptions)<300,'finite selected continuation')
  need(m.read(0x03003130,4)==0,'main callback1 zero across selected external boundaries')
  if stop==0xFFFFFFF0:need(m.reg[13]==0x03007000,'balanced phase stack')
  return m
 root=run(0x080697BC,mem)
 need(root.read(HEAP_CELL,4)==pointer and root.read(pointer,4)==0x08120319,'actual sixth stack argument stored into same allocation')
 need(root.read(PARTY+11,1)==12 and root.read(PARTY+9,1)==0,'constructor action12 and slot0 producers')
 need(root.read(0x03003134,4)==0x0811F3D9,'constructor installed actual init callback')
 phase='setup';init=run(0x08000510,root.mem)
 need(task_id==0 and init.read(TASKS,4)==0x08120319 and init.read(TASKS+4,1)==1,'state20 copies actual object callback to active selected task')
 need(init.read(0x03003134,4)==0x0811F3A9,'setup installs actual party scheduler')
 expected=ROOT['registered_callbacks'];mem=init.mem
 for index,phase in enumerate(('choose','replace_text','replace_input','stop_text','stop_input')):
  need(runtime.task_chain(mem)==[task_id],'selected task remains scheduler list member')
  need(runtime.getmem(mem,TASKS,4)==expected[index],'same task callback comes from preceding producer')
  need(runtime.getmem(mem,PARTY+9,1)==0 and runtime.getmem(mem,PARTY+11,1)==12,'selected party/action controls preserved')
  m=run(0x08000510,mem,HIT-1 if index==4 else 0xFFFFFFF0)
  trace.append(dict(phase=phase,callback=expected[index],steps=m.steps,next_callback=m.read(TASKS,4),runtasks_dispatch=0x08076D2A));mem=m.mem
 move=m.read(MOVES+2*tutor_id,2)
 need(m.reg[0]==0x02021C60 and m.reg[1]==0x090453C8+(move<<4),'actual argument producers reach complete StringCopy BL')
 need(question==2 and m.read(PARTY+14,2)==move and m.read(PARTY+16,2)==2,'same tutor move and learning method retained')
 need(all(a['callee']!=0x081C7AC8 for a in assumptions),'real registered main indirect dispatch executed')
 return dict(tutor_id=tutor_id,task_id=task_id,selected_slot=0,
  move_field=dict(address=MOVES+2*tutor_id,size=2),same_move_argument_proven=True,reached_call=HIT-1,
  static_successor=HIT+3,phases=trace,conditional_calls=assumptions,actual_stringcopy_at_hit_executed=False,
  main_and_task_registration_consumers_executed=True,ordinary_adapter_other_callees_remain_conditional=True)

def evidence_template():
 return dict(root_verified=True,root=copy.deepcopy(ROOT),claims=copy.deepcopy(CLAIMS),
  input_contract=copy.deepcopy(CONTRACT),instruction_window=dict(address=HIT-1,**BOUNDARY),
  instructions=[dict(address=HIT-1,size=4,role='complete_thumb_StringCopy_BL',target=0x08008900),
   dict(address=HIT+3,size=2,role='complete_static_return_successor_LDR',literal=0x08126B44)],
  literal_pool_included=False,successor_type='static BL return successor',type_classification_only=True,finite_tutor_ids=list(range(15)))

def witness_geometry(evidence):
 need(exact(evidence,evidence_template()),'exact rooted6byte BL plus static successor geometry')
 a,n=HIT-1,6;need(a<=HIT and HIT+4<=a+n,'all four legacy hit bytes covered');return a,n

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','inherited_reviews','root','claims','input_contract','windows','hit'},'closed review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'schema version')
 need(exact(review['required_candidate'],CANDIDATE) and exact(inherited['candidate'],CANDIDATE),'fixed current candidate scope')
 need(exact(review['diagnostic_input'],DIAGNOSTIC),'old diagnostic distinct from current')
 for key,value in [('source_bindings',SOURCE_IDS),('inherited_reviews',PRIOR_REFS),('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT)]:need(exact(review[key],value),'fixed conditional contract '+key)
 original=[h for h in inherited['hits'] if h['address']==HIT]
 need(len(original)==1 and exact(original[0],review['hit']),'one exact unchanged inherited hit')
 h=original[0];need(h['accepted'] is False and h['owner_candidates']==[] and type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','only original external unknown')
 sources_bind(sources);d.signed(raw,h);d.signed(raw,protected_windows(review));semantic_bind(raw)
 cases=[finite_case(raw,tutor_id=i) for i in range(15)];evidence=evidence_template();a,n=witness_geometry(evidence)
 return [d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_SPECIAL397_TUTOR_TYPE',
  count=1,hit=HIT,tutor_cases=15,cases=cases,protected_windows=len(WINDOWS),
  protected_bytes=sum(n for a,n in WINDOWS.values()),inherited_reviews=PRIOR_REFS,**CLAIMS)

def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current identity mandatory; diagnostic cannot become current')
 return _regions(raw,inherited,review,sources)

def make_review(raw,hit):
 """明示的な記録生成。check APIはこの関数を呼ばず記録を更新しない。"""
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),inherited_reviews=copy.deepcopy(PRIOR_REFS),root=copy.deepcopy(ROOT),
  claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),
  windows=[dict(label=k,address=a,**identity(chunk(raw,a,n))) for k,(a,n) in WINDOWS.items()],hit=copy.deepcopy(hit))
