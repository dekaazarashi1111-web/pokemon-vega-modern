"""有限JP dispatcher/登録callback/switchから未知命令windowだけを検証する候補実装。"""
import hashlib,re,struct
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
import pr16_dex_hof_reference_gaps as gaps
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
HITS=(0x0805C9C9,0x080DF21B,0x080E5A83,0x0810C997,0x081CB487,0x090D9FF3)
def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')
def literal(raw,a,reg):
 op=half(raw,a);need(op&0xF800==0x4800 and(op>>8)&7==reg,'actual selected LDR register')
 return ((a+4)&~3)+(op&255)*4

def sources_bind(review,sources):
 for name,exp in review['source_bindings'].items():
  b=sources[exp['local']];need(identity(b)=={k:exp[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==exp['git_blob_sha'],'whole source binding')
 return re.sub(r'/\*.*?\*/|//[^\n]*','',sources['BPRJ.ld'].decode(),flags=re.S)
def symbol(bprj,name,address):
 values=re.findall(r'^\s*'+re.escape(name)+r'\s*=\s*(0x[0-9A-Fa-f]+)\s*\|\s*1\s*;',bprj,re.M)
 need(values and all((int(v,16)&~1)==address for v in values),'fixed exact JP symbol entry')

def bind_consumers(raw,review,bprj):
 d.signed(raw,review['consumer_windows']);d.signed(raw,review['consumer_literals'])
 lit={r['label']:r for r in review['consumer_literals']}
 for r in lit.values():need(d.u32(raw,r['address'])==r['value'],'actual selected dispatcher literal')
 symbol(bprj,'ScriptContext1_SetupScript',0x080693A4)
 need(literal(raw,0x080693B6,1)==0x080693DC and literal(raw,0x080693B8,2)==0x080693E0,'setup table and end loads')
 need(code.thumb_bl(chunk(raw,0x080693BC,4),0x080693BC)==0x0806906C,'actual InitScriptContext call')
 need((lit['script_dispatch_base']['value'],lit['script_dispatch_end']['value'])==(0x08162CC4,0x08163010),'actual bounded script table')
 need(lit['special_handler_slot']['address']==0x08162CC4+37*4 and lit['special_handler_slot']['value']==0x080697BD,'special command typed slot')
 need((lit['special_table_base']['value'],lit['special_table_end']['value'])==(0x08163068,0x08163758),'actual bounded special table')
 need(literal(raw,0x080697C6,1)==0x080697D8 and literal(raw,0x080697CA,0)==0x080697DC,'special exact table literal loads')
 need(code.thumb_bl(chunk(raw,0x080697BE,4),0x080697BE)==0x080691B8 and code.thumb_bl(chunk(raw,0x080697D2,4),0x080697D2)==0x081C7AC8,'special halfword and r0 interwork calls')
 need(half(raw,0x081C7AC8)&0xFF87==0x4700 and(half(raw,0x081C7AC8)>>3)&15==0 and half(raw,0x081C7ACC)&0xFF87==0x4700 and(half(raw,0x081C7ACC)>>3)&15==1,'exact BX r0/BX r1 consumers')
 symbol(bprj,'CreateTask',0x08076BB4);symbol(bprj,'RunTasks',0x08076D10)
 need(lit['CreateTask_gTasks']['value']==lit['RunTasks_gTasks']['value']==0x030050D0,'same actual task table')
 need(literal(raw,0x08076BBE,7)==lit['CreateTask_gTasks']['address'] and literal(raw,0x08076D1E,5)==lit['RunTasks_gTasks']['address'],'task writer and reader actual roots')
 store=half(raw,0x08076BCE);load=half(raw,0x08076D28)
 need(store&0xF800==0x6000 and(store>>6)&31==0 and(store>>3)&7==4 and store&7==2,'CreateTask stores preserved argument r2 to task.func')
 need(load&0xF800==0x6800 and(load>>6)&31==0 and(load>>3)&7==4 and load&7==1,'RunTasks reads task.func into r1')
 need(code.thumb_bl(chunk(raw,0x08076D2A,4),0x08076D2A)==0x081C7ACC,'RunTasks dispatches actual task.func')

def indirect(raw,edge,path_addresses):
 need(edge['from']in path_addresses and edge['to']in path_addresses,'finite typed edge inside selected path')
 if edge['kind']=='callback_edge':
  need(edge['from']==edge['call']and edge['callee']==0x08076BB4 and edge['load'] in path_addresses and edge['load']+2 in path_addresses,'only reviewed rooted CreateTask typed callback edge')
  need(code.thumb_bl(chunk(raw,edge['call'],4),edge['call'])==edge['callee'],'actual callback registration BL')
  need(edge['load']+4==edge['call'] and literal(raw,edge['load'],0)==edge['literal'],'LDR r0 then one priority setup')
  op=half(raw,edge['load']+2);need(op&0xFF00==0x2100,'only MOVS r1 priority between pointer load and CreateTask')
  w=edge['literal_witness'];d.signed(raw,w)
  need(w['address']==edge['literal']and d.u32(raw,w['address'])==w['value']==edge['target']==edge['to']|1,'actual odd Thumb task target')
 elif edge['kind']=='switch_edge':
  pc=edge['dispatch'];need(edge['from']==pc and half(raw,pc)==0x4687,'only actual MOV pc,r0 switch edge')
  a=pc-8;shift=half(raw,a);need(shift&0xFFC7==0x0080,'LSL r0,index,#2')
  reg=(shift>>3)&7;cmp=half(raw,edge['compare']);need(cmp&0xF800==0x2800 and(cmp>>8)&7==reg and(cmp&255)+1==edge['count']and 0<=edge['index']<edge['count']<=256,'same bounded switch index')
  br=edge['conditional'];need(edge['compare']+2==br and edge['compare'] in path_addresses and br in path_addresses,'rooted adjacent compare and unsigned bound branch')
  op=half(raw,br);off=op&255;off=off-256 if off&128 else off;target=br+4+2*off
  need((op&0xFF00==0xD800 and br+2==a) or (op&0xFF00==0xD900 and target==a),'valid BHI-fallthrough or BLS-taken bound to dispatch')
  need(literal(raw,pc-6,1)==edge['table_literal'],'actual switch table pointer literal')
  add=half(raw,pc-4);load=half(raw,pc-2)
  need(add&0xFE00==0x1800 and(add>>6)&7==1 and(add>>3)&7==0 and add&7==0,'ADD r0,r0,r1 table index')
  need(load&0xF800==0x6800 and(load>>6)&31==0 and(load>>3)&7==0 and load&7==0,'LDR r0,[r0] exact table row')
  for k in('table_literal','slot'):
   w=edge[k+'_witness'];d.signed(raw,w);need(w['address']==edge[k]and d.u32(raw,w['address'])==w['value'],'actual switch literal and selected slot')
  need(d.u32(raw,edge['table_literal'])==edge['table']and edge['slot']==edge['table']+4*edge['index'] and d.u32(raw,edge['slot'])==edge['target']==edge['to']and edge['to']%2==0,'finite bounded same-state switch target')
 else:need(False,'unreviewed indirect edge forbidden')

def _regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and tuple(r['hit']['address']for r in review['rows'])==HITS,'closed six finite unknown rows')
 bprj=sources_bind(review,sources);bind_consumers(raw,review,bprj);regions=[]
 for row in review['rows']:
  hit=row['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original==hit and not original['accepted']and not original['owner_candidates'],'exact original unowned unknown only');d.signed(raw,hit)
  root=row['root'];entry=root['entry']
  if root['kind']=='pinned_jp_symbol':symbol(bprj,root['symbol'],entry)
  else:
   slot=root['slot'];d.signed(raw,slot)
   if root['kind']=='script_command':base,end,idx=0x08162CC4,0x08163010,root['opcode']
   else:need(root['kind']=='special_function'and root['opcode']==37,'only exact typed special opcode');base,end,idx=0x08163068,0x08163758,root['special_id']
   need(0<=idx<(end-base)//4 and slot['address']==base+4*idx and d.u32(raw,slot['address'])==slot['value']==entry|1,'actual indexed typed Thumb root')
  rows=row['instruction_path'];need(rows and rows[0]['address']==entry and len(rows)<=512,'bounded whole rooted path');d.signed(raw,rows)
  addresses=[p['address']for p in rows];edges={e['from']:e for e in row['typed_indirect_edges']};start=0
  need(len(edges)==len(row['typed_indirect_edges']),'unique typed outgoing branches')
  for i,p in enumerate(rows):
   if p['address']not in edges:continue
   edge=edges[p['address']];need(i+1<len(rows)and rows[i+1]['address']==edge['to'],'typed indirect connects exact adjacent path nodes')
   # The known PC-writing instruction is verified by its semantic edge, not generic fallthrough.
   if edge['kind']=='switch_edge':
    need(p['size']==2,'one complete ARMv4T MOV pc instruction at typed switch')
    need(i>start,'switch must have a rooted prefix');gaps.thumb_path(raw,rows[start:i],rows[start]['address']);need(rows[i-1]['address']+rows[i-1]['size']==p['address'],'switch contiguous predecessor')
   else:gaps.thumb_path(raw,rows[start:i+1],rows[start]['address'])
   indirect(raw,edge,addresses);start=i+1
  need(start<len(rows),'nonempty target suffix');gaps.thumb_path(raw,rows[start:],rows[start]['address'])
  window=row['instruction_window'];d.signed(raw,window);selected=[p for p in rows if window['address']<=p['address']<window['address']+window['size']]
  need(selected and selected[0]['address']==window['address']and all(a['address']+a['size']==b['address']for a,b in zip(selected,selected[1:]))and selected[-1]['address']+selected[-1]['size']==window['address']+window['size']and d.contains(window['address'],window['address']+window['size'],hit['address'],4),'only complete minimal selected instruction crossing')
  need(not row['literal_pool_included']and not row['whole_function_range_classified']and not any(window['address']<=p.get('literal_address',0)<window['address']+window['size']for p in rows),'literal pools and blanket function typing forbidden')
  regions.append(d.TypedRegion(window['address'],window['address']+window['size'],'rooted_thumb_instruction_stream',dict(root=root,instruction_window=window,instructions=[{k:p[k]for k in('address','size')}for p in selected],root_verified=True,literal_pool_included=False,path_instructions=len(rows),typed_indirect_edges=len(edges),full_story_reachability_claimed=False)))
 return regions,dict(status='PASS_SIX_FINITE_JP_ROOTED_CODE_WINDOWS',count=len(regions),full_story_reachability_claimed=False)

def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources)
