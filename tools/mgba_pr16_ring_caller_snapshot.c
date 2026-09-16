/* Read-only, instruction-bounded observation of the original FlagSet body.
 * This is a BOOT caller diagnostic, not the map97/80 Ring acquisition route.
 * No game function invocation, register/memory writes, ROM patch, or savestate
 * restore is available in this driver. Reset and ordinary keypad input only.
 */
#define _POSIX_C_SOURCE 200809L
#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <mgba/core/config.h>
#include <mgba/core/core.h>

#define ENTRY 0x093789F2U
#define LIMIT UINT64_C(240000000)
#define CALL_LIMIT 4096U
#define MAX_HITS 8U

static uint32_t reg(struct mCore *c, const char *name) {
    int32_t v = 0;
    if (!c->readRegister(c, name, &v)) { fprintf(stderr,"register read failed\n"); exit(3); }
    return (uint32_t)v;
}
static uint32_t r8(struct mCore *c,uint32_t a) { return c->rawRead8(c,a,-1)&255U; }
static uint32_t r16(struct mCore *c,uint32_t a) { return c->rawRead16(c,a,-1)&65535U; }
static uint32_t r32(struct mCore *c,uint32_t a) { return c->rawRead32(c,a,-1); }
static bool ram(uint32_t a,unsigned n) {
    return n && ((a>=0x02000000U && a<=0x02040000U-n)
              || (a>=0x03000000U && a<=0x03008000U-n));
}
/* mGBA's public PC read at the pre-step boundary is one instruction ahead.
 * Raw PC and CPSR are both retained; Python independently checks normalization.
 */
static uint32_t pc(struct mCore *c,uint32_t cpsr) {
    return (reg(c,"pc")&~1U)-((cpsr&32U)?2U:4U);
}
static uint32_t dma(struct mCore *c) {
    return r16(c,0x040000BAU)|r16(c,0x040000C6U)
         | r16(c,0x040000D2U)|r16(c,0x040000DEU);
}
static uint32_t pointer(uint32_t id,uint32_t save) {
    if (!id) return 0U;
    if(id<2304U) return save+0xEE0U+(id>>3);
    if(id<6400U) return 0x0203B0E8U+((id-2304U)>>3);
    if(id<16384U) return 0x02036FECU;
    return 0x02037014U+((id-16384U)>>3);
}

static bool capture(struct mCore *c,uint64_t start,unsigned ordinal) {
    uint32_t cpsr=reg(c,"cpsr"),raw_pc=reg(c,"pc"),id=reg(c,"r0");
    uint32_t sp=reg(c,"sp"),lr=reg(c,"lr"),r4=reg(c,"r4"),minimum=sp;
    uint32_t save=r32(c,0x03005048U),base=r32(c,0x0300202CU);
    uint32_t selector=r8(c,0x03005ED8U),count=r16(c,0x0203AF10U);
    uint32_t limit=r16(c,0x03005EDCU),index=r16(c,0x0203AF96U),capacity=r16(c,0x03002030U);
    uint32_t flag=pointer(id&65535U,save);
    uint64_t record_wide=(uint64_t)base+4U*index;
    uint32_t record=(uint32_t)record_wide;
    bool record_ok=record_wide<=UINT32_MAX && !(record&3U) && ram(record,4U);
    bool flag_ok=flag && ram(flag,1U);
    uint32_t word=record_ok?r32(c,record):0U,byte=flag_ok?r8(c,flag):0U;
    uint32_t mapping=r32(c,0x04000800U),dma_enable=dma(c)&0x8000U;
    uint32_t first_ime=r16(c,0x04000208U),first_ie=r16(c,0x04000200U);
    bool mode_stable=true,mapping_stable=true,dma_disabled=!dma_enable;
    bool returned=false; unsigned steps=0U;
    printf("{\"kind\":\"entry\",\"ordinal\":%u,\"step\":%"PRIu64",\"raw_pc\":%u,\"cpsr\":%u,\"r0\":%u,\"r4\":%u,",ordinal,start,raw_pc,cpsr,id,r4);
    printf("\"snapshot\":{\"id\":%u,\"selector\":%u,\"sp\":%u,\"lr\":%u,\"save_base\":%u,\"record_base\":%u,\"count\":%u,\"limit\":%u,\"index\":%u,\"capacity\":%u,\"record_word\":%u,\"flag_byte\":%u},",id&65535U,selector,sp,lr,save,base,count,limit,index,capacity,word,byte);
    printf("\"record_readable\":%s,\"flag_readable\":%s,\"memory_control\":%u,\"ime\":%u,\"ie\":%u,\"dma_enable\":%u}\n",record_ok?"true":"false",flag_ok?"true":"false",mapping,first_ime,first_ie,dma_enable);
    fflush(stdout);
    for(steps=0U;steps<CALL_LIMIT;++steps) {
        uint32_t state=reg(c,"cpsr"),at=pc(c,state),now_sp=reg(c,"sp");
        if(now_sp<minimum)minimum=now_sp;
        if((state&31U)!=(cpsr&31U))mode_stable=false;
        if(r32(c,0x04000800U)!=mapping)mapping_stable=false;
        if(dma(c)&0x8000U)dma_disabled=false;
        if(steps && at==(lr&~1U) && (state&32U)) {returned=true;break;}
        /* Numeric PC sequence is essential for observing a real execution,
         * rather than promoting a hand-built snapshot to runtime evidence. */
        printf("{\"kind\":\"pc\",\"ordinal\":%u,\"offset\":%u,\"pc\":%u,\"sp\":%u,\"cpsr\":%u}\n",ordinal,steps,at,now_sp,state);
        c->step(c);
    }
    printf("{\"kind\":\"exit\",\"ordinal\":%u,\"returned\":%s,\"steps\":%u,\"raw_pc\":%u,\"cpsr\":%u,\"sp\":%u,\"r0\":%u,\"r4\":%u,\"minimum_sp\":%u,",ordinal,returned?"true":"false",steps,reg(c,"pc"),reg(c,"cpsr"),reg(c,"sp"),reg(c,"r0"),reg(c,"r4"),minimum);
    printf("\"saved_lr_word\":%u,\"saved_r4_word\":%u,\"record_word_after\":%u,\"flag_byte_after\":%u,\"counter_after\":%u,\"pending_id_after\":%u,",sp>=8U && ram(sp-4U,4U)?r32(c,sp-4U):0U,sp>=8U && ram(sp-8U,4U)?r32(c,sp-8U):0U,record_ok?r32(c,record):0U,flag_ok?r8(c,flag):0U,r16(c,0x0203AF96U),r16(c,0x030050BCU));
    printf("\"cpu_mode_stable\":%s,\"memory_control_stable\":%s,\"dma_disabled_at_step_boundaries\":%s}\n",mode_stable?"true":"false",mapping_stable?"true":"false",dma_disabled?"true":"false");fflush(stdout);
    return returned;
}

int main(int argc,char **argv) {
    if(argc!=3)return 2;
    struct mCore *c=mCoreFind(argv[1]);
    if(!c || !c->init(c) || !mCoreLoadFile(c,argv[1]))return 3;
    if(!mCoreLoadSaveFile(c,argv[2],false))return 3;
    mCoreInitConfig(c,NULL);
    mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");
    color_t *video=calloc(240U*160U,sizeof(*video));if(!video)return 3;
    c->setVideoBuffer(c,video,240U);c->reset(c);c->setKeys(c,0U);
    /* Cold title preparation is not an acquisition/Save/Continue test. */
    for(unsigned f=0U;f<1200U;++f)c->runFrame(c);
    unsigned first_frame=c->frameCounter(c),old_frame=~0U,hits=0U;
    uint64_t steps;
    for(steps=0;steps<LIMIT && hits<MAX_HITS;++steps) {
        unsigned frame=c->frameCounter(c)-first_frame;
        if(frame!=old_frame){
            c->setKeys(c,frame<2U?8U:(frame>180U && frame%90U==0U?1U:0U));old_frame=frame;
        }
        uint32_t state=reg(c,"cpsr");
        if((state&32U) && pc(c,state)==ENTRY) {
            if(!capture(c,steps,++hits))break;
        } else c->step(c);
    }
    printf("{\"kind\":\"summary\",\"hits\":%u,\"search_steps\":%"PRIu64",\"search_limit\":%"PRIu64",\"unobserved_title_frames\":1200,\"host_memory_writes\":0,\"host_register_writes\":0,\"host_function_calls\":0,\"savestate_loads\":0,\"ring_acquisition_accepted\":false}\n",hits,steps,LIMIT);
    mCoreConfigDeinit(&c->config);c->deinit(c);free(video);return 0;
}
