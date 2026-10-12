/* Save14分離fixture。ROM native CreateMon/SetMonDataで作成し、wild開始後はキーと読取のみ。
 * 80-byte BoxPokemonと100-byte party imageは区別し、後者の原本は別途不変保存する。 */
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/savedata.h>
#include <mgba-util/vfs.h>
#include "pr16_story_acceleration_vectors.h"
static color_t sa_video[240*160];
static unsigned sa_frames,sa_inputs,sa_guarded,sa_chosen,sa_damage,sa_used,sa_started;
static uint8_t sa_original[200];
static unsigned sa_pc[2],sa_slots[2],sa_evo_frame,sa_cancel_frame,sa_national;
_Noreturn static void sa_die(const char*s){fprintf(stderr,"acceleration: %s\n",s);exit(1);}
static void sa_need(bool v,const char*s){if(!v)sa_die(s);}
#define DENY(n,t) static void n(struct mCore*c,uint32_t a,t v){(void)c;(void)a;(void)v;sa_die("host write after barrier");}
DENY(sa_w8,uint8_t) DENY(sa_w16,uint16_t) DENY(sa_w32,uint32_t)
#define RAW(n,t) static void n(struct mCore*c,uint32_t a,int s,t v){(void)c;(void)a;(void)s;(void)v;sa_die("host write after barrier");}
RAW(sa_r8,uint8_t) RAW(sa_r16,uint16_t) RAW(sa_r32,uint32_t)
static bool sa_reg(struct mCore*c,const char*n,const void*v){(void)c;(void)n;(void)v;sa_die("host write after barrier");}
static void sa_guard(struct mCore*c){c->busWrite8=sa_w8;c->busWrite16=sa_w16;c->busWrite32=sa_w32;c->rawWrite8=sa_r8;c->rawWrite16=sa_r16;c->rawWrite32=sa_r32;c->writeRegister=sa_reg;++sa_guarded;}
static void sa_guard_check(const char*n){struct mCore c={0};uint32_t v=0;sa_guard(&c);if(!strcmp(n,"bus8"))c.busWrite8(&c,0,0);else if(!strcmp(n,"bus16"))c.busWrite16(&c,0,0);else if(!strcmp(n,"bus32"))c.busWrite32(&c,0,0);else if(!strcmp(n,"raw8"))c.rawWrite8(&c,0,0,0);else if(!strcmp(n,"raw16"))c.rawWrite16(&c,0,0,0);else if(!strcmp(n,"raw32"))c.rawWrite32(&c,0,0,0);else if(!strcmp(n,"register"))c.writeRegister(&c,"pc",&v);exit(2);}
static void sa_bytes(struct mCore*c,unsigned at,unsigned n,uint8_t*out){for(unsigned i=0;i<n;++i)out[i]=read8(c,at+i);}
static void sa_file(const char*name,const uint8_t*b,unsigned n){FILE*f=fopen(name,"wb");sa_need(f!=NULL,"output file");sa_need(fwrite(b,1,n,f)==n&&!fclose(f),"output bytes");}
static void sa_ram(struct mCore*c,const char*name){uint8_t*b=malloc(0x48000);sa_need(b!=NULL,"RAM allocation");sa_bytes(c,0x02000000,0x40000,b);sa_bytes(c,0x03000000,0x8000,b+0x40000);sa_file(name,b,0x48000);free(b);}
static void sa_screen(const char*name){FILE*f=fopen(name,"wb");sa_need(f!=NULL,"screen file");fprintf(f,"P6\n240 160\n255\n");for(unsigned i=0;i<240*160;++i){uint32_t p=sa_video[i];uint8_t b[3]={p,p>>8,p>>16};sa_need(fwrite(b,1,3,f)==3,"screen pixels");}sa_need(!fclose(f),"screen close");}
static bool sa_field(struct mCore*c){unsigned q=read8(c,0x0203AD72),p=read8(c,0x03005ED8);return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==0x08055E75&&!read8(c,0x03000F9C)&&((q==0&&p==0)||(q==1&&p==2));}
static void sa_frame(struct mCore*c,unsigned key){sa_need(++sa_frames<=150000,"frame budget");c->setKeys(c,key);c->runFrame(c);if(sa_started){
 unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
 if(cb==0x080CF869&&!sa_evo_frame){sa_evo_frame=sa_frames;sa_screen("evolution-start.ppm");}
 if(cb==0x080CF869&&!sa_cancel_frame)for(unsigned i=0;i<16;++i){unsigned task=QOL_TASKS+40*i;
  if(read8(c,task+4)&&read16(c,task+10)==sa_axew&&read16(c,task+12)==sa_fraxure&&read16(c,task+8)==17&&read16(c,task+26)==1){
   sa_cancel_frame=sa_frames;sa_screen("evolution-autocancel.ppm");
   fprintf(stderr,"AUTOCANCEL_TASK frame=%u task=%u state=%u from=%u target=%u stopped=%u\n",sa_frames,i,read16(c,task+8),read16(c,task+10),read16(c,task+12),read16(c,task+26));}}
 }if(sa_started){static unsigned prevcb=0,prevlv=0;unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),lv=read8(c,QOL_PLAYER_PARTY+84);if(cb!=prevcb||lv!=prevlv){fprintf(stderr,"NATIVE_TRANSITION frame=%u cb=%08x level=%u species=%u\n",sa_frames,cb,lv,read16(c,QOL_PLAYER_PARTY+32));prevcb=cb;prevlv=lv;}}if(sa_started&&read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){
 unsigned chosen=read16(c,BATTLE_CORE_CHOSEN_MOVES),hp=read16(c,ADDR_BATTLE_MONS+BATTLE_MON_SIZE+BATTLE_CORE_MON_HP),pp=read8(c,ADDR_BATTLE_MONS+BATTLE_MON_PP_OFFSET);
 if(chosen==sa_expected_move&&!sa_chosen)sa_chosen=sa_frames;
 if(sa_chosen&&pp<sa_initial_pp&&!sa_used)sa_used=sa_frames;
 if(sa_chosen&&hp<sa_enemy_hp&&!sa_damage)sa_damage=sa_frames;
 }}
static void sa_wait(struct mCore*c,unsigned n){while(n--)sa_frame(c,0);}
static void sa_press(struct mCore*c,unsigned key,unsigned n){++sa_inputs;sa_frame(c,key);sa_frame(c,key);sa_wait(c,n);}
static struct mCore*sa_open(const char*rom,const char*save){
 static struct mRTCSource rtc={.sample=NULL,.unixTime=fixed_unix_time,.serialize=NULL,.deserialize=NULL};
 struct mCore*c=mCoreFind(rom);sa_need(c&&c->init(c),"core init");sa_need(mCoreLoadFile(c,rom)&&mCoreLoadSaveFile(c,save,false),"ROM/save attach");
 mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");mCoreSetRTC(c,&rtc);c->setVideoBuffer(c,sa_video,240);c->reset(c);
 struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;sa_need(s->type==SAVEDATA_FLASH1M&&s->data,"Flash1M");
 uint8_t*b=malloc(0x20000);sa_need(b!=NULL,"flash snapshot");memcpy(b,s->data,0x20000);uintptr_t bank=s->currentBank-s->data;GBASavedataRTCWrite(s);s->currentBank=s->data+bank;sa_need(!memcmp(b,s->data,0x20000)&&s->vf->size(s->vf)==0x20010,"RTC keeps all Flash");free(b);
 return c;
}
static void sa_continue(struct mCore*c){sa_wait(c,600);for(unsigned k=0;k<100;++k){sa_press(c,k==0?8:(k>12?2:1),120);if(sa_field(c)){sa_wait(c,180);if(sa_field(c))return;}}sa_screen("continue-failure.ppm");sa_die("fresh Continue timeout");}
static void sa_save(struct mCore*c){sa_need(sa_field(c),"save idle field");unsigned before=read32(c,0x030053E0);sa_press(c,8,120);sa_need(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"Start input");unsigned count=read8(c,QOL_START_MENU_COUNT),cur=read8(c,QOL_START_MENU_CURSOR),target=99;sa_need(count>0&&count<=10&&cur<count,"Start bounds");for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==4)target=i;sa_need(target<count,"Save option");while(cur!=target){sa_press(c,128,30);cur=(cur+1)%count;}sa_press(c,1,120);bool seen=false;for(unsigned i=0;i<32;++i){if(read32(c,QOL_START_MENU_CALLBACK)==0x0806EDB9)seen=true;if(seen&&read32(c,0x030053E0)==before+1&&sa_field(c)){sa_wait(c,0+180);return;}sa_press(c,1,180);}sa_screen("save-failure.ppm");sa_die("ordinary Save timeout");}
static void sa_create(struct mCore*c,unsigned at,unsigned species,unsigned level,unsigned nature){
 struct CpuState cpu=capture_cpu_state(c);unsigned pid=0x24680000U;pid+=((nature+25)-pid%25)%25;
 uint32_t args[4]={1,pid,0,0};struct HostCallStack stack;begin_host_call_stack(c,&stack,args,4);
 call_rom_args(c,BATTLE_CORE_CREATE_MON,at,species,level,31);sa_need(restore_host_call_stack(c,&stack),"CreateMon stack");restore_cpu_state(c,&cpu);
 sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,11,0,0)==species&&call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,56,0,0)==level,"native CreateMon readback");
}
static void sa_mon(struct mCore*c,unsigned index,unsigned species,unsigned level,unsigned nature,const unsigned moves[4],unsigned item,unsigned abilityslot,bool special){
 unsigned at=QOL_PLAYER_PARTY+100*index;sa_create(c,at,species,level,nature);
 for(unsigned i=0;i<6;++i)set_mon_data_u32(c,at,26+i,(i==0?4:((i==3||i==(special?4:1))?252:0)));
 set_mon_data_u32(c,at,46,abilityslot);set_mon_data_u32(c,at,12,item);
 for(unsigned i=0;i<4;++i){set_mon_data_u32(c,at,13+i,moves[i]);set_mon_data_u32(c,at,17+i,moves[i]?read8(c,sa_move_table+12*moves[i]+4):0);}
 set_mon_data_u32(c,at,21,0);call_preserving(c,0x0803DBE9,at,0,0,0);
 unsigned sb2=read32(c,QOL_SAVE_BLOCK2_SLOT);unsigned ot=0;for(unsigned b=0;b<4;++b)ot|=(unsigned)read8(c,sb2+10+b)<<(8*b);sa_need(read32(c,at+4)==ot,"self OT 32-bit ID");
 for(unsigned j=0;j<7;++j)sa_need(read8(c,at+20+j)==read8(c,sb2+j),"self OT name bytes");
 sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,49,0,0)==read8(c,sb2+8),"self OT gender");
 sa_need(read8(c,at+18)==sa_original[18],"self OT language");
 sa_need(read16(c,at+0x20)==species&&read8(c,at+84)==level,"bound plaintext native mon ABI");
 sa_need(read32(c,at)%25==nature,"native nature");
 for(unsigned j=0;j<6;++j){sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,39+j,0,0)==31,"31 IV native readback");sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,26+j,0,0)==(j==0?4:((j==3||j==(special?4:1))?252:0)),"EV native readback");}
 unsigned stats=read32(c,0x080001BC);unsigned ability=read16(c,stats+32*species+(abilityslot?26:22));
 sa_need(call_preserving(c,0x090DA23D,at,0,0,0)==ability,"native chosen ability");
 for(unsigned j=0;j<4;++j)sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,at,13+j,0,0)==moves[j],"native move readback");
}
static void sa_box(struct mCore*c){sa_bytes(c,QOL_PLAYER_PARTY,200,sa_original);sa_file("original-party-100byte-images.bin",sa_original,200);
 for(unsigned n=0;n<2;++n){unsigned slot=0;while(slot<420&&call_preserving(c,QOL_GET_BOX_MON_DATA_AT,slot/30,slot%30,11,0))++slot;sa_need(slot<420,"empty native PC slot");sa_slots[n]=slot;call_preserving(c,QOL_SET_BOX_MON,slot/30,slot%30,QOL_PLAYER_PARTY+100*n,0);sa_need(call_preserving(c,QOL_GET_BOX_MON_DATA_AT,slot/30,slot%30,11,0)==read16(c,QOL_PLAYER_PARTY+100*n+32),"boxed original species");
 unsigned found=0;for(unsigned at=0x02000000;at<=0x02040000-80;++at){if(at>=QOL_PLAYER_PARTY&&at<QOL_PLAYER_PARTY+600)continue;unsigned saved=read32(c,QOL_SAVE_BLOCK1_SLOT);if(at>=saved&&at<saved+0x3d88)continue;if(read8(c,at)!=sa_original[100*n])continue;bool same=true;for(unsigned i=1;i<80&&same;++i)same=read8(c,at+i)==sa_original[100*n+i];if(same){sa_pc[n]=at;++found;}}
 if(found!=1){sa_ram(c,"pc-failure.ram");fprintf(stderr,"BOX_IDENTITY n=%u matches=%u slot=%u original=",n,found,slot);for(unsigned z=0;z<100;++z)fprintf(stderr,"%02x",sa_original[100*n+z]);fputc('\n',stderr);}sa_need(found==1,"one unchanged 80-byte native boxed identity");}
}
static void sa_pc_check(struct mCore*c){
 /* Battle/ContinueのSaveBlock再配置を固定RAM番地の破壊と混同しない。全80byteを再同定する。 */
 unsigned saved=read32(c,QOL_SAVE_BLOCK1_SLOT);
 for(unsigned n=0;n<2;++n){unsigned found=0;
  for(unsigned at=0x02000000;at<=0x02040000-80;++at){
   if((at>=QOL_PLAYER_PARTY&&at<QOL_PLAYER_PARTY+600)||(at>=saved&&at<saved+0x3d88))continue;
   if(read8(c,at)!=sa_original[100*n])continue;
   bool same=true;for(unsigned i=1;i<80&&same;++i)same=read8(c,at+i)==sa_original[100*n+i];
   if(same){sa_pc[n]=at;++found;}}
  if(found!=1)sa_ram(c,"pc-preservation-failure.ram");
  sa_need(found==1,"original PC bytes remain uniquely unchanged");
 }
 fprintf(stderr,"PC_PRESERVED frame=%u addresses=%08x,%08x slots=%u,%u\n",sa_frames,sa_pc[0],sa_pc[1],sa_slots[0],sa_slots[1]);
}
static void sa_fixture(struct mCore*c,bool progression){
 sa_need(read8(c,QOL_PLAYER_PARTY_COUNT)==2&&read32(c,0x030053E0)==14,"Save14 source state");
 unsigned s1=read32(c,QOL_SAVE_BLOCK1_SLOT),s2=read32(c,QOL_SAVE_BLOCK2_SLOT);sa_need(s1>=0x02000000&&s1+0x3d88<=0x02040000&&s2>=0x02000000&&s2+0xf24<=0x02040000,"save blocks");
 uint8_t before1[0x3d88],before2[0xf24];sa_bytes(c,s1,sizeof(before1),before1);sa_bytes(c,s2,sizeof(before2),before2);
 sa_national=call_preserving(c,0x0806DA51,0,0,0,0);sa_need(sa_national==0,"Save14 national dex must not be injected");
 sa_ram(c,"fixture-before.ram");sa_box(c);clear_parties(c);
 if(progression){
   /* 閾値のnative readerを実際のCreateMonで照合してからEXPを1未満へ設定する。 */
   sa_create(c,QOL_PLAYER_PARTY,sa_axew,sa_evolution_level,3);sa_need(call_preserving(c,BATTLE_CORE_GET_MON_DATA,QOL_PLAYER_PARTY,25,0,0)==sa_threshold,"native growth threshold");fprintf(stderr,"EVOLUTION_PREFLIGHT level=%u target=%u\n",read8(c,QOL_PLAYER_PARTY+84),call_preserving(c,0x090FB775,QOL_PLAYER_PARTY,0,0,0));
   sa_mon(c,0,sa_axew,sa_evolution_level-1,3,sa_growth_moves,0,1,false);
   set_mon_data_u32(c,QOL_PLAYER_PARTY,25,sa_threshold-1);call_preserving(c,0x0803DBE9,QOL_PLAYER_PARTY,0,0,0);write8(c,QOL_PLAYER_PARTY_COUNT,1);
 }else{
   for(unsigned i=0;i<4;++i)sa_mon(c,i,sa_species[i],100,i==0?15:(i==1?3:0),sa_story_moves[i],sa_held[i],i==1?1:0,i==0);
   write8(c,QOL_PLAYER_PARTY_COUNT,4);
 }
 create_mon(c,QOL_ENEMY_PARTY,sa_caterpie,2);set_mon_data_u32(c,QOL_ENEMY_PARTY,13,sa_splash);set_mon_data_u32(c,QOL_ENEMY_PARTY,17,40);for(unsigned i=1;i<4;++i){set_mon_data_u32(c,QOL_ENEMY_PARTY,13+i,0);set_mon_data_u32(c,QOL_ENEMY_PARTY,17+i,0);}write8(c,BATTLE_CORE_ENEMY_PARTY_COUNT,1);
 sa_enemy_hp=read16(c,QOL_ENEMY_PARTY+86);sa_expected_move=progression?sa_growth_moves[0]:sa_story_moves[0][0];sa_initial_pp=read8(c,QOL_PLAYER_PARTY+52);
 uint8_t after1[0x3d88],after2[0xf24];sa_bytes(c,s1,sizeof(after1),after1);sa_bytes(c,s2,sizeof(after2),after2);
 sa_need(!memcmp(before1,after1,sizeof(before1))&&!memcmp(before2,after2,sizeof(before2)),"fixture changed a story/save-block byte");sa_pc_check(c);sa_ram(c,"fixture-after.ram");
 fprintf(stderr,"FIXTURE save1=%08x save2=%08x pc0=%08x pc1=%08x slots=%u,%u move=%u pp=%u enemyhp=%u\n",s1,s2,sa_pc[0],sa_pc[1],sa_slots[0],sa_slots[1],sa_expected_move,sa_initial_pp,sa_enemy_hp);
}
static bool sa_action(struct mCore*c){unsigned ctrl=read32(c,0x03005020);return read32(c,0x03004FC4)==0x08013861&&(read32(c,0x02023B28)&1)&&read8(c,0x02022B24)==0x12&&(ctrl==0x0802DC15||ctrl==0x09118B85);}
static void sa_cursor(struct mCore*c,unsigned at,unsigned target){for(unsigned i=0;i<8;++i){unsigned cur=read8(c,at);sa_need(cur<4,"menu cursor bounds");if(cur==target)return;sa_press(c,(cur&1)!=(target&1)?((target&1)?16:32):((target&2)?128:64),12);}sa_die("menu cursor timeout");}
static void sa_battle(struct mCore*c,bool progression){
 sa_started=sa_frames;unsigned initial_xp=read32(c,QOL_PLAYER_PARTY+36);unsigned ready=0;
 for(unsigned i=0;i<16000&&ready<12;++i){if(sa_action(c))++ready;else ready=0;sa_frame(c,i%60==0?1:0);}sa_need(ready==12,"ordinary action menu");sa_screen("action.ppm");sa_cursor(c,BATTLE_CORE_ACTION_SELECTION_CURSOR,0);
 bool selected=false;for(unsigned i=0;i<1200;++i){if(read8(c,0x02022B24)==0x14&&(read32(c,0x02023B28)&1)){sa_cursor(c,BATTLE_CORE_MOVE_SELECTION_CURSOR,0);sa_screen("move.ppm");sa_press(c,1,2);selected=true;break;}sa_frame(c,sa_action(c)&&i%30==0?1:0);}sa_need(selected,"ordinary move selection");
 for(unsigned i=0;i<40000;++i){if(sa_chosen&&sa_field(c)){sa_wait(c,180);if(sa_field(c))break;}sa_frame(c,i%60==0?1:0);if(i==39999){sa_screen("battle-failure.ppm");sa_die("battle return timeout");}}
 sa_screen("returned.ppm");sa_need(sa_chosen&&sa_used&&sa_damage&&read8(c,BATTLE_CORE_BATTLE_OUTCOME)==1,"normal victory and move effect");
 sa_ram(c,"returned.ram");fprintf(stderr,"PROGRESSION_READBACK xp_before=%u xp_after=%u species=%u level=%u target=%u targetlevel=%u outcome=%u\n",initial_xp,read32(c,QOL_PLAYER_PARTY+36),read16(c,QOL_PLAYER_PARTY+32),read8(c,QOL_PLAYER_PARTY+84),sa_fraxure,sa_evolution_level,read8(c,BATTLE_CORE_BATTLE_OUTCOME));
 if(progression&&read16(c,QOL_PLAYER_PARTY+32)!=sa_fraxure){
  sa_need(sa_national==0&&sa_fraxure>151&&sa_evo_frame&&sa_cancel_frame&&sa_cancel_frame>sa_evo_frame&&read16(c,QOL_PLAYER_PARTY+32)==sa_axew&&read8(c,QOL_PLAYER_PARTY+84)==sa_evolution_level&&read32(c,QOL_PLAYER_PARTY+36)==sa_threshold,"bounded unmodified national-dex gate reproduction");
  sa_pc_check(c);
  printf("{\"status\":\"BLOCKED_NATIONAL_DEX_EVOLUTION_GUARD\",\"lane\":\"progression\",\"xp_before\":%u,\"xp_after\":%u,\"level\":%u,\"species\":%u,\"target\":%u,\"evolution_frame\":%u,\"autocancel_frame\":%u,\"returned_frame\":%u,\"national_dex\":0,\"post_battle_host_writes\":0,\"evolution_accepted\":false,\"release_ready\":false}\n",initial_xp,read32(c,QOL_PLAYER_PARTY+36),sa_evolution_level,sa_axew,sa_fraxure,sa_evo_frame,sa_cancel_frame,sa_frames);
  qol_close(c);exit(3);
 }
 if(progression)sa_need(read16(c,QOL_PLAYER_PARTY+32)==sa_fraxure&&read8(c,QOL_PLAYER_PARTY+84)==sa_evolution_level&&read32(c,QOL_PLAYER_PARTY+36)>initial_xp,"native EXP evolution");
 else sa_need(read16(c,QOL_PLAYER_PARTY+32)==sa_species[0]&&read8(c,QOL_PLAYER_PARTY+84)==100&&read32(c,QOL_PLAYER_PARTY+36)==initial_xp,"Lv100 no overflow");
 fprintf(stderr,"BATTLE start=%u chosen=%u used=%u damage=%u returned=%u xp_before=%u xp_after=%u species=%u level=%u\n",sa_started,sa_chosen,sa_used,sa_damage,sa_frames,initial_xp,read32(c,QOL_PLAYER_PARTY+36),read16(c,QOL_PLAYER_PARTY+32),read8(c,QOL_PLAYER_PARTY+84));
}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--guard-check"))sa_guard_check(argv[2]);
 sa_need(argc==4&&(!strcmp(argv[3],"story-fast")||!strcmp(argv[3],"progression")||!strcmp(argv[3],"prepare-progression")),"closed invocation");bool preparation=!strcmp(argv[3],"prepare-progression"),progression=preparation||!strcmp(argv[3],"progression");
 char sha[65];sha256_file(argv[1],sha);sa_need(!strcmp(sha,SA_ROM),"fixed candidate SHA");sha256_file(argv[2],sha);sa_need(!strcmp(sha,SA_SAVE),"fixed Save14 copy SHA");
 struct mLogger logger={.log=qol_log};mLogSetDefaultLogger(&logger);struct mCore*c=sa_open(argv[1],argv[2]);struct mCore api=*c;sa_guard(c);sa_continue(c);
 /* 初回Continue後にのみfixture書込みを解禁する。wild開始後は復元しない。 */
 c->busWrite8=api.busWrite8;c->busWrite16=api.busWrite16;c->busWrite32=api.busWrite32;c->rawWrite8=api.rawWrite8;c->rawWrite16=api.rawWrite16;c->rawWrite32=api.rawWrite32;c->writeRegister=api.writeRegister;
 sa_fixture(c,progression);sa_screen("fixture.ppm");
 if(!preparation){struct CallObservation start=call_bounded(c,BATTLE_CORE_START_WILD,0,0,0,0);sa_need(start.instructions>0,"native wild setup");}sa_guard(c);if(!preparation)sa_battle(c,progression);sa_pc_check(c);sa_save(c);sa_screen("saved.ppm");
 uint8_t party[600],continued[600];sa_bytes(c,QOL_PLAYER_PARTY,600,party);sa_file("saved-party.bin",party,600);sa_need(read32(c,0x030053E0)==15,"one ordinary Save");sa_ram(c,"saved.ram");qol_close(c);sha256_file(argv[2],sha);char saved_sha[65];memcpy(saved_sha,sha,65);
 c=sa_open(argv[1],argv[2]);sa_guard(c);sa_continue(c);sa_bytes(c,QOL_PLAYER_PARTY,600,continued);sa_need(!memcmp(party,continued,600)&&read32(c,0x030053E0)==15,"fresh Continue full party/counter");sa_pc_check(c);sa_screen("continued.ppm");sa_ram(c,"continued.ram");qol_close(c);sha256_file(argv[2],sha);sa_need(!strcmp(sha,saved_sha),"fresh Continue preserves full Save/RTC file");sa_need(!log_problem_count,"mGBA warnings/errors");
 printf("{\"status\":\"%s\",\"lane\":\"%s\",\"frames\":%u,\"inputs\":%u,\"fresh_cores\":2,\"guard_installations\":%u,\"ordinary_saves\":1,\"save_counter\":15,\"save_sha256\":\"%s\",\"accepted_case_reruns\":0,\"rom_changes\":0,\"release_ready\":false}\n",preparation?"PASS_PREBATTLE_PROGRESSION_COPY":"PASS_SPLIT_SMOKE",argv[3],sa_frames,sa_inputs,sa_guarded,sha);return 0;
}
