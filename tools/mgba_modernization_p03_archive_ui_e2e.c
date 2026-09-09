/* Stage82 archive UI. Fixture setup ends before opening Bag. Across Bag,
 * party/page/list/summary input, native Save and a new core's Continue, all
 * seven mCore host write APIs are denied. No target ROM function is called
 * during those observed phases. This is not breeding or full P03 acceptance. */
#include "p03a_fullslots_embedded.c"
#include <mgba/internal/gba/gba.h>
#include <mgba/internal/gba/savedata.h>
#include <mgba-util/vfs.h>

#define A_SCOPE "P03_ARCHIVE_NATIVE_UI_SAVE_RELOAD"
#define A_ITEM 347U
#define A_MENU 0x09539E49U
#define A_STATE_PTR 0x0203AA2CU
#define A_CALLBACK 0x080E5849U
#define A_MAX_FRAMES 18000U
#define A_HOF 0x082CU
#define A_MODE 0x0203EC00U

_Noreturn static void a_die(const char *s) { fprintf(stderr,"P03 archive: %s\n",s); exit(1); }
static void a_require(bool b,const char *s) { if(!b) a_die(s); }
#define DENY(name,type) static void name(struct mCore*c,uint32_t a,type v){(void)c;(void)a;(void)v;a_die("host write after observation barrier");}
DENY(a_deny8,uint8_t)
DENY(a_deny16,uint16_t)
DENY(a_deny32,uint32_t)
#define DENY_RAW(name,type) static void name(struct mCore*c,uint32_t a,int s,type v){(void)c;(void)a;(void)s;(void)v;a_die("host write after observation barrier");}
DENY_RAW(a_raw8,uint8_t)
DENY_RAW(a_raw16,uint16_t)
DENY_RAW(a_raw32,uint32_t)
static bool a_register(struct mCore*c,const char*n,const void*v){(void)c;(void)n;(void)v;a_die("host write after observation barrier");}
static void a_guard(struct mCore*c) {
    c->busWrite8=a_deny8;c->busWrite16=a_deny16;c->busWrite32=a_deny32;
    c->rawWrite8=a_raw8;c->rawWrite16=a_raw16;c->rawWrite32=a_raw32;c->writeRegister=a_register;
}
static void a_restore(struct mCore*c,const struct mCore*s) {
    c->busWrite8=s->busWrite8;c->busWrite16=s->busWrite16;c->busWrite32=s->busWrite32;
    c->rawWrite8=s->rawWrite8;c->rawWrite16=s->rawWrite16;c->rawWrite32=s->rawWrite32;c->writeRegister=s->writeRegister;
}
static void a_guard_check(const char *api) {
    struct mCore c={0};uint32_t v=0;a_guard(&c);
    if(!strcmp(api,"bus8"))c.busWrite8(&c,0,0);
    else if(!strcmp(api,"bus16"))c.busWrite16(&c,0,0);
    else if(!strcmp(api,"bus32"))c.busWrite32(&c,0,0);
    else if(!strcmp(api,"raw8"))c.rawWrite8(&c,0,0,0);
    else if(!strcmp(api,"raw16"))c.rawWrite16(&c,0,0,0);
    else if(!strcmp(api,"raw32"))c.rawWrite32(&c,0,0,0);
    else if(!strcmp(api,"register"))(void)c.writeRegister(&c,"pc",&v);
    exit(2);
}
static void a_flash_prepare(struct mCore*c) {
    /* mGBA 0.10.2 GBASavedataRTCWrite remaps on first trailer extension but
     * does not rebind currentBank. Do this BEFORE observation, preserving all
     * 128 KiB of game flash. Keep RTC, native saving and both banks enabled. */
    struct GBASavedata*s=&((struct GBA*)c->board)->memory.savedata;
    a_require(s->type==SAVEDATA_FLASH1M && s->data && s->currentBank,"flash type/bank unavailable");
    uintptr_t offset=(uintptr_t)s->currentBank-(uintptr_t)s->data;
    a_require(offset==0 || offset==0x10000,"flash bank offset invalid");
    uint8_t*before=malloc(0x20000);a_require(before!=NULL,"flash snapshot allocation");
    memcpy(before,s->data,0x20000);GBASavedataRTCWrite(s);s->currentBank=s->data+offset;
    a_require(!memcmp(before,s->data,0x20000),"RTC preparation changed game flash");
    a_require(s->vf->size(s->vf)==0x20010,"RTC trailer not reserved");free(before);
}
static bool a_field(struct mCore*c) {
    unsigned id=read8(c,P02S_PLAYER_AVATAR+5);
    return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD && p02s_continue_position(c)
        && read8(c,P02S_FIELD_LOCK)==0 && read8(c,P02S_QUEST_LOG_STATE)==0
        && read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)==0 && id<16
        && (read8(c,P02S_OBJECT_EVENTS+id*0x24)&1U)
        && read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_RUNNING_STATE_OFFSET)==0
        && read8(c,P02S_PLAYER_AVATAR+P02S_PLAYER_TILE_TRANSITION_STATE_OFFSET)==0;
}
static bool a_continue(struct mCore*c) {
    run_key_frames(c,0,P02S_TITLE_FRAMES);
    for(unsigned p=0;p<P02S_CONTINUE_PULSES;p++) {
        qol_press(c,p==0?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD || !p02s_continue_position(c))continue;
        run_key_frames(c,0,300);
        for(unsigned r=0;r<8;r++) {
            if(!read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) {
                run_key_frames(c,0,P02S_FIELD_SETTLE_FRAMES);unsigned stable=0;
                for(unsigned f=0;f<3600;f++) {
                    if(a_field(c)){if(++stable>=P02S_INPUT_READY_FRAMES)return true;}else stable=0;
                    run_key_frames(c,0,1);
                }
            }
            qol_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);
        }
        return false;
    }
    return false;
}
static void a_key_item(struct mCore*c) {
    unsigned s1=read32(c,QOL_SAVE_BLOCK1_SLOT),s2=read32(c,QOL_SAVE_BLOCK2_SLOT);
    a_require(p02s_ewram_pointer(s1)&&p02s_ewram_pointer(s2),"save block unavailable");
    uint16_t key=read16(c,s2+0xf20);
    for(unsigned i=0;i<30;i++){write16(c,s1+0x3b8+4*i,0);write16(c,s1+0x3ba+4*i,key);}
    write16(c,s1+0x3b8,A_ITEM);write16(c,s1+0x3ba,1^key);
}
static unsigned a_menu_count(struct mCore*c) {
    for(unsigned i=0;i<16;i++) {
        unsigned t=QOL_TASKS+i*QOL_TASK_SIZE;
        if(read8(c,t+4) && read32(c,t)==A_MENU)return read16(c,t+10);
    }
    return 0;
}
static bool a_locked_text(struct mCore*c) {
    for(unsigned i=0;i<128;i++) {
        unsigned v=read8(c,0x0953A870+i);
        if(read8(c,0x02021C88+i)!=v)return false;
        if(v==0xff)return i>0;
    }
    return false;
}
static void a_slots(struct mCore*c,unsigned species,unsigned level,const unsigned moves[4],const unsigned pp[4]) {
    a_require(p02s_data(c,P02S_MON_DATA_SPECIES2)==species && p02s_data(c,QOL_MON_DATA_LEVEL)==level,"species/level differs");
    a_require(p02s_data(c,P03F_PP_BONUSES)==0 && read8(c,QOL_PLAYER_PARTY_COUNT)==1,"party/PP Ups differs");
    for(unsigned i=0;i<4;i++) {
        unsigned m=p02s_data(c,QOL_MON_DATA_MOVE1+i),p=p02s_data(c,MON_DATA_PP1+i);
        fprintf(stderr,"slot=%u move=%u/%u pp=%u/%u\n",i,m,moves[i],p,pp[i]);
        a_require(m==moves[i] && p==pp[i],"learned/retained move or PP differs");
    }
    a_require(p02s_bag_exact(c,A_ITEM,1),"Move Memory item not retained exactly once");
}
static unsigned a_candidates(struct mCore*c,unsigned family,unsigned species,unsigned page,const unsigned known[4],unsigned out[40]) {
    unsigned count=0;
    if(family==0) {
        /* Same production provider is called only in fixture preparation.
         * Wrapper independently binds the expected existing normal learnset. */
        unsigned dst=0x0203e300;
        unsigned n=call_preserving(c,0x080432d1,QOL_PLAYER_PARTY,dst,0,0);
        a_require(n<=40,"normal fixture provider capacity");
        for(unsigned i=0;i<n;i++)out[count++]=read16(c,dst+2*i);
        return count;
    }
    unsigned index=family==3?0x0953a89a:0,table=family==3?0x0953b546:0;
    /* Exact tutor roots are supplied by the immutable Stage74 symbol table. */
    if(family==4){index=0x09548294U;table=0x09548F40U;}
    a_require(index && table,"unsupported family");
    unsigned start=read16(c,index+species*2),end=read16(c,index+(species+1)*2);
    start+=40*page;if(end>start+40)end=start+40;
    for(unsigned i=start;i<end;i++) {
        unsigned m=read16(c,table+2*i);bool skip=!m;
        for(unsigned k=0;k<4;k++)if(known[k]==m)skip=true;
        for(unsigned k=0;k<count;k++)if(out[k]==m)skip=true;
        if(!skip){a_require(count<40,"candidate capacity exceeded");out[count++]=m;}
    }
    return count;
}
struct ATrace {unsigned bag,mode_menu,mode_choice,party,page_menu,page_choice,list,ask,delete_ask,summary,selection,replaced,learned,giveup,locked,field;};
static unsigned a_stamp(struct mCore*c,unsigned start){return c->frameCounter(c)-start+1;}
static void a_list(struct mCore*c,unsigned p,unsigned count,const unsigned moves[40]) {
    a_require(p02s_ewram_pointer(p) && p+0xdd0<=0x02040000,"native allocation outside EWRAM");
    a_require(read8(c,p+0x1e3)==0,"native list corrupted selected party metadata");
    a_require(read8(c,p+0x1a)==count+1,"native candidate count differs");
    a_require(read32(c,0x03005ec0)==p+0x9f0,"native menu item pointer not relocated");
    for(unsigned i=0;i<count;i++) {
        a_require(read16(c,p+0xe8+2*i)==moves[i],"native candidate IDs overlap menu items");
        a_require(read32(c,p+0x9f0+8*i)==p+0xb40+16*i && read32(c,p+0x9f4+8*i)==i,"native list item binding differs");
        for(unsigned j=0;j<16;j++) {
            unsigned want=j==15?0xff:read8(c,0x090453c8+16*moves[i]+j);
            a_require(read8(c,p+0xb40+16*i+j)==want,"native move name bytes differ");
        }
    }
    a_require(read32(c,p+0x9f4+8*count)==0xfe,"native cancel entry missing");
}
/* action: 0 replace, 1 empty slot, 2 refuse teach, 3 cancel summary,
 * 4 cancel candidate list, 5 cancel page, 6 pre-HOF locked, 7 cancel mode. */
static struct ATrace a_scene(struct mCore*c,unsigned family,unsigned page,unsigned index,int slot,unsigned action,unsigned count,const unsigned moves[40]) {
    struct ATrace t={0};unsigned start=c->frameCounter(c),mode_down=0,page_down=0,list_down=0;
    bool list_selected=false,summary_selected=false,exit_list=false;unsigned stable=0,lastcb=0,laststate=999;
    a_require(p02s_enter_bag_physical(c,"archive_bag",A_ITEM),"normal Start/Bag input failed");t.bag=a_stamp(c,start);
    for(unsigned i=0;i<6 && read8(c,0x0203ac7a)!=1;i++)qol_press(c,QOL_KEY_RIGHT,120);
    a_require(read8(c,0x0203ac7a)==1,"key item pocket unreachable");
    qol_press(c,QOL_KEY_A,60);qol_press(c,QOL_KEY_A,120);
    for(unsigned f=0;f<A_MAX_FRAMES;f++) {
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),p=read32(c,A_STATE_PTR),state=999,stamp=a_stamp(c,start),menu=a_menu_count(c);
        if(cb==A_CALLBACK) {a_require(p02s_ewram_pointer(p),"native state unavailable");state=read8(c,p);}
        if(cb!=lastcb || state!=laststate) {
            fprintf(stderr,"frame=%u callback=%08x state=%u mode=%u\n",stamp,cb,state,read8(c,A_MODE));lastcb=cb;laststate=state;
        }
        if(menu==6 && !t.mode_menu)t.mode_menu=stamp;
        if(cb==P02S_CB2_PARTY && !t.party)t.party=stamp;
        if(menu>1 && menu<6 && !t.page_menu)t.page_menu=stamp;
        if((state==4 || state==6) && !t.list){a_list(c,p,count,moves);t.list=stamp;}
        if(state==8 && !t.ask)t.ask=stamp;
        if(state==18 && !t.delete_ask)t.delete_ask=stamp;
        if(cb==P03F_SUMMARY_CB && !t.summary)t.summary=stamp;
        if(state==30 && !t.replaced)t.replaced=stamp;
        if(state==31 && !t.learned)t.learned=stamp;
        if(state==13 && !t.giveup)t.giveup=stamp;
        if(t.mode_choice && a_locked_text(c) && !t.locked)t.locked=stamp;
        if(t.locked && action!=6)a_die("unlocked archive denied by stale comparison");
        bool route_done=(action==6?t.locked!=0:(action==5?t.page_choice!=0:(action==7?t.mode_choice!=0:(t.learned!=0 || t.giveup!=0))));
        if(route_done && a_field(c) && !menu && read8(c,A_MODE)==0) {
            if(++stable>=120){t.field=stamp;c->setKeys(c,0);return t;}
        }else stable=0;
        unsigned key=0;
        if(f%30==0) {
            if(menu==6) {
                if(action==7){key=QOL_KEY_B;t.mode_choice=stamp;}
                else if(!t.mode_choice){if(mode_down<family){key=QOL_KEY_DOWN;mode_down++;}else{key=QOL_KEY_A;t.mode_choice=stamp;}}
                else key=QOL_KEY_B;
            }else if(menu>1 && menu<6) {
                if(!t.page_choice){if(action==5){key=QOL_KEY_B;t.page_choice=stamp;}
                    else if(page_down<page){key=QOL_KEY_DOWN;page_down++;}else{key=QOL_KEY_A;t.page_choice=stamp;}}
                else key=QOL_KEY_B;
            }else if(cb==P02S_CB2_PARTY) {key=(t.learned || t.giveup || exit_list)?QOL_KEY_B:QOL_KEY_A;}
            else if(cb==A_CALLBACK) {
                if(state==4 || state==6) {
                    if(action==4 || exit_list){key=QOL_KEY_B;exit_list=true;}
                    else if(!list_selected){unsigned cursor=read8(c,p+0x9eb);
                        a_require(cursor==list_down,"candidate cursor did not follow physical input");
                        if(cursor<index){key=QOL_KEY_DOWN;list_down++;}
                        else{a_require(cursor==index,"wrong candidate selection");key=QOL_KEY_A;list_selected=true;}}
                    else {key=QOL_KEY_B;exit_list=true;}
                }else if(state==9 && action==2){key=QOL_KEY_B;exit_list=true;}
                else key=QOL_KEY_A;
            }else if(cb==P03F_SUMMARY_CB) {
                unsigned q=read32(c,QOL_SUMMARY_DATA_SLOT);
                a_require(p02s_ewram_pointer(q) && q+P03F_SUMMARY_STATE<0x02040000,"summary pointer invalid");
                if(p03f_task(c,P03F_SUMMARY_TASK) && read8(c,q+P03F_SUMMARY_STATE)==2 && !summary_selected) {
                    unsigned cursor=read8(c,P03F_SUMMARY_CURSOR);a_require(cursor<5,"summary cursor invalid");
                    if(action==3){key=QOL_KEY_B;summary_selected=true;t.selection=stamp;exit_list=true;}
                    else if(cursor!=(unsigned)slot)key=QOL_KEY_DOWN;
                    else{key=QOL_KEY_A;summary_selected=true;t.selection=stamp;}
                }
            }else if(t.mode_choice)key=QOL_KEY_A;
        }
        c->setKeys(c,key);c->runFrame(c);
    }
    c->setKeys(c,0);a_die("native archive route timed out");
}
static bool a_save(struct mCore*c) {
    unsigned counter=read32(c,P03_SAVE_COUNTER);qol_press(c,QOL_KEY_START,120);
    if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;
    if(!count || count>9 || cursor>=count)return false;
    for(unsigned i=0;i<count;i++)if(read8(c,QOL_START_MENU_ORDER+i)==P03_SAVE_ACTION)target=i;
    if(target==count)return false;
    for(unsigned i=0,n=(target+count-cursor)%count;i<n;i++)qol_press(c,QOL_KEY_DOWN,30);
    if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;
    qol_press(c,QOL_KEY_A,120);bool seen=false;
    for(unsigned i=0;i<32;i++) {
        unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==P03_SAVE_CALLBACK)seen=true;
        if(seen && cb==P03_SAVE_CALLBACK && read32(c,P03_SAVE_COUNTER)==counter+1 && a_field(c)) {
            run_key_frames(c,0,180);return a_field(c);
        }
        qol_press(c,QOL_KEY_A,180);
    }
    return false;
}
static void a_array(const unsigned a[4]){printf("[%u,%u,%u,%u]",a[0],a[1],a[2],a[3]);}
int main(int argc,char**argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=14)return 2;
    /* All numeric arguments are bound by the wrapper to existing ROM rows. */
    unsigned family=qol_number(argv[5],"archive argument"),species=qol_number(argv[6],"archive argument"),level=qol_number(argv[7],"archive argument"),page=qol_number(argv[8],"archive argument"),index=qol_number(argv[9],"archive argument");
    int slot=(int)qol_number(argv[10],"archive argument")-1;unsigned action=qol_number(argv[11],"archive argument"),expected=qol_number(argv[12],"archive argument"),expected_count=qol_number(argv[13],"archive argument");
    if((family!=0 && family!=3 && family!=4) || species>=1621 || !species || !level || level>100 || page>3 || index>=40 || slot>3 || action>7 || expected_count>40)return 2;
    char before_rom[65],h[65];sha256_file(argv[1],before_rom);sha256_file(argv[2],h);
    a_require(!strcmp(before_rom,argv[3]) && !strcmp(h,argv[4]),"ROM/seed identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);p03f_rtc_reserve(argv[2]);
    struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;static color_t video[240*160];c->setVideoBuffer(c,video,240);
    a_require(a_continue(c),"initial normal Continue failed");a_flash_prepare(c);
    a_require(p02s_install_field_fixture(c),"fixture boundary failed");p02s_enable_national_dex(c);
    clear_parties(c);create_mon(c,QOL_PLAYER_PARTY,species,level);write8(c,QOL_PLAYER_PARTY_COUNT,1);
    unsigned before[4]={33,81,45,52},before_pp[4]={7,8,9,10};
    if(action==1){before[2]=before[3]=before_pp[2]=before_pp[3]=0;slot=2;}
    for(unsigned i=0;i<4;i++){p02s_set_data(c,QOL_MON_DATA_MOVE1+i,before[i]);p02s_set_data(c,MON_DATA_PP1+i,before_pp[i]);}
    (void)call_preserving(c,action==6?QOL_FLAG_CLEAR:QOL_FLAG_SET,A_HOF,0,0,0);a_key_item(c);
    a_require(call_preserving(c,QOL_FLAG_GET,A_HOF,0,0,0)==(action==6?0U:1U),"HOF fixture differs");
    a_slots(c,species,level,before,before_pp);
    unsigned candidates[40]={0},count=a_candidates(c,family,species,page,before,candidates);
    a_require(count==expected_count,"fixed candidate row/count differs");
    a_require((action>=4 || (index<count && candidates[index]==expected)),"fixed selected move differs");
    unsigned after[4],after_pp[4];memcpy(after,before,sizeof(after));memcpy(after_pp,before_pp,sizeof(after_pp));
    bool learns=action<2;unsigned learned_pp=0;
    if(learns) {a_require(slot>=0,"learning slot missing");unsigned table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
        learned_pp=read8(c,table+expected*BATTLE_CORE_BATTLE_MOVE_SIZE+4);a_require(learned_pp>0 && learned_pp<=64,"canonical PP invalid");
        after[slot]=expected;after_pp[slot]=learned_pp;}
    struct mCore saved=*c;a_guard(c);struct ATrace t=a_scene(c,family,page,index,slot,action,count,candidates);a_restore(c,&saved);
    a_require(t.bag && t.mode_menu && t.mode_choice && t.field,"Bag/mode/field witness missing");
    a_require((t.party!=0)==(action<=5) && (t.list!=0)==(action<5),"party/list route differs");
    a_require((t.ask!=0)==(action<4) && (t.summary!=0)==(action==0 || action==3),"learning/summary route differs");
    a_require((t.replaced!=0)==(action==0) && (t.learned!=0)==learns,"native learn/replace route differs");
    a_require((t.locked!=0)==(action==6),"HOF denial message differs");
    a_slots(c,species,level,after,after_pp);unsigned counter=read32(c,P03_SAVE_COUNTER);
    a_guard(c);a_require(a_save(c),"normal Start-menu save failed");a_restore(c,&saved);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1,"save counter differs");a_slots(c,species,level,after,after_pp);
    qol_close(c);c=NULL;qol_log_core=NULL;fprintf(stderr,"original core destroyed; new core normal Continue\n");
    c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,video,240);saved=*c;a_guard(c);
    a_require(a_continue(c),"new core normal Continue failed");a_restore(c,&saved);
    a_slots(c,species,level,after,after_pp);a_require(read32(c,P03_SAVE_COUNTER)==counter+1,"new core save counter differs");
    a_require(call_preserving(c,QOL_FLAG_GET,A_HOF,0,0,0)==(action==6?0U:1U),"HOF persistence differs");
    qol_close(c);c=NULL;qol_log_core=NULL;sha256_file(argv[1],h);a_require(!strcmp(h,before_rom),"ROM modified");
    a_require(log_problem_count==0,"mGBA warning/error observed");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"rom_sha256\":\"%s\",\"family\":%u,\"species\":%u,\"level\":%u,\"page\":%u,\"index\":%u,\"action\":%u,\"learned_slot\":%d,\"candidate_count\":%u,\"selected_move\":%u,\"canonical_pp\":%u,\"moves_before\":",A_SCOPE,before_rom,family,species,level,page,index,action,learns?slot:-1,count,expected,learned_pp);
    a_array(before);printf(",\"pp_before\":");a_array(before_pp);printf(",\"moves_after\":");a_array(after);printf(",\"pp_after\":");a_array(after_pp);
    printf(",\"normal_bag_input\":true,\"host_write_barriers\":3,\"normal_save_menu\":true,\"fresh_core_normal_continue\":true,\"save_counter_delta\":1,\"rtc_flash_bytes_preserved\":131072,\"breeding_e2e\":false,\"full_p03_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"witness\":{");
#define W(name) printf("\""#name"\":%u,",t.name)
    W(bag);W(mode_menu);W(mode_choice);W(party);W(page_menu);W(page_choice);W(list);W(ask);W(delete_ask);W(summary);W(selection);W(replaced);W(learned);W(giveup);W(locked);
    printf("\"field\":%u}}\n",t.field);return 0;
}
