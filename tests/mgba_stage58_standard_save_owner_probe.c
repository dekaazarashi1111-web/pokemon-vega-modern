/* Read-only Stage58 standard-save owner probe for the T19 purchase path. */
#define QOL_PRODUCTION_EMBEDDED
#include "../tools/mgba_qol_production_smoke.c"

enum {
    PROBE_BAG_POCKETS = 0x020397D8U,
    PROBE_BAG_ITEMS_OFFSET = 0x0310U,
    PROBE_ENCRYPTION_KEY_OFFSET = 0x0F20U,
    PROBE_ABILITY_PATCH = 943U,
    PROBE_SET_BAG_POCKETS_POINTERS = 0x0809984DU,
};

int main(int argc, char **argv)
{
    if (argc != 3) {
        printf("{\"status\":\"ERROR\",\"error\":\"usage\"}\n");
        return 2;
    }
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    run_key_frames(core, 0U, 180U);
    bool descriptor_uninitialized = read32(core, PROBE_BAG_POCKETS) == 0U
        && read8(core, PROBE_BAG_POCKETS + 4U) == 0U;
    uint32_t result = call_preserving(core, QOL_LOAD_GAME_DATA,
                                      0U, 0U, 0U, 0U);
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    uint32_t bag_before = read32(core, PROBE_BAG_POCKETS);
    uint16_t item = save1
        ? read16(core, save1 + PROBE_BAG_ITEMS_OFFSET) : 0U;
    uint16_t quantity_encrypted = save1
        ? read16(core, save1 + PROBE_BAG_ITEMS_OFFSET + 2U) : 0U;
    uint16_t key_low = save2
        ? (uint16_t)read32(core, save2 + PROBE_ENCRYPTION_KEY_OFFSET) : 0U;
    uint16_t quantity = (uint16_t)(quantity_encrypted ^ key_low);
    bool standard_save_restored = result == 1U && save1 != 0U && save2 != 0U
        && item == PROBE_ABILITY_PATCH && quantity == 2U;
    bool descriptor_false_negative = read32(core, PROBE_BAG_POCKETS) == 0U
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           PROBE_ABILITY_PATCH, 2U, 0U, 0U) == 0U;
    (void)call_preserving(core, PROBE_SET_BAG_POCKETS_POINTERS,
                          0U, 0U, 0U, 0U);
    uint32_t bag_after = read32(core, PROBE_BAG_POCKETS);
    uint8_t capacity_after = read8(core, PROBE_BAG_POCKETS + 4U);
    bool descriptor_rebound = bag_after
            == save1 + PROBE_BAG_ITEMS_OFFSET
        && capacity_after == 42U
        && call_preserving(core, QOL_CHECK_BAG_ITEM,
                           PROBE_ABILITY_PATCH, 2U, 0U, 0U) == 1U;
    bool passed = descriptor_uninitialized && standard_save_restored
        && descriptor_false_negative && descriptor_rebound
        && log_problem_count == 0U;
    printf("{\"status\":\"%s\",\"warnings_errors\":%u,\"tests\":{"
           "\"descriptor_uninitialized_reproduced\":%s,"
           "\"standard_save_item_restored\":%s,"
           "\"descriptor_false_negative_reproduced\":%s,"
           "\"set_bag_pockets_repairs_visibility\":%s},"
           "\"evidence\":{\"load_result\":%" PRIu32
           ",\"save1\":%" PRIu32 ",\"save2\":%" PRIu32
           ",\"bag_before\":%" PRIu32 ",\"bag_after\":%" PRIu32
           ",\"expected_bag\":%" PRIu32 ",\"capacity_after\":%u"
           ",\"item_id\":%u,\"quantity_encrypted\":%u"
           ",\"key_low\":%u,\"quantity\":%u}}\n",
           passed ? "PASS" : "FAIL", log_problem_count,
           descriptor_uninitialized ? "true" : "false",
           standard_save_restored ? "true" : "false",
           descriptor_false_negative ? "true" : "false",
           descriptor_rebound ? "true" : "false",
           result, save1, save2, bag_before, bag_after,
           save1 + PROBE_BAG_ITEMS_OFFSET, capacity_after,
           item, quantity_encrypted, key_low, quantity);
    qol_close(core);
    return passed ? 0 : 1;
}
