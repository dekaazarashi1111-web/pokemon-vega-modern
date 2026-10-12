/* Stage82: 預かり屋のFIFO生成、手持ち/PC満杯の通常受取、保存と新core。
 * 親・開始位置・PC占有はfixture。観測開始後のhost書込/ROM呼出はゼロ。 */
#include "p03bc_archive_embedded.c"
#define BC_SCOPE "P03_DAYCARE_CAPACITY_FIFO_COLD_SAVE"
#define BC_ROM_SHA "e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d"
#define BC_SEED_SHA "f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb"
#define BC_STORAGE_SLOT 0x03005050U
#define BC_PC_BYTES (14U*30U*80U)
#define BC_QUEUE (QOL_LEDGER+512U)
#define BC_LEFT 32U
static unsigned bc_frames,bc_steps,bc_locked_dialogues;
static unsigned bc_deposit_menu,bc_first_deposit,bc_second_deposit,bc_generated;
static unsigned bc_cap_checked,bc_claim[3],bc_saved[2],bc_reloaded[2],bc_retry;
static color_t bc_video[240U*160U];
static unsigned bc_save1(struct mCore*c){unsigned p=read32(c,QOL_SAVE_BLOCK1_SLOT);a_require(p02s_ewram_pointer(p),"capacity save absent");return p;}
static unsigned bc_storage(struct mCore*c){unsigned p=read32(c,BC_STORAGE_SLOT);a_require(p>=0x02000000U&&p+4U+BC_PC_BYTES<=0x02040000U,"capacity PC pointer invalid");return p+4U;}
static unsigned bc_count(struct mCore*c){return read8(c,QOL_PLAYER_PARTY_COUNT);}
static unsigned bc_queue_count(struct mCore*c){return read8(c,BC_QUEUE);}
static bool bc_field(struct mCore*c){unsigned id=read8(c,P02S_PLAYER_AVATAR+5U);return read32(c,BATTLE_CORE_MAIN_CALLBACK2)==P02S_CB2_FIELD&&!read8(c,P02S_FIELD_LOCK)&&!read8(c,P02S_QUEST_LOG_STATE)&&!read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)&&id<16U&&(read8(c,P02S_OBJECT_EVENTS+id*0x24U)&1U)&&!read8(c,P02S_PLAYER_AVATAR+2U)&&!read8(c,P02S_PLAYER_AVATAR+3U);}
static void bc_copy(struct mCore*c,unsigned p,uint8_t*out,unsigned n){for(unsigned i=0;i<n;++i)out[i]=read8(c,p+i);}
static void bc_equal(struct mCore*c,unsigned p,const uint8_t*want,unsigned n,const char*msg){for(unsigned i=0;i<n;++i)if(read8(c,p+i)!=want[i]){fprintf(stderr,"capacity mismatch address=%08x offset=%u got=%u expected=%u\n",p,i,read8(c,p+i),want[i]);a_die(msg);}}
static void bc_frame(struct mCore*c,unsigned key){c->setKeys(c,key);c->runFrame(c);++bc_frames;a_require(bc_frames<=700000U,"capacity frame budget exceeded");a_require(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=0x080468C1U,"unexpected hatch in capacity-only case");}
static void bc_run(struct mCore*c,unsigned key,unsigned n){for(unsigned i=0;i<n;++i)bc_frame(c,key);}
static void bc_press(struct mCore*c,unsigned key,unsigned n){bc_run(c,key,2U);bc_run(c,0U,n);}
static void bc_state(struct mCore*c,const char*label){unsigned p=bc_save1(c);fprintf(stderr,"CAPACITY %s frame=%u steps=%u map=%u/%u xy=%u,%u party=%u queue=%u head=%u cb=%08x\n",label,bc_frames,bc_steps,read8(c,p+4U),read8(c,p+5U),read16(c,p),read16(c,p+2U),bc_count(c),bc_queue_count(c),read8(c,BC_QUEUE+1U),read32(c,BATTLE_CORE_MAIN_CALLBACK2));}
static void bc_wait(struct mCore*c){unsigned stable=0;for(unsigned i=0;i<9000U;++i){bc_frame(c,0U);if(bc_field(c)){if(++stable==12U)return;}else stable=0;}bc_state(c,"not-idle");a_die("capacity field not idle");}
static void bc_position(struct mCore*c,unsigned g,unsigned m,unsigned x,unsigned y){unsigned p=bc_save1(c);a_require(bc_field(c)&&read8(c,p+4U)==g&&read8(c,p+5U)==m&&read16(c,p)==x&&read16(c,p+2U)==y,"capacity physical map/position differs");}
static void bc_step(struct mCore*c,unsigned key){a_require(bc_field(c),"capacity step outside idle field");unsigned p=bc_save1(c),x=read16(c,p),y=read16(c,p+2U),g=read8(c,p+4U),m=read8(c,p+5U);bool moved=false;for(unsigned i=0;i<90U;++i){bc_frame(c,key);p=bc_save1(c);if(read16(c,p)!=x||read16(c,p+2U)!=y||read8(c,p+4U)!=g||read8(c,p+5U)!=m){moved=true;break;}}c->setKeys(c,0U);a_require(moved,"capacity physical step blocked");++bc_steps;bc_wait(c);}
static void bc_to(struct mCore*c,unsigned x,unsigned y){for(unsigned i=0;i<60U;++i){unsigned p=bc_save1(c),cx=read16(c,p),cy=read16(c,p+2U);if(cx==x&&cy==y)return;bc_step(c,cy<y?QOL_KEY_DOWN:cy>y?QOL_KEY_UP:cx<x?QOL_KEY_RIGHT:BC_LEFT);}a_die("capacity walking destination not reached");}
static void bc_dialogue(struct mCore*c,bool deposit){
    bc_press(c,QOL_KEY_A,90U);bool locked=false;
    for(unsigned f=0;f<10000U;++f){unsigned cb=read32(c,BATTLE_CORE_MAIN_CALLBACK2),count=bc_count(c);
        if(read8(c,P02S_FIELD_LOCK))locked=true;
        if(deposit){if(cb==P02S_CB2_PARTY&&!bc_deposit_menu)bc_deposit_menu=bc_frames+1U;if(count==5U&&!bc_first_deposit)bc_first_deposit=bc_frames+1U;if(count==4U&&!bc_second_deposit)bc_second_deposit=bc_frames+1U;}
        if(locked&&bc_field(c)){++bc_locked_dialogues;bc_wait(c);bc_state(c,deposit?"deposited":"dialogue-ended");return;}
        bc_frame(c,f%90U==0U?QOL_KEY_A:0U);
    }bc_state(c,"dialogue-timeout");a_die("capacity ordinary dialogue timed out");
}
static void bc_create_parent(struct mCore*c,unsigned dst,unsigned pid,unsigned ot){struct CpuState state=capture_cpu_state(c);uint32_t args[4]={1U,pid,1U,ot};struct HostCallStack stack;begin_host_call_stack(c,&stack,args,4U);(void)call_rom_args(c,BATTLE_CORE_CREATE_MON,dst,25U,20U,31U);bool ok=restore_host_call_stack(c,&stack);restore_cpu_state(c,&state);a_require(ok&&call_preserving(c,BATTLE_CORE_GET_MON_DATA,dst,11U,0U,0U)==25U,"capacity parent construction failed");}
static bool bc_save(struct mCore*c){
    unsigned counter=read32(c,P03_SAVE_COUNTER);bc_press(c,QOL_KEY_START,120U);
    if(read32(c,QOL_START_MENU_CALLBACK)!=QOL_START_MENU_INPUT)return false;
    unsigned n=read8(c,QOL_START_MENU_COUNT),cursor=read8(c,QOL_START_MENU_CURSOR),target=n;
    if(!n||n>9U||cursor>=n)return false;
    for(unsigned i=0;i<n;++i)if(read8(c,QOL_START_MENU_ORDER+i)==P03_SAVE_ACTION)target=i;
    if(target==n)return false;
    for(unsigned i=0,steps=(target+n-cursor)%n;i<steps;++i)bc_press(c,QOL_KEY_DOWN,30U);
    if(read8(c,QOL_START_MENU_CURSOR)!=target)return false;
    bc_press(c,QOL_KEY_A,120U);bool seen=false;
    for(unsigned i=0;i<32U;++i){unsigned cb=read32(c,QOL_START_MENU_CALLBACK);if(cb==P03_SAVE_CALLBACK)seen=true;
        if(seen&&cb==P03_SAVE_CALLBACK&&read32(c,P03_SAVE_COUNTER)==counter+1U&&bc_field(c)){bc_run(c,0U,180U);return bc_field(c);}bc_press(c,QOL_KEY_A,180U);}
    return false;
}
static bool bc_continue(struct mCore*c){
    bc_run(c,0U,P02S_TITLE_FRAMES);
    for(unsigned i=0;i<P02S_CONTINUE_PULSES;++i){bc_press(c,i==0U?QOL_KEY_START:QOL_KEY_A,P02S_CONTINUE_WAIT_FRAMES);if(read32(c,BATTLE_CORE_MAIN_CALLBACK2)!=P02S_CB2_FIELD)continue;bc_run(c,0U,300U);
        for(unsigned r=0;r<8U;++r){if(!read8(c,P02S_QUEST_LOG_STATE)&&!read8(c,P02S_QUEST_LOG_PLAYBACK_STATE)){bc_wait(c);return true;}bc_press(c,QOL_KEY_B,P02S_CONTINUE_WAIT_FRAMES);}return false;}
    return false;
}
struct BCSnapshot{uint8_t party[600],pc[BC_PC_BYTES],queue[402],daycare[284];unsigned count;};
static struct BCSnapshot bc_snapshot(struct mCore*c){struct BCSnapshot s;bc_copy(c,QOL_PLAYER_PARTY,s.party,sizeof(s.party));bc_copy(c,bc_storage(c),s.pc,sizeof(s.pc));bc_copy(c,BC_QUEUE,s.queue,sizeof(s.queue));bc_copy(c,bc_save1(c)+QOL_DAYCARE_OFFSET,s.daycare,sizeof(s.daycare));s.count=bc_count(c);return s;}
static void bc_check_snapshot(struct mCore*c,const struct BCSnapshot*s){a_require(bc_count(c)==s->count,"capacity party count not persisted");bc_equal(c,QOL_PLAYER_PARTY,s->party,sizeof(s->party),"capacity party not byte-exact after cold save");bc_equal(c,bc_storage(c),s->pc,sizeof(s->pc),"capacity PC not byte-exact after cold save");bc_equal(c,BC_QUEUE,s->queue,sizeof(s->queue),"capacity pending queue not byte-exact after cold save");bc_equal(c,bc_save1(c)+QOL_DAYCARE_OFFSET,s->daycare,sizeof(s->daycare),"capacity parents not byte-exact after cold save");}
static void bc_queue_after(struct mCore*c,const uint8_t original[402],unsigned delivered){a_require(delivered<=3U&&bc_queue_count(c)==5U-delivered&&read8(c,BC_QUEUE+1U)==delivered,"capacity FIFO count/head differs");const uint8_t zero[80]={0};for(unsigned i=0;i<5U;++i)bc_equal(c,BC_QUEUE+2U+80U*i,i<delivered?zero:original+2U+80U*i,80U,"capacity FIFO consumed wrong egg");}
static struct mCore*bc_reload(struct mCore*c,const char*rom,const char*save){qol_close(c);qol_log_core=NULL;fprintf(stderr,"capacity old core destroyed; fresh core ordinary Continue\n");c=qol_open(rom,save);qol_log_core=c;c->setVideoBuffer(c,bc_video,240U);a_guard(c);a_require(bc_continue(c),"capacity fresh-core Continue failed");return c;}
int main(int argc,char**argv){
    if(argc==3&&!strcmp(argv[1],"--guard-check"))a_guard_check(argv[2]);
    if(argc!=6)return 2;
    int vacant=-1;
    if(!strcmp(argv[5],"pc-first"))vacant=0;else if(!strcmp(argv[5],"pc-last"))vacant=419;else if(strcmp(argv[5],"pc-full"))return 2;
    char rom_sha[65],seed_sha[65],after[65];sha256_file(argv[1],rom_sha);sha256_file(argv[2],seed_sha);
    a_require(!strcmp(rom_sha,BC_ROM_SHA)&&!strcmp(rom_sha,argv[3])&&!strcmp(seed_sha,BC_SEED_SHA)&&!strcmp(seed_sha,argv[4]),"capacity ROM/seed identity mismatch");
    struct mLogger logger={.log=qol_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    p03f_rtc_reserve(argv[2]);struct mCore*c=qol_open(argv[1],argv[2]);qol_log_core=c;c->setVideoBuffer(c,bc_video,240U);
    a_require(a_continue(c),"capacity initial Continue failed");a_flash_prepare(c);
    (void)call_preserving(c,0x09220861U,35U,0U,2U,3U);run_key_frames(c,0U,900U);bc_position(c,35U,0U,2U,3U);
    clear_parties(c);bc_create_parent(c,QOL_PLAYER_PARTY,0x123456F0U,0x11223344U);bc_create_parent(c,QOL_PLAYER_PARTY+100U,0x34567801U,0x99887766U);
    for(unsigned i=2;i<6U;++i)create_mon(c,QOL_PLAYER_PARTY+100U*i,649U,20U);
    write8(c,QOL_PLAYER_PARTY_COUNT,6U);const unsigned moves[2][4]={{175,33,0,0},{273,45,0,0}};
    for(unsigned p=0;p<2U;++p)for(unsigned k=0;k<4U;++k){set_mon_data_u32(c,QOL_PLAYER_PARTY+100U*p,13U+k,moves[p][k]);set_mon_data_u32(c,QOL_PLAYER_PARTY+100U*p,17U+k,moves[p][k]?5U:0U);}
    unsigned storage=bc_storage(c);a_require(call_preserving(c,0x0808B7CDU,0U,0U,0U,0U)==storage&&call_preserving(c,0x0808B7CDU,13U,29U,0U,0U)==storage+419U*80U,"capacity native PC layout differs");
    for(unsigned i=0;i<420U;++i){if((int)i==vacant)(void)call_preserving(c,QOL_ZERO_BOX_MON,i/30U,i%30U,0U,0U);else (void)call_preserving(c,QOL_SET_BOX_MON,i/30U,i%30U,QOL_PLAYER_PARTY+200U,0U);}
    unsigned s=bc_save1(c);for(unsigned i=0;i<284U;++i)write8(c,s+QOL_DAYCARE_OFFSET+i,0U);
    (void)call_preserving(c,QOL_FLAG_CLEAR,0x266U,0U,0U,0U);(void)call_preserving(c,QOL_FLAG_CLEAR,QOL_FLAG_EGG_BASKET,0U,0U,0U);
    for(unsigned i=0;i<402U;++i)write8(c,BC_QUEUE+i,0U);
    (void)call_preserving(c,QOL_SAVE_FINALIZE,QOL_LEDGER,0U,0U,0U);
    /* 以下ではhost書込、ROM直接呼出、snapshot復元を一切行わない。 */
    a_guard(c);bc_press(c,QOL_KEY_UP,30U);bc_dialogue(c,true);
    a_require(bc_count(c)==4U&&bc_deposit_menu&&bc_deposit_menu<bc_first_deposit&&bc_first_deposit<bc_second_deposit,"capacity two ordinary deposits not observed");
    bc_to(c,2U,5U);unsigned start=bc_steps;
    for(unsigned i=0;i<8192U&&bc_queue_count(c)<5U;++i)bc_step(c,read16(c,bc_save1(c))==2U?QOL_KEY_RIGHT:BC_LEFT);
    a_require(bc_queue_count(c)==5U&&read8(c,BC_QUEUE+1U)==0U,"capacity queue did not fill by walking");bc_generated=bc_frames;
    unsigned generation_steps=bc_steps-start;uint8_t queue[402];bc_copy(c,BC_QUEUE,queue,sizeof(queue));
    for(unsigned i=0;i<5U;++i){a_require(memcmp(queue+2U+80U*i,(uint8_t[80]){0},80U)!=0,"capacity generated empty egg");for(unsigned j=0;j<i;++j)a_require(memcmp(queue+2U+80U*i,queue+2U+80U*j,8U)!=0,"capacity duplicate egg identity");}
    for(unsigned i=0;i<512U;++i)bc_step(c,read16(c,bc_save1(c))==2U?QOL_KEY_RIGHT:BC_LEFT);
    bc_equal(c,BC_QUEUE,queue,sizeof(queue),"capacity overflow changed pending egg FIFO");bc_cap_checked=bc_frames;
    bc_to(c,4U,6U);bc_step(c,QOL_KEY_DOWN);bc_step(c,QOL_KEY_DOWN);bc_position(c,3U,37U,3U,24U);
    bc_to(c,3U,27U);bc_to(c,8U,27U);bc_press(c,QOL_KEY_UP,30U);struct BCSnapshot before=bc_snapshot(c);
    for(unsigned n=0;n<2U;++n){bc_dialogue(c,false);bc_claim[n]=bc_frames;a_require(bc_count(c)==5U+n,"capacity ordinary claim did not fill final party slots");bc_equal(c,QOL_PLAYER_PARTY+(4U+n)*100U,queue+2U+n*80U,80U,"capacity wrong FIFO egg in party");bc_equal(c,QOL_PLAYER_PARTY,before.party,400U,"capacity original four party members changed");bc_equal(c,bc_storage(c),before.pc,sizeof(before.pc),"capacity party delivery modified PC");bc_queue_after(c,queue,n+1U);}
    uint8_t fullparty[600];bc_copy(c,QOL_PLAYER_PARTY,fullparty,sizeof(fullparty));bc_dialogue(c,false);bc_claim[2]=bc_frames;
    unsigned delivered=vacant<0?2U:3U;bc_queue_after(c,queue,delivered);a_require(bc_count(c)==6U,"capacity full party count changed");
    bc_equal(c,QOL_PLAYER_PARTY,fullparty,sizeof(fullparty),"capacity PC/full refusal changed party");
    for(unsigned i=0;i<420U;++i)bc_equal(c,bc_storage(c)+i*80U,(int)i==vacant?queue+2U+2U*80U:before.pc+i*80U,80U,"capacity incorrect PC destination/overwrite");
    bc_equal(c,bc_save1(c)+QOL_DAYCARE_OFFSET,before.daycare,sizeof(before.daycare),"capacity claim changed deposited parents");
    struct BCSnapshot result=bc_snapshot(c);unsigned counter=read32(c,P03_SAVE_COUNTER);
    a_require(bc_save(c),"capacity ordinary save failed");bc_saved[0]=bc_frames;bc_check_snapshot(c,&result);
    c=bc_reload(c,argv[1],argv[2]);bc_reloaded[0]=bc_frames;bc_position(c,3U,37U,8U,27U);bc_check_snapshot(c,&result);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+1U,"capacity first manual save counter differs");
    bc_press(c,QOL_KEY_UP,30U);bc_dialogue(c,false);bc_retry=bc_frames;bc_check_snapshot(c,&result);
    a_require(bc_save(c),"capacity retry ordinary save failed");bc_saved[1]=bc_frames;bc_check_snapshot(c,&result);
    c=bc_reload(c,argv[1],argv[2]);bc_reloaded[1]=bc_frames;bc_check_snapshot(c,&result);
    a_require(read32(c,P03_SAVE_COUNTER)==counter+2U,"capacity two manual saves not persisted");bc_state(c,"done");
    qol_close(c);qol_log_core=NULL;sha256_file(argv[1],after);a_require(!strcmp(rom_sha,after)&&log_problem_count==0U,"capacity ROM changed or emulator warning/error");
    printf("{\"schema_version\":1,\"status\":\"PASS\",\"scope\":\"%s\",\"case\":\"%s\",\"rom_sha256\":\"%s\",",BC_SCOPE,argv[5],rom_sha);
    printf("\"generated_eggs\":5,\"overflow_steps\":512,\"party_deliveries\":2,\"pc_deliveries\":%u,\"pc_destination\":%d,\"remaining_eggs\":%u,\"queue_head\":%u,",vacant<0?0U:1U,vacant,5U-delivered,delivered);
    printf("\"generation_steps\":%u,\"total_steps\":%u,\"total_frames\":%u,\"ordinary_deposit\":true,\"ordinary_claim\":true,\"fifo_byte_identity\":true,\"pc_full_retry_preserves_pending\":true,",generation_steps,bc_steps,bc_frames);
    printf("\"party_bytes_checked\":600,\"pc_bytes_checked\":%u,\"queue_bytes_checked\":402,\"daycare_bytes_checked\":284,\"manual_save_counter_delta\":2,\"fresh_cores\":3,\"host_write_barriers\":7,\"post_fixture_rom_calls\":0,",BC_PC_BYTES);
    printf("\"locked_dialogues\":%u,\"parent_and_pc_fixture_only\":true,\"full_p03_acceptance\":false,\"release_ready\":false,\"warnings_errors\":0,\"witness\":{",bc_locked_dialogues);
    printf("\"deposit_menu\":%u,\"first_deposit\":%u,\"second_deposit\":%u,\"generated\":%u,\"capacity_checked\":%u,",bc_deposit_menu,bc_first_deposit,bc_second_deposit,bc_generated,bc_cap_checked);
    printf("\"first_claim\":%u,\"second_claim\":%u,\"capacity_claim\":%u,\"first_saved\":%u,\"first_reloaded\":%u,\"full_retry\":%u,\"second_saved\":%u,\"second_reloaded\":%u}}\n",bc_claim[0],bc_claim[1],bc_claim[2],bc_saved[0],bc_reloaded[0],bc_retry,bc_saved[1],bc_reloaded[1]);return 0;
}
