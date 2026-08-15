#ifndef VEGA_WILD_OVERLAY_H
#define VEGA_WILD_OVERLAY_H

#include <stdint.h>

enum VegaEcologyMode {
    VEGA_ECOLOGY_MODE_AUTO = 0,
    VEGA_ECOLOGY_MODE_DAY = 1,
    VEGA_ECOLOGY_MODE_NIGHT = 2,
    VEGA_ECOLOGY_MODE_SWARM = 3,
    VEGA_ECOLOGY_MODE_HIDDEN = 4,
};

uint16_t VegaWildOverlay_SelectSpecies(uint16_t original_species, uint8_t area);
uint8_t VegaWildOverlay_TryGenerateWildMon(const void *info, uint8_t area,
                                           uint8_t flags);
uint16_t VegaWildOverlay_GenerateFishingEncounter(const void *info, uint8_t rod);
void VegaWildOverlay_SetMode(uint8_t mode);
uint8_t VegaWildOverlay_GetMode(void);
uint8_t VegaWildOverlay_TryHiddenEncounter(void);
void VegaWildOverlay_FieldUse(uint8_t task_id);

#endif
