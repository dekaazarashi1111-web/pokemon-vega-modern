"""stock参加制限max2/3の両登録textが跨ぐ4byteだけを型分類する。"""
import copy,hashlib,json
import pr16_dex_hof_choose_limit_roots as prior
import pr16_dex_hof_donor as d
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as text
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE,DIAGNOSTIC=prior.CANDIDATE,prior.DIAGNOSTIC
KIND='registered_stock_choose_limit_minimum_text'
TYPE_CATEGORY='data'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x083DDEFC,)
HELD_HITS=()
INS,EXTERNAL,OBJECT,Machine=prior.INS,prior.EXTERNAL,prior.OBJECT,prior.Machine
exact,encoded,encode_text,preserve=prior.exact,prior.encoded,prior.encode_text,prior.preserve
SOURCE_IDS={k:copy.deepcopy(v)for k,v in prior.SOURCE_IDS.items()if k!='cfru-overworld_strings.string'}
ROOT=dict(copy.deepcopy(prior.ROOT),selected_indices=[1,2])
CLAIMS=dict(copy.deepcopy(prior.CLAIMS),proof_scope='conditional_registered_stock_choose_limit_minimum_text')
CONTRACT=copy.deepcopy(prior.CONTRACT)
CONTRACT['selection_ja']='GetNumMonsOnTeamInFrontierのu8結果2/3。facility判定非zero、先頭max個の選択slotは有効な非zero。text pointerは実table LDR/stack storeだけで生成する。'
CONTRACT['minimum_ja']='stock境界083DDEFCの4byteだけ。max3 text末尾FC09/EOS3byteとmax2 text先頭1byteを別々の正の登録caseで読む。'
CONTRACT['serializer_ja']='公開charmapとFC09/EOS単byte文法で、実登録起点から各27byteを独立encodeする。日本語3びき/2ひきは現候補で全extent一致を必須とし、英語版配置や名前だけを根にしない。'
TEXTS=[dict(address=0x083DDEE4,maximum=3,size=27,sha256='ac6b97db77c122b6131e23e29fcb1ebbe0c09480bb8ca57b04ba7aaca182e724',source_label='gOtherText_NoMoreThreePoke',text='さんか できる ポケモンは\\n3びき まで です！[FC][09]'),
 dict(address=0x083DDEFF,maximum=2,size=27,sha256='2656947a13326f2f9563249b36c591cdfb61a77eed40af2bdb67628e86c1f8fc',source_label='gOtherText_NoMoreTwoPoke',text='さんか できる ポケモンは\\n2ひき まで です！[FC][09]')]
DATA_FIELDS=[x for x in prior.DATA_FIELDS if not 0x0916901C<=x[0]<0x09169030]+[(0x09169020,4,0x083DDEFF),(0x09169024,4,0x083DDEE4)]
FIXED_WINDOWS=[copy.deepcopy(w)for w in prior.FIXED_WINDOWS if w['address']not in(0x091492B2,0x0916901C,0x09169028)]+[dict(address=t['address'],size=t['size'],sha256=t['sha256'])for t in TEXTS]+[
 dict(address=0x09169020,size=4,sha256='ed47ddf084c2fbcc0e80eef9e920e139ba1bf3ea6d0f2ebcac7a3db214981c72'),
 dict(address=0x09169024,size=4,sha256='09c05c571e957303716f69a5b5de4d4822b18a9da6fcd2667c0ccfb869e91c18')]
FIXED_WINDOWS.sort(key=lambda r:(r['address'],r['size']))
def bind_semantics(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立Thumb意味 '+hex(i.address))
 for a,n,value in DATA_FIELDS:need(int.from_bytes(chunk(raw,a,n),'little')==value,'完全登録pointer/field幅 '+hex(a))
 for row in TEXTS:
  value=encode_text(row['text']);need(identity(value)=={k:row[k]for k in('size','sha256')}and len(value)==27,'独立日本語serializer全extent')
  need(value[-3:]==bytes((252,9,255))and 255 not in value[:-1],'FC09と完全EOS境界')
  need(chunk(raw,row['address'],row['size'])==value,'現候補の登録起点から全serializer一致')
 d.signed(raw,FIXED_WINDOWS)
 return True
def _compose(raw,maximum,boundary_live=None,opaque_writes=None,epoch_events=None,contract=None):
 need(type(maximum)is int and maximum in(2,3),'有限有効maxだけ')
 need(contract is None or exact(contract,CONTRACT),'閉じた条件付きAPI契約')
 mem={};trace=[];boundaries=[];aggregates={};removed=0
 for a,n,v in((0x0203B01C,1,4),(0x0203B010,4,OBJECT),(OBJECT+12,1,0),(OBJECT+13,1,1),
  (0x03003DD0,4,0x083E30E8),(0x03003E90,1,0),(0x0300315C,2,0),(0x0300315E,2,0)):
  rt.setmem(mem,a,n,v)
 for j in range(maximum):rt.setmem(mem,0x0203C6C8+j,1,j+1)
 m=Machine(raw,ROOT['api_entry'],{0:0},mem,instructions=INS,trace=trace)
 while m.pc!=ROOT['endpoint']:
  if m.pc in INS:m.step();continue
  target=m.pc;site=(m.reg[14]&~1)-4;key=(site,target)
  need(key in EXTERNAL,'閉じた実opaque呼出site')
  value=rt.U;outputs=[];object_live=removed<2
  def put(a,n,v):m.write(a,n,v);outputs.append((a,n,v if rt.concrete(v)else 'unspecified'))
  if target==0x09101728:value=maximum
  elif target in(0x091269A4,0x090D8B60,0x0800564C):value=1
  elif target==0x09099E16:
   need(m.reg[1]==0 and m.reg[2]==6,'条件付きmemsetの正確な引数')
   for j in range(6):put(m.reg[0]+j,1,0)
   value=m.reg[0]
  elif target==0x080F8908:value=255
  elif target==0x081224B0:
   need(m.reg[0]==OBJECT+12+removed and removed<2,'既存補助windowの正確なfield')
   need(m.read(m.reg[0],1)==removed,'補助window0/1の妥当性条件')
   put(m.reg[0],1,255);removed+=1
  elif target==0x08006354:put(0x03003E60,1,rt.U)
  index=len(boundaries);boundaries.append(key);trace.append(('boundary',index,0))
  if boundary_live is not None:
   need(index<len(boundary_live),'同一boundary数');live=boundary_live[index]
   writes=(opaque_writes or {}).get(site,());event=(epoch_events or {}).get(site,{})
   preserve(live,writes,event,object_live)
   for a,n,v in writes:
    for j in range(n):m.mem[a+j]=(v>>(j*8))&255
   kept={a+j for a,n in live for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
   signature=(site,target,tuple(map(tuple,live)),tuple(outputs),value if rt.concrete(value)else None,object_live)
   aggregates[signature]=aggregates.get(signature,0)+1
  for r in(0,1,2,3,12):m.reg[r]=rt.U
  m.reg[0]=value;m.pc=m.reg[14]&~1;m.flag_pc=None
 row=next(r for r in TEXTS if r['maximum']==maximum)
 need(m.reads==[(row['address']+j,1)for j in range(row['size'])],'各公開text27byte全てを実LDRBで消費')
 need(m.pc==ROOT['endpoint']and len(boundaries)==62 and removed==2,'EOS処理後printer実復帰まで閉鎖')
 return dict(steps=m.steps,reads=m.reads,trace=trace,boundaries=boundaries,aggregates=aggregates)
def compose_selected(raw,opaque_writes=None,epoch_events=None,contract=None):
 known={s for s,_ in EXTERNAL}
 need(set(opaque_writes or {})<=known and set(epoch_events or {})<=known,'未実行siteへの契約を黙殺しない')
 cases=[]
 for maximum in(2,3):
  first=_compose(raw,maximum,contract=contract);live=text.future_live(first['trace'],len(first['boundaries']))
  replay=_compose(raw,maximum,live,opaque_writes,epoch_events,contract)
  need(first['reads']==replay['reads']and first['boundaries']==replay['boundaries'],'非live RAM全消去後も同一の登録/読取')
  groups=[]
  for(site,target,fields,outputs,value,object_live),count in replay['aggregates'].items():
   allbytes={a+j for a,n in fields for j in range(n)};made={a+j for a,n,_ in outputs for j in range(n)}
   groups.append(dict(site=site,target=target,count=count,required_fields=[dict(address=a,size=n)for a,n in text.coalesce(allbytes-made)],
    produced_memory_ranges=[dict(address=a,size=n)for a,n in text.coalesce(allbytes&made)],conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],
    return_value=value if value is not None else 'unspecified',object_epoch_required=object_live,window6_epoch_required=True,normal_abi_return_required=True,effects_discharged=False))
  cases.append(dict(maximum=maximum,table_index=maximum-1,steps=first['steps'],complete_consumed_bytes=27,boundary_count=len(first['boundaries']),
   read_trace_identity=identity(json.dumps(first['reads'],separators=(',',':')).encode()),conditional_call_groups=groups))
 return dict(status='PASS_CONDITIONAL_TWO_REGISTERED_STOCK_TEXTS',cases=cases,complete_consumed_bytes=54,
  all_two_eos_consumed=True,all_two_fc09_operands_consumed=True,printer_return_observed_in_model=True,
  root_verified=True,pointer_host_seeded=False,nonlive_ram_erased_at_each_boundary=True,synthetic_contract_execution=True,
  actual_runtime_execution_observed=False,whole_prefix_natural_reachability_proven=False)
def protected_windows(review):
 need(exact(review['windows'],FIXED_WINDOWS),'固定新scope保護窓');return copy.deepcopy(FIXED_WINDOWS)
def sources_bind(review,sources):
 need(set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'閉じた公開source集合')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'独立公開source全文')
 c=sources['cfru-party_menu.c'].decode()
 need('sChoosePokemonMaxStrings[PARTY_SIZE - 1]'in c and '*strPtr = sChoosePokemonMaxStrings[max - 1];'in c and 'DisplayPartyMenuMessage(string, 1);'in c,'登録table/型consumer意味')
 start=c.index('sChoosePokemonMaxStrings[PARTY_SIZE - 1]');array=c[start:c.index('};',start)]
 expected=['gOtherText_NoMoreOnePoke','gOtherText_NoMoreTwoPoke','gOtherText_NoMoreThreePoke','gOtherText_NoMoreFourPoke','gOtherText_NoMoreFivePoke']
 need([line.strip().rstrip(',')for line in array.splitlines()[2:]]==expected,'独立公開table登録順')
 mapping={}
 for line in sources['cfru-charmap.tbl'].decode('utf-8-sig').splitlines():
  if '='in line:
   a,b=line.split('=',1)
   if len(a)==2:mapping[b]=int(a,16)
 need(exact(mapping,prior.CHARSET),'公開日本語charmap全文')
 need(b'"PAUSE_UNTIL_PRESS": ["FC", "09"]'in sources['cfru-string.py'],'公開FC09制御serializer')
 need(b'PartyMenuPrintText(str);'in sources['pret-party_menu.c']and b'currChar = *textPrinter->printerTemplate.currentChar;'in sources['pret-text.c'],'実byte reader意味')
 return True
def evidence_template(hit):
 need(type(hit)is int and hit==HITS[0],'新stock境界1件だけ')
 return dict(root=copy.deepcopy(ROOT),root_verified=True,classified_window=dict(address=hit,size=4),texts=copy.deepcopy(TEXTS),
  boundary_parts=[dict(address=hit,size=3,role='max3のFC09とEOS'),dict(address=hit+3,size=1,role='max2登録text先頭')],
  all_hit_bytes_consumed=True,actual_byte_consumers=[ROOT['text_byte_read'],ROOT['control_operand_read']],**copy.deepcopy(CLAIMS))
def witness_geometry(evidence):
 need(exact(evidence,evidence_template(HITS[0])),'独立固定witness全field');return HITS[0],4
def make_review(raw,hits):
 by={h['address']:h for h in hits};need(HITS[0]in by,'親unknown行')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
  source_bindings=copy.deepcopy(SOURCE_IDS),hits=[copy.deepcopy(by[HITS[0]])],root=copy.deepcopy(ROOT),
  windows=copy.deepcopy(FIXED_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),texts=copy.deepcopy(TEXTS))
def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','root','windows','claims','input_contract','texts'},'閉じた新review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'厳密整数版')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'現/旧診断identity分離')
 for key,wanted in(('root',ROOT),('claims',CLAIMS),('input_contract',CONTRACT),('texts',TEXTS)):need(exact(review[key],wanted),'新review全field '+key)
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(len(selected)==1 and exact(selected,review['hits']),'元のunknown全field')
 h=selected[0];need(h['accepted']is False and h['classification']=='UNCLASSIFIED'and h['owner_candidates']==[]and type(h['size'])is int and h['size']==4 and h['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','新所有者外4byteだけ');d.signed(raw,h)
 protected_windows(review);sources_bind(review,sources);bind_semantics(raw);composition=compose_selected(raw)
 evidence=evidence_template(HITS[0]);a,n=witness_geometry(evidence)
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_ONE_STOCK_BOUNDARY_TWO_REGISTERED_TEXTS',count=1,hits=list(HITS),composition=composition,
  protected_windows=len(FIXED_WINDOWS),protected_bytes=sum(w['size']for w in FIXED_WINDOWS),source_bindings=copy.deepcopy(SOURCE_IDS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'正式current whole identity gate');return _regions(raw,inherited,review,sources)
