#define CIRCUS_PIVOT_HOST_TEST
#include "../../tools/mgba_pr16_circus_pivot.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    assert(pv_allowed(2,0,12,12,0,0));
    assert(!pv_allowed(2,1,12,12,0,0));
    assert(!pv_allowed(2,0,0,12,0,0));
    assert(!pv_allowed(2,0,12,0,0,0));
    assert(!pv_allowed(2,0,12,12,0,11));
    assert(!pv_allowed(2,0,12,12,11,0));
    unsigned checks=6U;
    for(unsigned type=0;type<25U;++type)
        for(unsigned streak=0;streak<2U;++streak){
            assert(!pv_allowed(streak,0,type,type,0,0));++checks;
        }
    printf("PASS_CIRCUS_PIVOT_POLICY checks=%u\n",checks);return 0;
}
