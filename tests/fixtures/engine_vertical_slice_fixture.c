#include "engine_slice.h"
#include "runtime.h"
#include "save_migration.h"

#include <assert.h>
#include <string.h>

static int Persist(const VegaModernSaveData *data, size_t size, void *context)
{
    VegaModernSaveData *disk = context;
    assert(size == sizeof(*disk));
    memcpy(disk, data, size);
    return 1;
}

int main(void)
{
    VegaModernSaveData save, disk;
    struct VegaSliceGift gift = {0};
    struct VegaSliceMovementResult movement;
    struct VegaSliceTextResult text;
    const uint8_t events[] = {VEGA_SLICE_ENCOUNTER, VEGA_SLICE_HATCH, VEGA_SLICE_POISON,
                              VEGA_SLICE_CONTACT, VEGA_SLICE_COORD, VEGA_SLICE_WARP,
                              VEGA_SLICE_LEDGE};
    const uint8_t tokens[] = {VEGA_TEXT_GLYPH, VEGA_TEXT_VARIABLE, VEGA_TEXT_COLOR,
                              VEGA_TEXT_NEWLINE, VEGA_TEXT_PAGE, VEGA_TEXT_CHOICE,
                              VEGA_TEXT_WAIT, VEGA_TEXT_SOUND};
    struct VegaSliceEncounter original = {25, 0, 0, 12, 0, 0, 0, 20};
    struct VegaSliceEncounter overlay = {445, 669, 1027, 35, 20, 2, 1, 10};
    struct VegaSliceEncounter result;
    const uint16_t candidates[6] = {412, 425, 445, 512, 700, 900};
    const uint8_t selections[3] = {0, 2, 4};
    uint16_t rental[3] = {0};
    uint16_t tm_count = 1;
    uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE];
    uint8_t restored[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE];
    uint8_t party_count = 6;
    CfruCandyTarget target = {10, 1000};
    cfru_u32 experience[102];
    CfruCandyResult candy;
    CfruMirageItemState mirage;
    CfruRaidState raid;
    VegaEncounterRequest request = {0};
    unsigned index;

    for (index = 0; index < 102; ++index) experience[index] = index * 100u;
    memset(party, 0x5A, sizeof(party));
    memset(restored, 0, sizeof(restored));
    VegaSaveInitNew(&save, 1);
    assert(save.text_speed == VEGA_TEXT_INSTANT && save.hatch_mode == VEGA_HATCH_FAST);
    assert(save.exp_share_enabled == 1);
    assert(!VegaSliceDebugGift(&gift)); /* release build has no active debug grant */

    assert(VegaSliceMoveCourse(100, 8, events, sizeof(events), &movement));
    assert(movement.frames == 800 && movement.event_count[VEGA_SLICE_STEP] == 100);
    assert(VegaSliceMoveCourse(100, 5, events, sizeof(events), &movement));
    assert(movement.frames == 500 && movement.event_count[VEGA_SLICE_WARP] == 1);
    assert(VegaSliceRenderText(tokens, sizeof(tokens), true, &text));
    assert(text.glyph_count == 1 && text.delayed_glyph_count == 0);
    assert(text.token_count[VEGA_TEXT_WAIT] == 1 && text.token_count[VEGA_TEXT_SOUND] == 1);
    assert(VegaSliceResolveQuantity(3, 2) == 3 && VegaSliceResolveQuantity(99, 3) == 99);

    result = VegaSliceSelectOverlay(original, overlay, false, true, false);
    assert(memcmp(&result, &original, sizeof(result)) == 0);
    result = VegaSliceSelectOverlay(original, overlay, true, false, false);
    assert(memcmp(&result, &original, sizeof(result)) == 0);
    result = VegaSliceSelectOverlay(original, overlay, true, true, true);
    assert(memcmp(&result, &original, sizeof(result)) == 0);
    result = VegaSliceSelectOverlay(original, overlay, true, true, false);
    assert(result.species == 445 && result.held_item == 669);
    result = VegaSliceApplyResearch(original, VEGA_SLICE_NORMAL, 9, 20, 2, 1027, 669, 1);
    assert(memcmp(&result, &original, sizeof(original)) == 0);
    result = VegaSliceApplyResearch(original, VEGA_SLICE_RESEARCH, 9, 20, 2, 1027, 669, 1);
    assert(result.level == 21 && result.iv_floor == 20 && result.egg_move == 1027);
    assert(VegaSaveSetEncounterProfile(&save, VEGA_REGION_TOHOKU, VEGA_PROFILE_RESEARCH) == VEGA_SAVE_OK);

    assert(VegaSliceUseTm(&tm_count, false) && tm_count == 0);
    tm_count = 1;
    assert(VegaSliceUseTm(&tm_count, true) && tm_count == 1);

    candy = cfru_apply_exp_candy(&target, 800, 100, experience, 102);
    assert(candy.status == CFRU_CANDY_APPLIED && candy.consumed && target.level >= 11);
    assert(VegaSliceSelectRentals(candidates, selections, rental));
    assert(rental[0] == 412 && rental[1] == 445 && rental[2] == 700);
    assert(VegaSliceExchangeRental(rental, 1, 426) && rental[1] == 426);
    memset(&disk, 0, sizeof(disk));
    assert(VegaFactoryEnter(&save, party, 6, Persist, &disk) == VEGA_SAVE_OK);
    assert(VegaFactorySetBattleActive(&save, Persist, &disk) == VEGA_SAVE_OK);
    save.factory.current_streak[0] = 3;
    VegaSaveFinalize(&save);
    assert(VegaFactoryRestore(&save, restored, &party_count, Persist, &disk) == VEGA_SAVE_OK);
    assert(party_count == 6 && memcmp(restored, party, sizeof(party)) == 0);
    assert(VegaFactoryClaimReward(&save, 0, 9, Persist, &disk) == VEGA_SAVE_OK);
    assert(save.factory.battle_points == 9);

    save.encounter_credits[0] = 1;
    request.credit_kind = 0; request.cost = 1; request.pool = 7;
    request.species = 445; request.level = 35; request.ability = 129;
    request.ivs[0] = request.ivs[1] = request.ivs[2] = 20;
    request.ivs[3] = request.ivs[4] = request.ivs[5] = 20;
    assert(VegaSavePurchaseEncounter(&save, &request, Persist, &disk) == VEGA_SAVE_OK);
    assert(save.pending_encounter.valid && save.encounter_credits[0] == 0);
    VegaSaveFinalize(&save); disk = save;
    assert(VegaSaveLoad(&disk, sizeof(disk)) == VEGA_SAVE_OK && disk.pending_encounter.valid);
    assert(VegaSaveCompleteCapture(&disk, 0, Persist, &save) == VEGA_SAVE_OK);
    assert(!disk.pending_encounter.valid && VegaSaveIsSpecialCaptured(&disk, 0));

    assert(cfru_mirage_item_begin(&mirage, 10, 669));
    assert(cfru_mirage_item_set_battle_value(&mirage, 700));
    assert(cfru_mirage_item_finish(&mirage, CFRU_EXIT_WON, &tm_count));
    assert(tm_count == 10); /* virtual item mutation never persists */

    assert(cfru_raid_begin(&raid, CFRU_SIDE_OPPONENT, 0, 0x07, 4, 1000, 1000, 10, 1));
    while (cfru_raid_shields_remaining(&raid) != 0) assert(cfru_raid_break_shield(&raid));
    assert(cfru_raid_set_boss_hp(&raid, 0));
    assert(cfru_raid_try_capture(&raid));
    assert(raid.end_reason == CFRU_RAID_END_CAPTURED && raid.captured);
    cfru_raid_cleanup(&raid);
    assert(!raid.active && raid.partner_mask == 0);

    VegaSaveFinalize(&disk);
    save = disk;
    assert(VegaSaveLoad(&save, sizeof(save)) == VEGA_SAVE_OK);
    assert(save.encounter_profile[VEGA_REGION_TOHOKU] == VEGA_PROFILE_RESEARCH);
    return 0;
}
