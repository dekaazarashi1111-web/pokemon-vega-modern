#ifndef PR16_LEARNSET_CONDITIONAL_GAME_H
#define PR16_LEARNSET_CONDITIONAL_GAME_H
#include "pr16_learnset_conditional.h"
uint16_t Pr16_GameAfterEvolution(void *mon, uint8_t first);
uint8_t Pr16_GameGetEggMoves(void *mon, uint16_t *moves);
uint8_t Pr16_GameGetAllEggMoves(void *mon, uint16_t *moves, uint8_t ignore_known);
uint8_t Pr16_GameGetConditionalRelearnerMoves(void *mon, uint16_t *moves);
#endif
