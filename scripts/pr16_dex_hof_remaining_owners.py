"""四つの実owner根・型境界をcurrent全ROMへ束縛する。"""
import hashlib,struct
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_reference_code as code
need,identity,chunk,u32=d.need,d.identity,d.chunk,d.u32
CANDIDATE=gaps.CANDIDATE
HITS={'36':0x09387B76,'38':0x0939075D,'55':0x093F0BF7,'70':0x09485CC2}
SCHEMAS={
'36':{'required_candidate','hit','kind','current_actual_owners','sources','texts','iv_first_row_path_conditions','root_hook','entry','rooted_paths','total_literal','iv_words_literal','iv_words_table','total_argument_and_call','iv_index_and_call','iv_append_call','byte_consumer','direct_calls'},
'38':{'required_candidate','hit','kind','current_actual_owners','sources','root','instruction_path','selected_instruction_window','literal_pool_included','full_function_range_classified'},
'55':{'required_candidate','hit','kind','current_actual_owners','sources','map_root','script','script_path','selected_command','success_script','source_serializer','root_consumer'},
'70':{'required_candidate','hit','kind','current_actual_owners','sources','species_id','species_key','species_transform','asset','asset_source_identity','selected_frame','table_literal','table_slot','oam_literal','oam','animations_literal','animation_slot','animation','size_table_literal','creation_size_table_literal','frame_size_slot','code_windows','direct_calls'},
}
def h16(raw,a):return int.from_bytes(chunk(raw,a,2),'little')
def exact(row,a,n):need(row['address']==a and row['size']==n,'finite selected source window')
def direct(raw,a,target):need(code.thumb_bl(chunk(raw,a,4),a)==target,'actual direct Thumb BL')
def literal(raw,instruction,slot,register):
 op=h16(raw,instruction);need(op&0xF800==0x4800 and(op>>8)&7==register and((instruction+4)&~3)+(op&255)*4==slot,'exact PC-relative literal load and register')
def sources(review,source_bytes):
 for s in review['sources']:
  need(set(s)=={'path','size','sha256','git_blob_sha'},'closed source identity schema')
  raw=source_bytes[s['path']]
  need(identity(raw)=={k:s[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==s['git_blob_sha'],'whole independent pinned source binding')
def common(raw,latest,inherited,key,r,source_bytes):
 need(set(r)==SCHEMAS[key]and r['required_candidate']==CANDIDATE,'closed review schema/current candidate')
 need(r['hit']['address']==HITS[key]and next(h for h in inherited['hits']if h['address']==HITS[key])==r['hit']and r['hit']['accepted']is False,'exact remaining inherited unknown')
 sources(r,source_bytes)
 for o in r['current_actual_owners']:gaps.bind_owner(raw,latest,o)
 d.signed(raw,r)
 for c in r.get('direct_calls',[]):direct(raw,c['address'],c['target'])
def _stage38_instruction_window(raw,r):
 root=r['root'];call=root['callnative'];entry=root['entry'];exact(call,0x9391a48,5);exact(entry,0x939066c,6)
 need(chunk(raw,call['address'],1)==bytes([35])and u32(raw,call['address']+1)==call['target']==entry['address']|1,'source CALLNATIVE target')
 exact(root['script'],0x9391a3c,33);need(root['source_script']=='script::mirage_choose'and root['source_function']=='MirageProduction_CommitSelection','explicit source function/root')
 rows=r['instruction_path'];gaps.thumb_path(raw,rows,entry['address']);win=r['selected_instruction_window'];exact(win,0x939075c,6)
 selected=[x for x in rows if win['address']<=x['address']<win['address']+win['size']]
 need([(x['address'],x['size'])for x in selected]==[(0x939075c,4),(0x9390760,2)]and r['literal_pool_included']is False and r['full_function_range_classified']is False,'minimal whole rooted instructions only')
 direct(raw,0x939075c,0x9391518);need(h16(raw,0x9390760)&0xF800==0x4800,'following instruction is LDR literal, not its pool')
 return dict(instruction_window=win,instructions=[{k:x[k]for k in('address','size')}for x in selected],root_verified=True,literal_pool_included=False,source_root=call)
def stage55(raw,r):
 root=r['map_root'];need((root['group'],root['map'],root['index'],root['event'])==(97,39,1,'BG'),'finite selected BG root')
 groups,group,maprow,header,events,bg=root['chain'];exact(groups,0x8054b0c,4)
 for row in (groups,group,maprow):need(row['size']==4 and u32(raw,row['address'])==row['value'],'actual root pointer')
 need(group['address']==groups['value']+4*97 and maprow['address']==group['value']+4*39 and header['address']==maprow['value']and header['size']==8 and events['address']==u32(raw,header['address']+4)==header['events'],'exact finite map chain')
 need(chunk(raw,bg['address']+5,1)==bytes([0]),'BG kind0 is a script pointer, not packed hidden-item data')
 need(events['size']==20 and chunk(raw,events['address']+3,1)[0]==events['selected_count']>1 and u32(raw,events['address']+16)==events['table']and bg['address']==events['table']+12 and bg['size']==12 and bg['script_field']==bg['address']+8 and u32(raw,bg['script_field'])==bg['script']==0x93f0bd0,'complete BG script field ABI')
 exact(r['script'],bg['script'],61);rows=r['script_path'];layout=[(0,1,105),(1,5,26),(6,5,35),(11,5,33),(16,6,6),(22,5,26),(27,5,26),(32,2,9),(34,5,33),(39,6,6)]
 need([(x['address']-bg['script'],x['size'],x['opcode'])for x in rows]==layout,'source serialized hidden-item opcode/operand geometry')
 for x in rows:need(chunk(raw,x['address'],1)[0]==x['opcode'],'actual event opcode')
 need(chunk(raw,0x93f0bf0,2)==bytes([9,0]),'source CALLSTD0 known continuation')
 need(chunk(raw,0x93f0be0,2)==bytes([6,1]) and u32(raw,0x93f0be2)==0x93f0c0b and chunk(raw,0x93f0c0b,2)==bytes([107,2]),'first branch has source conditional fallthrough or explicit terminal target')
 need(struct.unpack('<H',chunk(raw,0x93f0bd4,2))[0]==4920 and struct.unpack('<H',chunk(raw,0x93f0be9,2))[0]==988 and struct.unpack('<H',chunk(raw,0x93f0bee,2))[0]==1,'selected exact source hidden-item flag/item/quantity scalars')
 cmd=r['selected_command'];exact(cmd,0x93f0bf7,6);need(cmd['opcode']==6 and cmd['condition']==1 and chunk(raw,cmd['address'],2)==bytes([6,1])and cmd['pointer_field']==cmd['address']+2 and u32(raw,cmd['pointer_field'])==cmd['pointer_value']==0x93f0bff,'exact condition byte and independent full pointer operand')
 exact(r['success_script'],cmd['pointer_value'],12);need(r['hit']['address']==cmd['address']and r['hit']['size']==4,'only opcode/condition/half-pointer crossing')
 c=r['root_consumer'];slot=c['dispatch_slot'];exact(slot,0x8162cc4+6*4,4);need(u32(raw,slot['address'])==slot['value']==0x80698ad,'actual JP opcode6 handler slot')
 exact(c['handler'],0x80698ac,54);exact(c['read_word'],0x80691d0,48);exact(c['goto'],0x8069190,4)
 direct(raw,0x80698ba,0x80691d0);direct(raw,0x80698d6,0x8069190)
 need(h16(raw,0x80698b2)&0xF800==0x7800,'condition is one LDRB scalar')
 return dict(command=cmd,opcode_bytes=1,condition_bytes=1,pointer_offset=2,pointer_bytes=4,root_verified=True,hit=r['hit'])
def _stage36_byte_consumers(raw,r):
 left,right=r['texts'];exact(left,0x9387b74,5);exact(right,0x9387b79,5)
 need(left['address']+left['size']==right['address']and r['hit']['address']==right['address']-3,'adjacent complete byte texts crossing')
 for t in(left,right):
  b=chunk(raw,t['address'],t['size']);need(b[-1]==255 and 255 not in b[:-1]and not set(b)&{248,249,252,253},'finite EOS-terminated text without controls/placeholders')
 hook=r['root_hook'];exact(hook,0x81378b4,8);need(struct.unpack('<HHI',chunk(raw,hook['address'],8))==(0x4b00,0x4718,0x9378485)and hook['target']==0x9378485,'current summary entry trampoline')
 exact(r['entry'],0x9378484,12)
 need(len(r['rooted_paths'])==2 and[r[-1]['address']for r in r['rooted_paths']]==[0x9379dd0,0x9379cb0],'both independent consumer paths required')
 for rows in r['rooted_paths']:gaps.thumb_path(raw,rows,0x9378484)
 for name,slot,target,pc,reg in [('total_literal',0x9379e5c,left['address'],0x9379dca,2),('iv_words_literal',0x9379d2c,right['address'],0x9379ce2,3)]:
  exact(r[name],slot,4);need(u32(raw,slot)==r[name]['value']==target,'separate actual string literal');literal(raw,pc,slot,reg)
 table=r['iv_words_table'];exact(table,right['address'],96);need(table['count']==6 and table['stride']==16,'source IV words fixed6x16')
 for i in range(6):
  b=chunk(raw,table['address']+16*i,16);e=b.find(bytes([255]));need(0<e<16 and b[e+1:]==bytes(15-e),'each IV row has finite EOS and zero padding')
 need(chunk(raw,right['address'],5)==chunk(raw,table['address'],5),'first selected row whole text')
 for name,a,n in [('total_argument_and_call',0x9379dca,10),('iv_index_and_call',0x9379cc4,42),('iv_append_call',0x9379cae,6),('byte_consumer',0x9379c0c,46)]:exact(r[name],a,n)
 need(h16(raw,0x9379ce4)==0x0132 and h16(raw,0x9379ce6)==0x18d2,'IV selected index stride16 and base add')
 direct(raw,0x9379dd0,0x9379c0c);direct(raw,0x9379cb0,0x9379c0c)
 need(h16(raw,0x9379c24)==0x7815 and h16(raw,0x9379c26)==0x2dff,'append consumer reads u8 from r2 and checks EOS')
 return dict(left=left,right=right,both_text_consumers_verified=True,source_pointer_interpretation=False,root_verified=True)
def _stage70_icon_frame(raw,r):
 need(r['species_id']==1645 and r['species_key']=='SPECIES_KEY_GRENINJA_MEGA','finite source species selector')
 a=r['asset'];exact(a,0x9485c48,1024);need(r['asset_source_identity']==dict(role='ICON',size=a['size'],sha256=a['sha256']),'entire source raw icon identity')
 literal(raw,0x8096a5c,0x8096a7c,2);exact(r['table_literal'],0x8096a7c,4);need(u32(raw,0x8096a7c)==r['table_literal']['value']==0x955896c,'current Stage75 table root')
 slot=r['table_slot'];exact(slot,0x955896c+4*1645,4);need(u32(raw,slot['address'])==slot['value']==a['address'],'selected current species icon pointer')
 frame=r['selected_frame'];exact(frame,a['address'],512);need((frame['width'],frame['height'],frame['bits_per_pixel'],frame['frame_index'])==(32,32,4,0)and frame['size']==32*32//2 and d.contains(frame['address'],frame['address']+512,r['hit']['address'],4),'selected exact raw4bpp frame')
 exact(r['oam_literal'],0x80968e0,4);need(u32(raw,0x80968e0)==r['oam_literal']['value']==r['oam']['address']==0x839c570,'actual CreateMonIcon OAM pointer')
 oam=chunk(raw,0x839c570,8);need((oam[1]>>6,oam[3]>>6)==(r['oam']['shape'],r['oam']['oam_size'])==(0,2),'actual shape0 size2 is32x32')
 exact(r['size_table_literal'],0x8096d00,4);need(u32(raw,0x8096d00)==r['size_table_literal']['value']==0x839c5f0,'actual size table root')
 literal(raw,0x8096d52,0x8096df4,2);exact(r['creation_size_table_literal'],0x8096df4,4);need(u32(raw,0x8096df4)==r['creation_size_table_literal']['value']==r['size_table_literal']['value'],'creation and update use same actual frame size table')
 size=r['frame_size_slot'];exact(size,0x839c5f0+0*8+2*2,2);need(h16(raw,size['address'])==size['value']==512,'actual frame byte count')
 exact(r['animations_literal'],0x80968e4,4);need(u32(raw,0x80968e4)==r['animations_literal']['value']==r['animation_slot']['address']==0x839c5b4,'actual animations root')
 anim=r['animation'];need(u32(raw,0x839c5b4)==r['animation_slot']['value']==anim['address'],'animation0 pointer');exact(anim,0x839c578,12)
 words=struct.unpack('<6H',chunk(raw,anim['address'],12));need(list(words[::2])==anim['frame_indices']==[0,1,65534]and anim['first_frame']==0,'source two-frame animation0, beginning at frame0')
 need(h16(raw,0x8096a5e)==0x0081 and h16(raw,0x8096a62)==0x680a,'index is4byte pointer slot')
 need(h16(raw,0x8096de0)==0x6851 and h16(raw,0x8096de2)==0x6019 and h16(raw,0x8096cba)==0x68e0,'raw image stored and read at sprite+12')
 return dict(asset=a,selected_frame=frame,species_id=1645,table_slot=slot,root_verified=True,actual_screen_rendered=False)
# Every final validator below includes both geometry and complete finite roots.
VALIDATORS={}
def regions(raw,latest,inherited,review,source_bytes):
 need(identity(raw)==latest['candidate']==CANDIDATE,'whole exact current0641 candidate; diagnostic formal never accepted')
 need(set(review)==set(HITS),'closed four owner scope')
 regions=[];proof={}
 for k in ('36','38','55','70'):
  r=review[k];common(raw,latest,inherited,k,r,source_bytes)
  if k=='70':
   import json
   contract=json.loads(source_bytes['content/modernization/p04_species_runtime_contract.json']);record=next(x for x in contract['records']if x['id']==1645);asset=next(x for x in record['asset_evidence']if x['role']=='ICON')
   need(record['species_key']==r['species_key'] and {p:asset[p]for p in('role','size','sha256')}==r['asset_source_identity'],'independent pinned source contract whole ICON identity')
  e=VALIDATORS[k](raw,r)
  if k=='38':start,size=e['instruction_window']['address'],e['instruction_window']['size']
  elif k=='70':start,size=e['selected_frame']['address'],e['selected_frame']['size']
  else:start,size=r['hit']['address'],4
  regions.append(d.TypedRegion(start,start+size,r['kind'],e));proof[k]=dict(status='PASS_EXACT_ROOTED_OWNER_REFERENCE',evidence=e)
 return regions,proof


def stage36(raw,r):
 result=_stage36_byte_consumers(raw,r);c=r['iv_first_row_path_conditions']
 need(c==dict(mode=1,trained_bit=0,value_low8=31,selected_index=0,selected_address=0x9387b79,source_function='append_stat_judge/iv_judge_word',dynamic_playback_claimed=False),'explicit feasible first-row selection conditions')
 rows=r['rooted_paths'][1];required=[0x9379c70,0x9379c72,0x9379ca2,0x9379ca6,0x9379ca8,0x9379caa,0x9379cc4,0x9379cc6,0x9379cc8,0x9379cca,0x9379cea,0x9379cec,0x9379ce2,0x9379ce4,0x9379ce6,0x9379ce8,0x9379cae,0x9379cb0]
 need(all(a in [x['address']for x in rows]for a in required),'entire index0 selection-to-append path')
 # mode==1; trained bit test is clear, so r2=0; IV31 copies that0 into index r6.
 need(h16(raw,0x9379c70)==0x2e01 and h16(raw,0x9379ca2)==0x001a and h16(raw,0x9379ca6)==0x4032 and h16(raw,0x9379ca8)==0x4233,'same mode1 mask feeds zero-bit branch and r2')
 need(h16(raw,0x9379cc8)==0x2c1f and h16(raw,0x9379cea)==0x0016,'IV31 selects proven zero index')
 need(h16(raw,0x9379ce4)==0x0132 and h16(raw,0x9379ce6)==0x18d2 and h16(raw,0x9379cae)==0x0038,'index0 base pointer remains r2 at append')
 direct(raw,0x9379cb0,0x9379c0c);result['first_row_selection_verified']=True;return result

def stage38(raw,r):
 result=_stage38_instruction_window(raw,r);root=r['root'];m=root['map_root'];need((m['group'],m['map'],m['index'],m['event'])==(31,1,0,'OBJECT'),'finite Mirage map31/1 object0 root')
 groups,group,maprow,header,events,obj=m['chain'];exact(groups,0x8054b0c,4)
 for row in(groups,group,maprow):need(row['size']==4 and u32(raw,row['address'])==row['value'],'actual map root pointer')
 need(group['address']==groups['value']+31*4 and maprow['address']==group['value']+4 and header['address']==maprow['value']and u32(raw,header['address']+4)==header['events']==events['address'],'finite current Mirage map chain')
 need(events['size']==20 and chunk(raw,events['address'],1)[0]==events['selected_count']>0 and u32(raw,events['address']+4)==events['table']and obj['address']==events['table']and obj['size']==24 and obj['script_field']==obj['address']+16 and u32(raw,obj['script_field'])==obj['script']==0x9391a08,'current object script root is reception')
 rows=root['script_path'];sizes={106:1,90:1,15:6,9:2,33:5,6:6,35:5,37:3,39:1}
 need(rows[0]['address']==obj['script']and rows[-1]['address']==root['callnative']['address']and len(rows)==14,'complete reception/enter/choose finite path')
 for i,row in enumerate(rows):
  a,op=row['address'],row['opcode'];need(op in sizes and row['size']==sizes[op]and chunk(raw,a,1)==bytes([op]),'exact source script opcode extent')
  if op==6:
   need(chunk(raw,a+1,1)==bytes([1]),'only source equal conditional');targets={a+6,u32(raw,a+2)}
  else:targets={a+row['size']}
  if i+1<len(rows):need(rows[i+1]['address']in targets,'each rooted source bytecode edge')
 need(u32(raw,0x9391a19)==0x9391a24 and u32(raw,0x9391a30)==0x9391a3c,'conditional reception→enter→choose')
 need(chunk(raw,0x9391a10,2)==bytes([9,5])and chunk(raw,0x9391a42,2)==bytes([9,4])and h16(raw,0x9391a45)==41 and chunk(raw,0x9391a47,1)==bytes([39]),'source msgbox standards, party-selection special41, resumed waitstate')
 c=root['callnative_consumer'];exact(c['dispatch_slot'],0x8162cc4+35*4,4);need(u32(raw,c['dispatch_slot']['address'])==c['dispatch_slot']['value']==0x8069855,'JP actual opcode35 dispatch')
 exact(c['handler'],0x8069854,16);exact(c['read_word'],0x80691d0,48);exact(c['call_via_r0_veneer'],0x81c7ac8,2)
 direct(raw,0x8069856,0x80691d0);direct(raw,0x806985a,0x81c7ac8);need(h16(raw,0x81c7ac8)==0x4700,'whole script u32 return is called via BX r0')
 result['map_object_and_event_consumer_root_verified']=True;return result

def gender_leaf_preserves_r4(raw):
 """Static ARMv4T CFG and destination audit, not execution or native emulation."""
 valid=set(range(0x803eef8,0x803ef32,2))|{0x803ef38,0x803ef3a,0x803ef3c}
 todo=[0x803eef8];seen=set();returns=0
 while todo:
  a=todo.pop()
  if a in seen:continue
  need(a in valid,'gender leaf instruction edge excludes literal pool');seen.add(a);op=h16(raw,a);nxt=[a+2];dest=None
  if op==0xb500:need(a==0x803eef8,'only pushLR')
  elif op==0xbc02:need(a==0x803ef3a,'only pop return address into r1')
  elif op==0x4708:need(a==0x803ef3c,'only BX returned LR');returns+=1;nxt=[]
  elif op==0x46c0:pass
  elif op&0xF000==0xD000:
   need(((op>>8)&15)<14,'ordinary conditional leaf branch');off=op&255;off-=256 if off&128 else 0;nxt.append(a+4+2*off)
  elif op&0xF800==0xE000:
   off=op&2047;off-=2048 if off&1024 else 0;nxt=[a+4+2*off]
  elif op&0xE000==0:dest=op&7
  elif op&0xE000==0x2000:
   if op&0xF800!=0x2800:dest=(op>>8)&7
  elif op&0xFC00==0x4000:
   if(op>>6)&15 not in(8,10,11):dest=op&7
  elif op&0xF800==0x4800:dest=(op>>8)&7
  elif op&0xF800 in(0x6800,0x7800,0x8800):dest=op&7
  else:raise ValueError('unsupported store/call/indirect opcode in gender leaf')
  need(dest is None or dest!=4,'gender leaf never overwrites saved species r4');todo+=nxt
 need(returns==1 and seen==valid,'all bounded leaf instructions classified and one matching return')
 return len(seen)

def transform1645(raw,t):
 need(t['species_id']==1645 and t['required_candidate']==CANDIDATE,'same transform species/candidate')
 direct(raw,0x8096a88,0x8096988);exact(t['call'],0x8096a88,4);exact(t['hook'],0x8096988,8)
 need(struct.unpack('<HHI',chunk(raw,0x8096988,8))==(0x4a00,0x4710,0x9fd9f9d)and t['hook']['target']==0x9fd9f9d,'actual r2 LDR/BX species transform hook')
 exact(t['entry'],0x9fd9f9c,22);literal(raw,0x9fd9f9c,0x9fda050,3);exact(t['maximum_species_literal'],0x9fda050,4)
 need(u32(raw,0x9fda050)==t['maximum_species_literal']['value']==1670 and 1645<=1670,'current expanded maximum admits1645')
 g=t['prefix_path'];gaps.thumb_path(raw,g,0x9fd9f9c);need(g[-1]['address']==0x9fd9ff0,'bound prefix through delegate call')
 # These comparisons route1645 past Egg/Unown unchanged, keeping it in r4.
 need(h16(raw,0x9fd9fa0)==0x0004 and h16(raw,0x9fd9faa)==0x4298 and h16(raw,0x9fd9fae)==0x28c9,'species copied into r4 and special species checks')
 exact(t['gender_delegate_literal'],0x9fda058,4);need(u32(raw,0x9fda058)==t['gender_delegate_literal']['value']==0x803eef9,'exact gender callee literal');literal(raw,0x9fd9fee,0x9fda058,3)
 direct(raw,0x9fd9ff0,0x9fda088);exact(t['gender_veneer'],0x9fda088,2);need(h16(raw,0x9fda088)==0x4718,'explicit BX r3 delegate')
 need([(w['address'],w['size'])for w in t['gender_consumer_windows']]==[(0x803eef8,58),(0x803ef38,6)],'complete nonpool gender leaf windows');gender_leaf_preserves_r4(raw)
 need(len(t['post_gender_paths'])==2 and all(len(p)>2 and[p[0]['address'],p[1]['address']]==[0x9fd9ff4,0x9fd9ff6]for p in t['post_gender_paths'])and {p[2]['address']for p in t['post_gender_paths']}=={0x9fd9ff8,0x9fda024},'both distinct equality branch successors required exactly once')
 for rows in t['post_gender_paths']:gaps.thumb_path(raw,rows,0x9fd9ff4);need(rows[-1]['address']==0x9fd9fde,'both static paths return selected species')
 need(h16(raw,0x9fd9ff4)==0x28fe and h16(raw,0x9fd9ff8)==0x23d2 and h16(raw,0x9fd9ffa)==0x009b and h16(raw,0x9fd9ffc)==0x429c,'female branch compares species with840')
 for row,a,v in zip(t['post_gender_literals'],[0x9fda068,0x9fda06c,0x9fda070],[841,957,1005]):exact(row,a,4);need(u32(raw,a)==row['value']==v and 1645!=v,'remaining female/display substitutions do not select1645')
 need(1645>840 and h16(raw,0x9fd9fde)==0x0020,'both gender paths reach r0=r4 return')
 exact(t['return_window'],0x9fd9fde,8);need([h16(raw,a)for a in [0x9fd9fe0,0x9fd9fe2,0x9fd9fe4]]==[0xbc10,0xbc02,0x4708],'callee restores r4 after fixing return species and returns normally')
 return True

def stage70(raw,r):
 result=_stage70_icon_frame(raw,r);transform1645(raw,r['species_transform']);result['species_transform_preserves1645']=True;return result

VALIDATORS={'36':stage36,'38':stage38,'55':stage55,'70':stage70}
