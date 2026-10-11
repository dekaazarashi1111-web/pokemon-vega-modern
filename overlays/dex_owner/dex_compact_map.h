#ifndef VEGA_DEX_COMPACT_MAP_H
#define VEGA_DEX_COMPACT_MAP_H
#include "dex_adapter.h"
uint16_t VegaDexCompactSpeciesOwner(uint16_t sid);
uint16_t VegaDexCompactOfficialOwner(uint16_t national);
uint16_t VegaDexCompactOwnerRepresentative(uint16_t owner);
extern const uint8_t VegaDexCompactOfficialMask[VEGA_DEX_BITMAP_SIZE];
#endif
