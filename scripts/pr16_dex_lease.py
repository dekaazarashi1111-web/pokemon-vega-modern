#!/usr/bin/env python3
"""旧T09 pointer ownerの退役証拠をfail-closedで検証。配置前後の範囲を限定する。"""
from __future__ import annotations
import argparse,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROOF='content/modernization/pr16_dex_capacity_lease.json'
CANDIDATE=dict(size=33554432,sha256='06c5e85cf8cf86eacb369347896154d33594e7a42b3da3a25140bc1cc4da03d5')
START=0x01FC0998;END=0x01FC22EC
OLD_DATA_START=0x01FAC9B8;OLD_DATA_END=0x01FC0995
BASE=0x08000000

def need(value,message):
 if not value:raise ValueError(message)
def identity(raw):return dict(size=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def u32(raw,at):return struct.unpack_from('<I',raw,at)[0]
def exact_refs(raw,value):
 out=[];needle=struct.pack('<I',value);at=raw.find(needle)
 while at>=0:out.append(at);at=raw.find(needle,at+1)
 return out

def check_window(raw,window):
 offset=window['offset'];size=window['size']
 need(type(offset)is int and type(size)is int and offset>=0 and size>0 and offset+size<=len(raw),'bounded signed window')
 need(identity(raw[offset:offset+size])==dict(size=size,sha256=window['sha256']),'signed window differs at '+hex(offset))
def check_bindings(raw,node):
 if type(node)is dict:
  if {'offset','size','sha256'}<=node.keys():check_window(raw,node)
  for value in node.values():check_bindings(raw,value)
 elif type(node)is list:
  for value in node:check_bindings(raw,value)

def check_external_range_candidates(raw,proof):
 # 全byte開始位置。word-aligned literalだけに限定しない。
 got=[]
 for at in range(len(raw)-3):
  if START<=at<END or raw[at+3]!=9:continue
  value=u32(raw,at)
  if BASE+START<=value<BASE+END:got.append((at,value))
 expected=[(x['offset'],x['value'])for x in proof['range_candidates']]
 need(got==expected and len(got)==35,'complete canonical range candidates differ')

def check_old_rows(raw,proof):
 for row in proof['bounded_old_data_row_scan']:
  count=0;maximum=0
  for sid in range(row['rows']):
   start=u32(raw,row['table']+4*sid)-BASE
   if not OLD_DATA_START<=start<OLD_DATA_END:continue
   count+=1
   for i in range(256):
    at=start+3*i;need(at+3<=OLD_DATA_END,'old learnset row crosses donor boundary')
    if raw[at:at+3]==b'\0\0\xff':maximum=max(maximum,at+3);break
   else:raise ValueError('unterminated old learnset row')
  need(count==row['old_data_rows']and maximum==row['maximum_read_end'],'old row domain changed')

def check_typed_candidates(raw,proof):
 counts={}
 for row in proof['range_candidates']:
  at=row['offset'];kind=row['type'];counts[kind]=counts.get(kind,0)+1
  need(row['literal_load_candidates']==dict(thumb=[],arm=[]),'unresolved direct literal use')
  if kind=='THUMB_BL_OVERLAP':
   start=row['instruction_binding']['offset'];hi,lo=struct.unpack_from('<HH',raw,start)
   need(hi&0xF800==0xF000 and lo&0xF800==0xF800 and start<at<start+4,'actual Thumb BL overlaps false pointer')
   displacement=((hi&0x7FF)<<12)|((lo&0x7FF)<<1)
   if displacement&(1<<22):displacement-=1<<23
   target=BASE+start+4+displacement
   need(target==row['branch_target'],'bound real Thumb target')
   need(not BASE+START<=target<BASE+END,'branch really enters donor')
  elif kind=='JP_TEXT_GLYPHS_PAUSE_EOS':
   need(raw[at+2:at+5]==bytes((252,9,255))and row['string_start']<=at and row['string_end']==at+5,'text glyph/pause/EOS ABI')
   for site in row['string_pointer_sites']:need(u32(raw,site)==BASE+row['string_start'],'text root drift')
   # rootless stock string must carry an independently pinned exact source witness.
   need(row['string_pointer_sites']or row.get('typed_source_proof',{}).get('status')=='EXACT_PINNED_U8_STRING_ENCODING_MATCH','rootless text needs exact source witness')
  elif kind in('M4A_PCM_SAMPLE','M4A_DELTA_COMPRESSED_SAMPLE'):
   start=row['wave_header_offset'];typ,status,freq,loop,size=struct.unpack_from('<HHIII',raw,start)
   need(typ==row['wave_type']and size==row['samples']and 0<=loop<=size,'wave header ABI')
   encoded=size if kind=='M4A_PCM_SAMPLE'else((size+63)//64)*33
   need(start+16<=at and at+4<=start+16+encoded and row['encoded_range_binding']['size']==16+encoded,'bounded sample payload')
   need(row['wave_pointer_sites'],'wave roots present')
   for site in row['wave_pointer_sites']:need(u32(raw,site)==BASE+start,'wave root drift')
  elif kind=='GBA_LZ77_STREAM':
   start=row['header_offset'];need(raw[start]==0x10 and int.from_bytes(raw[start+1:start+4],'little')==row['decoded_size'],'LZ77 header ABI')
   need(start+4<=at and at+4<=row['compressed_end'],'bounded compressed data')
   need(row['header_pointer_sites'],'LZ77 source roots present')
   for site in row['header_pointer_sites']:need(u32(raw,site)==BASE+start,'LZ77 root drift')
  else:raise ValueError('unclassified external range candidate')
 need(counts==proof['candidate_types'],'all candidate classes exact')

def proof():
 p=json.loads((ROOT/PROOF).read_bytes());need(p['candidate']==CANDIDATE,'proof exact candidate')
 d=p['donor'];need((d['name'],d['owner'],d['start'],d['end_exclusive'],d['size'],d['alignment'])==('species_surface_level_up_pointers','T09',START,END,END-START,4),'one exact declared parent owner')
 need(p['retirement_stage']==39 and len(p['known_root_consumers'])==5 and len(p['indirect_storage_sites'])==8 and len(p['empty_row_pointer_sites'])==6,'known retired root contract')
 return p

def validate_preimage(raw):
 need(identity(raw)==CANDIDATE,'exact fixed candidate before any lease')
 p=proof();d=p['donor'];need(hashlib.sha256(raw[START:END]).hexdigest()==d['content_sha256'],'whole donor preimage')
 check_bindings(raw,p)
 for base in(BASE,0x0A000000,0x0C000000):need(not exact_refs(raw,base+START),'old table base or mirrored base became rooted')
 for row in p['known_root_consumers']:need(u32(raw,row['site'])==row['current_value']and not BASE+START<=row['current_value']<BASE+END,'current typed root')
 need(exact_refs(raw,0x0804346C)==p['indirect_storage_sites'],'whole indirect root inventory')
 need(exact_refs(raw,0x09FC0804)==p['empty_row_pointer_sites'],'whole live empty-row reference inventory')
 check_external_range_candidates(raw,p);check_typed_candidates(raw,p);check_old_rows(raw,p)
 return dict(status='PASS_EXACT_RETIRED_OWNER_PREIMAGE_ONLY',donor=dict(offset=START,size=END-START,sha256=d['content_sha256']),false_pointer_candidates=35,known_roots=5,old_data_preserved=True,allocator_transferred=False,rom_changed=False,native_processes=0,whole_program_unreachability_claimed=False)

def plan_payload(size,alignment=4):
 need(type(size)is int and 0<size<=END-START,'payload fits exclusive donor')
 need(type(alignment)is int and alignment in(2,4)and START%alignment==0,'declared alignment supported')
 return dict(parent='species_surface_level_up_pointers',new_owner='USER-20261004-DEX-CAPACITY',offset=START,size=size,exclusive_lease_size=END-START,remaining=END-START-size,allocator_transfer_required=True)

def validate_postimage(before,after):
 validate_preimage(before);need(len(after)==len(before),'fixed ROM length')
 need(after[:START]==before[:START]and after[END:]==before[END:],'no write outside exclusive lease')
 changed=sum(a!=b for a,b in zip(before[START:END],after[START:END]));need(changed>0,'a postimage must contain an actual candidate placement')
 return dict(status='PASS_LEASE_DIFF_ONLY_NOT_RUNTIME_ACCEPTANCE',changed_bytes=changed,postimage=identity(after),ordinary_save_accepted=False,consumer_wired=False)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('rom',type=Path);args=parser.parse_args();print(json.dumps(validate_preimage(args.rom.read_bytes()),ensure_ascii=False,indent=2))
