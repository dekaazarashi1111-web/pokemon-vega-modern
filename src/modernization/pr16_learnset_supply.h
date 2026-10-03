#ifndef PR16_LEARNSET_SUPPLY_H
#define PR16_LEARNSET_SUPPLY_H
#include <stdint.h>
#include "pr16_learnset_runtime.h"
#define PR16_SUPPLY_MACHINE 0u
#define PR16_SUPPLY_TUTOR 1u
#define PR16_SUPPLY_MAX_ROWS 160u
#define PR16_SUPPLY_PAGE_SIZE 40u
/* 0=invalid/nonlearning, 1=decoded (including an explicit empty row).
 * Invalid inputs never modify output/count. No ROM/mon/save writes. */
uint8_t Pr16SupplyDecode(const uint8_t *image, uint32_t size, uint16_t owner,
    uint8_t family, uint16_t *moves, uint16_t capacity, uint16_t *count);
uint8_t Pr16SupplyTutorBit(const struct Pr16RuntimeView *view,
    uint16_t owner, uint8_t slot);
uint8_t Pr16SupplyPageCount(uint16_t count);
uint8_t Pr16SupplyPage(const uint16_t *archive, uint16_t count,
    const uint16_t known[4], uint8_t mode, uint8_t hall_of_fame,
    uint16_t *out, uint8_t capacity);
#endif
