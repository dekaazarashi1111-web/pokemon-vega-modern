#!/usr/bin/env python3
"""受付の残高/rank数値buffer接続。既存15byte文言/132byteイベント窓だけ。"""
from pathlib import Path
import hashlib
import json
import struct
ROOT=Path(__file__).resolve().parents[1]
PARENT={'size':33554432,'sha256':'26dac23cfdbc02c3c25e357b79dcdf3d247c10d893f54a4f6d6b1227bf5624da'}
CANDIDATE={'size':33554432,'sha256':'c3971e83184613a27730eaec6490d203a2c1261c77894b711b0352f487808557'}
SCRIPT=0x093C02A4
TEXT=0x093C004B
TEXT_BEFORE=bytes.fromhex('9f527e642dfe0608162e0c1f0dadff')
TEXT_AFTER=bytes.fromhex('ccca00fd02fe777e5800fd03ffffff')
SCRIPT_BEFORE=bytes.fromhex('6a5a0f003d003c09090423a1e83b09210d8000000601dc023c09210d800400060104033c09210d800d00060114033c090524033c090000000f004b003c0909040f005a003c0909040f006d003c0909040f008e003c0909040524033c090000000f007e003c0909040524033c090000000f009e003c0909040524033c090000006c020000')
ROOTS={
 0x093BE032:(36,'1a5248b36921d67d6b9d2f4b2c6bd6ee438d766e95db1ffa9afcf4b1fe42e1ad'),
 0x093BE056:(72,'c31639668764f4b7f9c9b2c9129e064f42f876ff0c29e100133c8eae0099b621'),
 0x0806B684:(68,'7ad4eba7ab8630ba0480d9b273f2fc65e07a3e4355e5c8fc49a2b40d228bbb60'),
 0x08162CC4:(848,'02ec8b5d59392777bf839feb24cbef40e029ab3190a8569f8605785c37ab57f4'),
 0x0806933C:(44,'aedd88ea822c1edb9e36fef2b6c4c933a8f28d252e974e03d5c27dc28a08629e'),
 0x080693BC:(40,'99c5c54e7ce5df848aa4a6e12174872a1cf63e57e5ffbaf8aabc419ea4c5c27a'),
 0x08069418:(40,'f60a3d3aa9c573237cb339ed97d314f335f391ae9c2faa521a004d49303de59c')}

def need(ok,reason):
 if not ok:raise ValueError(reason)
def identity(b):return {'size':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def script():
 code=bytearray(b'\x6a\x5a');labels={};fixes=[]
 def pointer(value):code.extend(struct.pack('<I',value))
 def message(address):code.extend(b'\x0f\0');pointer(address);code.extend(b'\x09\x04')
 def call(address):code.append(0x23);pointer(address)
 def branch(result,label):
  code.extend(b'\x21\x0d\x80'+struct.pack('<H',result)+b'\x06\x01');fixes.append((len(code),label));pointer(0)
 def end():code.extend(b'\x6c\x02')
 message(0x093C003D);call(0x093BE8A1)
 for result,label in ((0,'normal'),(4,'cap'),(13,'save_fail')):branch(result,label)
 code.append(5);fixes.append((len(code),'end'));pointer(0)
 labels['normal']=SCRIPT+len(code)
 call(0x093BE033);code.extend(b'\x83\0\x0d\x80')
 call(0x093BE057);code.extend(b'\x83\x01\x0d\x80')
 # getterが使うgSpecialVar_Resultは元の成功値へ戻す。
 code.extend(b'\x16\x0d\x80\0\0')
 for address in (TEXT,0x093C005A,0x093C006D,0x093C008E):message(address)
 end()
 labels['cap']=SCRIPT+len(code);message(0x093C007E);end()
 labels['save_fail']=SCRIPT+len(code);message(0x093C009E);end()
 labels['end']=SCRIPT+len(code);end()
 for at,label in fixes:struct.pack_into('<I',code,at,labels[label])
 need(len(code)==132,'exact existing event window')
 return bytes(code),labels

def audit(parent):
 need(type(parent) is bytes and identity(parent)==PARENT,'exact accepted predecessor')
 def span(a,n):return parent[a-0x08000000:a-0x08000000+n]
 def word(a):return struct.unpack('<I',span(a,4))[0]
 need(span(SCRIPT,132)==SCRIPT_BEFORE and span(TEXT,15)==TEXT_BEFORE,'existing script/text preimages')
 need(len(TEXT_AFTER)==15 and TEXT_AFTER[-3:]==b'\xff'*3,'bounded format + unchanged window')
 for a,(n,digest) in ROOTS.items():need(identity(span(a,n))=={'size':n,'sha256':digest},'bound engine/getter code')
 need(word(0x0806935C)==word(0x080693DC)==word(0x08069438)==0x08162CC4,'actual interpreter command-table roots')
 need(word(0x08162CC4+0x83*4)==0x0806B685 and word(0x0806B6C4)==0x0836B2CC,'buffernumber actual handler')
 need([word(0x0836B2CC+4*i) for i in range(3)]==[0x02021C4C,0x02021C60,0x02021C74],'native string buffer table')
 table=word(0x08054B0C);need(word(word(table+98*4)+3*4)==0x092C2ADC,'actual lab header')
 events=word(0x092C2ADC+4);objects=word(events+4)
 need(span(events,1)==b'\x07' and objects+3*24==0x09413B9C and span(objects+3*24,1)==b'\x04' and word(objects+3*24+16)==SCRIPT,'actual local4 host root')
 model=json.loads((ROOT/'content/research_economy_v1/canonical_model.json').read_bytes())
 balance=next(r for r in model['dialogue'] if r['dialogue_key']=='DIALOGUE_KEY_COUNTER_BALANCE')
 rank=next(r for r in model['dialogue'] if r['dialogue_key']=='DIALOGUE_KEY_RANK_UP')
 need(balance['runtime_address']==TEXT and bytes.fromhex(balance['encoded_hex'])==TEXT_BEFORE and bytes.fromhex(rank['encoded_hex'])[:3]==bytes.fromhex('777e58'),'base dialogue model and rank glyphs')
 return dict(get_balance=0x093BE033,get_rank=0x093BE057,buffer_opcode=0x83,result_variable=0x800D,slot_addresses=[0x02021C4C,0x02021C60],physical_host=0x09413B9C,root_hashes={hex(a):{'size':n,'sha256':h} for a,(n,h) in ROOTS.items()})

def apply(parent):
 roots=audit(parent);code,labels=script();result=bytearray(parent)
 patches=[]
 for address,before,after in ((TEXT,TEXT_BEFORE,TEXT_AFTER),(SCRIPT,SCRIPT_BEFORE,code)):
  off=address-0x08000000;result[off:off+len(before)]=after
  patches.append(dict(offset=off,before=before.hex(),after=after.hex()))
 result=bytes(result);undo=bytearray(result)
 for p in patches:undo[p['offset']:p['offset']+len(bytes.fromhex(p['before']))]=bytes.fromhex(p['before'])
 need(bytes(undo)==parent and identity(result)==CANDIDATE,'complete rollback/outside windows/successor invariant')
 return result,dict(schema_version=1,parent=PARENT,candidate=identity(result),patches=patches,roots=roots,labels=labels,changed_bytes=sum(x!=y for x,y in zip(parent,result)),declared_bytes=147,outside_declared_changes=0,arm_compiles=0,new_allocations=0,scope='COUNTER_NUMERIC_TEXT_NOT_STANDARD_LIST',base_model='content/research_economy_v1/canonical_model.json',display_source='RP {STR_VAR_1}\\nランク {STR_VAR_2}',result_restored=0,cap_result_preserved=4,save_failure_preserved=13,standard_list_implemented=False,natural_earning_spending_accepted=False,active_baseline_changed=False,release_ready=False)
