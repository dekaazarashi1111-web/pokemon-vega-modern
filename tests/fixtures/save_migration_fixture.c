#include "save_migration.h"
#include "acquisition_save_migration.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(expr)                                                                                 \
    do {                                                                                            \
        if (!(expr)) {                                                                              \
            fprintf(stderr, "CHECK failed at %s:%d: %s\n", __FILE__, __LINE__, #expr);            \
            return 1;                                                                               \
        }                                                                                           \
    } while (0)

typedef struct FlashFixture {
    VegaModernSaveData active;
    VegaModernSaveData staging;
    int fail_next;
    int partial_write_on_failure;
    unsigned commits;
} FlashFixture;

static int Persist(const VegaModernSaveData *data, size_t size, void *context)
{
    FlashFixture *flash = context;
    CHECK(size == sizeof(*data));
    if (flash->fail_next) {
        flash->fail_next = 0;
        if (flash->partial_write_on_failure)
            memcpy(&flash->staging, data, size / 2u);
        return 0;
    }
    memcpy(&flash->staging, data, size);
    memcpy(&flash->active, &flash->staging, size);
    flash->commits++;
    return 1;
}

static VegaWarpAnchor Anchor(uint8_t group, uint8_t map, uint8_t warp)
{
    VegaWarpAnchor anchor = {group, map, warp, 1, 10, 12};
    return anchor;
}

static int RunSaveSuite(void)
{
    VegaModernSaveData save;
    VegaModernSaveData loaded;
    VegaModernSaveData corrupt;
    VegaModernSaveData legacy_v1;
    VegaModernSaveData migrated_once;
    VegaLegacySignals legacy = {.recognized_vega_signature = 1,
                                .legacy_checksum_valid = 1,
                                .shiou_complete_flag_0824 = 1,
                                .dh_complete_flag_114b = 1,
                                .hall_of_fame = 0,
                                .first_badge_owned = 1};
    VegaLegacySignals invalid = {.recognized_vega_signature = 1,
                                 .legacy_checksum_valid = 0,
                                 .shiou_complete_flag_0824 = 1,
                                 .dh_complete_flag_114b = 1,
                                 .hall_of_fame = 0,
                                 .first_badge_owned = 1};
    VegaWarpAnchor tohoku = Anchor(3, 4, 1);
    VegaWarpAnchor kanto = Anchor(40, 2, 0);
    VegaWarpAnchor resolved;
    uint8_t badge_bytes[8] = {0xA5, 0x5A, 1, 2, 3, 4, 5, 6};
    uint8_t badge_before[8];
    uint8_t egg[VEGA_BOX_MON_SIZE];
    uint8_t out[VEGA_BOX_MON_SIZE];
    uint8_t mon[VEGA_PARTY_MON_SIZE];
    uint8_t boxed[VEGA_BOX_MON_SIZE];
    uint8_t evolved[VEGA_BOX_MON_SIZE];
    uint16_t arcade_coin = VEGA_ARCADE_COIN_CAP;
    FlashFixture flash;
    unsigned i;

    memset(&flash, 0, sizeof(flash));
    VegaSaveInitNew(&save, 0);
    CHECK(VegaSaveValidate(&save, sizeof(save)) == VEGA_SAVE_OK);
    CHECK(!VegaAcqSaveValidate(
        (const VegaAcqSaveBlock *)(const void *)save.acquisition_save_block));
    CHECK(save.text_speed == VEGA_TEXT_INSTANT);
    CHECK(save.hatch_mode == VEGA_HATCH_FAST);
    CHECK(save.exp_share_enabled == 0);
    CHECK(save.current_region == VEGA_REGION_TOHOKU);
    CHECK(save.encounter_profile[0] == VEGA_PROFILE_NORMAL);
    CHECK(save.encounter_profile[1] == VEGA_PROFILE_NORMAL);
    CHECK(save.version == VEGA_SAVE_VERSION);
    CHECK(save.research_economy.owner_schema_version == 1u);
    CHECK(save.research_economy.owner_struct_size == sizeof(save.research_economy));
    CHECK(save.research_economy.economy_rank == 1u);
    CHECK(save.research_economy.next_transaction_id == 1u);

    /* Stage 39 v1 uses all 193 tail bytes as zero-reserved storage. */
    memcpy(&legacy_v1, &save, sizeof(legacy_v1));
    legacy_v1.version = VEGA_SAVE_LEGACY_VERSION;
    legacy_v1.generation = 0x13579BDFu;
    legacy_v1.kanto_certifications = 0x5Au;
    memset(&legacy_v1.research_economy, 0, sizeof(legacy_v1.research_economy));
    memset(legacy_v1.reserved, 0, sizeof(legacy_v1.reserved));
    legacy_v1.checksum = 0u;
    legacy_v1.checksum = VegaSaveChecksum(&legacy_v1);
    CHECK(VegaSaveValidate(&legacy_v1, sizeof(legacy_v1)) == VEGA_SAVE_OK);
    memcpy(&loaded, &legacy_v1, sizeof(loaded));
    CHECK(VegaSaveMigrateV1(&loaded, sizeof(loaded)) == VEGA_SAVE_OK);
    CHECK(loaded.version == VEGA_SAVE_VERSION);
    CHECK(loaded.generation == 0x13579BDFu);
    CHECK(loaded.kanto_certifications == 0x5Au);
    CHECK(loaded.research_economy.owner_schema_version == 1u);
    CHECK(loaded.research_economy.owner_struct_size == sizeof(loaded.research_economy));
    CHECK(loaded.research_economy.economy_rank == 1u);
    CHECK(loaded.research_economy.next_transaction_id == 1u);
    CHECK(VegaSaveValidate(&loaded, sizeof(loaded)) == VEGA_SAVE_OK);
    memcpy(&migrated_once, &loaded, sizeof(migrated_once));
    CHECK(VegaSaveMigrateV1(&loaded, sizeof(loaded)) == VEGA_SAVE_OK);
    CHECK(memcmp(&loaded, &migrated_once, sizeof(loaded)) == 0);

    memcpy(&corrupt, &legacy_v1, sizeof(corrupt));
    corrupt.research_economy.owner_reserved[0] = 1u;
    corrupt.checksum = 0u;
    corrupt.checksum = VegaSaveChecksum(&corrupt);
    CHECK(VegaSaveMigrateV1(&corrupt, sizeof(corrupt)) == VEGA_SAVE_RESERVED_NONZERO);
    CHECK(corrupt.version == VEGA_SAVE_LEGACY_VERSION);

    VegaAcqSaveInitialize(
        (VegaAcqSaveBlock *)(void *)save.acquisition_save_block);
    CHECK(VegaAcqSaveValidate(
        (const VegaAcqSaveBlock *)(const void *)save.acquisition_save_block));
    VegaSaveFinalize(&save);
    CHECK(VegaSaveValidate(&save, sizeof(save)) == VEGA_SAVE_OK);
    save.acquisition_save_block[32] ^= 1u;
    VegaSaveFinalize(&save);
    CHECK(VegaSaveValidate(&save, sizeof(save)) == VEGA_SAVE_RESERVED_NONZERO);
    VegaAcqSaveFinalize(
        (VegaAcqSaveBlock *)(void *)save.acquisition_save_block);
    VegaSaveFinalize(&save);
    CHECK(VegaSaveValidate(&save, sizeof(save)) == VEGA_SAVE_OK);
    legacy.item_obtained_flags[103] = 0x40u;

    memcpy(badge_before, badge_bytes, sizeof(badge_bytes));
    CHECK(VegaSaveMigrateLegacy(&save, &invalid) == VEGA_SAVE_BAD_CHECKSUM);
    CHECK(memcmp(badge_bytes, badge_before, sizeof(badge_bytes)) == 0);
    CHECK(arcade_coin == VEGA_ARCADE_COIN_CAP);
    CHECK(VegaSaveMigrateLegacy(&save, &legacy) == VEGA_SAVE_OK);
    CHECK(save.kanto_travel_unlocked == 1);
    CHECK(save.vega_hall_of_fame == 0);
    CHECK(save.exp_share_enabled == 1);
    CHECK(save.legacy_migration_done == 1);
    CHECK(save.item_obtained_flags[103] == 0x40u);
    CHECK(memcmp(badge_bytes, badge_before, sizeof(badge_bytes)) == 0);

    CHECK(VegaSaveSetRegion(&save, VEGA_REGION_KANTO) == VEGA_SAVE_OK);
    CHECK(save.kanto_visited == 1);
    save.kanto_certifications = 0x0Fu;
    save.heal_anchor[VEGA_REGION_KANTO] = Anchor(41, 7, 2);
    save.return_anchor[VEGA_REGION_KANTO] = Anchor(41, 8, 3);
    resolved = VegaSaveResolveAnchor(&save, VEGA_REGION_KANTO, 0, tohoku, kanto);
    CHECK(resolved.map_group == 41 && resolved.map_num == 7);
    save.heal_anchor[VEGA_REGION_KANTO].valid = 0;
    resolved = VegaSaveResolveAnchor(&save, VEGA_REGION_KANTO, 0, tohoku, kanto);
    CHECK(memcmp(&resolved, &kanto, sizeof(resolved)) == 0);
    CHECK(VegaSaveSetEncounterProfile(&save, VEGA_REGION_KANTO, VEGA_PROFILE_RESEARCH)
          == VEGA_SAVE_OK);

    CHECK(VegaSaveAdvanceLeague(&save, VEGA_LEAGUE_STAGE_II) == VEGA_SAVE_NOT_ALLOWED);
    CHECK(VegaSaveAdvanceLeague(&save, VEGA_LEAGUE_STAGE_I) == VEGA_SAVE_OK);
    CHECK(VegaSaveAdvanceLeague(&save, VEGA_LEAGUE_STAGE_II) == VEGA_SAVE_OK);
    CHECK(save.league_i_cleared && save.league_ii_cleared);

    CHECK(VegaSaveMarkSpecialCaptured(&save, 124) == VEGA_SAVE_OK);
    CHECK(VegaSaveIsSpecialCaptured(&save, 124));
    CHECK(VegaSaveMarkSpecialCaptured(&save, 125) == VEGA_SAVE_RANGE_ERROR);
    memcpy(&flash.active, &save, sizeof(save));
    flash.fail_next = 1;
    CHECK(VegaRaidClaimReward(&save, 3, Persist, &flash) == VEGA_SAVE_PERSIST_FAILED);
    CHECK(VegaRaidClaimReward(&save, 3, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(VegaRaidClaimReward(&save, 3, Persist, &flash) == VEGA_SAVE_ALREADY_CLAIMED);
    CHECK(VegaRaidSetRetry(&save, 3, 1, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(VegaRaidSetBonusTier(&save, 3, 2, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(VegaRaidSetBonusTier(&save, 3, 1, Persist, &flash) == VEGA_SAVE_NOT_ALLOWED);

    memset(mon, 0xCC, sizeof(mon));
    mon[0x0F] = 17;
    mon[0x10] = 0x3Fu;
    mon[0x11] = 23;
    memcpy(boxed, mon, sizeof(boxed));
    memcpy(evolved, boxed, sizeof(evolved));
    evolved[32] ^= 0x01u; /* species change must not touch the persistent QOL bytes */
    CHECK(evolved[0x0F] == 17 && evolved[0x10] == 0x3F && evolved[0x11] == 23);
    memcpy(egg, boxed, VEGA_BOX_MON_SIZE);
    CHECK(egg[0x0F] == 17 && egg[0x10] == 0x3F && egg[0x11] == 23);
    for (i = 0; i < VEGA_EGG_QUEUE_CAPACITY; ++i) {
        egg[0] = (uint8_t)i;
        CHECK(VegaEggQueuePush(&save, egg) == VEGA_SAVE_OK);
    }
    CHECK(VegaEggQueuePush(&save, egg) == VEGA_SAVE_QUEUE_FULL);
    for (i = 0; i < VEGA_EGG_QUEUE_CAPACITY; ++i) {
        CHECK(VegaEggQueuePop(&save, out) == VEGA_SAVE_OK);
        CHECK(out[0] == i);
        CHECK(out[0x0F] == 17 && out[0x10] == 0x3F && out[0x11] == 23);
    }
    CHECK(VegaEggQueuePop(&save, out) == VEGA_SAVE_QUEUE_EMPTY);

    save.item_obtained_flags[VEGA_ITEM_OBTAINED_BYTES - 1] |= (1u << 6);
    VegaSaveFinalize(&save);
    memcpy(&loaded, &save, sizeof(save));
    CHECK(VegaSaveValidate(&loaded, sizeof(loaded)) == VEGA_SAVE_OK);
    CHECK(loaded.kanto_travel_unlocked && loaded.kanto_visited);
    CHECK(loaded.kanto_certifications == 0x0F);
    CHECK(loaded.encounter_profile[VEGA_REGION_KANTO] == VEGA_PROFILE_RESEARCH);
    resolved = VegaSaveResolveAnchor(&loaded, VEGA_REGION_KANTO, 1, tohoku, kanto);
    CHECK(resolved.map_group == 41 && resolved.map_num == 8);
    CHECK(loaded.item_obtained_flags[VEGA_ITEM_OBTAINED_BYTES - 1] & (1u << 6));
    CHECK(loaded.raid_reward_claimed[0] & (1u << 3));
    CHECK(loaded.raid_retry_pending[0] & (1u << 3));
    CHECK(loaded.raid_bonus_tier[3] == 2);
    CHECK(memcmp(badge_bytes, badge_before, sizeof(badge_bytes)) == 0);

    memcpy(&corrupt, &save, sizeof(corrupt));
    ((uint8_t *)&corrupt)[700] ^= 0x40u;
    CHECK(VegaSaveValidate(&corrupt, sizeof(corrupt)) == VEGA_SAVE_BAD_CHECKSUM);
    memcpy(&corrupt, &save, sizeof(corrupt));
    corrupt.version = 99;
    corrupt.checksum = VegaSaveChecksum(&corrupt);
    CHECK(VegaSaveValidate(&corrupt, sizeof(corrupt)) == VEGA_SAVE_UNSUPPORTED_VERSION);
    memcpy(&corrupt, &save, sizeof(corrupt));
    corrupt.encounter_profile[VEGA_REGION_KANTO] = 0xFFu;
    corrupt.checksum = VegaSaveChecksum(&corrupt);
    CHECK(VegaSaveLoad(&corrupt, sizeof(corrupt)) == VEGA_SAVE_OK);
    CHECK(corrupt.encounter_profile[VEGA_REGION_KANTO] == VEGA_PROFILE_NORMAL);
    memcpy(&corrupt, &save, sizeof(corrupt));
    corrupt.reserved[0] = 1;
    corrupt.checksum = VegaSaveChecksum(&corrupt);
    CHECK(VegaSaveValidate(&corrupt, sizeof(corrupt)) == VEGA_SAVE_RESERVED_NONZERO);
    memset(&corrupt, 0xFF, sizeof(corrupt));
    CHECK(VegaSaveValidate(&corrupt, sizeof(corrupt)) == VEGA_SAVE_EMPTY_OR_LEGACY);

    puts("save-suite: PASS");
    return 0;
}

static void FillParty(uint8_t party[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE])
{
    size_t mon;
    size_t byte;
    for (mon = 0; mon < VEGA_PARTY_CAPACITY; ++mon)
        for (byte = 0; byte < VEGA_PARTY_MON_SIZE; ++byte)
            party[mon][byte] = (uint8_t)(mon * 31u + byte);
}

static VegaEncounterRequest EncounterRequest(void)
{
    VegaEncounterRequest request;
    unsigned i;
    memset(&request, 0, sizeof(request));
    request.encounter_kind = 2;
    request.credit_kind = 3;
    request.cost = 7;
    request.pool = 22;
    request.species = 1024;
    request.form = 4;
    request.level = 73;
    request.nature = 11;
    request.ability = 2;
    request.shiny = 1;
    request.tera_type = 23;
    request.personality = 0x1234ABCDu;
    request.generator_version = 5;
    for (i = 0; i < 6; ++i)
        request.ivs[i] = (uint8_t)(26u + i);
    for (i = 0; i < sizeof(request.generator_fingerprint); ++i)
        request.generator_fingerprint[i] = (uint8_t)(0xA0u + i);
    return request;
}

static int RunFacilitySuite(void)
{
    VegaModernSaveData save;
    VegaModernSaveData reset;
    VegaModernSaveData before;
    FlashFixture flash;
    uint8_t original[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE];
    uint8_t live[VEGA_PARTY_CAPACITY][VEGA_PARTY_MON_SIZE];
    uint8_t restored_count = 0;
    VegaEncounterRequest request = EncounterRequest();
    VegaMirageState mirage_before;

    memset(&flash, 0, sizeof(flash));
    VegaSaveInitNew(&save, 1);
    memcpy(&flash.active, &save, sizeof(save));
    FillParty(original);
    memcpy(live, original, sizeof(live));

    flash.fail_next = 1;
    memcpy(&before, &save, sizeof(before));
    CHECK(VegaFactoryEnter(&save, original, 6, Persist, &flash) == VEGA_SAVE_PERSIST_FAILED);
    CHECK(memcmp(&save, &before, sizeof(save)) == 0);
    CHECK(save.factory.snapshot_valid == 0);

    CHECK(VegaFactoryEnter(&save, original, 6, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.factory.snapshot_valid == 1);
    CHECK(save.factory.marker == VEGA_FACTORY_SNAPSHOT_COMMITTED);
    memset(live, 0xEE, sizeof(live));
    memcpy(&reset, &flash.active, sizeof(reset));
    CHECK(VegaSaveValidate(&reset, sizeof(reset)) == VEGA_SAVE_OK);
    CHECK(reset.factory.snapshot_valid == 1);
    CHECK(VegaFactorySetBattleActive(&reset, Persist, &flash) == VEGA_SAVE_OK);

    flash.fail_next = 1;
    CHECK(VegaFactoryRestore(&reset, live, &restored_count, Persist, &flash)
          == VEGA_SAVE_PERSIST_FAILED);
    CHECK(memcmp(live, original, sizeof(live)) == 0);
    CHECK(reset.factory.snapshot_valid == 1);
    CHECK(VegaFactoryRestore(&reset, live, &restored_count, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(restored_count == 6);
    CHECK(memcmp(live, original, sizeof(live)) == 0);
    CHECK(reset.factory.snapshot_valid == 0);
    CHECK(reset.factory.marker == VEGA_FACTORY_OUTSIDE);
    memcpy(&save, &flash.active, sizeof(save));
    CHECK(VegaFactoryRestore(&save, live, &restored_count, Persist, &flash) == VEGA_SAVE_NOT_ALLOWED);

    save.mirage.current_record[2] = 33;
    save.mirage.best_record[2] = 44;
    save.mirage.reward_claim_bits = 0x20u;
    memcpy(&mirage_before, &save.mirage, sizeof(mirage_before));
    flash.fail_next = 1;
    memcpy(&before, &save, sizeof(before));
    CHECK(VegaFactoryClaimReward(&save, 2, 500, Persist, &flash) == VEGA_SAVE_PERSIST_FAILED);
    CHECK(memcmp(&save, &before, sizeof(save)) == 0);
    CHECK(VegaFactoryClaimReward(&save, 2, 500, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.factory.battle_points == 500);
    CHECK(VegaFactoryClaimReward(&save, 2, 500, Persist, &flash) == VEGA_SAVE_ALREADY_CLAIMED);
    CHECK(save.factory.battle_points == 500);
    CHECK(memcmp(&save.mirage, &mirage_before, sizeof(mirage_before)) == 0);
    CHECK(VegaFactoryAddBattlePoints(&save, 20000) == VEGA_SAVE_OK);
    CHECK(save.factory.battle_points == VEGA_BP_CAP);
    CHECK(VegaFactorySpendBattlePoints(&save, VEGA_BP_CAP + 1u) == VEGA_SAVE_INSUFFICIENT_CREDIT);
    CHECK(save.factory.battle_points == VEGA_BP_CAP);

    save.encounter_credits[request.credit_kind] = 20;
    VegaSaveFinalize(&save);
    memcpy(&flash.active, &save, sizeof(save));
    memcpy(&before, &save, sizeof(before));
    flash.fail_next = 1;
    flash.partial_write_on_failure = 1;
    CHECK(VegaSavePurchaseEncounter(&save, &request, Persist, &flash) == VEGA_SAVE_PERSIST_FAILED);
    CHECK(memcmp(&save, &before, sizeof(save)) == 0);
    CHECK(memcmp(&flash.active, &before, sizeof(before)) == 0);
    CHECK(VegaSavePurchaseEncounter(&save, &request, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(save.encounter_credits[request.credit_kind] == 13);
    CHECK(save.pending_encounter.valid == 1);
    CHECK(save.pending_encounter.personality == request.personality);
    CHECK(memcmp(save.pending_encounter.generator_fingerprint,
                 request.generator_fingerprint,
                 sizeof(request.generator_fingerprint)) == 0);
    CHECK(VegaSavePurchaseEncounter(&save, &request, Persist, &flash) == VEGA_SAVE_PENDING_EXISTS);
    CHECK(save.encounter_credits[request.credit_kind] == 13);

    memcpy(&reset, &flash.active, sizeof(reset));
    CHECK(reset.pending_encounter.valid == 1);
    CHECK(reset.pending_encounter.personality == request.personality);
    flash.fail_next = 1;
    CHECK(VegaSaveCompleteCapture(&reset, 77, Persist, &flash) == VEGA_SAVE_PERSIST_FAILED);
    CHECK(reset.pending_encounter.valid == 1);
    CHECK(!VegaSaveIsSpecialCaptured(&reset, 77));
    CHECK(VegaSaveCompleteCapture(&reset, 77, Persist, &flash) == VEGA_SAVE_OK);
    CHECK(reset.pending_encounter.valid == 0);
    CHECK(VegaSaveIsSpecialCaptured(&reset, 77));
    memcpy(&save, &flash.active, sizeof(save));
    CHECK(save.pending_encounter.valid == 0);
    CHECK(save.encounter_credits[request.credit_kind] == 13);
    CHECK(VegaSaveIsSpecialCaptured(&save, 77));

    puts("facility-suite: PASS");
    return 0;
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        fprintf(stderr, "usage: %s save|facility\n", argv[0]);
        return 2;
    }
    if (strcmp(argv[1], "save") == 0)
        return RunSaveSuite();
    if (strcmp(argv[1], "facility") == 0)
        return RunFacilitySuite();
    fprintf(stderr, "unknown suite: %s\n", argv[1]);
    return 2;
}
