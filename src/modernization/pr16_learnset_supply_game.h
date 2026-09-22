#ifndef PR16_LEARNSET_SUPPLY_GAME_H
#define PR16_LEARNSET_SUPPLY_GAME_H
#include "pr16_learnset_supply.h"
/* Table slots only. Special tutor IDs and actual ROM callsites need separate ABI binding. */
uint8_t Pr16_GameSupplyTutorSlot(void *mon, uint8_t slot);
uint16_t Pr16_GameSupplyArchiveRowCount(void *mon, uint8_t family);
uint8_t Pr16_GameSupplyRelearner(void *mon, uint16_t *moves);
#endif
