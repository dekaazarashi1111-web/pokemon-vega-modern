/* P06既決2種。既存個体の保存slotを親ROMで作成・通常保存し、別ROMの
 * 新coreでContinue。次に通常Bagのアメで再計算し、通常保存・第3coreで再確認。
 * fixture作成とABI読取は観測外。保存/Continue/アメ操作中はhost書込7 API禁止。
 * 捕獲・戦闘効果そのものの試験ではない。 */
#include "p06_archive_embedded.c"
#define D_SCOPE "P06_DECIDED_SLOTS_NATIVE_CANDY_CROSS_ROM_COLD_SAVE"
static void d_bytes(struct mCore*c,uint8_t b[100]){for(unsigned i=0;i<100;i++)b[i]=read8(c,QOL_PLAYER_PARTY+i);}
static unsigned d_ability(struct mCore*c){return call_preserving(c,P02S_GET_MON_ABILITY,QOL_PLAYER_PARTY,0,0,0);}
static void d_stats(struct mCore*c,unsigned v[6]){
    for(unsigned i=0;i<6;i++)v[i]=read16(c,QOL_PLAYER_PARTY+0x58+2*i);
}
static void d_array(const unsigned a[6]){printf("[%u,%u,%u,%u,%u,%u]",a[0],a[1],a[2],a[3],a[4],a[5]);}
static void d_hex(const uint8_t a[100]){putchar('"');for(unsigned i=0;i<100;i++)printf("%02x",a[i]);putchar('"');}
struct DTrace {unsigned bag_party,level_up,field;};
static struct DTrace d_candy(struct mCore*c){
    unsigned start=c->frameCounter(c);struct DTrace t={0};
    a_require(p02s_enter_item_party(c,P02S_ITEM_RARE_CANDY,"p06_native_candy"),"normal Bag item did not reach party");
    t.bag_party=a_stamp(c,start);unsigned stable=0;
    for(unsigned f=1;f<=12000;f++){
        unsigned level=read8(c,QOL_PLAYER_PARTY+84),cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        a_require(level==48 || level==49,"unexpected level during Candy");
        if(level==49 && !t.level_up)t.level_up=a_stamp(c,start);
        if(t.level_up && a_field(c)){if(++stable>=240){t.field=a_stamp(c,start);c->setKeys(c,0);return t;}}else stable=0;
        unsigned key=0;
        if(f%30==0){
            if(t.level_up && (cb==P02S_CB2_PARTY || cb==P02S_CB2_BAG || cb==P02S_CB2_FIELD))key=QOL_KEY_B;
            else key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
    }
    a_die("native Candy route timed out");
}
int main(int argc,char**argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=10)return 2;
    unsigned species=qol_number(argv[7],"species"),slot=qol_number(argv[8],"slot"),mode=qol_number(argv[9],"mode");
    if((species!=220 && species!=373) || slot>1 || mode>1)return 2;
    char parent_sha[65],child_sha[65],h[65];sha256_file(argv[1],parent_sha);sha256_file(argv[2],child_sha);sha256_file(argv[3],h);
    a_require(!strcmp(parent_sha,argv[4]) && !strcmp(child_sha,argv[5]) && !strcmp(h,argv[6]),"P06 fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[3]);
    const char*initial_rom=mode?argv[2]:argv[1];
    struct mCore*c=qol_open(initial_rom,argv[3]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);
    a_require(a_continue(c),"initial Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"P06 fixture failed");p02s_enable_national_dex(c);
    clear_parties(c);write32_bytes(c,BATTLE_CORE_GLOBAL_RNG,0x12345678U);create_mon(c,QOL_PLAYER_PARTY,species,48);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    p02s_set_data(c,P02S_MON_DATA_ALT_ABILITY,slot);p02s_set_hidden(c,false);
    const unsigned moves[4]={33,81,407,52};for(unsigned i=0;i<4;i++){p02s_set_data(c,QOL_MON_DATA_MOVE1+i,moves[i]);p02s_set_data(c,MON_DATA_PP1+i,10);}
    p02s_prepare_item(c,P02S_ITEM_RARE_CANDY);
    unsigned ability_before=d_ability(c),initial_stats[6],loaded_stats[6],final_stats[6];d_stats(c,initial_stats);
    unsigned ivs[6],evs[6];for(unsigned i=0;i<6;i++){ivs[i]=p02s_data(c,QOL_MON_DATA_HP_IV+i);evs[i]=p02s_data(c,QOL_MON_DATA_HP_EV+i);}
    unsigned personality=p02s_data(c,0),counter=read32(c,P03_SAVE_COUNTER);uint8_t before[100],loaded[100],after[100],cold[100];
    struct mCore apis=*c;a_guard(c);a_require(a_save(c),"parent/native save failed");a_restore(c,&apis);d_bytes(c,before);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1,"parent save counter differs");
    qol_close(c);qol_log_core=NULL;
    c=qol_open(argv[2],argv[3]);qol_log_core=c;c->setVideoBuffer(c,video,240);a_flash_prepare(c);apis=*c;a_guard(c);
    a_require(a_continue(c),"candidate cross-ROM Continue failed");d_bytes(c,loaded);d_stats(c,loaded_stats);a_restore(c,&apis);
    a_require(!memcmp(before,loaded,100),"candidate Continue rewrote existing mon");
    unsigned ability_loaded=d_ability(c);
    a_require(p02s_data(c,P02S_MON_DATA_ALT_ABILITY)==slot && !p02s_hidden(c),"stored ability slot changed");
    a_require(p02s_data(c,P02S_MON_DATA_SPECIES2)==species && p02s_data(c,QOL_MON_DATA_LEVEL)==48,"loaded species/level differs");
    a_guard(c);struct DTrace t=d_candy(c);a_restore(c,&apis);d_stats(c,final_stats);
    a_require(p02s_data(c,QOL_MON_DATA_LEVEL)==49 && p02s_data(c,P02S_MON_DATA_SPECIES2)==species,"Candy changed species or wrong level");
    a_require(p02s_data(c,P02S_MON_DATA_ALT_ABILITY)==slot && !p02s_hidden(c),"Candy changed saved slot");
    a_require(p02s_bag_exact(c,P02S_ITEM_RARE_CANDY,0),"Candy was not consumed exactly once");
    for(unsigned i=0;i<4;i++)a_require(p02s_data(c,QOL_MON_DATA_MOVE1+i)==moves[i] && p02s_data(c,MON_DATA_PP1+i)==10,"Candy changed retained moves/PP");
    a_guard(c);a_require(a_save(c),"candidate native save failed");a_restore(c,&apis);d_bytes(c,after);
    a_require(!memcmp(before,after,8) && read32(c,P03_SAVE_COUNTER)==counter+2,"identity or second counter changed");
    qol_close(c);qol_log_core=NULL;
    c=qol_open(argv[2],argv[3]);qol_log_core=c;c->setVideoBuffer(c,video,240);a_flash_prepare(c);apis=*c;a_guard(c);
    a_require(a_continue(c),"third core Continue failed");d_bytes(c,cold);a_restore(c,&apis);
    unsigned ability_final=d_ability(c);
    a_require(!memcmp(after,cold,100) && read32(c,P03_SAVE_COUNTER)==counter+2,"candidate cold-save bytes/counter differs");
    a_require(p02s_bag_exact(c,P02S_ITEM_RARE_CANDY,0),"cold save restored consumed Candy");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],h);a_require(!strcmp(h,parent_sha),"parent ROM changed");sha256_file(argv[2],h);
    a_require(!strcmp(h,child_sha) && !log_problem_count,"candidate changed or emulator warning/error");
    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\",\"parent_sha256\":\"%s\",\"candidate_sha256\":\"%s\",\"species\":%u,\"slot\":%u,\"mode\":%u,\"ability_before\":%u,\"ability_loaded\":%u,\"ability_final\":%u,\"personality\":%u,\"ivs\":",D_SCOPE,parent_sha,child_sha,species,slot,mode,ability_before,ability_loaded,ability_final,personality);
    d_array(ivs);printf(",\"evs\":");d_array(evs);printf(",\"initial_stats\":");d_array(initial_stats);printf(",\"loaded_stats\":");d_array(loaded_stats);printf(",\"final_stats\":");d_array(final_stats);
    printf(",\"initial_level\":48,\"final_level\":49,\"bag_party_frame\":%u,\"level_up_frame\":%u,\"field_frame\":%u,\"save_counter_delta\":2,\"normal_save_menu\":true,\"fresh_core_count\":3,\"cross_rom_100_bytes_equal\":true,\"candidate_cold_100_bytes_equal\":true,\"slot_preserved\":true,\"host_write_barriers\":5,\"native_creation_is_fixture\":true,\"ability_read_uses_native_abi\":true,\"full_p06_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"before_mon_hex\":",t.bag_party,t.level_up,t.field);
    d_hex(before);printf(",\"after_mon_hex\":");d_hex(after);puts("}");return 0;
}
