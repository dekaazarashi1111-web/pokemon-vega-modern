/* 新条件入口の実ROM呼出し。ボタン操作/Save/Continue E2Eとは区別する。 */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop
#include "pr16_conditional_samples.h"
static unsigned calls,read_checks,full_checks,duplicate_checks,egg_checks;
static uint32_t conditional_call(struct mCore *core,uint32_t fn,uint32_t a,uint32_t b,uint32_t d,uint32_t lr)
{
    struct CpuState original=capture_cpu_state(core);
    struct HostCallStack stack;const uint32_t args[4]={0,0,0,0};
    unsigned steps=0;bool seen=false;
    begin_host_call_stack(core,&stack,args,4);
    write_register(core,"cpsr",(uint32_t)original.registers[16]|0xA0U);
    write_register(core,"lr",lr);write_register(core,"r0",a);write_register(core,"r1",b);
    write_register(core,"r2",d);write_register(core,"r3",0);write_register(core,"pc",fn);
    while (((uint32_t)read_register(core,"pc")&~1U)!=((lr&~1U)+2U)) {
        uint32_t pc=(uint32_t)read_register(core,"pc")&~1U;
        if(pc>=PR16_CODE_START && pc<PR16_CODE_END)seen=true;
        if(++steps>BATTLE_CORE_DIRECT_CALL_LIMIT)battle_core_die("conditional call timeout");
        core->step(core);
    }
    uint32_t result=(uint32_t)read_register(core,"r0");
    bool intact=restore_host_call_stack(core,&stack);restore_cpu_state(core,&original);
    if(!seen || !intact)battle_core_die("conditional PC/stack evidence missing");
    ++calls;return result;
}
static void setdata(struct mCore *c,unsigned field,unsigned value)
{
    const uint32_t at=0x0203C000U;write32_bytes(c,at,value);
    (void)call_bounded(c,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,field,at,0);
}
static unsigned getdata(struct mCore *c,unsigned field)
{return call_bounded(c,ROM_GET_MON_DATA,ADDR_PLAYER_PARTY,field,0,0).result;}
static void monbytes(struct mCore *c,uint8_t *out)
{for(unsigned i=0;i<POKEMON_SIZE;i++)out[i]=read8(c,ADDR_PLAYER_PARTY+i);}
static void setmoves(struct mCore *c,const uint16_t *list,unsigned count)
{
    for(unsigned i=0;i<4;i++){setdata(c,13+i,i<count?list[i]:0);setdata(c,17+i,i<count?7+i:0);}
    setdata(c,21,0x39);
}
static unsigned contains(const uint16_t *list,unsigned count,unsigned move)
{for(unsigned i=0;i<count;i++)if(list[i]==move)return 1;return 0;}
static void check_list(struct mCore *core,const struct ConditionalSample *s,unsigned family,
                       unsigned entry,unsigned flag,const uint16_t *known,unsigned known_count)
{
    const uint32_t out=0x0203C100U;
    uint16_t expect[50];unsigned count=0;
    for(unsigned i=0;i<s->count[family];i++)
        if(!contains(known,known_count,s->moves[family][i]))expect[count++]=s->moves[family][i];
    for(unsigned i=0;i<52;i++)write16(core,out+2*i,0xBEEFU);
    uint8_t before[POKEMON_SIZE],after[POKEMON_SIZE];monbytes(core,before);
    unsigned result=conditional_call(core,entry,ADDR_PLAYER_PARTY,out,flag,0x08000001U);
    if(result!=count){fprintf(stderr,"sid=%u family=%u entry=%x count=%u expected=%u\n",s->species,family,entry,result,count);battle_core_die("conditional count mismatch");}
    for(unsigned i=0;i<52;i++)if(read16(core,out+2*i)!=(i<count?expect[i]:0xBEEF))battle_core_die("conditional list/canary mismatch");
    monbytes(core,after);if(memcmp(before,after,POKEMON_SIZE))battle_core_die("readonly consumer rewrote mon/PP");
    ++read_checks;
}
static void check_empty(struct mCore *core,unsigned entry,unsigned flag)
{
    const uint32_t out=0x0203C100U;
    for(unsigned i=0;i<52;i++)write16(core,out+2*i,0xBEEFU);
    uint8_t before[POKEMON_SIZE],after[POKEMON_SIZE];monbytes(core,before);
    if(conditional_call(core,entry,ADDR_PLAYER_PARTY,out,flag,0x08000001U))battle_core_die("denied path returned moves");
    for(unsigned i=0;i<52;i++)if(read16(core,out+2*i)!=0xBEEF)battle_core_die("denied path changed buffer");
    monbytes(core,after);if(memcmp(before,after,POKEMON_SIZE))battle_core_die("denied path rewrote mon");
    ++read_checks;
}
int main(int argc,char **argv)
{
    if(argc!=3)return 2;
    char sha[65];sha256_file(argv[1],sha);if(strcmp(sha,argv[2]))battle_core_die("candidate identity differs");
    struct mLogger logger={.log=quiet_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore *core=mCoreFind(argv[1]);
    if(!core || !core->init(core) || !mCoreLoadFile(core,argv[1]))battle_core_die("core load");
    mCoreInitConfig(core,NULL);mCoreConfigSetDefaultValue(&core->config,"idleOptimization","ignore");
    static color_t video[240*160];core->setVideoBuffer(core,video,240);
    struct mRTCSource rtc={.sample=NULL,.unixTime=fixed_unix_time,.serialize=NULL,.deserialize=NULL};mCoreSetRTC(core,&rtc);
    core->reset(core);
    const uint16_t known[4]={1000,1001,1002,1003};
    for(unsigned i=0;i<sizeof(conditional_samples)/sizeof(*conditional_samples);i++) {
        const struct ConditionalSample *s=conditional_samples+i;
        fprintf(stderr,"sample=%u species=%u level=%u policy=%u\n",i,s->species,s->level,s->policy);
        /* 合成fixture生成は旧初期技の再受入ではない。ID0等はCreateMon後に設定。 */
        (void)call_bounded(core,BATTLE_CORE_CREATE_MON,ADDR_PLAYER_PARTY,1,s->level,0);
        setdata(core,11,s->species);setdata(core,45,0);setmoves(core,known,4);
        if(getdata(core,11)!=s->species || getdata(core,56)!=s->level)battle_core_die("fixture identity mismatch");
        check_list(core,s,0,0x080451EDU,0,NULL,0);
        check_list(core,s,1,0x090EB971U,0,NULL,0);
        check_list(core,s,1,0x090EB971U,1,known,4);
        write8(core,0x0203EC00U,0);check_list(core,s,2,0x091141D5U,0,known,4);
        write8(core,0x0203EC00U,1);check_list(core,s,1,0x091141D5U,0,known,4);
        if(s->count[1]) {
            setmoves(core,s->moves[1],1);
            check_list(core,s,1,0x090EB971U,1,s->moves[1],1);
            check_list(core,s,1,0x091141D5U,0,s->moves[1],1);
        }
        if(s->count[2]) {
            setmoves(core,s->moves[2],1);write8(core,0x0203EC00U,0);
            check_list(core,s,2,0x091141D5U,0,s->moves[2],1);
        }
        setmoves(core,known,4);
        /* 保存済みP03振分けの両LR経路を使い、新delegateに到達することも確認。 */
        const uint32_t entries[3]={0x09114121U,0x0803E1F5U,0x0803E1F5U};
        const uint32_t lrs[3]={0x08000001U,0x080CFEF9U,0x080D0A6DU};
        for(unsigned entry=0;entry<3;entry++) {
            uint8_t before[POKEMON_SIZE],after[POKEMON_SIZE];monbytes(core,before);
            for(unsigned k=0;k<=s->count[3];k++) {
                unsigned value=conditional_call(core,entries[entry],ADDR_PLAYER_PARTY,k==0,0,lrs[entry]);
                if(value!=(k<s->count[3]?0xFFFFU:0U))battle_core_die("evolution full/termination mismatch");
                if(k<s->count[3] && read16(core,0x02023F82U)!=s->moves[3][k])battle_core_die("evolution pending move mismatch");
                monbytes(core,after);if(memcmp(before,after,POKEMON_SIZE))battle_core_die("full slots/PP rewritten");
                if(k<s->count[3])++full_checks;
            }
        }
        if(s->count[3]) {
            setmoves(core,s->moves[3],1);
            if(conditional_call(core,0x09114121U,ADDR_PLAYER_PARTY,1,0,0x08000001U)!=0xFFFEU || getdata(core,17)!=7)battle_core_die("duplicate PP changed");
            ++duplicate_checks;
            for(unsigned k=1;k<s->count[3];k++) {
                uint16_t existing[4];unsigned slot=4;
                for(unsigned j=0;j<4;j++){existing[j]=(uint16_t)getdata(core,13+j);if(!existing[j] && slot==4)slot=j;}
                unsigned mid=s->moves[3][k];unsigned expected=contains(existing,4,mid)?0xFFFEU:slot==4?0xFFFFU:mid;
                unsigned value=conditional_call(core,0x09114121U,ADDR_PLAYER_PARTY,0,0,0x08000001U);
                if(value!=expected)battle_core_die("evolution duplicate cursor continuity");
                if(value==mid) {
                    uint32_t table=read32(core,BATTLE_CORE_MOVE_TABLE_REPOINT);
                    if(getdata(core,13+slot)!=mid || getdata(core,17+slot)!=read8(core,table+mid*BATTLE_CORE_BATTLE_MOVE_SIZE+4))battle_core_die("real move/PP grant mismatch");
                }
            }
            if(conditional_call(core,0x09114121U,ADDR_PLAYER_PARTY,0,0,0x08000001U))battle_core_die("duplicate sequence did not terminate");
        }
        setmoves(core,known,4);setdata(core,45,1);
        check_list(core,s,0,0x080451EDU,0,NULL,0);
        write8(core,0x0203EC00U,0);check_empty(core,0x091141D5U,0);
        if(conditional_call(core,0x09114121U,ADDR_PLAYER_PARTY,1,0,0x08000001U))battle_core_die("egg evolution granted");
        ++egg_checks;setdata(core,45,0);
        if(s->species==1029 || s->policy!=1) {
            for(unsigned mode=2;mode<8;mode++){write8(core,0x0203EC00U,(uint8_t)mode);check_empty(core,0x091141D5U,0);}
        }
        write8(core,0x0203EC00U,255);check_empty(core,0x091141D5U,0);
    }
    if(log_problem_count)battle_core_die("mGBA warning/error");
    printf("{\"status\":\"PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS\",\"scope\":\"HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E\",\"candidate_sha256\":\"%s\",\"samples\":%zu,\"calls\":%u,\"readonly_checks\":%u,\"full_slot_notifications\":%u,\"duplicate_paths\":%u,\"egg_guard_paths\":%u,\"new_code_pc_seen_for_every_call\":true,\"stored_four_moves_and_pp_preserved\":true,\"real_granted_pp_checked\":true,\"p03_two_evolution_lr_paths_checked\":true,\"floette_archive_denied\":true}\n",sha,sizeof(conditional_samples)/sizeof(*conditional_samples),calls,read_checks,full_checks,duplicate_checks,egg_checks);
    mCoreConfigDeinit(&core->config);core->deinit(core);return 0;
}
