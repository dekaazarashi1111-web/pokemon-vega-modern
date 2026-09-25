/* Issue19 Collection gifts: actual NPC/menu inputs, never a TestGift call.
 * Party, map, progress and unclaimed owner are fixtures before the barrier.
 * Original initial moves are independent vectors; ROM/host writes prohibited
 * throughout gift/menu/Save/Continue. Getter calls are separated explicitly. */
#include "cf_helpers.c"
#include "cf_vectors.h"
#include "../overlays/collection_supply_v1/collection_supply_v1.h"
#define CF_STATE 0x0203F720U
#define CF_OWNER 0x0203D900U
#define CF_CURSOR 0x0203AD5EU
static const struct CFCase *cf_v;
static const char *cf_prefix;
static bool cf_watching;
static unsigned cf_claimed, cf_saves;
struct CFTrace {unsigned boundary,root,list,selected,claimed,returned,saved,continued,revisited,cancelled;};
static struct CFTrace cf_t;
_Static_assert(offsetof(CollectionSupplyOwnerV1, form_gift_bits)==80U,"owner claim offset");
_Static_assert(offsetof(CollectionSupplyVolatileState, test_mode)==27U,"test mode offset");
static void cf_shot(const char *stage) {
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",cf_prefix,stage);
    a_require(n>0 && n<(int)sizeof(path),"screenshot path");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"screenshot open");
    a_require(fprintf(f,"P6\n240 160\n255\n")>0,"screenshot header");
    for(unsigned i=0;i<240U*160U;++i) {
        uint32_t p=(uint32_t)b_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};
        a_require(fwrite(rgb,1,3,f)==3,"screenshot bytes");
    }
    a_require(!fclose(f),"screenshot close");
}
static void cf_diagnostic(struct mCore *c,const char *stage) {
    b_state(c,stage);
    fprintf(stderr,"CF_UI stage=%s mode=%u page=%u window=%u cursor=%u result=%u pending=%u host=%u service=%u test=%u lock=%u\n",
        stage,read8(c,CF_STATE+19),read8(c,CF_STATE+21),read8(c,CF_STATE+22),read8(c,CF_CURSOR),
        read16(c,CF_STATE+8),read16(c,CF_STATE+10),read8(c,CF_STATE+18),read8(c,CF_STATE+20),read8(c,CF_STATE+27),read8(c,P02S_FIELD_LOCK));
}
static void cf_frame(struct mCore *c,unsigned key) {
    unsigned before=read32(c,P03_SAVE_COUNTER);b_frame(c,key);
    if(cf_watching) {
        if(!cf_claimed && read8(c,QOL_PLAYER_PARTY_COUNT)==2U)cf_claimed=b_frames;
        unsigned after=read32(c,P03_SAVE_COUNTER);
        if(before!=after) {
            ++cf_saves;
            unsigned count=read8(c,QOL_PLAYER_PARTY_COUNT),lock=read8(c,P02S_FIELD_LOCK);
            fprintf(stderr,"CF_SAVE frame=%u before=%u after=%u count=%u lock=%u\n",b_frames,before,after,count,lock);
            a_require(cf_saves<=8U && after==before+1U && count>=1U && count<=2U && lock,"native collection Save transition");
        }
    }
}
static void cf_press(struct mCore *c,unsigned key,unsigned settle) {
    for(unsigned i=0;i<2U;++i)cf_frame(c,key);
    for(unsigned i=0;i<settle;++i)cf_frame(c,0U);
}
static bool cf_menu(struct mCore *c,unsigned mode) {
    return read32(c,CF_STATE)==0x31545343U && read8(c,CF_STATE+19)==mode
        && read8(c,CF_STATE+22)<32U && read8(c,P02S_FIELD_LOCK)
        && read8(c,CF_STATE+18)==CF_HOST_INDEX && read8(c,CF_STATE+20)==5U
        && read8(c,CF_STATE+27)==0U;
}
static void cf_wait_menu(struct mCore *c,unsigned mode) {
    for(unsigned f=0;f<2400U;++f) {
        if(cf_menu(c,mode)) {for(unsigned k=0;k<30U;++k)cf_frame(c,0U);cf_diagnostic(c,"menu");return;}
        cf_frame(c,0U);
    }
    cf_diagnostic(c,"menu-timeout");cf_shot("menu-timeout");a_die("actual collection menu missing");
}
static void cf_down(struct mCore *c,unsigned target) {
    for(unsigned k=0;k<6U && read8(c,CF_CURSOR)!=target;++k)cf_press(c,QOL_KEY_DOWN,30U);
    a_require(read8(c,CF_CURSOR)==target,"physical collection cursor");
}
static void cf_open(struct mCore *c) {
    b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);
    cf_press(c,QOL_KEY_UP,30U);b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);
    cf_press(c,QOL_KEY_A,30U);cf_wait_menu(c,0U);
}
static void cf_list(struct mCore *c) {
    cf_down(c,1U);cf_press(c,QOL_KEY_A,30U);cf_wait_menu(c,3U);
    a_require(read8(c,CF_STATE+21)==0U,"initial collection page");
}
static void cf_finish(struct mCore *c) {
    unsigned stable=0U;
    for(unsigned f=0;f<16000U;++f) {
        if(b_field(c)) {if(++stable==30U){c->setKeys(c,0U);return;}}else stable=0U;
        cf_frame(c,read8(c,P02S_FIELD_LOCK) && f%90U==0U?QOL_KEY_B:0U);
    }
    cf_diagnostic(c,"return-timeout");a_die("collection field return timeout");
}
static void cf_raw(struct mCore *c,const char *stage,unsigned count,uint8_t *party) {
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==count,"collection party count");
    b_copy(c,QOL_PLAYER_PARTY,party,count*100U);
    fprintf(stderr,"CF_PARTY stage=%s counter=%u hex=",stage,read32(c,P03_SAVE_COUNTER));
    for(unsigned i=0;i<count*100U;++i){fprintf(stderr,"%02x",party[i]);}
    fputc('\n',stderr);
    fprintf(stderr,"CF_OWNER stage=%s hex=",stage);
    for(unsigned i=0;i<512U;++i){fprintf(stderr,"%02x",read8(c,CF_OWNER+i));}
    fputc('\n',stderr);
}
static void cf_check(struct mCore *c,const char *stage) {
    unsigned mon=QOL_PLAYER_PARTY+100U;
    unsigned species=b_data(c,mon,11U),level=b_data(c,mon,56U),egg=b_data(c,mon,45U);
    a_require(species==cf_v->species && level==cf_v->level && egg==cf_v->egg && b_data(c,mon,21U)==0U,"gift owner/level/egg/PP bonus");
    for(unsigned i=0;i<4U;++i)a_require(b_data(c,mon,13U+i)==cf_v->moves[i] && b_data(c,mon,17U+i)==cf_v->pp[i],"gift original slot/PP");
    unsigned hp=b_data(c,mon,57U),maximum=b_data(c,mon,58U);
    a_require(hp>0U && hp<=maximum,"gift native HP");
    fprintf(stderr,"CF_MON stage=%s species=%u level=%u egg=%u hp=%u max=%u\n",stage,species,level,egg,hp,maximum);
    a_require(read8(c,CF_OWNER+20)==0U && read8(c,CF_OWNER+80)==(cf_v->egg?0U:1U<<cf_v->bit),"gift committed owner");
}
static void cf_fixture_owner(struct mCore *c) {
    CollectionSupplyOwnerV1 o;memset(&o,0,sizeof(o));
    o.magic=0x31565343U;o.magic_inverse=~o.magic;o.version=1U;o.struct_size=sizeof(o);o.generation=1U;o.transaction_id=1U;
    const uint8_t *raw=(const uint8_t *)&o;uint32_t crc=0xFFFFFFFFU;
    for(unsigned i=0;i<sizeof(o);++i) {
        crc^=raw[i];for(unsigned j=0;j<8U;++j)crc=(crc>>1)^((0U-(crc&1U))&0xEDB88320U);
    }
    o.crc32=crc^0xFFFFFFFFU;
    for(unsigned i=0;i<sizeof(o);++i)write8(c,CF_OWNER+i,raw[i]);
}
int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    for(unsigned i=0;i<sizeof(cf_cases)/sizeof(cf_cases[0]);++i)if(!strcmp(argv[5],cf_cases[i].name))cf_v=&cf_cases[i];
    if(!cf_v)return 2;
    cf_prefix=argv[6];
    a_require(!strcmp(projectVersion,"0.10.2"),"mGBA version");
    char rom_hash[65],seed_hash[65],after_hash[65];sha256_file(argv[1],rom_hash);sha256_file(argv[2],seed_hash);
    a_require(!strcmp(rom_hash,B_ROM_SHA) && !strcmp(rom_hash,argv[3]) && !strcmp(seed_hash,B_SEED_SHA) && !strcmp(seed_hash,argv[4]),"collection input identity");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);
    a_require(a_continue(c),"collection seed Continue");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"collection initial party fixture");
    /* Explicit unlock fixture; never claim story/progression acceptance. */
    for(unsigned i=16U;i<=21U;++i)write8(c,QOL_LEDGER+i,1U);
    write8(c,QOL_LEDGER+0x73FU,1U);write8(c,QOL_LEDGER+0x745U,1U);
    for(unsigned flag=0x820U;flag<0x828U;++flag)(void)call_preserving(c,QOL_FLAG_SET,flag,0,0,0);
    (void)call_preserving(c,QOL_FLAG_SET,0x82CU,0,0,0);(void)call_preserving(c,QOL_FLAG_SET,0x114BU,0,0,0);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0,0,0);
    (void)call_preserving(c,0x09220861U,CF_GROUP,CF_NUMBER,CF_X,CF_Y);run_key_frames(c,0U,900U);
    b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);cf_fixture_owner(c);
    a_require(!read8(c,CF_STATE+27U),"test mode forbidden");
    uint8_t initial[100],party[200],again[200];cf_raw(c,"fixture",1U,initial);
    unsigned counter[5]={read32(c,P03_SAVE_COUNTER),0,0,0,0};
    struct mCore saved=*c;a_guard(c);b_frames_run(c,0U,1U);cf_t.boundary=b_frames;
    cf_open(c);cf_t.root=b_frames;cf_list(c);cf_t.list=b_frames;
    for(unsigned page=0;page<cf_v->index/5U;++page) {
        cf_down(c,5U);cf_press(c,QOL_KEY_A,60U);
        a_require(cf_menu(c,3U) && read8(c,CF_STATE+21)==page+1U && read8(c,CF_CURSOR)==0U,"physical next page");
    }
    cf_down(c,cf_v->index%5U);cf_shot("selected");cf_t.selected=b_frames;cf_watching=true;
    cf_press(c,QOL_KEY_A,30U);cf_finish(c);cf_watching=false;
    cf_t.claimed=cf_claimed;cf_t.returned=b_frames;
    a_require(cf_claimed>cf_t.selected && cf_claimed<cf_t.returned && read16(c,CF_STATE+8)==0U && read16(c,CF_STATE+10)==cf_v->index,"native selected gift result");
    cf_raw(c,"claimed",2U,party);counter[1]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(initial,party,100U) && counter[1]>counter[0] && counter[1]-counter[0]==cf_saves,"original party/native saves");
    cf_shot("received");a_restore(c,&saved);cf_check(c,"claimed");a_guard(c);
    a_require(b_save(c),"collection ordinary Save");cf_t.saved=b_frames;
    cf_raw(c,"saved",2U,again);counter[2]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200U) && counter[2]==counter[1]+1U,"saved collection party");
    a_restore(c,&saved);c=b_restart(c,argv[1],argv[2]);saved=*c;a_guard(c);
    a_require(b_continue(c),"collection fresh Continue");cf_t.continued=b_frames;b_position(c,CF_GROUP,CF_NUMBER,CF_X,CF_Y);
    cf_raw(c,"continued",2U,again);counter[3]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200U) && counter[3]==counter[2],"fresh collection persistence");
    cf_shot("continued");a_restore(c,&saved);cf_check(c,"continued");a_guard(c);
    cf_open(c);cf_list(c);cf_t.revisited=b_frames;cf_press(c,QOL_KEY_B,30U);cf_finish(c);cf_t.cancelled=b_frames;
    cf_raw(c,"cancelled",2U,again);counter[4]=read32(c,P03_SAVE_COUNTER);
    a_require(!memcmp(party,again,200U) && counter[4]==counter[3] && read16(c,CF_STATE+8)==2U,"revisit cancel preserved party/save");
    a_restore(c,&saved);cf_check(c,"cancelled");qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after_hash);
    a_require(!strcmp(rom_hash,after_hash) && !log_problem_count,"collection ROM/log invariant");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"COLLECTION_NPC_INITIAL_MOVES_SAVE_CONTINUE\",\"case\":\"%s\",\"candidate_sha256\":\"%s\",\"gift_index\":%u,\"species\":%u,\"level\":%u,\"is_egg\":%u,\"moves\":",cf_v->name,rom_hash,cf_v->index,cf_v->species,cf_v->level,cf_v->egg);
    a_array(cf_v->moves);printf(",\"pp\":");a_array(cf_v->pp);
    printf(",\"npc_script\":%u,\"save_counters\":[%u,%u,%u,%u,%u],\"owner_claim_bits\":[0,%u,%u,%u,%u],\"native_save_steps\":%u,",CF_SCRIPT,counter[0],counter[1],counter[2],counter[3],counter[4],cf_v->egg?0U:1U<<cf_v->bit,cf_v->egg?0U:1U<<cf_v->bit,cf_v->egg?0U:1U<<cf_v->bit,cf_v->egg?0U:1U<<cf_v->bit,cf_saves);
    printf("\"fresh_cores\":2,\"denied_host_write_apis\":7,\"guarded_phases\":4,\"party_preserved_bytes\":200,\"initial_party_map_unlock_claim_are_fixtures\":true,\"story_acquisition_verified\":false,\"egg_hatch_verified\":false,\"all_owners_accepted\":false,\"issue19_complete\":false,\"release_ready\":false,\"warnings_errors\":0,\"witness\":{");
#define CF_W(name) printf("\""#name"\":%u,",cf_t.name)
    CF_W(boundary);CF_W(root);CF_W(list);CF_W(selected);CF_W(claimed);CF_W(returned);CF_W(saved);CF_W(continued);CF_W(revisited);
    printf("\"cancelled\":%u}}\n",cf_t.cancelled);return 0;
}
