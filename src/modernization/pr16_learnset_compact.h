#ifndef PR16_LEARNSET_COMPACT_H
#define PR16_LEARNSET_COMPACT_H
#include "pr16_learnset_runtime.h"
/* PLC2はPLC1と同じowner/列/順序。共有するのは不変の同一行だけ。 */
uint8_t Pr16ReadCompactConditional(const uint8_t *image, uint32_t size,
    uint16_t species, uint8_t consumer, struct Pr16RuntimeView *out);
#endif
