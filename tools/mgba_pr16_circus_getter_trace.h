/* 正規sp072呼出しの５引数と戻り値のみをCPU step/readで観測する。 */
#include "cg_addresses.h"
static void (*cg_fast)(struct mCore *);
static unsigned cg_phase,cg_frames,cg_returns;
static uint32_t cg_args[4],cg_sp,cg_fifth,cg_r3;
static uint64_t cg_steps;
static uint32_t cg_reg(struct mCore *c,const char *name){
    uint32_t value=0U;bp_require(c,c->readRegister(c,name,&value),"getter register read failed");return value;
}
static void cg_observe(struct mCore *c){
    uint32_t psr=cg_reg(c,"cpsr"),pc=cg_reg(c,"pc");
    if(!(psr&32U))return;
    pc=(pc&~1U)-2U;
    if(pc==0x09103380U && !cg_phase){
        cg_args[0]=cg_reg(c,"r0");cg_args[1]=cg_reg(c,"r1");
        cg_args[2]=cg_reg(c,"r2");cg_args[3]=cg_reg(c,"r3");
        cg_sp=cg_reg(c,"sp");cg_fifth=read32(c,cg_sp);cg_phase=1U;
        bp_require(c,sc_current(c)==30U && sc_phase(c)==2U,"getter not in genuine armed30");
    }
    if(pc==(CG_TARGET&~1U) && cg_phase==1U){
        cg_r3=cg_reg(c,"r3");
        bp_require(c,cg_reg(c,"r0")==cg_args[0] && cg_reg(c,"r1")==cg_args[1]
            && cg_reg(c,"r2")==cg_args[2] && cg_r3==cg_args[3]
            && cg_reg(c,"sp")==cg_sp && read32(c,cg_sp)==cg_fifth
            && cg_reg(c,"lr")==0x09103385U,"getter veneer corrupted argument/SP/LR");
        cg_phase=2U;
    }
    if(pc==0x09103384U && cg_phase==2U){
        unsigned result=cg_reg(c,"r0");
        fprintf(stderr,"CIRCUS_GETTER_ABI {\"callsite\":%u,\"veneer\":%u,\"target\":%u,\"args\":[%u,%u,%u,%u],\"r3_at_entry\":%u,\"fifth_argument\":%u,\"sp_before\":%u,\"sp_after\":%u,\"result\":%u,\"owner_current\":%u,\"phase\":%u,\"frames\":%u,\"steps\":%llu,\"host_writes\":0,\"host_calls\":0}\n",0x09103380U,CG_VENEER,CG_TARGET,cg_args[0],cg_args[1],cg_args[2],cg_args[3],cg_r3,cg_fifth,cg_sp,cg_reg(c,"sp"),result,sc_current(c),sc_phase(c),cg_frames,(unsigned long long)cg_steps);
        fflush(stderr);bp_require(c,result==30U && cg_reg(c,"sp")==cg_sp,"natural getter did not return genuine30");
        cg_phase=3U;++cg_returns;
    }
}
static void cg_frame(struct mCore *c){
    if(cg_returns){cg_fast(c);return;}
    bp_require(c,++cg_frames<=1200U,"getter observation frame bound");
    unsigned frame=c->frameCounter(c),steps=0U;
    do{cg_observe(c);c->step(c);++cg_steps;bp_require(c,++steps<2000000U,"getter instruction bound");}while(c->frameCounter(c)==frame);
}
static void cg_begin(struct mCore *c){
    if(!cg_returns){bp_require(c,!cg_fast,"duplicate getter trace");cg_fast=c->runFrame;c->runFrame=cg_frame;}
}
static void cg_end(struct mCore *c){
    if(cg_fast && c->runFrame==cg_frame)c->runFrame=cg_fast;
    bp_require(c,cg_returns==1U,"natural getter return not observed");
}
