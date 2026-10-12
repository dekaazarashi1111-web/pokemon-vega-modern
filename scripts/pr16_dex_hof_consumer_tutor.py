"""固定Stage38の実byteから旧T09の5個の数値mask読取経路だけを検証する。

私有ROMの逆patch・再構築・実行はしない。公開出力はidentity/型/意味検査のみ。
"""
from __future__ import annotations
import hashlib,json,struct,zipfile,urllib.request
from pathlib import Path
BASE=0x08000000
HISTORICAL=dict(size=33554432,sha256='17240646e2aa58be929bbb73c8176673f2c31d841733d7712ae2fab912f87e39')
CURRENT=dict(size=33554432,sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
OWNER=dict(address=0x09FCC1E0,size=25936,sha256='a44431aea3f197a030bd496482aa91b747f260d19822d8ab4eedc0a8363b441f')
HIT=dict(address=0x09FCD7A8,size=4,sha256='aee5e311f93b083c1cbcb45af72d17f997942cde34f2d5fbf4268d446d10a19f')
ENTRY=0x09110228
ROOT=0x08121420
LITERAL=0x09110384
ROW=OWNER['address']+278*20
SOURCE_BLOBS={
 'config/github_private_environment.json':'32913e02fdb71f007d3c65801a9bb5d3f5a6c210',
 'config/move_distribution_v4.json':'21c9e42f655ff1c910778211f5e8a347ae0ed52d',
 'config/species_surface.json':'fe52aa5d43f860a80f3b7b24681bf874ba9a8e28',
 'scripts/build_species_surface.py':'6bf37ee88f559ba76997dabb8a0c35127c088342',
 'config/cfru_vega_minimal.h':'dacccff5804eafd687773c77b880a9108ae45f3f',
 'vendor/upstream/CFRU-JP/src/item.c':'ea5302c0dc2bb9fc92e665aab6015a27ff4275d7',
 'vendor/upstream/CFRU-JP/include/pokemon.h':'b18f2ee2a1517efa8aeb742daedac9e778d73d7a',
}

def need(v,msg):
 if not v:raise ValueError(msg)
def identity(b):return dict(size=len(b),sha256=hashlib.sha256(b).hexdigest())
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def chunk(raw,a,n):
 need(type(a)is int and type(n)is int and 0<=a-BASE<=len(raw)-n and n>0,'bounded ROM read')
 return raw[a-BASE:a-BASE+n]
def u16(raw,a):return struct.unpack('<H',chunk(raw,a,2))[0]
def u32(raw,a):return struct.unpack('<I',chunk(raw,a,4))[0]
def span(raw,a,n):return dict(address=a,**identity(chunk(raw,a,n)))
def sign(v,b):return v-(1<<b)if v&(1<<(b-1))else v

def decode(raw,a):
 """必要なThumb-1だけ。unknownは停止し、raw命令値は返さない。"""
 h=u16(raw,a);top=h&0xf800
 if top in (0,0x800,0x1000):
  op={0:'lsl',0x800:'lsr',0x1000:'asr'}[top];n=(h>>6)&31
  return ('mov_reg',h&7,(h>>3)&7) if op=='lsl' and n==0 else (op,h&7,(h>>3)&7,n or 32)
 if top==0x1800:
  return ('mov_reg',h&7,(h>>3)&7) if h&0x600==0x400 and (h>>6)&7==0 else ('sub3'if h&0x200 else 'add3',h&7,(h>>3)&7,'imm'if h&0x400 else 'reg',(h>>6)&7)
 if top in (0x2000,0x2800,0x3000,0x3800):return ({0x2000:'mov_imm',0x2800:'cmp_imm',0x3000:'add_imm',0x3800:'sub_imm'}[top],(h>>8)&7,h&255)
 if h&0xfc00==0x4000:
  op={0:'and',2:'lsl_reg',6:'sbc'}.get((h>>6)&15)
  need(op is not None,'unsupported scalar ALU')
  return(op,h&7,(h>>3)&7)
 if h&0xff87==0x4700:return('bx',(h>>3)&15)
 if top==0x4800:return('ldr_literal',(h>>8)&7,((a+4)&~3)+((h&255)*4))
 if top==0x6800:return('ldr_word',h&7,(h>>3)&7,((h>>6)&31)*4)
 if h&0xfe00 in(0xb400,0xbc00):return ('pop'if h&0x800 else 'push',tuple([i for i in range(8)if h&(1<<i)]+([15 if h&0x800 else 14]if h&0x100 else [])))
 if h&0xf000==0xd000 and(h>>8)&15<14:return('bcond',(h>>8)&15,a+4+sign(h&255,8)*2)
 if top==0xe000:return('b',a+4+sign(h&0x7ff,11)*2)
 if top==0xf000:
  lo=u16(raw,a+2);need(lo&0xf800==0xf800,'complete Thumb BL pair')
  return('bl',a+4+(sign(h&0x7ff,11)<<12)+((lo&0x7ff)<<1))
 raise ValueError('unsupported Thumb instruction at bounded consumer address')

# Public source semantics, not byte preimages copied from a modern replacement.
# Historical ROM must independently satisfy every operand/target/field below.
EXPECTED={
 0x228:('push',(3,4,5,6,7,14)),0x22a:('mov_imm',2,0),
 0x22c:('mov_reg',4,1),0x22e:('ldr_literal',7,0x09110380),
 0x230:('mov_imm',1,11),0x232:('mov_reg',6,0),0x234:('bl',0x09111c7a),
 0x238:('cmp_imm',4,151),0x23a:('bcond',8,0x09110290),
 0x23c:('lsl',0,0,16),0x23e:('lsr',3,0,16),0x240:('lsr',0,0,14),
 0x242:('add3',0,0,'reg',3),0x244:('ldr_literal',3,LITERAL),
 0x246:('ldr_word',3,3,0),0x248:('lsl',0,0,2),0x24a:('add3',0,0,'reg',3),
 0x24c:('cmp_imm',4,31),0x24e:('bcond',9,0x09110282),
 0x250:('mov_reg',2,4),0x252:('sub_imm',2,32),0x254:('lsl',3,2,24),0x256:('lsr',3,3,24),0x258:('cmp_imm',3,31),0x25a:('bcond',9,0x091102ba),
 0x25c:('mov_reg',2,4),0x25e:('sub_imm',2,64),0x260:('lsl',3,2,24),0x262:('lsr',3,3,24),0x264:('cmp_imm',3,31),0x266:('bcond',9,0x091102ac),
 0x268:('mov_reg',2,4),0x26a:('sub_imm',2,96),0x26c:('lsl',3,2,24),0x26e:('lsr',3,3,24),0x270:('cmp_imm',3,31),0x272:('bcond',8,0x091102c8),
 0x274:('mov_imm',3,1),0x276:('lsl_reg',3,2),0x278:('ldr_word',0,0,12),0x27a:('and',0,3),0x27c:('sub3',3,0,'imm',1),0x27e:('sbc',0,3),0x280:('b',0x0911028e),
 0x282:('mov_imm',3,1),0x284:('lsl_reg',3,4),0x286:('ldr_word',0,0,0),0x288:('and',0,3),0x28a:('sub3',3,0,'imm',1),0x28c:('sbc',0,3),0x28e:('pop',(3,4,5,6,7,15)),
 0x2ac:('mov_imm',3,1),0x2ae:('lsl_reg',3,2),0x2b0:('ldr_word',0,0,8),0x2b2:('and',0,3),0x2b4:('sub3',3,0,'imm',1),0x2b6:('sbc',0,3),0x2b8:('b',0x0911028e),
 0x2ba:('mov_imm',3,1),0x2bc:('lsl_reg',3,2),0x2be:('ldr_word',0,0,4),0x2c0:('and',0,3),0x2c2:('sub3',3,0,'imm',1),0x2c4:('sbc',0,3),0x2c6:('b',0x0911028e),
 0x2c8:('mov_imm',3,1),0x2ca:('sub_imm',4,128),0x2cc:('lsl_reg',3,4),0x2ce:('ldr_word',0,0,16),0x2d0:('and',0,3),0x2d2:('sub3',3,0,'imm',1),0x2d4:('sbc',0,3),0x2d6:('b',0x0911028e),
}

def sources(root,supplied=None):
 texts={};bindings={};supplied=supplied or{}
 for p,h in SOURCE_BLOBS.items():
  if p in supplied:raw=supplied[p]
  else:
   file=Path(root)/p;need(file.is_file()and not file.is_symlink(),'regular fixed source');raw=file.read_bytes()
  need(type(raw)is bytes and blob(raw)==h,'whole fixed source identity '+p)
  bindings[p]=dict(**identity(raw),git_blob_sha=h);texts[p]=raw.decode('utf8')
 cfg=json.loads(texts['config/move_distribution_v4.json']);surface=json.loads(texts['config/species_surface.json'])
 need({k:cfg['inputs']['stage38_rom'][k]for k in('size','sha256')}==HISTORICAL,'separate Stage38 input authority')
 need(cfg['stage38_roots']['tutor']==dict(site='0x08121420',expected='0x09FCC1E0'),'declared historical root authority')
 need(surface['counts']['canonical_species']==1621 and surface['counts']['tutor_bytes_per_species']==16,'serializer count remains16, never historical consumer stride')
 c=texts['vendor/upstream/CFRU-JP/src/item.c']
 for s in ('#define gTutorLearnsets ((ExpandedTutor_T*) *((u32*) 0x8121420))','if (tutorId < NUM_MOVE_TUTORS)','gTutorLearnsets[species][4]','u16 species = GetMonData(mon, MON_DATA_SPECIES, NULL);'):
  need(s in c,'pinned historical source scalar reader')
 need('#define NUM_MOVE_TUTORS 152'in texts['config/cfru_vega_minimal.h']and '#define MON_DATA_SPECIES           11'in texts['vendor/upstream/CFRU-JP/include/pokemon.h'],'fixed tutor count and species selector')
 return texts,bindings

def semantic_check(raw):
 """明示5word全経路の命令・branch・callee/root literalを実byteで確認。"""
 for offset,want in EXPECTED.items():
  got=decode(raw,0x09110000+offset)
  need(got==want,'historical numeric consumer semantic mismatch at '+hex(0x09110000+offset))
 need(decode(raw,0x09111c7a)==('bx',7),'GetMonData source-call register veneer')
 need(u32(raw,0x09110380)==0x0803f355,'source-call concrete GetMonData target')
 need(u32(raw,LITERAL)==ROOT and u32(raw,ROOT)==OWNER['address'],'concrete two-level historical table root')
 # The gate covers the entire u8 input; all accepted regular IDs select exactly one word.
 ids=[]
 for tutor in range(256):
  if tutor>151:continue
  if tutor<=31:word=0
  elif(tutor-32)&255<=31:word=1
  elif(tutor-64)&255<=31:word=2
  elif(tutor-96)&255<=31:word=3
  else:word=4
  need(word==tutor//32,'every gated input scalar field selection')
  ids.append((tutor,word,tutor%32))
 need(len(ids)==152 and {w for _,w,_ in ids}==set(range(5)),'complete finite regular ID domain')
 return dict(entry=ENTRY,regular_id_count=152,regular_id_min=0,regular_id_max=151,
  excluded_special_id_min=152,excluded_special_id_max=255,
  species_result_mask_bits=16,species_index=278,stride_bytes=20,word_count=5,
  entry_extent_bytes=20,word_offsets=[0,4,8,12,16],target_word_index=4,
  target_tutor_id_min=128,target_tutor_id_max=151,
  read_role='LE_U32_NUMERIC_COMPATIBILITY_MASK',result_role='MASK_AND_BIT_TO_BOOL',
  code_pointer_from_table=False,branch_pointer_from_table=False,stores_from_table=False,
  current_runtime_reachability_claimed=False,full_1621_species_historical_reader_safety_claimed=False,indirect_reference_completeness_claimed=False)

def historical_probe(raw,root,supplied=None):
 need(identity(raw)==HISTORICAL,'whole actual Stage38 candidate identity')
 _,bindings=sources(root,supplied)
 need(identity(chunk(raw,OWNER['address'],OWNER['size']))=={k:OWNER[k]for k in('size','sha256')},'entire historical T09 table owner')
 need(identity(chunk(raw,HIT['address'],4))=={k:HIT[k]for k in('size','sha256')},'historical hit identity')
 need(ROW+16==HIT['address']and OWNER['address']<=ROW<ROW+20<=OWNER['address']+OWNER['size'],'target whole20-byte consumer row inside immutable owner')
 semantics=semantic_check(raw)
 return dict(schema_version=1,status='PASS_HISTORICAL_T09_NUMERIC_CONSUMER_ONLY',historical_candidate=identity(raw),sources=bindings,
  historical_owner=OWNER,hit=HIT,row=span(raw,ROW,20),
  root_roles=[dict(**span(raw,ROOT,4),role='HISTORICAL_TUTOR_TABLE_ROOT',target=OWNER['address']),dict(**span(raw,LITERAL,4),role='CONSUMER_ROOT_LITERAL',target=ROOT)],
  consumer_roles=[dict(**span(raw,ENTRY,104),role='NUMERIC_GATE_STRIDE_WORD0_WORD3_RETURN'),dict(**span(raw,0x091102ac,44),role='NUMERIC_WORD1_WORD2_WORD4_RETURN'),dict(**span(raw,0x09110380,4),role='SPECIES_READER_LITERAL'),dict(**span(raw,0x09111c7a,2),role='SPECIES_READER_REGISTER_VENEER')],
  semantics=semantics,historical_typing_only=True,current_candidate_accepted=False,
  donor_eligible=False,rom_reconstructions=0,rom_writes=0,native_processes=0)

def bind_current(raw,owners,historical_raw,proof,root,supplied=None):
 """過去consumer証明と現actual owner束縛を分離。旧formalでは必ず拒否。"""
 need(identity(raw)==CURRENT,'whole exact current candidate')
 need(proof==historical_probe(historical_raw,root,supplied),'entire measured historical proof recomputed')
 matches=[x for x in owners if x['name']=='species_surface_tutor']
 need(len(matches)==1,'one exact current T09 owner');o=matches[0]
 need((o['address'],o['size'],o['after_sha256'])==(OWNER['address'],OWNER['size'],OWNER['sha256']),'current actual byte-owner authority')
 need(chunk(raw,OWNER['address'],OWNER['size'])==chunk(historical_raw,OWNER['address'],OWNER['size']),'entire historical and current T09 bytes equal')
 need(identity(chunk(raw,HIT['address'],4))=={k:HIT[k]for k in('size','sha256')},'all current hit bytes same')
 return dict(status='PASS_CURRENT_T09_HISTORICAL_NUMERIC_TYPE',candidate=identity(raw),historical_candidate=HISTORICAL,hit=HIT,actual_owner=OWNER,row=proof['row'],semantics=proof['semantics'],historical_typing_only=True,current_runtime_reachability_claimed=False,retirement_completeness_claimed=False,donor_eligible=False)

def archive_input(path,root,supplied=None):
 """既存固定archive全体と単一Stage38 memberを別々に全SHA検証する。"""
 texts,_=sources(root,supplied);cfg=json.loads(texts['config/github_private_environment.json']);contract=json.loads(texts['config/move_distribution_v4.json'])['inputs']['stage38_rom']
 spec=archive_spec(cfg,json.loads(texts['config/move_distribution_v4.json'])['inputs']['stage38_rom'])
 path=Path(path);need(path.is_file()and not path.is_symlink(),'regular historical source archive')
 h=hashlib.sha256();size=0
 with path.open('rb')as f:
  while b:=f.read(1024*1024):size+=len(b);need(size<=spec['size'],'bounded pinned archive');h.update(b)
 need(dict(size=size,sha256=h.hexdigest())=={k:spec[k]for k in('size','sha256')},'whole existing historical archive identity')
 with zipfile.ZipFile(path)as z:
  need(z.namelist().count(contract['path'])==1,'one historical input member')
  item=z.getinfo(contract['path']);need(not item.is_dir()and item.external_attr>>28!=10 and item.file_size==HISTORICAL['size'],'bounded regular historical member')
  raw=z.read(item)
 need(identity(raw)==HISTORICAL,'whole historical member identity')
 return raw

def fetch_archive(work,root,supplied=None):
 """既存source契約と同じreleaseだけ。出力に私有入力所在を含めない。"""
 texts,_=sources(root,supplied);cfg=json.loads(texts['config/github_private_environment.json'])
 spec=archive_spec(cfg,json.loads(texts['config/move_distribution_v4.json'])['inputs']['stage38_rom'])
 work=Path(work);work.mkdir(parents=True,exist_ok=True);p=work/spec['name']
 need(not p.exists(),'one private historical fetch, no overwrite')
 url='https://github.com/dekaazarashi1111-web/pokemon-vega-modern/releases/download/'+cfg['release']['tag']+'/'+spec['name']
 h=hashlib.sha256();size=0
 with urllib.request.urlopen(url,timeout=120)as response,p.open('xb')as out:
  while b:=response.read(1024*1024):
   size+=len(b);need(size<=spec['size'],'bounded historical download');h.update(b);out.write(b)
 need(dict(size=size,sha256=h.hexdigest())=={k:spec[k]for k in('size','sha256')},'whole original downloaded archive')
 return p


def archive_spec(cfg,contract):
 """保存済み契約のdestinationだけで必要archiveを選ぶ。入力所在の重複記録をしない。"""
 parent=Path(contract['path']).parent.as_posix()
 matches=[a for a in cfg['archives']if any(s['destination']==parent for s in a['sources'])]
 need(len(matches)==1,'one exact existing archive for historical contract')
 return matches[0]

KIND='historical_t09_tutor_numeric_mask'

def geometry(e):
 need(set(e)=={'historical','current','hit'},'closed historical/current split numeric evidence')
 h,c,hit=e['historical'],e['current'],e['hit']
 need(h['status']=='PASS_HISTORICAL_T09_NUMERIC_CONSUMER_ONLY'and h['historical_candidate']==HISTORICAL and h['historical_owner']==OWNER,'separate exact historical candidate/table')
 need(c['status']=='PASS_CURRENT_T09_HISTORICAL_NUMERIC_TYPE'and c['candidate']==CURRENT and c['historical_candidate']==HISTORICAL and c['actual_owner']==OWNER,'whole current actual owner tied to historical whole bytes')
 need(h['hit']==c['hit']=={k:hit[k]for k in('address','size','sha256')}==HIT,'same exact original four-byte hit')
 need(h['row']==c['row']and h['row']['address']==ROW and h['row']['size']==20 and ROW+16==HIT['address'],'exact species278 historical20-byte row/word4')
 semantics=h['semantics'];need(semantics==c['semantics']and semantics['stride_bytes']==20 and semantics['word_offsets']==[0,4,8,12,16]and semantics['word_count']==5 and semantics['regular_id_count']==152 and semantics['target_word_index']==4 and semantics['read_role']=='LE_U32_NUMERIC_COMPATIBILITY_MASK','actual complete five-word scalar consumer')
 need(h['historical_typing_only']is c['historical_typing_only']is True and c['current_runtime_reachability_claimed']is c['retirement_completeness_claimed']is c['donor_eligible']is False,'historical typing never grants retirement or current reachability')
 return HIT['address'],4

def regions(raw,latest,inherited,historical_raw,proof,root,supplied=None):
 import pr16_dex_hof_donor as d
 current=bind_current(raw,latest['placement']['owner_byte_audit'],historical_raw,proof,root,supplied)
 hit=next(h for h in inherited['hits']if h['address']==HIT['address'])
 need(hit['accepted']is False and {k:hit[k]for k in('address','size','sha256')}==HIT,'exact inherited unknown remains eligible only for typed classification')
 evidence=dict(historical=proof,current=current,hit=hit);a,n=geometry(evidence)
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status=current['status'],newly_classified=1,historical_candidate=HISTORICAL,current_candidate=CURRENT,actual_owner=OWNER,historical_typing_only=True,retirement_completeness_claimed=False,donor_eligible=False)
