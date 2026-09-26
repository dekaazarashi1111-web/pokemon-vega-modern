#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "../../overlays/circus_streak/circus_streak_return.h"
int main(void)
{
    const uint32_t scripts[] = {0x09FF4D16u,0x09FF4D77u,0x09FF4DD8u,0x092CF669u,0u};
    const uint32_t callbacks[] = {0x08055E75u,0x08055F65u,0u};
    const uint8_t outcomes[] = {0u,1u,2u,3u,0x82u,0xffu};
    unsigned combinations=0;
    for(unsigned armed=0;armed<3;++armed)
    for(unsigned circus=0;circus<3;++circus)
    for(unsigned marker=0;marker<5;++marker)
    for(unsigned snapshot=0;snapshot<3;++snapshot)
    for(unsigned count=0;count<8;++count)
    for(unsigned o=0;o<6;++o)
    for(unsigned s=0;s<5;++s)
    for(unsigned c=0;c<3;++c)
    for(unsigned ready=0;ready<3;++ready)
    for(unsigned weather=0;weather<3;++weather)
    for(unsigned script=0;script<3;++script){
        int expected=armed==1 && circus==1 && marker==2 && snapshot==1 && count>=1 && count<=6
            && (outcomes[o]&0x7f)==2 && s<3 && c==0 && ready==0 && weather==1 && script==1;
        assert(CircusStreakReturnFadeAllowed(armed,circus,marker,snapshot,count,outcomes[o],scripts[s],callbacks[c],ready,weather,script)==expected);
        ++combinations;
    }
    printf("return_fade combinations=%u PASS\n",combinations);
    return 0;
}
