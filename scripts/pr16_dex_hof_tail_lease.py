#!/usr/bin/env python3
"""HOF新260byteの全見かけ参照を型付き入力窓へ照合。原本byteは公開しない。"""
import json,struct
from pathlib import Path
import pr16_dex_tail_lease as old
ROOT=Path(__file__).resolve().parents[1]
PROOF='content/modernization/pr16_dex_hof_tail_lease.json'
LO=0x09FFFCC0;HI=LO+260
need,digest=old.need,old.digest

def validate(raw):
 p=json.loads((ROOT/PROOF).read_bytes());need(p['scope']==dict(base=LO,size=260,end_exclusive=HI,literal_candidates=22,thumb_bl_candidates=3),'exact HOF scope')
 a,b=old.LO,old.HI
 try:
  old.LO,old.HI=LO,HI;literals=old.literals(raw);branches=old.branches(raw)
 finally:old.LO,old.HI=a,b
 take=lambda rows:sorted(({k:r[k]for k in('address','target')}for r in rows),key=lambda r:r['address'])
 need(literals==take(p['candidates'])and branches==take(p['branch_candidates']),'full allbyte three-mirror and ThumbBL inventory')
 def chunk(a,n):
  need(0x08000000<=a<a+n<=0x0A000000,'in-ROM signed window');return raw[a-0x08000000:a-0x08000000+n]
 def signed(x):
  if isinstance(x,dict):
   if all(k in x for k in('address','size','sha256')):need(digest(chunk(x['address'],x['size']))=={k:x[k]for k in('size','sha256')},'every root/ref/consumer whole signed window')
   for y in x.values():signed(y)
  elif isinstance(x,list):
   for y in x:signed(y)
 signed(p['roots']);roots={r['address']:r for r in p['roots']};need(len(roots)==17,'all17 roots')
 for r in roots.values():
  b=chunk(r['address'],r['size']);kind=r['kind']
  for ref in r.get('refs',[]):need(struct.unpack('<I',chunk(ref['address'],4))[0]==ref['value']==r['address'],'original rooted reference')
  if kind=='battle_anim_script_prefix':
   cursor=r['address']
   for cmd in r['commands']:
    need(cmd['address']==cursor and chunk(cursor,1)[0]==cmd['opcode'],'continuous typed command prefix');d=chunk(cursor,cmd['size'])
    if cmd['opcode']==2:
     need(len(d)==7+2*d[6],'createsprite argc controls extent')
     if 'argc'in cmd:need(struct.unpack_from('<I',d,1)[0]==cmd['template']and d[5]==cmd['battler_priority']and d[6]==cmd['argc']and list(struct.unpack_from('<'+'h'*d[6],d,7))==cmd['argv'],'candidate solely numeric sprite arguments')
    cursor+=cmd['size']
   need(cursor==r['address']+r['size'],'whole rooted prefix consumed')
  elif kind in('pcm8','dpcm4'):
   need(struct.unpack_from('<HHIII',b)==tuple(r[k]for k in('wave_type','wave_status','wave_frequency','wave_loop_start','decoded_size')),'complete wave header');out=old.dpcm(b[16:],r['decoded_size'])if kind=='dpcm4'else b[16:];need(digest(out)==dict(size=r['decoded_size'],sha256=r['decoded_sha256']),'complete typed audio decode')
  elif kind=='lz77':
   need(digest(old.lz(b))==dict(size=r['decoded_size'],sha256=r['decoded_sha256']),'complete typed sprite decode')
   for table in r['typed_tables']:
    row=table['row'];need(row['address']==table['table_address']+table['stride']*table['row_index'],'typed SID row position');need(struct.unpack('<IHH',chunk(row['address'],8))==(r['address'],row['size_field'],row['tag_field']),'sprite row pointer/size/tag')
    for ref in table['table_root_sites']:need(struct.unpack('<I',chunk(ref['address'],4))[0]==table['table_address']==ref['value'],'actual table root')
  elif kind=='thumb_code_basic_block':
   d=chunk(r['candidate_instruction_span']['address'],8);h,l,x,y=struct.unpack('<4H',d);need(h&0xF800==0xF000 and l&0xF800==0xF800 and x==0x0409 and y==0x0C09,'apparent pointer crosses Thumb BL and shift instructions');off=((h&0x7FF)<<12)|((l&0x7FF)<<1);off-=1<<23 if off&(1<<22)else 0;need(r['candidate_instruction_span']['address']+4+off==0x09099E04,'real call points outside new tail')
  elif kind=='thumb_literal_mask':
   for read in r['literal_reads']:
    at=read['instruction']['address'];ins=struct.unpack('<H',chunk(at,2))[0];need(ins&0xF800==0x4800 and((at+4)&~3)+(ins&255)*4==read['target'],'literal load decodes to actual mask');need(struct.unpack('<I',chunk(read['target'],4))[0]==read['value'],'nonpointer mask literal')
   need([x['value']for x in r['literal_reads']]==[0xFFFD0000,0x0002000D],'signed packed sprite mask pair')
  else:raise ValueError('unknown typed HOF root')
 for row in p['candidates']:
  root=roots[row['root']];need(root['address']<=row['address']and row['address']+4<=root['address']+root['size'],'candidate wholly inside signed typed root')
  if row['kind']=='battle_anim_createsprite_operands':
   command=next(c for c in root['commands']if c['address']==row['command_address']);need(command['opcode']==2 and command['address']+6<=row['address']and row['address']+4<=command['address']+command['size'],'all four bytes inside argc and numeric arguments; never template pointer')
 for row in p['branch_candidates']:
  r=roots[row['root']];need(r['kind']=='dpcm4'and r['address']+16<=row['address']and row['address']+4<=r['address']+r['size'],'all branch-looking bytes inside encoded audio')
 return dict(status='PASS_TYPED_HOF_TAIL_REFERENCE_CLASSIFICATION',address=LO,size=260,literal_candidates=22,thumb_bl_candidates=3,root_count=17,candidate_types=p['candidate_types'],branch_candidate_types=p['branch_candidate_types'],unclassified_candidates=0)
