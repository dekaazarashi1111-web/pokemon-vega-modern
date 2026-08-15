#ifndef VEGA_SPECIES_RUNTIME_H
#define VEGA_SPECIES_RUNTIME_H

#include <stdint.h>

void VegaSpeciesSurface_GetSpeciesName(uint8_t *destination, uint16_t species);
uint16_t VegaSpeciesSurface_NationalPokedexNumToSpecies(uint16_t national_dex);
void VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended(
    void *box_mon, uint16_t species, uint8_t level);
void VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch(void);

uint16_t VegaSpeciesSurface_GetIconSpecies(
    uint16_t species, uint32_t personality);
void VegaSpeciesSurface_SafeLoadMonIconPalette(uint16_t species);
void VegaSpeciesSurface_SafeFreeMonIconPalette(uint16_t species);
const uint16_t *VegaSpeciesSurface_GetValidMonIconPalettePtr(uint16_t species);
uint8_t VegaSpeciesSurface_GetValidMonIconPalIndex(uint16_t species);

#endif
