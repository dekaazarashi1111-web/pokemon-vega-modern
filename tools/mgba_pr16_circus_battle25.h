#ifndef VEGA_CIRCUS_BATTLE25_POLICY_H
#define VEGA_CIRCUS_BATTLE25_POLICY_H
#include <stdint.h>
/* 25戦目以降だけ、全攻撃技が同じタイプに無効となる個体を減点する。
 * 技/PPから得たmaskと既存相性表の純粋計算。種族・乱数・勝敗・RAMを操作しない。
 * 未知の追加タイプは既存wx_effectと同じ中立扱い。24勝prefixの順位は不変。 */
static unsigned wx_effect(unsigned attack, unsigned defense);
static uint64_t b25_rank(unsigned streak, uint64_t score, uint32_t mask)
{
    if (streak < 24U) return score;
    if (!mask || (mask & ~0x01ffffffU)) return 0U;
    for (unsigned defense = 0U; defense < 19U; ++defense) {
        unsigned can_hit = 0U;
        for (unsigned attack = 0U; attack < 25U; ++attack)
            if ((mask & (1U << attack)) && wx_effect(attack, defense)) can_hit = 1U;
        if (!can_hit) score /= 4U;
    }
    return score;
}
/* 旧順位の読取専用対照。最初に変える通常chooser入力を記録するために使う。 */
static void b25_legacy_plan(const uint64_t scores[6], const uint32_t types[6], unsigned plan[3])
{
    unsigned used = 0U;
    uint32_t covered = 0U;
    for (unsigned n = 0U; n < 3U; ++n) {
        unsigned best = 6U;
        uint64_t top = 0U;
        for (unsigned i = 0U; i < 6U; ++i) {
            uint64_t score = scores[i];
            if (!(types[i] & ~covered)) score /= 4U;
            if (!(used & (1U << i)) && (best == 6U || score > top)) { best = i; top = score; }
        }
        plan[n] = best;
        used |= 1U << best;
        covered |= types[best];
    }
}
#endif
