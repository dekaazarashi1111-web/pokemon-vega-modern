/* 通常calleeだけの読取/step観測。真正退出Saveからの状態注入はない。 */
struct SSRoute {const char *name;uint32_t root,target,normal,suppressed;unsigned preserve_r3;};
#include "po_routes.h"
struct SSCall {bool active;unsigned length,bank,ability;uint32_t r3,lr,entry_r12,pcs[128];};
static struct SSCall po_predicate,po_dispatch[29];
static unsigned po_predicates,po_delegates,po_trace_frames;
static uint64_t po_instructions;
static void (*po_fast_frame)(struct mCore *);
static uint32_t po_reg(struct mCore *c,const char *name){
    uint32_t value=0U;bp_require(c,c->readRegister(c,name,&value),"suppression register read failed");return value;
}
static void po_pc_add(struct mCore *c,struct SSCall *call,uint32_t pc){
    if(!call->active || pc<0x08000000U || pc>=0x0A000000U)return;
    bp_require(c,call->length<128U,"suppression native call trace bound");call->pcs[call->length++]=pc;
}
static void po_pcs(const struct SSCall *call){
    fprintf(stderr,"\"pcs\":[");for(unsigned i=0;i<call->length;++i)fprintf(stderr,"%s%u",i?",":"",call->pcs[i]);fprintf(stderr,"]");
}
static void po_observe(struct mCore *c){
    uint32_t cpsr=po_reg(c,"cpsr"),raw=po_reg(c,"pc");
    uint32_t pc=(raw&~1U)-((cpsr&32U)?2U:4U);
    if(!(cpsr&32U))return;
    unsigned flags=read32(c,CF_FLAGS),types=read32(c,CF_TYPES);
    bp_require(c,!flags && !(types&CF_CIRCUS_BIT),"Circus suppression leaked into ordinary battle");
    if(po_predicate.active){
        po_pc_add(c,&po_predicate,pc);
        if(pc==(po_predicate.lr&~1U)){
            unsigned result=po_reg(c,"r0");
            fprintf(stderr,"P08_ORDINARY_CALL {\"kind\":\"predicate\",\"frame\":%u,\"flags\":%u,\"types\":%u,\"bank\":%u,\"raw_ability\":%u,\"result\":%u,\"return_pc\":%u,\"host_writes\":0,\"host_calls\":0,",b_frames,flags,types,po_predicate.bank,po_predicate.ability,result,pc);
            po_pcs(&po_predicate);fprintf(stderr,"}\n");po_predicate.active=false;++po_predicates;
            bp_require(c,result==0U,"ordinary ability suppression did not return false");
        }
    }
    for(unsigned i=0;i<29U;++i){
        const struct SSRoute *route=&po_routes[i];struct SSCall *call=&po_dispatch[i];
        if(call->active){
            po_pc_add(c,call,pc);
            if(pc==route->normal && route->preserve_r3){
                call->entry_r12=po_reg(c,"r12");
                bp_require(c,read16(c,pc)==0x4663U && call->entry_r12==call->r3,
                    "Stage72 mov r3,r12 or incoming fourth argument differs");
            }
            uint32_t restored=route->normal+(route->preserve_r3?2U:0U);
            bp_require(c,pc!=route->suppressed,"ordinary reached suppressed trampoline");
            if(pc==restored){
                uint32_t after=po_reg(c,"r3");
                fprintf(stderr,"P08_ORDINARY_CALL {\"kind\":\"dispatch\",\"name\":\"%s\",\"frame\":%u,\"flags\":%u,\"types\":%u,\"root\":%u,\"delegate\":%u,\"expected_normal\":%u,\"preserve_r3\":%s,\"r3_before\":%u,\"r3_after\":%u,\"entry_r12\":%u,\"restored_pc\":%u,\"host_writes\":0,\"host_calls\":0,",route->name,b_frames,flags,types,route->root,route->normal,route->normal,route->preserve_r3?"true":"false",call->r3,after,call->entry_r12,pc);
                po_pcs(call);fprintf(stderr,"}\n");call->active=false;++po_delegates;
                bp_require(c,!route->preserve_r3 || call->r3==after,"Stage72 entry did not restore fourth argument");
            }
        }
        if(pc==route->root && po_delegates<12U){
            bp_require(c,!call->active,"nested dispatcher entry");memset(call,0,sizeof(*call));call->active=true;call->r3=po_reg(c,"r3");po_pc_add(c,call,pc);
        }
    }
    if(pc==0x090D7BB0U && po_predicates<8U){
        unsigned bank=po_reg(c,"r0");
        if(bank<2U){
            unsigned ability=read16(c,ADDR_BATTLE_MONS+bank*0x58U+0x38U);
            if(ability){bp_require(c,!po_predicate.active,"nested suppression predicate");memset(&po_predicate,0,sizeof(po_predicate));po_predicate.active=true;po_predicate.bank=bank;po_predicate.ability=ability;po_predicate.lr=po_reg(c,"lr");po_pc_add(c,&po_predicate,pc);}
        }
    }
}
static void po_frame(struct mCore *c){
    if(!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)){po_fast_frame(c);return;}
    if(po_trace_frames>=600U || (po_predicates>=4U && po_delegates>=4U)) {po_fast_frame(c);return;}
    ++po_trace_frames;unsigned start=c->frameCounter(c),steps=0U;
    do {po_observe(c);c->step(c);++po_instructions;bp_require(c,++steps<2000000U,"instruction observation frame bound");}while(c->frameCounter(c)==start);
}
