"""登録animation背景3資産内4hitの有限LZ型。自然playや描画成功は主張しない。"""
import ast,copy,hashlib,json,re,struct,zlib,binascii
import pr16_dex_hof_animation_registered_roots as ab
import pr16_dex_hof_extra_roots as prior
import pr16_dex_hof_callback_party as party
import pr16_dex_hof_runtime_party as rt
import pr16_dex_hof_menu_text as engine
import pr16_dex_hof_donor as d
need,identity,chunk=d.need,d.identity,d.chunk
exact,encoded=prior.exact,prior.encoded
CANDIDATE,DIAGNOSTIC=party.CANDIDATE,party.DIAGNOSTIC
KIND='registered_animation_background_minimum_lz_payload'
KINDS=(KIND,)
TYPE_CATEGORY='data'
HITS=CLASSIFIED_HITS=TARGET_HITS=(0x0917E399,0x0918BDD3,0x0918FBA2,0x0918FFDE)
HELD_HITS=()
CURSOR,FRAMES,SCRIPT_ACTIVE,FADE,TARGET,TASKS,PALETTE=0x02037E08,0x02037E14,0x02037E15,0x02037E4B,0x02037E4F,0x030050D0,0x020379EC
# 既独立source命令の必要範囲だけを再利用。旧scenarioを再実行しない。
REUSE_RANGES=((0x8071fcc,0x8071ffa),(0x8072230,0x807225e),(0x8076bb4,0x8076c06),(0x8076c08,0x8076c9e),(0x8076d10,0x8076d7c),(0x81c9df8,0x81c9e4a),(0x81c7ac8,0x81c7ace))
INS={a:i for a,i in prior.INS.items()if any(start<=a<end for start,end in REUSE_RANGES)}
WORDS={a:v for a,v in prior.WORDS.items()if any(i.kind=='literal'and i.args[1]==a for i in INS.values())}

def block(a,forms):
 for i in party.block(a,forms):
  need(i.address not in INS,'意味命令非重複');INS[i.address]=i
# source Cmd_fadetobg: script byte reader→real CreateTask→selected task data0 writer。
block(0x8072f44,[('push',16,True),('literal',1,0x8072f78),('mem',True,'word',2,1,0),('addi',0,2,1),('mem',False,'word',0,1,0),('mem',True,'byte',4,2,1),('imm','add',0,1),('mem',False,'word',0,1,0),('literal',0,0x8072f7c),('imm','mov',1,5),('call',0x8076bb4),('shift','lsl',0,0,24),('shift','lsr',0,0,24),('literal',2,0x8072f80),('shift','lsl',1,0,2),('add',1,1,0),('shift','lsl',1,1,3),('add',1,1,2),('mem',False,'half',4,1,8),('literal',1,0x8072f84),('imm','mov',0,1),('mem',False,'byte',0,1,0),('pop',16,False),('pop',1,False),('bx',0)])
# source Cmd_fadetobgfromset reads first two byte IDs; target-side branch chooses operand0.
block(0x8072f88,[('push',112,True),('literal',1,0x8072fc4),('mem',True,'word',0,1,0),('addi',2,0,1),('mem',False,'word',2,1,0),('mem',True,'byte',6,0,1),('mem',True,'byte',5,2,1),('imm','add',0,4),('mem',False,'word',0,1,0),('literal',0,0x8072fc8),('imm','mov',1,5),('call',0x8076bb4),('shift','lsl',0,0,24),('shift','lsr',4,0,24),('literal',0,0x8072fcc),('mem',True,'byte',0,0,0),('call',0x8074968),('shift','lsl',0,0,24),('imm','cmp',0,0),('branch',1,0x8072fd4)])
block(0x8072fd4,[('literal',1,0x8072fec),('shift','lsl',0,4,2),('add',0,0,4),('shift','lsl',0,0,3),('add',0,0,1),('mem',False,'half',6,0,8),('literal',1,0x8072ff0),('imm','mov',0,1),('mem',False,'byte',0,1,0),('pop',112,False),('pop',1,False),('bx',0)])
# source script goto, next waitbgfadeout/waitbgfadein ensure balanced dispatcher return.
block(0x8072f08,[('literal',3,0x8072f28),('mem',True,'word',0,3,0),('addi',2,0,1),('mem',False,'word',2,3,0),('mem',True,'byte',1,0,1),('mem',True,'byte',0,2,1),('shift','lsl',0,0,8),('add',1,1,0),('mem',True,'byte',0,2,2),('shift','lsl',0,0,16),('add',1,1,0),('mem',True,'byte',0,2,3),('shift','lsl',0,0,24),('add',1,1,0),('mem',False,'word',1,3,0),('bx',14)])
block(0x8073160,[('push',0,True),('literal',0,0x8073178),('mem',True,'byte',0,0,0),('imm','cmp',0,2),('branch',1,0x8073184)])
block(0x8073184,[('literal',1,0x8073190),('imm','mov',0,1),('mem',False,'byte',0,1,0),('pop',1,False),('bx',0)])
block(0x8073194,[('push',0,True),('literal',0,0x80731ac),('mem',True,'byte',2,0,0),('imm','cmp',2,0),('branch',1,0x80731b8)])
block(0x80731b8,[('literal',1,0x80731c4),('imm','mov',0,1),('mem',False,'byte',0,1,0),('pop',1,False),('bx',0)])
# Task_FadeToBg state0→state1→state2 is produced by the actual task stores.
block(0x8072ff4,[('push',240,True),('spadd',-4),('shift','lsl',0,0,24),('shift','lsr',5,0,24),('literal',1,0x8073028),('shift','lsl',0,5,2),('add',0,0,5),('shift','lsl',0,0,3),('add',4,0,1),('mem',True,'half',6,4,28),('imm','mov',0,28),('signed_load','half',3,4,0),('addi',7,1,0),('imm','cmp',3,0),('branch',1,0x807302c),('spmem',False,3,0),('imm','mov',0,232),('imm','mov',1,0),('imm','mov',2,0),('imm','mov',3,16),('call',0x8070a08),('mem',True,'half',0,4,28),('imm','add',0,1),('mem',False,'half',0,4,28),('jump',0x80730bc)])
block(0x807302c,[('literal',2,0x8073048),('mem',True,'byte',1,2,7),('imm','mov',0,128),('alu','and',0,1),('imm','cmp',0,0),('branch',1,0x80730bc),('imm','cmp',3,1),('branch',1,0x8073050),('addi',0,6,1),('mem',False,'half',0,4,28),('literal',1,0x807304c),('imm','mov',0,2),('mem',False,'byte',0,1,0),('jump',0x8073094)])
block(0x8073050,[('imm','cmp',3,2),('branch',1,0x8073094),('mem',True,'half',0,4,8),('shift','lsl',2,0,16),('shift','asr',1,2,16),('imm','mov',0,1),('alu','neg',0,0),('compare',1,0),('branch',1,0x8073068)])
block(0x8073068,[('shift','lsr',0,2,16),('call',0x80730c8)])
block(0x8073094,[('mem',True,'byte',1,2,7),('imm','mov',0,128),('alu','and',0,1),('shift','lsl',0,0,24),('shift','lsr',4,0,24),('imm','cmp',4,0),('branch',1,0x80730bc),('shift','lsl',0,5,2),('add',0,0,5),('shift','lsl',0,0,3),('add',0,0,7),('imm','mov',1,28),('signed_load','half',0,0,1),('imm','cmp',0,3),('branch',1,0x80730bc)])
block(0x80730bc,[('spadd',4),('pop',240,False),('pop',1,False),('bx',0)])
# LoadMoveBg: selected descriptor tilemap normal return, then actual image pointer→VRAM BIOS SWI12.
block(0x80730c8,[('push',48,True),('shift','lsl',0,0,16),('shift','lsr',0,0,16),('literal',5,0x8073104),('shift','lsl',4,0,1),('add',4,4,0),('shift','lsl',4,4,2),('addi',0,5,0),('imm','add',0,8),('add',0,4,0),('mem',True,'word',0,0,0),('literal',1,0x8073108),('call',0x800e574),('add',0,4,5),('mem',True,'word',0,0,0),('literal',1,0x807310c),('call',0x800e574)])
block(0x800e574,[('push',0,True),('call',0x81c7a8c),('pop',1,False),('bx',0)])
WORDS.update({0x8071d74:0x904a6d4,0x8371f9c:0x8072231,0x8371fd8:0x8072f09,0x8371fdc:0x8072f45,0x8371fe4:0x8073161,0x8371fe8:0x8073195,0x8372020:0x8072f89,0x8072f28:0x2037e08,0x8072f78:0x2037e08,0x8072f7c:0x8072ff5,0x8072f80:0x30050d0,0x8072f84:0x2037e4b,0x8072fc4:0x2037e08,0x8072fc8:0x8072ff5,0x8072fcc:0x2037e4f,0x8072fec:0x30050d0,0x8072ff0:0x2037e4b,0x8073028:0x30050d0,0x8073048:0x20379ec,0x807304c:0x2037e4b,0x8073104:0x9009f68,0x8073108:0x600d000,0x807310c:0x6008000,0x8073178:0x2037e4b,0x8073190:0x2037e14,0x80731ac:0x2037e4b,0x80731c4:0x2037e14,0x8076d78:0x30050d0})

# Input PNG parser and tile serializer are independent of the ROM decoder. Fixed indexed
# PNGs use packed 4-bit pixels, 256x112, no interlace; CRC and every filtered row are checked.
def png_pixels(b):
 need(b[:8]==b'\x89PNG\r\n\x1a\n','公開PNG signature');p=8;parts=[];header=None;palette=None;ended=False
 while p<len(b):
  need(p+12<=len(b),'PNG complete chunk');n=int.from_bytes(b[p:p+4],'big');typ=b[p+4:p+8];val=b[p+8:p+8+n]
  need(p+12+n<=len(b)and(binascii.crc32(typ+val)&0xffffffff)==int.from_bytes(b[p+8+n:p+12+n],'big'),'PNG chunk CRC/extent')
  if typ==b'IHDR':need(header is None,'PNG single IHDR');header=struct.unpack('>IIBBBBB',val)
  elif typ==b'PLTE':need(palette is None and n%3==0,'PNG palette');palette=val
  elif typ==b'IDAT':parts.append(val)
  elif typ==b'IEND':need(n==0 and p+12==len(b),'PNG exact IEND');ended=True
  p+=12+n
 need(ended and header==(256,112,4,3,0,0,0)and palette is not None,'固定PNG geometry/4bit indexed')
 stream=zlib.decompressobj();raw=stream.decompress(b''.join(parts))+stream.flush();need(stream.eof and not stream.unused_data and not stream.unconsumed_tail and len(raw)==129*112,'全PNG scanline extent')
 priorrow=[0]*128;pixels=[]
 for y in range(112):
  filt=raw[y*129];row=[];need(filt in range(5),'PNG filter')
  for x,v in enumerate(raw[y*129+1:(y+1)*129]):
   left=row[x-1]if x else 0;above=priorrow[x];corner=priorrow[x-1]if x else 0
   pred=left+above-corner;dist=[abs(pred-left),abs(pred-above),abs(pred-corner)];paeth=[left,above,corner][dist.index(min(dist))]
   value=(v+[0,left,above,(left+above)//2,paeth][filt])&255;row.append(value);pixels.extend((value>>4,value&15))
  priorrow=row
 need(len(pixels)==256*112 and all(p<len(palette)//3 for p in pixels),'PNG全index')
 return pixels

def encode_tiles(b,flags):
 need(flags.decode().strip()=='-fts -fh -m -mR4 -mzl -mu8 -mp2 -pzl -pe16 -g -gB4 -gzl -gu8 -ah112 -aw256','固定source grit options')
 pixels=png_pixels(b);seen={bytes(32):0};tiles=[bytes(32)]
 def variants(tile):
  pix=[(v>>shift)&15 for v in tile for shift in (0,4)]
  return [bytes(pix[y*8+x]|pix[y*8+x2]<<4 for y in ys for x,x2 in xs)for ys in(range(8),range(7,-1,-1))for xs in([(i,i+1)for i in range(0,8,2)],[(i,i-1)for i in range(7,-1,-2)])]
 for y in range(0,112,8):
  for x in range(0,256,8):
   p=[pixels[(y+j)*256+x+i]for j in range(8)for i in range(8)];tile=bytes(p[i]|p[i+1]<<4 for i in range(0,64,2))
   if tile not in seen:
    index=len(tiles);tiles.append(tile)
    for t in variants(tile):seen.setdefault(t,index)
 return b''.join(tiles)

SOURCE_IDS={'BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
             'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
             'local': 'BPRJ.ld',
             'source': 'BPRJ.ld',
             'repository': 'kapibarasan000/CFRU-JP',
             'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
             'size': 68505,
             'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/BPRJ.ld'},
 'Giga_Impact_Opponent.png': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                              'git_blob_sha': 'e5ed2e5f3e599b5e8861cba80bbb27a6fd71bcc3',
                              'local': 'Giga_Impact_Opponent.png',
                              'source': 'graphics/Backgrounds/Animation_Backgrounds/Giga_Impact_Opponent.png',
                              'repository': 'kapibarasan000/CFRU-JP',
                              'sha256': '6cca39328f09db740bad5710d3f80e9c6121fbfc38c56402841e9b29d133ca2a',
                              'size': 3239,
                              'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/graphics/Backgrounds/Animation_Backgrounds/Giga_Impact_Opponent.png'},
 'Nightmare.png': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                   'git_blob_sha': '153d919678dd03d8b3a08480b05731c66dbcf599',
                   'local': 'Nightmare.png',
                   'source': 'graphics/Backgrounds/Animation_Backgrounds/Nightmare.png',
                   'repository': 'kapibarasan000/CFRU-JP',
                   'sha256': '4715865d3b8032772764983a86400d3c24dbaa86f9c4405b4e9278fd70ea5bea',
                   'size': 3626,
                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/graphics/Backgrounds/Animation_Backgrounds/Nightmare.png'},
 'Sky_Day.png': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                 'git_blob_sha': 'd0b0f2c3f58878c31f31a51400b225898b1ffa6a',
                 'local': 'Sky_Day.png',
                 'source': 'graphics/Backgrounds/Animation_Backgrounds/Sky_Day.png',
                 'repository': 'kapibarasan000/CFRU-JP',
                 'sha256': 'f0bf8757263094d900b43f11d137a44b5a6e2c562afd9b07f2a7bd5a982c81e1',
                 'size': 7388,
                 'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/graphics/Backgrounds/Animation_Backgrounds/Sky_Day.png'},
 'cfru-anim_background_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                  'git_blob_sha': '2aa74a775408cda1f8ffae1b2bfe60873ffbb856',
                                  'local': 'cfru-anim_background_table.s',
                                  'source': 'assembly/data/anim_background_table.s',
                                  'repository': 'kapibarasan000/CFRU-JP',
                                  'sha256': '427be85c29b46f63195a1e67bb611be6218f5ef019af8eae2b34d713532331cc',
                                  'size': 5808,
                                  'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/anim_background_table.s'},
 'cfru-anim_backgrounds_graphics_defines.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                              'git_blob_sha': 'd5412780635c97ed44679dbd60bb231d8f20ae02',
                                              'local': 'cfru-anim_backgrounds_graphics_defines.s',
                                              'source': 'assembly/data/anim_backgrounds_graphics_defines.s',
                                              'repository': 'kapibarasan000/CFRU-JP',
                                              'sha256': '2b3b79ddacb3380bc22158cbd56cfaa20e79fbb7e871b98630eafd624483b86f',
                                              'size': 6456,
                                              'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/anim_backgrounds_graphics_defines.s'},
 'cfru-anim_defines.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                         'git_blob_sha': 'fc4168cbc9f43ef084afb04ff4ec8c81f9390592',
                         'local': 'cfru-anim_defines.s',
                         'source': 'anim_defines.s',
                         'repository': 'kapibarasan000/CFRU-JP',
                         'sha256': '166cbae334e3c45cb0d694fb483b8ac13b9cc84dc4bd64eb8d04ee696c1e84e4',
                         'size': 33164,
                         'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/anim_defines.s'},
 'cfru-attack-anim-table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                              'git_blob_sha': '2049efe7d416113b0b5be496e6a9c5ed6b305d1a',
                              'local': 'cfru-attack-anim-table.s',
                              'source': 'assembly/data/attack_anim_table.s',
                              'repository': 'kapibarasan000/CFRU-JP',
                              'sha256': '9c5ef07b85c3a0cbf809ad18cfeddf59d548a970d2df12f480ea93b6de9febb2',
                              'size': 1232828,
                              'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/assembly/data/attack_anim_table.s'},
 'gritflags.txt': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                   'git_blob_sha': '4a5b409b8bc381761df59f4a75a7cc84b5c9ba90',
                   'local': 'gritflags.txt',
                   'source': 'graphics/Backgrounds/Animation_Backgrounds/gritflags.txt',
                   'repository': 'kapibarasan000/CFRU-JP',
                   'sha256': '3085e9dbd3464b8824af9dc4a456ef5781c60bcb70a3085c930389dea29b538a',
                   'size': 75,
                   'url': 'https://github.com/kapibarasan000/CFRU-JP/blob/e24a16fe39e27ae162faf5b78596d1f3df18489d/graphics/Backgrounds/Animation_Backgrounds/gritflags.txt'},
 'pret-battle_anim.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                        'git_blob_sha': '30f9a7ad2482d1767f5c70ee30a3c85528605bb3',
                        'local': 'pret-battle_anim.c',
                        'source': 'src/battle_anim.c',
                        'repository': 'pret/pokefirered',
                        'sha256': '5883d9ee0483120ef67461952f5880499f322fb1c706cc213ca13c0c2b0e88c5',
                        'size': 46944,
                        'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/battle_anim.c'},
 'pret-task.c': {'commit': 'c75f352304d529f6ba92d4f74b9cf8b5c3810788',
                 'git_blob_sha': '01503dc7ae78cf2348524bfb5bbb89183640f944',
                 'local': 'pret-task.c',
                 'source': 'src/task.c',
                 'repository': 'pret/pokefirered',
                 'sha256': '8bdd5205ec396be7b66d6e384a82309b3cab59783d46fb8c4c991b2172d4868b',
                 'size': 5029,
                 'url': 'https://github.com/pret/pokefirered/blob/c75f352304d529f6ba92d4f74b9cf8b5c3810788/src/task.c'}}


EXPECTED_HITS=[{'accepted': False,
  'address': 152560537,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '2444281266349c37b5afdfcbed61c48309da3d388635193df08c0780da7f2603',
  'size': 4,
  'target': 167707120},
 {'accepted': False,
  'address': 152616403,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': '5d98e6b2dbcf4da280660fab6114884eb166087b91ce1ff597158f2c499a2078',
  'size': 4,
  'target': 167709252},
 {'accepted': False,
  'address': 152632226,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': 'b04ac6cb02102f9920c3e98dbaf278253fd54c32468446682894d6b51d866de4',
  'size': 4,
  'target': 167709450},
 {'accepted': False,
  'address': 152633310,
  'classification': 'UNCLASSIFIED',
  'kind': 'ALL_BYTE_START_U32_ALL_ROM_MIRRORS',
  'owner_candidates': [],
  'reason': 'no_complete_typed_asset_consumer_witness',
  'sha256': 'c259741d12103350cf749f6261cca4539b406ec33985e5fb3260a085b52fb340',
  'size': 4,
  'target': 167700736}]

ASSETS={'giga': {'address': 152557028,
          'bg_id': 33,
          'decoded': {'sha256': 'c4ad2f3057ab14f69e4ea2969a1c9b7b26e011f53953ae9c5ddffd82394e7b64', 'size': 8928},
          'descriptor_address': 151036148,
          'descriptor_values': [152557028, 152561544, 152560840],
          'hits': [152560537],
          'sha256': '7003087ccf3155a3f3b871e8ff38fb2e363930961be4eab38ca27f843dca3eca',
          'size': 3811,
          'source_png': 'Giga_Impact_Opponent.png'},
 'nightmare': {'address': 152613208,
               'bg_id': 29,
               'decoded': {'sha256': '35b583bf59cb860e6604ce269984165e3e9fdece4e71319b125d4341690627fc', 'size': 9664},
               'descriptor_address': 151036100,
               'descriptor_values': [152613208, 152617980, 152617224],
               'hits': [152616403],
               'sha256': '4188ccccf0c25a7b7202a62dd095c6a84e470552711d05f9a3af57299e1a348f',
               'size': 4015,
               'source_png': 'Nightmare.png'},
 'sky': {'address': 152625300,
         'bg_id': 58,
         'decoded': {'sha256': 'c528c7385cec1c2c60631c5b1964ff92bfd748281abe466e56298652f991f92f', 'size': 14304},
         'descriptor_address': 151036448,
         'descriptor_values': [152625300, 152618384, 152634860],
         'hits': [152632226, 152633310],
         'sha256': 'a630ddc5f934a5b31963f51f39fbbd658e93792830c55b39fb9474e5e9c2516f',
         'size': 9558,
         'source_png': 'Sky_Day.png'}}

ROOTS={'giga': {'bg_id': 33,
          'cell': 151301340,
          'command': 151057562,
          'frames': 11,
          'handler': 134688648,
          'index': 386,
          'next_cursor': 151057568,
          'opcode': 37,
          'script': 151057536},
 'nightmare': {'bg_id': 29,
               'cell': 151302508,
               'command': 151123014,
               'frames': 1,
               'handler': 134688580,
               'index': 678,
               'next_cursor': 151123016,
               'opcode': 20,
               'script': 151123008},
 'sky': {'bg_id': 58,
         'cell': 151303292,
         'command': 151191214,
         'frames': 1,
         'handler': 134688580,
         'index': 874,
         'next_cursor': 151191230,
         'opcode': 20,
         'script': 151191088}}

BLOCKS=[('ANIM_SHADOWBONE', 151123008, 4, 9, 'prefix'),
 ('ANIM_GIGAIMPACT', 151057536, 8, 32, 'prefix'),
 ('ANIM_CATASTROPIKA', 151191088, 22, 126, 'full'),
 ('CATASTROPIKA_NIGHT', 151191214, 2, 7, 'full'),
 ('CATASTROPIKA_DAY', 151191221, 2, 7, 'full'),
 ('CATASTROPIKA_AFTERNOON', 151191228, 1, 2, 'full'),
 ('FINISH_CATASTROPIKA', 151191230, 1, 1, 'prefix')]

REGISTERED_POINTER_FIELDS={151191097: ('AnimTask_AllBanksInvisibleExceptAttackerAndTarget', 151804045),
 151191192: ('AnimTask_GetTimeOfDay', 151799085),
 151191202: ('CATASTROPIKA_DAY', 151191221),
 151191210: ('CATASTROPIKA_AFTERNOON', 151191228),
 151191217: ('FINISH_CATASTROPIKA', 151191230),
 151191224: ('FINISH_CATASTROPIKA', 151191230)}

DATA_WINDOWS=[{'address': 151123008, 'sha256': '8ebfff2ad0c2ee441f29e47b3488bee68c78dc48cbae4deffed35862c4a1db9d', 'size': 9},
 {'address': 151057536, 'sha256': 'bdc391ce51a54306571d908e11b6fed6d01a56d2a42f0b82bdda6b25b84b38bf', 'size': 32},
 {'address': 151191088, 'sha256': 'a606ee3b43c5a429c7e0ed36baaf1f1617e25adace753cc4b8edbfc935c3a613', 'size': 126},
 {'address': 151191214, 'sha256': '6699f7c7721c5eafdcbf71cb412428cb48a086f76756db262cb9f6379113b983', 'size': 7},
 {'address': 151191221, 'sha256': 'c85534f458cabf617b33ec662e23544b7c6efc33f91f6d9f42d5511c7114c021', 'size': 7},
 {'address': 151191228, 'sha256': 'a19bd0444027c6ac5b1c2a37b2bf910f2b0d07a8807b927c9198bb04366a2767', 'size': 2},
 {'address': 151191230, 'sha256': '7cb7c4547cf2653590d7a9ace60cc623d25148adfbc88a89aeb0ef88da7839ba', 'size': 1},
 {'address': 151036100, 'sha256': 'd37be0903387bfbfeafbc20bdaff9526169d0d602533eb32ded318a0657d844a', 'size': 12},
 {'address': 152613208, 'sha256': '4188ccccf0c25a7b7202a62dd095c6a84e470552711d05f9a3af57299e1a348f', 'size': 4015},
 {'address': 151036148, 'sha256': '222f261c1f0a899767b06caa597d2ea02ca9dab22467d979fe8b4406410d0cb5', 'size': 12},
 {'address': 152557028, 'sha256': '7003087ccf3155a3f3b871e8ff38fb2e363930961be4eab38ca27f843dca3eca', 'size': 3811},
 {'address': 151036448, 'sha256': 'e441ab2ee85bb4fd589271e9bcfb3aeda85f79c626a59022b60e4be2101230c6', 'size': 12},
 {'address': 152625300, 'sha256': 'a630ddc5f934a5b31963f51f39fbbd658e93792830c55b39fb9474e5e9c2516f', 'size': 9558}]

_scalar=ab._scalar
_definitions=ab._definitions
_source_lines=ab._source_lines
def _command(line, address, constants, macros):
    normalized = re.sub(r"\s*\|\s*", "|", line).replace(",", " ")
    name, *tokens = normalized.split()
    need(name in macros and macros[name].fields, f"未対応macro: {name}")
    macro = macros[name]
    need(len(tokens) <= len(macro.params), f"macro引数過剰: {name}")
    args = dict(zip(macro.params, tokens))
    if name in ("launchtask", "launchtemplate"):
        need(len(tokens) >= 3, f"launch引数不足: {name}")
        count = _scalar(tokens[2], constants)
        need(0 <= count <= 9 and len(tokens) == 3 + count, f"launch ArgsNo不一致: {name}")
    else:
        need(len(tokens) == len(macro.params), f"macro引数数不一致: {name}")
    raw = bytearray()
    fields = []
    for width, expression in macro.fields:
        parameter = expression[1:] if expression.startswith("\\") else None
        if parameter is not None:
            need(parameter in macro.params, f"macro未定義parameter: {parameter}")
            if parameter not in args:
                need(name in ("launchtask", "launchtemplate") and "arg" in parameter,
                         "必須macro field欠落")
                continue
            expression = args[parameter]
        field_address = address + len(raw)
        try:
            value = _scalar(expression, constants)
            kind = "source_equ" if expression in constants else "source_numeric_expression"
            need(field_address not in REGISTERED_POINTER_FIELDS, "登録pointerがsource定数へ置換された")
        except KeyError:
            need(width == 4 and re.fullmatch(r"[A-Za-z_]\w*", expression) is not None,
                     f"未解決非pointer式: {expression}")
            binding = REGISTERED_POINTER_FIELDS.get(field_address)
            need(binding is not None and binding[0] == expression,
                     f"未結合source symbol: {expression}")
            value = binding[1]
            kind = "actual_registered_pointer_field"
        need(-(1 << (width * 8 - 1)) <= value < 1 << (width * 8), "field値が幅外")
        encoded = (value & ((1 << (width * 8)) - 1)).to_bytes(width, "little")
        raw.extend(encoded)
        fields.append({"address": field_address, "size": width, "source_expression": expression,
                       "source_macro_field": parameter or expression, "value": value,
                       "derivation": kind, "sha256": hashlib.sha256(encoded).hexdigest()})
    return bytes(raw), {"address": address, **identity(raw), "source": line,
                        "macro": name, "fields": fields}

CLAIMS=dict(proof_scope='conditional_registered_background_minimum_payload',conditional_api_entry=True,complete_selected_source_serializer=True,actual_command_task_and_bg_reader=True,asset_source_pixels_independently_serialized=True,source_asset_full_decoded_match=True,whole_candidate_identity_checked_by_parent_required=True,actual_runtime_execution_observed=False,full_animation_prefix_executed=False,natural_battle_reachability_claimed=False,graphics_rendering_success_claimed=False,opaque_callee_effects_proven=False,universal_heap_or_irq_lifetime_proven=False,whole_asset_classified=False,padding_classified=False,indirect_reference_completeness_claimed=False,donor_eligible=False,donor_leased=False)
CONTRACT=dict(entry_ja='実animation table cell386/678/874とsource全field serializerから得たBG command処理時を条件付きAPI入口とする。公開move indexや一律offsetを現在値に代用しない。前段animation全実行、自然move選択、時刻の生成は未証明。',producer_ja='全16slot inactive、未使用callback/dataを非zeroに汚染。実CreateTask/InsertTask/FindFirstActiveTask/memsetがcallback/priority/state0を作り、実command byte readerがBG IDを書き込む。次pause/wait/gotoを実dispatcherで処理してstack復帰し、RunTasks3回がstate0→1→2を作る。',conditions_ja='gBattleAnimTarget=1、有効script context。GigaImpactだけGetBattlerSide(1)=1の正常ABI復帰。BeginHardwarePaletteFadeがactiveを生成し、次の選択scheduler invocationまでに通常fade更新が完了してinactiveとなることを明示出力条件とする。隣接frameで完了するとは主張しない。先行tilemap LZ call正常復帰と有効VRAMを条件に、実image pointer→SWI12入力へ進む。',memory_ja='各ABI/frame境界のfuture-read-before-write RAMと最終useまで同task epochだけを保存し、他RAMはreplayでUnknownへ消す。palette完了出力と事前保存fieldを分離。全callee/heap/IRQ効果は成功証明しない。',lz_ja='公開固定PNGを独立4bpp/8x8/flip除去serializerで全tile列へ変換し、厳密LZ10 decoderの全展開結果と完全一致する。終端paddingを含めない。BIOS SWI12の標準LZ10入力型だけを証明し、画面描画/native実行は未証明。',geometry_ja='4hit各4byteだけ。LZ全streamを証拠保護するが全assetや隣接header/paddingを分類しない。')
PROFILE=dict(target=1,task_id=0,empty_task_registry=True,target_side=1,initial_frames=0,script_active=1,normal_abi_returns=True,fade_completes_before_second_selected_task_invocation=True,valid_vram_destination=True)

def serialize_animation_sources(sources):
 constants,macros=_definitions(sources['cfru-anim_defines.s'].decode());source=sources['cfru-attack-anim-table.s'].decode();chunks={r['cell']:r['script'].to_bytes(4,'little')for r in ROOTS.values()};rows=[];pointer_fields=set()
 for label,a,count,n,mode in BLOCKS:
  lines,inline=_source_lines(source,label);need(not inline and len(lines)>=count,'source prefix extent')
  if mode=='full':need(len(lines)==count,'source block complete extent')
  b=bytearray();commands=[]
  for line in lines[:count]:
   part,row=_command(line,a+len(b),constants,macros);b.extend(part);commands.append(row)
   pointer_fields.update(f['address']for f in row['fields']if f['derivation']=='actual_registered_pointer_field')
  need(len(b)==n,'independent macro field extent');chunks[a]=bytes(b);rows.append(dict(label=label,address=a,size=n,command_count=count,commands=commands))
 need(pointer_fields==set(REGISTERED_POINTER_FIELDS),'complete source pointer binding set')
 by={r['label']:r['address']for r in rows}
 for a,(name,v)in REGISTERED_POINTER_FIELDS.items():
  if name in by:need(v==by[name],'source in-script jump label location')
 table=sources['cfru-anim_background_table.s'].decode().split('gAnimationBackgrounds:',1)[1]
 entries=[[x.strip()for x in line.split('@')[0].strip()[6:].split(',')]for line in table.splitlines()if line.strip().startswith('.word ')]
 need(len(entries)==77 and all(len(x)==3 for x in entries),'source-only77 descriptor serializer')
 expected={29:['BG_NIGHTMARE_IMG','BG_NIGHTMARE_PAL','BG_NIGHTMARE_RAW'],33:['BG_GIGA_IMPACT_ON_OPPONENT_IMG','BG_GIGA_IMPACT_ON_OPPONENT_PAL','BG_GIGA_IMPACT_ON_OPPONENT_RAW'],58:['BG_BLUE_SKY_DAY_IMG','BG_BLUE_SKY_NIGHT_PAL','BG_BLUE_SKY_DAY_RAW']}
 defs=dict(re.findall(r'\.equ\s+(\w+),\s*(\w+)',sources['cfru-anim_backgrounds_graphics_defines.s'].decode()))
 for name,asset in ASSETS.items():
  need(entries[asset['bg_id']]==expected[asset['bg_id']],'selected source BG descriptor fields')
  need(defs[entries[asset['bg_id']][0]]=={'nightmare':'NightmareTiles','giga':'Giga_Impact_OpponentTiles','sky':'Sky_DayTiles'}[name],'public asset symbol definition')
  chunks[asset['descriptor_address']]=struct.pack('<III',*asset['descriptor_values'])
 return chunks,rows

def sources_bind(review,sources):
 need(type(sources)is dict and set(sources)==set(SOURCE_IDS)and exact(review['source_bindings'],SOURCE_IDS),'closed source bindings')
 for name,row in SOURCE_IDS.items():
  b=sources[name];need(type(b)is bytes and identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'fixed whole source '+name)
 src=sources['pret-battle_anim.c'].decode()
 for token in ['sScriptCmdTable[sBattleAnimScriptPtr[0]]();','taskId = CreateTask(Task_FadeToBg, 5);','gTasks[taskId].tBackgroundId = backgroundId;','gTasks[taskId].tState++;','LoadMoveBg(bgId);','LZDecompressVram(gBattleAnimBackgroundTable[bgId].image, (void *)(BG_CHAR_ADDR(2)));']:
  need(token in src,'independent consumer source meaning '+token)
 for token in ['gTasks[i].func = func;','memset(gTasks[i].data, 0, sizeof(gTasks[i].data));']:
  need(token in sources['pret-task.c'].decode(),'task producer source '+token)
 return True

def fixed_windows():
 parts={i.address:encoded(i)for i in INS.values()}
 for a,v in WORDS.items():need(a not in parts,'literal/code nonoverlap');parts[a]=v.to_bytes(4,'little')
 parts[0x81c7a8c]=struct.pack('<HH',0xdf12,0x4770)
 for r in ROOTS.values():parts[r['cell']]=r['script'].to_bytes(4,'little')
 rows=[];start=None;end=None;data=b''
 for a,b in sorted(parts.items()):
  need(end is None or a>=end,'fixed-byte nonoverlap')
  if end!=a:
   if start is not None:rows.append(dict(address=start,**identity(data)))
   start=a;data=b''
  data+=b;end=a+len(b)
 if start is not None:rows.append(dict(address=start,**identity(data)))
 rows+=copy.deepcopy(DATA_WINDOWS);rows.sort(key=lambda r:(r['address'],r['size']))
 for l,r in zip(rows,rows[1:]):need(l['address']+l['size']<=r['address'],'protected window nonoverlap')
 return rows
FIXED_WINDOWS=fixed_windows()

def bind_semantics(raw,sources):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'independent Thumb encoder '+hex(i.address))
 for a,v in WORDS.items():need(d.u32(raw,a)==v,'whole actual literal '+hex(a))
 need(chunk(raw,0x81c7a8c,4)==struct.pack('<HH',0xdf12,0x4770),'BIOS SWI12 and BX LR')
 chunks,rows=serialize_animation_sources(sources)
 for a,b in chunks.items():need(chunk(raw,a,len(b))==b,'independent complete source serializer '+hex(a))
 assets=[]
 for name,a in ASSETS.items():
  source_bytes=encode_tiles(sources[a['source_png']],sources['gritflags.txt']);need(identity(source_bytes)==a['decoded'],'whole source-derived tile extent')
  enc,dec=d.decode_lz_at(raw,a['address'],16384)
  need(identity(enc)=={k:a[k]for k in('size','sha256')}and dec==source_bytes,'strict whole LZ source match and exact consumed endpoint')
  need(all(a['address']+4<=h and h+4<=a['address']+len(enc)for h in a['hits']),'all selected hits wholly in compressed payload')
  assets.append(dict(name=name,source_png=a['source_png'],asset={k:a[k]for k in('address','size','sha256')},decoded=a['decoded'],source_tile_count=len(source_bytes)//32,whole_decoded_equal=True,padding_excluded=True))
 return dict(blocks=rows,assets=assets,full_source_serialized_bytes=sum(n for _,_,_,n,_ in BLOCKS),public_move_index_translation_used=False)

class Machine(ab.Machine):
 def __init__(self,*args,**kw):super().__init__(*args,**kw);self.observed_reads=[];self.observed_writes=[]
 def read(self,a,n):
  v=super().read(a,n)
  if self.pc in(0x8072f4e,0x8072f92,0x8072f94,0x8076d28,0x8073054,0x80730dc,0x80730e6):self.observed_reads.append((self.pc,a,n,v))
  return v
 def write(self,a,n,v):
  super().write(a,n,v)
  if self.pc in(0x8076bce,0x8072f6a,0x8072fde,0x8073024,0x807303e):self.observed_writes.append((self.pc,a,n,v))

def preservation_contract(fields,writes=(),events=None):
 need(type(fields)is list and all(type(x)is list and len(x)==2 and type(x[0])is int and type(x[1])is int and x[1]>0 for x in fields),'finite live fields')
 events={}if events is None else events
 need(type(events)is dict and set(events)<={'task_epoch_changed'}and all(type(v)is bool for v in events.values()),'closed resource epoch events')
 need(not(events.get('task_epoch_changed',False)and any(a<TASKS+640 and TASKS<a+n for a,n in fields)),'same live task epoch')
 for a,n,v in writes:
  need(type(a)is int and type(n)is int and n in(1,2,4)and type(v)is int and 0<=v<1<<(8*n)and 0<=a<a+n<=1<<32,'finite concrete write')
  need(not any(a<b+k and b<a+n for b,k in fields),'future-live RAM cannot be changed')
 return True

def _compose(raw,case,projections=None,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 need(case in ROOTS,'closed selected background');need(profile is None or exact(profile,PROFILE),'fixed finite input profile');need(contract is None or exact(contract,CONTRACT),'fixed conditional input contract')
 root,asset=ROOTS[case],ASSETS[case];trace=[];visited=[];boundaries=[];reads=[];writes=[];mem=rt.task_fixture([])
 for slot in range(16):
  for off in range(40):
   if off!=4:mem[TASKS+40*slot+off]=0xa5
 for a,n,v in((CURSOR,4,root['command']),(FRAMES,1,0),(SCRIPT_ACTIVE,1,1),(TARGET,1,1)):rt.setmem(mem,a,n,v)
 def boundary(m,site,target,outputs=(),result=rt.U,frame=False):
  idx=len(boundaries);trace.append(('boundary',idx,0));fields=[]if projections is None else projections[idx]
  if projections is not None:
   effects=(opaque_writes or{}).get(site,());events=(epoch_events or{}).get(site,{})
   preservation_contract(fields,effects,events)
   for a,n,v in effects:
    for j in range(n):m.mem[a+j]=(v>>(8*j))&255
   kept={a+j for a,n in fields for j in range(n)};m.mem={a:v for a,v in m.mem.items()if a in kept}
  for a,n,v in outputs:m.write(a,n,v)
  boundaries.append(dict(site=site,target=target,required_fields=fields,conditional_outputs=[dict(address=a,size=n,value=v)for a,n,v in outputs],return_value=result if rt.concrete(result)else'unspecified',normal_abi_return_required=not frame,frame_interval_completion_condition=frame,task_epoch_required=any(a<TASKS+640 and TASKS<a+n for a,n in fields),effects_discharged=False))
 def go(entry,memory):
  m=Machine(raw,entry,{},memory,instructions=INS,trace=trace)
  while m.pc!=0xfffffff0:
   if m.pc==0x81c7a8c:
    need(m.reg[:2]==[asset['address'],0x6008000],'actual image pointer and VRAM destination reach SWI12');break
   if m.pc==0x80730e0:
    need(m.reg[:2]==[asset['descriptor_values'][2],0x600d000],'actual earlier tilemap pointer and VRAM destination')
    # This earlier decompressor is an explicit normal-return condition, not an asserted effect.
    m.step();site=0x80730e0;target=0x800e574;result=rt.U;outputs=[]
   elif m.pc in INS:
    visited.append(m.pc);m.step();continue
   else:
    site=(m.reg[14]&~1)-4;target=m.pc;outputs=[];result=rt.U
    need((site,target)in((0x8072faa,0x8074968),(0x807301c,0x8070a08)),'closed external ABI boundary')
    if target==0x8074968:need(case=='giga'and m.reg[0]==1,'actual target-side input');result=1
    else:need(m.reg[:4]==[232,0,0,16]and m.read(m.reg[13],4)==0,'actual fade-out inputs');outputs=[(PALETTE+7,1,128)]
   boundary(m,site,target,outputs,result)
   for r in(0,1,2,3,12):m.reg[r]=rt.U
   m.reg[0]=result;m.flags=(rt.U,)*4;m.flag_pc=None;m.pc=m.reg[14]&~1
  reads.extend(m.observed_reads);writes.extend(m.observed_writes)
  if m.pc==0xfffffff0:need(m.reg[13]==0x3007000,'balanced API/frame stack')
  return m
 m=go(0x8071fcc,mem)
 need(m.pc==0xfffffff0 and m.read(TASKS,4)==0x8072ff5 and m.read(TASKS+4,1)==1 and m.read(TASKS+7,1)==5 and m.read(TASKS+8,2)==root['bg_id']and m.read(TASKS+28,2)==0,'real task registration, source byte BG selector, and zero-fill producer')
 need(m.read(CURSOR,4)==root['next_cursor']and m.read(FRAMES,1)==root['frames']and m.read(FADE,1)==1,'actual next command and balanced script dispatcher')
 for frame in range(3):
  outputs=[(PALETTE+7,1,0)]if frame==1 else[]
  boundary(m,0,0,outputs,frame=True);m=go(0x8076d10,m.mem)
  if frame<2:need(m.pc==0xfffffff0 and m.read(TASKS+28,2)==frame+1,'actual finite task state writer')
 need(m.pc==0x81c7a8c and root['handler']in visited and 0x8076bce in visited and 0x8076d28 in visited and 0x8073054 in visited and 0x80730e6 in visited,'registered dispatcher→task producer→scheduler→BG selector→image consumer')
 need((0x8076bce,TASKS,4,0x8072ff5)in writes and(0x8073054,TASKS+8,2,root['bg_id'])in reads and(0x80730e6,asset['descriptor_address'],4,asset['address'])in reads,'actual complete producer/consumer fields')
 live=engine.future_live(trace,len(boundaries))
 if projections is not None:need(exact(live,projections),'stable future-live projection')
 return dict(trace=trace,visited=visited,boundaries=boundaries,projections=live,reads=reads,writes=writes,endpoint=m.pc)

def compose_selected(raw,opaque_writes=None,epoch_events=None,profile=None,contract=None):
 known={0,0x8072faa,0x807301c,0x80730e0}
 for value in(opaque_writes,epoch_events):need(value is None or type(value)is dict and set(value)<=known,'closed boundary effect sites')
 cases=[];observed=set()
 for case in ROOTS:
  a=_compose(raw,case,profile=profile,contract=contract);b=_compose(raw,case,a['projections'],opaque_writes,epoch_events,profile,contract)
  need(exact(a['visited'],b['visited'])and exact(a['reads'],b['reads'])and exact(a['writes'],b['writes']),'same finite route after nonlive RAM erasure')
  observed.update(x['site']for x in b['boundaries'])
  cases.append(dict(case=case,endpoint=b['endpoint'],instruction_steps=len(b['visited']),scheduler_invocations=3,real_task_registration=True,nonlive_ram_erased_at_every_boundary=True,callback_or_bg_host_seeded=False,reads=b['reads'],writes=b['writes'],conditional_call_groups=b['boundaries'],trace_identity=identity(json.dumps(b['trace'],separators=(',',':')).encode())))
 for value in(opaque_writes,epoch_events):need(set(value or{})<=observed,'nonexecuted effect site rejected')
 return dict(status='PASS_THREE_REGISTERED_BACKGROUND_CONSUMERS',cases=cases,actual_runtime_execution_observed=False)

def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'four minimum hit scope');name=next(k for k,a in ASSETS.items()if hit in a['hits'])
 return dict(root_verified=True,root=copy.deepcopy(ROOTS[name]),asset=copy.deepcopy(ASSETS[name]),classified_window=dict(address=hit,size=4),input_contract=copy.deepcopy(CONTRACT),**copy.deepcopy(CLAIMS))
def witness_geometry(e):
 h=e.get('classified_window',{}).get('address');need(type(h)is int and h in HITS and exact(e,evidence_template(h)),'closed exact minimum payload witness');return h,4

def protected_windows(review):need(exact(review['windows'],FIXED_WINDOWS),'immutable finite protected windows');return copy.deepcopy(FIXED_WINDOWS)
def make_review(raw,hits):
 selected=[h for h in hits if h['address']in HITS];need(exact(selected,EXPECTED_HITS),'all original four unknown fields')
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),hits=copy.deepcopy(selected),roots=copy.deepcopy(ROOTS),assets=copy.deepcopy(ASSETS),windows=copy.deepcopy(FIXED_WINDOWS),claims=copy.deepcopy(CLAIMS),input_contract=copy.deepcopy(CONTRACT),finite_profile=copy.deepcopy(PROFILE))
prepare_review=make_review

def _regions(raw,inherited,review,sources):
 need(type(review)is dict and set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','hits','roots','assets','windows','claims','input_contract','finite_profile'},'closed exact review schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'strict schema version')
 for k,v in(('required_candidate',CANDIDATE),('diagnostic_input',DIAGNOSTIC),('roots',ROOTS),('assets',ASSETS),('claims',CLAIMS),('input_contract',CONTRACT),('finite_profile',PROFILE)):need(exact(review[k],v),'immutable review field '+k)
 need(exact(inherited['candidate'],CANDIDATE),'current and diagnostic identity separated')
 selected=[h for h in inherited['hits']if h['address']in HITS]
 need(exact(selected,review['hits'])and exact(selected,EXPECTED_HITS),'all original four unowned unknown fields')
 for h in selected:need(h['classification']=='UNCLASSIFIED'and h['accepted']is False and h['owner_candidates']==[]and type(h['size'])is int and h['size']==4,'original inventory type');d.signed(raw,h)
 d.signed(raw,protected_windows(review));sources_bind(review,sources);serialization=bind_semantics(raw,sources);composition=compose_selected(raw)
 regions=[]
 for h in HITS:
  e=evidence_template(h);a,n=witness_geometry(e);regions.append(d.TypedRegion(a,a+n,KIND,e))
 return regions,dict(status='PASS_REGISTERED_BACKGROUND_MINIMUM_PAYLOADS',count=4,hits=list(HITS),serialization=serialization,composition=composition,protected_windows=len(FIXED_WINDOWS),protected_bytes=sum(w['size']for w in FIXED_WINDOWS),**copy.deepcopy(CLAIMS))
def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current0641 identity gate');return _regions(raw,inherited,review,sources)
