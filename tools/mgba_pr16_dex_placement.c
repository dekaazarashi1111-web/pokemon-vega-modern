/* Isolated linked ARMv4T API/veneer tests. No boot, battle, save or game hook. */
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mgba/core/core.h>
#include <mgba/core/config.h>
#include "overlays/dex_owner/dex_adapter.h"
#include "overlays/dex_owner/dex_compact_map.h"
#include "overlays/dex_owner/dex_save_bridge.h"

#define RAM 0x02000000u
#define ENTRY 0x09FC0998u
#define LIVE 0x3DB40u
#define SECTOR 0x6000u
#define SAVE1 0x1000u
#define SAVE2 0x7000u
#define LEGACY 0x8000u
#define SNAP 0x8200u
#define OUTPUT 0x8400u
#define STACK 0x03007E00u
static uint8_t original[0x40000], expected[0x40000];
static unsigned calls, steps;
static void need(int b, const char *s) { if (!b) { fprintf(stderr,"dex-placement: %s\n",s); exit(1); } }
static uint32_t reg(struct mCore *c, const char *n) { int32_t v=0; need(c->readRegister(c,n,&v),"read register"); return (uint32_t)v; }
static void set(struct mCore *c, const char *n, uint32_t v) { need(c->writeRegister(c,n,&v),"write fixture register"); }
static void put32(uint8_t *p, uint32_t v) { for(unsigned i=0;i<4;++i)p[i]=(uint8_t)(v>>(8*i)); }
static void setup(void) {
    memset(original,0xA5,sizeof(original));
    for(unsigned i=0;i<208;++i)original[LEGACY+i]=(uint8_t)(i*37u+11u);
    need(VegaDexInitLegacy(original+LIVE,522,original+LEGACY,208)==VEGA_DEX_OK,"host legacy fixture");
    uint8_t v;
    need(VegaDexSpeciesFlags(original+LIVE,522,129,VEGA_DEX_SET_CAUGHT,&v)==0,"native owner fixture");
    need(VegaDexSpeciesFlags(original+LIVE,522,1670,VEGA_DEX_SET_SEEN,&v)==0,"form owner fixture");
    original[SECTOR+0xFF4]=13;original[SECTOR+0xFF5]=0;
    put32(original+SECTOR+0xFF8,0x08012025);put32(original+SECTOR+0xFFC,101);
    need(VegaDexInjectSector(original+SECTOR,4096,original+LIVE,522,101,1)==0,"host sector fixture");
}
static uint32_t reference(unsigned test, uint32_t a[10],unsigned *argc) {
    uint8_t *m=expected,*live=m+LIVE,*sector=m+SECTOR,*snap=m+SNAP,*out=m+OUTPUT;
    *argc=0;
#define ARGS(...) do { const uint32_t q[]={__VA_ARGS__};*argc=sizeof(q)/sizeof(q[0]);memcpy(a,q,sizeof(q)); } while(0)
    switch(test) {
    case 0: ARGS(RAM+LIVE,522); return VegaDexChecksum(live,522);
    case 1: ARGS(RAM+LIVE,522); return VegaDexValidate(live,522);
    case 2: ARGS(RAM+LIVE,522); return VegaDexInitNew(live,522);
    case 3: ARGS(RAM+LIVE,522,RAM+LEGACY,208);return VegaDexInitLegacy(live,522,m+LEGACY,208);
    case 4: ARGS(RAM+LIVE,522,1206,3,RAM+OUTPUT);return VegaDexAccess(live,522,1206,3,out);
    case 5: ARGS(RAM+LIVE,522,1,RAM+OUTPUT);return VegaDexCount(live,522,1,(uint16_t*)out);
    case 6: ARGS(RAM+LIVE,522,RAM+SECTOR+0xDE6,522,RAM+LEGACY,208,1);return VegaDexLoad(live,522,sector+0xDE6,522,m+LEGACY,208,1);
    case 7: ARGS(RAM+LIVE,522,481,3,RAM+OUTPUT);return VegaDexSpeciesFlags(live,522,481,3,out);
    case 8: ARGS(RAM+LIVE,522,129,3,RAM+OUTPUT);return VegaDexOfficialFlags(live,522,129,3,out);
    case 9: ARGS(129,RAM+OUTPUT);return VegaDexOfficialRepresentative(129,(uint16_t*)out);
    case 10: ARGS(RAM+LIVE,522,1,RAM+OUTPUT);return VegaDexOfficialCount(live,522,1,(uint16_t*)out);
    case 11: ARGS(RAM+LIVE,522,129,RAM+SNAP,4);return VegaDexSnapshotSpecies(live,522,129,snap,4);
    case 12: ARGS(RAM+LIVE,522,129,RAM+SNAP,4);return VegaDexRestoreSpecies(live,522,129,snap,4);
    case 13: ARGS(RAM+LIVE,522,RAM+SNAP,151);return VegaDexSnapshotSeen(live,522,snap,151);
    case 14: ARGS(RAM+LIVE,522,RAM+SNAP,151);return VegaDexRestoreSeen(live,522,snap,151);
    case 15: ARGS(1670);return VegaDexCompactSpeciesOwner(1670);
    case 16: ARGS(744);return VegaDexCompactOfficialOwner(744);
    case 17: ARGS(925);return VegaDexCompactOwnerRepresentative(925);
    case 18: ARGS(RAM+SECTOR+0xDE6,522);return VegaDexClassifyRecord(sector+0xDE6,522);
    case 19: ARGS(RAM+SECTOR,4096,101,1);return VegaDexCheckSector(sector,4096,101,1);
    case 20: ARGS(RAM+SECTOR,4096,RAM+LIVE,522,101,1);return VegaDexInjectSector(sector,4096,live,522,101,1);
    case 21: ARGS(RAM+SECTOR,4096,RAM+LIVE,522,101,1,RAM+OUTPUT);return VegaDexTailMatches(sector,4096,live,522,101,1,out);
    case 22: ARGS(RAM+LIVE,522,RAM+SECTOR,4096,RAM+SAVE1,0x3D40,RAM+SAVE2,0xF24,101,1);return VegaDexLoadSelected(live,522,sector,4096,m+SAVE1,0x3D40,m+SAVE2,0xF24,101,1);
    case 23: ARGS(RAM+LIVE,522);return VegaDexInvalidateSession(live,522);
    default: need(0,"bounded API case");return 0;
    }
#undef ARGS
}
static void seed_cpu(struct mCore *c,unsigned api,const uint32_t a[10],unsigned argc) {
    set(c,"cpsr",0xDFu); /* system mode, IRQ+FIQ disabled, ARM until PC exchange */
    set(c,"sp",STACK);set(c,"lr",0x08000001u);
    for(unsigned i=0;i<12;++i) { char n[8];snprintf(n,sizeof(n),"r%u",i);set(c,n,i<4?(i<argc?a[i]:0x55000000u+i):0x77000000u+i); }
    for(unsigned i=0;i<6;++i)c->busWrite32(c,STACK+4*i,i+4<argc?a[i+4]:0x66000000u+i);
    set(c,"cpsr",0xFFu);set(c,"pc",(ENTRY+16u*api)|1u);
}
int main(int argc,char **argv) {
    need(argc==2,"one private placed ROM input");
    struct mCore *c=mCoreFind(argv[1]);need(c&&c->init(c),"core initialization");
    mCoreInitConfig(c,NULL);mCoreConfigSetDefaultValue(&c->config,"idleOptimization","ignore");
    need(mCoreLoadFile(c,argv[1]),"private candidate loaded");c->reset(c);
    unsigned veneer_cases=0,functional_cases=0;
    for(unsigned test=0;test<24;++test) {
        setup();
        if(test==12)need(VegaDexSnapshotSpecies(original+LIVE,522,129,original+SNAP,4)==0,"snapshot fixture");
        if(test==14)need(VegaDexSnapshotSeen(original+LIVE,522,original+SNAP,151)==0,"seen fixture");
        memcpy(expected,original,sizeof(original));uint32_t a[10]={0};unsigned n;uint32_t result=reference(test,a,&n);
        for(unsigned i=0;i<sizeof(original);++i)c->busWrite8(c,RAM+i,original[i]);
        seed_cpu(c,test,a,n);uint32_t target=c->busRead32(c,ENTRY+16*test+12);
        need((target&1u)&&target>ENTRY+24*16&&target<0x09FC22ECu,"owned Thumb implementation");
        for(unsigned i=0;i<5;++i) { c->step(c);++steps; }
        need((reg(c,"pc")&~1u)==(target&~1u)+2u,"veneer reaches exact implementation");
        for(unsigned i=0;i<4;++i){char r[8];snprintf(r,sizeof(r),"r%u",i);need(reg(c,r)==(i<n?a[i]:0x55000000u+i),"veneer preserves r0-r3");}
        need(reg(c,"sp")==STACK&&reg(c,"lr")==0x08000001u,"veneer preserves SP and LR");
        for(unsigned i=0;i<6;++i)need(c->busRead32(c,STACK+4*i)==(i+4<n?a[i+4]:0x66000000u+i),"veneer preserves stack arguments");
        ++veneer_cases;
        for(unsigned i=0;;++i){need(i<2000000,"bounded linked API instruction count");if((reg(c,"pc")&~1u)==0x08000002u)break;c->step(c);++steps;}
        need(reg(c,"r0")==result,"linked API return equals host reference");
        need(reg(c,"sp")==STACK,"callee stack restored");
        for(unsigned i=4;i<12;++i){char r[8];snprintf(r,sizeof(r),"r%u",i);need(reg(c,r)==0x77000000u+i,"callee-saved registers intact");}
        for(unsigned i=0;i<sizeof(expected);++i)need(c->busRead8(c,RAM+i)==expected[i],"all EWRAM equals reference; no non-owner clobber");
        ++functional_cases;++calls;
    }
    printf("{\"status\":\"PASS_PLACED_ARM_APIS_AND_VENEERS_ONLY\",\"native_processes\":1,\"fresh_cores\":1,\"api_calls\":%u,\"veneer_cases\":%u,\"functional_cases\":%u,\"steps\":%u,\"ewram_bytes_compared_per_case\":262144,\"game_boots\":0,\"ordinary_saves\":0,\"game_hooks_installed\":false,\"story_progress_accepted\":false}\n",calls,veneer_cases,functional_cases,steps);
    c->deinit(c);free(c);return 0;
}
