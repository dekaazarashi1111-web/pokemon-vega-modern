"""MOVE_AMNESIAの最初のloadspritegfxから有限LZ10 payload一件を分類する。"""
from pathlib import Path
import hashlib,json,re,struct
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=dict(size=33554432,sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
KIND='rooted_battle_animation_lz77'
HIT=0x08C0DF31
SELECT=dict(move_id=133,move_symbol='MOVE_AMNESIA',command_opcode=0,tag=10093,tag_symbol='ANIM_TAG_AMNESIA',table_index=93)
CLAIMS=dict(finite_static_consumer_root=True,allocation_success_path_only=True,actual_screen_rendered=False,natural_battle_reachability=False,whole_animation_table_extent=False,indirect_reference_completeness_claimed=False,donor_leased=False)
ROOT=Path(__file__).resolve().parents[1]
FIELDS={'schema_version','required_candidate','sources','accepted_root_review','accepted_window_names','accepted_root_names','selection','move_slot','command','consumer_windows','consumer_literals','table_row','asset','decoded','hit','claims','lz_header'}
NEW_WINDOWS={'loadspritegfx_first_sheet':(0x090C5D08,0x24),'interwork_r3':(0x090C69D0,2),'sheet_decompress_to_bios':(0x0800E9E8,0x1E),'bios_lz77_wram':(0x081C7A90,4)}
LITERALS={'script_pointer':(0x090C5D54,0x02037E08),'negative_tag_base':(0x090C5D58,0xFFFFD8F0),'pic_table':(0x090C5D5C,0x0900A304),'sheet_loader':(0x090C5D60,0x0800E9E9)}
W_NAMES=['DoMoveAnim_hook','CFRU_DoMoveAnim','LaunchBattleAnimation_with_installed_illusion_hook','RunAnimScriptCommand','dispatch_r0_trampoline','loadspritegfx_hook']
R_NAMES=['DoMoveAnim_hook_target','DoMoveAnim_gMoveAnimations','DoMoveAnim_LaunchBattleAnimation','legacy_gMoveAnimations_repoint','LaunchBattleAnimation_RunAnimScriptCommand','RunAnimScriptCommand_table','dispatch_slot0_loadspritegfx','loadspritegfx_hook_target']

def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')

def source_proof(review,sources):
 need(review['sources']==SOURCE_ROWS,'independently fixed whole source bindings')
 for row in SOURCE_ROWS:
  value=sources[row['local']]
  need(identity(value)=={k:row[k]for k in('size','sha256')}and blob(value)==row['git_blob_sha'],'whole fixed public source '+row['local'])
 text={k:v.decode()for k,v in sources.items()if k in {r['local']for r in SOURCE_ROWS}}
 need(re.search(r'#define\s+MOVE_AMNESIA\s+0x85\b',text['cfru-moves.h']),'source-defined exact move133')
 need(re.search(r'#define\s+ANIM_SPRITES_START\s+10000\b',text['cfru-include_battle_anim.h'])and re.search(r'#define\s+ANIM_TAG_AMNESIA\s+\(ANIM_SPRITES_START\s*\+\s*93\)',text['cfru-include_battle_anim.h']),'independent C sprite base and tag offset')
 defs=text['cfru-anim-defines.s']
 need(re.search(r'\.equ\s+ANIM_TAG_AMNESIA,\s*0x276d\b',defs),'same assembler tag10093')
 need(re.search(r'\.macro\s+animparticle offset size tag\s+\.word \\offset\s+\.hword \\size\s+\.hword \\tag\s+\.endm',defs),'source 4+2+2-byte particle serializer')
 table=text['cfru-particle-table.s'].split('gBattleAnimPicTable:',1)[1].split('gBattleAnimPaletteTable:',1)[0]
 rows=[line.strip().split(' ',1)[1].split(',')for line in table.splitlines()if line.strip().startswith('animparticle ')]
 need(len(rows)==371 and [s.strip()for s in rows[93]]==['0x8C0DD94','0x1000','ANIM_TAG_AMNESIA'],'exact designated source row93, no neighboring-tag substitution')
 need(re.search(r'\.macro\s+loadspritegfx tag:req\s+\.byte 0x0\s+\.2byte \\tag\s+\.endm',text['pret-battle-anim-script.inc']),'exact first command format')
 strip=lambda t:re.sub(r'//[^\n]*|/\*.*?\*/','',t,flags=re.S)
 need(re.search(r'struct\s+CompressedSpriteSheet\s*\{\s*const u32 \*data;\s*u16 size;\s*u16 tag;\s*\};',strip(text['pret-sprite.h'])),'source pointer32/size16/tag16 ABI')
 src=text['cfru-battle-anims.c'];need('#define GET_TRUE_SPRITE_INDEX(i) ((i - ANIM_SPRITES_START))'in src and 'LoadCompressedSpriteSheetUsingHeap(&gBattleAnimPicTable[GET_TRUE_SPRITE_INDEX(index)]);'in src,'source command data selection')
 src=text['pret-decompress.c'];need('buffer = AllocZeroed(*((u32 *)src->data) >> 8);'in src and 'LZ77UnCompWram(src->data, buffer);'in src,'source allocation and exact payload consumer')
 bprj=text['cfru-BPRJ.ld'];need(re.search(r'LoadCompressedSpriteSheetUsingHeap\s*=\s*0x800E9E8\s*\|\s*1',bprj,re.I),'independent JP sheet consumer root')
 return SOURCE_ROWS

def accepted_roots(raw,review,root):
 need(review['accepted_root_review']==PRIOR and review['accepted_window_names']==W_NAMES and review['accepted_root_names']==R_NAMES,'immutable accepted move/dispatch roots only')
 path=Path(root)/PRIOR['path'];need(path.is_file()and not path.is_symlink(),'regular immutable accepted review')
 value=path.read_bytes();need(identity(value)=={k:PRIOR[k]for k in('size','sha256')}and blob(value)==PRIOR['git_blob_sha'],'accepted root review whole identity')
 prior=json.loads(value);windows=[w for name in W_NAMES for w in prior['windows']if w['name']==name];roots=[w for name in R_NAMES for w in prior['roots']if w['name']==name]
 need(len(windows)==len(W_NAMES)and len(roots)==len(R_NAMES),'all exact accepted windows and roots')
 for w in windows+roots:d.signed(raw,w)
 for w in roots:need(d.u32(raw,w['address'])==w['value'],'actual accepted root field')
 by={w['name']:w for w in roots}
 need(by['DoMoveAnim_gMoveAnimations']['value']==by['legacy_gMoveAnimations_repoint']['value']==0x0904A6D4,'same accepted actual JP move table')
 need(by['RunAnimScriptCommand_table']['value']==by['dispatch_slot0_loadspritegfx']['address']==0x08371F8C and by['dispatch_slot0_loadspritegfx']['value']==0x0807200D and by['loadspritegfx_hook_target']['value']==0x090C5D09,'accepted opcode0 enters the modeled new consumer')
 return windows+roots

def geometry(e):
 need(set(e)=={'asset','decoded','selection','table_row','command','hit','claims','root_verified'},'closed new animation LZ witness')
 need(e['asset']==ASSET and e['decoded']==DECODED and e['selection']==SELECT and e['claims']==CLAIMS and e['root_verified']is True,'exact finite source payload geometry and limited claims')
 need(e['table_row']['address']==0x0900A304+93*8 and e['table_row']['size']==8 and e['command']['address']==0x081AEBB1 and e['command']['size']==3 and e['hit']['address']==HIT and e['hit']['size']==4,'exact descriptor/command/hit windows')
 need(d.contains(ASSET['address']+4,ASSET['address']+ASSET['size'],HIT,4),'only payload, never LZ header or terminal padding')
 return ASSET['address']+4,ASSET['size']-4

def _regions(raw,inherited,review,sources,root=ROOT):
 need(set(review)==FIELDS and review['schema_version']==1 and review['required_candidate']==CANDIDATE and review['selection']==SELECT and review['claims']==CLAIMS,'closed current-bound one-asset scope')
 source_proof(review,sources);prior_roles=accepted_roots(raw,review,root)
 need(review['asset']==ASSET and review['decoded']==DECODED,'independent complete stream and decoded identities')
 need({w['label']:(w['address'],w['size'])for w in review['consumer_windows']}==NEW_WINDOWS and len(review['consumer_windows'])==len(NEW_WINDOWS),'every new finite consumer window exactly once')
 for w in review['consumer_windows']:d.signed(raw,w)
 for label,program in PROGRAMS.items():
  a,n=NEW_WINDOWS[label];need(decode(raw,a,n)==program,'all source-corresponding Thumb roles '+label)
 need(half(raw,0x081C7A90)==(0xDF00|0x11)and half(raw,0x081C7A92)==(0x4700|(14<<3)),'actual BIOS LZ77 Wram SWI11 and BX LR')
 need({w['label']:(w['address'],w['value'])for w in review['consumer_literals']}==LITERALS and len(review['consumer_literals'])==len(LITERALS),'closed exact new consumer literals')
 for w in review['consumer_literals']:
  need(w['size']==4,'complete literal role');d.signed(raw,w);need(d.u32(raw,w['address'])==w['value'],'actual new literal')
 slot,cmd,row=review['move_slot'],review['command'],review['table_row']
 for w in (slot,cmd,row,review['asset'],review['hit']):d.signed(raw,w)
 need(slot['address']==0x0904A6D4+133*4 and slot['size']==4 and slot['value']==d.u32(raw,slot['address'])==cmd['address']==0x081AEBB1,'actual source move133 table selection')
 need(cmd['size']==3 and chunk(raw,cmd['address'],3)==struct.pack('<BH',0,10093),'first command selects tag10093 with no preceding callback')
 need(row['address']==0x0900A304+(10093-10000)*8 and row['size']==8 and chunk(raw,row['address'],8)==struct.pack('<IHH',0x08C0DD94,4096,10093),'whole source exact descriptor and selected index stride8')
 need(review['lz_header']['address']==ASSET['address']and review['lz_header']['size']==4,'complete separate LZ header read role');d.signed(raw,review['lz_header'])
 enc,dec=d.decode_lz_at(raw,ASSET['address']);need(identity(enc)=={k:ASSET[k]for k in('size','sha256')}and identity(dec)==DECODED,'exact consumed LZ77 stream and decoded4096')
 hit=review['hit'];original=next(h for h in inherited['hits']if h['address']==HIT)
 need(hit==original and hit['accepted']is False and not hit['owner_candidates']and hit['kind']=='ALL_BYTE_START_U32_ALL_ROM_MIRRORS','unchanged original unowned unknown only')
 evidence={k:review[k]for k in('asset','decoded','selection','table_row','command','hit','claims')};evidence['root_verified']=True
 a,n=geometry(evidence)
 roles=prior_roles+review['consumer_windows']+review['consumer_literals']+[slot,cmd,row,review['lz_header']]
 return[d.TypedRegion(a,a+n,KIND,evidence)],dict(status='PASS_FINITE_AMNESIA_ANIMATION_LZ77_CONSUMER',count=1,hit=HIT,asset=ASSET,decoded=DECODED,source_bindings=SOURCE_ROWS,protected_read_windows=roles,claims=CLAIMS)

def regions(raw,latest,inherited,review,sources,root=ROOT):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'whole current0641 candidate mandatory')
 return _regions(raw,inherited,review,sources,root)

SOURCE_ROWS = [{'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': 'fc4168cbc9f43ef084afb04ff4ec8c81f9390592',
  'local': 'cfru-anim-defines.s',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': '166cbae334e3c45cb0d694fb483b8ac13b9cc84dc4bd64eb8d04ee696c1e84e4',
  'size': 33164,
  'source': 'anim_defines.s'},
 {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': '814f613a56d1314a462d5a4aebcca8bb3cdf9010',
  'local': 'cfru-particle-table.s',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': 'ee2d106484b531e17c52d9edb2d966ed1a214685c19fbf6d186328e67372d9fa',
  'size': 39352,
  'source': 'assembly/data/anim_particle_table.s'},
 {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': '444712bfec68c13fabffd3e167d380b6c23770ba',
  'local': 'cfru-moves.h',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': 'bc2ae17e444625fa2e1727d42c50a24f6758da26e44229a6f12a3afa3a275d79',
  'size': 30601,
  'source': 'include/constants/moves.h'},
 {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': '096a8763a4260052566ed029f841bc68e561d269',
  'local': 'cfru-battle-anims.c',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': '4893fda793e75356672e8b1be3bca4bd54fe562774fd8b07ed9f8f9ba501aff3',
  'size': 192535,
  'source': 'src/battle_anims.c'},
 {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
  'local': 'cfru-BPRJ.ld',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
  'size': 68505,
  'source': 'BPRJ.ld'},
 {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
  'git_blob_sha': 'f4740f917ed9ae7e0fd967107e1e63733bb8c66a',
  'local': 'pret-decompress.c',
  'repository': 'pret/pokefirered',
  'sha256': 'f190145b3948c1c22213e1a540f261aba89592ed9f30b6d13fa25b78ac417c7f',
  'size': 11157,
  'source': 'src/decompress.c'},
 {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
  'git_blob_sha': '6a1b272119ce6e3a8dcf45adf2eef8923a6d5175',
  'local': 'pret-sprite.h',
  'repository': 'pret/pokefirered',
  'sha256': 'a77aa1c837dfb58cf60b3eac299c7cc29a23ce27735ba710b9e8eeed102bf773',
  'size': 9368,
  'source': 'include/sprite.h'},
 {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
  'git_blob_sha': '15c48c39f5860efe132e782c22a6cedb0f8d5ac3',
  'local': 'pret-battle-anim-script.inc',
  'repository': 'pret/pokefirered',
  'sha256': 'cb193c567289983c26ed8acaa8dd64501c64c7e088e28995c49439333b52b27c',
  'size': 4279,
  'source': 'asm/macros/battle_anim_script.inc'},
 {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
  'git_blob_sha': '30f9a7ad2482d1767f5c70ee30a3c85528605bb3',
  'local': 'pret-battle-anim.c',
  'repository': 'pret/pokefirered',
  'sha256': '5883d9ee0483120ef67461952f5880499f322fb1c706cc213ca13c0c2b0e88c5',
  'size': 46944,
  'source': 'src/battle_anim.c'},
 {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
  'git_blob_sha': '68822edced83efcff0dc1893ec5052ba59875750',
  'local': 'cfru-include_battle_anim.h',
  'repository': 'kapibarasan000/CFRU-JP',
  'sha256': 'fd80eac8342c2452e9cb62f7b86b6db651d8136c25c9a6eb1369c1a92e4afb98',
  'size': 28504,
  'source': 'include/battle_anim.h'}]
PRIOR = {'git_blob_sha': 'd119a7e06a5d0b45c4c41f9ff4aafe847a68ef50',
 'path': 'content/modernization/pr16_dex_hof_reference_song_review.json',
 'sha256': '754bb9e4f4af3d33e9ff9724bf394f34ee12ff02a1e95f0052082350ef658b2c',
 'size': 25500}
ASSET = {'address': 146857364, 'size': 1725, 'sha256': '7290f1e8474951c3022f75e2e7cd8aae442dd61b4dfac5b9d44fe7cace76bff2'}
DECODED = {'size': 4096, 'sha256': 'd99c7d9e90665de0bb3b7330068768f1510ed5899b45dd1a208b1873f4eab844'}

def decode(raw,address,size):
 result=[];pc=address;end=address+size
 while pc<end:
  op=int.from_bytes(d.chunk(raw,pc,2),'little');n=2
  if op&0xF800==0xF000:
   d.need(pc+4<=end,'whole Thumb BL');x=('bl',code.thumb_bl(d.chunk(raw,pc,4),pc));n=4
  elif op&0xE000==0 and op&0x1800!=0x1800:
   x=(('lsls','lsrs','asrs')[(op>>11)&3],op&7,(op>>3)&7,(op>>6)&31)
  elif op&0xF800==0x1800:
   x=('subs3'if op&0x200 else'adds3',op&7,(op>>3)&7,'imm'if op&0x400 else'reg',(op>>6)&7)
  elif op&0xE000==0x2000:
   x=(('movs','cmp_imm','adds8','subs8')[(op>>11)&3],(op>>8)&7,op&255)
  elif op&0xFC00==0x4000:
   x=(('ands','eors','lsls_reg','lsrs_reg','asrs_reg','adcs','sbcs','rors','tst','negs','cmp_reg','cmn','orrs','muls','bics','mvns')[(op>>6)&15],op&7,(op>>3)&7)
  elif op&0xFC00==0x4400:
   kind=(op>>8)&3;rd=(op&7)|((op>>4)&8);rs=(op>>3)&15
   if kind==3:d.need(op&0x87==0,'only ARMv4T BX');x=('bx',rs)
   else:x=(('add_high','cmp_high','mov_high')[kind],rd,rs)
  elif op&0xF800==0x4800:x=('ldr_literal',(op>>8)&7,((pc+4)&~3)+(op&255)*4)
  elif op&0xF000==0x5000:
   x=(('str_reg','strh_reg','strb_reg','ldrsb_reg','ldr_reg','ldrh_reg','ldrb_reg','ldrsh_reg')[(op>>9)&7],op&7,(op>>3)&7,(op>>6)&7)
  elif op&0xE000==0x6000:
   byte=bool(op&0x1000);load=bool(op&0x800);x=(('ldr'if load else'str')+('b'if byte else''),op&7,(op>>3)&7,((op>>6)&31)*(1 if byte else 4))
  elif op&0xF000==0x8000:x=('ldrh'if op&0x800 else'strh',op&7,(op>>3)&7,((op>>6)&31)*2)
  elif op&0xF000==0x9000:x=('ldr_sp'if op&0x800 else'str_sp',(op>>8)&7,(op&255)*4)
  elif op&0xF000==0xA000:x=('add_sp'if op&0x800 else'add_pc',(op>>8)&7,(op&255)*4)
  elif op&0xFF00==0xB000:x=('sub_sp'if op&0x80 else'add_sp_imm',(op&127)*4)
  elif op&0xFE00 in(0xB400,0xBC00):
   pop=bool(op&0x800);regs=tuple(i for i in range(8)if op&(1<<i))+( (15 if pop else 14,) if op&0x100 else())
   x=('pop'if pop else'push',regs)
  elif op&0xF000==0xD000:
   condition=(op>>8)&15;d.need(condition<14,'ordinary conditional branch');offset=op&255;offset=offset-256 if offset&128 else offset;x=('b_cond',condition,pc+4+2*offset)
  elif op&0xF800==0xE000:
   offset=op&2047;offset=offset-2048 if offset&1024 else offset;x=('b',pc+4+2*offset)
  else:d.need(False,'unmodeled ARMv4T instruction')
  result.append((pc,x));pc+=n
 d.need(pc==end,'exact complete Thumb window')
 return result

PROGRAMS = {'interwork_r3': [(151808464, ('bx', 3))],
 'loadspritegfx_first_sheet': [(151805192, ('push', (4, 5, 6, 14))),
                               (151805194, ('ldr_literal', 5, 151805268)),
                               (151805196, ('ldr', 2, 5, 0)),
                               (151805198, ('adds3', 3, 2, 'imm', 1)),
                               (151805200, ('str', 3, 5, 0)),
                               (151805202, ('ldrb', 4, 3, 1)),
                               (151805204, ('ldr_literal', 3, 151805272)),
                               (151805206, ('mov_high', 12, 3)),
                               (151805208, ('ldrb', 2, 2, 1)),
                               (151805210, ('lsls', 4, 4, 8)),
                               (151805212, ('orrs', 4, 2)),
                               (151805214, ('add_high', 4, 12)),
                               (151805216, ('ldr_literal', 0, 151805276)),
                               (151805218, ('lsls', 6, 4, 3)),
                               (151805220, ('adds3', 0, 6, 'reg', 0)),
                               (151805222, ('ldr_literal', 3, 151805280)),
                               (151805224, ('bl', 151808464))],
 'sheet_decompress_to_bios': [(134277608, ('push', (4, 5, 14))),
                              (134277610, ('sub_sp', 8)),
                              (134277612, ('adds3', 4, 0, 'imm', 0)),
                              (134277614, ('ldr', 0, 4, 0)),
                              (134277616, ('ldr', 0, 0, 0)),
                              (134277618, ('lsrs', 0, 0, 8)),
                              (134277620, ('bl', 134228912)),
                              (134277624, ('adds3', 5, 0, 'imm', 0)),
                              (134277626, ('cmp_imm', 5, 0)),
                              (134277628, ('b_cond', 0, 134277666)),
                              (134277630, ('ldr', 0, 4, 0)),
                              (134277632, ('adds3', 1, 5, 'imm', 0)),
                              (134277634, ('bl', 136084112))]}
