#include "pr16_learnset_supply_game.h"
#include "pr16_learnset_supply_bindings.h"

/* 実ROMのID 152..160は通常slotではない。旧特殊条件は絞込みだけに使う。 */
uint8_t Pr16_GameCanLearnTutor(void *mon, uint8_t tutor_id)
{
    struct Pr16RuntimeView view;
    uint16_t species, move, archive[160], count = 0, i;
    uint8_t allowed = 0;
    if (tutor_id < 64u)
        return Pr16_GameSupplyTutorSlot(mon, tutor_id);
    if (tutor_id < 152u || tutor_id > 160u || !mon ||
        PR16_SUPPLY_GET_MON_DATA(mon, 45, (uint8_t *)0))
        return 0;
    species = (uint16_t)PR16_SUPPLY_GET_MON_DATA(mon, 11, (uint8_t *)0);
    if (PR16_SUPPLY_READ_CONDITIONAL(species, PR16_CONSUMER_TUTOR, &view)
            != PR16_OWNER_PREPARED_LOOKUP || view.owner != species)
        return 0;
    move = PR16_SUPPLY_GET_TUTOR_MOVE(tutor_id);
    if (move == 0u || move > 1062u)
        return 0;
    for (i = 0; i < 64u; ++i)
        if (Pr16SupplyTutorBit(&view, species, (uint8_t)i) &&
            PR16_SUPPLY_GET_TUTOR_MOVE((uint8_t)i) == move)
            allowed = 1u;
    if (!Pr16SupplyDecode(PR16_SUPPLY_IMAGE, PR16_SUPPLY_IMAGE_SIZE,
            species, PR16_SUPPLY_TUTOR, archive, 160u, &count))
        return 0;
    for (i = 0; i < count; ++i)
        if (archive[i] == move)
            allowed = 1u;
    /* 追加archiveの殿堂入りgateを通常Tutor NPCへ持ち込まない。 */
    return allowed ? (PR16_SUPPLY_SPECIAL_TUTOR(mon, tutor_id) != 0u) : 0u;
}

static void *selected_mon(void)
{
    uint16_t slot = *PR16_SUPPLY_PARTY_SELECTION;
    return slot < 6u ? (void *)(PR16_SUPPLY_PARTY + (uint32_t)slot * 100u) : (void *)0;
}

/* 既存Prepare/Open/Commitが呼ぶ単一helperを置換し、UIと取消処理を保つ。 */
uint16_t Pr16_GameSupplySelectedRowCount(void)
{
    return Pr16_GameSupplyArchiveRowCount(selected_mon(), PR16_SUPPLY_MACHINE);
}

void Pr16_GameSupplySelectedPageHasMoves(void)
{
    uint16_t moves[40];
    uint8_t mode = *PR16_SUPPLY_MEMORY_MODE;
    uint8_t count = 0;
    if (mode >= 3u && mode <= 6u)
        count = Pr16_GameSupplyRelearner(selected_mon(), moves);
    *PR16_SUPPLY_RESULT = count != 0u ? 1u : 0u;
}
