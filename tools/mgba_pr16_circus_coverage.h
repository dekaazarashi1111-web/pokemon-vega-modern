#ifndef VEGA_CIRCUS_COVERAGE_H
#define VEGA_CIRCUS_COVERAGE_H
/* 初回3戦の既受入順位はそのまま。再入場では補助技の一律2倍加点を外す。
 * party生成/能力/選択結果へのhost書込みはせず、通常chooser入力で選ぶ。 */
static unsigned cv_utility(unsigned streak,unsigned utility)
{
    return streak<3U?utility:0U;
}
#endif
