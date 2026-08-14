#ifndef POKEMON_VEGA_MOVE_MEMORY_H
#define POKEMON_VEGA_MOVE_MEMORY_H

#include <stdint.h>

enum VegaMoveMemoryMode {
    VEGA_MOVE_MEMORY_MODE_NORMAL = 0,
    VEGA_MOVE_MEMORY_MODE_EGG = 1,
};

enum VegaMoveMemoryEggPolicy {
    VEGA_MOVE_MEMORY_EGG_LOCKED = 0,
    VEGA_MOVE_MEMORY_EGG_ALLOWED = 1,
    VEGA_MOVE_MEMORY_EGG_NEEDS_HERB = 2,
    VEGA_MOVE_MEMORY_EGG_NEEDS_EMPTY_SLOT = 3,
};

void VegaMoveMemory_FieldUse(uint8_t task_id);
void VegaMoveMemory_CheckContext(void);
void VegaMoveMemory_OpenModeMenu(void);
void VegaMoveMemory_SetNormalMode(void);
void VegaMoveMemory_SetEggMode(void);
void VegaMoveMemory_ResetMode(void);
uint8_t VegaMoveMemory_GetMoveRelearnerMoves(void *mon, uint16_t *moves);
void VegaMoveMemory_CheckEggEntry(void);
void VegaMoveMemory_CheckEggSlot(void);
void VegaMoveMemory_SelectedMonHasEmptySlot(void);
void VegaMoveMemory_SelectedMoveHasPpUps(void);
void VegaMoveMemory_SelectedMoveCanForget(void);
void VegaMoveMemory_DeleteSelectedMove(void);

uint8_t VegaMoveMemory_ContextAllowedFromState(
    uint32_t battle_type_flags, uint8_t facility, uint8_t raid);
uint8_t VegaMoveMemory_EvaluateEggPolicy(
    uint8_t dh_clear, uint8_t hall_of_fame, uint8_t has_mirror_herb,
    uint8_t has_empty_slot);
uint8_t VegaMoveMemory_CanForgetMove(uint16_t move);

extern volatile const uint32_t VegaMoveMemory_ItemScriptPointer;

#endif /* POKEMON_VEGA_MOVE_MEMORY_H */
