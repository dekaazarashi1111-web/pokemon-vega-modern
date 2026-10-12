#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../../overlays/circus_streak/circus_drought_selection.h"
#include "../../overlays/circus_streak/circus_drought_launch.h"
static uint8_t weather[0x800];
static unsigned originals,inits,steps,stuck;
static CircusDroughtContext good(void){CircusDroughtContext c={1,1,1,2,1,1,0,12,12,1,1,0x08055E75u,0x09FF4DADu};return c;}
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
static void reset(void){memset(weather,0,sizeof(weather));originals=inits=steps=stuck=0;}
int main(void){
    unsigned combinations=0;assert(!CircusDroughtSelectionAllowed(NULL,3));
    const uint32_t scripts[]={0x09FF4CEBu,0x09FF4D4Cu,0x09FF4DADu};
    for(unsigned s=0;s<3u;++s){
        CircusDroughtContext c=good();c.script=scripts[s];
        for(unsigned f=0;f<11u;++f)for(unsigned v=0;v<256u;++v){
            CircusDroughtContext x=c;((uint8_t *)&x)[f]=v;
            int valid=f==5u?(v>=1u && v<=6u):v==((uint8_t *)&c)[f];
            assert(CircusDroughtSelectionAllowed(&x,3)==valid);
            if(!valid){
                memset(weather,0xA5,sizeof(weather));uint8_t before[sizeof(weather)];memcpy(before,weather,sizeof(weather));
                originals=inits=steps=0;CircusDroughtInitializeSelection(&x,3,weather,original,init,step);
                assert(originals==1 && inits==0 && steps==0 && !memcmp(weather,before,sizeof(weather)));
            }
            ++combinations;
        }
        for(unsigned count=1;count<=6;++count){
            c.count=count;CircusDroughtContext before=c;
            for(unsigned selected=0;selected<256;++selected){
                assert(CircusDroughtSelectionAllowed(&c,selected)==(selected==3));++combinations;
            }
            reset();CircusDroughtInitializeSelection(&c,3,weather,original,init,step);
            assert(originals==0 && inits==1 && steps==5 && weather[0x6CC]==5 && weather[0x6D2]==1);
            assert(!memcmp(&c,&before,sizeof(c)));
        }
        for(unsigned bit=0;bit<32;++bit){CircusDroughtContext x=c;x.callback^=1u<<bit;assert(!CircusDroughtSelectionAllowed(&x,3));}
    }
    CircusDroughtContext c=good(); /* 実fixtureは元1体・現在3体。旧guardが誤って拒否した縮小再現。 */
    assert(!CircusDroughtLaunchAllowed(&c));assert(CircusDroughtSelectionAllowed(&c,3));
    c.script=0x09FF4D77u;c.outcome=1;reset();
    CircusDroughtInitializeSelection(&c,1,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==5); /* 旧WINは元人数とnative完了の規約を維持 */
    c=good();reset();stuck=1;CircusDroughtInitializeSelection(&c,3,weather,original,init,step);
    assert(originals==0 && inits==1 && steps==256 && !weather[0x6D2]);
    printf("selection_guard combinations=%u saved1-selected3-regression original1..6-preserved PASS\n",combinations);
}
