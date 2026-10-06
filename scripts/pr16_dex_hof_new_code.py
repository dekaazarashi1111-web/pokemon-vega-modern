"""RFU実constructor登録からの条件付き最小Thumb型。通信の自然到達は主張しない。"""
import copy
import hashlib
import json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_runtime_party as runtime
need, identity, chunk = d.need, d.identity, d.chunk
CANDIDATE, DIAGNOSTIC = party.CANDIDATE, party.DIAGNOSTIC
HIT = 0x080FC36B
HITS = (HIT,)
KIND = 'rooted_rfu_parent_disconnect_minimum_thumb'
RFU, LMAN, RECEIVED, LINKCELL = 0x030054A0, 0x03005E60, 0x03003FA4, 0x030074C0
LINK_STATUS = 0x0203F000
ENTRY, MANAGER, STOP = 0x080FCBE8, 0x080FE9FC, 0x080FC384
BLOCKS = {}
def put(name, address, specs):
    BLOCKS[name] = tuple(party.block(address, specs))

SOURCE_IDS = {'pret-src-AgbRfu_LinkManager.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                                   'git_blob_sha': '35317ab86d99fb21fe0a68dd25c89ffa8b4f3b4a',
                                   'local': 'pret-src-AgbRfu_LinkManager.c',
                                   'path': 'src/AgbRfu_LinkManager.c',
                                   'repository': 'pret/pokefirered',
                                   'sha256': '96b15b35068f7cbc84ba491988d5204af84e56315b8b71a21d6b6ef39976dc9b',
                                   'size': 48777},
 'pret-src-link_rfu_2.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                           'git_blob_sha': '78087d76fd3b2869b2bedc5b6dc29840e7d7a55a',
                           'local': 'pret-src-link_rfu_2.c',
                           'path': 'src/link_rfu_2.c',
                           'repository': 'pret/pokefirered',
                           'sha256': 'a81f75e46ea0114f15317f9b8714352a3ccc4aee8722403e3f2ad184e3719743',
                           'size': 91134}}

put('leader_constructor',0x080FCBE8,[('push', 112, True),
 ('addi', 4, 0, 0),
 ('literal', 1, 135253024),
 ('imm', 'mov', 0, 1),
 ('mem', False, 'byte', 0, 1, 12),
 ('call', 135249784),
 ('literal', 0, 135253028),
 ('imm', 'mov', 1, 0),
 ('call', 135259132),
 ('literal', 2, 135253032),
 ('addi', 1, 2, 0),
 ('literal', 0, 135253036),
 ('multiple', True, 0, 104),
 ('multiple', False, 1, 104),
 ('multiple', True, 0, 104),
 ('multiple', False, 1, 104),
 ('literal', 0, 135253040),
 ('imm', 'sub', 4, 1),
 ('add', 4, 4, 0),
 ('mem', True, 'byte', 0, 4, 0),
 ('mem', False, 'half', 0, 2, 2),
 ('call', 135241440),
 ('pop', 112, False),
 ('pop', 1, False),
 ('bx', 0)])

put('lman_initializer',0x080FE3FC,[('push', 112, True),
 ('spadd', -4),
 ('addi', 5, 0, 0),
 ('addi', 6, 1, 0),
 ('imm', 'cmp', 5, 0),
 ('branch', 0, 135259204),
 ('movhi', 1, 13),
 ('imm', 'mov', 0, 0),
 ('mem', False, 'half', 0, 1, 0),
 ('literal', 4, 135259188),
 ('literal', 2, 135259192),
 ('movhi', 0, 13),
 ('addi', 1, 4, 0),
 ('call', 136084104),
 ('imm', 'mov', 0, 255),
 ('mem', False, 'byte', 0, 4, 6),
 ('mem', False, 'word', 5, 4, 64),
 ('mem', False, 'word', 6, 4, 68),
 ('literal', 0, 135259196),
 ('call', 136071120),
 ('literal', 0, 135259200),
 ('call', 136071132),
 ('imm', 'mov', 0, 0),
 ('jump', 135259206)])

put('lman_initializer_return',0x080FE446,[('spadd', 4), ('pop', 112, False), ('pop', 2, False), ('bx', 1)])

put('manager_entry',0x080FE9FC,[('push', 16, True),
 ('addi', 3, 0, 0),
 ('literal', 1, 135260692),
 ('mem', True, 'word', 2, 1, 64),
 ('imm', 'cmp', 2, 0),
 ('branch', 1, 135260696),
 ('mem', True, 'byte', 0, 1, 4),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135260696),
 ('mem', False, 'byte', 2, 1, 4),
 ('jump', 135261158)])

put('manager_ready',0x080FEA18,[('literal', 0, 135260748),
 ('mem', True, 'byte', 0, 0, 7),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135260710),
 ('addi', 0, 3, 0),
 ('call', 135261172),
 ('literal', 4, 135260748),
 ('mem', True, 'byte', 0, 4, 4),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135260720),
 ('jump', 135261104)])

put('manager_parent_watch',0x080FEBB0,[('literal', 0, 135261164),
 ('mem', True, 'byte', 0, 0, 4),
 ('imm', 'sub', 0, 18),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('imm', 'cmp', 0, 1),
 ('branch', 8, 135261120),
 ('jump', 135260710),
 ('literal', 0, 135261168),
 ('mem', True, 'word', 0, 0, 0),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135261142),
 ('imm', 'mov', 0, 0),
 ('call', 135260188)])

put('watcher_input_and_writers',0x080FE81C,[('push', 240, True),
 ('movhi', 7, 9),
 ('movhi', 6, 8),
 ('push', 192, False),
 ('spadd', -4),
 ('shift', 'lsl', 0, 0, 16),
 ('shift', 'lsr', 0, 0, 16),
 ('imm', 'mov', 1, 0),
 ('movhi', 8, 1),
 ('movhi', 5, 13),
 ('imm', 'add', 5, 1),
 ('movhi', 4, 13),
 ('imm', 'add', 4, 2),
 ('movhi', 1, 13),
 ('addi', 2, 5, 0),
 ('addi', 3, 4, 0),
 ('call', 136074068),
 ('movhi', 0, 13),
 ('mem', True, 'byte', 0, 0, 0),
 ('addi', 7, 4, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135260398),
 ('literal', 1, 135260344),
 ('movhi', 0, 13),
 ('mem', True, 'byte', 0, 0, 0),
 ('mem', False, 'half', 0, 1, 20),
 ('mem', True, 'byte', 0, 5, 0),
 ('mem', False, 'half', 0, 1, 22),
 ('mem', True, 'byte', 0, 1, 9),
 ('addi', 6, 1, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 0, 135260374)])

put('watcher_no_recovery',0x080FE8D6,[('movhi', 0, 13),
 ('mem', True, 'byte', 0, 0, 0),
 ('call', 135264228),
 ('imm', 'mov', 1, 1),
 ('movhi', 8, 1),
 ('imm', 'mov', 0, 48),
 ('imm', 'mov', 1, 2),
 ('call', 135264188)])

put('disconnect_wrapper',0x080FF7E4,[('push', 48, True),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('literal', 4, 135264260),
 ('mem', True, 'byte', 5, 4, 14),
 ('imm', 'mov', 1, 1),
 ('mem', False, 'byte', 1, 4, 14),
 ('call', 136075148),
 ('call', 136071380),
 ('mem', False, 'byte', 5, 4, 14),
 ('pop', 48, False),
 ('pop', 1, False),
 ('bx', 0)])

put('callback_dispatch',0x080FF7BC,[('push', 16, True),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 0, 0, 24),
 ('shift', 'lsl', 1, 1, 24),
 ('shift', 'lsr', 1, 1, 24),
 ('literal', 4, 135264224),
 ('mem', True, 'word', 2, 4, 64),
 ('imm', 'cmp', 2, 0),
 ('branch', 0, 135264210),
 ('call', 136084176),
 ('imm', 'mov', 0, 0),
 ('mem', False, 'half', 0, 4, 22),
 ('mem', False, 'half', 0, 4, 20),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0)])

put('dispatch_interwork',0x081C7AD0,[('bx', 2)])

put('parent_message_switch',0x080FC1E0,[('push', 240, True),
 ('movhi', 7, 10),
 ('movhi', 6, 9),
 ('movhi', 5, 8),
 ('push', 224, False),
 ('shift', 'lsl', 0, 0, 24),
 ('shift', 'lsr', 4, 0, 24),
 ('imm', 'mov', 6, 0),
 ('imm', 'cmp', 4, 50),
 ('branch', 1, 135250422),
 ('jump', 135250740),
 ('imm', 'cmp', 4, 50),
 ('branch', 12, 135250470),
 ('imm', 'cmp', 4, 19),
 ('branch', 12, 135250452)])

put('parent_message_48',0x080FC214,[('imm', 'cmp', 4, 48), ('branch', 1, 135250458), ('jump', 135250752)])

put('parent_disconnect_hit',0x080FC340,[('literal', 1, 135250800),
 ('addi', 2, 1, 0),
 ('imm', 'add', 2, 240),
 ('imm', 'mov', 0, 4),
 ('mem', False, 'byte', 0, 2, 0),
 ('literal', 3, 135250804),
 ('add', 1, 1, 3),
 ('literal', 0, 135250808),
 ('mem', True, 'byte', 2, 0, 20),
 ('mem', True, 'byte', 0, 1, 0),
 ('addi', 3, 0, 0),
 ('alu_ext', 'bic', 3, 2),
 ('addi', 2, 3, 0),
 ('mem', False, 'byte', 2, 1, 0),
 ('literal', 0, 135250812),
 ('mem', True, 'byte', 0, 0, 0),
 ('imm', 'cmp', 0, 1),
 ('branch', 1, 135250820),
 ('imm', 'cmp', 2, 0),
 ('branch', 1, 135250816),
 ('addi', 0, 4, 0),
 ('call', 135250244),
 ('jump', 135250820)])

put('error_parameter_writer',0x080FC144,[('push', 16, True),
 ('addi', 4, 0, 0),
 ('literal', 2, 135250284),
 ('addi', 3, 2, 0),
 ('imm', 'add', 3, 238),
 ('mem', True, 'byte', 0, 3, 0),
 ('imm', 'cmp', 0, 0),
 ('branch', 1, 135250278),
 ('literal', 1, 135250288),
 ('mem', True, 'half', 0, 1, 20),
 ('mem', False, 'half', 0, 2, 16),
 ('mem', True, 'half', 0, 1, 22),
 ('mem', False, 'half', 0, 2, 18),
 ('mem', False, 'half', 4, 2, 10),
 ('mem', True, 'byte', 0, 3, 0),
 ('imm', 'mov', 0, 1),
 ('mem', False, 'byte', 0, 3, 0),
 ('pop', 16, False),
 ('pop', 1, False),
 ('bx', 0)])

LITERALS = {135250284: 50353312,
 135250288: 50355808,
 135250800: 50353312,
 135250804: 2458,
 135250808: 50355808,
 135250812: 50347940,
 135253024: 50353312,
 135253028: 135250401,
 135253032: 33794920,
 135253036: 138422360,
 135253040: 138422384,
 135259188: 50355808,
 135259192: 16777252,
 135259196: 135263073,
 135259200: 135261285,
 135260344: 50355808,
 135260692: 50355808,
 135260748: 50355808,
 135261164: 50355808,
 135261168: 50361536,
 135264224: 50355808,
 135264260: 50355808}

BOUNDARY = {'address': 135250794, 'size': 6, 'sha256': '53b73cfccd787f387f20b448de12962721e0696902e38f779245a6f55df1d6b7'}
TYPE_CATEGORY = 'code'
INS = {i.address:i for rows in BLOCKS.values() for i in rows}
WINDOWS = {name:(rows[0].address,sum(i.size for i in rows)) for name,rows in BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4) for a in sorted(LITERALS)})
DATA = {'configuration_template':(0x08402858,24),'group_two_available_slots':(0x08402871,1)}
WINDOWS.update(DATA)
ROOT = dict(constructor=ENTRY,group_max=2,registered_callback=0x080FC1E1,registration_store=0x080FE41E,registration_cell=LMAN+0x40,later_conditional_manager_entry=MANAGER,manager_state=0,watcher=0x080FE81C,hardware_watch_call=0x080FE83C,parameter_stores=[0x080FE850,0x080FE854],message=48,parameter_count=2,occurrence_dispatch=0x080FF7BC,callback_load=0x080FF7C8,interwork=0x081C7AD0,hit=HIT,error_writer=0x080FC144,stop=STOP)
CLAIMS = dict(proof_scope='conditional_initialized_rfu_manager_finite_registered_consumer',full_story_reachability_claimed=False,natural_wireless_lifecycle_proven=False,actual_runtime_execution_observed=False,universal_irq_lifetime_proven=False,opaque_callee_effects_proven=False,source_pointer_interpretation=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False,complete_manager_execution_claimed=False)
CONTRACT = dict(
 root='Actual LinkLeader constructor groupMax2 executes and returns before a separate conditional manager call. Game scheduling and a natural live wireless session are not proved.',
 state='Explicit initial external inputs: parentSlots1, receivedPlayers1, errorState0, bounded link-status object parentChild1. CpuFill16 zeros lman and actual constructor stores callback and MODE_PARENT. No task state is invented to dispatch the hit.',
 event='Actual manager reads constructor-produced state0 and fastSearch0, reads conditional parent status, and calls watcher(0). watchLink conditionally writes lossMask1/reason0/recoveredMask0 to actual stack outputs. Actual watcher stores both lman.params and emits msg48/count2.',
 boundaries='Eight opaque sites require normal Thumb ABI return, r4-r11/SP preservation and concrete future-read-before-write RAM projection. CPU fill and watchLink have explicit finite output contracts. All other RAM is erased at each boundary in a second complete composition.',
 lifetime='Same static lman registry generation from constructor through dispatch: no reinitialization or callback replacement. No universal IRQ or wireless-session lifetime claim.',
 consumer='Actual switch and AND-NOT path reach complete BL; actual RfuSetErrorParams writes parameters and message, returns, and actual successor branch executes. Stop before the subsequent status call.',
 geometry='Only complete BL and next Thumb branch, six bytes, are newly typed; no wider function, literal, configuration or table is classified.')
OPAQUE = {0x080FCBF2:(0x080FBF78,'set_host_username'),0x080FE416:(0x081C7A88,'cpu_fill_lman'),0x080FE424:(0x081C47D0,'install_msc_callback'),0x080FE42A:(0x081C47DC,'install_req_callback'),0x080FCC16:(0x080F9EE0,'create_parent_search_task'),0x080FE83C:(0x081C5354,'hardware_watch_link'),0x080FF7F2:(0x081C578C,'hardware_disconnect'),0x080FF7F6:(0x081C48D4,'hardware_wait_complete')}
def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(WINDOWS),'closed RFU windows')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'} for r in rows),'address-size-SHA-only windows')
 need(exact([(r['label'],r['address'],r['size'])for r in rows],[(k,*v)for k,v in WINDOWS.items()]),'exact ordered window geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef'for c in r['sha256'])for r in rows),'complete SHA256 format')
 return [{k:r[k]for k in('address','size','sha256')}for r in rows]
def encoded(ins):
 if ins.kind=='multiple':
  load,reg,mask=ins.args;return (0xC000|(int(load)<<11)|(reg<<8)|mask).to_bytes(2,'little')
 return menu.encoded(ins)
def bind_semantics(raw):
 for name,rows in BLOCKS.items():
  for i in rows:need(chunk(raw,i.address,i.size)==encoded(i),'RFU instruction '+name+' '+hex(i.address))
 for a,v in LITERALS.items():need(d.u32(raw,a)==v,'RFU literal '+hex(a))
 need(identity(chunk(raw,HIT-1,6))=={k:BOUNDARY[k]for k in('size','sha256')},'complete BL plus branch')
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'exact fixed public sources')
 for key,row in SOURCE_IDS.items():
  b=sources[key];need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'fixed source identity '+key)
 source=sources['pret-src-link_rfu_2.c'].decode()
 for t in('InitializeRfuLinkManager_LinkLeader(u32 groupMax)','rfu_LMAN_initializeManager(LinkManagerCB_Parent, NULL);','gRfu.parentSlots &= ~lman.param[0];','if (gReceivedRemoteLinkPlayers == 1)','if (gRfu.parentSlots == 0)','RfuSetErrorParams(msg);'):need(t in source,'public RFU semantic role')
 source=sources['pret-src-AgbRfu_LinkManager.c'].decode()
 for t in('lman.LMAN_callback = LMAN_callback_p;','if (rfu_LMAN_linkWatcher(0))','lman.param[0] = bm_linkLossSlot;','lman.param[1] = reason;','rfu_LMAN_occureCallback(LMAN_MSG_LINK_LOSS_DETECTED_AND_DISCONNECTED, 2);','lman.LMAN_callback(msg, param_count);'):need(t in source,'SDK writer and registered dispatch')
class Machine(runtime.Machine):
 def __init__(self,raw):
  super().__init__(raw,ENTRY,{0:2},instructions=INS);self.trace=[]
 def read(self,a,n):
  v=super().read(a,n)
  if type(a)is int and not 0x08000000<=a<0x0A000000:self.trace.append(('read',self.pc,a,n,runtime.concrete(v)))
  return v
 def write(self,a,n,v):
  super().write(a,n,v);self.trace.append(('write',self.pc,a,n))
 def step(self,branch_choice=None):
  need(branch_choice is None,'RFU branches use actual compared values');i=self.instructions.get(self.pc)
  if i is not None and i.kind=='alu_ext':
   op,rd,rs=i.args;need(op=='bic'and runtime.concrete(self.reg[rd])and runtime.concrete(self.reg[rs]),'concrete AND-NOT slots')
   self.reg[rd]=self.reg[rd]&~self.reg[rs]&runtime.MASK;self.pc+=2;self.steps+=1;self.flag_pc=None;return
  if i is not None and i.kind=='multiple'and i.args[0]:
   _,rb,mask=i.args;need(not mask&(1<<rb),'no configuration base alias')
   for rd in range(8):
    if mask&(1<<rd):self.reg[rd]=self.read(self.reg[rb],4);self.reg[rb]+=4
   self.pc+=2;self.steps+=1;self.flag_pc=None;return
  super().step()
def inputs_template():return dict(group_max=2,parent_slots=1,received_players=1,error_state=0,link_status_address=LINK_STATUS,hardware_parent_mode=1,loss_mask=1,reason=0,recovered_mask=0,manager_call_admitted=True)
def _seed(m,inputs):
 need(exact(inputs,inputs_template()),'exact explicitly conditional external inputs')
 for a,n,v in((RFU+0x99A,1,1),(RECEIVED,1,1),(RFU+0xEE,1,0),(LINKCELL,4,LINK_STATUS),(LINK_STATUS,1,1)):runtime.setmem(m.mem,a,n,v)
def _read_projection(trace,ordinal):
 marker=next(i for i,r in enumerate(trace)if r==('boundary',ordinal));seen=set();needed={}
 for r in trace[marker+1:]:
  if r[0]not in('read','write'):continue
  kind,pc,a,n=r[:4]
  for address in range(a,a+n):
   if address not in seen and kind=='read'and r[4]:needed[address]=pc
   seen.add(address)
 fields=[]
 for a,pc in sorted(needed.items()):
  role='active ABI saved stack'if 0x03006000<=a<0x03007000 else 'future read at 0x%08X'%pc
  if fields and fields[-1]['address']+fields[-1]['size']==a and fields[-1]['role']==role:fields[-1]['size']+=1
  else:fields.append(dict(address=a,size=1,role=role))
 return fields
def preservation_contract(fields,writes,registry_reinitialized=False,callback_replaced=False):
 need(registry_reinitialized is False and callback_replaced is False,'same registration epoch')
 need(type(fields)is list and all(type(f)is dict and set(f)=={'address','size','role'}and type(f['address'])is int and type(f['size'])is int and f['size']>0 and type(f['role'])is str for f in fields),'concrete future-live projection')
 for a,n in writes:
  need(type(a)is int and type(n)is int and n>0 and 0<=a<a+n<=1<<32,'bounded declared write')
  need(all(runtime.disjoint(a,n,f['address'],f['size'])for f in fields),'declared write intersects future-live field')
 return True
def _opaque(m,site,ordinal,projections,boundary_effects=None):
 target,role=OPAQUE[site];need(m.pc==target and m.reg[14]==((site+4)|1),'exact opaque target and real return')
 args=tuple(m.reg[:4]);outputs=[]
 if role=='cpu_fill_lman':
  need(args[:3]==(m.reg[13],LMAN,0x01000024),'actual CpuFill16 arguments');need(m.read(args[0],2)==0,'stack zero source')
  outputs=[(LMAN+j,2,0)for j in range(0,72,2)]
 elif role=='install_msc_callback':need(args[0]==0x080FF361,'actual MSC callback')
 elif role=='install_req_callback':need(args[0]==0x080FEC65,'actual REQ callback')
 elif role=='hardware_watch_link':
  need(args==(0,m.reg[13],m.reg[13]+1,m.reg[13]+2),'actual watcher output destinations')
  outputs=[(args[1],1,1),(args[2],1,0),(args[3],1,0)]
 elif role=='hardware_disconnect':need(args[0]==1,'same actual loss mask to disconnect')
 m.trace.append(('boundary',ordinal));fields=None if projections is None else projections[ordinal]
 if fields is not None:
  effect={'writes':[],'registry_reinitialized':False,'callback_replaced':False,'normal_abi_return':True} if boundary_effects is None else boundary_effects.get(site,{'writes':[],'registry_reinitialized':False,'callback_replaced':False,'normal_abi_return':True})
  need(type(effect)is dict and set(effect)=={'writes','registry_reinitialized','callback_replaced','normal_abi_return'}and effect['normal_abi_return']is True,'closed explicit normal ABI boundary effect')
  need(type(effect['writes'])is list and all(type(w)is tuple and len(w)==3 and type(w[2])is int and w[1]in(1,2,4)and 0<=w[2]<(1<<(8*w[1]))for w in effect['writes']),'concrete bounded boundary write values')
  preservation_contract(fields,[(a,n)for a,n,_ in effect['writes']],registry_reinitialized=effect['registry_reinitialized'],callback_replaced=effect['callback_replaced'])
  for a,n,value in effect['writes']:m.write(a,n,value)
  m.mem={a:v for a,v in m.mem.items()if any(f['address']<=a<f['address']+f['size']for f in fields)}
 for a,n,v in outputs:m.write(a,n,v)
 for r in(0,1,2,3,12):m.reg[r]=runtime.U
 m.flag_pc=None;m.pc=m.reg[14]&~1
 return dict(site=site,target=target,role=role,normal_abi_return_required=True,effects_discharged=False,preserved_registers=[4,5,6,7,8,9,10,11,13],required_fields=[]if fields is None else copy.deepcopy(fields),conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs])
def _compose(raw,inputs,projections=None,mutate_registered=None,boundary_effects=None):
 m=Machine(raw);_seed(m,inputs);calls=[];events=[];transitioned=False;ordinal=0;hit_visited=False;copied=False
 while m.pc!=STOP:
  if m.pc==0xFFFFFFF0:
   need(not transitioned and m.reg[13]==0x03007000,'actual constructor complete with balanced stack')
   need(m.read(LMAN+0x40,4)==0x080FC1E1 and m.read(LMAN+4,1)==0 and m.read(LMAN+7,1)==0 and m.read(LMAN+9,1)==0,'constructor-produced callback/ready/recovery')
   events.append(dict(role='constructor_returned_registered_callback',cell=LMAN+0x40,value=0x080FC1E1))
   if mutate_registered is not None:mutate_registered(m)
   need(m.read(LMAN+0x40,4)==0x080FC1E1,'same constructor registration at manager admission')
   m.pc=MANAGER;m.reg=[runtime.U]*16;m.reg[0]=0;m.reg[13]=0x03007000;m.reg[14]=0xFFFFFFF1;transitioned=True;continue
  site=(m.reg[14]&~1)-4 if runtime.concrete(m.reg[14])else None
  if site in OPAQUE and m.pc==OPAQUE[site][0]:calls.append(_opaque(m,site,ordinal,projections,boundary_effects));ordinal+=1;continue
  need(m.pc in INS,'conditional RFU route escaped at '+hex(m.pc))
  if m.pc==0x080FF7CE:
   need(m.reg[2]==0x080FC1E1 and tuple(m.reg[:2])==(48,2),'actual callback and source-emitted message')
   need(m.read(LMAN+20,2)==1 and m.read(LMAN+22,2)==0,'actual parameter stores')
   events.append(dict(role='registered_callback_loaded',callsite=m.pc,target=m.reg[2],message=m.reg[0],parameter_count=m.reg[1]))
  if m.pc==HIT-1:
   need(transitioned and m.reg[0]==48 and m.read(RFU+0x99A,1)==0,'AND-NOT result and message reach complete BL');hit_visited=True
  if m.pc==HIT+3:
   need(hit_visited and m.read(RFU+16,2)==1 and m.read(RFU+18,2)==0 and m.read(RFU+10,2)==48 and m.read(RFU+0xEE,1)==1,'actual error writer returned to successor');copied=True
  m.step()
 need(hit_visited and copied and ordinal==len(OPAQUE),'whole rooted composition and eight boundaries')
 return m,dict(status='PASS_CONDITIONAL_RFU_INITIALIZER_TO_REGISTERED_DISCONNECT',constructor_returned=True,conditional_later_manager_call=True,actual_callback_load_and_interwork=True,actual_parameter_writes=True,complete_bl_and_successor_executed=True,stop=STOP,conditional_calls=calls,events=events,synthetic_contract_execution=True,actual_runtime_execution_observed=False,nonlive_ram_erased_at_each_boundary=projections is not None)
def compose_selected(raw,inputs=None,boundary_effects=None):
 need(boundary_effects is None or type(boundary_effects)is dict and all(type(k)is int and k in OPAQUE for k in boundary_effects),'closed boundary effect sites')
 bind_semantics(raw);chosen=inputs_template()if inputs is None else inputs;first,_=_compose(raw,chosen)
 projections=[_read_projection(first.trace,i)for i in range(len(OPAQUE))];second,proof=_compose(raw,chosen,projections,boundary_effects=boundary_effects)
 if boundary_effects is None:need([r[:4]for r in first.trace if r[0]in('read','write')]==[r[:4]for r in second.trace if r[0]in('read','write')],'nonlive havoc preserves complete memory-access route')
 rejected=0
 for fields in projections:
  for f in fields:
   try:preservation_contract(fields,[(f['address'],1)])
   except ValueError:rejected+=1
   else:raise ValueError('live overwrite admitted')
  need(preservation_contract(fields,[(0x02010000,4)]),'unrelated RAM writable')
 proof['projection_counterexamples']=dict(live_field_write_rejections=rejected,boundary_count=len(OPAQUE),unrelated_ram_writes_allowed=True,all_other_ram_erased=True,actual_external_effects_proven=False)
 return proof
def evidence_template():return dict(schema_version=1,root_verified=True,root=copy.deepcopy(ROOT),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),instruction_window=copy.deepcopy(BOUNDARY),instructions=[dict(address=HIT-1,size=4,role='complete_thumb_bl',callee=0x080FC144),dict(address=HIT+3,size=2,role='static_thumb_branch_return_successor',target=STOP)],same_registered_callback=True,literal_pool_included=False,type_classification_only=True)
def witness_geometry(e):
 need(exact(e,evidence_template()),'exact rooted RFU minimum evidence');need(BOUNDARY['address']<=HIT and HIT+4<=BOUNDARY['address']+6,'hit covered by complete instructions');return HIT-1,6
def make_review(raw,hit):return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hit=copy.deepcopy(hit),root=copy.deepcopy(ROOT),windows=[dict(label=k,address=a,**identity(chunk(raw,a,n)))for k,(a,n)in WINDOWS.items()],claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT))
def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract'},'closed review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'exact review version')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'separate current/diagnostic identities')
 need(exact(review['root'],ROOT)and exact(review['claims'],CLAIMS)and exact(review['input_contract'],CONTRACT),'closed conditional claims')
 rows=[h for h in inherited['hits']if h['address']==HIT]
 need(len(rows)==1 and exact(rows[0],review['hit'])and rows[0]['accepted']is False and rows[0]['owner_candidates']==[],'one unchanged owner-external unknown')
 need(type(rows[0]['size'])is int and rows[0]['size']==4 and rows[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','four-byte inventory hit')
 d.signed(raw,rows[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));bind_semantics(raw)
 proof=compose_selected(raw);e=evidence_template();a,n=witness_geometry(e)
 return [d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_ONE_CONDITIONAL_RFU_MINIMUM_TYPE',count=1,hit=HIT,protected_windows=len(WINDOWS),protected_bytes=sum(n for a,n in WINDOWS.values()),composition=proof,source_bindings=copy.deepcopy(SOURCE_IDS),**CLAIMS)
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current gate; diagnostic cannot classify current');return _regions(raw,inherited,review,sources)
