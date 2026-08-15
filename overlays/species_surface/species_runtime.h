#ifndef VEGA_SPECIES_RUNTIME_H
#define VEGA_SPECIES_RUNTIME_H

#include <stdint.h>

void VegaSpeciesSurface_GetSpeciesName(uint8_t *destination, uint16_t species);
void VegaSpeciesSurface_GiveBoxMonInitialMovesetAppended(
    void *box_mon, uint16_t species, uint8_t level);
void VegaSpeciesSurface_GiveBoxMonInitialMovesetDispatch(void);

#endif
