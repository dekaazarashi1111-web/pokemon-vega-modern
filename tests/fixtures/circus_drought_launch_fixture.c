#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../overlays/circus_streak/circus_drought_launch.h"
static uint8_t weather[0x800];
static unsigned originals,inits,steps,stuck;
static CircusDroughtContext good(void){CircusDroughtContext c={1,1,1,2,1,3,0,12,12,1,1,0x08055E75u,0x09FF4DADu};return c;}
static void original(void){++originals;}
static void init(void){++inits;weather[0x6CC]=0;weather[0x6D2]=0;}
static void step(void){
    assert(++steps<=256u);if(stuck)return;
    switch(weather[0x6CC]){
    case 0:++weather[0x6CC];break;
    case 1:weather[0x74D]=1;weather[0x74E]=1;++weather[0x6CC];break;
    case 2:assert(weather[0x74D]==32 && weather[0x74E]==32);++weather[0x6CC];break;
    case 3:++weather[0x6CC];break;
    case 4:weather[0x6D2]=1;++weather[0x6CC];break;
    default:assert(0);
    }
}
int main(void){
    unsigned combinations=0;assert(!CircusDroughtLaunchAllowed(NULL));
    const uint32_t scripts[]={0x09FF4CEBu,0x09FF4D4Cu,0x09FF4DADu};
    for(unsigned s=0;s<3u;++s){
        CircusDroughtContext c=good();c.script=scripts[s];
        for(unsigned f=0;f<11u;++f)for(unsigned v=0;v<256u;++v){
            CircusDroughtContext x=c;((uint8_t *)&x)[f]=v;
            int valid=v==((uint8_t *)&c)[f];assert(CircusDroughtLaunchAllowed(&x)==valid);
            if(!valid){
                memset(weather,0xA5,sizeof(weather));uint8_t before[sizeof(weather)];memcpy(before,weather,sizeof(weather));
                originals=inits=steps=0;CircusDroughtInitializeLaunch(&x,weather,original,init,step);
                assert(originals==1 && inits==0 && steps==0 && !memcmp(weather,before,sizeof(weather)));
            }
            ++combinations;
        }
        for(unsigned bit=0;bit<32u;++bit){CircusDroughtContext x=c;x.callback^=1u<<bit;assert(!CircusDroughtLaunchAllowed(&x));}
        memset(weather,0,sizeof(weather));originals=inits=steps=stuck=0;
        CircusDroughtInitializeLaunch(&c,weather,original,init,step);
        assert(originals==0 && inits==1 && steps==5 && weather[0x6CC]==5 && weather[0x6D2]==1);
        assert(c.outcome==0 && c.script==scripts[s]);
    }
    CircusDroughtContext c=good();c.script=0x09FF4D77u;c.outcome=1;
    memset(weather,0,sizeof(weather));originals=inits=steps=stuck=0;
    CircusDroughtInitializeLaunch(&c,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==5); /* 旧WINを維持 */
    c.outcome=0;originals=inits=steps=0;CircusDroughtInitializeLaunch(&c,weather,original,init,step);
    assert(originals==1 && inits==0 && steps==0); /* WIN位置でoutcome0を許可しない */
    c=good();memset(weather,0,sizeof(weather));originals=inits=steps=0;stuck=1;
    CircusDroughtInitializeLaunch(&c,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==256 && weather[0x6D2]==0);
    printf("circus_launch combinations=%u scoped-zero-outcome/native-only-completion/bound PASS\n",combinations);
    return 0;
}
