/* P06 adopted abilities and Attack: normal Summary input and native battle.
 * Only deterministic party/opponent fixture construction precedes the barrier.
 * From before the first battle/Start-menu frame all seven host write APIs are
 * denied. No BattleMon ability/stat injection or direct effect call is used. */
#include "p06_archive_embedded.c"
#define F_SCOPE "P06_ADOPTED_NATIVE_SUMMARY_AND_BATTLE"
#define F_MAIN 0x03004FC4U
#define F_EXEC 0x02023B28U
#define F_BUFFER 0x02022B24U
#define F_ACTION 0x08013861U
#define F_END 0x0801333DU
#define F_MON(n) (ADDR_BATTLE_MONS+(n)*BATTLE_MON_SIZE)
#define F_DISABLE 0x02023D6CU
#define F_LAST_ABILITY 0x0203DFACU
#define F_LAST_ITEM 0x02023CC8U
#define F_NAMES 0x0904B770U
#define F_DESCRIPTIONS 0x0904CC28U
#define F_LIMIT 24000U
static const char *f_names[]={"summary-220-0","summary-220-1","summary-373-0","cursed-body","cursed-slot-control","frisk-item","frisk-no-item","frisk-slot-control","attack-before","attack-after"};
static color_t f_video[240*160];
struct FResult {unsigned frames,presses,menu_frame,event_frame,turns,ability,party_attack,battle_attack,player_hp,enemy_hp,enemy_initial_hp,player_pp,enemy_pp,disabled_move,disable_timer,reveal_item,summary_page;bool ended,summary_equal,mon_equal;uint8_t name[9],description[23];};
static void f_shot(const char *prefix,const char *suffix){
    char path[4096];int n=snprintf(path,sizeof(path),"%s-%s.ppm",prefix,suffix);a_require(n>0 && n<(int)sizeof(path),"screenshot path too long");
    FILE *f=fopen(path,"wb");a_require(f!=NULL,"screenshot open failed");a_require(fprintf(f,"P6\n240 160\n255\n")>0,"screenshot header failed");
    for(unsigned i=0;i<240*160;i++){uint32_t p=(uint32_t)f_video[i];uint8_t rgb[3]={(uint8_t)p,(uint8_t)(p>>8),(uint8_t)(p>>16)};a_require(fwrite(rgb,1,3,f)==3,"screenshot write failed");}
    a_require(!fclose(f),"screenshot close failed");
}
static void f_mon_bytes(struct mCore*c,uint8_t *b){for(unsigned i=0;i<100;i++)b[i]=read8(c,QOL_PLAYER_PARTY+i);}
static void f_hex(const uint8_t*b,unsigned n){putchar('"');for(unsigned i=0;i<n;i++)printf("%02x",b[i]);putchar('"');}
static bool f_action(struct mCore*c){return read32(c,F_MAIN)==F_ACTION && (read32(c,F_EXEC)&1U) && read8(c,F_BUFFER)==0x12U;}
static bool f_string(struct mCore*c,unsigned dst,unsigned src,uint8_t*out,unsigned size){
    bool ended=false,equal=true;for(unsigned i=0;i<size;i++){unsigned expected=ended || i==size-1?255:read8(c,src+i);if(expected==255)ended=true;out[i]=read8(c,dst+i);if(out[i]!=expected)equal=false;}return equal;
}
static struct FResult f_summary(struct mCore*c,unsigned ability,unsigned attack,const char*prefix){
    struct FResult r={0};r.ability=ability;r.party_attack=attack;unsigned start=c->frameCounter(c);uint8_t before[100],after[100];f_mon_bytes(c,before);
    qol_press(c,QOL_KEY_START,90);r.presses++;
    a_require(read32(c,QOL_START_MENU_CALLBACK)==QOL_START_MENU_INPUT,"Start menu not ready");
    unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;
    a_require(count>0 && count<=8 && cursor<count,"invalid Start menu");
    for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==1)target=i;
    a_require(target<count,"party not offered");
    for(unsigned i=0,n=(target+count-cursor)%count;i<n;i++){qol_press(c,QOL_KEY_DOWN,30);r.presses++;}
    a_require(read8(c,QOL_START_MENU_CURSOR)==target,"party cursor mismatch");
    qol_press(c,QOL_KEY_A,600);qol_press(c,QOL_KEY_A,240);qol_press(c,QOL_KEY_UP,12);qol_press(c,QOL_KEY_A,30);r.presses+=4;
    unsigned summary=0;
    for(unsigned f=0;f<1800;f++){unsigned p=read32(c,QOL_SUMMARY_DATA_SLOT);if(p>=0x02000000U && p+0x3308U<0x02040000U && read8(c,p+QOL_SUMMARY_INPUT_STATE)==2){summary=p;break;}c->setKeys(c,0);c->runFrame(c);}
    f_shot(prefix,"summary-entry");
    a_require(summary!=0,"native Summary input timed out");r.menu_frame=c->frameCounter(c)-start;
    qol_press(c,QOL_KEY_RIGHT,120);r.presses++;r.summary_page=read8(c,summary+QOL_SUMMARY_PAGE);
    r.summary_equal=f_string(c,summary+0x318c,F_NAMES+ability*17,r.name,9);
    r.summary_equal=f_string(c,summary+0x3195,read32(c,F_DESCRIPTIONS+ability*4),r.description,23) && r.summary_equal;
    a_require(r.summary_page==1 && read8(c,summary+QOL_SUMMARY_INPUT_STATE)==2,"skills page not ready");
    a_require(read16(c,summary+0x323c+0x5a)==attack,"Summary copied Attack differs");
    f_shot(prefix,"skills");qol_press(c,QOL_KEY_B,240);r.presses++;
    for(unsigned i=0;i<4 && !a_field(c);i++){qol_press(c,QOL_KEY_B,240);r.presses++;}
    r.ended=a_field(c);f_mon_bytes(c,after);r.mon_equal=!memcmp(before,after,100);r.frames=c->frameCounter(c)-start;
    return r;
}
static struct FResult f_battle(struct mCore*c,unsigned id,unsigned ability,unsigned attack,const char*prefix){
    struct FResult r={0};r.ability=ability;r.party_attack=attack;unsigned last_pp=20,previous_keys=0,last_main=0;bool pending_end=false;
    for(unsigned f=1;f<=F_LIMIT;f++){
        r.frames=f;unsigned main=read32(c,F_MAIN),pp=read8(c,F_MON(0)+0x24),ep=read8(c,F_MON(1)+0x24);
        unsigned la=read16(c,F_LAST_ABILITY),li=read16(c,F_LAST_ITEM);
        if(la==120 && li==13 && !r.event_frame){r.event_frame=f;r.reveal_item=li;f_shot(prefix,"frisk-event");}
        unsigned disabled=read16(c,F_DISABLE+0x1c+4),timer=read8(c,F_DISABLE+0x1c+0xb)&15U;
        if(disabled && timer){r.disabled_move=disabled;r.disable_timer=timer;if(!r.event_frame){r.event_frame=f;f_shot(prefix,"disable-event");}}
        if(!r.menu_frame && f_action(c)){
            r.menu_frame=f;r.battle_attack=read16(c,F_MON(0)+2);r.enemy_initial_hp=read16(c,F_MON(1)+0x28);
            a_require(read16(c,F_MON(0)+0x38)==ability,"native battle imported wrong adopted ability");
            a_require(r.battle_attack==attack,"native battle imported wrong Attack");
            a_require(read16(c,F_MON(0))==(id>=8?373U:220U),"native battle imported wrong species");
            a_require(pp==20 && ep==20,"first input PP differs");f_shot(prefix,"first-input");
            if(id>=5 && id<=7){r.ended=true;break;}
        }
        if(r.menu_frame){
            if(main==F_END)pending_end=true;
            if(pp<last_pp && pending_end && main==F_ACTION){
                r.turns++;last_pp=pp;pending_end=false;
                if(id>=8 || (id==3 && r.disabled_move==44) || (id==4 && r.turns==4)){r.ended=true;break;}
            }
            if(read8(c,BATTLE_CORE_BATTLE_OUTCOME))break;
        }
        if(main!=last_main){fprintf(stderr,"frame=%u main=%08x pp=%u/%u ability=%u item=%u disable=%u/%u\n",f,main,pp,ep,la,li,disabled,timer);last_main=main;}
        unsigned key=(f%30<2 && (main==F_ACTION || f%90<2))?QOL_KEY_A:0;
        if(key && !previous_keys)r.presses++;
        previous_keys=key;c->setKeys(c,key);c->runFrame(c);
    }
    c->setKeys(c,0);r.player_hp=read16(c,F_MON(0)+0x28);r.enemy_hp=read16(c,F_MON(1)+0x28);r.player_pp=read8(c,F_MON(0)+0x24);r.enemy_pp=read8(c,F_MON(1)+0x24);
    f_shot(prefix,"end");return r;
}
int main(int argc,char**argv){
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=7)return 2;
    unsigned id=qol_number(argv[5],"case");if(id>=ARRAY_LEN(f_names))return 2;
    char rom_sha[65],seed_sha[65];sha256_file(argv[1],rom_sha);sha256_file(argv[2],seed_sha);
    a_require(!strcmp(rom_sha,argv[3]) && !strcmp(seed_sha,argv[4]),"fixed input identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,f_video,240);c->reset(c);a_require(a_continue(c),"initial Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"field fixture failed");p02s_enable_national_dex(c);clear_parties(c);seed_fixture(c);
    unsigned species=id==2 || id>=8?373:220,slot=id==1 || id==4 || id==5 || id==6?1:0;
    create_mon(c,QOL_PLAYER_PARTY,species,48);write8(c,QOL_PLAYER_PARTY_COUNT,1);p02s_set_data(c,P02S_MON_DATA_ALT_ABILITY,slot);p02s_set_hidden(c,false);
    for(unsigned i=0;i<4;i++){p02s_set_data(c,MON_DATA_MOVE1+i,i?0:(id>=8?33:150));p02s_set_data(c,MON_DATA_PP1+i,i?0:20);}
    unsigned ability=call_preserving(c,P02S_GET_MON_ABILITY,QOL_PLAYER_PARTY,0,0,0),attack=read16(c,QOL_PLAYER_PARTY+0x5a);
    unsigned pid=read32(c,QOL_PLAYER_PARTY);struct FResult r;
    if(id>=3){
        create_mon(c,ADDR_ENEMY_PARTY,id>=8?93:481,id>=8?48:10);write8(c,BATTLE_CORE_ENEMY_PARTY_COUNT,1);
        for(unsigned i=0;i<4;i++){set_mon_data_u32(c,ADDR_ENEMY_PARTY,MON_DATA_MOVE1+i,i?0:(id==3 || id==4?44:150));set_mon_data_u32(c,ADDR_ENEMY_PARTY,MON_DATA_PP1+i,i?0:20);}
        set_mon_data_u32(c,ADDR_ENEMY_PARTY,12,id==5 || id==7?13:0);seed_fixture(c);
        struct CallObservation entry=call_bounded(c,BATTLE_CORE_START_WILD,0,0,0,0);a_require(entry.payload_pc_seen,"native battle construction failed");
    }
    struct mCore apis=*c;a_guard(c);
    if(id<3)r=f_summary(c,ability,attack,argv[6]);else r=f_battle(c,id,ability,attack,argv[6]);
    a_restore(c,&apis);qol_close(c);qol_log_core=NULL;
    sha256_file(argv[1],seed_sha);a_require(!strcmp(seed_sha,rom_sha),"ROM modified");a_require(!log_problem_count,"emulator warnings/errors");
    printf("{\"schema_version\":1,\"status\":\"OBSERVED\",\"scope\":\"%s\",\"rom_sha256\":\"%s\",\"case\":\"%s\",\"species\":%u,\"slot\":%u,\"personality\":%u,\"ability\":%u,\"party_attack\":%u,\"battle_attack\":%u,\"frames\":%u,\"key_presses\":%u,\"menu_frame\":%u,\"event_frame\":%u,\"turns\":%u,\"player_hp\":%u,\"enemy_hp\":%u,\"enemy_initial_hp\":%u,\"player_pp\":%u,\"enemy_pp\":%u,\"disabled_move\":%u,\"disable_timer\":%u,\"reveal_item\":%u,\"summary_page\":%u,\"ended\":%s,\"summary_equal\":%s,\"mon_equal\":%s,\"host_write_guard\":true,\"fixture_boundary\":\"BEFORE_FIRST_OBSERVED_FRAME\",\"full_p06_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"ability_name_hex\":",F_SCOPE,rom_sha,f_names[id],species,slot,pid,r.ability,r.party_attack,r.battle_attack,r.frames,r.presses,r.menu_frame,r.event_frame,r.turns,r.player_hp,r.enemy_hp,r.enemy_initial_hp,r.player_pp,r.enemy_pp,r.disabled_move,r.disable_timer,r.reveal_item,r.summary_page,r.ended?"true":"false",r.summary_equal?"true":"false",r.mon_equal?"true":"false");f_hex(r.name,9);printf(",\"ability_description_hex\":");f_hex(r.description,23);puts("}");return 0;
}
