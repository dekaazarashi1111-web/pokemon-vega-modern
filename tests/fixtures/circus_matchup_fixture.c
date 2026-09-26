#define CIRCUS_MATCHUP_HOST_TEST
#include "../../tools/mgba_pr16_circus_matchup.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
    unsigned checks=0U;
    for(unsigned streak=0;streak<2U;++streak)
        for(unsigned type=0;type<=24U;++type){assert(!mt_role(streak,type,10U,0x80,0x80,1,171));++checks;}
    assert(mt_role(2,12,10,0,0,163,163)==10);++checks;
    assert(mt_role(2,10,11,0,0,116,116)==12);++checks;
    assert(mt_role(2,0,0,0x180,0x180,108,171)==12);++checks;
    assert(!mt_role(2,0,0,0x80,0,108,171));++checks;
    assert(!mt_role(2,0,0,0,0x80,108,171));++checks;
    assert(!mt_role(2,0,0,0x80,0x80,138,171));++checks;
    assert(!mt_role(2,12,11,0,0,163,163));++checks;
    assert(!mt_role(2,10,10,0,0,116,116));++checks;
    for(unsigned n=0;n<4U;++n){assert(mt_toxic(1,n,16,0,0,0));++checks;}
    assert(!mt_toxic(1,4,16,0,0,0));++checks;
    assert(!mt_toxic(1,0,0,0,0,0));++checks;
    assert(!mt_toxic(0,0,16,0,0,0));++checks;
    assert(!mt_toxic(1,0,16,0x80,0,0));++checks;
    for(unsigned t=0;t<=24U;++t){assert(mt_toxic(1,0,16,0,t,t)==(t!=3 && t!=8));++checks;}
    struct mt_feedback m={0};
    assert(mt_spent(&m,1,2,16)==0);++checks;
    assert(mt_spent(&m,1,2,16)==0);++checks; /* 混乱で未実行 */
    assert(mt_spent(&m,1,2,15)==1);++checks; /* 実際に1回 */
    assert(mt_spent(&m,1,2,15)==1);++checks;
    assert(mt_spent(&m,1,2,13)==2);++checks; /* Pressure等のPP2消費は1回 */
    assert(mt_spent(&m,1,3,13)==0);++checks;
    assert(mt_spent(&m,5,3,10)==0);++checks;
    assert(mt_spent(&m,5,3,9)==1);++checks;
    assert(mt_spent(&m,5,3,16)==0);++checks; /* 回復された別区間 */
    printf("PASS_CIRCUS_MATCHUP_POLICY checks=%u\n",checks);return 0;
}
