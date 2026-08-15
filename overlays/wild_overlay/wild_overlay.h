#ifndef VEGA_WILD_OVERLAY_H
#define VEGA_WILD_OVERLAY_H

#include <stdint.h>

uint16_t VegaWildOverlay_SelectSpecies(uint16_t original_species, uint8_t area);
uint8_t VegaWildOverlay_TryGenerateWildMon(const void *info, uint8_t area,
                                           uint8_t flags);

#endif
