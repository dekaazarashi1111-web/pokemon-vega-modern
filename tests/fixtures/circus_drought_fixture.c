#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../overlays/circus_streak/circus_drought.h"
static uint8_t weather[0x800];
static unsigned originals, inits, steps, stuck;
static CircusDroughtContext good(void)
{
    CircusDroughtContext c = {1,1,1,2,1,3,1,12,12,1,1,0x08055E75u,0x09FF4D77u};
    return c;
}
static void original(void) {++originals;}
static void init(void) {++inits;weather[0x6CC]=0;weather[0x6D2]=0;}
static void step(void)
{
    assert(++steps <= 256u);
    if (stuck) return;
    switch(weather[0x6CC]) {
    case 0: ++weather[0x6CC];break;
    case 1: weather[0x74D]=1;weather[0x74E]=1;++weather[0x6CC];break;
    case 2: assert(weather[0x74D]==32 && weather[0x74E]==32);++weather[0x6CC];break;
    case 3: ++weather[0x6CC];break;
    case 4: weather[0x6D2]=1;++weather[0x6CC];break;
    default: assert(0);
    }
}
int main(void)
{
    CircusDroughtContext c=good();unsigned combinations=0;
    assert(!CircusDroughtAllowed(NULL));
    for(unsigned field=0;field<11;++field) for(unsigned v=0;v<256;++v) {
        CircusDroughtContext changed=good();uint8_t *p=(uint8_t *)&changed;p[field]=(uint8_t)v;
        int expected=field==5 ? (v>=1 && v<=6) : v==((uint8_t *)&c)[field];
        assert(CircusDroughtAllowed(&changed)==expected);
        if(!expected) {
            memset(weather,0xA5,sizeof(weather));uint8_t before[sizeof(weather)];memcpy(before,weather,sizeof(weather));
            originals=inits=steps=0;CircusDroughtInitialize(&changed,weather,original,init,step);
            assert(originals==1 && inits==0 && steps==0 && !memcmp(before,weather,sizeof(weather)));
        }
        ++combinations;
    }
    const uint32_t scripts[]={0x09FF4D16u,0x09FF4D77u,0x09FF4DD8u,0x092CF669u,0};
    for(unsigned s=0;s<5;++s) {c=good();c.script=scripts[s];assert(CircusDroughtAllowed(&c)==(s<3));}
    for(unsigned bit=0;bit<32;++bit) {c=good();c.callback^=1u<<bit;assert(!CircusDroughtAllowed(&c));}
    for(unsigned state=0;state<8;++state) for(unsigned index=0;index<256;++index)
    for(unsigned offset=0;offset<256;++offset) {
        memset(weather,0xA5,sizeof(weather));weather[0x6CC]=state;weather[0x6CD]=0;weather[0x74D]=index;weather[0x74E]=offset;
        uint8_t before[sizeof(weather)];memcpy(before,weather,sizeof(weather));
        int changed=CircusDroughtEmptyLoader(weather);
        assert(changed==(state==2 && index==1 && offset==1));
        if(changed) {before[0x74D]=32;before[0x74E]=32;}
        assert(!memcmp(before,weather,sizeof(weather)));++combinations;
    }
    c=good();memset(weather,0,sizeof(weather));originals=inits=steps=0;stuck=0;
    CircusDroughtInitialize(&c,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==5 && weather[0x6D2]==1 && weather[0x6CC]==5);
    memset(weather,0,sizeof(weather));originals=inits=steps=0;stuck=1;
    CircusDroughtInitialize(&c,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==256 && weather[0x6D2]==0);
    printf("circus_drought combinations=%u scope/fallback/write-set/native-completion/bound PASS\n",combinations);
    return 0;
}
