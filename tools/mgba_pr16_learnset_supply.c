/* New supply hooks only. Synthetic direct ROM calls are NOT gameplay E2E. */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop
#include "pr16_supply_samples.h"
static unsigned calls, checks, tutor_yes, tutor_no, specials_yes, specials_no;
static unsigned pages, denied, filtered, selection_checks, page_four, gates;
static unsigned hook_seen[4];
static const uint32_t hooks[4]={0x09110229U,0x091141D5U,0x09539D79U,0x0953A23DU};
static uint32_t invoke(struct mCore *c,uint32_t fn,uint32_t a,uint32_t b)
{
    struct CpuState original=capture_cpu_state(c);
    struct HostCallStack stack;const uint32_t args[4]={0,0,0,0};
    unsigned steps=0;bool seen=false;int hook=-1;
    for(unsigned i=0;i<4;i++)if(fn==hooks[i])hook=(int)i;
    begin_host_call_stack(c,&stack,args,4);
    write_register(c,"cpsr",(uint32_t)original.registers[16]|0xA0U);
    write_register(c,"lr",0x08000001U);write_register(c,"r0",a);write_register(c,"r1",b);
    write_register(c,"r2",0);write_register(c,"r3",0);write_register(c,"pc",fn);
    while(((uint32_t)read_register(c,"pc")&~1U)!=0x08000002U){
        uint32_t pc=(uint32_t)read_register(c,"pc")&~1U;
        if(pc>=PR16_CODE_START && pc<PR16_CODE_END)seen=true;
        if(hook==1 && !hook_seen[1] && steps<128)
            fprintf(stderr,"first_archive step=%u pc=%08x sp=%08x lr=%08x r0=%08x r1=%08x r3=%08x r5=%08x mode=%u cpsr=%08x\n",
                steps,pc,(uint32_t)read_register(c,"sp"),(uint32_t)read_register(c,"lr"),
                (uint32_t)read_register(c,"r0"),(uint32_t)read_register(c,"r1"),
                (uint32_t)read_register(c,"r3"),(uint32_t)read_register(c,"r5"),
                read8(c,0x0203EC00U),(uint32_t)read_register(c,"cpsr"));
        if(++steps>BATTLE_CORE_DIRECT_CALL_LIMIT){fprintf(stderr,"fn=%08x a=%u b=%u pc=%08x\n",fn,a,b,pc);battle_core_die("supply timeout");}
        c->step(c);
    }
    uint32_t result=(uint32_t)read_register(c,"r0");
    bool intact=restore_host_call_stack(c,&stack);restore_cpu_state(c,&original);
    if(!intact || (hook>=0 && !seen))battle_core_die("supply PC/stack contract");
    if(hook>=0)++hook_seen[hook];
    ++calls;return result;
}
static void setdata(struct mCore *c,unsigned field,unsigned value)
{write32_bytes(c,0x0203C000U,value);(void)call_bounded(c,ROM_SET_MON_DATA,ADDR_PLAYER_PARTY,field,0x0203C000U,0);}
static unsigned getdata(struct mCore *c,unsigned field)
{return call_bounded(c,ROM_GET_MON_DATA,ADDR_PLAYER_PARTY,field,0,0).result;}
static void monbytes(struct mCore *c,uint8_t *out)
{for(unsigned i=0;i<POKEMON_SIZE;i++)out[i]=read8(c,ADDR_PLAYER_PARTY+i);}
static unsigned readonly(struct mCore *c,uint32_t fn,uint32_t a,uint32_t b)
{
    uint8_t before[POKEMON_SIZE],after[POKEMON_SIZE];monbytes(c,before);
    unsigned result=invoke(c,fn,a,b);monbytes(c,after);
    if(memcmp(before,after,POKEMON_SIZE))battle_core_die("supply rewrote stored mon/four moves/PP");
    ++checks;return result;
}
static void gate(struct mCore *c,unsigned enabled)
{
    (void)invoke(c,enabled?PR16_FLAG_SET:PR16_FLAG_CLEAR,0x82C,0);
    if(invoke(c,0x0806DEC5U,0x82C,0)!=enabled)battle_core_die("real FlagSet/Get ABI mismatch");
    ++gates;
}
static void moves(struct mCore *c,const uint16_t known[4])
{
    for(unsigned k=0;k<4;k++){setdata(c,13+k,known[k]);setdata(c,17+k,known[k]?7+k:0);}
    setdata(c,21,0x39);
}
static unsigned contains(const uint16_t *seq,unsigned n,unsigned value)
{for(unsigned i=0;i<n;i++)if(seq[i]==value)return 1;return 0;}
static unsigned expected(const struct SupplySample *s,unsigned mode,const uint16_t known[4],uint16_t out[40])
{
    const uint16_t *seq=mode==7?s->tutor:s->machine;
    unsigned n=mode==7?s->tutor_count:s->machine_count,begin=0,end=n,count=0;
    if(mode<2 || mode>7 || s->policy!=1)return 0;
    if(mode>=3 && mode<=6){begin=(mode-3)*40;end=begin+40;if(end>n)end=n;}
    for(unsigned i=begin;i<end;i++)if(!contains(known,4,seq[i])){
        if(count>=40)battle_core_die("source oracle capacity");
        out[count++]=seq[i];if(mode==2)break;
    }
    return count;
}
static void page(struct mCore *c,const struct SupplySample *s,unsigned mode,
                 const uint16_t known[4],unsigned allow)
{
    const uint32_t out=0x0203C100U;uint16_t want[40];
    unsigned count=allow?expected(s,mode,known,want):0;
    write8(c,0x0203EC00U,(uint8_t)mode);
    for(unsigned i=0;i<44;i++)write16(c,out-4+2*i,0xBEEF);
    unsigned actual=readonly(c,hooks[1],ADDR_PLAYER_PARTY,out);
    if(actual!=count){fprintf(stderr,"species=%u mode=%u actual=%u expected=%u allow=%u\n",s->species,mode,actual,count,allow);battle_core_die("supply page count");}
    for(unsigned i=0;i<44;i++){
        unsigned v=(i>=2 && i<2+count)?want[i-2]:0xBEEF;
        if(read16(c,out-4+2*i)!=v)battle_core_die("supply page order/canary");
    }
    write16(c,0x02037004U,0xA55A);
    (void)readonly(c,hooks[3],0,0);
    unsigned page_has=(mode>=3 && mode<=6 && count)?1:0;
    if(read16(c,0x02037004U)!=page_has)battle_core_die("selected page readiness");
    if(mode==6 && count)++page_four;
    if(allow)++pages;else ++denied;
}
int main(int argc,char **argv)
{
    if(argc!=4)return 2;
    bool reverse=!strcmp(argv[3],"reverse");
    if(!reverse && strcmp(argv[3],"forward"))return 2;
    char sha[65];sha256_file(argv[1],sha);if(strcmp(sha,argv[2]))battle_core_die("supply candidate identity");
    struct mLogger logger={.log=quiet_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore *c=mCoreFind(argv[1]);
    if(!c || !c->init(c) || !mCoreLoadFile(c,argv[1]))battle_core_die("core load");
    mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");
    static color_t video[240*160];c->setVideoBuffer(c,video,240);
    struct mRTCSource rtc={.sample=NULL,.unixTime=fixed_unix_time,.serialize=NULL,.deserialize=NULL};mCoreSetRTC(c,&rtc);
    c->reset(c);
    /* Synthetic save-block backing, not a user's save or a Continue test. */
    for(unsigned i=0;i<0x4000;i++)write8(c,0x02010000U+i,0);
    write32_bytes(c,PR16_SAVE_BLOCK1_PTR,0x02010000U);
    uint16_t catalog[64];for(unsigned i=0;i<64;i++)catalog[i]=(uint16_t)invoke(c,0x091103A9U,i,0);
    const uint16_t empty[4]={0,0,0,0};
    for(unsigned at=0;at<ARRAY_LEN(supply_samples);at++){
        const struct SupplySample *s=&supply_samples[reverse?ARRAY_LEN(supply_samples)-1-at:at];
        fprintf(stderr,"sample=%u species=%u policy=%u machine=%u tutor=%u\n",at,s->species,s->policy,s->machine_count,s->tutor_count);
        (void)call_bounded(c,BATTLE_CORE_CREATE_MON,ADDR_PLAYER_PARTY,1,50,0);
        setdata(c,11,s->species);setdata(c,45,0);moves(c,empty);write16(c,0x02036FF4U,0);
        if(getdata(c,11)!=s->species || getdata(c,45))battle_core_die("fixture mon identity");
        for(unsigned enabled=0;enabled<2;enabled++){
            gate(c,enabled);
            for(unsigned slot=0;slot<64;slot++){
                unsigned want=s->policy==1?(unsigned)((s->bits>>slot)&1U):0;
                unsigned actual=readonly(c,hooks[0],ADDR_PLAYER_PARTY,slot);
                if(actual!=want)battle_core_die("ordinary tutor bit/HoF independence");
                if(actual)++tutor_yes;else ++tutor_no;
            }
            for(unsigned friend_value=0;friend_value<2;friend_value++){
                /* Field32 is the friendship read in the preserved special body. */
                setdata(c,32,friend_value?255:0);
                for(unsigned j=0;j<9;j++){
                    unsigned id=152+j,move=invoke(c,0x091103A9U,id,0),allowed=0;
                    if(move!=special_moves[j])battle_core_die("special tutor move mapping");
                    if(s->policy==1){
                        for(unsigned slot=0;slot<64;slot++)if((s->bits>>slot)&1U && catalog[slot]==move)allowed=1;
                        if(contains(s->tutor,s->tutor_count,move))allowed=1;
                    }
                    unsigned original=0;
                    if(s->policy==1)original=readonly(c,PR16_ORIGINAL_TUTOR,ADDR_PLAYER_PARTY,id)!=0;
                    unsigned actual=readonly(c,hooks[0],ADDR_PLAYER_PARTY,id);
                    if(actual!=(allowed && original))battle_core_die("special tutor owner/original predicate");
                    if(actual)++specials_yes;else ++specials_no;
                }
            }
            const unsigned bad[5]={64,127,151,161,255};
            for(unsigned j=0;j<ARRAY_LEN(bad);j++)if(readonly(c,hooks[0],ADDR_PLAYER_PARTY,bad[j]))battle_core_die("invalid tutor id");
            unsigned rows=readonly(c,hooks[2],0,0),want_rows=enabled?s->machine_count:0;
            if(rows!=want_rows)battle_core_die("selected raw row count");
            for(unsigned mode=2;mode<=7;mode++)page(c,s,mode,empty,enabled);
        }
        /* Known moves deliberately cross raw page boundaries. They must not shift page2 into page1. */
        uint16_t known[4]={0,0,0,0};
        const unsigned pick[4]={0,39,40,80};
        for(unsigned j=0;j<4;j++)if(pick[j]<s->machine_count)known[j]=s->machine[pick[j]];
        moves(c,known);
        for(unsigned mode=2;mode<=7;mode++)page(c,s,mode,known,1);
        if(s->machine_count>40)++filtered;
        if(readonly(c,hooks[2],0,0)!=s->machine_count)battle_core_die("known moves reduced raw row count");
        for(unsigned j=0;j<4;j++)known[j]=j<s->tutor_count?s->tutor[j]:0;
        moves(c,known);page(c,s,7,known,1);
        /* Party slot5 must resolve the same owner; slot6 and 65535 must deny. */
        for(unsigned j=0;j<POKEMON_SIZE;j++)write8(c,ADDR_PLAYER_PARTY+5*POKEMON_SIZE+j,read8(c,ADDR_PLAYER_PARTY+j));
        write16(c,0x02036FF4U,5);
        if(readonly(c,hooks[2],0,0)!=s->machine_count)battle_core_die("selected slot5 resolution");
        ++selection_checks;
        for(unsigned j=0;j<2;j++){
            write16(c,0x02036FF4U,j?65535:6);
            if(readonly(c,hooks[2],0,0))battle_core_die("invalid selected party slot");
            write8(c,0x0203EC00U,3);write16(c,0x02037004U,0xA55A);
            (void)readonly(c,hooks[3],0,0);
            if(read16(c,0x02037004U))battle_core_die("invalid slot readiness");
            ++selection_checks;
        }
        write16(c,0x02036FF4U,0);setdata(c,45,1);
        if(readonly(c,hooks[2],0,0))battle_core_die("egg row count");
        for(unsigned mode=2;mode<=7;mode++)page(c,s,mode,known,0);
        for(unsigned id=0;id<64;id++)if(readonly(c,hooks[0],ADDR_PLAYER_PARTY,id))battle_core_die("egg ordinary tutor");
        for(unsigned id=152;id<=160;id++)if(readonly(c,hooks[0],ADDR_PLAYER_PARTY,id))battle_core_die("egg special tutor");
        setdata(c,45,0);
        page(c,s,8,known,0);page(c,s,255,known,0);
        if(readonly(c,hooks[0],0,0) || readonly(c,hooks[0],0,152) || readonly(c,hooks[1],0,0x0203C100U) || readonly(c,hooks[1],ADDR_PLAYER_PARTY,0))battle_core_die("null input");
    }
    for(unsigned i=0;i<4;i++)if(!hook_seen[i])battle_core_die("unreached hook");
    if(!tutor_yes || !tutor_no || !specials_yes || !specials_no || !page_four || !filtered || log_problem_count)battle_core_die("vacuous coverage or mGBA warning/error");
    printf("{\"status\":\"PASS_NEW_SUPPLY_FOUR_HOOKS\",\"scope\":\"HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E\",\"candidate_sha256\":\"%s\",\"samples\":%zu,\"calls\":%u,\"readonly_checks\":%u,\"hook_calls\":[%u,%u,%u,%u],\"ordinary_allowed\":%u,\"ordinary_denied\":%u,\"special_allowed\":%u,\"special_denied\":%u,\"archive_pages\":%u,\"archive_denied\":%u,\"raw_boundary_filtered_samples\":%u,\"page_four_nonempty\":%u,\"selection_checks\":%u,\"real_flag_checks\":%u,\"stored_four_moves_and_pp_preserved\":true,\"buffer_canaries_preserved\":true,\"new_code_pc_seen_for_every_hook_call\":true,\"physical_supply_verified\":false,\"gameplay_e2e_accepted\":false}\n",sha,ARRAY_LEN(supply_samples),calls,checks,hook_seen[0],hook_seen[1],hook_seen[2],hook_seen[3],tutor_yes,tutor_no,specials_yes,specials_no,pages,denied,filtered,page_four,selection_checks,gates);
    mCoreConfigDeinit(&c->config);c->deinit(c);return 0;
}
