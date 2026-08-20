#ifndef POKEMON_VEGA_MOVE_DISTRIBUTION_V4_H
#define POKEMON_VEGA_MOVE_DISTRIBUTION_V4_H

#include <stdint.h>

enum MoveDistributionV4Domain {
    MOVE_DISTRIBUTION_DOMAIN_LEVEL_UP = 0,
    MOVE_DISTRIBUTION_DOMAIN_EGG = 1,
    MOVE_DISTRIBUTION_DOMAIN_TM_TUTOR = 2,
    MOVE_DISTRIBUTION_DOMAIN_WILD = 3
};

uint32_t MoveDistributionV4_Probe(uint32_t selector);
uint16_t MoveDistributionV4_ResolveFormDomain(uint16_t record,
                                               uint8_t domain);
uint8_t MoveDistributionV4_ApplyWildInitialMoves(void *mon);
void MoveDistributionV4_GiveInitialMoves(void *box_mon, uint16_t species,
                                          uint8_t level);
uint8_t MoveDistributionV4_TryGenerateWildMonAdapter(const void *info,
                                                      uint8_t area,
                                                      uint8_t flags);
uint16_t MoveDistributionV4_GenerateFishingEncounterAdapter(const void *info,
                                                             uint8_t rod);
uint8_t MoveDistributionV4_TryHiddenEncounterAdapter(void);
void MoveDistributionV4_GiveBoxMonInitialMovesetDispatch(void);

#endif
