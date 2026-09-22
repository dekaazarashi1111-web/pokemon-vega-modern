#include "pr16_learnset_conditional_game.h"
#include "pr16_learnset_conditional_bindings.h"

static uint8_t conditional(uint16_t species, uint8_t family, struct Pr16RuntimeView *view)
{
    return PR16_READ_CONDITIONAL(PR16_CONDITIONAL_IMAGE, PR16_CONDITIONAL_IMAGE_SIZE,
        species, family, view) == PR16_OWNER_PREPARED_LOOKUP;
}
static void known_moves(const void *mon, uint16_t moves[4])
{
    uint8_t i;
    for (i = 0; i < 4u; ++i)
        moves[i] = (uint16_t)PR16_GET_MON_DATA(mon, 13 + i, (uint8_t *)0);
}
uint16_t Pr16_GameAfterEvolution(void *mon, uint8_t first)
{
    struct Pr16RuntimeView evolution, levels;
    uint16_t species, move;
    uint8_t cursor, level;
    if (!mon || PR16_GET_MON_DATA(mon, 45, (uint8_t *)0)) return 0;
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (!conditional(species, PR16_CONSUMER_EVOLUTION, &evolution) ||
        PR16_READ_VIEW(PR16_IMAGE, PR16_IMAGE_SIZE, species, PR16_CONSUMER_LEVEL_UP,
            &levels) != PR16_OWNER_PREPARED_LOOKUP) return 0;
    level = (uint8_t)PR16_GET_MON_DATA(mon, 56, (uint8_t *)0);
    cursor = *PR16_LEARNING_CURSOR;
    move = Pr16ConditionalEvolutionNext(&evolution, &levels, level, first, &cursor);
    *PR16_LEARNING_CURSOR = cursor;
    if (!move) return 0;
    *PR16_PENDING_MOVE = move;
    /* 既存の満杯/既習得コードと実PP初期化はJP engineのまま。 */
    return PR16_GIVE_MON_MOVE(mon, move);
}
uint8_t Pr16_GameGetEggMoves(void *mon, uint16_t *moves)
{
    struct Pr16RuntimeView view;
    uint16_t species;
    if (!mon || !moves) return 0;
    /* 育て屋の生成途中のeggも呼ぶ読取API。共有/祖先表へfallbackしない。 */
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (!conditional(species, PR16_CONSUMER_EGG, &view)) return 0;
    return Pr16ConditionalList(&view, (const uint16_t *)0, 0, moves, 50u);
}
uint8_t Pr16_GameGetAllEggMoves(void *mon, uint16_t *moves, uint8_t ignore_known)
{
    struct Pr16RuntimeView view;
    uint16_t species, known[4], part[50], result[PR16_CONDITIONAL_CAPACITY];
    uint8_t family, count = 0, n, i, j;
    if (!mon || !moves) return 0;
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    known_moves(mon, known);
    /* 共有はMove Memory/保持候補専用。GetEggMovesや通常levelへ混ぜない。 */
    for (family = 0; family < 2u; ++family) {
        if (!conditional(species, family ? PR16_CONSUMER_SHARED_EGG : PR16_CONSUMER_EGG,
            &view)) return 0;
        n = Pr16ConditionalList(&view, known, ignore_known ? 4u : 0u, part, 50u);
        for (i = 0; i < n; ++i) {
            for (j = 0; j < count && result[j] != part[i]; ++j) {}
            if (j != count) continue;
            if (count >= PR16_CONDITIONAL_CAPACITY) return 0;
            result[count++] = part[i];
        }
    }
    for (i = 0; i < count; ++i) moves[i] = result[i];
    return count;
}
uint8_t Pr16_GameGetConditionalRelearnerMoves(void *mon, uint16_t *moves)
{
    struct Pr16RuntimeView evolution, levels, reminder;
    uint16_t species, known[4];
    uint8_t mode, level;
    if (!mon || !moves || PR16_GET_MON_DATA(mon, 45, (uint8_t *)0)) return 0;
    species = (uint16_t)PR16_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (!conditional(species, PR16_CONSUMER_EVOLUTION, &evolution)) return 0;
    mode = *PR16_MEMORY_MODE;
    if (mode == 1u) return Pr16_GameGetAllEggMoves(mon, moves, 1u);
    /* 既存archiveのmode ABIは維持。新owner表への再binding受入は別工程。 */
    if (mode >= 2u && mode <= 7u) return PR16_PARENT_ARCHIVE_MOVES(mon, moves);
    if (mode != 0u || !conditional(species, PR16_CONSUMER_REMINDER, &reminder) ||
        PR16_READ_VIEW(PR16_IMAGE, PR16_IMAGE_SIZE, species, PR16_CONSUMER_LEVEL_UP,
            &levels) != PR16_OWNER_PREPARED_LOOKUP) return 0;
    known_moves(mon, known);
    level = (uint8_t)PR16_GET_MON_DATA(mon, 56, (uint8_t *)0);
    return Pr16ConditionalReminder(&evolution, &levels, &reminder, level, known,
        moves, PR16_CONDITIONAL_CAPACITY);
}
