#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "overlays/circus_streak/circus_streak_loss.h"
int main(void)
{
    unsigned cases = 0;
    const uint32_t scripts[] = {0x09FF4D16u,0x09FF4D77u,0x09FF4DD8u,
        0x092CF669u,0x092CF6A5u,0x092CF6E1u,0u,0x09FF4D17u};
    for (unsigned armed=0;armed<3;++armed)
    for (unsigned valid=0;valid<3;++valid)
    for (unsigned marker=0;marker<5;++marker)
    for (unsigned snapshot=0;snapshot<3;++snapshot)
    for (unsigned count=0;count<8;++count)
    for (unsigned outcome=0;outcome<256;++outcome)
    for (unsigned script=0;script<8;++script) {
        int expected=armed==1 && valid==1 && marker==VEGA_FACTORY_BATTLE_ACTIVE && snapshot==1
            && count>0 && count<7 && (outcome==2 || outcome==130) && script<3;
        assert(CircusStreakLossAllowed(armed,valid,marker,snapshot,count,outcome,scripts[script])==expected);
        ++cases;
    }
    printf("PASS_CIRCUS_LOSS_GUARD combinations=%u native_processes=0\n",cases);
    return 0;
}
