#ifndef VEGA_CIRCUS_RELIABILITY_H
#define VEGA_CIRCUS_RELIABILITY_H
#include <stdint.h>
/* 期待値差10%以内では命中率を優先。無効技・PP切れ・paid無進展を復活させない。
 * scoreは読取専用の既存評価値。勝敗、乱数、能力、ownerには介入しない。 */
static unsigned rl_pick(unsigned selected, unsigned blocked,
    const uint64_t score[4], const unsigned accuracy[4])
{
    if (selected >= 4U || !score[selected]) return selected;
    unsigned best=selected;
    uint64_t floor=score[selected]-score[selected]/10U;
    for (unsigned i=0;i<4U;++i) {
        if ((blocked&(1U<<i)) || !score[i] || score[i]<floor || !accuracy[i] || accuracy[i]>100U) continue;
        if (accuracy[i]>accuracy[best] || (accuracy[i]==accuracy[best] && score[i]>score[best])) best=i;
    }
    return best;
}
#endif
