"""Summary実setupからnature2文字列の消費を合成する条件付き最小境界型。"""
import copy,hashlib,json
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_lifetime_menu as menu
import pr16_dex_hof_runtime_party as runtime
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
HIT=0x0842D18A
KIND='rooted_summary_adjacent_nature_text'
CELL,PLACEHOLDERS=0x0203B0B4,0x0203F2C0
LOCAL_SOURCES={
 'pret-dynamic_placeholder_text_util.c':dict(local='pret-dynamic_placeholder_text_util.c',repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/dynamic_placeholder_text_util.c',size=11041,sha256='a6d59c5e69f6406b9cfbdf97048b150b91c5d1dde21afce6d481da78151fad7d',git_blob_sha='c56b5116cd5964b69e180fecd5f6f25708148758'),
 'pret-nature_names.h':dict(local='pret-nature_names.h',repository='pret/pokefirered',commit='c75f352304d529f6ba92d4f74b9cf8b5c3810788',path='src/data/text/nature_names.h',size=2305,sha256='a8e82bf571e9eab767f7bcc654befc8fe1782c34250fe89e2542ef2894e55031',git_blob_sha='4c387a64c88f5108a19e0dee6757ec0f41be3efb'),
}
BLOCKS={}
def put(name,address,specs):BLOCKS[name]=tuple(party.block(address,specs))
put('setup8_call',0x081364A0,[('call',0x08137CA0)])
put('bottom_page_dispatch',0x08137CA0,[('push',16,True),('literal',4,0x08137CCC),('mem',True,'word',0,4,0),('literal',1,0x08137CD0),('add',0,0,1),('mem',True,'byte',0,0,0),('imm','mov',1,0),('call',0x08004428),('mem',True,'word',0,4,0),('imm','mov',1,199),('shift','lsl',1,1,6),('add',0,0,1),('mem',True,'byte',0,0,0),('imm','cmp',0,1),('branch',0,0x08137CE4),('imm','cmp',0,1),('branch',12,0x08137CD4),('imm','cmp',0,0),('branch',0,0x08137CDE)])
put('bottom_info_call',0x08137CDE,[('call',0x08137D0C)])
put('trainer_non_egg_dispatch',0x08137D0C,[('push',0,True),('literal',0,0x08137D24),('mem',True,'word',0,0,0),('literal',1,0x08137D28),('add',0,0,1),('mem',True,'byte',0,0,0),('imm','cmp',0,0),('branch',1,0x08137D2C),('call',0x08138100)])
put('trainer_own_ot_dispatch',0x08138100,[('push',0,True),('literal',0,0x0813811C),('mem',True,'word',0,0,0),('literal',1,0x08138120),('add',0,0,1),('call',0x08138C14),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,1),('branch',1,0x08138124),('call',0x08137D34)])
put('memo_nature_and_fields',0x08137D34,[('push',240,True),('spadd',-108),('call',0x0813D3D4),('literal',7,0x08137DA4),('mem',True,'word',0,7,0),('literal',4,0x08137DA8),('add',0,0,4),('call',0x0804258C),('shift','lsl',0,0,24),('shift','lsr',6,0,24),('literal',1,0x08137DAC),('shift','lsl',0,6,2),('add',0,0,1),('mem',True,'word',1,0,0),('imm','mov',0,0),('call',0x0813D3F0),('mem',True,'word',0,7,0),('add',0,0,4),('imm','mov',1,36),('call',0x0803F354),('shift','lsl',0,0,24),('shift','lsr',1,0,24),('imm','cmp',1,0),('branch',1,0x08137D6E),('imm','mov',1,5),('spaddr',0,20),('imm','mov',2,0),('imm','mov',3,3),('call',0x080089F4),('imm','mov',0,1),('spaddr',1,20),('call',0x0813D3F0),('mem',True,'word',0,7,0),('add',0,0,4),('imm','mov',1,35),('call',0x0803F354),('shift','lsl',0,0,24),('shift','lsr',5,0,24),('addi',0,5,0),('call',0x0813BFFC),('imm','cmp',0,1),('branch',1,0x08137DB0)])
put('outside_location_branch',0x08137DB0,[('mem',True,'word',0,7,0),('literal',1,0x08137DD0),('add',0,0,1),('mem',True,'word',0,0,0),('imm','cmp',0,1),('branch',0,0x08137DC4),('call',0x08139310),('imm','cmp',0,1),('branch',1,0x08137DD8)])
put('location_copy_and_metlevel',0x08137DD8,[('spaddr',4,28),('literal',1,0x08137E1C),('addi',0,4,0),('call',0x08008900),('addi',1,4,0),('imm','mov',0,2),('call',0x0813D3F0),('literal',4,0x08137E20),('mem',True,'word',0,4,0),('literal',1,0x08137E24),('add',0,0,1),('imm','mov',1,36),('call',0x0803F354),('imm','cmp',0,0),('branch',1,0x08137E58)])
put('fateful_location_nature_grammar',0x08137E58,[('imm','cmp',5,255),('branch',1,0x08137E7C),('addi',0,6,0),('call',0x0813BFA4),('imm','cmp',0,0),('branch',0,0x08137E70),('spaddr',4,48),('literal',1,0x08137E6C),('jump',0x08137E8A)])
put('ordinary_nature_template',0x08137E70,[('spaddr',4,48),('literal',1,0x08137E78),('jump',0x08137E8A)])
put('expand_selected_template',0x08137E8A,[('addi',0,4,0),('call',0x0813D40C)])
put('nature_getter',0x0804258C,[('push',0,True),('imm','mov',1,0),('imm','mov',2,0),('call',0x0803F354),('imm','mov',1,25),('call',0x081C85A4),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('pop',2,False),('bx',1)])
put('mod25_small_dividend',0x081C85A4,[('imm','cmp',1,0),('branch',0,0x081C865A),('imm','mov',3,1),('compare',0,1),('branch',2,0x081C85B0),('movhi',15,14)])
put('bold_gentle_grammar',0x0813BFA4,[('push',0,True),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,5),('branch',0,0x0813BFB2),('imm','cmp',0,21),('branch',1,0x0813BFB6),('imm','mov',0,1),('jump',0x0813BFB8),('imm','mov',0,0),('pop',2,False),('bx',1)])
put('placeholder_reset',0x0813D3D4,[('push',0,True),('literal',1,0x0813D3EC),('imm','mov',2,0),('addi',0,1,0),('imm','add',0,28),('mem',False,'word',2,0,0),('imm','sub',0,4),('compare',0,1),('branch',10,0x0813D3DE),('pop',1,False),('bx',0)])
put('placeholder_store',0x0813D3F0,[('push',0,True),('addi',2,1,0),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('imm','cmp',0,7),('branch',8,0x0813D404),('literal',1,0x0813D408),('shift','lsl',0,0,2),('add',0,0,1),('mem',False,'word',2,0,0),('pop',1,False),('bx',0)])
put('expand_first_dynamic_token',0x0813D40C,[('push',48,True),('addi',2,0,0),('addi',4,1,0),('mem',True,'byte',1,4,0),('addi',0,1,0),('imm','cmp',0,255),('branch',0,0x0813D44C),('literal',5,0x0813D428),('imm','cmp',1,247),('branch',0,0x0813D42C)])
put('dynamic0_copy',0x0813D42C,[('imm','add',4,1),('mem',True,'byte',0,4,0),('shift','lsl',0,0,2),('add',0,0,5),('mem',True,'word',1,0,0),('imm','cmp',1,0),('branch',0,0x0813D442),('addi',0,2,0),('call',0x08008900)])
put('stringcopy_complete',0x08008900,[('push',0,True),('addi',3,0,0),('jump',0x0800890C),('mem',False,'byte',2,3,0),('imm','add',3,1),('imm','add',1,1),('mem',True,'byte',2,1,0),('addi',0,2,0),('imm','cmp',0,255),('branch',1,0x08008906),('imm','mov',0,255),('mem',False,'byte',0,3,0),('addi',0,3,0),('pop',2,False),('bx',1)])
LITERALS={0x08137CCC:CELL,0x08137CD0:0x3004,0x08137D24:CELL,0x08137D28:0x31AC,0x0813811C:CELL,0x08138120:0x323C,0x08137DA4:CELL,0x08137DA8:0x323C,0x08137DAC:0x0842D1EC,0x08137DD0:0x3024,0x08137E1C:0x083E01FB,0x08137E20:CELL,0x08137E24:0x323C,0x08137E6C:0x083DFF45,0x08137E78:0x083DFF25,0x0813D3EC:PLACEHOLDERS,0x0813D408:PLACEHOLDERS,0x0813D428:PLACEHOLDERS,0x0842D200:0x0842D188,0x0842D204:0x0842D18D}
TEXTS=[dict(index=5,symbol='NATURE_BOLD',address=0x0842D188,size=5,sha256='698bc554e1f3608a697243335b9885a7f1faaee432af3c2269db8c444910ffbd'),dict(index=6,symbol='NATURE_DOCILE',address=0x0842D18D,size=4,sha256='f594446977d67bdaf45dcf66898b259ccc410ea8ce77e72c3b866c9fe235dd99')]
TEMPLATES={5:0x083DFF45,6:0x083DFF25}
INS={i.address:i for block in BLOCKS.values()for i in block}
WINDOWS={name:(rows[0].address,sum(i.size for i in rows))for name,rows in BLOCKS.items()}
WINDOWS.update({f'literal_{a:08x}':(a,4)for a in sorted(LITERALS)})
WINDOWS.update({f'nature_text_{r["index"]}':(r['address'],r['size'])for r in TEXTS})
WINDOWS.update({f'template_dynamic0_{ix}':(a,2)for ix,a in TEMPLATES.items()})
CLAIMS=dict(proof_scope='conditional_registered_summary_setup_finite_text_consumer',full_story_reachability_claimed=False,actual_runtime_execution_observed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,whole_string_table_classified=False,source_pointer_interpretation=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
ROOT=dict(summary_cell=CELL,setup_state=8,setup_call=0x081364A0,bottom_text=0x08137CA0,page=0,is_egg=0,trainer_dispatch=0x08138100,held_by_ot=0x08137D34,nature_getter=0x0804258C,nature_modulo=0x081C85A4,nature_table=0x0842D1EC,nature_indices=[5,6],placeholder_store=0x0813D3F0,placeholder_cell=PLACEHOLDERS,expand_call=0x08137E8C,stringcopy_call=0x0813D43C,stringcopy=0x08008900,stop=0x0813D440)
CONTRACT={
 'root':'same real StartMenuPokemon action0 and Summary constructor/setup0..7 as shared root_at_setup; stop before actual setup8 BL',
 'profile':'two sufficient conditional cases: same selected heap mon personality5 or6, non-egg, current page0, held by own OT, met level1, met location255, not enemy party and not multi-battle partner',
 'getter':'GetMonData exact sites read Summary heap currentMon+0x323C: field0 personality5/6; field36 met level1; field35 met location255. Opaque getter effects and scalar outputs explicitly conditional, never reused party getter theorem',
 'nature':'actual GetNature calls field0 then actual modulo25 early-return instructions for5/6<25; actual index*4 pointer read and placeholder0 store; no assumed GetNature result',
 'lifetime':'Summary pointer/epoch and future-read page/isEgg/enemy/currentMon/window fields persist to last reads; only selected call-boundary fields and ABI registers/saved stack are protected, not whole heap/IRQ lifetime',
 'outputs':'FillWindowPixelBuffer, own-OT predicate, integer formatter, MapSec predicate, multi-battle predicate, and location StringCopy have the declared finite normal returns and preserve future-live fields; outputs for placeholder1/2 are not consumed before stop',
 'placeholder':'actual Reset clears eight slots, actual Set stores slots0/1/2; opaque calls preserve slot0 after nature store, current stack and retained r4-r7',
 'copy':'both selected ROM templates begin dynamic-token247,index0; actual expander loads the stored selected pointer and calls actual StringCopy; every byte including terminal255 is read for each text; stop at return0x0813D440 before later template output',
 'geometry':'two complete terminal-only EOS strings5/4 are adjacent; exactly four hit bytes cross their boundary; neither pointer rows nor full strings become newly classified',
}
def exact(a,b):return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def bind_semantics(raw):
 for name,rows in BLOCKS.items():
  for i in rows:need(chunk(raw,i.address,i.size)==menu.encoded(i),'nature semantic '+name+' '+hex(i.address))
 for a,v in LITERALS.items():need(d.u32(raw,a)==v,'nature literal/table '+hex(a))
 for row in TEXTS:
  d.signed(raw,row);b=chunk(raw,row['address'],row['size']);need(b[-1]==255 and 255 not in b[:-1],'complete terminal-only nature string')
 for a in TEMPLATES.values():need(chunk(raw,a,2)==bytes((247,0)),'actual selected dynamic0 prefix, no guessed expansion')
class Machine(runtime.Machine):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.rom_reads=[];self.active_saved_slots=set(range(self.reg[13],0x03007000))
 def read(self,a,n):
  v=super().read(a,n)
  if type(a)is int and 0x08000000<=a<0x0A000000:self.rom_reads.append((self.pc,a,n))
  return v
 def step(self,branch_choice=None):
  i=self.instructions.get(self.pc)
  if i is not None and i.kind=='spaddr':
   self.reg[i.args[0]]=self.reg[13]+i.args[1];self.pc+=2;self.steps+=1;return
  if i is not None and i.kind in ('push','pop'):
   mask,extra=i.args;n=4*(sum(bool(mask&(1<<r))for r in range(8))+int(extra));sp=self.reg[13]
   if i.kind=='push':self.active_saved_slots.update(range(sp-n,sp))
   else:self.active_saved_slots.difference_update(range(sp,sp+n))
  return super().step(branch_choice)
# Shared constructor/setup semantics remain one source of truth. Nature does not
# call the later page-flip consumer or classify its code occurrence.
import pr16_dex_hof_summary_type as summary
SOURCE_IDS={**copy.deepcopy(summary.SOURCE_IDS),**copy.deepcopy(LOCAL_SOURCES)}
LOCAL_WINDOWS=dict(WINDOWS)
WINDOWS={**{'shared_'+name:value for name,value in summary.WINDOWS.items()},**LOCAL_WINDOWS}
def protected_windows(review):
 rows=review['windows'];need(type(rows)is list and len(rows)==len(WINDOWS),'closed nature/shared windows')
 need(all(type(r)is dict and set(r)=={'label','address','size','sha256'}for r in rows),'address-size-SHA-only windows')
 need(exact([(r['label'],r['address'],r['size'])for r in rows],[(name,*value)for name,value in WINDOWS.items()]),'exact ordered shared/local geometry')
 need(all(type(r['sha256'])is str and len(r['sha256'])==64 and all(c in '0123456789abcdef'for c in r['sha256'])for r in rows),'complete SHA256 format')
 return[{k:r[k]for k in('address','size','sha256')}for r in rows]
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'exact closed fixed sources')
 shared_review={'source_bindings':summary.SOURCE_IDS}
 summary.sources_bind(shared_review,{k:sources[k]for k in summary.SOURCE_IDS})
 for key in LOCAL_SOURCES:
  b=sources[key];row=LOCAL_SOURCES[key]
  need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'whole fixed public source '+key)
 text=sources['pret-pokemon_summary_screen.c'].decode()
 for token in ('case 8:\n        PokeSum_PrintBottomPaneText();','case PSS_PAGE_INFO:\n        PokeSum_PrintTrainerMemo();','if (!sMonSummaryScreen->isEgg)','PokeSum_PrintTrainerMemo_Mon_HeldByOT','nature = GetNature(&sMonSummaryScreen->currentMon);','DynamicPlaceholderTextUtil_SetPlaceholderPtr(0, gNatureNamePointers[nature]);'):
  need(token in text,'source-derived Summary semantic role')
 names=sources['pret-nature_names.h'].decode();need('[NATURE_BOLD] = sBoldNatureName' in names and '[NATURE_DOCILE] = sDocileNatureName'in names,'source named nature table roles')
 text=sources['pret-dynamic_placeholder_text_util.c'].decode()
 for token in ('sStringPointers[8]','if (idx < NELEMS(sStringPointers))','sStringPointers[idx] = ptr;','while (*src != EOS)','if (*src != CHAR_DYNAMIC)','dest = StringCopy(dest, sStringPointers[*src]);'):
  need(token in text,'source actual placeholder store/expansion/copy ABI')
def evidence_template():
 return dict(schema_version=1,root_verified=True,root=copy.deepcopy(ROOT),input_contract=copy.deepcopy(CONTRACT),claims=copy.deepcopy(CLAIMS),
  left=copy.deepcopy(TEXTS[0]),right=copy.deepcopy(TEXTS[1]),both_complete_text_consumers_verified=True,
  classified_window=dict(address=HIT,size=4),pointer_table_rows_classified=False,template_prefix_classified=False,type_classification_only=True)
def witness_geometry(e):
 need(exact(e,evidence_template()),'exact rooted two-consumer boundary evidence')
 left,right=e['left'],e['right'];need(left['address']+left['size']==right['address']and left['address']<=HIT<right['address']<HIT+4<=right['address']+right['size'],'all four bytes covered by two adjacent consumed strings')
 return HIT,4

def _compose_from_root(raw,root,nature):
 need(type(nature)is int and nature in (5,6),'only two selected source indices')
 need(root.pc==0x081364A0,'actual setup8 callsite required')
 p=root.read(CELL,4);need(type(p)is int and p%4==0 and 0x02000010<=p<=0x02020000-0x32B4,'actual Summary allocation geometry')
 need(root.read(p+0x3220,1)==8 and root.read(p+0x31C0,1)==0 and root.read(p+0x31AC,1)==0 and root.read(p+0x3024,4)==0,'constructor/setup-produced current control fields')
 m=Machine(raw,root.pc,dict(enumerate(root.reg)),root.mem,INS);calls=[];events=[];copy_destination=None;copy_sp=None
 text=next(r for r in TEXTS if r['index']==nature)
 boundaries={
  (0x08137CAE,0x08004428):('fill selected trainer memo window',runtime.U),
  (0x0813810A,0x08138C14):('same heap mon held by own OT',1),
  (0x08042592,0x0803F354):('same heap mon personality field0',nature),
  (0x08137D60,0x0803F354):('same heap mon met-level field36',1),
  (0x08137D74,0x080089F4):('decimal formatter normal return',runtime.U),
  (0x08137D86,0x0803F354):('same heap mon met-location field35',255),
  (0x08137D90,0x0813BFFC):('met-location255 outside Kanto/Sevii',0),
  (0x08137DBC,0x08139310):('not a multi-battle partner',0),
  (0x08137DDE,0x08008900):('location-text copy normal return',runtime.U),
  (0x08137DF4,0x0803F354):('same heap mon unchanged met-level field36',1),
 }
 while m.pc!=ROOT['stop']:
  site=(m.reg[14]&~1)-4 if runtime.concrete(m.reg[14])else None
  boundary=boundaries.get((site,m.pc))
  if boundary is not None:
   role,result=boundary
   if m.pc==0x0803F354:
    field={0x08042592:0,0x08137D60:36,0x08137D86:35,0x08137DF4:36}[site]
    need((m.reg[0],m.reg[1])==(p+0x323C,field),'exact selected heap mon and field getter')
    if field==0:need(m.reg[2]==0,'personality getter null data destination')
   elif site==0x08137CAE:need((m.reg[0],m.reg[1])==(root.read(p+0x3004,1),0),'actual selected window ID and fill value')
   elif site==0x0813810A:need(m.reg[0]==p+0x323C,'same currentMon to own-OT predicate')
   elif site==0x08137D74:need(m.reg[0]==m.reg[13]+20 and tuple(m.reg[1:4])==(1,0,3),'metlevel1 decimal arguments')
   elif site==0x08137D90:need(m.reg[0]==255,'source-selected metlocation255 predicate')
   elif site==0x08137DDE:need((m.reg[0],m.reg[1])==(m.reg[13]+28,0x083E01FB),'selected location copy only, not nature copy')
   live=live_projection(p,site,m.active_saved_slots)
   calls.append(dict(site=site,target=m.pc,role=role,normal_abi_return_required=True,effects_discharged=False,
    return_value=result if runtime.concrete(result)else'unspecified',required_fields=live,conditional_outputs=[]))
   # Erase every nonlive RAM cell at each boundary. Continued execution may not
   # silently depend on an entire preserved heap/task array/stack-local buffer.
   m.mem={a:value for a,value in m.mem.items()if any(f['address']<=a<f['address']+f['size']for f in live)}
   for r in (0,1,2,3,12):m.reg[r]=runtime.U
   m.reg[0]=result;m.flag_pc=None;m.pc=m.reg[14]&~1;continue
  need(m.pc in INS,'nature path escaped exact finite model at '+hex(m.pc))
  if m.pc==0x08137D52:need(m.reg[0]==0x0842D1EC+4*nature,'actual index*4 selected pointer row')
  if m.pc==0x08137D5A:
   need(m.read(PLACEHOLDERS,4)==text['address'],'actual placeholder0 store')
   events.append(dict(role='selected_nature_pointer_stored',index=nature,table_cell=0x0842D1EC+4*nature,pointer=text['address']))
  if m.pc==0x08137E8C:need(m.reg[1]==TEMPLATES[nature],'actual Bold/ordinary grammar picks its own template')
  if m.pc==0x0813D43C:
   need(m.reg[1]==text['address']and m.read(PLACEHOLDERS,4)==text['address'],'actual stored pointer consumed by expander')
   need(m.reg[4]==TEMPLATES[nature]+1,'actual first template token index')
   copy_destination=m.reg[0];copy_sp=m.reg[13]
  m.step()
 need(copy_destination is not None and m.reg[13]==copy_sp,'complete StringCopy returns with balanced own frame')
 reads=[(a,n)for pc,a,n in m.rom_reads if pc==0x0800890C]
 need(reads==[(text['address']+j,1)for j in range(text['size'])],'every selected text byte including EOS consumed exactly once')
 need(all(m.read(copy_destination+j,1)==chunk(raw,text['address']+j,1)[0]for j in range(text['size'])),'complete selected text copied including terminal EOS')
 need(m.reg[0]==copy_destination+text['size']-1,'StringCopy returns actual terminal destination')
 return dict(index=nature,personality=nature,complete_text=copy.deepcopy(text),table_cell=0x0842D1EC+4*nature,template_prefix=dict(address=TEMPLATES[nature],size=2),
  events=events,conditional_calls=calls,nature_byte_reads=text['size'],includes_eos_read=True,stringcopy_return_observed_in_synthetic_composition=True,
  stop=m.pc,nonlive_ram_erased_at_each_boundary=True,synthetic_contract_execution=True,actual_runtime_execution_observed=False)

def compose_selected(raw):
 bind_semantics(raw);root,proof=summary.root_at_setup(raw,state=8)
 cases=[_compose_from_root(raw,root,nature)for nature in (5,6)]
 return dict(status='PASS_CONDITIONAL_REGISTERED_SUMMARY_NATURE_PAIR',shared_root=proof,cases=cases,complete_consumed_bytes=9,
  projection_counterexamples=projection_counterexamples(root.read(CELL,4)),synthetic_contract_execution=True,actual_runtime_execution_observed=False)

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hit','root','windows','claims','input_contract','texts'},'closed nature review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'exact review version')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'fixed current and separate diagnostic identities')
 need(exact(review['root'],ROOT)and exact(review['claims'],CLAIMS)and exact(review['input_contract'],CONTRACT)and exact(review['texts'],TEXTS),'exact natural-reachability-limited nature proof')
 originals=[h for h in inherited['hits']if h['address']==HIT]
 need(len(originals)==1 and exact(originals[0],review['hit'])and originals[0]['accepted']is False and originals[0]['owner_candidates']==[],'one exact owner-external unknown nature hit')
 need(type(originals[0]['size'])is int and originals[0]['size']==4 and originals[0]['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','one original all-byte-start 4-byte hit')
 d.signed(raw,originals[0]);sources_bind(review,sources);d.signed(raw,protected_windows(review));bind_semantics(raw)
 composition=compose_selected(raw);evidence=evidence_template();a,n=witness_geometry(evidence)
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_CONDITIONAL_ROOTED_NATURE_TEXT_CROSSING',count=1,hit=HIT,
  protected_windows=len(WINDOWS),protected_bytes=sum(n for a,n in WINDOWS.values()),composition=composition,source_bindings=SOURCE_IDS,**CLAIMS)
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current required; old diagnostic cannot classify current')
 return _regions(raw,inherited,review,sources)
def make_review(raw,hit):
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hit=copy.deepcopy(hit),root=copy.deepcopy(ROOT),windows=[dict(label=name,address=a,**identity(chunk(raw,a,n)))for name,(a,n)in WINDOWS.items()],claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),texts=copy.deepcopy(TEXTS))

BOUNDARY_SITES=(0x08137CAE,0x0813810A,0x08042592,0x08137D60,0x08137D74,0x08137D86,0x08137D90,0x08137DBC,0x08137DDE,0x08137DF4)
def live_projection(pointer,site,saved_stack=()):
 need(type(pointer)is int and pointer%4==0 and 0x02000010<=pointer<=0x02020000-0x32B4,'bounded Summary allocation')
 need(type(site)is int and site in BOUNDARY_SITES,'fixed opaque boundary')
 fields=[]
 def add(a,n,role):fields.append(dict(address=a,size=n,role=role))
 add(pointer-16,8,'same live allocation used/magic/extent; epoch additionally required')
 add(pointer+0x323C,100,'same heap currentMon through getter boundary')
 if site!=0x08137DF4:add(CELL,4,'Summary pointer used by a future read')
 if site==0x08137CAE:
  add(pointer+0x31C0,1,'page0 read after window-fill return');add(pointer+0x31AC,1,'non-egg dispatch read')
 if site in (0x08137CAE,0x0813810A,0x08042592,0x08137D60,0x08137D74,0x08137D86,0x08137D90):add(pointer+0x3024,4,'enemy-party dispatch word until its last read')
 if site in (0x08137D60,0x08137D74,0x08137D86,0x08137D90,0x08137DBC,0x08137DDE,0x08137DF4):add(PLACEHOLDERS,4,'actual selected nature placeholder0 through copy')
 stack=sorted(set(saved_stack));need(all(type(a)is int and 0x03006000<=a<0x03007000 for a in stack),'concrete active ABI stack cells')
 if stack:
  start=last=stack[0]
  for a in stack[1:]:
   if a!=last+1:add(start,last-start+1,'active saved ABI stack');start=a
   last=a
  add(start,last-start+1,'active saved ABI stack')
 return fields
def preservation_contract(pointer,site,writes,saved_stack=(),freed=(),heap_reinitialized=False):
 need(heap_reinitialized is False and pointer not in freed,'live allocation epoch, not pointer-value ABA')
 fields=live_projection(pointer,site,saved_stack)
 for a,n in writes:
  need(type(a)is int and type(n)is int and n>0 and 0<=a<a+n<=1<<32,'bounded concrete declared write')
  need(all(runtime.disjoint(a,n,f['address'],f['size'])for f in fields),'declared write intersects future-live field')
 return True
def projection_counterexamples(pointer):
 rejected=0
 for site in BOUNDARY_SITES:
  for field in live_projection(pointer,site):
   try:preservation_contract(pointer,site,[(field['address'],1)])
   except ValueError:rejected+=1
   else:raise ValueError('live field overwrite was incorrectly admitted')
  need(preservation_contract(pointer,site,[(0x0203F000,4),(PLACEHOLDERS+4,4)]),'unrelated RAM and unused placeholder1 are not frozen')
 return dict(status='PASS_CONCRETE_NATURE_LIVE_PROJECTION_COUNTEREXAMPLES',live_field_write_rejections=rejected,boundaries=len(BOUNDARY_SITES),unused_placeholder1_writes_allowed=True,unrelated_ram_writes_allowed=True,opaque_actual_effects_proven=False)
