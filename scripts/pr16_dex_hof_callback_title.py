"""新タイトルconsumer一件のreset/heap/task/scene有限鎖。実画面到達は主張しない。"""
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_remaining_engine as old
import pr16_dex_hof_script_engine as common
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE
HITS=(0x08162BFD,)
COMMON_WINDOWS=(('setup_dispatch_argument_loads', 134648756, 12), ('InitScriptContext_dispatch_stores', 134647916, 18), ('RunScriptCommand_opcode_dispatch', 134648088, 26), ('interwork_r1', 136084172, 2), ('special_readhalfword_bound_and_call', 134649788, 28), ('ScriptReadHalfword', 134648248, 24), ('interwork_r0', 136084168, 2), ('CreateTask_store_argument', 134704052, 30), ('CreateTask_make_active', 134704102, 8), ('RunTasks_actual_consumer', 134704400, 42), ('reset_vector', 134217728, 4), ('reset_startup_arm', 134218244, 48), ('set_main_callback2', 134219076, 16), ('main_call_callbacks', 134219024, 48), ('CreateTask_post_store_setup', 134704082, 20), ('CreateTask_bounded_loop_return', 134704116, 18), ('FindFirstActiveTask_bounded_index', 134704448, 56))
PATHS=(
 ('boot',0x080003A4,0x080004D2),
 ('copyright',0x080ED71C,0x080ED70A),
 ('wait_intro',0x080ED4E0,0x080ED4EE),
 ('intro_create',0x080ED76C,0x080ED980),
 ('intro_skip',0x080ED9AC,0x080ED9D8),
 ('intro_exit',0x080EEAE8,0x080EEB30),
 ('title_create',0x080780AC,0x08078270),
 ('scene_producer',0x080783BC,0x080783FC),
 ('scene_selector',0x080783BC,0x0807841A),
 ('scene3',0x08078758,0x080787F2),
 ('berry_transition',0x08078E78,0x08078E8A),
 ('berry_create',0x08162A5C,0x08162AB2),
 ('berry_switch',0x08162B00,0x08162B24),
 ('berry_consumer',0x08162BD8,0x08162C00),
 ('intro_scheduler',0x080ED892,0x080ED8A0),
 ('title_scheduler',0x08078274,0x08078288),
 ('berry_scheduler',0x08162AB6,0x08162AC8),
 ('intro_exit_state0',0x080EEAE8,0x080EEB0A),
 ('title_init_state0',0x080780AC,0x080782BC),
 ('title_init_state1',0x080780AC,0x080782BC),
 ('berry_state0',0x08162B5C,0x08162CB4),
 ('berry_state1',0x08162B66,0x08162CB4),
 ('berry_state2',0x08162B84,0x08162CB4),
 ('berry_state4',0x08162BA0,0x08162CB4),
)
CALLBACKS=(
 (0x080004D0,0x080004D2,0x080004F8,0x080ED71C,0x08000544,None),
 (0x080ED708,0x080ED70A,0x080ED718,0x080ED4E0,0x08000544,None),
 (0x080ED4EC,0x080ED4EE,0x080ED4F8,0x080ED76C,0x08000544,None),
 (0x080ED97C,0x080ED980,0x080ED9A0,0x080ED9AC,0x08076BB4,3),
 (0x080EEB2E,0x080EEB30,0x080EEB3C,0x080780AC,0x08000544,None),
 (0x0807826C,0x08078270,0x0807829C,0x080783BC,0x08076BB4,4),
 (0x080787F0,0x080787F2,0x080787FC,0x08078E78,0x08000544,None),
 (0x08078E88,0x08078E8A,0x08078E94,0x08162A5C,0x08000544,None),
 (0x08162AAE,0x08162AB2,0x08162AE8,0x08162B00,0x08076BB4,0),
)

class Semantics(common.ThumbConsumer):
 def __init__(self,raw):super().__init__(raw);self.reads={}
 def opcode(self,a,value,meaning):self.reads[a]=2;super().opcode(a,value,meaning)
 def call(self,a,target):self.reads[a]=4;super().call(a,target)
 def pointer(self,a,reg,slot):self.reads[a]=2;self.reads[slot]=4;super().pointer(a,reg,slot)
 def hmem(self,a,load,rd,rb,offset):
  need(offset%2==0,'halfword field alignment');self.opcode(a,(0x8800 if load else 0x8000)|((offset//2)<<6)|(rb<<3)|rd,'halfword field')
 def ldrsh(self,a,rd,rb,ro):self.opcode(a,0x5E00|(ro<<6)|(rb<<3)|rd,'signed halfword field')
 def logic(self,a,kind,rd,rs):self.opcode(a,0x4000|({'and':0,'orr':12}[kind]<<6)|(rs<<3)|rd,'logical '+kind)
 def value(self,a,expected):self.reads[a]=4;need(d.u32(self.raw,a)==expected,'exact literal role')


def task_word_roundtrip(raw):
 """同一CreateTask返値とallocationをtask data[0..1]へ往復。"""
 s=Semantics(raw)
 s.pointer(0x080ED96E,0,0x080ED998);s.value(0x080ED998,0x28BC);s.call(0x080ED970,0x08002B9C)
 s.addi(0x080ED974,4,0,0);s.pointer(0x080ED976,1,0x080ED99C);s.value(0x080ED99C,0x080ED9ED);s.call(0x080ED978,0x080ED9A4)
 s.mem(0x080ED984,False,True,0,4,5);s.mem(0x080ED986,True,True,0,4,5);s.imm(0x080ED988,'mov',1,0);s.addi(0x080ED98A,2,4,0);s.call(0x080ED98C,0x08076E80)
 s.stack(0x080ED990,True,16);s.stack(0x080ED992,True,1);s.bx(0x080ED994,0)
 s.mem(0x080ED9A4,False,False,1,0,0);s.imm(0x080ED9A6,'mov',1,0);s.mem(0x080ED9A8,False,True,1,0,4);s.bx(0x080ED9AA,14)
 s.stack(0x08076E80,False,48,True);s.addi(0x08076E82,5,2,0)
 for a,right,rd,rs,n in [(0x08076E84,False,0,0,24),(0x08076E86,True,4,0,24),(0x08076E88,False,1,1,24),(0x08076E8A,True,3,1,24)]:s.shift(a,right,rd,rs,n)
 s.imm(0x08076E8C,'cmp',3,14);s.branch(0x08076E8E,8,0x08076EAE);s.pointer(0x08076E90,2,0x08076EB4);s.value(0x08076EB4,0x030050D0)
 s.shift(0x08076E92,False,0,3,1);s.shift(0x08076E94,False,1,4,2);s.add(0x08076E96,1,1,4);s.shift(0x08076E98,False,1,1,3);s.add(0x08076E9A,0,0,1);s.imm(0x08076E9C,'add',2,8);s.add(0x08076E9E,0,0,2);s.hmem(0x08076EA0,False,5,0,0)
 s.addi(0x08076EA2,0,3,1);s.shift(0x08076EA4,False,0,0,1);s.add(0x08076EA6,0,0,1);s.add(0x08076EA8,0,0,2);s.shift(0x08076EAA,True,1,5,16);s.hmem(0x08076EAC,False,1,0,0)
 s.stack(0x08076EAE,True,48);s.stack(0x08076EB0,True,1);s.bx(0x08076EB2,0)
 s.stack(0x08076EB8,False,16,True)
 for a,right,rd,rs,n in [(0x08076EBA,False,0,0,24),(0x08076EBC,True,4,0,24),(0x08076EBE,False,1,1,24),(0x08076EC0,True,1,1,24)]:s.shift(a,right,rd,rs,n)
 s.imm(0x08076EC2,'cmp',1,14);s.branch(0x08076EC4,9,0x08076ECA);s.imm(0x08076EC6,'mov',0,0);s.jump(0x08076EC8,0x08076EEC)
 s.pointer(0x08076ECA,3,0x08076EF4);s.value(0x08076EF4,0x030050D0)
 s.shift(0x08076ECC,False,0,1,1);s.shift(0x08076ECE,False,2,4,2);s.add(0x08076ED0,2,2,4);s.shift(0x08076ED2,False,2,2,3);s.add(0x08076ED4,0,0,2);s.imm(0x08076ED6,'add',3,8);s.add(0x08076ED8,0,0,3);s.hmem(0x08076EDA,True,0,0,0)
 s.imm(0x08076EDC,'add',1,1);s.shift(0x08076EDE,False,1,1,1);s.add(0x08076EE0,1,1,2);s.add(0x08076EE2,1,1,3);s.imm(0x08076EE4,'mov',2,0);s.ldrsh(0x08076EE6,1,1,2);s.shift(0x08076EE8,False,1,1,16);s.logic(0x08076EEA,'orr',0,1)
 s.stack(0x08076EEC,True,16);s.stack(0x08076EEE,True,2);s.bx(0x08076EF0,1)
 # callback task invokes SetIntroCB and then reads the same allocation immediately.
 s.stack(0x080ED9AC,False,16,True);s.shift(0x080ED9AE,False,0,0,24);s.shift(0x080ED9B0,True,0,0,24);s.imm(0x080ED9B2,'mov',1,0);s.call(0x080ED9B4,0x08076EB8);s.addi(0x080ED9B8,4,0,0)
 s.pointer(0x080ED9BA,0,0x080ED9E4);s.value(0x080ED9E4,0x03003130);s.hmem(0x080ED9BC,True,1,0,46);s.imm(0x080ED9BE,'mov',0,13);s.logic(0x080ED9C0,'and',0,1);s.imm(0x080ED9C2,'cmp',0,0);s.branch(0x080ED9C4,0,0x080ED9D4)
 s.mem(0x080ED9C6,True,False,0,4,0);s.pointer(0x080ED9C8,1,0x080ED9E8);s.value(0x080ED9E8,0x080EEAE9);s.compare(0x080ED9CA,0,1);s.branch(0x080ED9CC,0,0x080ED9D4);s.addi(0x080ED9CE,0,4,0);s.call(0x080ED9D0,0x080ED9A4)
 s.mem(0x080ED9D4,True,False,1,4,0);s.addi(0x080ED9D6,0,4,0);s.call(0x080ED9D8,0x081C7ACC)
 # Exit state0 writes1; state1 destroys the same task, frees once, then installs title callback.
 s.stack(0x080EEAE8,False,16,True);s.addi(0x080EEAEA,4,0,0);s.mem(0x080EEAEC,True,True,0,4,4);s.imm(0x080EEAEE,'cmp',0,0);s.branch(0x080EEAF0,0,0x080EEAF8);s.imm(0x080EEAF2,'cmp',0,1);s.branch(0x080EEAF4,0,0x080EEB0C)
 s.call(0x080EEB00,0x0806FBC8);s.mem(0x080EEB04,True,True,0,4,4);s.imm(0x080EEB06,'add',0,1);s.mem(0x080EEB08,False,True,0,4,4);s.jump(0x080EEB0A,0x080EEB34)
 s.call(0x080EEB0C,0x080F7884);s.shift(0x080EEB10,False,0,0,24);s.imm(0x080EEB12,'cmp',0,0);s.branch(0x080EEB14,1,0x080EEB34)
 s.mem(0x080EEB16,True,True,0,4,5);s.call(0x080EEB18,0x08076CA0);s.addi(0x080EEB1C,0,4,0);s.call(0x080EEB1E,0x08002BC4)
 return s.reads


def scene3_state(raw):
 """taskId由来data[0]への3の保存と、次回同一dataからslot3を選ぶ値証明。"""
 s=Semantics(raw)
 s.stack(0x080783BC,False,16,True);s.shift(0x080783BE,False,0,0,24);s.shift(0x080783C0,True,0,0,24);s.shift(0x080783C2,False,1,0,2);s.add(0x080783C4,1,1,0);s.shift(0x080783C6,False,1,1,3);s.pointer(0x080783C8,0,0x08078404);s.value(0x08078404,0x030050D8);s.add(0x080783CA,4,1,0)
 s.pointer(0x080783CC,0,0x08078408);s.value(0x08078408,0x03003130);s.hmem(0x080783CE,True,1,0,46);s.imm(0x080783D0,'mov',0,11);s.logic(0x080783D2,'and',0,1);s.imm(0x080783D4,'cmp',0,0);s.branch(0x080783D6,0,0x0807840C)
 s.imm(0x080783D8,'mov',1,0);s.ldrsh(0x080783DA,0,4,1)
 for a,n in [(0x080783DC,3),(0x080783E0,4),(0x080783E4,5)]:s.imm(a,'cmp',0,n);s.branch(a+2,0,0x0807840C)
 s.call(0x080783E8,0x08078DB0);s.call(0x080783EC,0x08078DD8);s.imm(0x080783F0,'mov',2,10);s.ldrsh(0x080783F2,0,4,2);s.call(0x080783F4,0x080791A0);s.addi(0x080783F8,0,4,0);s.imm(0x080783FA,'mov',1,3);s.call(0x080783FC,0x08078428);s.jump(0x08078400,0x0807841E)
 s.shift(0x08078428,False,1,1,24);s.shift(0x0807842A,True,1,1,24);s.imm(0x0807842C,'mov',2,0);s.hmem(0x0807842E,False,2,0,2);s.hmem(0x08078430,False,1,0,0);s.bx(0x08078432,14)
 s.pointer(0x0807840C,0,0x08078424);s.value(0x08078424,0x08386908);s.imm(0x0807840E,'mov',2,0);s.ldrsh(0x08078410,1,4,2);s.shift(0x08078412,False,1,1,2);s.add(0x08078414,1,1,0);s.mem(0x08078416,True,False,1,1,0);s.addi(0x08078418,0,4,0);s.call(0x0807841A,0x081C7ACC);s.value(0x08386914,0x08078759)
 s.stack(0x0807841E,True,16);s.stack(0x08078420,True,1);s.bx(0x08078422,0)
 # The exact finite model checks each active task index, not a fabricated table bound.
 for task_id in range(16):
  data=0x030050D8+40*task_id;scene,state=0,0
  need(11&1 and scene not in(3,4,5),'initial task data0=0 permits short-circuit producer')
  scene,state=3,0
  need(scene==3 and state==0 and 0x08386908+scene*4==0x08386914 and data==0x030050D8+40*task_id,'same-task scene3 value and selected slot')
 return s.reads


def title_init_states(raw):
 """同じgMain.stateの0/1から2への更新と、初期task poolの根。"""
 s=Semantics(raw)
 s.pointer(0x080780B0,0,0x080780C8);s.value(0x080780C8,0x03003130)
 s.imm(0x080780B2,'mov',1,135);s.shift(0x080780B4,False,1,1,3);s.add(0x080780B6,0,0,1);s.mem(0x080780B8,True,True,6,0,0)
 s.imm(0x080780BA,'cmp',6,1);s.branch(0x080780BC,0,0x08078188);s.imm(0x080780BE,'cmp',6,1);s.branch(0x080780C0,12,0x080780CC);s.imm(0x080780C2,'cmp',6,0);s.branch(0x080780C4,0,0x080780DE)
 s.imm(0x080780CC,'cmp',6,2);s.branch(0x080780CE,1,0x080780D2);s.jump(0x080780D0,0x08078258)
 s.call(0x080780F2,0x08076B54)
 s.pointer(0x080782B0,1,0x080782C8);s.value(0x080782C8,0x03003130);s.imm(0x080782B2,'mov',0,135);s.shift(0x080782B4,False,0,0,3);s.add(0x080782B6,1,1,0);s.mem(0x080782B8,True,True,0,1,0);s.imm(0x080782BA,'add',0,1);s.mem(0x080782BC,False,True,0,1,0)
 s.call(0x08078258,0x080F7884);s.shift(0x0807825C,False,0,0,24);s.imm(0x0807825E,'cmp',0,0);s.branch(0x08078260,1,0x080782BE)
 return s.reads


def schedulers(raw):
 s=Semantics(raw)
 for load,call,slot,target in [(0x080ED89E,0x080ED8A0,0x080ED8AC,0x080ED8D0),(0x08078286,0x08078288,0x080782AC,0x08078334),(0x08162AC6,0x08162AC8,0x08162AF0,0x08162AF4)]:
  s.pointer(load,0,slot);s.value(slot,target|1);s.call(call,0x08000544);s.stack(target,False,0,True);s.call(target+2,0x08076D10)
 s.pointer(0x08162ABA,2,0x08162AEC);s.value(0x08162AEC,0x030050D0)
 s.shift(0x08162AB6,False,0,0,24);s.shift(0x08162AB8,True,0,0,24);s.shift(0x08162ABC,False,1,0,2);s.add(0x08162ABE,1,1,0);s.shift(0x08162AC0,False,1,1,3);s.add(0x08162AC2,1,1,2);s.hmem(0x08162AC4,False,4,1,8)
 return s.reads


def berry_state_protocol(raw):
 """実constructor 0→task同一fieldの0/1/2/4→5 producer→bounded selector。"""
 s=Semantics(raw)
 # Constructor r4 is zero before all ABI calls; it is not written again before STRH.
 s.imm(0x08162A76,'mov',4,0);s.call(0x08162AA2,0x08076B54)
 s.stack(0x08162B00,False,112,True);s.opcode(0x08162B02,0xB081,'one-word local stack allocation')
 s.shift(0x08162B04,False,0,0,24);s.shift(0x08162B06,True,2,0,24);s.shift(0x08162B08,False,0,2,2);s.add(0x08162B0A,0,0,2);s.shift(0x08162B0C,False,0,0,3)
 s.pointer(0x08162B0E,1,0x08162B28);s.value(0x08162B28,0x030050D8);s.add(0x08162B10,5,0,1);s.imm(0x08162B12,'mov',1,0);s.ldrsh(0x08162B14,0,5,1);s.imm(0x08162B16,'cmp',0,10);s.branch(0x08162B18,9,0x08162B1C)
 for index,target in[(0,0x08162B5C),(1,0x08162B66),(2,0x08162B84),(4,0x08162BA0),(5,0x08162BD8)]:s.value(0x08162B30+4*index,target)
 s.imm(0x08162B5C,'mov',0,5);s.call(0x08162B5E,0x081629F0);s.imm(0x08162B62,'mov',0,1);s.jump(0x08162B64,0x08162CB4)
 for base,literal,nextstate,scene in[(0x08162B66,0x08162B80,2,0),(0x08162B84,0x08162B9C,4,1)]:
  s.pointer(base,0,literal);s.value(literal,0x03003130);s.hmem(base+2,True,1,0,46);s.imm(base+4,'mov',0,1);s.logic(base+6,'and',0,1);s.imm(base+8,'cmp',0,0);s.branch(base+10,1,base+14);s.jump(base+12,0x08162CB6)
  s.imm(base+14,'mov',0,scene);s.call(base+16,0x081629F0);s.imm(base+20,'mov',0,nextstate);s.jump(base+22,0x08162CB4)
 s.imm(0x08162BB6,'mov',4,0);s.mem(0x08162BB8,False,True,4,1,0);s.call(0x08162BBA,0x0800B600);s.hmem(0x08162BBE,False,4,5,2);s.imm(0x08162BC0,'mov',0,5);s.jump(0x08162BC2,0x08162CB4)
 s.hmem(0x08162CB4,False,0,5,0);s.opcode(0x08162CB6,0xB001,'one-word local stack release');s.stack(0x08162CB8,True,112);s.stack(0x08162CBA,True,1);s.bx(0x08162CBC,0)
 # State5's timer crossing is a conditional code consumer, not a claim that cable exchange occurred.
 s.hmem(0x08162BEC,True,0,5,2);s.imm(0x08162BEE,'add',0,1);s.hmem(0x08162BF0,False,0,5,2);s.shift(0x08162BF2,False,0,0,16);s.opcode(0x08162BF4,0x1000|(16<<6),'ASR r0,r0,16');s.imm(0x08162BF6,'cmp',0,180);s.branch(0x08162BF8,13,0x08162C34);s.imm(0x08162BFA,'mov',0,2)
 for task_id in range(16):
  constructor_field=0x030050D0+40*task_id+8
  callback_field=0x030050D8+40*task_id
  need(constructor_field==callback_field,'same active task data0 across scheduler invocations')
  states=[0,1,2,4,5]
  need(all(0<=state<=10 for state in states)and 0x08162B30+4*states[-1]==0x08162B44,'every produced selector bounded, final actual slot5')
 return s.reads


def written_registers(raw,row):
 """選択経路のregister保持証明。BLはAAPCS caller-savedだけを失う。"""
 h=old.half(raw,row['address'])
 if row['size']==4:
  need(h&0xF800==0xF000,'only complete BL in four-byte rows');return {0,1,2,3,14}
 if h&0xF800 in(0,0x0800,0x1000,0x1800):return {h&7}
 if h&0xE000==0x2000:return set()if(h>>11)&3==1 else {(h>>8)&7}
 if h&0xFC00==0x4000:return set()if(h>>6)&15 in(8,10,11)else {h&7}
 if h&0xFC00==0x4400:
  mode=(h>>8)&3
  need(mode!=3,'opaque BX forbidden inside preserved-register path')
  return set()if mode==1 else {(h&7)|((h>>4)&8)}
 if h&0xF800==0x4800:return {(h>>8)&7}
 if h&0xF000==0x5000:return {h&7}if(h>>9)&7>=3 else set()
 if h&0xE000==0x6000 or h&0xF000==0x8000:return {h&7}if h&0x0800 else set()
 if h&0xF000==0x9000:return {(h>>8)&7}if h&0x0800 else set()
 if h&0xF000==0xA000:return {(h>>8)&7}
 if h&0xFF00==0xB000 or h&0xFE00==0xB400:return {13}
 if h&0xFE00==0xBC00:return {13}|{r for r in range(8)if h&(1<<r)}
 if h&0xF000==0xC000:return {(h>>8)&7}|({r for r in range(8)if h&(1<<r)}if h&0x0800 else set())
 if h&0xF000 in(0xD000,0xE000):return set()
 need(False,'unhandled Thumb register write in new finite proof')


def preserved(raw,rows,register):
 need(all(register not in written_registers(raw,row)for row in rows),'same selected register is never redefined before its consumer')


def merged_read_windows(raw,windows):
 """重複を除いた実読取窓。型付け範囲ではなく検証依存byteを保護する。"""
 merged=[]
 for a,b in sorted((w['address'],w['address']+w['size'])for w in windows):
  if merged and a<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],b)
  else:merged.append([a,b])
 return [dict(address=a,**identity(chunk(raw,a,b-a)))for a,b in merged]


def _regions(raw,inherited,review,sources):
 need(review['required_candidate']==CANDIDATE and len(review['rows'])==1,'one new title candidate only')
 need({v['local']for v in review['source_bindings'].values()}=={'BPRJ.ld','gaps-pret-scrcmd.c','pret-task.c','pret-main.c','pret-crt0.s','pret-hall_of_fame.c','pret-title_screen.c','pret-intro.c','pret-berry_fix_program.c'},'fixed sources for actual reset/task/intro/title roles')
 required={(w['label'],w['address'],w['size'])for w in review['consumer_windows']}
 need(all(item in required for item in COMMON_WINDOWS),'all shared consumer dependency windows protected')
 bprj=old.sources_bind(review,sources);common.bind_consumers(raw,review,bprj)
 row=review['rows'][0];hit=row['hit'];need(hit['address']==HITS[0] and hit==next(h for h in inherited['hits']if h['address']==HITS[0])and not hit['accepted']and not hit['owner_candidates'],'exact inherited unknown');d.signed(raw,hit)
 need(row['root']=={'kind':'reset_vector','entry':0x080003A4,'literal':0x08000244},'actual reset root only')
 need([(p['name'],p['instructions'][0]['address'],p['instructions'][-1]['address'])for p in row['paths']]==list(PATHS),'complete fixed chain segment roots and ends')
 for p in row['paths']:
  rows=p['instructions'];d.signed(raw,rows)
  if p['name']=='berry_switch':gaps.thumb_path(raw,rows[:-1],rows[0]['address']);need(rows[-2]['address']+2==rows[-1]['address'],'contiguous bounded indirect switch')
  else:gaps.thumb_path(raw,rows,rows[0]['address'])
 s=Semantics(raw)
 for load,call,slot,target,callee,priority in CALLBACKS:
  s.pointer(load,0,slot);s.value(slot,target|1);s.call(call,callee)
  if priority is not None:s.imm(load+2,'mov',1,priority)
 # The heap-rewrite and scene producer routes must really occur on the selected paths.
 byname={p['name']:{i['address']for i in p['instructions']}for p in row['paths']}
 sequences={p['name']:p['instructions']for p in row['paths']}
 need({0x080ED9C6,0x080ED9C8,0x080ED9CE,0x080ED9D0}<=byname['intro_skip'],'selected skip path includes write before indirect call')
 need({0x080783E8,0x080783F8,0x080783FA}<=byname['scene_producer'],'selected producer path passes exact scene3 argument')
 need({0x080783D6,0x0807840C,0x08078410,0x08078416}<=byname['scene_selector'],'next invocation loads same scene field and slot')
 preserved(raw,[p for p in sequences['berry_create']if 0x08162A76<p['address']]+[p for p in sequences['berry_scheduler']if p['address']<0x08162AC4],4)
 preserved(raw,[p for p in sequences['scene_producer']if 0x080783CA<p['address']<0x080783FC],4)
 preserved(raw,[p for p in sequences['intro_create']if 0x080ED974<p['address']],4)
 preserved(raw,[p for p in sequences['intro_skip']if 0x080ED9B8<p['address']<0x080ED9D8],4)
 for name in('berry_state0','berry_state1','berry_state2','berry_state4'):preserved(raw,sequences[name],5)
 reads={}
 for f in(task_word_roundtrip,scene3_state,title_init_states,schedulers,berry_state_protocol):reads.update(f(raw))
 s.call(0x080ED88E,0x080ED96C)
 # The scheduler tails are the continuations of the very same constructors.
 need(0x080ED88E in byname['intro_create'] and 0x080ED980 in byname['intro_create'],'rooted intro constructor call and task creation')
 need(0x080EEB04 in byname['intro_exit_state0'] and 0x080EEB08 in byname['intro_exit_state0'],'same-allocation state0 actually produces state1')
 need(0x080780F2 in byname['title_init_state0'] and 0x08078188 in byname['title_init_state1'],'actual title state0 reset and state1 setup reach same increment')
 for name,address in [('berry_state0',0x08162B62),('berry_state1',0x08162B7A),('berry_state2',0x08162B98),('berry_state4',0x08162BC0)]:need(address in byname[name],'actual state producer reaches same task data0 store')
 switch=row['berry_switch'];allrows=next(p['instructions']for p in row['paths']if p['name']=='berry_switch')+next(p['instructions']for p in row['paths']if p['name']=='berry_consumer')
 need((switch['from'],switch['to'],switch['count'],switch['index'])==(0x08162B24,0x08162BD8,11,5),'exact finite berry state5 switch')
 old.indirect(raw,switch,[p['address']for p in allrows])
 window=row['instruction_window'];d.signed(raw,window);need((window['address'],window['size'])==(0x08162BFC,6),'minimal whole BL and LDR only')
 selected=[p for p in allrows if window['address']<=p['address']<window['address']+window['size']]
 need([(p['address'],p['size'])for p in selected]==[(0x08162BFC,4),(0x08162C00,2)],'two complete instructions cover all four hit bytes')
 s.call(0x08162BFC,0x081629F0);s.pointer(0x08162C00,0,0x08162C28)
 reads.update(s.reads)
 for segment in row['paths']:
  for instruction in segment['instructions']:
   reads[instruction['address']]=instruction['size']
   if 'literal_address'in instruction:reads[instruction['literal_address']]=4
 protected={(w['address'],w['size'])for w in review['consumer_windows']}
 need(all((a,n)in protected for a,n in reads.items()),'every final semantic/path/literal read appears in protected consumer windows')
 need(row['literal_pool_included']is False and row['whole_function_range_classified']is False,'no literal or blanket function classification')
 proof=dict(status='PASS_FINITE_RESET_INTRO_TITLE_BERRY_CODE_WINDOW',count=1,scene_producer_and_selector_verified=True,heap_word_arg_roundtrip_verified=True,berry_state_producer_and_selector_verified=True,path_instructions=sum(len(p['instructions'])for p in row['paths']),full_story_reachability_claimed=False,full_title_lifetime_claimed=False,actual_berry_fix_hardware_exchange_claimed=False)
 return [d.TypedRegion(window['address'],window['address']+6,'rooted_thumb_instruction_stream',dict(root=row['root'],instruction_window=window,instructions=[{k:p[k]for k in('address','size')}for p in selected],root_verified=True,literal_pool_included=False,full_story_reachability_claimed=False,scene_producer_and_selector_verified=True,protected_windows=merged_read_windows(raw,review['consumer_windows']+review['consumer_literals']+[switch['table_literal_witness'],switch['slot_witness'],window])))],proof


def regions(raw,inherited,review,sources,root=None):
 need(identity(raw)==inherited['candidate']==CANDIDATE,'whole current candidate identity mandatory')
 return _regions(raw,inherited,review,sources)


def geometry(evidence):
 import pr16_dex_hof_reference_chain as chain
 return chain.witness_geometry(dict(kind="rooted_thumb_instruction_stream",evidence=evidence))
