"""effect184/231の実登録・独立serializerからgoto/FF09境界各4byteを分類する。"""
from __future__ import annotations
import copy, hashlib, json, re
import pr16_dex_hof_battle_script_roots as rooted
import pr16_dex_hof_donor as d
import pr16_dex_hof_callback_party as native
import pr16_dex_hof_runtime_party as rt
prior = rooted.prior
need, identity, chunk = d.need, d.identity, d.chunk
exact = rooted.exact
CANDIDATE, DIAGNOSTIC = rooted.CANDIDATE, rooted.DIAGNOSTIC
KIND = 'rooted_battle_tail_minimum_cross_field'
TYPE_CATEGORY = 'data'
HITS = (0x09005D94, 0x09007271)
ROOTS = {184: 0x09005D7F, 231: 0x090071BA}
CURSOR = prior.CURSOR
SOURCE_IDS = copy.deepcopy(rooted.SOURCE_IDS)
SOURCE_ROLES = copy.deepcopy(rooted.SOURCE_ROLES)
COMMON_ROOT_SHA256 = rooted.COMMON_ROOT_SHA256
CLAIMS = dict(rooted.CLAIMS, callasm_success_proven=False, goto_fallthrough_claimed=False,
              all_prefix_execution_claimed=False, owner_transfer_proven=False)
# 公開serializerの幅・field role。callasm等は型境界だけで成功契約を置かない。
GRAMMAR = dict(rooted.GRAMMAR, **{
 'jumpifnotmove': (42,12,((1,1,'predicate'),(2,4,'read_address'),(6,2,'move_id'),(8,4,'script_pointer'))),
 'accuracycheck': (1,7,((1,4,'script_pointer'),(5,2,'parameter'))),
 'attackstring': (2,1,()), 'ppreduce': (3,1,()),
 'attackanimation': (9,1,()), 'waitanimation': (10,1,()),
 'setcounter': (0xFF0E,5,((2,1,'bank'),(3,1,'counter'),(4,1,'amount'))),
 'setword': (250,9,((1,4,'write_address'),(5,4,'data_pointer'))),
 'printstring': (16,3,((1,2,'string_id'),)),
 'waitmessage': (18,3,((1,2,'delay'),)),
 'callasm': (248,5,((1,4,'function_pointer'),)),
 'goto': (40,5,((1,4,'script_pointer'),)),
})
ROOT231_PREFIX = rooted.PROGRAM[:6]
EMBARGO = (
 (0x09007236,'jumpifbehindsubstitute',(0,0x1000000,0x09008E11)),
 (0x09007240,'jumpifcounter',(0,5,1,0,0x09008E11)),
 (0x0900724A,'accuracycheck',(0x081BA91A,0)),
 (0x09007251,'attackstring',()), (0x09007252,'ppreduce',()),
 (0x09007253,'attackanimation',()), (0x09007254,'waitanimation',()),
 (0x09007255,'setcounter',(0,5,5)),
 (0x0900725A,'setword',(0x0203DF98,0x09007C1C)),
 (0x09007263,'printstring',(0x184,)), (0x09007266,'waitmessage',(0x40,)),
 (0x09007269,'callasm',(0x90cbfb5,)),
 (0x0900726E,'goto',(0x081BA90A,)),
)
POWDER = ((0x09007273,'jumpifcounter',(0,14,1,0,0x09008E11)),)
RECYCLE = (
 (0x09005D7F,'attackcanceler',()),
 (0x09005D80,'jumpifnotmove',(1,0x02023CAA,0x2C8,0x09005D96)),
 (0x09005D8C,'callasm',(0x90c9a79,)),
 (0x09005D91,'goto',(0x081BA8E3,)),
 (0x09005D96,'jumpifcounter',(1,13,1,0,0x09008E11)),
)
PROGRAM = ROOT231_PREFIX + EMBARGO + POWDER + RECYCLE
# 技名の上流番号を流用せず、現tableのeffect値で独立に束縛する。
MOVE_EFFECTS = {0x2B4:231,0x2E0:231,0x2D3:231,0x2D8:231,0x426:231,0x2C8:184,278:184}
# 実NOTEQUALS/EQUALS/gotoの選択pathだけ。未選択predicateへ広げない。
CONTROL_SPECS = {134356560: ('literal', 3, 134356588),
 134356562: ('mem', True, 'word', 2, 3, 0),
 134356564: ('mem', True, 'byte', 1, 2, 1),
 134356566: ('mem', True, 'byte', 0, 2, 2),
 134356568: ('shift', 'lsl', 0, 0, 8),
 134356570: ('add', 1, 1, 0),
 134356572: ('mem', True, 'byte', 0, 2, 3),
 134356574: ('shift', 'lsl', 0, 0, 16),
 134356576: ('add', 1, 1, 0),
 134356578: ('mem', True, 'byte', 0, 2, 4),
 134356580: ('shift', 'lsl', 0, 0, 24),
 134356582: ('add', 1, 1, 0),
 134356584: ('mem', False, 'word', 1, 3, 0),
 134356586: ('bx', 14),
 134356752: ('push', 112, True),
 134356754: ('literal', 3, 134356828),
 134356756: ('mem', True, 'word', 1, 3, 0),
 134356758: ('mem', True, 'byte', 6, 1, 1),
 134356760: ('mem', True, 'byte', 2, 1, 2),
 134356762: ('mem', True, 'byte', 0, 1, 3),
 134356764: ('shift', 'lsl', 0, 0, 8),
 134356766: ('add', 2, 2, 0),
 134356768: ('mem', True, 'byte', 0, 1, 4),
 134356770: ('shift', 'lsl', 0, 0, 16),
 134356772: ('add', 2, 2, 0),
 134356774: ('mem', True, 'byte', 0, 1, 5),
 134356776: ('shift', 'lsl', 0, 0, 24),
 134356778: ('add', 5, 2, 0),
 134356780: ('mem', True, 'byte', 4, 1, 6),
 134356782: ('mem', True, 'byte', 0, 1, 7),
 134356784: ('shift', 'lsl', 0, 0, 8),
 134356786: ('alu', 'orr', 4, 0),
 134356788: ('mem', True, 'byte', 2, 1, 8),
 134356790: ('mem', True, 'byte', 0, 1, 9),
 134356792: ('shift', 'lsl', 0, 0, 8),
 134356794: ('add', 2, 2, 0),
 134356796: ('mem', True, 'byte', 0, 1, 10),
 134356798: ('shift', 'lsl', 0, 0, 16),
 134356800: ('add', 2, 2, 0),
 134356802: ('mem', True, 'byte', 0, 1, 11),
 134356804: ('shift', 'lsl', 0, 0, 24),
 134356806: ('add', 2, 2, 0),
 134356808: ('imm', 'add', 1, 12),
 134356810: ('mem', False, 'word', 1, 3, 0),
 134356812: ('imm', 'cmp', 6, 5),
 134356814: ('branch', 8, 134356912),
 134356816: ('shift', 'lsl', 0, 6, 2),
 134356818: ('literal', 1, 134356832),
 134356820: ('add', 0, 0, 1),
 134356822: ('mem', True, 'word', 0, 0, 0),
 134356824: ('movhi', 15, 0),
 134356860: ('mem', True, 'half', 0, 5, 0),
 134356862: ('compare', 0, 4),
 134356864: ('branch', 1, 134356912),
 134356866: ('jump', 134356910),
 134356868: ('mem', True, 'half', 0, 5, 0),
 134356870: ('compare', 0, 4),
 134356872: ('branch', 0, 134356912),
 134356874: ('jump', 134356910),
 134356910: ('mem', False, 'word', 2, 3, 0),
 134356912: ('pop', 112, False),
 134356914: ('pop', 1, False),
 134356916: ('bx', 0)}
CONTROL_INS = {a:native.block(a,[s])[0] for a,s in CONTROL_SPECS.items()}
BLOCKS = {name:rooted.BLOCKS[name] for name in ('counter_pointer_read','bank_resolver','bank_return','target_bank')}
BLOCKS['attacker_bank'] = native.block(0x090D3D84,[
 ('literal',3,0x090D3DA8), ('mem',True,'byte',0,3,0), ('jump',0x090D3D3C)])
POINTER_INS = {i.address:i for block in BLOCKS.values() for i in block}
INS = {**CONTROL_INS, **POINTER_INS}
WORDS = {
 0x08021E6C:CURSOR, 0x08021F5C:CURSOR, 0x08021F60:0x08021F64,
 0x08021F64:0x08021F7C, 0x08021F68:0x08021F84,
 0x0911B0E0:CURSOR, 0x090D3D8C:0x09161410,
 0x09161410:0x090D3D7E, 0x09161414:0x090D3D84,
 0x090D3DA4:0x02023CCC, 0x090D3DA8:0x02023CCB,
 prior.EFFECTS+184*4:ROOTS[184], prior.EFFECTS+231*4:ROOTS[231],
 prior.PRIMARY:0x090BD385,
}
encoded = rooted.encoded

class Machine(rooted.Machine):
 """実bank table slotとattacker/target RAM読取りを区別して記録する。"""
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs); self.reads=[]
 def read(self,a,n):
  self.reads.append((a,n)); return super().read(a,n)

def source_proof(review,sources):
 rooted.source_proof(review,sources)
 macro=re.sub(r'@[^\n]*','',sources[SOURCE_ROLES['battle_script_macros.s']].decode())
 defs=re.sub(r'@[^\n]*','',sources[SOURCE_ROLES['asm_defines.s']].decode())
 for text,constants in [(macro,{'BANK_ATTACKER':1,'BS_MOVE_END':0x081BA90A,'BS_MOVE_MISSED':0x081BA91A,'DELAY_1SECOND':0x40}),
                        (defs,{'INCINERATE_COUNTERS':13,'POWDER_TIMERS':14,'BATTLE_STRING_LOADER':0x0203DF98})]:
  for name,value in constants.items():
   m=re.search(r'^\.equ\s+'+name+r',\s*(\w+)',text,re.M)
   need(m is not None and int(m[1],0)==value,'公開sourceの独立定数 '+name)
 shapes={
 'jumpifnotmove':[(1,'0x2a'),(1,'NOTEQUALS'),(4,'CURRENT_MOVE'),(2,'\\compare'),(4,'\\rom_address')],
 'accuracycheck':[(1,'0x01'),(4,'\\rom_address'),(2,'\\param1')],
 'attackstring':[(1,'0x02')], 'ppreduce':[(1,'0x03')],
 'attackanimation':[(1,'0x09')], 'waitanimation':[(1,'0x0a')],
 'setcounter':[(1,'0xFF'),(1,'0x0E'),(1,'\\bank'),(1,'\\counter_id'),(1,'\\amount')],
 'setword':[(1,'0xfa'),(4,'\\mem_address'),(4,'\\word')],
 'printstring':[(1,'0x10'),(2,'\\string')], 'waitmessage':[(1,'0x12'),(2,'\\delay')],
 'callasm':[(1,'0xf8'),(4,'\\asm_address')], 'goto':[(1,'0x28'),(4,'\\rom_address')],
 }
 for name,shape in shapes.items():
  bodies=re.findall(r'\.macro\s+'+name+r'(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S)
  need(len(bodies)==1,'公開serializerは一意'); fields=[]
  for line in bodies[0].splitlines():
   if not line.strip():continue
   m=re.fullmatch(r'\s*\.(byte|2byte|4byte|word)\s+(.+)',line)
   need(m is not None,'有限の直接serializerのみ')
   fields.extend(({'byte':1,'2byte':2,'4byte':4,'word':4}[m[1]],v.strip())for v in m[2].split(','))
  need(fields==shape and sum(z for z,_ in fields)==GRAMMAR[name][1],'独立serializerの全field幅 '+name)
 src=sources[SOURCE_ROLES['assembly/battle_scripts/general_attack_battle_scripts.s']].decode()
 compact=lambda s:[' '.join(x.split())for x in re.sub(r'@[^\n]*','',s).splitlines()if x.strip()]
 embargo=compact(src.split('EmbargoBS:',1)[1].split('PowderBS:',1)[0])
 need(embargo==['jumpifbehindsubstitute BANK_TARGET FAILED_PRE','jumpifcounter BANK_TARGET EMBARGO_TIMERS NOTEQUALS 0x0 FAILED_PRE',
 'accuracycheck BS_MOVE_MISSED 0x0','attackstring','ppreduce','attackanimation','waitanimation',
 'setcounter BANK_TARGET EMBARGO_TIMERS 5','setword BATTLE_STRING_LOADER EmbargoSetString',
 'printstring 0x184','waitmessage DELAY_1SECOND','callasm TryRemovePrimalWeatherAfterItemChange','goto BS_MOVE_END'],
 'Embargo全13命令を固定source順序で閉じる')
 recycle=compact(src.split('BS_184_Recycle:',1)[1].split('RecycleBS:',1)[0])
 need(recycle==['attackcanceler','jumpifnotmove MOVE_BELCH RecycleBS','callasm BelchFunction','goto 0x81BA8E3'],
      'Recycle登録prefix全4命令を閉じる')
 for label,line in [('PowderBS','jumpifcounter BANK_TARGET POWDER_TIMERS NOTEQUALS 0x0 FAILED_PRE'),
                    ('RecycleBS','jumpifcounter BANK_ATTACKER INCINERATE_COUNTERS NOTEQUALS 0x0 FAILED_PRE')]:
  need(compact(src.split(label+':',1)[1])[0]==line,'右側の独立label-root命令')
 effects=sources[SOURCE_ROLES['assembly/data/move_effect_table.s']].decode().split('gBattleScriptsForMoveEffects:',1)[1].split('gSetStatusMoveEffects:',1)[0]
 need(re.findall(r'^\s*\.word\s+(\S+)',effects,re.M)[184]=='BS_184_Recycle','公開effect184登録')
 bprj=sources[SOURCE_ROLES['BPRJ.ld']].decode()
 need(re.search(r'^gBankAttacker\s*=\s*0x2023CCB;',bprj,re.M),'日本語attacker symbolの実アドレス')
 return True

def bind_program(raw):
 rows=[]
 for a,name,values in PROGRAM:
  op,size,fields=GRAMMAR[name]; b=chunk(raw,a,size)
  prefix=bytes([255,op&255] if op>255 else [op])
  need(b[:len(prefix)]==prefix,'source命令境界の実opcode')
  need(tuple(int.from_bytes(b[o:o+n],'little')for o,n,_ in fields)==values,'全実operandを独立値へ束縛')
  rows.append(dict(address=a,name=name,opcode=op,size=size,fields=[dict(address=a+o,size=n,role=role,value=v)for(o,n,role),v in zip(fields,values)]))
 for sequence in (ROOT231_PREFIX,EMBARGO+POWDER,RECYCLE):
  for left,right in zip(sequence,sequence[1:]):
   need(left[0]+GRAMMAR[left[1]][1]==right[0],'連続serializer境界。runtime fallthroughではない')
 need(len(EMBARGO)==13 and sum(GRAMMAR[name][1]for _,name,_ in EMBARGO)==61,'Embargo全61byte')
 need(sum(GRAMMAR[name][1]for _,name,_ in RECYCLE[:4])==23,'Recycle prefix全23byte')
 for move,effect in MOVE_EFFECTS.items():
  need(chunk(raw,0x090421F4+12*move,1)[0]==effect,'現Move表のeffect producer')
 return rows

def semantic_bindings(raw):
 for i in INS.values():need(chunk(raw,i.address,i.size)==encoded(i),'独立JP命令意味 '+i.kind)
 for a,value in WORDS.items():need(d.u32(raw,a)==value,'真のslot/literalの独立値')
 return True

def control_proof(raw):
 semantic_bindings(raw); bind_program(raw); result=[]
 for a,name,values in PROGRAM:
  if name not in ('jumpifmove','jumpifnotmove','goto'):continue
  op=GRAMMAR[name][0]
  for edge in (('taken',)if name=='goto'else('taken','next')):
   value=None;target=values[-1] if edge=='taken'else a+12
   writes=[]
   if name!='goto':
    predicate,_,compare,_=values
    # Recycleの非等値例も同effect184の現Move表から選ぶ。
    unequal=278 if name=='jumpifnotmove'else compare^1
    value=(compare if edge=='taken'else unequal) if predicate==0 else (unequal if edge=='taken'else compare)
    need((value==compare)==(edge=='taken') if predicate==0 else (value!=compare)==(edge=='taken'),'述語と独立入力の対応')
    writes=[dict(address=CURSOR,size=4,value=a+12)]
   if edge=='taken':writes.append(dict(address=CURSOR,size=4,value=target))
   cursor,actual,trace,reads=prior.thumb_handler(raw,prior.HANDLERS[op],a,value)
   need(cursor==target and actual==writes,'実JP handlerのtaken/nextと全write')
   need(all(r['address']in CONTROL_INS for r in trace),'選択native pathを独立命令集合に限定')
   result.append(dict(command=a,opcode=op,edge=edge,entry=prior.HANDLERS[op],next_cursor=target))
 need(any(x['command']==0x090071C7 and x['edge']=='taken'and x['next_cursor']==0x09007236 for x in result),'Embargoの第二selector根')
 need(any(x['command']==0x090071D3 and x['edge']=='taken'and x['next_cursor']==0x09007273 for x in result),'Powderの第三selector根')
 need(any(x['command']==0x09005D80 and x['edge']=='taken'and x['next_cursor']==0x09005D96 for x in result),'RecycleのNOTEQUALS根')
 return result

def pointer_read_proof(raw):
 semantic_bindings(raw); proof=[]
 for a,_,values in POWDER+(RECYCLE[-1],):
  bank=values[0]
  for actual_bank in range(4):
   mem={}; rt.setmem(mem,CURSOR,4,a+1)
   rt.setmem(mem,0x02023CCC,1,actual_bank if bank==0 else actual_bank^3)
   rt.setmem(mem,0x02023CCB,1,actual_bank if bank==1 else actual_bank^3)
   m=Machine(raw,0x0911AF68,memory=mem,instructions=POINTER_INS)
   while m.pc!=0x0911AF94:m.step()
   need(m.reg[4]==values[-1] and m.reg[0]==actual_bank,'完全pointer再構成と実bank値')
   need((0x09161410+4*bank,4)in m.reads and (0x02023CCC-bank,1)in m.reads,'実bank slotと実RAM fieldを読む')
   need((0x09161410+4*(1-bank),4)not in m.reads and (0x02023CCB+bank,1)not in m.reads,'別bankの値差替えを禁止')
   need(m.calls==[(0x0911AF74,0x090D3D2C)],'未知callee契約なし。実resolverだけを実行')
   need(rt.getmem(m.mem,CURSOR,4)==a+1,'pointer読取りでcursorを捏造しない')
   need(all(0x03006F00<=addr<addr+n<=0x03007000 for _,addr,n in m.writes),'正規stack以外は書かない')
  proof.append(dict(command=a,handler=0x0911AF68,stop=0x0911AF94,pointer=values[-1],pointer_bytes=4,
                    bank_operand=bank,resolver_slot=0x09161410+4*bank,bank_read_address=0x02023CCC-bank,
                    actual_resolver_table=True,distinct_bank_value_cases=4))
 return proof


def evidence_template(hit):
 need(type(hit)is int and hit in HITS,'新2hitだけ')
 effect=184 if hit==HITS[0]else 231; left=hit-3;right=hit+2
 e=dict(hit=hit,kind=KIND,root=ROOTS[effect],effect=effect,
        left_command=dict(address=left,size=5,opcode=40),right_command=dict(address=right,size=10,opcode=0xFF09),
        whole_pointers=[dict(address=left+1,size=4,value=0x081BA8E3 if effect==184 else 0x081BA90A),
                        dict(address=right+6,size=4,value=0x09008E11)],
        byte_roles=['left_script_pointer_byte2','left_script_pointer_byte3','right_primary_opcode','right_secondary_opcode'],
        claims=copy.deepcopy(CLAIMS))
 return e

def witness_geometry(e):
 need(isinstance(e,dict)and type(e.get('hit'))is int and e['hit']in HITS,'最小の既知hit')
 need(exact(e,evidence_template(e['hit'])),'完全field/根/role/非昇格を閉じた型witness')
 for pointer in e['whole_pointers']:
  need(not d.DONOR_LO<=d.canonical(pointer['value'])<d.DONOR_HI,'実pointer全体はdonor外')
 return e['hit'],4

def own_geometry():
 rows={(i.address,i.size)for i in INS.values()}|{(a,4)for a in WORDS}|{(0x0913194E,2)}
 rows|={(a,GRAMMAR[name][1])for a,name,_ in PROGRAM}
 rows|={(0x090421F4+12*move,1)for move in MOVE_EFFECTS}
 return sorted(rows)

def protected_windows(review):
 return prior.protected_windows({'common_root':review['common_root'],'windows':review['windows']})

def make_review(raw,inherited,common_root):
 by={h['address']:h for h in inherited['hits']}
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),
             source_bindings=copy.deepcopy(SOURCE_IDS),common_root=copy.deepcopy(common_root),
             hits=[copy.deepcopy(by[h])for h in HITS],
             windows=[dict(address=a,**identity(chunk(raw,a,n)))for a,n in own_geometry()],claims=copy.deepcopy(CLAIMS))

def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','common_root','hits','windows','claims'},'新reviewの閉schema')
 need(type(review['schema_version'])is int and review['schema_version']==1,'schemaは厳密な整数')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'正式候補と診断入力は別identity')
 need(exact(review['claims'],CLAIMS),'型を自然到達/退役/owner移管へ昇格しない')
 common=review['common_root']
 need(hashlib.sha256(json.dumps(common,sort_keys=True,separators=(',',':')).encode()).hexdigest()==COMMON_ROOT_SHA256,'既受入共通登録根の独立digest')
 source_proof(review,sources);prior.root_consumers(raw,common)
 need([(w['address'],w['size'])for w in review['windows']]==own_geometry(),'最小有限窓の閉集合')
 for w in review['windows']:
  need(set(w)=={'address','size','sha256'},'窓はdigestのみ');d.signed(raw,w)
 rows=bind_program(raw);selectors=control_proof(raw);consumers=pointer_read_proof(raw)
 old=inherited['hits'];need(len({h['address']for h in old})==len(old),'親hitは重複禁止')
 by={h['address']:h for h in old};need(exact(review['hits'],[by[h]for h in HITS]),'親の未知行全fieldを保持')
 regions=[]
 for h in review['hits']:
  need(type(h['accepted'])is bool and h['accepted']is False and h['owner_candidates']==[] and h['classification']=='UNCLASSIFIED'and type(h['size'])is int and h['size']==4,'無所有の未知4byteだけ');d.signed(raw,h)
  evidence=evidence_template(h['address']);a,n=witness_geometry(evidence);regions.append(d.TypedRegion(a,a+n,KIND,evidence))
 return regions,dict(status='PASS_TWO_SOURCE_ROOTED_BATTLE_TAIL_TYPES',count=2,hits=list(HITS),typed_bytes=8,
                     embargo_commands=13,embargo_serialized_bytes=61,recycle_prefix_serialized_bytes=23,
                     source_serialized_root=True,native_pointer_read_proofs=consumers,native_selector_models=selectors,
                     protected_windows=len(protected_windows(review)),protected_bytes=sum(w['size']for w in protected_windows(review)),**CLAIMS)

def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'正式受入前にcurrent0641全体identityを要求')
 return _regions(raw,inherited,review,sources)
