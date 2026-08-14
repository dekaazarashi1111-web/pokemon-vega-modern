#ifndef POKEMON_VEGA_BATTLE_UI_H
#define POKEMON_VEGA_BATTLE_UI_H

#include <stdint.h>

enum VegaBattleUIEffectClass {
    VEGA_BATTLE_UI_EFFECT_NORMAL = 0,
    VEGA_BATTLE_UI_EFFECT_SUPER = 1,
    VEGA_BATTLE_UI_EFFECT_RESISTED = 2,
    VEGA_BATTLE_UI_EFFECT_NONE = 3,
};

uint8_t VegaBattleUI_ClassifyResult(uint8_t move_result);
uint8_t VegaBattleUI_GetSelectedMoveType(void);
void VegaBattleUI_DisplayMoveType(void);
void VegaBattleUI_DisplayMoveEffectiveness(void);
void VegaBattleUI_InitMoveSelection(void);
void VegaBattleUI_HandleInputChooseMove(void);

#endif /* POKEMON_VEGA_BATTLE_UI_H */
