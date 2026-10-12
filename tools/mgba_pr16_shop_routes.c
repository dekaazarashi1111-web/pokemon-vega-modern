/* Actual Factory NPC -> paged Mega Stone shop -> native transaction -> Save.
 * Only the initial map, ring, BP and claim state are fixtures. After the
 * observation barrier there are no host writes or injected ROM calls. */
#include "pr16_shop_breeding_helpers.c"
#define G_SHA "635fd890a8d1071560d3cb56c9c663425f7c988119ce098dedad6bf6554f973e"
#define G_SCOPE "PR16_PHYSICAL_MEGA_SHOP_ACQUISITION_SAVE"
#define G_STATE 0x0203ED40U
#define G_CURSOR 0x0203AD5EU
#define G_ITEMS 2048U
struct GCase {const char *name;unsigned item,action;};
static const struct GCase g_cases[]={
 {"feraligatr",1016,0},{"eelektross",1012,0},{"pyroar",1031,0},
 {"meganium",1029,0},{"excadrill",1014,0},{"scovillain",1035,0},
 {"cancel-first",1012,1},{"cancel-page",1035,2},
 {"insufficient-bp",1012,3},{"missing-ring",1012,4}
};
static const char *g_prefix;
static void g_shot(const char *suffix){
 char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",g_prefix,suffix);
 a_require(n>0 && n<(int)sizeof(path),"shop screenshot path too long");
 FILE *f=fopen(path,"wb");a_require(f!=NULL,"shop screenshot open failed");
 a_require(fprintf(f,"P6\n240 160\n255\n")>0,"shop screenshot header failed");
 for(unsigned i=0;i<240U*160U;++i){uint32_t p=(uint32_t)b_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};a_require(fwrite(rgb,1,3,f)==3,"shop screenshot write failed");}
 a_require(!fclose(f),"shop screenshot close failed");
}
static void g_state(struct mCore *c,const char *label){
 b_state(c,label);fprintf(stderr,"SHOP result=%u selected=%u eligible=%u page=%u window=%u cursor=%u bp=%u save=%u\n",
  read16(c,G_STATE+90U),read16(c,G_STATE+92U),read8(c,G_STATE+94U),read8(c,G_STATE+95U),
  read8(c,G_STATE+96U),read8(c,G_CURSOR),read16(c,QOL_LEDGER+0x392U),read32(c,P03_SAVE_COUNTER));
}
static void g_inventory(struct mCore *c,uint32_t counts[G_ITEMS]){
 static const unsigned capacities[]={42,30,13,58,43};memset(counts,0,G_ITEMS*sizeof(*counts));
 unsigned s2=read32(c,QOL_SAVE_BLOCK2_SLOT);a_require(p02s_ewram_pointer(s2),"shop save2 pointer invalid");
 unsigned key=read16(c,s2+0xF20U);
 for(unsigned p=0;p<5U;++p){unsigned d=0x020397D8U+8U*p,slots=read32(c,d),cap=read8(c,d+4U);
  a_require(cap==capacities[p] && p02s_ewram_pointer(slots) && slots+4U*cap<=0x02040000U,"shop bag descriptor differs");
  for(unsigned k=0;k<cap;++k){unsigned id=read16(c,slots+4U*k),quantity=read16(c,slots+4U*k+2U)^key;
   a_require(id<G_ITEMS,"shop item ID outside inventory bound");if(id){a_require(quantity>0U && quantity<=999U,"shop bag quantity invalid");counts[id]+=quantity;}}
 }
}
static void g_remove_fixture(struct mCore *c,unsigned id){
 uint32_t counts[G_ITEMS];g_inventory(c,counts);
 if(counts[id])a_require(call_preserving(c,0x08099BE1U,id,counts[id],0,0)!=0U,"shop fixture item removal failed");
}
static bool g_menu(struct mCore *c){return read16(c,G_STATE+90U)==9U && read8(c,G_STATE+96U)<32U && read8(c,P02S_FIELD_LOCK);}
static void g_menu_check(struct mCore *c,unsigned omitted){
 unsigned count=read8(c,G_STATE+94U),expected=omitted<45U?44U:45U;
 a_require(g_menu(c) && count==expected,"physical shop eligible count differs");
 for(unsigned k=0,index=0;k<count;++k,++index){if(index==omitted)++index;a_require(read16(c,G_STATE+2U*k)==index,"physical shop eligible sequence differs");}
}
static void g_open(struct mCore *c,bool unlocked){
 b_position(c,96,5,24,20);unsigned object=read8(c,P02S_PLAYER_AVATAR+5U);a_require(object<16U,"shop avatar absent");
 if((read8(c,P02S_OBJECT_EVENTS+object*0x24U+0x18U)&15U)!=2U)b_frame(c,QOL_KEY_UP);
 b_frames_run(c,0,30);b_position(c,96,5,24,20);b_press(c,QOL_KEY_A,60);
 for(unsigned f=0;f<1800U;++f){
  if(unlocked?g_menu(c):read16(c,G_STATE+90U)==3U){b_frames_run(c,0,30);g_state(c,"opened");g_shot("opened");return;}
  b_frame(c,0);
 }
 g_state(c,"open-timeout");g_shot("open-timeout");a_die("real shop NPC did not open expected route");
}
static void g_finish(struct mCore *c){
 unsigned stable=0;
 for(unsigned f=0;f<12000U;++f){
  if(b_field(c)){if(++stable==60U){c->setKeys(c,0);return;}}else stable=0;
  b_frame(c,read8(c,P02S_FIELD_LOCK) && f%30U==0U?QOL_KEY_B:0U);
 }
 g_state(c,"return-timeout");g_shot("return-timeout");a_die("physical shop dialogue did not return to field");
}
static void g_down(struct mCore *c,unsigned target){
 for(unsigned k=0;k<6U && read8(c,G_CURSOR)!=target;++k)b_press(c,QOL_KEY_DOWN,30);
 a_require(read8(c,G_CURSOR)==target,"physical shop cursor did not follow input");
}
int main(int argc,char **argv){
 if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
 if(argc!=7)return 2;
 const struct GCase *v=NULL;for(unsigned k=0;k<sizeof(g_cases)/sizeof(g_cases[0]);++k)if(!strcmp(argv[5],g_cases[k].name))v=&g_cases[k];if(!v)return 2;
 g_prefix=argv[6];char hash[65],seed[65],after[65];sha256_file(argv[1],hash);sha256_file(argv[2],seed);
 a_require(!strcmp(hash,G_SHA) && !strcmp(hash,argv[3]) && !strcmp(seed,B_SEED_SHA) && !strcmp(seed,argv[4]),"shop input identity differs");
 struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
 struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);c->reset(c);
 a_require(a_continue(c),"shop initial Continue failed");a_flash_prepare(c);
 (void)call_preserving(c,0x09220861U,96U,5U,24U,20U);run_key_frames(c,0,1800U);
 for(unsigned k=0;k<12U && !b_field(c);++k)b_press(c,QOL_KEY_B,180U);
 g_state(c,"fixture-warp");g_shot("fixture");b_position(c,96,5,24,20);a_require(b_field(c),"shop fixture field did not settle");
 (void)call_preserving(c,0x0809984DU,0,0,0,0);
 for(unsigned k=0;k<45U;++k){g_remove_fixture(c,999U+k);(void)call_preserving(c,QOL_FLAG_CLEAR,0x14A0U+k,0,0,0);}
 g_remove_fixture(c,580U);if(v->action!=4U)a_require(call_preserving(c,0x08099A8DU,580U,1U,0,0)!=0U,"shop ring fixture rejected");
 unsigned initial_bp=v->action==3U?15U:64U;write16(c,QOL_LEDGER+0x392U,initial_bp);
 (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
 uint32_t before[G_ITEMS],expected[G_ITEMS],now[G_ITEMS];g_inventory(c,before);memcpy(expected,before,sizeof(expected));
 uint8_t party[600],party_after[600];b_copy(c,QOL_PLAYER_PARTY,party,600U);unsigned party_count=read8(c,QOL_PLAYER_PARTY_COUNT);
 unsigned initial_counter=read32(c,P03_SAVE_COUNTER),index=v->item-999U,pages=0U,result=v->action==0U?0U:v->action==3U?14U:v->action==4U?3U:2U;
 unsigned interaction,menu=0U,selection=0U,returned,saved_frame,reloaded,revisit=0U;
 /* The only actions after this boundary are physical input and reads. */
 struct mCore original=*c;a_guard(c);interaction=b_frames+1U;g_open(c,v->action!=4U);
 if(v->action!=4U){g_menu_check(c,45U);menu=b_frames;
  unsigned target_page=v->action==1U?0U:index/5U;
  while(pages<target_page){g_down(c,5U);b_press(c,QOL_KEY_A,60U);++pages;g_menu_check(c,45U);a_require(read8(c,G_STATE+95U)==pages && !read8(c,G_CURSOR),"physical shop page transition differs");}
  g_shot("selected-page");selection=b_frames+1U;
  if(v->action==1U || v->action==2U)b_press(c,QOL_KEY_B,60U);else{g_down(c,index%5U);b_press(c,QOL_KEY_A,180U);}
 }
 g_finish(c);returned=b_frames;g_state(c,"returned");g_shot("returned");
 a_require(read16(c,G_STATE+90U)==result,"physical shop transaction result differs");
 if(v->action==0U)expected[v->item]++;
 g_inventory(c,now);a_require(!memcmp(now,expected,sizeof(now)),"physical shop changed wrong item/quantity");
 unsigned expected_bp=initial_bp-(v->action==0U?16U:0U),automatic=v->action==0U?1U:0U;
 a_require(read16(c,QOL_LEDGER+0x392U)==expected_bp && read32(c,P03_SAVE_COUNTER)==initial_counter+automatic,"physical shop BP or automatic save differs");
 b_copy(c,QOL_PLAYER_PARTY,party_after,600U);a_require(!memcmp(party,party_after,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==party_count,"shop changed party");
 a_require(b_save(c),"shop normal Start Save failed");saved_frame=b_frames;
 a_restore(c,&original);c=b_restart(c,argv[1],argv[2]);c->reset(c);original=*c;a_guard(c);
 a_require(b_continue(c),"shop cold Continue failed");reloaded=b_frames;b_position(c,96,5,24,20);
 g_inventory(c,now);a_require(!memcmp(now,expected,sizeof(now)) && read16(c,QOL_LEDGER+0x392U)==expected_bp && read32(c,P03_SAVE_COUNTER)==initial_counter+automatic+1U,"shop cold save inventory/BP/counter differs");
 b_copy(c,QOL_PLAYER_PARTY,party_after,600U);a_require(!memcmp(party,party_after,600U) && read8(c,QOL_PLAYER_PARTY_COUNT)==party_count,"shop cold save changed party");
 if(v->action!=4U){g_open(c,true);g_menu_check(c,v->action==0U?index:45U);revisit=b_frames;g_shot("reloaded-catalogue");b_press(c,QOL_KEY_B,60U);g_finish(c);g_inventory(c,now);a_require(!memcmp(now,expected,sizeof(now)) && read16(c,QOL_LEDGER+0x392U)==expected_bp,"shop revisiting modified transaction");}
 a_restore(c,&original);qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(hash,after) && log_problem_count==0U,"shop ROM changed or emulator warning/error");
 printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",G_SCOPE,v->name,hash);
 printf("\"item\":%u,\"catalog_index\":%u,\"result\":%u,\"pages\":%u,\"quantity\":%u,\"bp_before\":%u,\"bp_after\":%u,\"automatic_saves\":%u,",v->item,index,result,pages,now[v->item],initial_bp,expected_bp,automatic);
 printf("\"manual_saves\":1,\"fresh_cores\":2,\"host_write_barriers\":7,\"rtc_flash_bytes_preserved\":131072,\"physical_host\":[96,5,14,24,19],\"inventory_and_party_preserved\":true,\"claim_catalogue_rechecked\":%s,",v->action==4U?"false":"true");
 printf("\"map_ring_bp_claims_are_fixtures\":true,\"natural_capture_accepted\":false,\"battle_connection_accepted\":false,\"full_p05_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"total_frames\":%u,",b_frames);
 printf("\"witness\":{\"interaction\":%u,\"menu\":%u,\"selection\":%u,\"returned\":%u,\"saved\":%u,\"reloaded\":%u,\"revisit\":%u}}\n",interaction,menu,selection,returned,saved_frame,reloaded,revisit);return 0;
}
