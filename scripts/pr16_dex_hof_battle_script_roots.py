"""実effect231登録と独立serializerから2箇所8byteだけをbattle命令境界へ分類。"""
from __future__ import annotations
import copy, hashlib, json, re
import pr16_dex_hof_donor as d
import pr16_dex_hof_script_battle as prior
import pr16_dex_hof_callback_party as native
import pr16_dex_hof_runtime_party as rt
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=prior.CANDIDATE
DIAGNOSTIC=native.DIAGNOSTIC
KIND='rooted_battle_script_minimum_cross_field'
TYPE_CATEGORY='data'
HITS=(0x090071FF,0x0900723E)
ROOT=0x090071BA
EFFECT=231
CURSOR=prior.CURSOR
CLAIMS={'donor_leased':False,'donor_eligible':False,'full_story_reachability_claimed':False,
 'natural_battle_entry_reachability_claimed':False,'whole_script_range_classified':False,
 'attackcanceler_success_proven':False,'indirect_reference_completeness_claimed':False}
SOURCE_ROLES = {'BPRJ.ld': 'battle-BPRJ.ld',
 'asm_defines.s': 'battle-asm_defines.s',
 'assembly/battle_scripts/general_attack_battle_scripts.s': 'battle-assembly--battle_scripts--general_attack_battle_scripts.s',
 'assembly/data/battle_script_commands_table.s': 'battle-assembly--data--battle_script_commands_table.s',
 'assembly/data/move_effect_table.s': 'battle-assembly--data--move_effect_table.s',
 'battle_script_macros.s': 'battle-battle_script_macros.s',
 'src/general_bs_commands.c': 'battle-src--general_bs_commands.c',
 'src/new_bs_commands.c': 'battle-src--new_bs_commands.c'}
SOURCE_IDS = {'battle-BPRJ.ld': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                    'git_blob_sha': 'cf5363abd8439d63c7bd12cbe83ade861b0ebb51',
                    'local': 'battle-BPRJ.ld',
                    'repository': 'kapibarasan000/CFRU-JP',
                    'sha256': 'e371c23b9c9ea914c9ca3f644983e0b4e05be07bf11054492fa37afcfd58892a',
                    'size': 68505,
                    'source': 'BPRJ.ld'},
 'battle-asm_defines.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                          'git_blob_sha': '67f802d777e348e74c0f2d6c7ae2227fdf849f6f',
                          'local': 'battle-asm_defines.s',
                          'repository': 'kapibarasan000/CFRU-JP',
                          'sha256': '1beb8b1cce26e302eb17b6907951fc4ae0a1a0ae94cffb168a12c648ca45c8a7',
                          'size': 131732,
                          'source': 'asm_defines.s'},
 'battle-assembly--battle_scripts--general_attack_battle_scripts.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                                      'git_blob_sha': 'f0a04c0f348555a82aa861ccb62b9cc046699a48',
                                                                      'local': 'battle-assembly--battle_scripts--general_attack_battle_scripts.s',
                                                                      'repository': 'kapibarasan000/CFRU-JP',
                                                                      'sha256': '8ce944c4bc85f2827eb806a3ba1f046e332429ceadd2b55bbc79f900a6a7bd11',
                                                                      'size': 178625,
                                                                      'source': 'assembly/battle_scripts/general_attack_battle_scripts.s'},
 'battle-assembly--data--battle_script_commands_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                           'git_blob_sha': '10e8cf9821e5be79798b3ab1d02ea3e44ce44f05',
                                                           'local': 'battle-assembly--data--battle_script_commands_table.s',
                                                           'repository': 'kapibarasan000/CFRU-JP',
                                                           'sha256': 'ef6615d20d0768e23828b941fcd2a4f04ba06507a7ed498ab51b8db10e71f5f6',
                                                           'size': 11083,
                                                           'source': 'assembly/data/battle_script_commands_table.s'},
 'battle-assembly--data--move_effect_table.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                                'git_blob_sha': '8a80d63f814e97b353416a73e2be7c82c453b244',
                                                'local': 'battle-assembly--data--move_effect_table.s',
                                                'repository': 'kapibarasan000/CFRU-JP',
                                                'sha256': '6200094d2df850f70121a981c89e776a8419cc71423b44ea4773f609ca39a7ee',
                                                'size': 8052,
                                                'source': 'assembly/data/move_effect_table.s'},
 'battle-battle_script_macros.s': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': 'bc62b1a589d0569980bd723d8da6272f40f12817',
                                   'local': 'battle-battle_script_macros.s',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '203f55037871e670401692a2a08ba282745a442fc84fca0615fbe1b136f8f317',
                                   'size': 28316,
                                   'source': 'battle_script_macros.s'},
 'battle-src--general_bs_commands.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                       'git_blob_sha': '476cbdd3ee2cfe3ce2ccca51b609560b1f1a4282',
                                       'local': 'battle-src--general_bs_commands.c',
                                       'repository': 'kapibarasan000/CFRU-JP',
                                       'sha256': 'ee23f75ab32b0f453128a9e5f9c7e77aba4a0de646e762a5fe821b61c1b20643',
                                       'size': 170849,
                                       'source': 'src/general_bs_commands.c'},
 'battle-src--new_bs_commands.c': {'commit': 'e24a16fe39e27ae162faf5b78596d1f3df18489d',
                                   'git_blob_sha': '78614276ea045eaa06781210d588dd6ea6995bf3',
                                   'local': 'battle-src--new_bs_commands.c',
                                   'repository': 'kapibarasan000/CFRU-JP',
                                   'sha256': '203c32caf217965e468bc2efee45809b05289c51201412250b2352e17643688b',
                                   'size': 63964,
                                   'source': 'src/new_bs_commands.c'}}
COMMON_ROOT_SHA256 = '3634bed55ba5bcb8321040fc55a83057a94438a17ed6a7dede0e73b07d2dbc31'

# 独立公開serializerの意味。ROMのbyte列を意味定義として複写しない。
GRAMMAR={
 'attackcanceler':(0,1,()),
 'jumpifmove':(42,12,((1,1,'predicate'),(2,4,'read_address'),(6,2,'move_id'),(8,4,'script_pointer'))),
 'jumpifbehindsubstitute':(29,10,((1,1,'bank'),(2,4,'status_mask'),(6,4,'script_pointer'))),
 'jumpifcounter':(0xFF09,10,((2,1,'bank'),(3,1,'counter'),(4,1,'predicate'),(5,1,'compare'),(6,4,'script_pointer'))),
}
PROGRAM=(
 (ROOT,'attackcanceler',()),
 (ROOT+1,'jumpifmove',(0,0x02023CAA,0x2B4,0x090072E6)),
 (ROOT+13,'jumpifmove',(0,0x02023CAA,0x2E0,0x09007236)),
 (ROOT+25,'jumpifmove',(0,0x02023CAA,0x2D3,0x09007273)),
 (ROOT+37,'jumpifmove',(0,0x02023CAA,0x2D8,0x090072AD)),
 (ROOT+49,'jumpifmove',(0,0x02023CAA,0x426,0x09007319)),
 (0x090071F7,'jumpifbehindsubstitute',(0,0x1000000,0x09008E11)),
 (0x09007201,'jumpifcounter',(0,2,1,0,0x09008E11)),
 (0x09007236,'jumpifbehindsubstitute',(0,0x1000000,0x09008E11)),
 (0x09007240,'jumpifcounter',(0,5,1,0,0x09008E11)),
)

# 現JP 1DとFF09の全pointer operand読みを、実bank0 resolverまで実行する。
BLOCKS={
 'status_pointer_read':native.block(0x091074D4,[
  ('push',0xF8,True),('literal',5,0x0910754C),('mem',True,'word',3,5,0),('mem',True,'byte',0,3,1),('call',0x090D3D2C),
  ('mem',True,'word',3,5,0),('mem',True,'byte',1,3,3),('mem',True,'byte',2,3,2),('shift','lsl',1,1,8),('alu','orr',1,2),
  ('mem',True,'byte',2,3,4),('mem',True,'byte',4,3,5),('shift','lsl',2,2,16),('alu','orr',2,1),('shift','lsl',4,4,24),('alu','orr',4,2),
  ('mem',True,'byte',2,3,7),('mem',True,'byte',1,3,6),('shift','lsl',2,2,8),('alu','orr',2,1),('mem',True,'byte',1,3,8),('mem',True,'byte',7,3,9),
  ('shift','lsl',1,1,16),('mem',True,'byte',3,3,1),('alu','orr',1,2),('shift','lsl',7,7,24),('shift','lsl',6,0,0),('alu','orr',7,1)]),
 'counter_pointer_read':native.block(0x0911AF68,[
  ('push',0xF0,True),('movhi',14,8),('push',0,True),('literal',6,0x0911B0E0),('mem',True,'word',3,6,0),('mem',True,'byte',0,3,1),('call',0x090D3D2C),
  ('mem',True,'word',3,6,0),('mem',True,'byte',1,3,6),('mem',True,'byte',2,3,5),('shift','lsl',1,1,8),('alu','orr',1,2),
  ('mem',True,'byte',2,3,7),('mem',True,'byte',4,3,8),('mem',True,'byte',5,3,3),('mem',True,'byte',7,3,4),
  ('shift','lsl',2,2,16),('mem',True,'byte',3,3,2),('alu','orr',2,1),('shift','lsl',4,4,24),('alu','orr',4,2)]),
 'bank_resolver':native.block(0x090D3D2C,[('push',16,True),('imm','cmp',0,15),('branch',8,0x090D3D3A),('literal',3,0x090D3D8C),('shift','lsl',0,0,2),('loadreg',3,3,0),('movhi',15,3)]),
 'bank_return':native.block(0x090D3D3C,[('pop',16,True)]),
 'target_bank':native.block(0x090D3D7E,[('literal',3,0x090D3DA4),('mem',True,'byte',0,3,0),('jump',0x090D3D3C)]),
}
INS={i.address:i for rows in BLOCKS.values()for i in rows}
# 値を具体化するのは真のtable/literalだけ。未使用labelの領域は型付けしない。
WORDS={0x0910754C:CURSOR,0x0911B0E0:CURSOR,0x090D3D8C:0x09161410,0x090D3DA4:0x02023CCC,
 0x09161410:0x090D3D7E,prior.PRIMARY+29*4:0x091074D5,prior.PRIMARY:0x090BD385,
 prior.EFFECTS+EFFECT*4:ROOT}

def exact(a,b):return type(a)is type(b)and a==b if not isinstance(a,(dict,list,tuple)) else (type(a)is type(b)and (set(a)==set(b)and all(exact(a[k],b[k])for k in a)if isinstance(a,dict)else len(a)==len(b)and all(exact(x,y)for x,y in zip(a,b))))

def encoded(i):
 if i.kind=='loadreg':rd,rb,ro=i.args;return (0x5800|(ro<<6)|(rb<<3)|rd).to_bytes(2,'little')
 return native.encoded(i)

class Machine(rt.Machine):
 def step(self,branch_choice=None):
  i=self.instructions[self.pc]
  if i.kind=='loadreg':
   rd,rb,ro=i.args;self.reg[rd]=self.read(self.reg[rb]+self.reg[ro],4);self.pc+=2;self.steps+=1
  else:super().step(branch_choice)


def source_proof(review,sources):
 need(exact(review['source_bindings'],SOURCE_IDS),'independently pinned closed source metadata')
 need(set(sources)=={v['local']for v in SOURCE_IDS.values()},'all and only finite public source files')
 for b in SOURCE_IDS.values():
  raw=sources[b['local']];need(identity(raw)=={k:b[k]for k in('size','sha256')},'whole independent source digest')
  need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==b['git_blob_sha'],'whole independent Git blob')
 old={role:SOURCE_IDS[local]for role,local in SOURCE_ROLES.items()if role!='assembly/battle_scripts/general_attack_battle_scripts.s'}
 prior.source_bindings({'source_bindings':old},sources)
 macro=re.sub(r'@[^\n]*','',sources[old['battle_script_macros.s']['local']].decode())
 defines=re.sub(r'@[^\n]*','',sources[old['asm_defines.s']['local']].decode())
 constants={'EQUALS':0,'CURRENT_MOVE':0x02023CAA,'STATUS2_SUBSTITUTE':0x1000000}
 for name,value in [('EQUALS',0),('BANK_TARGET',0),('NOTEQUALS',1)]:
  m=re.search(r'^\.equ\s+'+name+r',\s*(\w+)',macro,re.M);need(m and int(m[1],0)==value,'source constant')
 for name,value in [('STATUS2_SUBSTITUTE',0x1000000),('HEAL_BLOCK_TIMERS',2),('EMBARGO_TIMERS',5)]:
  m=re.search(r'^\.equ\s+'+name+r',\s*(\w+)',defines,re.M);need(m and int(m[1],0)==value,'source fixed condition constant')
 shapes={
 'attackcanceler':[(1,'0x00')],
 'jumpifmove':[(1,'0x2a'),(1,'EQUALS'),(4,'CURRENT_MOVE'),(2,'\\compare'),(4,'\\rom_address')],
 'jumpifbehindsubstitute':[(1,'0x1D'),(1,'\\bank'),(4,'STATUS2_SUBSTITUTE'),(4,'\\rom_address')],
 'jumpifcounter':[(1,'0xFF'),(1,'0x09'),(1,'\\bank'),(1,'\\counter_id'),(1,'\\predicate'),(1,'\\compare_byte'),(4,'\\rom_address')],
 }
 for name,shape in shapes.items():
  body=re.findall(r'\.macro\s+'+name+r'(?:[ \t][^\n]*)?\n(.*?)\.endm',macro,re.S);need(len(body)==1,'one concrete serializer');fields=[]
  for line in body[0].splitlines():
   line=line.strip()
   if not line:continue
   m=re.fullmatch(r'\.(byte|2byte|4byte|word)\s+(.+)',line);need(m is not None,'finite direct serializer')
   fields.extend(({'byte':1,'2byte':2,'4byte':4,'word':4}[m[1]],v.strip())for v in m[2].split(','))
  need(fields==shape and sum(z for z,_ in fields)==GRAMMAR[name][1],'independent exact serializer layout '+name)
 src=sources[SOURCE_IDS[SOURCE_ROLES['assembly/battle_scripts/general_attack_battle_scripts.s']]['local']].decode()
 compact=lambda s:[' '.join(line.split())for line in re.sub(r'@[^\n]*','',s).splitlines()if line.strip()]
 root=compact(src.split('BS_231_AttackBlockers:',1)[1].split('HealBlockBS:',1)[0])
 need(root==['attackcanceler','jumpifmove MOVE_THROATCHOP ThroatChopBS','jumpifmove MOVE_EMBARGO EmbargoBS','jumpifmove MOVE_POWDER PowderBS','jumpifmove MOVE_TELEKINESIS TelekinesisBS','jumpifmove MOVE_PSYCHICNOISE PsychicNoiseBS'],'independent source effect231 prefix')
 for label,counter in [('HealBlockBS','HEAL_BLOCK_TIMERS'),('EmbargoBS','EMBARGO_TIMERS')]:
  rows=compact(src.split(label+':',1)[1]);need(rows[:2]==['jumpifbehindsubstitute BANK_TARGET FAILED_PRE',f'jumpifcounter BANK_TARGET {counter} NOTEQUALS 0x0 FAILED_PRE'],'source adjacent complete commands with distinct pointer fields')
 effects=sources[old['assembly/data/move_effect_table.s']['local']].decode().split('gBattleScriptsForMoveEffects:',1)[1].split('gSetStatusMoveEffects:',1)[0]
 need(re.findall(r'^\s*\.word\s+(\S+)',effects,re.M)[EFFECT]=='BS_231_AttackBlockers','actual selected source registration')
 table=sources[old['assembly/data/battle_script_commands_table.s']['local']].decode().split('gBattleScriptingCommandsTable:',1)[1].split('gBattleScriptingCommandsTable2:',1)[0]
 need(re.findall(r'^\s*\.word\s+(\S+)',table,re.M)[29]=='atk1D_jumpifstatus2','exact selected native handler source registration')
 general=sources[old['src/general_bs_commands.c']['local']].decode();body=general.split('void atk1D_jumpifstatus2(void)',1)[1].split('void atk1F_',1)[0]
 for token in ['T2_READ_32(gBattlescriptCurrInstr + 2)','T2_READ_PTR(gBattlescriptCurrInstr + 6)','gBattlescriptCurrInstr += 10;']:
  need(token in body,'independent current consumer operand semantics')
 return True


def bind_program(raw):
 out=[]
 for address,name,values in PROGRAM:
  op,size,fields=GRAMMAR[name];prefix=bytes([255,op&255]if op>255 else[op]);b=chunk(raw,address,size)
  need(b[:len(prefix)]==prefix,'source opcode at registered command boundary')
  need(tuple(int.from_bytes(b[o:o+n],'little')for o,n,_ in fields)==values,'independent complete typed actual arguments')
  out.append(dict(address=address,name=name,opcode=op,size=size,fields=[dict(address=address+o,size=n,role=role,value=v)for (o,n,role),v in zip(fields,values)]))
 for left,right in zip(out[:7],out[1:8]):need(left['address']+left['size']==right['address'],'root-source serialized boundaries, not pointer search')
 need(out[8]['address']+out[8]['size']==out[9]['address'],'branch-root complete neighboring commands')
 for row in out[1:6]:need(chunk(raw,0x090421F4+12*row['fields'][2]['value'],1)[0]==EFFECT,'current move data actually registers this effect')
 return out


def pointer_read_proof(raw):
 for rows in BLOCKS.values():
  for i in rows:need(chunk(raw,i.address,i.size)==encoded(i),'independent actual JP operand consumer '+i.kind)
 for a,value in WORDS.items():need(d.u32(raw,a)==value,'finite true registration/literal role')
 proof=[]
 for address,name,values in PROGRAM:
  if name not in('jumpifbehindsubstitute','jumpifcounter'):continue
  extended=name=='jumpifcounter';cursor=address+int(extended);mem={};rt.setmem(mem,CURSOR,4,cursor);rt.setmem(mem,0x02023CCC,1,1)
  entry,stop=(0x0911AF68,0x0911AF94)if extended else(0x091074D4,0x0910750E)
  m=Machine(raw,entry,memory=mem,instructions=INS)
  while m.pc!=stop:m.step()
  need(m.reg[4 if extended else 7]==values[-1],'actual full four-byte operand reconstruction')
  need(rt.getmem(m.mem,CURSOR,4)==cursor,'read prefix does not manufacture successor')
  need(m.reg[0]==1,'real bank0 helper follows its real table slot')
  need(all(0x03006F00<=a<a+n<=0x03007000 for _,a,n in m.writes),'only legitimate handler/callee stack writes before pointer read')
  proof.append(dict(command=address,handler=entry,stop=stop,pointer=values[-1],pointer_bytes=4,actual_resolver_table=True,steps=m.steps))
 return proof


def witness_geometry(e):
 need(isinstance(e,dict)and set(e)=={'hit','kind','root','left_command','right_command','whole_pointers','byte_roles','claims'},'closed minimum battle type witness')
 need(type(e['hit'])is int and e['hit']in HITS and e['kind']==KIND and e['root']==ROOT,'only two independently rooted crossing hits')
 hit=e['hit'];left=hit-8;right=hit+2
 need(exact(e['left_command'],{'address':left,'size':10,'opcode':29}),'complete left jumpifstatus2 command')
 need(exact(e['right_command'],{'address':right,'size':10,'opcode':0xFF09}),'complete right extended command')
 need(exact(e['whole_pointers'],[{'address':left+6,'size':4,'value':0x09008E11},{'address':right+6,'size':4,'value':0x09008E11}]),'whole real pointer fields separate from crossing')
 need(exact(e['byte_roles'],['left_script_pointer_byte2','left_script_pointer_byte3','right_primary_opcode','right_secondary_opcode']),'all four exact byte roles')
 need(exact(e['claims'],CLAIMS),'minimal static type is not runtime reachability')
 need(not d.DONOR_LO<=d.canonical(0x09008E11)<d.DONOR_HI,'full genuine pointers outside donor')
 return hit,4


def evidence_template(hit):
 e=dict(hit=hit,kind=KIND,root=ROOT,left_command=dict(address=hit-8,size=10,opcode=29),right_command=dict(address=hit+2,size=10,opcode=0xFF09),
  whole_pointers=[dict(address=hit-2,size=4,value=0x09008E11),dict(address=hit+8,size=4,value=0x09008E11)],
  byte_roles=['left_script_pointer_byte2','left_script_pointer_byte3','right_primary_opcode','right_secondary_opcode'],claims=copy.deepcopy(CLAIMS))
 witness_geometry(e);return e


def own_geometry():
 rows={(i.address,i.size)for i in INS.values()}|{(a,4)for a in WORDS}|{(0x0913194E,2)}
 rows|={(a,GRAMMAR[n][1])for a,n,_ in PROGRAM}
 rows|={(0x090421F4+12*v[2],1)for _,n,v in PROGRAM if n=='jumpifmove'}
 # 実primary 2Aの独立interpreterは新selector operandsだけで再利用。
 rows|={(a,2)for a in range(0x08021F10,0x08021FB8,2)}
 return sorted(rows)


def protected_windows(review):
 return prior.protected_windows({'common_root':review['common_root'],'windows':review['windows']})


def make_review(raw,inherited,common_root):
 by={h['address']:h for h in inherited['hits']}
 return dict(schema_version=1,required_candidate=copy.deepcopy(CANDIDATE),diagnostic_input=copy.deepcopy(DIAGNOSTIC),source_bindings=copy.deepcopy(SOURCE_IDS),common_root=copy.deepcopy(common_root),
  hits=[copy.deepcopy(by[h])for h in HITS],windows=[dict(address=a,**identity(chunk(raw,a,n)))for a,n in own_geometry()],claims=copy.deepcopy(CLAIMS))


def _regions(raw,inherited,review,sources):
 need(set(review)=={'schema_version','required_candidate','diagnostic_input','source_bindings','common_root','hits','windows','claims'},'closed new classifier review')
 need(type(review['schema_version'])is int and review['schema_version']==1,'exact schema')
 need(exact(review['required_candidate'],CANDIDATE)and exact(inherited['candidate'],CANDIDATE)and exact(review['diagnostic_input'],DIAGNOSTIC),'distinct accepted and diagnostic identities')
 need(exact(review['claims'],CLAIMS),'separate type and runtime obligations')
 common=review['common_root'];need(hashlib.sha256(json.dumps(common,sort_keys=True,separators=(',',':')).encode()).hexdigest()==COMMON_ROOT_SHA256,'independent inherited common registration proof only')
 source_proof(review,sources);prior.root_consumers(raw,common)
 need([(w['address'],w['size'])for w in review['windows']]==own_geometry(),'closed minimal new read windows')
 for w in review['windows']:need(set(w)=={'address','size','sha256'},'digest-only source window');d.signed(raw,w)
 rows=bind_program(raw);consumers=pointer_read_proof(raw)
 selectors=[]
 for row in rows[1:6]:
  c=dict(address=row['address'],opcode=42,**identity(chunk(raw,row['address'],12)),control_fields=[dict(address=row['address']+8,size=4,value=d.u32(raw,row['address']+8))])
  selectors.append(prior.native_model(raw,c,'taken'))
  selectors.append(prior.native_model(raw,c,'next'))
 need(selectors[2]['next_cursor']==0x09007236,'current actual native selector roots second typed block')
 old=inherited['hits'];need(len({h['address']for h in old})==len(old),'unique inherited hits')
 by={h['address']:h for h in old};need(exact(review['hits'],[by[h]for h in HITS]),'entire inherited unknown rows preserved')
 regions=[]
 for h in review['hits']:
  need(type(h['accepted'])is bool and h['accepted']is False and h['owner_candidates']==[] and h['classification']=='UNCLASSIFIED'and type(h['size'])is int and h['size']==4,'unowned exact four-byte unknown only');d.signed(raw,h)
  e=evidence_template(h['address']);start,size=witness_geometry(e);regions.append(d.TypedRegion(start,start+size,KIND,e))
 return regions,dict(status='PASS_TWO_SOURCE_ROOTED_BATTLE_SCRIPT_TYPES',count=2,hits=list(HITS),typed_bytes=8,source_serialized_root=True,native_pointer_read_proofs=consumers,native_selector_models=[{k:m[k]for k in ('command','opcode','edge','entry','next_cursor')}for m in selectors],
  protected_windows=len(protected_windows(review)),protected_bytes=sum(w['size']for w in protected_windows(review)),**CLAIMS)


def regions(raw,inherited,review,sources):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'full current0641 identity before formal acceptance')
 return _regions(raw,inherited,review,sources)
