#ifndef PR16_LEARNSET_CONDITIONAL_H
#define PR16_LEARNSET_CONDITIONAL_H
#include "pr16_learnset_runtime.h"

/* PLC1は条件別の候補表。条件成立や技の自動付与を意味しない。 */
#define PR16_CONDITIONAL_CAPACITY 40u
uint8_t Pr16ReadLearnsetConditional(const uint8_t *image, uint32_t size,
    uint16_t species, uint8_t consumer, struct Pr16RuntimeView *out);
/* 容量不足・不正入力時は出力を変更しない。既存4技を編集するAPIではない。 */
uint8_t Pr16ConditionalList(const struct Pr16RuntimeView *view,
    const uint16_t *known, uint8_t known_count, uint16_t *moves, uint16_t capacity);
uint16_t Pr16ConditionalEvolutionNext(const struct Pr16RuntimeView *evolution,
    const struct Pr16RuntimeView *levels, uint8_t level, uint8_t first,
    uint8_t *cursor);
uint8_t Pr16ConditionalReminder(const struct Pr16RuntimeView *evolution,
    const struct Pr16RuntimeView *levels, const struct Pr16RuntimeView *reminder,
    uint8_t level, const uint16_t known[4], uint16_t *moves, uint16_t capacity);
uint8_t Pr16ConditionalTutorAllowed(const uint8_t *image, uint32_t size,
    uint16_t species, uint16_t slot);
#endif
