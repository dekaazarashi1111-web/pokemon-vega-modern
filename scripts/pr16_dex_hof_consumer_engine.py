"""残未知1件を実special/保存taskId/有限switch/hook consumerで検証。"""
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_remaining_engine as old
import pr16_dex_hof_script_engine as previous
need,identity,chunk=d.need,d.identity,d.chunk
half,literal=old.half,old.literal
CANDIDATE=gaps.CANDIDATE
HITS=(0x0808D7FF,)
NEW_WINDOWS={'storage_constructor_prefix':(0x0808C820,28),'storage_constructor_body':(0x0808C854,56),'storage_task_setter':(0x0808CA34,30),'storage_scheduler_callback':(0x0808C800,30)}
SOURCE_LOCAL='pret-pokemon_storage_system_tasks.c'
SOURCE_IDENTITY={'size':77841,'sha256':'ac9e5037b244339c48a930cecbeb07a4cea20086c9347bdf9536164be8d74188'}


def storage_consumers(raw,review):
 """constructor戻り値のbyte保存と同一field読出・task40stride・func保存を全命令拘束。"""
 s=previous.ThumbConsumer(raw)
 # The caller keeps the global-pointer address in callee-preserved r4.
 s.stack(0x0808C820,False,0x30,True);s.shift(0x0808C822,False,0,0,24);s.shift(0x0808C824,True,5,0,24)
 s.call(0x0808C826,0x08076B54);s.pointer(0x0808C82A,0,0x0808C844);s.mem(0x0808C82C,False,True,5,0,0)
 s.pointer(0x0808C82E,4,0x0808C848);s.pointer(0x0808C830,0,0x0808C84C);s.call(0x0808C832,0x08002B9C)
 s.mem(0x0808C836,False,False,0,4,0);s.imm(0x0808C838,'cmp',0,0);s.branch(0x0808C83A,1,0x0808C854)
 # Successful constructor: callback argument and priority, task ID r0 -> [gStorage]+4 without an intervening call.
 s.imm(0x0808C854,'mov',2,0);s.mem(0x0808C856,False,True,5,0,1);s.mem(0x0808C858,True,False,0,4,0);s.mem(0x0808C85A,False,True,2,0,3)
 s.pointer(0x0808C85C,0,0x0808C88C);s.imm(0x0808C85E,'mov',1,0);s.opcode(0x0808C860,0x8000|(0<<6)|(0<<3)|2,'STRH r2,[r0] unrelated item field')
 s.mem(0x0808C862,True,False,0,4,0);s.mem(0x0808C864,False,True,1,0,0)
 s.pointer(0x0808C866,0,0x0808C890);s.imm(0x0808C868,'mov',1,3);s.call(0x0808C86A,0x08076BB4)
 s.mem(0x0808C86E,True,False,1,4,0);s.mem(0x0808C870,False,True,0,1,4)
 s.imm(0x0808C872,'mov',0,28);s.call(0x0808C874,0x0812B9F4);s.call(0x0808C878,0x0808B490)
 s.pointer(0x0808C87C,1,0x0808C894);s.mem(0x0808C87E,False,True,0,1,0)
 s.pointer(0x0808C880,0,0x0808C898);s.call(0x0808C882,0x08000544);s.stack(0x0808C886,True,0x30);s.stack(0x0808C888,True,1);s.bx(0x0808C88A,0)
 # New main callback starts with RunTasks. Exact full body has ordinary calls and return.
 s.stack(0x0808C800,False,0,True)
 for a,t in [(0x0808C802,0x08076D10),(0x0808C806,0x080F7810),(0x0808C80A,0x0808EA04),(0x0808C80E,0x0808F3D8),(0x0808C812,0x080066D8),(0x0808C816,0x08006724)]:s.call(a,t)
 s.stack(0x0808C81A,True,1);s.bx(0x0808C81C,0)
 # Setter preserves argument r0 while loading the saved byte ID, then stores to exact task.func.
 s.stack(0x0808CA34,False,16,True);s.pointer(0x0808CA36,4,0x0808CA54);s.pointer(0x0808CA38,1,0x0808CA58)
 s.mem(0x0808CA3A,True,False,3,1,0);s.mem(0x0808CA3C,True,True,2,3,4)
 s.shift(0x0808CA3E,False,1,2,2);s.add(0x0808CA40,1,1,2);s.shift(0x0808CA42,False,1,1,3);s.add(0x0808CA44,1,1,4)
 s.mem(0x0808CA46,False,False,0,1,0);s.imm(0x0808CA48,'mov',0,0);s.mem(0x0808CA4A,False,True,0,3,0)
 s.stack(0x0808CA4C,True,16);s.stack(0x0808CA4E,True,1);s.bx(0x0808CA50,0)
 lit={r['label']:r for r in review['consumer_literals']}
 expected={'storage_constructor_gStorage':(0x0808C848,0x020396FC),'storage_constructor_task_target':(0x0808C890,0x0808CA5D),'storage_constructor_main_target':(0x0808C898,0x0808C801),'storage_setter_gTasks':(0x0808CA54,0x030050D0),'storage_setter_gStorage':(0x0808CA58,0x020396FC)}
 for label,(a,v)in expected.items():
  w=lit[label];need(w['address']==a and w['value']==d.u32(raw,a)==v,'same storage/table field provenance literal')


def indirect(raw,edge,rows,edges):
 addresses=[p['address']for p in rows]
 if edge['kind']=='callback_edge'and edge['callee']==0x0808CA34:
  need(edge['from']==edge['call']and edge['load']+2==edge['call']and edge['load']in addresses and edge['to']in addresses,'immediate storage callback registration')
  need(code.thumb_bl(chunk(raw,edge['call'],4),edge['call'])==0x0808CA34 and literal(raw,edge['load'],0)==edge['literal'],'same r0 pointer reaches storage setter')
  w=edge['literal_witness'];d.signed(raw,w);need(w['address']==edge['literal']and d.u32(raw,w['address'])==w['value']==edge['target']==edge['to']|1,'odd Thumb target same loaded callback')
 elif edge['kind']=='hook_edge':
  need(edge['from']==edge['branch']and edge['load']+2==edge['branch']and edge['load']in addresses and edge['to']in addresses,'immediate finite hook transfer')
  reg=edge['register'];need(reg==3 and literal(raw,edge['load'],reg)==edge['literal'],'same exact hook pointer register')
  previous.ThumbConsumer(raw).bx(edge['branch'],reg)
  w=edge['literal_witness'];d.signed(raw,w);need(w['address']==edge['literal']and d.u32(raw,w['address'])==w['value']==edge['target']==edge['to']|1,'same odd hook pointer and selected Thumb target')
 else:previous.indirect(raw,edge,rows,edges)


def _regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and tuple(r['hit']['address']for r in review['rows'])==HITS,'closed single newly unknown storage code window')
 need(identity(sources[SOURCE_LOCAL])==SOURCE_IDENTITY,'immutable pinned storage source')
 need(len(review['source_bindings'])==7 and {e['local']for e in review['source_bindings'].values()}=={'BPRJ.ld','gaps-pret-scrcmd.c','pret-task.c','pret-main.c','pret-crt0.s','pret-hall_of_fame.c',SOURCE_LOCAL},'all inherited and one new source roles')
 by_label={w['label']:w for w in review['consumer_windows']}
 need(len(by_label)==len(review['consumer_windows'])and all(label in by_label and(by_label[label]['address'],by_label[label]['size'])==geom for label,geom in NEW_WINDOWS.items()),'complete storage consumer windows')
 bprj=old.sources_bind(review,sources);previous.bind_consumers(raw,review,bprj);storage_consumers(raw,review)
 regions=[]
 for row in review['rows']:
  hit=row['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original==hit and not original['accepted']and not original['owner_candidates'],'exact inherited unknown only');d.signed(raw,hit)
  root=row['root'];entry=root['entry'];slot=root['slot'];d.signed(raw,slot)
  need(root['kind']=='special_function'and root['opcode']==37 and root['special_id']==60 and entry==0x0808C0E4,'exact bounded special60 root')
  need(slot['address']==0x08163068+4*60 and d.u32(raw,slot['address'])==slot['value']==entry|1,'actual special dispatch slot')
  rows=row['instruction_path'];need(rows and rows[0]['address']==entry and len(rows)<=512,'finite rooted instruction path');d.signed(raw,rows)
  addresses=[p['address']for p in rows];extra=row['typed_indirect_edges'];edges={e['from']:e for e in extra};need(len(edges)==len(extra),'unique typed outgoing edges')
  # Task-ID constructor lies on this same root, and its CreateTask callback is the first rewritten task.
  need(all(a in addresses for a in [0x0808C820,0x0808C82E,0x0808C836,0x0808C854,0x0808C866,0x0808C86A,0x0808CA5C]),'same rooted constructor provenance')
  registrations=[e for e in extra if e['kind']=='callback_edge'and e['callee']==0x0808CA34]
  need([(e['from'],e['to'])for e in registrations]==[(0x0808CC16,0x0808CC5C),(0x0808CC9A,0x0808CCF8),(0x0808CF4C,0x0808D7C4)],'exact storage callback rewrite chain')
  start=0
  for i,p in enumerate(rows):
   if p['address']not in edges:continue
   edge=edges[p['address']];need(i+1<len(rows)and rows[i+1]['address']==edge['to'],'typed path adjacency')
   if edge['kind']in('switch_edge','hook_edge'):
    need(p['size']==2 and i>start,'single actual indirect Thumb instruction');gaps.thumb_path(raw,rows[start:i],rows[start]['address']);need(rows[i-1]['address']+rows[i-1]['size']==p['address'],'contiguous typed predecessor')
   else:gaps.thumb_path(raw,rows[start:i+1],rows[start]['address'])
   indirect(raw,edge,rows,extra);start=i+1
  need(start<len(rows),'nonempty suffix');gaps.thumb_path(raw,rows[start:],rows[start]['address'])
  w=row['instruction_window'];d.signed(raw,w);selected=[p for p in rows if w['address']<=p['address']<w['address']+w['size']]
  need((w['address'],w['size'])==(0x0808D7FE,6),'only one complete minimal BL/LDR crossing')
  need([(p['address'],p['size'])for p in selected]==[(0x0808D7FE,4),(0x0808D802,2)]and d.contains(w['address'],w['address']+w['size'],hit['address'],4),'actual whole instruction window')
  need(not row['literal_pool_included']and not row['whole_function_range_classified']and not any(w['address']<=p.get('literal_address',0)<w['address']+w['size']for p in rows),'no literals or blanket range classification')
  regions.append(d.TypedRegion(w['address'],w['address']+w['size'],'rooted_thumb_instruction_stream',dict(root=root,instruction_window=w,instructions=[{k:p[k]for k in('address','size')}for p in selected],root_verified=True,literal_pool_included=False,path_instructions=len(rows),typed_indirect_edges=len(edges),full_story_reachability_claimed=False,full_storage_lifetime_claimed=False)))
 return regions,dict(status='PASS_ONE_FINITE_STORAGE_TASK_CODE_WINDOW',count=1,full_story_reachability_claimed=False,full_storage_lifetime_claimed=False)


def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources)
