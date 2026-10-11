/* Issue19: direct-entry fixture diagnostic, NOT rod/scanner UI acceptance.
 * No emulated memory/register mutation while the native call is observed. */
#define main special_wild_unused_regression_main
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_regression_smoke.c"
#pragma GCC diagnostic pop
#undef main
#include <string.h>

static unsigned violations;
#define DENY(N,T) static void N(struct mCore*c,uint32_t a,T v){(void)c;(void)a;(void)v;++violations;die("host write inside native observation");}
DENY(deny8,uint8_t)
DENY(deny16,uint16_t)
DENY(deny32,uint32_t)
/* Keep the raw API signature distinct from bus writes. */
static void raw8(struct mCore*c,uint32_t a,int s,uint8_t v){(void)s;deny8(c,a,v);}
static void raw16(struct mCore*c,uint32_t a,int s,uint16_t v){(void)s;deny16(c,a,v);}
static void raw32(struct mCore*c,uint32_t a,int s,uint32_t v){(void)s;deny32(c,a,v);}
static bool denyreg(struct mCore*c,const char*n,const void*v){(void)c;(void)n;(void)v;++violations;die("host write inside native observation");return false;}
static void guard(struct mCore*c){c->busWrite8=deny8;c->busWrite16=deny16;c->busWrite32=deny32;c->rawWrite8=raw8;c->rawWrite16=raw16;c->rawWrite32=raw32;c->writeRegister=denyreg;}
static void unguard(struct mCore*c,const struct mCore*s){c->busWrite8=s->busWrite8;c->busWrite16=s->busWrite16;c->busWrite32=s->busWrite32;c->rawWrite8=s->rawWrite8;c->rawWrite16=s->rawWrite16;c->rawWrite32=s->rawWrite32;c->writeRegister=s->writeRegister;}
static void reject_test(const char*n){
    struct mCore c={0};uint32_t v=0;guard(&c);
    if(!strcmp(n,"bus8"))c.busWrite8(&c,0,0);
    else if(!strcmp(n,"bus16"))c.busWrite16(&c,0,0);
    else if(!strcmp(n,"bus32"))c.busWrite32(&c,0,0);
    else if(!strcmp(n,"raw8"))c.rawWrite8(&c,0,0,0);
    else if(!strcmp(n,"raw16"))c.rawWrite16(&c,0,0,0);
    else if(!strcmp(n,"raw32"))c.rawWrite32(&c,0,0,0);
    else if(!strcmp(n,"register"))(void)c.writeRegister(&c,"pc",&v);
    exit(2);
}
static void dump_mon(struct mCore*c,const char*label,unsigned attempt,uint64_t step){
    printf("{\"event\":\"%s\",\"attempt\":%u,\"step\":%" PRIu64 ",\"party\":\"",label,attempt,step);
    for(unsigned i=0;i<100U;++i)printf("%02x",read8(c,ENEMY_PARTY+i));
    printf("\"}\n");fflush(stdout);
}
static uint32_t observed(struct mCore*c,uint32_t function,uint32_t r0,uint32_t r1,unsigned attempt,uint32_t qb,uint32_t qe,unsigned*special,unsigned*apply){
    struct CpuContext cpu=capture_cpu(c);struct mCore api=*c;
    write_register(c,"cpsr",cpu.registers[16]|0xA0);write_register(c,"lr",0x08000001);
    write_register(c,"r0",(int32_t)r0);write_register(c,"r1",(int32_t)r1);
    write_register(c,"r2",0);write_register(c,"r3",0);write_register(c,"pc",(int32_t)function);
    uint64_t steps=0;guard(c);*special=0;*apply=0;
    for(;;){
        uint32_t pc=(uint32_t)read_register(c,"pc")&~1U;
        if(pc==0x08000002U)break;
        if(++steps>MAX_CALL_STEPS)die("special wild bounded native call did not return");
        uint32_t at=pc-2U,lr=(uint32_t)read_register(c,"lr");
        if(at==0x08082750U||at==0x09220198U||at==0x093BEA68U||at==0x093BEA98U||at==0x09392714U||at==0x0939273CU)
            printf("{\"event\":\"entry\",\"attempt\":%u,\"step\":%" PRIu64 ",\"pc\":%u,\"lr\":%u}\n",attempt,steps,at,lr);
        if(at==0x09114698U && lr>=qb && lr<qe && (uint32_t)read_register(c,"r0")==ENEMY_PARTY && read_register(c,"r2")==3){
            ++*special;printf("{\"event\":\"special_setter\",\"attempt\":%u,\"step\":%" PRIu64 ",\"pc\":%u,\"lr\":%u,\"move\":%u,\"slot\":3}\n",attempt,steps,at,lr,(unsigned)read_register(c,"r1"));
        }
        if(at==0x093925F4U){++*apply;dump_mon(c,"before_apply",attempt,steps);}
        c->step(c);
    }
    uint32_t result=(uint32_t)read_register(c,"r0");dump_mon(c,"after_return",attempt,steps);
    unguard(c,&api);restore_cpu(c,&cpu);return result;
}
int main(int argc,char**argv){
    if(argc==3&&!strcmp(argv[1],"--reject"))reject_test(argv[2]);
    if(argc!=6){fprintf(stderr,"usage: probe ROM fishing|hidden DISPATCH QOL_START QOL_END\n");return 2;}
    bool fishing=!strcmp(argv[2],"fishing");if(!fishing&&strcmp(argv[2],"hidden"))return 2;
    uint32_t dispatch=parse_u32(argv[3],"dispatch"),qb=parse_u32(argv[4],"QOL start"),qe=parse_u32(argv[5],"QOL end");
    if(!rom_code_pointer(dispatch)||qb<ROM_BASE||qe>ROM_END||qb>=qe)die("QOL address contract");
    struct mLogger logger={.log=silent_log,.filter=NULL};mLogSetDefaultLogger(&logger);
    struct mCore*c=mCoreFind(argv[1]);if(!c||!c->init(c)||!mCoreLoadFile(c,argv[1]))die("core init");
    mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");
    color_t*video=calloc(GBA_WIDTH*GBA_HEIGHT,sizeof(*video));if(!video)die("video");c->setVideoBuffer(c,video,GBA_WIDTH);c->reset(c);
    uint32_t transitions=run_natural_new_game(c,video),save=read32(c,G_SAVE_BLOCK1);
    if(save<0x02000000U||save+6U>=0x02040000U)die("save pointer");
    /* Explicit initial fixture only, NOT proof of normal unlock acquisition. */
    for(unsigned f=0x0820U;f<=0x082CU;++f)(void)call_thumb(c,0x0806DE75U,f,0,0,0);
    (void)call_thumb(c,0x0806DE75U,0x114BU,0,0,0);
    uint32_t status=call_thumb(c,dispatch,15U,1U,0,0);
    printf("{\"event\":\"fixture\",\"method\":\"%s\",\"dispatch_status\":%u,\"profile\":%u,\"transitions\":%u,\"normal_unlock_claimed\":false}\n",argv[2],status,read8(c,0x0203D01FU),transitions);fflush(stdout);
    if(status!=0U||read8(c,0x0203D01FU)!=1U)die("native RESEARCH profile fixture not enabled");
    uint32_t info=0,root=read32(c,0x0808257CU);if(!rom_pointer(root))die("wild root");
    for(unsigned i=0;i<1024U;++i){uint32_t h=root+20U*i;unsigned g=read8(c,h),m=read8(c,h+1U);if(g==255U&&m==255U)break;if(g==11U&&m==3U)info=read32(c,h+16U);}
    if(fishing&&!rom_pointer(info))die("fishing fixture table absent");
    write8(c,save+4U,fishing?11U:3U);write8(c,save+5U,fishing?3U:63U);
    unsigned specials=0,applies=0,attempt=0;
    for(attempt=1U;attempt<=8U;++attempt){
        for(unsigned i=0;i<PARTY_BYTES;++i)write8(c,ENEMY_PARTY+i,0);
        write8(c,ENEMY_PARTY_COUNT,0);uint32_t seed=(fishing?0x24681357U:0x10293847U)+attempt-1U;write32(c,GLOBAL_RNG,seed);
        printf("{\"event\":\"call\",\"attempt\":%u,\"seed\":%u,\"entry\":%u,\"map\":[%u,%u]}\n",attempt,seed,fishing?0x08082751U:0x09220199U,fishing?11U:3U,fishing?3U:63U);
        uint32_t result=observed(c,fishing?0x08082751U:0x09220199U,fishing?info:0,fishing?2U:0,attempt,qb,qe,&specials,&applies);
        printf("{\"event\":\"result\",\"attempt\":%u,\"returned\":%u,\"species\":%u,\"special_setters\":%u,\"apply_calls\":%u}\n",attempt,result,(unsigned)call_thumb(c,GET_MON_DATA,ENEMY_PARTY,11U,0,0),specials,applies);fflush(stdout);
        if(specials&&applies)break;
    }
    printf("{\"event\":\"summary\",\"status\":\"%s\",\"method\":\"%s\",\"calls\":%u,\"host_write_violations\":%u,\"direct_call_fixture\":true,\"gameplay_accepted\":false,\"save_continue_accepted\":false}\n",specials&&applies?"OBSERVED":"NO_SPECIAL_WITNESS",argv[2],attempt<=8U?attempt:8U,violations);
    free(video);mCoreConfigDeinit(&c->config);c->deinit(c);return specials&&applies?0:1;
}
