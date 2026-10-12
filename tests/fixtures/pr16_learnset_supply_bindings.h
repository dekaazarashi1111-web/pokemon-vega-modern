#ifndef PR16_SUPPLY_FIXTURE_BINDINGS_H
#define PR16_SUPPLY_FIXTURE_BINDINGS_H
#include "pr16_learnset_supply.h"
extern const uint8_t *SupplyFixtureImage;
extern uint32_t SupplyFixtureSize;
extern uint8_t SupplyFixtureMode;
uint32_t SupplyFixtureData(const void *, int, uint8_t *);
uint8_t SupplyFixtureConditional(uint16_t, uint8_t, struct Pr16RuntimeView *);
uint8_t SupplyFixtureFlag(uint16_t);
uint8_t SupplyFixtureParent(void *, uint16_t *);
#define PR16_SUPPLY_IMAGE SupplyFixtureImage
#define PR16_SUPPLY_IMAGE_SIZE SupplyFixtureSize
#define PR16_SUPPLY_GET_MON_DATA SupplyFixtureData
#define PR16_SUPPLY_READ_CONDITIONAL SupplyFixtureConditional
#define PR16_SUPPLY_FLAG_GET SupplyFixtureFlag
#define PR16_SUPPLY_MEMORY_MODE (&SupplyFixtureMode)
#define PR16_SUPPLY_PARENT_RELEARNER SupplyFixtureParent
#endif
