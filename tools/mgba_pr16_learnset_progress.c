/* Direct-ROM, host-fixture scope only; not a Bag/battle/Save/Continue acceptance. */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop
#include "pr16_progress_samples.h"

static unsigned calls;
static uint32_t progress_call(struct mCore *core, uint32_t fn, uint32_t a, uint32_t b, uint32_t d, uint32_t e)
{
    struct CpuState original=capture_cpu_state(core);
    struct HostCallStack stack;
    const uint32_t args[4]={0,0,0,0};
    unsigned steps=0;bool seen=false;
    begin_host_call_stack(core,&stack,args,4);
    write_register(core,"cpsr",(uint32_t)original.registers[16]|0xA0U);
    write_register(core,"lr",0x08000001U);
    write_register(core,"r0",a);write_register(core,"r1",b);
    write_register(core,"r2",d);write_register(core,"r3",e);
    write_register(core,"pc",fn);
    while (((uint32_t)read_register(core,"pc")&~1U)!=0x08000002U) {
        uint32_t pc=(uint32_t)read_register(core,"pc")&~1U;
        if (pc>=PR16_CODE_START && pc<PR16_CODE_END) seen=true;
        if (++steps>BATTLE_CORE_DIRECT_CALL_LIMIT) battle_core_die("progress call timeout");
        core->step(core);
    }
    uint32_t result=(uint32_t)read_register(core,"r0");
    bool intact=restore_host_call_stack(core,&stack);
    restore_cpu_state(core,&original);
    if (!seen || !intact) battle_core_die("new progression PC or stack missing");
    ++calls;return result;
}
static void setdata(struct mCore *c,unsigned field,unsigned value)
{
    const uint32_t at=0x0203C000;
    write32_bytes(c,at,value);
    (void)call_bounded(c,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,field,at,0);
}
static unsigned getdata(struct mCore *c,unsigned field)
{
    return call_bounded(c,ROM_GET_MON_DATA,ADDR_PLAYER_PARTY,field,0,0).result;
}
static void moves(struct mCore *c,const uint16_t *list,unsigned count)
{
    for(unsigned i=0;i<4;i++){setdata(c,13+i,i<count?list[i]:0);setdata(c,17+i,i<count?7+i:0);}
    setdata(c,21,0);
}
static void initial_check(struct mCore *c,const struct ProgressSample *s)
{
    uint32_t table=read32(c,BATTLE_CORE_MOVE_TABLE_REPOINT);
    for(unsigned i=0;i<4;i++) {
        unsigned mid=i<s->count?s->moves[i]:0;
        unsigned pp=mid?read8(c,table+mid*BATTLE_CORE_BATTLE_MOVE_SIZE+4):0;
        if(getdata(c,13+i)!=mid || getdata(c,17+i)!=pp) {
            fprintf(stderr,"initial sid=%u level=%u slot=%u actual=%u/%u expected=%u/%u\n",s->species,s->level,i,getdata(c,13+i),getdata(c,17+i),mid,pp);
            battle_core_die("initial real move/PP differs");
        }
    }
}
static void monbytes(struct mCore *c,uint8_t *out)
{for(unsigned i=0;i<POKEMON_SIZE;i++)out[i]=read8(c,ADDR_PLAYER_PARTY+i);}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    char sha[65];sha256_file(argv[1],sha);
    if(strcmp(sha,argv[2]))battle_core_die("candidate identity differs");
    struct mLogger logger={.log=quiet_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore *core=mCoreFind(argv[1]);
    if(!core || !core->init(core) || !mCoreLoadFile(core,argv[1]))battle_core_die("core load");
    mCoreInitConfig(core,NULL);mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
    static color_t video[240*160];core->setVideoBuffer(core,video,240);
    struct mRTCSource rtc={.sample=NULL,.unixTime=fixed_unix_time,.serialize=NULL,.deserialize=NULL};mCoreSetRTC(core,&rtc);
    core->reset(core);
    const uint16_t known[4]={1000,1001,1002,1003};
    unsigned preserved=0,creations=0,duplicate=0,full=0;
    for(unsigned i=0;i<sizeof(progress_samples)/sizeof(*progress_samples);i++) {
        const struct ProgressSample *s=progress_samples+i;
        fprintf(stderr,"sample=%u species=%u level=%u policy=%u\n",i,s->species,s->level,s->policy);
        for(unsigned k=0;k<s->next_count;k++)if(s->next[k]>=1000 && s->next[k]<=1003)battle_core_die("known fixture collision");
        /* Native CreateMon naturally calls the patched initializer. The call is
         * still a host fixture, not a wild encounter or gameplay creation proof. */
        (void)progress_call(core,BATTLE_CORE_CREATE_MON,ADDR_PLAYER_PARTY,s->species,s->level,0);
        if(getdata(core,11)!=s->species || getdata(core,56)!=s->level)battle_core_die("creation identity");
        initial_check(core,s);++creations;
        const uint32_t initial[2]={0x0803E175U,PR16_INITIAL_DIRECT};
        const uint32_t natural[2]={0x0803E1F5U,PR16_NATURAL_DIRECT};
        for(unsigned entry=0;entry<2;entry++) {
            moves(core,NULL,0);
            (void)progress_call(core,initial[entry],ADDR_PLAYER_PARTY,0,0,0);
            initial_check(core,s);
            moves(core,known,4);setdata(core,21,0x39);
            uint8_t before[POKEMON_SIZE],after[POKEMON_SIZE];monbytes(core,before);
            (void)progress_call(core,initial[entry],ADDR_PLAYER_PARTY,0,0,0);
            monbytes(core,after);if(memcmp(before,after,POKEMON_SIZE))battle_core_die("initializer rewrote stored four moves");
            unsigned count=s->policy==1?s->next_count:0;
            for(unsigned k=0;k<=count;k++) {
                unsigned result=progress_call(core,natural[entry],ADDR_PLAYER_PARTY,k==0,0,0);
                if(result!=(k<count?0xFFFFU:0U))battle_core_die("full-slot sequence result");
                if(k<count && read16(core,0x02023F82U)!=s->next[k])battle_core_die("JP pending move");
                monbytes(core,after);if(memcmp(before,after,POKEMON_SIZE))battle_core_die("full or preserved mon changed");
                if(k<count)++full;
            }
            if(s->policy!=1){++preserved;continue;}
            if(count) {
                moves(core,s->next,1);
                unsigned result=progress_call(core,natural[entry],ADDR_PLAYER_PARTY,1,0,0);
                if(result!=0xFFFEU || getdata(core,17)!=7)battle_core_die("duplicate did not preserve PP");
                ++duplicate;
                unsigned slot=1;
                for(unsigned k=1;k<count;k++) {
                    result=progress_call(core,natural[entry],ADDR_PLAYER_PARTY,0,0,0);
                    if(result!=s->next[k] || getdata(core,13+slot)!=s->next[k])battle_core_die("duplicate cursor failed to continue");
                    ++slot;
                }
                if(progress_call(core,natural[entry],ADDR_PLAYER_PARTY,0,0,0))battle_core_die("cursor did not terminate");
            }
        }
    }
    if(log_problem_count)battle_core_die("mGBA warning/error");
    printf("{\"status\":\"PASS_INITIAL_AND_NATURAL_ROM_PROBES\",\"scope\":\"HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E\",\"candidate_sha256\":\"%s\",\"samples\":%zu,\"calls\":%u,\"native_create_mon_calls\":%u,\"preserved_owner_entries\":%u,\"duplicate_paths\":%u,\"full_slot_notifications\":%u,\"new_code_pc_seen_for_every_call\":true,\"stored_four_moves_unchanged\":true,\"real_initial_pp_checked\":true}\n",sha,sizeof(progress_samples)/sizeof(*progress_samples),calls,creations,preserved,duplicate,full);
    mCoreConfigDeinit(&core->config);core->deinit(core);return 0;
}
