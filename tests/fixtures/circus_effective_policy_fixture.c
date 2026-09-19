#define CIRCUS_EFFECTIVE_HOST_TEST
#include "../../tools/mgba_pr16_circus_effective.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    /* run35418010512 frame50972: Normal/Normal、HP34/171、Shadow Ball無効。
     * HPの閾値を入力に持たず、低HPでもToxicへ切り替える。 */
    assert(ef_choose(0,1,1,0,0,0,0)==1);
    assert(ef_choose(0,1,1,1,0,0,0)==1);
    assert(ef_choose(0,1,1,2,0,0,0)==0);
    assert(ef_choose(0,1,4,0,0,0,0)==0);
    assert(ef_choose(0,0,1,0,0,0,0)==0);
    assert(ef_choose(3,0,1,0,0x80,0,0)==3);
    assert(ef_choose(0,1,1,0,0x80,0,0)==0);
    assert(ef_choose(0,1,1,0,0x10,0,0)==0);
    assert(ef_choose(0,1,1,0,0,3,0)==0);
    assert(ef_choose(0,1,1,0,0,0,3)==0);
    assert(ef_choose(0,1,1,0,0,8,0)==0);
    assert(ef_choose(0,1,1,0,0,0,8)==0);
    unsigned checks=12U;
    for(unsigned selected=0;selected<4U;++selected)
        for(unsigned type=0;type<=24U;++type){
            assert(ef_choose(selected,0,1,0,0,type,type)==selected);++checks;
        }
    printf("PASS_CIRCUS_EFFECTIVE_POLICY checks=%u\n",checks);return 0;
}
