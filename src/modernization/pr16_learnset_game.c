#include "pr16_learnset_runtime.h"
#include "pr16_learnset_runtime_generated.h"

extern const uint8_t Pr16LearnsetImage[];
/* ABI from fixed CFRU-JP item.c/learn_move.c. No Pokemon layout casts. */
typedef uint32_t (*GetMonDataFn)(const void *, int, uint8_t *);
#define GET_MON_DATA ((GetMonDataFn)0x0803F355u)

uint8_t Pr16_GameGetLevelUpMovesBySpecies(uint16_t species, uint16_t *moves)
{
    return Pr16RuntimeLevelMoves(Pr16LearnsetImage, PR16_IMAGE_SIZE, species, moves, 40u);
}
uint32_t Pr16_GameCanMonLearnTMHM(const void *mon, uint8_t slot)
{
    uint16_t species;
    if (!mon || slot >= 128u)
        return 0;
    /* SPECIES2 preserves the game's egg check; the owner gate rejects that identity. */
    species = (uint16_t)GET_MON_DATA(mon, 65, (uint8_t *)0);
    return Pr16RuntimeMachineAllowed(Pr16LearnsetImage, PR16_IMAGE_SIZE, species, slot);
}
