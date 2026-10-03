#include "pr16_learnset_progress.h"
/* Generated binding contains fixed JP engine functions and the accepted PLR1
 * span reader. Host tests inject equivalent typed functions, never ROM casts. */
#include "pr16_learnset_progress_bindings.h"

void Pr16_GameGiveBoxMonInitialMoveset(void *box)
{
    struct Pr16RuntimeView view;
    uint16_t species, moves[4];
    uint8_t i, count, level;
    if (!box)
        return;
    /* This is a creation initializer, never a saved-mon migration. Preserve
     * every nonempty moveset, including PP/PP Up/checksum/species side effects. */
    for (i = 0; i < 4u; ++i)
        if (PR16_GET_BOX_DATA(box, 13 + i, (uint8_t *)0))
            return;
    species = (uint16_t)PR16_GET_BOX_DATA(box, 11, (uint8_t *)0);
    if (PR16_READ_VIEW(PR16_IMAGE, PR16_IMAGE_SIZE, species,
                       PR16_CONSUMER_LEVEL_UP, &view) != PR16_OWNER_PREPARED_LOOKUP)
        return;
    level = PR16_GET_BOX_LEVEL(box);
    count = Pr16ProgressInitial(&view, level, moves, 4u);
    for (i = 0; i < count; ++i)
        if (PR16_GIVE_BOX_MOVE(box, moves[i]) == 0xFFFFu)
            break;
}
uint16_t Pr16_GameMonTryLearningNewMove(void *mon, uint8_t firstMove)
{
    struct Pr16RuntimeView view;
    uint16_t species, move;
    uint8_t level, cursor;
    if (!mon || PR16_GET_MON_DATA(mon, 45, (uint8_t *)0))
        return 0; /* Existing eggs are not level-up learners. */
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (PR16_READ_VIEW(PR16_IMAGE, PR16_IMAGE_SIZE, species,
                       PR16_CONSUMER_LEVEL_UP, &view) != PR16_OWNER_PREPARED_LOOKUP)
        return 0;
    level = (uint8_t)PR16_GET_MON_DATA(mon, 56, (uint8_t *)0);
    cursor = *PR16_LEARNING_CURSOR;
    move = Pr16ProgressNext(&view, level, firstMove, &cursor);
    *PR16_LEARNING_CURSOR = cursor;
    if (!move)
        return 0;
    *PR16_PENDING_MOVE = move;
    return PR16_GIVE_MON_MOVE(mon, move);
}
