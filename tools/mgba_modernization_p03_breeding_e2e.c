/* Stage82: real daycare dialogue -> steps -> egg claim -> Save/Continue ->
 * steps -> native hatch -> Save/Continue. Parents and starting map are an
 * isolated fixture; no claim of natural capture, all species or full P03.
 * All seven mCore host-write APIs are denied in every observed phase. */
#include "p03b_archive_embedded.c"

#define B_SCOPE "P03_DAYCARE_INHERITANCE_HATCH_SAVE_RELOAD"
#define QOL_KEY_LEFT 32U
#define B_CONTEXT 0x03000EA8U
#define B_HATCH_CALLBACK 0x080468C1U
#define B_HATCH_DATA 0x03000E74U
#define B_DAYCARE_OFFSET 0x2F80U
#define B_CLOCK_OFFSET 0x309AU
#define B_CHILD (QOL_PLAYER_PARTY + 100U)
#define B_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"
#define B_SEED_SHA "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"

struct BCase {
    const char *name;
    unsigned father[4], mother[4], father_item, mother_item, child[4];
};
static const struct BCase b_cases[] = {
    {"lightball-father", {175,33,0,0}, {273,45,0,0},202,0,{84,175,273,344}},
    {"lightball-mother", {175,33,0,0}, {273,45,0,0},0,202,{84,175,273,344}},
    {"both-parents", {175,33,0,0}, {273,45,0,0},0,0,{39,84,175,273}},
    {"father-only", {175,33,0,0}, {45,52,0,0},0,0,{39,84,175,0}},
    {"mother-only", {33,52,0,0}, {273,45,0,0},0,0,{39,84,273,0}},
    {"no-eligible-moves", {33,52,0,0}, {45,81,0,0},0,0,{39,84,0,0}},
    {"same-move-both", {175,33,0,0}, {175,45,0,0},0,0,{39,84,175,0}},
    {"lightball-only", {33,52,0,0}, {45,81,0,0},202,0,{39,84,344,0}},
};
struct BTrace {
    unsigned deposit_menu, first_deposit, second_deposit, generated, claim_menu;
    unsigned claimed, egg_saved, egg_reloaded, hatch_begin, nickname, hatch_end;
    unsigned hatch_saved, hatch_reloaded;
};
static struct BTrace b_trace;
static unsigned b_steps, b_frames, b_hatch_frames, b_hatch_states, b_native_hatch_saves;
static bool b_hatching, b_hatched;
static color_t b_video[240U * 160U];

static unsigned b_save1(struct mCore *c) {
    unsigned s = read32(c,QOL_SAVE_BLOCK1_SLOT);
    a_require(p02s_ewram_pointer(s),"breeding save1 unavailable");
    return s;
}
static bool b_field(struct mCore *c) {
    unsigned id = read8(c,P02S_PLAYER_AVATAR+5U);
    return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD
        && !read8(c,P02S_FIELD_LOCK) && !read8(c,P02S_QUEST_LOG_STATE)
        && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE) && id<16U
        && (read8(c,P02S_OBJECT_EVENTS+id*0x24U)&1U)
        && !read8(c,P02S_PLAYER_AVATAR+2U) && !read8(c,P02S_PLAYER_AVATAR+3U);
}
static void b_position(struct mCore *c,unsigned g,unsigned m,unsigned x,unsigned y) {
    unsigned s=b_save1(c);
    a_require(b_field(c) && read8(c,s+4U)==g && read8(c,s+5U)==m
        && read16(c,s)==x && read16(c,s+2U)==y,"breeding physical map/position differs");
}
static void b_frame(struct mCore *c,unsigned key) {
    unsigned old_counter=b_hatching?read32(c,P03_SAVE_COUNTER):0U;
    c->setKeys(c,key);c->runFrame(c);++b_frames;
    if(b_hatching && read32(c,P03_SAVE_COUNTER)!=old_counter) {
        a_require(read32(c,P03_SAVE_COUNTER)==old_counter+1U,"native hatch save counter jump");
        ++b_native_hatch_saves;
    }
    a_require(b_frames<=600000U,"breeding total frame budget exceeded");
}
static void b_frames_run(struct mCore *c,unsigned key,unsigned n) {
    for(unsigned i=0;i<n;++i)b_frame(c,key);
}
static void b_press(struct mCore *c,unsigned key,unsigned settle) {
    b_frames_run(c,key,2U);b_frames_run(c,0U,settle);
}
static void b_state(struct mCore *c,const char *label) {
    unsigned s=b_save1(c);
    fprintf(stderr,"BREED %s map=%u/%u xy=%u,%u party=%u queue=%u clock=%u steps=%u frame=%u cb=%08x\n",
        label,read8(c,s+4U),read8(c,s+5U),read16(c,s),read16(c,s+2U),
        read8(c,QOL_PLAYER_PARTY_COUNT),read8(c,QOL_LEDGER+512U),read8(c,s+B_CLOCK_OFFSET),
        b_steps,b_frames,read32(c,BATTLE_CORE_MAIN_CALLBACK2));
}
static void b_wait(struct mCore *c) {
    unsigned stable=0;
    for(unsigned i=0;i<9000U;++i) {
        unsigned key=0,cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2);
        if(cb==B_HATCH_CALLBACK) {
            a_require(b_hatching,"unexpected hatch outside measured walking phase");
            unsigned p=read32(c,B_HATCH_DATA);
            a_require(p02s_ewram_pointer(p),"native hatch state unavailable");
            unsigned state=read8(c,p+2U);
            a_require(state<16U,"native hatch state invalid");
            if(!b_trace.hatch_begin)b_trace.hatch_begin=b_frames+1U;
            b_hatch_states|=1U<<state;++b_hatch_frames;
            /* Refuse nickname only after the prompt's native state is visible. */
            if(state==10U && !b_trace.nickname)b_trace.nickname=b_frames+1U;
            if(i%90U==0U)key=state>=9U?QOL_KEY_B:QOL_KEY_A;
        } else if(b_hatching && read8(c,P02S_FIELD_LOCK) && i%90U==0U) {
            key=QOL_KEY_A; /* Ordinary pre-hatch "Oh?" script text. */
        }
        b_frame(c,key);
        if(b_field(c)) {
            if(++stable==12U) {
                if(b_trace.hatch_begin) {
                    b_hatched=true;
                    if(!b_trace.hatch_end)b_trace.hatch_end=b_frames;
                }
                return;
            }
        } else stable=0;
    }
    b_state(c,"not-idle");a_die("breeding field did not become idle");
}
static void b_step(struct mCore *c,unsigned key) {
    a_require(b_field(c),"breeding step outside idle field");
    unsigned s=b_save1(c),x=read16(c,s),y=read16(c,s+2U);
    unsigned g=read8(c,s+4U),m=read8(c,s+5U);bool moved=false;
    for(unsigned f=0;f<90U;++f) {
        b_frame(c,key);s=b_save1(c);
        if(read16(c,s)!=x || read16(c,s+2U)!=y || read8(c,s+4U)!=g || read8(c,s+5U)!=m) {
            moved=true;break;
        }
    }
    c->setKeys(c,0U);a_require(moved,"breeding physical step blocked");
    ++b_steps;b_wait(c);
}
static void b_to(struct mCore *c,unsigned x,unsigned y) {
    for(unsigned n=0;n<60U;++n) {
        unsigned s=b_save1(c),cx=read16(c,s),cy=read16(c,s+2U);
        if(cx==x && cy==y)return;
        b_step(c,cy<y?QOL_KEY_DOWN:cy>y?QOL_KEY_UP:cx<x?QOL_KEY_RIGHT:QOL_KEY_LEFT);
    }
    a_die("breeding physical walk target not reached");
}
static void b_dialog(struct mCore *c,bool deposit) {
    b_press(c,QOL_KEY_A,90U);bool locked=false;
    for(unsigned f=0;f<8000U;++f) {
        unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),count=read8(c,QOL_PLAYER_PARTY_COUNT);
        if(read8(c,P02S_FIELD_LOCK))locked=true;
        if(deposit) {
            if(cb==P02S_CB2_PARTY && !b_trace.deposit_menu)b_trace.deposit_menu=b_frames+1U;
            if(count==2U && !b_trace.first_deposit)b_trace.first_deposit=b_frames+1U;
            if(count==1U && !b_trace.second_deposit)b_trace.second_deposit=b_frames+1U;
        } else {
            if(locked && !b_trace.claim_menu)b_trace.claim_menu=b_frames+1U;
            if(count==2U && !read8(c,QOL_LEDGER+512U) && !b_trace.claimed)b_trace.claimed=b_frames+1U;
        }
        if(locked && b_field(c)) {b_wait(c);b_state(c,deposit?"deposited":"claimed");return;}
        b_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }
    a_die("breeding ordinary conversation timed out");
}
static unsigned b_data(struct mCore *c,unsigned mon,unsigned field) {
    return call_preserving(c,BATTLE_CORE_GET_MON_DATA,mon,field,0U,0U);
}
static void b_create(struct mCore *c,unsigned dst,unsigned pid,unsigned ot) {
    /* The only initial individual construction, before the observation guard. */
    struct CpuState original=capture_cpu_state(c);
    uint32_t args[4]={1U,pid,1U,ot};struct HostCallStack stack;
    begin_host_call_stack(c,&stack,args,4U);
    (void)call_rom_args(c,BATTLE_CORE_CREATE_MON,dst,25U,20U,31U);
    bool ok=restore_host_call_stack(c,&stack);restore_cpu_state(c,&original);
    a_require(ok && b_data(c,dst,11U)==25U && b_data(c,dst,0U)==pid
        && b_data(c,dst,1U)==ot,"breeding fixture identity differs");
}
static unsigned b_pp(struct mCore *c,unsigned move) {
    if(!move)return 0U;
    unsigned table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    a_require(table>=0x08000000U && table<0x0A000000U,"canonical move table unavailable");
    unsigned pp=read8(c,table+move*BATTLE_CORE_BATTLE_MOVE_SIZE+4U);
    a_require(pp>0U && pp<=64U,"canonical egg move PP invalid");return pp;
}
static void b_child(struct mCore *c,const struct BCase *v,unsigned egg,unsigned pp[4]) {
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==2U && b_data(c,QOL_PLAYER_PARTY,11U)==649U,
              "breeding non-egg party identity/count differs");
    a_require(b_data(c,B_CHILD,11U)==24U && b_data(c,B_CHILD,45U)==egg
        && b_data(c,B_CHILD,56U)==1U && b_data(c,B_CHILD,12U)==0U
        && b_data(c,B_CHILD,21U)==0U,"child species/egg/level/item/PP Ups differs");
    for(unsigned k=0;k<4U;++k) {
        pp[k]=b_pp(c,v->child[k]);
        unsigned move=b_data(c,B_CHILD,13U+k),actual=b_data(c,B_CHILD,17U+k);
        fprintf(stderr,"CHILD egg=%u slot=%u move=%u/%u pp=%u/%u\n",egg,k,move,v->child[k],actual,pp[k]);
        a_require(move==v->child[k] && actual==pp[k],"egg inheritance order/duplicate exclusion/canonical PP differs");
    }
}
struct BSnapshot {uint8_t party[200],daycare[284],queue[402];unsigned count;};
static void b_copy(struct mCore *c,unsigned address,uint8_t *out,unsigned size) {
    for(unsigned i=0;i<size;++i)out[i]=read8(c,address+i);
}
static struct BSnapshot b_snapshot(struct mCore *c) {
    struct BSnapshot s;
    b_copy(c,QOL_PLAYER_PARTY,s.party,sizeof(s.party));
    b_copy(c,b_save1(c)+B_DAYCARE_OFFSET,s.daycare,sizeof(s.daycare));
    b_copy(c,QOL_LEDGER+512U,s.queue,sizeof(s.queue));
    s.count=read8(c,QOL_PLAYER_PARTY_COUNT);return s;
}
static void b_snapshot_check(struct mCore *c,const struct BSnapshot *s) {
    struct BSnapshot now=b_snapshot(c);
    a_require(now.count==s->count && !memcmp(now.party,s->party,sizeof(s->party))
        && !memcmp(now.daycare,s->daycare,sizeof(s->daycare))
        && !memcmp(now.queue,s->queue,sizeof(s->queue)),"normal save/restart changed child/parents/pending eggs");
}
static bool b_save(struct mCore *c) {
    unsigned counter=read32(c,P03_SAVE_COUNTER);b_press(c,QOL_KEY_START,120U);
    if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    unsigned count=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=count;
    if(!count || count>9U || cursor>=count)return false;
    for(unsigned i=0;i<count;++i)if(read8(c,QOL_START_MENU_ORDER+i)==P03_SAVE_ACTION)target=i;
    if(target==count)return false;
    for(unsigned i=0,n=(target+count-cursor)%count;i<n;++i)b_press(c,QOL_KEY_DOWN,30U);
    if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;
    b_press(c,QOL_KEY_A,120U);bool seen=false;
    for(unsigned i=0;i<32U;++i) {
        unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==P03_SAVE_CALLBACK)seen=true;
        if(seen && cb==P03_SAVE_CALLBACK && read32(c,P03_SAVE_COUNTER)==counter+1U && b_field(c)) {
            b_frames_run(c,0U,180U);return b_field(c);
        }
        b_press(c,QOL_KEY_A,180U);
    }
    return false;
}
static bool b_continue(struct mCore *c) {
    b_frames_run(c,0U,P02S_TITLE_FRAMES);
    for(unsigned p=0;p<P02S_CONTINUE_PULSES;++p) {
        b_press(c,p==0U?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);
        if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD)continue;
        b_frames_run(c,0U,300U);
        for(unsigned r=0;r<8U;++r) {
            if(!read8(c,P02S_QUEST_LOG_STATE) && !read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)) {b_wait(c);return true;}
            b_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);
        }
        return false;
    }
    return false;
}
static struct mCore *b_restart(struct mCore *c,const char *rom,const char *save) {
    qol_close(c);qol_log_core=NULL;
    fprintf(stderr,"original core destroyed; new core boot and normal Continue\n");
    c=qol_open(rom,save);qol_log_core=c;c->setVideoBuffer(c,b_video,240U);return c;
}
static const struct BCase *b_case(const char *name) {
    for(unsigned i=0;i<sizeof(b_cases)/sizeof(b_cases[0]);++i)
        if(!strcmp(name,b_cases[i].name))return &b_cases[i];
    return NULL;
}
int main(int argc,char **argv) {
    if(argc==3 && !strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=6)return 2;
    const struct BCase *v=b_case(argv[5]);if(!v)return 2;
    char rom_sha[65],seed_sha[65],after[65];sha256_file(argv[1],rom_sha);sha256_file(argv[2],seed_sha);
    a_require(!strcmp(rom_sha,B_ROM_SHA) && !strcmp(rom_sha,argv[3])
        && !strcmp(seed_sha,B_SEED_SHA) && !strcmp(seed_sha,argv[4]),"breeding ROM/seed identity differs");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);struct mCore *c=qol_open(argv[1],argv[2]);qol_log_core=c;
    c->setVideoBuffer(c,b_video,240U);a_require(a_continue(c),"breeding initial normal Continue failed");
    a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,35U,0U,2U,3U);run_key_frames(c,0U,900U);
    b_position(c,35U,0U,2U,3U);
    clear_parties(c);b_create(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U);
    b_create(c,QOL_PLAYER_PARTY+100U,0x34567801U,0x99887766U);
    create_mon(c,QOL_PLAYER_PARTY+200U,649U,20U);write8(c,QOL_PLAYER_PARTY_COUNT,3U);
    const unsigned *moves[2]={v->father,v->mother};unsigned items[2]={v->father_item,v->mother_item};
    for(unsigned p=0;p<2U;++p) {
        for(unsigned k=0;k<4U;++k) {
            set_mon_data_u32(c,QOL_PLAYER_PARTY+100U*p,13U+k,moves[p][k]);
            set_mon_data_u32(c,QOL_PLAYER_PARTY+100U*p,17U+k,moves[p][k]?5U:0U);
        }
        set_mon_data_u32(c,QOL_PLAYER_PARTY+100U*p,12U,items[p]);
    }
    unsigned s=b_save1(c);
    for(unsigned i=0;i<284U;++i)write8(c,s+B_DAYCARE_OFFSET+i,0U);
    (void)call_preserving(c,QOL_FLAG_CLEAR,0x266U,0U,0U,0U);
    (void)call_preserving(c,QOL_FLAG_CLEAR,QOL_FLAG_EGG_BASKET,0U,0U,0U);
    write8(c,QOL_LEDGER+512U,0U);write8(c,QOL_LEDGER+513U,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0U,0U,0U);
    /* Fixture ends here. No injected scripts/specials/steps/egg flags below. */
    struct mCore saved=*c;a_guard(c);b_press(c,QOL_KEY_UP,30U);b_dialog(c,true);
    a_require(read8(c,QOL_PLAYER_PARTY_COUNT)==1U,"ordinary dialogue did not deposit both parents");
    a_require(b_trace.deposit_menu && b_trace.deposit_menu<b_trace.first_deposit
        && b_trace.first_deposit<b_trace.second_deposit,"two ordinary deposit transitions not observed");
    b_to(c,2U,5U);unsigned generated_start=b_steps;
    for(unsigned z=0;z<4096U;++z) {
        b_step(c,read16(c,b_save1(c))==2U?QOL_KEY_RIGHT:QOL_KEY_LEFT);
        if(read8(c,QOL_LEDGER+512U)==1U) {b_trace.generated=b_frames;break;}
    }
    a_require(b_trace.generated && !read16(c,b_save1(c)+0x3098U),"physical breeding did not produce one queued egg");
    unsigned generation_steps=b_steps-generated_start;b_state(c,"generated");
    b_to(c,4U,6U);b_step(c,QOL_KEY_DOWN);b_step(c,QOL_KEY_DOWN);b_position(c,3U,37U,3U,24U);
    b_to(c,3U,27U);b_to(c,8U,27U);b_press(c,QOL_KEY_UP,30U);b_dialog(c,false);
    b_position(c,3U,37U,8U,27U);a_require(b_trace.claimed && !read8(c,QOL_LEDGER+512U),"ordinary egg claim missing");
    a_restore(c,&saved);unsigned pp[4];b_child(c,v,1U,pp);
    unsigned initial_cycles=b_data(c,B_CHILD,32U);a_require(initial_cycles==10U,"Pichu native egg cycles changed");
    unsigned personality=b_data(c,B_CHILD,0U),ot_id=b_data(c,B_CHILD,1U);
    struct BSnapshot egg=b_snapshot(c);unsigned counter=read32(c,P03_SAVE_COUNTER),initial_counter=counter;
    a_guard(c);a_require(b_save(c),"ordinary egg save failed");b_trace.egg_saved=b_frames;
    b_snapshot_check(c,&egg);a_restore(c,&saved);
    c=b_restart(c,argv[1],argv[2]);saved=*c;a_guard(c);
    a_require(b_continue(c),"new core egg Continue failed");b_trace.egg_reloaded=b_frames;
    b_position(c,3U,37U,8U,27U);b_snapshot_check(c,&egg);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1U,"egg save counter not persisted exactly once");
    a_restore(c,&saved);b_child(c,v,1U,pp);a_guard(c);
    b_to(c,3U,27U);b_to(c,3U,24U);b_step(c,QOL_KEY_UP);b_position(c,35U,0U,4U,7U);
    b_to(c,2U,5U);unsigned hatch_start=b_steps,hatch_clock=read8(c,b_save1(c)+B_CLOCK_OFFSET);
    a_restore(c,&saved);unsigned cycles=b_data(c,B_CHILD,32U);a_guard(c);
    a_require(cycles==initial_cycles,"egg cycles changed before measured hatch walk");b_hatching=true;
    for(unsigned z=0;z<8192U && !b_hatched;++z) {
        b_step(c,read16(c,b_save1(c))==2U?QOL_KEY_RIGHT:QOL_KEY_LEFT);
        if(z%256U==0U)b_state(c,"hatch-walk");
    }
    b_hatching=false;unsigned hatch_steps=b_steps-hatch_start;
    a_require(b_hatched && b_trace.nickname && b_trace.hatch_begin<b_trace.nickname
        && b_trace.nickname<b_trace.hatch_end,"native hatch/nickname/field sequence missing");
    a_require(hatch_steps==(cycles+1U)*256U-hatch_clock-1U
        && read8(c,b_save1(c)+B_CLOCK_OFFSET)==255U,"native egg cycle/physical step cadence differs");
    a_restore(c,&saved);b_child(c,v,0U,pp);
    a_require(b_data(c,B_CHILD,0U)==personality && b_data(c,B_CHILD,1U)==ot_id,"hatch changed individual identity");
    struct BSnapshot hatched=b_snapshot(c);counter=read32(c,P03_SAVE_COUNTER);
    a_guard(c);a_require(b_save(c),"ordinary hatched save failed");b_trace.hatch_saved=b_frames;
    b_snapshot_check(c,&hatched);a_restore(c,&saved);
    c=b_restart(c,argv[1],argv[2]);saved=*c;a_guard(c);
    a_require(b_continue(c),"new core hatched Continue failed");b_trace.hatch_reloaded=b_frames;
    b_position(c,35U,0U,3U,5U);b_snapshot_check(c,&hatched);
    fprintf(stderr,"COUNTERS initial=%u before_hatched_save=%u after_hatched_reload=%u\n",initial_counter,counter,read32(c,P03_SAVE_COUNTER));
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1U && counter==initial_counter+2U
        && b_native_hatch_saves==1U,"two manual saves plus native hatch registration not persisted exactly");
    a_restore(c,&saved);b_child(c,v,0U,pp);b_state(c,"done");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);
    a_require(!strcmp(rom_sha,after) && log_problem_count==0U,"ROM changed or emulator warning/error");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",B_SCOPE,v->name,rom_sha);
    printf("\"child_species\":24,\"child_level\":1,\"moves\":");a_array(v->child);printf(",\"pp\":");a_array(pp);
    printf(",\"father_item\":%u,\"mother_item\":%u,\"ordinary_deposit\":true,\"ordinary_claim\":true,\"native_hatch\":true,",v->father_item,v->mother_item);
    printf("\"egg_and_hatched_save_reload\":true,\"parent_queue_byte_identity\":true,\"fresh_cores\":3,\"manual_save_counter_delta\":2,\"native_hatch_save_counter_delta\":1,\"total_save_counter_delta\":3,\"host_write_barriers\":7,\"rtc_flash_bytes_preserved\":131072,");
    printf("\"initial_egg_cycles\":%u,\"generation_steps\":%u,\"hatch_clock_start\":%u,\"hatch_steps\":%u,\"hatch_callback_frames\":%u,\"hatch_state_mask\":%u,\"total_frames\":%u,",initial_cycles,generation_steps,hatch_clock,hatch_steps,b_hatch_frames,b_hatch_states,b_frames);
    printf("\"parent_fixture_only\":true,\"all_breeding_paths_accepted\":false,\"full_p03_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"witness\":{");
#define BW(name) printf("\""#name"\":%u,",b_trace.name)
    BW(deposit_menu);BW(first_deposit);BW(second_deposit);BW(generated);BW(claim_menu);BW(claimed);
    BW(egg_saved);BW(egg_reloaded);BW(hatch_begin);BW(nickname);BW(hatch_end);BW(hatch_saved);
    printf("\"hatch_reloaded\":%u}}\n",b_trace.hatch_reloaded);return 0;
}
