#!/usr/bin/env python3
"""未分類行の有限serializer/consumer根。owner名から型を推定しない。"""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_data as prior
import pr16_dex_hof_reference_code as code
ROOT=Path(__file__).resolve().parents[1]
REVIEW='content/modernization/pr16_dex_hof_reference_gaps_review.json'
REVIEW_ID = {'size': 194252, 'sha256': '61eee6953d3c0daebfa332de2497d3b10058798edcd9ed223e21ce943c8c4ea4'}
CANDIDATE=prior.CANDIDATE
need,identity,chunk=d.need,d.identity,d.chunk


def source_proof(review,sources,root=ROOT):
 bindings={}
 for name,expected in review['source_bindings'].items():
  if 'local'in expected:raw=sources[expected['local']]
  elif name=='vendor/upstream/CFRU-JP/include/battle.h':raw=sources['cfru-trainer-battle.h']
  else:
   path=root/name;need(path.is_file()and not path.is_symlink(),'regular fixed semantic source');raw=path.read_bytes()
  need(identity(raw)=={k:expected[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected['git_blob_sha'],'whole pinned source and Git blob')
  bindings[name]=expected
 return bindings


def bind_owner(raw,latest,expected):
 owners={o['name']:o for o in latest['placement']['owner_byte_audit']}
 actual=owners.get(expected['name'])
 need(actual is not None and actual==expected,'latest actual owner record, never nominal owner hash')
 need(identity(chunk(raw,actual['address'],actual['size']))==dict(size=actual['size'],sha256=actual['after_sha256']),'whole actual owner bytes')
 return actual


def trainer_regions(raw,latest,inherited,review):
 owner=bind_owner(raw,latest,review['current_actual_owner'])
 need(review['required_candidate']==CANDIDATE,'fixed current trainer target')
 header=review['header'];d.signed(raw,header)
 value=chunk(raw,header['address'],header['size'])
 need(header['address']==owner['address']and header['size']==64 and value[:8]==b'VEGA17\0\0'and struct.unpack_from('<II',value,8)==(1,owner['size']),'whole source VEGA17 header and version/size')
 table=review['trainer_table'];d.signed(raw,table)
 need(table['count']==917 and table['stride']==32 and table['size']==917*32 and table['address']==153226568 and d.contains(owner['address'],owner['address']+owner['size'],table['address'],table['size']),'explicit historical table symbol and exact bounds')
 need(table['layout']=={k:prior.LAYOUT[k]for k in table['layout']}and set(table['layout'])=={'name_offset','name_size','item_offset','item_size','party_pointer_offset','origin_offset','origin_size'},'independent JP trainer scalar ABI')
 need([r['index']for r in table['rows']]==[191,414],'two retained original trainer rows')
 previous=json.loads((ROOT/prior.REVIEW).read_bytes())
 need(identity((ROOT/prior.REVIEW).read_bytes())==prior.REVIEW_ID,'accepted trainer source review')
 old_table=previous['trainer_tables'][1]
 result=[]
 for row in table['rows']:
  need(row['address']==table['address']+row['index']*32 and row['size']==32,'complete exact trainer row')
  d.signed(raw,row)
  accepted=next(r for r in old_table['rows']if r['index']==row['index'])
  need(row['sha256']==accepted['sha256']and chunk(raw,row['address'],32)==chunk(raw,accepted['address'],32),'whole independent accepted Stage31 trainer row equality')
  address=row['address']+7;hit=next(h for h in inherited['hits']if h['address']==address)
  need(hit['accepted']is False and hit['size']==4 and hit['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS'and identity(chunk(raw,address,4))=={k:hit[k]for k in('size','sha256')},'exact inherited unknown scalar crossing')
  evidence=dict(row=row,table={k:table[k]for k in('name','address','count','size','sha256')},layout=prior.LAYOUT,fixed_review=REVIEW,historical_typing_only=True,current_consumer_reachability_claimed=False,independent_accepted_row=accepted,scope_ja='name[3..5]のu8三つとitems[0]下位byte。party pointer row+28は別。')
  result.append(d.TypedRegion(address,address+4,'trainer_name_item_cross_field',evidence))
 return result,dict(status='PASS_HISTORICAL_REGRESSION_TRAINER_SCALARS',table=table,owner=owner['name'],current_consumer_reachability_claimed=False)



SCRIPT_SIZES={106:1,90:1,33:5,6:6,15:6,9:2,103:5,102:1,22:5,37:3,39:1,25:5,4:5,43:3,38:5,40:3,5:5,111:5,3:1,199:2}


def script_path(raw,text):
 path=text['path'];need(0<len(path)<=128 and path[0]['address']==text['target_script_root'],'bounded explicit source event path')
 stack=[]
 for index,row in enumerate(path):
  d.signed(raw,row);opcode=row['opcode'];need(type(opcode)is int and opcode in SCRIPT_SIZES and row['size']==SCRIPT_SIZES[opcode]and chunk(raw,row['address'],1)[0]==opcode,'fixed source opcode and exact operand extent')
  if index==len(path)-1:break
  next_pc=path[index+1]['address'];pc=row['address'];size=row['size']
  if opcode==4:stack.append(pc+size);targets={d.u32(raw,pc+1)}
  elif opcode==5:targets={d.u32(raw,pc+1)}
  elif opcode==6:
   condition=chunk(raw,pc+1,1)[0];need(condition<6,'bounded documented condition');targets={pc+size,d.u32(raw,pc+2)}
  elif opcode==3:
   need(stack,'explicit matching static call/return');targets={stack.pop()}
  else:targets={pc+size}
  need(next_pc in targets,'finite source-rooted control-flow edge')
 call=text['loadword_and_callstd'];d.signed(raw,call)
 need(path[-1]['address']==call['address']and path[-1]['opcode']==15 and call['size']==8,'text operand is final complete LOADWORD followed by CALLSTD')
 value=chunk(raw,call['address'],8)
 need(value[0]==15 and value[1]==0 and int.from_bytes(value[2:6],'little')==call['pointer']==text['address']and value[6:]==bytes([9,4]),'exact LOADWORD0 pointer and message standard4')
 return dict(instructions=len(path),source_root=text['target_script_root'],consumer=call)


def text_root(raw,text):
 chain=text['root_chain'];need([r['role']for r in chain]==['map_groups_literal','group_slot','map_slot','map_header','event_header','object_record'],'complete finite map/object/script root chain')
 d.signed(raw,chain)
 groups,group,maprow,header,events,obj=chain
 for row in (groups,group,maprow):need(row['size']==4 and d.u32(raw,row['address'])==row['value'],'each exact current root pointer')
 import re
 match=re.fullmatch(r'OBJECT:(\d+)/(\d+):(\d+)',text['owner_id']);need(match is not None,'explicit fixed source object identity');g,n,o=map(int,match.groups())
 need(groups['address']==0x08054B0C and group['address']==groups['value']+4*g and maprow['address']==group['value']+4*n and header['address']==maprow['value'],'explicit finite selected map path, no table extent claim')
 need(header['size']==8 and d.u32(raw,header['address']+4)==header['events']==events['address']and events['size']==8 and d.u32(raw,events['address']+4)==events['objects'],'map events and object table actual fields')
 need(chunk(raw,events['address'],1)[0]>o and obj['address']==events['objects']+24*o and obj['size']==24 and obj['script_field']==obj['address']+16 and d.u32(raw,obj['script_field'])==obj['script']==text['target_script_root'],'bounded object index and exact script field')
 return script_path(raw,text)


def text_regions(raw,latest,inherited,review):
 for owner in review['current_actual_owners']:bind_owner(raw,latest,owner)
 need(review['required_candidate']==CANDIDATE and len(review['pairs'])==3,'exact current candidate and reviewed text pairs')
 result=[];proofs=[]
 for pair in review['pairs']:
  left,right=pair['texts'];hit=pair['hit'];need(left['address']+left['size']==right['address']and hit['address']==right['address']-3 and hit['size']==4,'exact left-final3 and right-first1 crossing')
  original=next(h for h in inherited['hits']if h['address']==hit['address']);need(original['accepted']is False and all(original[k]==hit[k]for k in('address','size','sha256')),'only original exact unknown text hit')
  for text in (left,right):
   d.signed(raw,text);value=chunk(raw,text['address'],text['size'])
   need(0<len(value)<512 and value[-1]==255 and 255 not in value[:-1] and not set(value)&{248,249,252,253},'complete finite byte text, terminal-only EOS, no multibyte control or placeholder')
   proofs.append(text_root(raw,text))
  evidence=dict(left={k:left[k]for k in('address','size','sha256')},right={k:right[k]for k in('address','size','sha256')},fixed_review=REVIEW,both_text_consumers_verified=True,source_pointer_interpretation=False,full_story_reachability_claimed=False)
  result.append(d.TypedRegion(hit['address'],hit['address']+4,'adjacent_jp_text_crossing',evidence))
 return result,dict(status='PASS_EXACT_ADJACENT_JP_TEXT_OPERAND_ROOTS',roots=proofs,full_story_reachability_claimed=False)



def thumb_path(raw,rows,entry):
 need(0<len(rows)<=512 and rows[0]['address']==entry and entry%2==0,'finite source-rooted Thumb path')
 for index,row in enumerate(rows):
  d.signed(raw,row);pc=row['address'];need(pc%2==0,'aligned Thumb instruction');value=chunk(raw,pc,row['size']);first=int.from_bytes(value[:2],'little')
  if first&0xF800==0xF000:
   need(row['size']==4,'whole two-halfword BL');target=code.thumb_bl(value,pc)
   need(row.get('target')==target,'exact direct callee target');targets={pc+4,target}
  else:
   need(row['size']==2 and first&0xF800 not in(0xE800,0xF800),'one complete ARMv4T Thumb instruction, never BL halfword or BLX')
   need(first&0xF000!=0xB000 or first&0xFF00==0xB000 or first&0xFE00==0xB400 or first&0xFF00==0xBC00,'closed ARMv4T miscellaneous opcodes, no BKPT/CPS/REV')
   if first&0xF800==0xE000:
    offset=first&0x7FF;offset=offset-0x800 if offset&0x400 else offset;targets={pc+4+2*offset}
   elif first&0xF000==0xD000:
    condition=(first>>8)&15;need(condition<14,'ordinary conditional branch, not reserved or SWI');offset=first&255;offset=offset-256 if offset&128 else offset;targets={pc+2,pc+4+2*offset}
   else:
    need(first&0xFF00!=0x4700 and first&0xFF00!=0xBD00,'no opaque BX or POP PC inside rooted prefix')
    need(not(first&0xFC00==0x4400 and (first&7|((first>>4)&8))==15),'no untracked high-register PC write')
    targets={pc+2}
  if index+1<len(rows):need(rows[index+1]['address']in targets,'every direct instruction edge rooted from entry')
 return True



def bind_text_consumer(raw,review):
 consumer=review['actual_jp_consumer'];d.signed(raw,consumer['windows']);d.signed(raw,consumer['data_windows'])
 named={w['label']:w for w in consumer['data_windows']}
 for row in consumer['data_windows']:
  if 'value'in row:need(row['size']==4 and d.u32(raw,row['address'])==row['value'],'each exact JP consumer literal/table field')
 for edge in consumer['direct_calls']:need(code.thumb_bl(chunk(raw,edge['address'],4),edge['address'])==edge['target'],'each direct JP consumer call')
 base=named['setup_dispatch_base_literal']['value'];need(base==consumer['dispatch_base']==0x08162CC4 and named['setup_dispatch_end_literal']['value']==consumer['dispatch_end'],'JP actual script dispatch bounds')
 for name,opcode,target in [('loadword',15,0x08069B75),('callstd',9,0x08069A41),('message',103,0x0806B0CD)]:
  row=named[name+'_slot'];need(row['address']==base+4*opcode and row['value']==target,'explicit finite JP opcode dispatch')
 need(consumer['script_context_data0_offset']==100 and consumer['script_context_pointer_offset']==8 and consumer['script_context_dispatch_base_offset']==92 and consumer['script_context_dispatch_end_offset']==96,'bound actual JP context layout')
 std=named['std4_slot'];table=named['callstd_table_literal']['value'];need(std['address']==table+16 and std['address']<named['callstd_end_literal']['value']and std['value']==named['std4_exact_script']['address'],'finite standard4 root')
 need(chunk(raw,std['value'],8)==bytes([103,0,0,0,0,102,109,3]),'JP standard4 messageNULL/waitmessage/waitbuttonpress/return')
 switch=named['string_switch_table_literal']['value']
 for name,value in [('FA',0x08008C22),('FB',0x08008C22),('FE',0x08008C22),('FF',0x08008C28)]:
  row=named['string_switch_'+name];need(row['address']==switch+4*(int(name,16)-250)and row['value']==value,'explicit single-byte text/EOS consumer roles')
 return dict(status='PASS_ACTUAL_JP_TEXT_CONSUMER_CHAIN',windows=consumer['windows'],data_windows=consumer['data_windows'],direct_calls=consumer['direct_calls'])


def bind_small_owners(raw,latest,review):
 owners={o['name']:o for o in latest['placement']['owner_byte_audit']}
 for expected in review['owners']:
  owner=owners[expected['name']]
  need(owner['address']==expected['address']and owner['size']==expected['size']and owner['after_sha256']==expected['current_checkpoint_after_sha256']==expected['sha256'],'latest actual small-review owner')
  need(identity(chunk(raw,owner['address'],owner['size']))==dict(size=owner['size'],sha256=owner['after_sha256']),'entire actual small-review owner bytes')
 need(review['target_current_candidate']==CANDIDATE,'same current small-review candidate')


def flagmap_regions(raw,latest,inherited,review):
 bind_small_owners(raw,latest,review);geo=review['geometry'];root=review['root'];hit=review['hit']
 need(next(h for h in inherited['hits']if h['address']==hit['address'])==hit,'exact inherited flagmap unknown')
 need(geo['record_count']==372 and geo['record_size']==4 and geo['hit_row']==266 and geo['hit_row_byte_offset']==2,'exact packed scalar table geometry')
 table=geo['table'];selected=geo['selected_rows'];d.signed(raw,table);d.signed(raw,selected)
 need(table['address']==geo['address']and table['size']==372*4 and selected['address']==table['address']+266*4 and selected['size']==8 and hit['address']==selected['address']+2,'selected cross-record u16 pair')
 values=list(struct.iter_unpack('<HH',chunk(raw,table['address'],table['size'])))
 need(values==sorted(values)and len({a for a,b in values})==len(values),'entire sorted unique source flag map')
 for name in ('hook','entry','table_literal','bound_count_literal'):d.signed(raw,root[name])
 hook=chunk(raw,root['hook']['address'],8);need(struct.unpack_from('<HH',hook)==(0x4B00,0x4718)and int.from_bytes(hook[4:],'little')==root['target']==root['entry']['address']|1,'exact current Thumb hook and leaf target')
 need(d.u32(raw,root['table_literal']['address'])==root['table_literal']['value']==table['address']and d.u32(raw,root['bound_count_literal']['address'])==root['bound_count_literal']['value']==372,'same current leaf table and finite row count')
 for row in review['consumers']:
  inst=row['instruction'];d.signed(raw,inst);op=int.from_bytes(chunk(raw,inst['address'],2),'little')
  need(op&0xF800==0x8800 and ((op>>6)&31)*2==row['field_offset']and row['field_offset']in(0,2),'actual LDRH scalar field offset')
 evidence=dict(selected_rows=selected,record_size=4,field_offsets=[0,2],table=table,fixed_review=REVIEW,source_pointer_interpretation=False)
 return [d.TypedRegion(hit['address'],hit['address']+4,'packed_u16_cross_row',evidence)],dict(status='PASS_CURRENT_PACKED_U16_FLAGMAP',root=root,consumers=review['consumers'])


def rooted_code_regions(raw,latest,inherited,review):
 bind_small_owners(raw,latest,review);hit=review['hit'];root=review['root']
 need(next(h for h in inherited['hits']if h['address']==hit['address'])==hit,'exact original unknown instruction hit')
 call=root['callnative'];d.signed(raw,call);d.signed(raw,root['entry']);data=chunk(raw,call['address'],5)
 need(call['size']==5 and data[0]==35 and int.from_bytes(data[1:],'little')==call['target']==root['entry']['address']|1,'complete source CALLNATIVE root')
 rows=review['instruction_path'];thumb_path(raw,rows,root['entry']['address'])
 window=review['selected_instruction_window'];d.signed(raw,window)
 selected=[r for r in rows if window['address']<=r['address']<window['address']+window['size']]
 need(selected and selected[0]['address']==window['address']and selected[-1]['address']+selected[-1]['size']==window['address']+window['size']and d.contains(window['address'],window['address']+window['size'],hit['address'],4),'complete rooted minimal instruction window')
 need(not review['literal_pool_included']and not review['full_function_range_classified']and all(not window['address']<=r.get('literal_address',0)<window['address']+window['size']for r in rows),'literal pools and blanket function typing forbidden')
 evidence=dict(instruction_window=window,instructions=[{k:r[k]for k in('address','size')}for r in selected],root_verified=True,literal_pool_included=False,fixed_review=REVIEW,source_root=call,full_story_reachability_claimed=False)
 return [d.TypedRegion(window['address'],window['address']+window['size'],'rooted_thumb_instruction_stream',evidence)],dict(status='PASS_SOURCE_ROOTED_THUMB_PATH',root=call,path_instructions=len(rows),window=window)



def bind_code_windows(raw,review):
 d.signed(raw,review['code_windows'])
 for row in review.get('direct_calls',[]):need(code.thumb_bl(chunk(raw,row['address'],4),row['address'])==row['target'],'each exact JP asset consumer call')


def tileset_regions(raw,latest,inherited,review):
 need(review['required_candidate']==CANDIDATE,'same current tileset candidate')
 for owner in review['current_actual_owners']:bind_owner(raw,latest,owner)
 bind_code_windows(raw,review);literal=review['map_layouts_literal'];d.signed(raw,literal)
 need(literal['address']==0x08054A54 and d.u32(raw,literal['address'])==literal['value'],'current JP map-layout literal root')
 bios=next(w for w in review['code_windows']if w['label']=='LZ77UnCompWram_BIOS_entry')
 need(chunk(raw,bios['address'],4)==bytes([17,223,112,71]),'actual LZ77 BIOS SWI11 and return')
 need([r['layout_index']for r in review['assets']]==[384,513,394],'finite explicit source layout selectors')
 result=[];proof=[]
 for row in review['assets']:
  slot,layout,tileset,asset,hit=[row[k]for k in('layout_table_slot','layout','tileset','asset','hit')]
  for window in(slot,layout,tileset,asset,hit):d.signed(raw,window)
  need(slot['address']==literal['value']+4*row['layout_index']and row['layout_id']==row['layout_index']+1 and d.u32(raw,slot['address'])==slot['value']==layout['address'],'finite selected layout table field')
  need(layout['size']==28 and layout['tileset_field_offset']in(16,20)and d.u32(raw,layout['address']+layout['tileset_field_offset'])==layout['tileset']==tileset['address'],'exact source layout tileset field')
  flags=chunk(raw,tileset['address'],2);need(tileset['size']==24 and flags==bytes([tileset['is_compressed'],tileset['is_secondary']])and flags[0]==1 and tileset['graphics_field_offset']==4 and d.u32(raw,tileset['address']+4)==tileset['graphics']==asset['address'],'actual compressed tileset graphics pointer')
  encoded,decoded=d.decode_lz_at(raw,asset['address']);need(identity(encoded)=={k:asset[k]for k in('size','sha256')}and identity(decoded)==asset['decoded'],'finite exact LZ grammar, consumed extent and whole decoded identity')
  original=next(h for h in inherited['hits']if h['address']==hit['address']);need(not original['accepted']and all(original[k]==hit[k]for k in('address','size','sha256'))and d.contains(asset['address']+4,asset['address']+asset['size'],hit['address'],4),'only exact original compressed payload hit')
  witness=dict(asset={k:asset[k]for k in('address','size','sha256')},decoded=asset['decoded'],fixed_review=REVIEW,layout_id=row['layout_id'],actual_screen_rendered=False)
  result.append(d.TypedRegion(asset['address']+4,asset['address']+asset['size'],'rooted_tileset_lz77',witness));proof.append(dict(layout=layout,tileset=tileset,asset=asset))
 return result,dict(status='PASS_ROOTED_EXACT_TILESET_LZ77',assets=proof,actual_screen_rendered=False)


def sprite_regions(raw,latest,inherited,review):
 need(review['required_candidate']==CANDIDATE,'same current sprite candidate')
 for owner in review['current_actual_owners']:bind_owner(raw,latest,owner)
 bind_code_windows(raw,review);chain=review['root_chain'];d.signed(raw,chain);groups,group,maprow,header,events,obj=chain
 for row in(groups,group,maprow):need(d.u32(raw,row['address'])==row['value'],'current finite sprite map roots')
 need(groups['address']==0x08054B0C and group['address']==groups['value']+96*4 and maprow['address']==group['value']+3*4 and header['address']==maprow['value']and d.u32(raw,header['address']+4)==events['address']==header['events']and d.u32(raw,events['address']+4)==events['objects'],'finite map96/3 object roots')
 need(chunk(raw,events['address'],1)[0]>2 and obj['address']==events['objects']+2*24 and chunk(raw,obj['address']+1,1)[0]==obj['graphics_id']==153,'actual finite object2 graphicsID153')
 g=review['graphics'];need(g['runtime_graphics_id']==153 and g['source_graphics_id']==49 and(g['width'],g['height'])==(16,32),'fixed RocketM dimensions and explicit remap')
 for key in('table_literal','slot','info','frame_table','animation_slot','animation','frame','asset'):d.signed(raw,g[key])
 literal,slot,info,frames=g['table_literal'],g['slot'],g['info'],g['frame_table']
 need(d.u32(raw,literal['address'])==literal['value']and slot['address']==literal['value']+153*4 and d.u32(raw,slot['address'])==slot['value']==info['address'],'current graphics153 lookup')
 need(info['size']==36 and struct.unpack('<HH',chunk(raw,info['address']+8,4))==(16,32)and g['images_offset']==28 and d.u32(raw,info['address']+28)==frames['address']and frames['count']==9 and frames['stride']==8 and frames['size']==72,'source-shaped9 frame image array')
 animation,aslot=g['animation'],g['animation_slot'];need(g['animations_offset']==24 and aslot['address']==d.u32(raw,info['address']+24)+6*4 and d.u32(raw,aslot['address'])==aslot['value']==animation['address'],'finite animation6 root')
 words=struct.unpack('<10H',chunk(raw,animation['address'],20));need(list(words[::2])==[7,2,8,2,65534]and words[-1]==0 and animation['frame_indices']==[7,2,8,2]and animation['jump_to']==0,'source frame8 selected by exact animation and bounded loop')
 frame,asset=g['frame'],g['asset'];need(frame['index']==8 and frame['address']==frames['address']+8*8 and frame['size']==8 and struct.unpack('<IH',chunk(raw,frame['address'],6))==(asset['address'],asset['size'])and frame['data']==asset['address']and frame['data_size']==asset['size']==256,'selected complete raw4bpp frame extent')
 hit=review['hit'];original=next(h for h in inherited['hits']if h['address']==hit['address']);need(not original['accepted']and all(original[k]==hit[k]for k in('address','size','sha256'))and d.contains(asset['address'],asset['address']+256,hit['address'],4),'only original rooted sprite payload hit')
 evidence=dict(asset=asset,width=16,height=32,frame_index=8,fixed_review=REVIEW,actual_screen_rendered=False)
 return[d.TypedRegion(asset['address'],asset['address']+256,'rooted_sprite_4bpp_frame',evidence)],dict(status='PASS_ROOTED_RAW_SPRITE_FRAME',graphics=g,actual_screen_rendered=False)


def shared_regions(raw,latest,inherited,review):
 bind_small_owners(raw,latest,review);g=review['geometry'];consumer=review['consumer'];hit=review['hit'];table,moves=g['table'],g['move_table']
 need(next(h for h in inherited['hits']if h['address']==hit['address'])==hit,'exact inherited SharedIndex unknown')
 for row in(table,moves,g['selected_elements']):d.signed(raw,row)
 need(g['element_type']=='u16'and g['element_size']==2 and g['element_count']==1622 and table['size']==3244 and moves['size']==g['move_element_count']*2==10046,'source-serialized u16 index and move tables')
 index=list(struct.unpack('<1622H',chunk(raw,table['address'],table['size'])));need(index[0]==0 and index==sorted(index)and index[-1]==5023 and max(b-a for a,b in zip(index,index[1:]))==15,'whole finite scalar index invariants')
 need(g['selected_index']==722 and g['selected_elements']['address']==table['address']+2*722==hit['address']and g['selected_elements']['size']==4,'exact adjacent index entries, no u32 pointer field')
 audit=json.loads((ROOT/'content/modernization/p03_stage73_consumer_runtime_route_audit.json').read_bytes())['serialization']['runtime_tables']['Shared']
 need(audit==review['serialization_binding']['audit']and audit['index_sha256']==table['sha256']and audit['move_sha256']==moves['sha256'],'fixed serializer whole table identities')
 for key,value in consumer.items():
  if isinstance(value,dict)and all(k in value for k in('address','size','sha256')):d.signed(raw,value)
 need(d.u32(raw,consumer['index_literal']['address'])==table['address']and d.u32(raw,consumer['move_literal']['address'])==moves['address'],'actual historical typed consumer argument literals')
 call=consumer['direct_call'];need(code.thumb_bl(chunk(raw,call['address'],4),call['address'])==call['target']==consumer['append_table_entry']['address'],'actual typed consumer call')
 for row in consumer['indexed_u16_loads']:
  inst=row['instruction'];d.signed(raw,inst);op=int.from_bytes(chunk(raw,inst['address'],2),'little');need(op&0xF800==0x8800 or op&0xFE00==0x5A00,'actual halfword scalar read')
 evidence=dict(selected_elements=g['selected_elements'],element_size=2,table=table,fixed_review=REVIEW,historical_typing_only=True,current_live_reachability_claimed=False)
 return[d.TypedRegion(hit['address'],hit['address']+4,'indexed_u16_pair',evidence)],dict(status='PASS_SERIALIZED_HISTORICAL_SHARED_INDEX',geometry=g,consumer=consumer,current_live_reachability_claimed=False)


def shiny_regions(raw,latest,inherited,review):
 root=review['root'];call=root['callnative'];entry=root['delegate_entry'];literal=root['delegate_literal'];header=root['source_serialized_entry_pointer'];d.signed(raw,entry);d.signed(raw,literal);d.signed(raw,header);d.signed(raw,root['instructions'])
 config=json.loads((ROOT/'config/factory_high_modes_v2.json').read_bytes());expected=config['delegates']['trial_complete'];expected=int(expected,0)if isinstance(expected,str)else expected
 d.signed(raw,call);need(call['size']==5,'complete signed source CALLNATIVE')
 hooks=[h for h in config['hooks']if h['name']=='factory_trial_completion_chain'];need(len(hooks)==1 and int(hooks[0]['address'],0)==call['address']+1 and hooks[0]['mode']=='POINTER'and hooks[0]['target']=='FactoryHighModesV2_TrialCompleteAdapter'and hooks[0]['delegate']=='FactoryShinyMemorialRuntime_Complete','exact source wrapper hook and delegate')
 rows=root['instructions'];need(entry['size']==8 and len(rows)==4 and[(r['address'],r['size'])for r in rows[:3]]==[(entry['address'],2),(entry['address']+2,2),(entry['address']+4,4)],'consecutive PUSH LDR BL without hidden r3 overwrite')
 push=int.from_bytes(chunk(raw,entry['address'],2),'little');need(push&0xFF00==0xB500 and push&255,'entry PUSH with LR and nonempty register frame')
 need(d.u32(raw,literal['address'])==literal['value']==d.u32(raw,header['address'])==header['value']==expected==root['instruction_entry']['address']|1,'explicit source-config and serialized-entry delegate identity')
 load=root['instructions'][1];op=int.from_bytes(chunk(raw,load['address'],2),'little');need(op&0xF800==0x4800 and(op>>8)&7==3 and ((load['address']+4)&~3)+(op&255)*4==literal['address'],'exact adjacent LDR r3 delegate literal')
 bl=root['instructions'][2];bx=root['instructions'][3];need(code.thumb_bl(chunk(raw,bl['address'],4),bl['address'])==bl['target']==bx['address']and chunk(raw,bx['address'],2)==bytes([24,71]),'exact BL trampoline and BX r3, no unknown indirect control')
 # CALLNATIVE target is wrapper; bind it separately then pass the resolved direct entry.
 need(chunk(raw,call['address'],1)[0]==35 and d.u32(raw,call['address']+1)==call['target']==entry['address']|1,'current source wrapper CALLNATIVE')
 bind_small_owners(raw,latest,review);hit=review['hit'];need(next(h for h in inherited['hits']if h['address']==hit['address'])==hit,'exact original Shiny unknown')
 thumb_path(raw,review['instruction_path'],root['instruction_entry']['address'])
 window=review['selected_instruction_window'];d.signed(raw,window);selected=[r for r in review['instruction_path']if window['address']<=r['address']<window['address']+window['size']]
 need(selected and selected[0]['address']==window['address']and selected[-1]['address']+selected[-1]['size']==window['address']+window['size']and d.contains(window['address'],window['address']+window['size'],hit['address'],4),'complete minimal Shiny instruction crossing')
 need(not review['literal_pool_included']and not review['full_function_range_classified'],'no blanket code typing')
 evidence=dict(instruction_window=window,instructions=[{k:r[k]for k in('address','size')}for r in selected],root_verified=True,literal_pool_included=False,fixed_review=REVIEW,source_root=call,resolved_delegate=literal,full_story_reachability_claimed=False)
 return[d.TypedRegion(window['address'],window['address']+window['size'],'rooted_thumb_instruction_stream',evidence)],dict(status='PASS_EXPLICIT_RESOLVED_DELEGATE_THUMB_PATH',root=call,delegate=literal,path_instructions=len(review['instruction_path']),window=window)


def measured_regions(raw,latest,inherited,sources,review):
 bindings={}
 for value in review.values():
  if isinstance(value,dict)and 'source_bindings'in value:bindings.update(source_proof(value,sources))
 r1,p1=trainer_regions(raw,latest,inherited,review['regression'])
 consumer=bind_text_consumer(raw,review['stage61']);r2,p2=text_regions(raw,latest,inherited,review['stage61'])
 r3,p3=flagmap_regions(raw,latest,inherited,review['flagmap']);r4,p4=rooted_code_regions(raw,latest,inherited,review['circus'])
 r5,p5=rooted_code_regions(raw,latest,inherited,review['factory']);r6,p6=shiny_regions(raw,latest,inherited,review['shiny']);r7,p7=shared_regions(raw,latest,inherited,review['shared']);r8,p8=tileset_regions(raw,latest,inherited,review['tilesets']);r9,p9=sprite_regions(raw,latest,inherited,review['sprite'])
 return r1+r2+r3+r4+r5+r6+r7+r8+r9,dict(regression=p1,stage61=p2,text_consumer=consumer,flagmap=p3,circus=p4,factory=p5,shiny=p6,shared=p7,tilesets=p8,sprite=p9,source_bindings=bindings,donor_leased=False)


def regions(raw,latest,inherited,sources):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 candidate before classification')
 data=(ROOT/REVIEW).read_bytes();need(identity(data)==REVIEW_ID,'immutable finite root review')
 return measured_regions(raw,latest,inherited,sources,json.loads(data))
