"""薬のstat名とparty確認textの両実API最小読取。自然到達とは分離。"""
import copy,hashlib,json,re
import pr16_dex_hof_choose_limit_roots as printer
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_donor as d
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=printer.CANDIDATE,printer.DIAGNOSTIC
KIND='registered_stat_confirm_minimum_text'
TYPE_CATEGORY='data'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x083DDDFF,)
HELD_HITS=()
exact,encoded=printer.exact,printer.encoded
SOURCE_IDS={'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'source': 'BPRJ.ld'},
 'pret-charmap.txt': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                      'git_blob_sha': 'b9d0ed9de00d05fc303bb987a5aa634b19009b47',
                      'local': 'pret-charmap.txt',
                      'repository': 'pret/pokefirered',
                      'sha256': '4da662317b3b5109a52064f9012d85b644d1dbf0f3f24243374aeef4cf25f061',
                      'size': 21853,
                      'source': 'charmap.txt'},
 'pret-party_menu.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                       'git_blob_sha': '7f3a881e6c56773aee03da475c9a1adc50530223',
                       'local': 'pret-party_menu.c',
                       'repository': 'pret/pokefirered',
                       'sha256': '8290dfd5b6444e743029ab76543ed5e4b5b32c1c2f475c686946545f934d5f9b',
                       'size': 211085,
                       'source': 'src/party_menu.c'},
 'pret-text.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': 'f3eef07ce6dea8269980a5ecfdd6902c1c9c13d2',
                 'local': 'pret-text.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '5696f49443eeaaac74b530421ac7f0cbfc71996c557399583788111c322dd80c',
                 'size': 63210,
                 'source': 'src/text.c'}}
NEW_BLOCK_SPECS={'medicine_effect_selector': [135420348,
                              [['push', 0, True],
                               ['shift', 'lsl', 0, 0, 16],
                               ['shift', 'lsr', 0, 0, 16],
                               ['call', 135427492],
                               ['shift', 'lsl', 0, 0, 24],
                               ['shift', 'lsr', 0, 0, 24],
                               ['imm', 'sub', 0, 3],
                               ['imm', 'cmp', 0, 18],
                               ['branch', 9, 135420370],
                               ['jump', 135420776],
                               ['shift', 'lsl', 0, 0, 2],
                               ['literal', 1, 135420380],
                               ['add', 0, 0, 1],
                               ['mem', True, 'word', 0, 0, 0],
                               ['movhi', 15, 0]]],
 'medicine_spdef_text': [135420700, [['literal', 0, 135420720], ['literal', 1, 135420724], ['call', 134252800]]],
 'string_copy_complete': [134252800,
                          [['push', 0, True],
                           ['addi', 3, 0, 0],
                           ['jump', 134252812],
                           ['mem', False, 'byte', 2, 3, 0],
                           ['imm', 'add', 3, 1],
                           ['imm', 'add', 1, 1],
                           ['mem', True, 'byte', 2, 1, 0],
                           ['addi', 0, 2, 0],
                           ['imm', 'cmp', 0, 255],
                           ['branch', 1, 134252806],
                           ['imm', 'mov', 0, 255],
                           ['mem', False, 'byte', 0, 3, 0],
                           ['addi', 0, 3, 0],
                           ['pop', 2, False],
                           ['bx', 1]]],
 'confirm_window_first_text': [135403752,
                               [['push', 112, True],
                                ['movhi', 6, 8],
                                ['push', 64, False],
                                ['spadd', -20],
                                ['shift', 'lsl', 0, 0, 24],
                                ['shift', 'lsr', 2, 0, 24],
                                ['literal', 0, 135403892],
                                ['mem', True, 'byte', 1, 0, 8],
                                ['imm', 'mov', 0, 15],
                                ['alu', 'and', 0, 1],
                                ['imm', 'cmp', 0, 5],
                                ['branch', 1, 135403778],
                                ['jump', 135404038],
                                ['imm', 'cmp', 2, 1],
                                ['branch', 1, 135403916],
                                ['literal', 0, 135403896],
                                ['call', 134233264],
                                ['addi', 4, 0, 0],
                                ['shift', 'lsl', 4, 4, 24],
                                ['shift', 'lsr', 4, 4, 24],
                                ['addi', 0, 4, 0],
                                ['imm', 'mov', 1, 0],
                                ['call', 134235176],
                                ['imm', 'mov', 5, 0],
                                ['spmem', False, 5, 0],
                                ['spmem', False, 5, 4],
                                ['literal', 0, 135403900],
                                ['movhi', 8, 0],
                                ['spmem', False, 0, 8],
                                ['imm', 'mov', 6, 1],
                                ['alu', 'neg', 6, 6],
                                ['spmem', False, 6, 12],
                                ['literal', 0, 135403904],
                                ['spmem', False, 0, 16],
                                ['addi', 0, 4, 0],
                                ['imm', 'mov', 1, 2],
                                ['imm', 'mov', 2, 6],
                                ['imm', 'mov', 3, 1],
                                ['call', 135458220]]]}
NEW_WINDOWS=[{'address': 135420348, 'sha256': '5f9c2baea0614d734f76d25cf7606820225becbbd97a9fc91885b0d4b740618d', 'size': 32},
 {'address': 135420700, 'sha256': 'ee1527895c6feaa3f9b70e94e26d2e8d5ee5564fdcc4554611466235ac4baefc', 'size': 8},
 {'address': 134252800, 'sha256': '9f256aa82c7b59268956fe86bca001d2bad212728554d3b809ca7604007bc1f2', 'size': 30},
 {'address': 135403752, 'sha256': '83c590df070841422054a74ad2c1e2b27511c0de648898cb183b90689b4fc766', 'size': 84},
 {'address': 135420380, 'sha256': '03a2bdfa4d3b10575dc161698751ee7f83d953377ce4d3935fcabbe7848264d0', 'size': 4},
 {'address': 135420432, 'sha256': 'e6296421fb35038a8d9a15f8e96b6915c582dec818983ebfe9670d30a15b43a3', 'size': 4},
 {'address': 135420720, 'sha256': 'a7d838de04093cc2922b45e5355c1ad44dc67c319495b52060dc3fcabe376b21', 'size': 4},
 {'address': 135420724, 'sha256': 'a66240c85912154cc938a73b5d1ffda3b13c0daf20abf583ede850132f1bb87b', 'size': 4},
 {'address': 135403892, 'sha256': '04b2ea8055b0639e354b56e5fcd2cc6f6105ea531d9a3406b66415b3771ddb24', 'size': 4},
 {'address': 135403896, 'sha256': '574963fdfc8ad1cf6c0abb37e2e435ceb4f784ea6f17326349692127393524d5', 'size': 4},
 {'address': 135403900, 'sha256': '16d0527f8570b46a2eb4aa5f52dc5e5e8698aafcb7447c81b5b1bdc484c06c22', 'size': 4},
 {'address': 135403904, 'sha256': '005f65e3d23cef285b7c6557762db85fa9ce3dd8ad18802b9d3d3493774a0fc3', 'size': 4},
 {'address': 138272253, 'sha256': '50362ac0660a445c987d608f5b2158658d419d55a8fd901c3ce996714a3f6065', 'size': 5},
 {'address': 138272258, 'sha256': '821cc9386da9f27b86bb35d816ddec1544e8649925cd8a11da415bb905624d43', 'size': 3},
 {'address': 135394728, 'sha256': '9488a98ba3e4e782c954c6d72c3f84161b6f54a6303dad54ccc5f8a8a026a3bf', 'size': 4},
 {'address': 138516620, 'sha256': '6478851038d1264b0075d3eefca2ec22ed82b14cf66c3ddf8f3a3a8de2658a56', 'size': 3}]
LITERALS={135420380: 135420384, 135420432: 135420700, 135420720: 33692768, 135420724: 138272253, 135403892: 33796116, 135403896: 138516648, 135403900: 138516364, 135403904: 138272258}
TEXTS=[{'address': 138272253, 'size': 5, 'sha256': '50362ac0660a445c987d608f5b2158658d419d55a8fd901c3ce996714a3f6065', 'text_ja': 'とくぼう'}, {'address': 138272258, 'size': 3, 'sha256': '821cc9386da9f27b86bb35d816ddec1544e8649925cd8a11da415bb905624d43', 'text_ja': 'けっ'}]
def shared_core(a):return a<0x08008000 or a==0x081C7ACC or 0x09378A30<=a<0x09378B50
INS={a:i for a,i in printer.INS.items()if shared_core(a)}
INS.update({a:i for a,i in engine.INS.items()if 0x0812EDAC<=a<0x0812EE34})
for address,specs in NEW_BLOCK_SPECS.values():
 for i in party.block(address,specs):
  need(i.address not in INS,'新旧命令非重複');INS[i.address]=i
INS[0x0811F5A8]=party.Ins(0x0811F5A8,'call',(0x081218E8,))
CORE_FIELDS=[row for row in printer.DATA_FIELDS if shared_core(row[0])or row[0]in(0x083E3100,0x083E3105)]
FIXED_WINDOWS=[copy.deepcopy(w)for w in printer.FIXED_WINDOWS if shared_core(w['address'])or w['address']in(0x083E3100,0x083E3105)]+[copy.deepcopy(w)for w in engine.FIXED_WINDOWS if w['address']==0x0812EDAC]+copy.deepcopy(NEW_WINDOWS)
FIXED_WINDOWS.sort(key=lambda w:(w['address'],w['size']))
ROOT=dict(left=dict(api=0x081259BC,effect_call=0x081259C2,effect_callee=0x081275A4,effect_return=15,index=12,table=0x081259E0,cell=0x08125A10,target=0x08125B1C,literal=0x08125B34,text=0x083DDDFD,consumer=0x08008900,byte_read=0x0800890C,endpoint=0x08125B24),
 right=dict(actual_setup_call=0x0811F5A8,api=0x081218E8,choose_multiple=1,menu_type=4,literal=0x08121980,text=0x083DDE02,consumer_call=0x08121938,wrapper=0x0812EDAC,printer=0x08002CF0,hook=0x09378A30,byte_read=0x0800580E,endpoint=0x0812193C))
CLAIMS=dict(proof_scope='conditional_registered_stat_confirm_minimum_text',conditional_api_entry=True,complete_serializer_boundaries_proven=True,complete_selected_text_reads_proven=True,pointer_host_seeded=False,whole_candidate_identity_checked_by_parent_required=True,actual_runtime_execution_observed=False,full_story_reachability_claimed=False,all_prefix_natural_execution_claimed=False,universal_heap_or_irq_lifetime_proven=False,opaque_callee_effects_proven=False,whole_string_table_classified=False,padding_classified=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(left_ja='実GetMedicineItemEffectMessage入口。GetItemEffectTypeは通常ABIで15を返す有限条件。実subtract3/table index12からliteralを読み、StringCopyが全5byte/EOSを消費。item供給・自然使用・薬の全effectは未証明。',
 right_ja='実setup call0811F5A8が呼ぶCreateCancelConfirmWindows API入口。引数chooseMultiple=1とgPartyMenu.type=4を条件にする。全constructor/setup進行の完走は主張しない。実literalだけがtext pointerを生成する。',
 resource_ja='AddWindowは有効window0を返し、該当printer終端まで同epoch。opaque通常同期ABIと将来live fields以外のeffectsは未証明。glyph幅は未指定。',
 font_ja='既存font資源03003DD0=083E30E8、text制御byte/key halfwords=0。wrapperの実speed255とfont2から現hook/font dispatch/LDRBを通す。描画pixelは未検証。',
 memory_ja='各opaque境界後に将来read-before-write RAMだけを保存し、他はUnknownへ消去して同じ読取を確認。ABI callee-saved/stackは正常。',
 serializer_ja='固定公開pret/charmap.txtの日本語glyphとEOSを独立serialize。とくぼう5byteとけっ3byteは各実pointer起点から全byte一致。対象4byteだけを分類。')
EXTERNAL={(0x081259C2,0x081275A4),(0x08121908,0x08003CB0),(0x08121916,0x08004428),(0x08002D48,0x08002E78),(0x08005B0E,0x08006354),(0x08005B2C,0x08002FE4)}
class Machine(printer.Machine):
 def read(self,a,n):
  v=super().read(a,n)
  if self.pc==ROOT['left']['byte_read']:self.reads.append((a,n))
  return v
def serialize(value,sources):
 mapping={m.group(1):int(m.group(2),16)for m in re.finditer(r"^'([^']+)'\s*=\s*([0-9A-Fa-f]{2})\s*$",sources['pret-charmap.txt'].decode(),re.M)}
 need(all(c in mapping for c in value+'$'),'公開JP glyph/EOS完備')
 return bytes(mapping[c]for c in value+'$')
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'新scope公開source集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立公開source全文')
 need(b'GetMedicineItemEffectMessage = 0x81259BC | 1;'in sources['BPRJ.ld'],'実JP API公開export')
 c=sources['pret-party_menu.c'];need(b'CreateCancelConfirmWindows(sPartyMenuInternal->chooseMultiple);'in c and b'case ITEM_EFFECT_SPDEF_EV:'in c and b'StringCopy(gStringVar2, gText_ItemEffect_SpDef);'in c,'公開selector/実setup caller')
 need(b'currChar = *textPrinter->printerTemplate.currentChar;'in sources['pret-text.c'],'公開byte consumer')
 return True
def bind_semantics(raw,sources):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立命令意味 '+hex(i.address))
 for a,n,v in CORE_FIELDS:need(int.from_bytes(chunk(raw,a,n),'little')==v,'実printer dispatch field')
 for a,v in LITERALS.items():need(d.u32(raw,a)==v,'実完全登録pointer')
 for t in TEXTS:
  value=serialize(t['text_ja'],sources);need(identity(value)=={k:t[k]for k in('size','sha256')}and value[-1]==255 and all(x<248 for x in value[:-1]),'全serializer型境界');need(chunk(raw,t['address'],t['size'])==value,'現text全extent')
 d.signed(raw,FIXED_WINDOWS)
 return True
def preserve(live,writes=(),event=None):
 event=event or {};need(set(event)<= {'window_invalidated'},'閉じたepoch条件');need(event.get('window_invalidated',False)is False,'同window epochが必要')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and type(v)is int and n>0 and 0<=a<a+n<=1<<32,'有限書込')
  need(not any(a<b+z and b<a+n for b,z in live),'future-live clobber拒否')
def _compose(raw,case,boundary_live=None,opaque_writes=None,epoch_events=None,contract=None):
 need(case in('left','right')and type(case)is str,'二つの実APIだけ');need(contract is None or exact(contract,CONTRACT),'閉じた入力契約')
 root=ROOT[case];trace=[];mem={};boundaries=[];aggregates={};resource=False
 for a,n,v in((0x0203B01C,1,4),(0x03003DD0,4,0x083E30E8),(0x03003E90,1,0),(0x0300315C,2,0),(0x0300315E,2,0)):rt.setmem(mem,a,n,v)
 m=Machine(raw,root['api'],{0:1 if case=='right'else 0},mem,instructions=INS,trace=trace)
 while m.pc!=root['endpoint']:
  need(m.steps<10000,'有限実text path')
  if m.pc in INS:
   if m.pc==0x0812EDAC:need(resource,'新window生存が必要')
   m.step();continue
  site=(m.reg[14]&~1)-4;target=m.pc;need((site,target)in EXTERNAL,'閉じたcallee境界 '+hex(site)+' '+hex(target));value=rt.U;outputs=[]
  if target==0x081275A4:value=15
  elif target==0x08003CB0:value=0;resource=True
  elif target==0x08006354:m.write(0x03003E60,1,rt.U);outputs=[(0x03003E60,1,'unspecified')]
  index=len(boundaries);boundaries.append((site,target));trace.append(('boundary',index,0))
  if boundary_live is not None:
   need(index<len(boundary_live),'全opaque境界数');live=boundary_live[index];writes=(opaque_writes or {}).get(site,());event=(epoch_events or {}).get(site,{})
   preserve(live,writes,event)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(j*8))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   signature=(site,target,tuple(map(tuple,live)),tuple(outputs),value if rt.concrete(value)else None);aggregates[signature]=aggregates.get(signature,0)+1
  for reg in(0,1,2,3,12):m.reg[reg]=rt.U
  m.reg[0]=value;m.pc=m.reg[14]&~1;m.flag_pc=None
 t=TEXTS[0 if case=='left'else 1];need(m.reads==[(t['address']+j,1)for j in range(t['size'])],'両textを各実LDRBで全byte消費')
 return dict(steps=m.steps,reads=m.reads,trace=trace,boundaries=boundaries,aggregates=aggregates)
def compose_selected(raw,opaque_writes=None,epoch_events=None,contract=None):
 known={site for site,_ in EXTERNAL};need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known,'未知siteは黙殺しない');cases=[]
 for name in('left','right'):
  first=_compose(raw,name,contract=contract);live=engine.future_live(first['trace'],len(first['boundaries']));replay=_compose(raw,name,live,opaque_writes,epoch_events,contract)
  need(first['reads']==replay['reads']and first['boundaries']==replay['boundaries'],'非live RAM全消去後も同一読取');groups=[]
  for(site,target,fields,outputs,value),count in replay['aggregates'].items():groups.append(dict(site=site,target=target,count=count,required_fields=[dict(address=a,size=n)for a,n in fields],conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=value if value is not None else 'unspecified',normal_abi_return_required=True,effects_discharged=False))
  cases.append(dict(case=name,steps=first['steps'],read_bytes=len(first['reads']),read_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),conditional_call_groups=groups))
 return dict(status='PASS_TWO_REAL_API_COMPLETE_TEXTS',cases=cases,complete_consumed_bytes=8,all_hit_bytes_consumed=True,nonlive_ram_erased_at_each_boundary=True,pointer_host_seeded=False,actual_runtime_execution_observed=False)
def protected_windows(review):need(exact(review['windows'],FIXED_WINDOWS),'固定保護窓');return copy.deepcopy(FIXED_WINDOWS)
def evidence_template(hit):
 need(type(hit)is int and hit==HITS[0],'最小stock stat境界だけ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=hit,size=4),texts=copy.deepcopy(TEXTS),boundary_parts=[dict(address=hit,size=3,role='stat最後2glyphとEOS'),dict(address=hit+3,size=1,role='確認text先頭glyph')],actual_byte_consumers=[0x0800890C,0x0800580E],all_hit_bytes_consumed=True,**copy.deepcopy(CLAIMS))
def witness_geometry(evidence):need(exact(evidence,evidence_template(HITS[0])),'全witness field完全一致');return HITS[0],4
def make_review(raw,hits):
 by={h['address']:h for h in hits};need(HITS[0]in by,'元unknown1件')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=[copy.deepcopy(by[HITS[0]])],root=copy.deepcopy(ROOT),windows=copy.deepcopy(FIXED_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),texts=copy.deepcopy(TEXTS))
def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','texts'},'閉じたreview schema');need(type(review['schema_version'])is int and review['schema_version']==1,'厳密版')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現/旧診断分離')
 for key,value in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('texts',TEXTS)):need(exact(review[key],value),'review全field '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS];need(len(selected)==1 and exact(selected,review['hits']),'元unknown全field')
 h=selected[0];need(h['accepted']is False and h['classification']=='UNCLASSIFIED'and h['owner_candidates']==[]and type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','未知最小4byte');d.signed(raw,h)
 protected_windows(review);sources_bind(review,sources);bind_semantics(raw,sources);composition=compose_selected(raw)
 e=evidence_template(HITS[0]);a,n=witness_geometry(e);return[d.TypedRegion(a,a+n,KIND,e)],dict(status='PASS_REGISTERED_STAT_CONFIRM_BOUNDARY',count=1,hits=list(HITS),composition=composition,protected_windows=len(FIXED_WINDOWS),protected_bytes=sum(w['size']for w in FIXED_WINDOWS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):need(identity(raw)==inherited['candidate']==CANDIDATE,'current whole identity gate');return _regions(raw,inherited,review,sources)
