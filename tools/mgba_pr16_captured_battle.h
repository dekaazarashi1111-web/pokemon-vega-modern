/* Included after the immutable natural-capture helpers. No host-write API. */
struct NBProof {unsigned encounter,menu,switched,spent,field,saved,reloaded,steps,species,level,ability,move,pp_before,pp_after,party_attack,outcome;};
static struct NBProof nb_run(struct mCore*c,const struct NCase*v){
 struct NBProof p={0};unsigned before_steps=n_steps;
 for(unsigned i=0;i<1024U;++i){
  unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);
  a_require(read8(c,s+4U)==1U && read8(c,s+5U)==v->map,"post-capture walk left map");
  bool start=x==v->x && y==v->y,end=x==v->ex && y==v->ey;a_require(start || end,"post-capture walk left audited pair");
  n_step(c,start?(v->ex>v->x?QOL_KEY_RIGHT:QOL_KEY_DOWN):(v->ex>v->x?QOL_KEY_LEFT:QOL_KEY_UP));
  if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){p.encounter=b_frames;break;}
 }
 a_require(p.encounter,"post-capture natural encounter absent");p.steps=n_steps-before_steps;
 p.species=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE);p.level=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_LEVEL);
 a_require(!(read32(c,ADDR_BATTLE_TYPE_FLAGS)&8U),"post-capture encounter is trainer");
 n_cursor(c,2U);b_press(c,QOL_KEY_A,180U);
 for(unsigned i=0;i<1800U && read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_PARTY;++i)b_frame(c,0);
 a_require(read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_PARTY,"physical switch did not open party menu");p.menu=b_frames;g_shot("captured-party-menu");
 a_require(read8(c,BATTLE_CORE_SELECTED_PARTY_MON)==0U,"physical party menu starting selection differs");
 b_press(c,QOL_KEY_DOWN,60U);a_require(read8(c,BATTLE_CORE_SELECTED_PARTY_MON)==1U,"physical party menu did not select captured slot");
 b_press(c,QOL_KEY_A,80U);g_shot("captured-shift-choice");b_press(c,QOL_KEY_A,180U);n_wait_action(c);
 a_require(read16(c,ADDR_BATTLER_PARTY_INDEXES)==1U && read16(c,ADDR_BATTLE_MONS)==N_TARGET && read32(c,QOL_PLAYER_PARTY+100U)==n_pid,"switched battler is not captured individual");
 p.switched=b_frames;p.ability=read16(c,ADDR_BATTLE_MONS+0x38U);a_require(p.ability==26U,"natural base ability not assigned on sendout");g_shot("captured-sent-out");
 /* Bind all four native move/PP slots to this actual caught party record. */
 unsigned matches=0;
 for(unsigned part=0;part<4U;++part){bool match=true;unsigned a=QOL_PLAYER_PARTY+100U+32U+part*12U;
  for(unsigned k=0;k<4U;++k)if(read16(c,a+2U*k)!=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET+2U*k) || read8(c,a+8U+k)!=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET+k))match=false;
  if(match){++matches;p.party_attack=32U+part*12U;}
 }
 a_require(matches==1U,"caught move/PP slots not identical to native battler");
 p.move=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_MOVES_OFFSET);p.pp_before=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET);a_require(p.move && p.pp_before,"caught first native move unavailable");
 n_cursor(c,0U);b_press(c,QOL_KEY_A,60U);
 a_require(read8(c,0x02022B24U)==0x14U && (read32(c,0x02023B28U)&1U),"native move menu absent");
 for(unsigned k=0;k<6U;++k){unsigned at=read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR);a_require(at<4U,"native move cursor invalid");if(!at)break;b_press(c,at&1U?QOL_KEY_LEFT:QOL_KEY_UP,12U);}
 a_require(read8(c,BATTLE_CORE_MOVE_SELECTION_CURSOR)==0U,"physical move cursor not first slot");b_press(c,QOL_KEY_A,2U);
 for(unsigned f=0;f<18000U;++f){
  unsigned pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET);
  if(pp<p.pp_before && !p.spent){p.spent=b_frames;p.pp_after=pp;}
  if(p.spent && n_action(c))break;
  if(b_field(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){p.outcome=read8(c,BATTLE_CORE_BATTLE_OUTCOME);break;}
  b_frame(c,f%60U==0U?QOL_KEY_B:0);
 }
 a_require(p.spent && p.pp_before>p.pp_after && p.pp_before-p.pp_after<=2U,"captured battler did not spend native move PP");g_shot("captured-native-turn");
 if(read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){a_require(n_action(c),"captured turn did not return to action controller");n_cursor(c,3U);b_press(c,QOL_KEY_A,60U);n_return(c,false);p.outcome=n_outcome;}
 a_require(b_field(c) && !read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER) && (p.outcome==1U || p.outcome==4U),"captured battle did not end normally");p.field=b_frames;
 a_require(read32(c,QOL_PLAYER_PARTY+100U)==n_pid && read16(c,QOL_PLAYER_PARTY+100U+32U)==N_TARGET && read8(c,QOL_PLAYER_PARTY+100U+p.party_attack+8U)==p.pp_after,"native field return lost captured identity or PP");g_shot("captured-battle-field");
 a_require(b_save(c),"captured battle normal save failed");p.saved=b_frames;return p;
}
