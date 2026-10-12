"""FieldEffect8の実dispatch/native/template/animationを束縛する単一frame分類。"""
import hashlib,json,re,struct
import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_gaps as gaps
import pr16_dex_hof_reference_code as code
need,identity,chunk=d.need,d.identity,d.chunk
CANDIDATE=gaps.CANDIDATE

# source FieldEffectStart: u8 ID -> table slot -> stack script cursor -> opcode table -> BX r2.
# callnative: cursor+1 -> four byte reads -> BX r0 -> cursor+4; end returns false.
# SurfBlob: source template selector7 remains r0 at CreateSpriteAtEnd.
# callback: sprite argument r6 -> sync r1; direction nibble -> five-entry map -> anim r1.
# Every opcode, destination/base register, immediate, literal address and branch target
# of these complete finite slices is checked, including prologue/call/return clobbers.
SEMANTIC_PROGRAMS = {'FieldEffectStart': [(134754352, ('push', (4, 5, 14))),
                      (134754354, ('sub_sp', 8)),
                      (134754356, ('adds3', 4, 0, 'imm', 0)),
                      (134754358, ('lsls', 4, 4, 24)),
                      (134754360, ('lsrs', 4, 4, 24)),
                      (134754362, ('adds3', 0, 4, 'imm', 0)),
                      (134754364, ('bl', 134755260)),
                      (134754368, ('ldr_literal', 0, 134754416)),
                      (134754370, ('lsls', 4, 4, 2)),
                      (134754372, ('adds3', 4, 4, 'reg', 0)),
                      (134754374, ('ldr', 0, 4, 0)),
                      (134754376, ('str_sp', 0, 0)),
                      (134754378, ('add_sp', 4, 4)),
                      (134754380, ('ldr_literal', 5, 134754420)),
                      (134754382, ('ldr_sp', 0, 0)),
                      (134754384, ('ldrb', 0, 0, 0)),
                      (134754386, ('lsls', 0, 0, 2)),
                      (134754388, ('adds3', 0, 0, 'reg', 5)),
                      (134754390, ('ldr', 2, 0, 0)),
                      (134754392, ('mov_high', 0, 13)),
                      (134754394, ('adds3', 1, 4, 'imm', 0)),
                      (134754396, ('bl', 136084176)),
                      (134754400, ('lsls', 0, 0, 24)),
                      (134754402, ('cmp_imm', 0, 0)),
                      (134754404, ('b_cond', 1, 134754382)),
                      (134754406, ('ldr_sp', 0, 4)),
                      (134754408, ('add_sp_imm', 8)),
                      (134754410, ('pop', (4, 5))),
                      (134754412, ('pop', (1,))),
                      (134754414, ('bx', 1))],
 'dispatch_callnative': [(134754484, ('push', (14,))),
                         (134754486, ('ldr', 2, 0, 0)),
                         (134754488, ('adds8', 2, 1)),
                         (134754490, ('str', 2, 0, 0)),
                         (134754492, ('bl', 134754948)),
                         (134754496, ('movs', 0, 1)),
                         (134754498, ('pop', (1,))),
                         (134754500, ('bx', 1))],
 'dispatch_end': [(134754504, ('movs', 0, 0)), (134754506, ('bx', 14))],
 'script_readword': [(134754620, ('ldr', 2, 0, 0)),
                     (134754622, ('ldrb', 0, 2, 0)),
                     (134754624, ('ldrb', 1, 2, 1)),
                     (134754626, ('lsls', 1, 1, 8)),
                     (134754628, ('adds3', 0, 0, 'reg', 1)),
                     (134754630, ('ldrb', 1, 2, 2)),
                     (134754632, ('lsls', 1, 1, 16)),
                     (134754634, ('adds3', 0, 0, 'reg', 1)),
                     (134754636, ('ldrb', 1, 2, 3)),
                     (134754638, ('lsls', 1, 1, 24)),
                     (134754640, ('adds3', 0, 0, 'reg', 1)),
                     (134754642, ('bx', 14))],
 'call_native_and_advance': [(134754948, ('push', (4, 5, 14))),
                             (134754950, ('adds3', 4, 0, 'imm', 0)),
                             (134754952, ('adds3', 5, 1, 'imm', 0)),
                             (134754954, ('bl', 134754620)),
                             (134754958, ('bl', 136084168)),
                             (134754962, ('str', 0, 5, 0)),
                             (134754964, ('ldr', 0, 4, 0)),
                             (134754966, ('adds8', 0, 4)),
                             (134754968, ('str', 0, 4, 0)),
                             (134754970, ('pop', (4, 5))),
                             (134754972, ('pop', (0,))),
                             (134754974, ('bx', 0))],
 'interwork_r0': [(136084168, ('bx', 0))],
 'interwork_r2': [(136084176, ('bx', 2))],
 'surf_template_to_creator': [(135123896, ('push', (4, 5, 14))),
                              (135123898, ('ldr_literal', 4, 135124004)),
                              (135123900, ('adds3', 1, 4, 'imm', 4)),
                              (135123902, ('adds3', 0, 4, 'imm', 0)),
                              (135123904, ('movs', 2, 8)),
                              (135123906, ('movs', 3, 8)),
                              (135123908, ('bl', 134624388)),
                              (135123912, ('ldr_literal', 0, 135124008)),
                              (135123914, ('ldr', 0, 0, 28)),
                              (135123916, ('movs', 2, 0)),
                              (135123918, ('ldrsh_reg', 1, 4, 2)),
                              (135123920, ('movs', 3, 4)),
                              (135123922, ('ldrsh_reg', 2, 4, 3)),
                              (135123924, ('movs', 3, 150)),
                              (135123926, ('bl', 134245212)),
                              (135123930, ('lsls', 0, 0, 24)),
                              (135123932, ('lsrs', 0, 0, 24)),
                              (135123934, ('adds3', 5, 0, 'imm', 0)),
                              (135123936, ('cmp_imm', 0, 64)),
                              (135123938, ('b_cond', 0, 135123988)),
                              (135123940, ('lsls', 1, 0, 4)),
                              (135123942, ('adds3', 1, 1, 'reg', 0)),
                              (135123944, ('lsls', 1, 1, 2)),
                              (135123946, ('ldr_literal', 0, 135124012)),
                              (135123948, ('adds3', 1, 1, 'reg', 0)),
                              (135123950, ('adds3', 3, 1, 'imm', 0)),
                              (135123952, ('adds8', 3, 62)),
                              (135123954, ('ldrb', 0, 3, 0)),
                              (135123956, ('movs', 2, 2)),
                              (135123958, ('orrs', 0, 2)),
                              (135123960, ('strb', 0, 3, 0)),
                              (135123962, ('ldrb', 2, 1, 5)),
                              (135123964, ('movs', 0, 15)),
                              (135123966, ('ands', 0, 2)),
                              (135123968, ('strb', 0, 1, 5)),
                              (135123970, ('ldr', 0, 4, 8)),
                              (135123972, ('movs', 2, 0)),
                              (135123974, ('strh', 0, 1, 50)),
                              (135123976, ('strh', 2, 1, 52)),
                              (135123978, ('ldr_literal', 0, 135124016)),
                              (135123980, ('strh', 0, 1, 58)),
                              (135123982, ('movs', 0, 1)),
                              (135123984, ('negs', 0, 0)),
                              (135123986, ('strh', 0, 1, 60)),
                              (135123988, ('movs', 0, 8)),
                              (135123990, ('bl', 134755304)),
                              (135123994, ('adds3', 0, 5, 'imm', 0)),
                              (135123996, ('pop', (4, 5))),
                              (135123998, ('pop', (1,))),
                              (135124000, ('bx', 1)),
                              (135124002, ('lsls', 0, 0, 0))],
 'callback_sync_animation_call': [(135124192, ('push', (4, 5, 6, 14))),
                                  (135124194, ('adds3', 6, 0, 'imm', 0)),
                                  (135124196, ('movs', 1, 50)),
                                  (135124198, ('ldrsh_reg', 0, 6, 1)),
                                  (135124200, ('lsls', 4, 0, 3)),
                                  (135124202, ('adds3', 4, 4, 'reg', 0)),
                                  (135124204, ('lsls', 4, 4, 2)),
                                  (135124206, ('ldr_literal', 0, 135124272)),
                                  (135124208, ('adds3', 4, 4, 'reg', 0)),
                                  (135124210, ('ldrb', 0, 4, 4)),
                                  (135124212, ('lsls', 5, 0, 4)),
                                  (135124214, ('adds3', 5, 5, 'reg', 0)),
                                  (135124216, ('lsls', 5, 5, 2)),
                                  (135124218, ('ldr_literal', 0, 135124276)),
                                  (135124220, ('adds3', 5, 5, 'reg', 0)),
                                  (135124222, ('adds3', 0, 4, 'imm', 0)),
                                  (135124224, ('adds3', 1, 6, 'imm', 0)),
                                  (135124226, ('bl', 135124280)),
                                  (135124230, ('adds3', 0, 4, 'imm', 0))],
 'sync_animation_direction': [(135124280, ('push', (4, 5, 14))),
                              (135124282, ('sub_sp', 8)),
                              (135124284, ('adds3', 5, 0, 'imm', 0)),
                              (135124286, ('adds3', 4, 1, 'imm', 0)),
                              (135124288, ('ldr_literal', 1, 135124332)),
                              (135124290, ('mov_high', 0, 13)),
                              (135124292, ('movs', 2, 5)),
                              (135124294, ('bl', 136093080)),
                              (135124298, ('adds3', 0, 4, 'imm', 0)),
                              (135124300, ('bl', 135124168)),
                              (135124304, ('lsls', 0, 0, 24)),
                              (135124306, ('cmp_imm', 0, 0)),
                              (135124308, ('b_cond', 1, 135124324)),
                              (135124310, ('ldrb', 0, 5, 24)),
                              (135124312, ('lsrs', 0, 0, 4)),
                              (135124314, ('add_high', 0, 13)),
                              (135124316, ('ldrb', 1, 0, 0)),
                              (135124318, ('adds3', 0, 4, 'imm', 0)),
                              (135124320, ('bl', 134250272)),
                              (135124324, ('add_sp_imm', 8)),
                              (135124326, ('pop', (4, 5))),
                              (135124328, ('pop', (0,))),
                              (135124330, ('bx', 0))],
 'CreateSpriteAtEnd_selected_free_slot': [(134245212, ('push', (4, 5, 6, 7, 14))),
                                          (134245214, ('mov_high', 7, 8)),
                                          (134245216, ('push', (7,))),
                                          (134245218, ('sub_sp', 4)),
                                          (134245220, ('adds3', 7, 0, 'imm', 0)),
                                          (134245222, ('lsls', 3, 3, 24)),
                                          (134245224, ('lsrs', 6, 3, 24)),
                                          (134245226, ('movs', 3, 63)),
                                          (134245228, ('ldr_literal', 0, 134245288)),
                                          (134245230, ('mov_high', 8, 0)),
                                          (134245232, ('movs', 0, 1)),
                                          (134245234, ('negs', 0, 0)),
                                          (134245236, ('mov_high', 12, 0)),
                                          (134245238, ('lsls', 4, 1, 16)),
                                          (134245240, ('lsls', 5, 2, 16)),
                                          (134245242, ('lsls', 0, 3, 16)),
                                          (134245244, ('asrs', 1, 0, 16)),
                                          (134245246, ('lsls', 0, 1, 4)),
                                          (134245248, ('adds3', 0, 0, 'reg', 1)),
                                          (134245250, ('lsls', 0, 0, 2)),
                                          (134245252, ('add_high', 0, 8)),
                                          (134245254, ('adds8', 0, 62)),
                                          (134245256, ('ldrb', 0, 0, 0)),
                                          (134245258, ('lsls', 0, 0, 31)),
                                          (134245260, ('cmp_imm', 0, 0)),
                                          (134245262, ('b_cond', 1, 134245292)),
                                          (134245264, ('lsls', 0, 3, 24)),
                                          (134245266, ('lsrs', 0, 0, 24)),
                                          (134245268, ('str_sp', 6, 0)),
                                          (134245270, ('adds3', 1, 7, 'imm', 0)),
                                          (134245272, ('asrs', 2, 4, 16)),
                                          (134245274, ('asrs', 3, 5, 16)),
                                          (134245276, ('bl', 134245392)),
                                          (134245280, ('lsls', 0, 0, 24)),
                                          (134245282, ('lsrs', 0, 0, 24)),
                                          (134245284, ('b', 134245306))],
 'InitSprite_template_register_and_animation_fields': [(134245392, ('push', (4, 5, 6, 7, 14))),
                                                       (134245394, ('mov_high', 7, 10)),
                                                       (134245396, ('mov_high', 6, 9)),
                                                       (134245398, ('mov_high', 5, 8)),
                                                       (134245400, ('push', (5, 6, 7))),
                                                       (134245402, ('mov_high', 8, 1)),
                                                       (134245404, ('adds3', 5, 2, 'imm', 0)),
                                                       (134245406, ('adds3', 6, 3, 'imm', 0)),
                                                       (134245408, ('ldr_sp', 4, 32)),
                                                       (134245410, ('lsls', 0, 0, 24)),
                                                       (134245412, ('lsrs', 0, 0, 24)),
                                                       (134245414, ('mov_high', 10, 0)),
                                                       (134245416, ('lsls', 5, 5, 16)),
                                                       (134245418, ('lsrs', 5, 5, 16)),
                                                       (134245420, ('lsls', 6, 6, 16)),
                                                       (134245422, ('lsrs', 6, 6, 16)),
                                                       (134245424, ('lsls', 4, 4, 24)),
                                                       (134245426, ('lsrs', 4, 4, 24)),
                                                       (134245428, ('lsls', 0, 0, 4)),
                                                       (134245430, ('add_high', 0, 10)),
                                                       (134245432, ('lsls', 0, 0, 2)),
                                                       (134245434, ('ldr_literal', 1, 134245588)),
                                                       (134245436, ('adds3', 7, 0, 'reg', 1)),
                                                       (134245438, ('adds3', 0, 7, 'imm', 0)),
                                                       (134245440, ('bl', 134246232)),
                                                       (134245444, ('adds3', 2, 7, 'imm', 0)),
                                                       (134245446, ('adds8', 2, 62)),
                                                       (134245448, ('ldrb', 0, 2, 0)),
                                                       (134245450, ('movs', 1, 1)),
                                                       (134245452, ('orrs', 0, 1)),
                                                       (134245454, ('strb', 0, 2, 0)),
                                                       (134245456, ('movs', 0, 63)),
                                                       (134245458, ('adds3', 0, 0, 'reg', 7)),
                                                       (134245460, ('mov_high', 9, 0)),
                                                       (134245462, ('ldrb', 0, 0, 0)),
                                                       (134245464, ('movs', 1, 4)),
                                                       (134245466, ('orrs', 0, 1)),
                                                       (134245468, ('movs', 1, 8)),
                                                       (134245470, ('orrs', 0, 1)),
                                                       (134245472, ('movs', 1, 64)),
                                                       (134245474, ('orrs', 0, 1)),
                                                       (134245476, ('mov_high', 1, 9)),
                                                       (134245478, ('strb', 0, 1, 0)),
                                                       (134245480, ('adds3', 0, 7, 'imm', 0)),
                                                       (134245482, ('adds8', 0, 67)),
                                                       (134245484, ('strb', 4, 0, 0)),
                                                       (134245486, ('mov_high', 1, 8)),
                                                       (134245488, ('ldr', 0, 1, 4)),
                                                       (134245490, ('ldr', 1, 0, 4)),
                                                       (134245492, ('ldr', 0, 0, 0)),
                                                       (134245494, ('str', 0, 7, 0)),
                                                       (134245496, ('str', 1, 7, 4)),
                                                       (134245498, ('mov_high', 1, 8)),
                                                       (134245500, ('ldr', 0, 1, 8)),
                                                       (134245502, ('str', 0, 7, 8)),
                                                       (134245504, ('ldr', 0, 1, 16)),
                                                       (134245506, ('str', 0, 7, 16)),
                                                       (134245508, ('str', 1, 7, 20)),
                                                       (134245510, ('ldr', 0, 1, 20)),
                                                       (134245512, ('str', 0, 7, 28)),
                                                       (134245514, ('strh', 5, 7, 32)),
                                                       (134245516, ('strh', 6, 7, 34))],
 'InitSprite_frame_based_pointer_copy': [(134245518, ('ldrb', 3, 7, 1)),
                                         (134245520, ('lsrs', 1, 3, 6)),
                                         (134245522, ('ldrb', 2, 7, 3)),
                                         (134245524, ('lsrs', 2, 2, 6)),
                                         (134245526, ('lsls', 3, 3, 30)),
                                         (134245528, ('lsrs', 3, 3, 30)),
                                         (134245530, ('adds3', 0, 7, 'imm', 0)),
                                         (134245532, ('bl', 134246252)),
                                         (134245536, ('mov_high', 0, 8)),
                                         (134245538, ('ldrh', 1, 0, 0)),
                                         (134245540, ('ldr_literal', 4, 134245592)),
                                         (134245542, ('lsrs', 0, 4, 16)),
                                         (134245544, ('cmp_reg', 1, 0)),
                                         (134245546, ('b_cond', 1, 134245644)),
                                         (134245548, ('mov_high', 1, 8)),
                                         (134245550, ('ldr', 0, 1, 12)),
                                         (134245552, ('str', 0, 7, 12)),
                                         (134245554, ('ldrh', 0, 0, 4)),
                                         (134245556, ('lsrs', 0, 0, 5)),
                                         (134245558, ('lsls', 0, 0, 24)),
                                         (134245560, ('lsrs', 0, 0, 24)),
                                         (134245562, ('bl', 134246320)),
                                         (134245566, ('lsls', 0, 0, 16)),
                                         (134245568, ('lsrs', 2, 0, 16)),
                                         (134245570, ('asrs', 0, 0, 16)),
                                         (134245572, ('asrs', 1, 4, 16)),
                                         (134245574, ('cmp_reg', 0, 1)),
                                         (134245576, ('b_cond', 1, 134245596)),
                                         (134245578, ('adds3', 0, 7, 'imm', 0)),
                                         (134245580, ('bl', 134246232)),
                                         (134245584, ('movs', 0, 64)),
                                         (134245586, ('b', 134245716))],
 'StartSpriteAnimIfDifferent': [(134250272, ('push', (14,))),
                                (134250274, ('adds3', 2, 0, 'imm', 0)),
                                (134250276, ('lsls', 1, 1, 24)),
                                (134250278, ('lsrs', 1, 1, 24)),
                                (134250280, ('adds8', 0, 42)),
                                (134250282, ('ldrb', 0, 0, 0)),
                                (134250284, ('cmp_reg', 0, 1)),
                                (134250286, ('b_cond', 0, 134250294)),
                                (134250288, ('adds3', 0, 2, 'imm', 0)),
                                (134250290, ('bl', 134250248)),
                                (134250294, ('pop', (0,))),
                                (134250296, ('bx', 0))],
 'StartSpriteAnim': [(134250248, ('adds3', 2, 0, 'imm', 0)),
                     (134250250, ('adds8', 2, 42)),
                     (134250252, ('strb', 1, 2, 0)),
                     (134250254, ('adds8', 0, 63)),
                     (134250256, ('ldrb', 1, 0, 0)),
                     (134250258, ('movs', 2, 4)),
                     (134250260, ('orrs', 1, 2)),
                     (134250262, ('movs', 2, 17)),
                     (134250264, ('negs', 2, 2)),
                     (134250266, ('ands', 1, 2)),
                     (134250268, ('strb', 1, 0, 0)),
                     (134250270, ('bx', 14))]}

def decode_semantics(raw,address,size):
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

def _regions(raw,inherited,review,sources,root):
 need(review['required_candidate']==CANDIDATE,'same current target')
 for row in review['sources']:
  b=sources[row['local']];need(row['repository']=='pret/pokefirered'and row['commit']=='c75f352304d529f6ba92d4f74b9cf8b5c3810788'and identity(b)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['git_blob_sha'],'whole pinned public source')
 fixed=review['accepted_consumer_review'];b=(root/fixed['path']).read_bytes();need(identity(b)=={k:fixed[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==fixed['git_blob_sha'],'whole accepted sprite consumer identity')
 windows=[('FieldEffectStart', 134754352, 64), ('dispatch_callnative', 134754484, 18), ('dispatch_end', 134754504, 4), ('script_readword', 134754620, 24), ('call_native_and_advance', 134754948, 28), ('interwork_r0', 136084168, 2), ('interwork_r2', 136084176, 2), ('surf_template_to_creator', 135123896, 108), ('callback_sync_animation_call', 135124192, 40), ('sync_animation_direction', 135124280, 52), ('CreateSpriteAtEnd_selected_free_slot', 134245212, 74), ('InitSprite_template_register_and_animation_fields', 134245392, 126), ('InitSprite_frame_based_pointer_copy', 134245518, 70), ('StartSpriteAnimIfDifferent', 134250272, 26), ('StartSpriteAnim', 134250248, 24)]
 calls=[(134754396, 136084176), (134754492, 134754948), (134754954, 134754620), (134754958, 136084168), (135123926, 134245212), (135124226, 135124280), (135124320, 134250272), (134245276, 134245392), (134250290, 134250248)]
 need([(w['label'],w['address'],w['size'])for w in review['code_windows']]==windows and [(w['address'],w['target'])for w in review['direct_calls']]==calls and all(w['size']==4 for w in review['direct_calls']),'closed complete finite consumer windows and direct-call roots')
 gaps.bind_code_windows(raw,json.loads(b)['sprite']);gaps.bind_code_windows(raw,review)
 for window in review['code_windows']:
  need(decode_semantics(raw,window['address'],window['size'])==SEMANTIC_PROGRAMS[window['label']],'whole finite source register-transfer and control-flow semantics: '+window['label'])
 constants=sources['field_effects.h'].decode();need(re.search(r'#define\s+FLDEFF_SURF_BLOB\s+8\b',constants)and re.search(r'#define\s+FLDEFFOBJ_SURF_BLOB\s+7\b',constants),'two fixed source field effect selectors')
 src=sources['field_effect_objects.h'].decode();need('overworld_frame(gObjectEventPic_SurfBlob, 2, 8, 4)'in src,'source raw4bpp frame geometry')
 roots=review['roots'];d.signed(raw,roots)
 for v in roots.values():need(v['size']==4 and d.u32(raw,v['address'])==v['value'],'each current source-root pointer')
 st,dispatch,tt,dt=[roots[k]for k in('script_table_literal','dispatch_literal','template_table_literal','direction_table_literal')]
 need((st['address'],dispatch['address'],tt['address'],dt['address'])==(0x08083070,0x08083074,0x080DD428,0x080DD56C),'exact consumer literal sites')
 ss,cs,es,ts=[roots[k]for k in('script_slot','callnative_slot','end_slot','template_slot')]
 need(ss['address']==st['value']+8*4 and cs['address']==dispatch['value']+3*4 and cs['value']==0x080830B5 and es['address']==dispatch['value']+4*4 and es['value']==0x080830C9 and ts['address']==tt['value']+7*4,'finite source script/dispatch/template selector chain')
 need(roots['creator_sprite_table_literal']['address']==0x08006BA8 and roots['init_sprite_table_literal']['address']==0x08006CD4 and roots['creator_sprite_table_literal']['value']==roots['init_sprite_table_literal']['value']==0x020205B8 and roots['init_tag_limit_literal']['address']==0x08006CD8 and roots['init_tag_limit_literal']['value']==0xFFFF0000,'same current Sprite table and frame-based tag discriminator')
 script=review['script'];d.signed(raw,script)
 need(script['address']==ss['value']and script['size']==6 and script['effect_id']==8 and chunk(raw,script['address'],1)[0]==3 and d.u32(raw,script['address']+1)==script['native']==0x080DD3B9 and chunk(raw,script['address']+5,1)[0]==4,'whole callnative followed by end, no untyped operands')
 # Explicit argument selection instructions: source load table literal then table[7].
 need(int.from_bytes(chunk(raw,0x080DD3C8,2),'little')&0xF800==0x4800 and int.from_bytes(chunk(raw,0x080DD3CA,2),'little')==0x69C0,'actual template table literal and +28 field read')
 need(chunk(raw,0x081C7AC8,2)==bytes([0,71])and chunk(raw,0x081C7AD0,2)==bytes([16,71]),'exact native r0 and dispatch r2 interwork')
 template=review['template'];d.signed(raw,template)
 need(template['address']==ts['value']and template['size']==24 and template['object_id']==7 and int.from_bytes(chunk(raw,template['address'],2),'little')==65535 and d.u32(raw,template['address']+20)==template['callback']==0x080DD4E1,'selected frame-based template and actual callback')
 at,frames,dirs=review['animation_table'],review['frame_table'],review['direction_table'];d.signed(raw,at);d.signed(raw,frames);d.signed(raw,dirs)
 need(d.u32(raw,template['address']+8)==template['anims']==at['address']and at['size']==16 and d.u32(raw,template['address']+12)==template['images']==frames['address']and frames['size']==48,'whole source4-animation/6-frame arrays')
 need(dirs['address']==dt['value']and dirs['size']==5 and chunk(raw,dirs['address'],5)==bytes([0,0,1,2,3]),'actual movement direction to source animation mapping')
 need(len(review['animations'])==4,'all source SurfBlob animations')
 for i,row in enumerate(review['animations']):
  slot,anim=row['slot'],row['animation'];d.signed(raw,slot);d.signed(raw,anim)
  name=['sSurfBlobAnim_FaceSouth','sSurfBlobAnim_FaceNorth','sSurfBlobAnim_FaceWest','sSurfBlobAnim_FaceEast'][i]
  need(row['index']==i and row['source']==name and slot['address']==at['address']+4*i and slot['size']==4 and d.u32(raw,slot['address'])==slot['value']==anim['address'],'bounded actual source animation slot')
  body=re.search(r'static const union AnimCmd '+name+r'\[\]\s*=\s*\{(.*?)\};',src,re.S);need(body is not None,'fixed source SurfBlob sequence')
  commands=re.findall(r'ANIMCMD_FRAME\((\d+),\s*(\d+)([^)]*)\)',body[1]);need(len(commands)==2 and 'ANIMCMD_JUMP(0)'in body[1],'source exact two-frame loop')
  words=[]
  for image,duration,flags in commands:words.extend((int(image),int(duration)+(64 if '.hFlip = TRUE'in flags else 0)))
  words.extend((65534,0));expected=struct.pack('<6H',*words)
  need(anim['size']==12 and chunk(raw,anim['address'],12)==expected,'entire source-serialized frame/loop commands')
 selected=review['animations'][2];frame=review['frame'];asset=review['asset'];hit=review['hit']
 for w in(frame,asset,hit):d.signed(raw,w)
 need(review['source_frame_tiles']==[2,8]and review['bits_per_pixel']==4 and frame['index']==4 and frame['size']==8 and frame['address']==frames['address']+4*8 and struct.unpack('<IH',chunk(raw,frame['address'],6))==(asset['address'],asset['size'])and asset['size']==2*8*32==512,'whole exact fourth-index source frame payload')
 need(hit['address']==0x0835B4FE and next(h for h in inherited['hits']if h['address']==hit['address'])==hit and not hit['accepted']and not hit['owner_candidates']and d.contains(asset['address'],asset['address']+512,hit['address'],4),'only exact inherited unknown inside pixel payload')
 evidence=dict(asset=asset,width=16,height=64,bits_per_pixel=4,root_verified=True,frame_index=4,frame_record=frame,field_effect_id=8,object_template_id=7,animation_index=2,animation=selected['animation'],animation_source=selected['source'],source_extent=dict(command_count=3,command_stride=4,table_count=4,table_stride=4,frame_count=6,frame_stride=8),actual_screen_rendered=False,full_story_reachability_claimed=False)
 return[d.TypedRegion(asset['address'],asset['address']+512,'rooted_field_effect_sprite_4bpp_frame',evidence)],dict(status='PASS_FINITE_SOURCE_ROOTED_SURF_FRAME',count=1,asset=asset,actual_screen_rendered=False,full_story_reachability_claimed=False)

def regions(raw,latest,inherited,review,sources,root):
 need(identity(raw)==latest['candidate']==inherited['candidate']==CANDIDATE,'current whole candidate mandatory')
 return _regions(raw,inherited,review,sources,root)
